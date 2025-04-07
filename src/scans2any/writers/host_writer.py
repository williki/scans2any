"""Generates a list of IPs and hostnames of the infrastructure."""

from scans2any.internal import Infrastructure, printer

NAME = "host"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": True,
}


def write(infra: Infrastructure, args) -> str:
    """
    Generates a list of IP and hostnames based on the provided infrastructure.

    Returns:
        A newline-separated string of unique hosts.
    """
    address_set = set()
    dns_set: set[str] = set()

    for host in infra.hosts:
        # Collect all potential addresses: address and hostnames
        if host.address:
            for address in host.address:
                address_set.add(address)
        dns_set.update(host.hostnames)

    # Log the number of unique hosts generated
    printer.success(
        f"Set with {len(address_set)} hostnames and {len(dns_set)} IP entries has been created from parsed input data"
    )

    names_list = []
    if "IP-Addresses" in args.columns:
        names_list += sorted(address_set)
    if "Hostnames" in args.columns:
        names_list += sorted(dns_set)

    return "\n".join(names_list)
