"""
NetExec DB parser
Extracts IP, Hostname, SMB related settings & OS from NetExec/CrackMapExec
SQLite Databases.
"""

import sqlite3

from scans2any.helpers.utils import find_os
from scans2any.internal import Host, Infrastructure, Service, SortedSet

CONFIG = {
    "extensions": [".db"],
}


def add_arguments(parser):
    """
    Add arguments to the parser for input format.
    """
    parser.add_argument(
        "--nxc",
        type=str,
        action="append",
        nargs="+",
        metavar="filename/directory",
        help="NetExec/CrackMapExec SMB.db sqlite database/directory",
    )


def parse(filename: str) -> Infrastructure:
    infra = Infrastructure(identifier="NetExec")
    with sqlite3.connect(filename) as conn:
        cursor = conn.execute("SELECT ip, hostname, os, signing, smbv1 FROM hosts")
        for ip, hostname, os, signing, smbv1 in cursor:
            banner_parts = []
            if signing == 0:
                banner_parts.append("SMB Signing disabled!")
            if smbv1:
                banner_parts.append("SMBv1 enabled!")
            banner = " ".join(banner_parts)

            service = Service(
                port=445,
                protocol="tcp",
                service_names=SortedSet(["smb"]),
                banners=SortedSet([banner]),
            )

            os_result = find_os(os) if os else None
            host = Host(
                address=ip,
                hostnames=set([hostname.lower()]) if hostname else set(),
                os=set([(os_result, "NetExec")]) if os_result else set(),
            )

            host.services.append(service)
            infra.hosts.append(host)
    return infra
