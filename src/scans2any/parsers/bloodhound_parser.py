"""
Bloodhound parser
Extracts information (Hostname & OS) from Bloodhound JSON files.
Does not extract any services, ports or IP-Adresses!
"""

from scans2any.helpers.utils import find_os, read_json
from scans2any.internal import Host, Infrastructure, SortedSet

CONFIG = {
    "extensions": [".json"],
}


def add_arguments(parser):
    """
    Add arguments to the parser for input format.
    """
    parser.add_argument(
        "--bloodhound",
        type=str,
        action="append",
        nargs="+",
        metavar="filename/directory",
        help="Bloodhound computer JSON file/directory",
    )


def parse(filename: str) -> Infrastructure:
    """
    Parses Bloodhound JSON Computers report.

    Parameters
    ----------
    filename : str
        Path to JSON Bloodhound report

    Returns
    -------
    Infrastructure
        Bloodhound's scan as `Infrastructure` object.
    """

    try:
        infra = Infrastructure(__parse_json(filename), identifier="Bloodhound")
    except Exception:
        raise
    return infra


def __parse_json(filename: str) -> list[Host]:
    hosts: list[Host] = []
    data: dict[str, dict] = read_json(filename, dict)

    for host in data.get("data", []):
        try:
            hostos: SortedSet[tuple[str, str]] = SortedSet()
            properties = host.get("Properties", {})
            name = properties.get("name")
            operatingsystem = properties.get("operatingsystem")
            os_result = find_os(operatingsystem) if operatingsystem else None

            if os_result:
                hostos.add((os_result, "Bloodhound"))

            hosts.append(
                Host(
                    address=None,
                    hostnames=SortedSet([name.lower()]),
                    os=hostos,
                )
            )
        except (KeyError, IndexError):
            continue  # Skip incomplete objects from partial parsing
    return hosts
