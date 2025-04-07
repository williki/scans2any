import json
import re

from scans2any.helpers.utils import read_json
from scans2any.internal import Host, Infrastructure, Service, SortedSet

CONFIG = {
    "extensions": [".json"],
}


def add_arguments(parser):
    """
    Add arguments to the parser for input format.
    """
    parser.add_argument(
        "--json",
        type=str,
        action="append",
        nargs="+",
        metavar="filename/directory",
        help="JSON files/directory",
    )


# This parser turns a json into an infrastructure, for more information on the
# structure of the json, please see the json writer at
# src/scans2any/writers/json_writer.py.
def parse(filename: str) -> Infrastructure:
    """
    Parses JSON infrastructure.

    Parameters
    ----------
    filename : str
        Path to JSON output file.

    Returns
    -------
    Infrastructure
        Scan as `Infrastructure` object.
    """
    try:
        content = read_json(filename, dict)
        json_hosts = __parse_json(content)
    except Exception:
        raise
    return Infrastructure(json_hosts, "JSON")


def parse_string(content: str) -> Infrastructure:
    infra = json.loads(content)
    json_hosts = __parse_json(infra)
    return Infrastructure(json_hosts, "JSON")


def __parse_json(infra: dict) -> list[Host]:
    hosts = []
    for ip in infra:
        os_origin_construct = []
        for os in infra[ip].get("os", []):
            os_origin_construct.append((os, "json"))
        host = Host(
            address=set() if re.match(pattern="^unknown_.*$", string=ip) else set([ip]),
            hostnames=set(infra[ip].get("hostnames", [])),
            os=set(os_origin_construct),
        )
        host.address.update(infra[ip].get("ip-addresses", []))
        services = []
        for port in infra[ip].get("tcp_ports", []):
            services.append(
                __new_service(
                    infra[ip]["tcp_ports"],
                    port,
                    "tcp",
                )
            )
        for port in infra[ip].get("udp_ports", []):
            services.append(
                __new_service(
                    infra[ip]["udp_ports"],
                    port,
                    "udp",
                )
            )
        host.add_services(
            new_services=services,
        )
        hosts.append(host)

    return hosts


def __new_service(port_dict: dict, port: str, protocol: str) -> Service:
    service = Service(
        port=int(port),
        protocol=protocol,
        service_names=SortedSet(
            port_dict[port].get("service_names", []),
        ),
        banners=SortedSet(
            port_dict[port].get("banners", []),
        ),
    )
    return service
