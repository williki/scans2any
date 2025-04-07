"""Generates a list of potential URLs for the infrastructure."""

from scans2any.internal import Infrastructure, printer

NAME = "url"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": True,
}


def write(infra: Infrastructure, args) -> str:
    """
    Generates a list of potential URLs based on the provided infrastructure.

    For each host/port, generates URLs protocols.
    Includes URLs for the host address and all associated hostnames.

    Returns:
        A newline-separated string of unique URLs.
    """
    url_set = set()  # To avoid duplicate entries

    for host in infra.hosts:
        # Collect all potential addresses: address and hostnames
        addresses = []
        if host.address and "IP-Addresses" in args.columns:
            addresses.append(host.address)

        if "Hostnames" in args.columns:
            addresses.extend(host.hostnames)  # Add all hostnames if any

        # Generate URLs if services are available
        if host.services:
            for service in host.services:
                if not service.service_names:
                    protocol = "unknown"
                else:
                    protocol = service.service_names[0]
                for address in addresses:
                    if "Ports" in args.columns and "Services" in args.columns:
                        url_set.add(f"{protocol}://{address}:{service.port}")
                    elif "Ports" in args.columns:
                        url_set.add(f"{address}:{service.port}")
                    elif "Services" in args.columns:
                        url_set.add(f"{protocol}://{address}")
                    else:
                        url_set.add(address)

    # Log the number of unique URLs generated
    printer.success(
        f"URL set with {len(url_set)} potential entries has been created from parsed input data"
    )

    url_list = sorted(url_set)

    return "\n".join(url_list)
