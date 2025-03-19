import re

from scans2any.internal import Host

PRIORITY = 1


def add_arguments(parser):
    """
    Add arguments to the parser for the services allowlist filter.
    """
    parser.add_argument(
        "--service-regex",
        nargs="+",
        help="Servicenames match via regex (format: --service-regex <service-pattern> <service-pattern> ...)",
        default=[""],
    )


def apply_filter(host: Host, args):
    """Filter services by service regex."""

    if not args.service_regex or args.service_regex == [""]:
        return

    # Compile regex patterns for efficiency
    patterns = [re.compile(pattern) for pattern in args.service_regex]

    # Use list comprehension with regex matching
    host.services = [
        service
        for service in host.services
        if any(
            any(pattern.search(service_name) for pattern in patterns)
            for service_name in service.service_names
        )
    ]
