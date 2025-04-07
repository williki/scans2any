import ipaddress
import json
import re
from os import path
from typing import TypeVar

from partial_json_parser import loads as json_partial_loads  # type: ignore

from scans2any.internal import printer

# Define valid column names (normalized to lowercase for comparison)
VALID_COLUMNS = {
    "ip-addresses": "IP-Addresses",
    "hostnames": "Hostnames",
    "ports": "Ports",
    "services": "Services",
    "banners": "Banners",
    "os": "OS",
}


def validate_columns(columns: tuple[str, ...]) -> tuple[str, ...]:
    """
    Validates column names and normalizes them.

    Parameters
    ----------
    columns : tuple[str, ...]
        The columns specified by the user

    Returns
    -------
    tuple[str, ...]
        Validated and normalized column names
    """

    valid_columns = []
    for col in columns:
        col_lower = col.lower()
        if col_lower in VALID_COLUMNS:
            valid_columns.append(VALID_COLUMNS[col_lower])
        else:
            printer.warning(f"Invalid column: '{col}'. Ignoring this column.")

    if not valid_columns:
        printer.warning("No valid columns specified. Using default columns.")
        return tuple(VALID_COLUMNS.values())

    return tuple(valid_columns)


def joinit(lst, delimiter):
    """
    Joins a list using `delimiter` as in-between-item.
    """
    if not lst:
        return []

    joined_list = [lst[0]]
    for item in lst[1:]:
        joined_list.append(delimiter)
        joined_list.append(item)

    return joined_list


def is_valid_ip(address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def is_valid_ipv4(address: str | None) -> bool:
    try:
        ipaddress.IPv4Address(address)
        return True
    except ValueError:
        return False


def is_valid_ipv6(address: str | None) -> bool:
    try:
        ipaddress.IPv6Address(address)
        return True
    except ValueError:
        return False


def find_os(os_detection_result: str) -> str | None:
    """
    Extracts information from the given string (coming from some kind of
    os-detection (e.g. Nessus) result) to return a simplified OS result, if
    possible.
    """

    # OS detection mapping with variants simplified to core categories
    os_map = {
        # Linux distributions
        "linux": "linux",
        "centos": "linux",
        "arch": "linux",
        "manjaro": "linux",
        "ubuntu": "linux",
        "debian": "linux",
        "fedora": "linux",
        "red hat": "linux",
        "gentoo": "linux",
        "suse": "linux",
        # Windows variants
        "windows": "windows",
        "win": "windows",
        "microsoft": "windows",
        # macOS variants
        "macos": "macos",
        "mac os": "macos",
        "os x": "macos",
        "darwin": "macos",
        "mac_os": "macos",
        "mac-os": "macos",
        "macintosh": "macos",
        # FreeBSD
        "freebsd": "bsd",
        "openbsd": "bsd",
        "netbsd": "bsd",
    }

    # Convert the detection result to lowercase for case-insensitive matching
    os_detection_result = os_detection_result.lower()

    # Search for any OS indicator in the result
    for key, value in os_map.items():
        if key in os_detection_result:
            return value

    return None


def trustworthiness_os(info_origin: str) -> int:
    """
    Union OS lists based on info_origins
    Return trustworthiness of info_origin

    Parameters
    ----------
    info_origin : str
        The origin of the information

    Returns
    -------
    int
        Trustworthiness of the origin
    """
    os_prio_list = (
        "Nmap",
        "Nessus",
        "NetExec",
        "Bloodhound",
    )  # from least to most trustworthy
    if info_origin in os_prio_list:
        return os_prio_list.index(info_origin) + 1
    return 0


def no_common_elements(lists: list[list]):
    """
    Check if any two of the lists share an element.

    Parameters
    ----------
    lists : list
        List of lists to be compared for shared elements.
    """

    n = len(lists)
    for i in range(n):
        for j in range(i + 1, n):
            if bool(set(lists[i]) & set(lists[j])):
                return False

    return True


T = TypeVar("T")


class FileError(Exception):
    pass


class PartialParsingFailedError(Exception):
    pass


def is_special_fd(filename: str) -> bool:
    return bool(re.match(r"^(?:/proc/self/fd/|/dev/fd/)\d+$", filename))


def read_json[T](filename: str, return_type: type[T]) -> T:
    if not is_special_fd(filename) and (
        not path.isfile(filename) or path.getsize(filename) == 0
    ):
        raise FileError(f"File {filename} is empty or does not exist.")

    with open(filename) as file:
        content = file.read()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Fallback to partial parsing
        try:
            return json_partial_loads(content)
        except Exception as f:
            raise PartialParsingFailedError(
                f"JSON parsing '{e}' and partial parsing '{f}' failed."
            ) from e


def match_dns(dns: str) -> bool:
    """
    Check if a given string is a valid DNS name.

    Parameters
    ----------
    dns : str
        The string to be checked.

    Returns
    -------
    bool
        True if the string is a valid DNS name, False otherwise.
    """
    domain_regex = (
        r"^(?!-)(?:[a-zA-Z0-9-]{1,63}|(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,})$"
    )

    return re.match(domain_regex, dns) is not None


def match_fqdn(dns: str) -> bool:
    """
    Check if a given string is a valid DNS name.

    Parameters
    ----------
    dns : str
        The string to be checked.

    Returns
    -------
    bool
        True if the string is a valid FQDN name, False otherwise.
    """
    domain_regex = r"^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$"

    return re.match(domain_regex, dns) is not None


def cleanup(string: str, chars_to_escape: str) -> str:
    escaped_chars = re.escape(chars_to_escape)

    # Construct a regex pattern that matches any of the characters to be escaped
    # The regex looks for any character in escaped_chars that is not already preceded by a backslash
    pattern = r"(?<!\\)([" + escaped_chars + "])"

    # Replace any unescaped special character with its escaped version
    string = re.sub(pattern, r"\\\1", string)

    return string
