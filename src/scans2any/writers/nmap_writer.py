"""Prints a Nmap scan script for all TCP/UDP ports of the infrastructure."""

from scans2any.helpers.utils import is_valid_ipv6
from scans2any.internal import Infrastructure

NAME = "nmap"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": True,
}


def add_arguments(parser):
    """
    Add nmap scan options for TCP and UDP to the parser.
    """
    parser.add_argument(
        "--options-tcp",
        type=str,
        default="-sS -A -Pn -n -T4 -oA",
        help="TCP scan options for nmap",
    )

    parser.add_argument(
        "--options-udp",
        type=str,
        default="-sU -A -Pn -n -T4 -oA",
        help="UDP scan options for nmap",
    )


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into an nmap scan script.
    """
    nmap = []
    nmap.append("#!/bin/sh\n")

    for host in infra.hosts:
        # Determine the address (either IP or hostname)
        address = (
            next(iter(host.address))
            if "IP-Addresses" in args.columns and host.address
            else None
        ) or (
            next(iter(host.hostnames))
            if "Hostnames" in args.columns and host.hostnames
            else None
        )

        if not address:
            continue  # Skip if no valid address is available

        if "Ports" in args.columns:
            ports_tcp = [
                str(service.port)
                for service in host.services
                if service.protocol == "tcp"
            ]
            ports_udp = [
                str(service.port)
                for service in host.services
                if service.protocol == "udp"
            ]
        else:
            ports_tcp, ports_udp = [], []

        if ports_tcp:
            # Empty host are already filtered, but there might be the case that
            # we found a host with udp port and don't have tcp ports for it

            # Add an extra (closed) port for OS detection
            ports_tcp.append(str(int(ports_tcp[-1]) + 1))
            if is_valid_ipv6(address):
                nmap.append(
                    f"nmap {address} {args.options_tcp} {address} -p {','.join(ports_tcp)} -6"
                )
            else:
                nmap.append(
                    f"nmap {address} {args.options_tcp} {address} -p {','.join(ports_tcp)}"
                )
        else:
            nmap.append(f"nmap {address} {args.options_tcp} {address} --top-ports 1000")
        if ports_udp:
            nmap.append(
                f"nmap {address} {args.options_udp} {address}u -p {','.join(ports_udp)}"
            )
    return "\n".join(nmap)
