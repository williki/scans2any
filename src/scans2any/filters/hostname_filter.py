import re

from scans2any.internal import Infrastructure

PRIORITY = 3


def add_arguments(parser):
    """
    Add arguments to the parser for the hostname filter.
    """
    parser.add_argument(
        "--hosts-regex",
        nargs="+",
        help="Hostsnames match via regex (format: --hosts-regex <hostname-pattern> <hostname-pattern> ...)",
        default=[""],
    )


def apply_filter(infra: Infrastructure, args):
    """Filter hosts by hostname."""
    if not args.hosts_regex or args.hosts_regex == [""]:
        return

    # Compile regex patterns for efficiency
    patterns = [re.compile(pattern) for pattern in args.hosts_regex]

    # Use list comprehension with regex matching
    infra.hosts = [
        host
        for host in infra.hosts
        if any(
            any(pattern.search(hostname) for pattern in patterns)
            for hostname in host.hostnames
        )
    ]
