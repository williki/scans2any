"""Prints a list of potential http/https URLs with ports."""

from scans2any.internal import Infrastructure, printer

NAME = "aquatone"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": True,
}


def write(infra: Infrastructure, args) -> str:
    """
    Prints a list of potential http/https URLs.

    For each host/port there will be two outputs for the host-address:
    ```
    http://host-address:port
    https://host-address:port
    ```

    and 2 * count of hostnames outputs:
    ```
    http://hostname:port
    https://hostname:port
    ```
    """

    url_set = set()  # avoid duplicate entries

    protocols = ["http", "https"]

    for host in infra.hosts:
        # Collect all the potential URLs
        addresses = []

        if host.address and "IP-Addresses" in args.columns:
            addresses.append(host.address)

        if "Hostnames" in args.columns:
            addresses.extend(host.hostnames)  # Add all hostnames if any

        # If services exist, use ports; otherwise, no ports
        if host.services and "Ports" in args.columns:
            for service in host.services:
                for address in addresses:
                    for protocol in protocols:
                        url_set.add(f"{protocol}://{address}:{service.port}")
        else:
            for address in addresses:
                for protocol in protocols:
                    url_set.add(f"{protocol}://{address}")

    printer.success(
        f"URL set with {len(url_set)} potential entries has been created from parsed input data"
    )

    url_list = list(url_set)
    url_list.sort()

    return "\n".join(str(url) for url in url_list)
