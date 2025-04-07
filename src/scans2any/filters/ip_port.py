from ipaddress import ip_address, summarize_address_range

from scans2any.internal import Infrastructure, printer

PRIORITY = 1


def add_arguments(parser):
    """
    Add arguments to the parser for the ip and port filter.
    """
    parser.add_argument(
        "--ip-allowlist",
        nargs="+",
        help="IP ranges to allow (format: --ip-allowlist start_ip-end_ip start_ip-end_ip ...)",
        default=[],
    )
    parser.add_argument(
        "--ip-blocklist",
        nargs="+",
        help="IP ranges to block (format: --ip-blocklist start_ip-end_ip start_ip-end_ip ...)",
        default=[],
    )
    parser.add_argument(
        "--port-allowlist",
        nargs="+",
        help="Port ranges to allow (format: --port-allowlist start_port-end_port start_port-end_port ...)",
        default=[],
    )
    parser.add_argument(
        "--port-blocklist",
        nargs="+",
        help="Port ranges to block (format: --port-blocklist start_port-end_port start_port-end_port ...)",
        default=[],
    )


def apply_filter(infra: Infrastructure, args):
    """Filter out ips and/or ports by blocklist or by allowlist."""

    # Process Allowlisted and Blocklisted IPs
    if args.ip_allowlist:
        hosts = set()  # Use set to avoid redundancies
        for address_range in args.ip_allowlist:
            try:
                start_ip, end_ip = address_range.split("-")
                networks = summarize_address_range(
                    ip_address(start_ip), ip_address(end_ip)
                )
            except ValueError:
                printer.error(
                    f"Invalid IP range: {address_range}. Please use the format start_ip-end_ip."
                )
                return
            for network in networks:
                for ip in network:
                    host = infra.get_host_by_address(str(ip))
                    if host:
                        hosts.add(host)
        infra.hosts = list(hosts)

    if args.ip_blocklist:
        for address_range in args.ip_blocklist:
            try:
                start_ip, end_ip = address_range.split("-")
                networks = summarize_address_range(
                    ip_address(start_ip), ip_address(end_ip)
                )
            except ValueError:
                printer.error(
                    f"Invalid IP range: {address_range}. Please use the format start_ip-end_ip."
                )
                return
            for network in networks:
                for ip in network:
                    infra.remove_host(str(ip))

    # Process Allowlisted and Blocklisted Ports for each host
    for host in infra.hosts:
        # Allowlisted Ports
        if args.port_allowlist:
            allowed_services = set()
            for port_range in args.port_allowlist:
                try:
                    start_port, end_port = map(int, port_range.split("-"))
                except ValueError:
                    printer.error(
                        f"Invalid port range: {port_range}. Please use the format start_port-end_port."
                    )
                    return
                for port in range(start_port, end_port + 1):
                    service = host.get_service_by_port(port)
                    if service:
                        allowed_services.add(service)
            host.services = list(allowed_services)

        # Blocklisted Ports
        if args.port_blocklist:
            for port_range in args.port_blocklist:
                try:
                    start_port, end_port = map(int, port_range.split("-"))
                except ValueError:
                    printer.error(
                        f"Invalid port range: {port_range}. Please use the format start_port-end_port."
                    )
                    return
                host.remove_services((start_port, end_port))
