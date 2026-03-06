from pathlib import Path

from scans2any.internal import Infrastructure, printer

PRIORITY = 3


def add_arguments(parser):
    """
    Add arguments to the parser for the hosts file filter.
    """
    pass


def apply_filter(infra: Infrastructure, args):
    """Filter hosts by a list of IPs or hostnames from a file."""
    if not args.hosts_file:
        return

    hosts_file_path = Path(args.hosts_file)
    if not hosts_file_path.is_file():
        printer.error(f"Hosts file not found: {args.hosts_file}")
        return

    allowed_entries = set()
    try:
        with hosts_file_path.open("r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    allowed_entries.add(line)
    except Exception as e:
        printer.error(f"Error reading hosts file: {e}")
        return

    if not allowed_entries:
        printer.warning(
            f"Hosts file {args.hosts_file} is empty or contains no valid entries."
        )
        return

    # Filter hosts
    original_count = len(infra.hosts)
    infra.hosts = [
        host
        for host in infra.hosts
        if any(addr in allowed_entries for addr in host.address)
        or any(name in allowed_entries for name in host.hostnames)
    ]

    printer.info(
        f"Hosts file filter: kept {len(infra.hosts)} of {original_count} hosts."
    )
