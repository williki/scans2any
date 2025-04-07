"""
Infrastructure processing utilities for scans2any.
"""

from scans2any.helpers.file_processing import create_progress_bar
from scans2any.internal import Infrastructure, printer
from scans2any.parsers import merge_file_parser
from scans2any.writers import avail_writers


def handle_merge_file(merge_file) -> tuple[Infrastructure | None, list[dict] | None]:
    """Parse merge file if provided."""
    if merge_file:
        merge_infra, auto_merge_ruleset = merge_file_parser.parse(merge_file)
        printer.debug(merge_infra)
        printer.debug("\nAuto merge ruleset:")
        printer.debug(auto_merge_ruleset)
        return merge_infra, auto_merge_ruleset
    return None, None


def combine_infrastructure_scans(infras: list[Infrastructure], *, quiet=False):
    """Combine multiple infrastructure scans into one."""
    printer.section("Combining Reports")

    if not infras:
        printer.failure("No inputs given!")
        exit(1)

    if len(infras) == 1:
        combined_infra = infras[0]
        printer.status(f"One input given: {combined_infra.identifier}")
    else:
        combined_infra = infras[0]
        pbar = create_progress_bar(quiet=quiet)
        pbar.total = len(infras)
        pbar.set_description("Combining infrastructures")

        pbar.update(1)
        for next_infra in infras[1:]:
            combined_infra.union_with_infrastructure(next_infra)
            pbar.update(1)
        pbar.close()

    # Iteratively re-run the merge process on all hosts until no further merges occur.
    prev_count = -1
    while prev_count != len(combined_infra.hosts):
        prev_count = len(combined_infra.hosts)
        # Copy current hosts to re-run merging
        hosts = combined_infra.hosts[:]
        # Reset the hosts list before re-adding them
        combined_infra.hosts = []
        combined_infra.add_hosts(hosts)

    combined_infra.identifier = "Combined"

    return combined_infra


def resolve_infrastructure_conflicts(
    primary_infra: Infrastructure,
    merge_file_infra: Infrastructure | None,
    merge_ruleset: list[dict] | None,
) -> Infrastructure:
    """Resolve conflicts between infrastructures using a merge file."""
    printer.section("Manual Conflict Resolution")

    if primary_infra is None:
        if merge_file_infra is not None:
            printer.warning("No primary input data - using merge file input only")
            return merge_file_infra
        else:
            raise Exception("No input data available for processing")

    if merge_file_infra is None:
        printer.status("No merge file provided - keeping original infrastructure")
        return primary_infra

    # Apply merge file to resolve conflicts
    printer.status("Resolving conflicts using merge file decisions")
    merge_file_infra.merge_with_infrastructure(primary_infra, merge_ruleset)
    return merge_file_infra


def check_for_remaining_conflicts(
    infra: Infrastructure, *, passed_merge_file: bool
) -> bool:
    """Check for remaining conflicts and create a merge file if needed."""
    printer.section("Checking for Remaining Conflicts")

    conflict_found = infra.make_merge_file(passed_merge_file=passed_merge_file)
    if not conflict_found:
        printer.success("No conflicts detected in infrastructure data")
        return False

    printer.warning("Use merge file with '--merge-file filename' to resolve conflicts")
    return True


def apply_filters(infra: Infrastructure, enabled_filters: list[str], args):
    """Apply filters to the infrastructure."""
    if not enabled_filters:
        return

    from scans2any.filters import avail_filters

    printer.section("Applying filters")

    active_filters = [
        (name, obj, level)
        for name, obj, level in avail_filters
        if name in enabled_filters
    ]

    sorted_filters = sorted(active_filters, key=lambda item: item[1].PRIORITY)

    for name, obj, level in sorted_filters:
        printer.status(f"{name}: {obj.apply_filter.__doc__}")
        printer.debug(f"Priority: {obj.PRIORITY}")

        if level == "infra":
            obj.apply_filter(infra, args)
        elif level == "host":
            for host in infra.hosts:
                obj.apply_filter(host, args)
        elif level == "service":
            for host in infra.hosts:
                for service in host.services:
                    obj.apply_filter(service, args)


def generate_output(infra: Infrastructure, args):
    """Generate output based on selected writer."""
    printer.section("Output")

    writer = None
    for obj in avail_writers:
        if args.writer == obj.NAME:
            writer = obj
            break

    if not writer:
        printer.failure(f"Output writer {args.writer} is not defined!")
        exit(1)

    return writer.write(infra, args)
