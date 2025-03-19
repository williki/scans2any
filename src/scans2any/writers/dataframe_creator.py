"""Convert infrastructure objects to pandas DataFrames for unified writer processing."""

import pandas as pd

from scans2any.internal import Infrastructure, printer


def create_dataframes(
    infra: Infrastructure,
    *,
    columns: tuple[str, ...],
    multi_table: bool,
    merge_symbol: str,
) -> list[pd.DataFrame]:
    """
    Convert the internal representation of the infrastructure
    into pandas DataFrames.

    Parameters
    ----------
    infra : Infrastructure
        The infrastructure to convert
    columns : tuple[str, ...]
        The columns to include in the output
    multi_table : bool, optional
        Whether to create mutli table for all hosts, by default False
    merge_symbol : str, optional
        Symbol to use when merging multiple values, by default "<br>"

    Returns
    -------
    list[pd.DataFrame]
        A list of pandas DataFrames. If multi_table is True, the list contains
        only one DataFrame. Otherwise, it contains one DataFrame per host.
    """

    if multi_table:
        return _create_multi_tables(infra, columns=columns, merge_symbol=merge_symbol)
    return [_create_single_table(infra, columns=columns, merge_symbol=merge_symbol)]


def _create_multi_tables(
    infra: Infrastructure, *, columns: tuple[str, ...], merge_symbol: str
) -> list[pd.DataFrame]:
    """
    Create one pandas DataFrame per host.
    """
    dataframes = []

    # Define which columns belong in the header and which in the row data
    header_keys = {"IP-Addresses", "Hostnames", "OS"}
    row_keys = {"Ports", "Services", "Banners"}

    for host in infra.hosts:
        ip = host.address or ""
        hostnames = merge_symbol.join(h for h in host.hostnames if h)
        os_info = host.os[0] if host.os else ""

        ports = []
        services = []
        banners = []
        for service in host.services:
            banners.append(service.banners[0] if service.banners else "")
            services.append(service.service_names[0] if service.service_names else "")
            ports.append(f"{service.port}/{service.protocol}")

        header_values = []
        row_values: dict[str, list | str] = {}
        for col in columns:
            if col in header_keys:
                if col == "IP-Addresses":
                    header_values.append(ip)
                elif col == "Hostnames":
                    header_values.append(hostnames)
                elif col == "OS":
                    header_values.append(os_info)
            elif col in row_keys:
                if col == "Ports":
                    row_values[col] = ports
                elif col == "Services":
                    row_values[col] = services
                elif col == "Banners":
                    row_values[col] = banners

        # if only header_values, show only first line
        rows_len = 0 if not row_values else len(ports)

        # Add empty values to maintain column structure
        while len(header_values) > len(row_values):
            row_values[str(len(row_values))] = ""

        while len(row_values) > len(header_values):
            header_values.append("")

        df = pd.DataFrame(row_values, index=range(0, rows_len))
        df.columns = pd.Index(header_values)
        dataframes.append(df)

    return dataframes


def _create_single_table(
    infra: Infrastructure, *, columns: tuple[str, ...], merge_symbol: str
) -> pd.DataFrame:
    """
    Create a single pandas DataFrame for all hosts.
    """
    rows = []

    for host in infra.hosts:
        ip = host.address or ""
        hostnames = merge_symbol.join(h for h in host.hostnames if h)
        os_info = host.os[0] if host.os else ""

        ports = merge_symbol.join(f"{s.port}/{s.protocol}" for s in host.services)
        services = merge_symbol.join(
            " ".join(list(s.service_names)) for s in host.services
        )
        banners = merge_symbol.join(
            s.banners[0] if s.banners else "" for s in host.services
        )

        row = {}
        for col in columns:
            if col == "IP-Addresses":
                row[col] = ip
            elif col == "Hostnames":
                row[col] = hostnames
            elif col == "OS":
                row[col] = os_info
            elif col == "Ports":
                row[col] = ports
            elif col == "Services":
                row[col] = services
            elif col == "Banners":
                row[col] = banners

        rows.append(row)

    df = pd.DataFrame(rows)
    printer.success(f"Created dataframe with {len(rows)} hosts")
    return df


# For CSV and other formats that need flattened rows (one row per service)
def create_flat_dataframe(
    infra: Infrastructure,
    *,
    columns: tuple[str, ...],
    merge_symbol: str,
) -> pd.DataFrame:
    """
    Create a flattened DataFrame with one row per service.
    Useful for CSV and other row-based formats.
    """

    rows = []

    for host in infra.hosts:
        address = host.address or ""
        hostnames = merge_symbol.join(h for h in host.hostnames if h)
        os_info = host.os[0] if host.os else ""

        if host.services:
            for service in host.services:
                row = {}
                for col in columns:
                    if col == "IP-Addresses":
                        row[col] = address
                    elif col == "Hostnames":
                        row[col] = hostnames
                    elif col == "OS":
                        row[col] = os_info
                    elif col == "Ports":
                        row[col] = f"{service.port}/{service.protocol}"
                    elif col == "Services":
                        row[col] = merge_symbol.join(service.service_names)
                    elif col == "Banners":
                        row[col] = merge_symbol.join(service.banners)
                rows.append(row)
        else:
            # Host with no services
            row = {}
            for col in columns:
                if col == "IP-Addresses":
                    row[col] = address
                elif col == "Hostnames":
                    row[col] = hostnames
                elif col == "OS":
                    row[col] = os_info
                elif col in {"Ports", "Services", "Banners"}:
                    row[col] = ""
            rows.append(row)

    df = pd.DataFrame(rows)
    printer.success(f"Created flat dataframe with {len(rows)} rows")
    return df


def create_data_unmerged(
    infra: Infrastructure,
    *,
    columns: tuple[str, ...],
) -> dict:
    host_dict = {}
    unknown_counter = 0
    for host in infra.hosts:
        ip = host.address or f"unknown_{unknown_counter}"
        if not host.address:
            unknown_counter += 1

        ip_infos: dict[str, list | dict] = {}
        host_dict[ip] = ip_infos

        for col in columns:
            if col == "Hostnames":
                ip_infos[col.lower()] = list(host.hostnames)
            if col == "OS":
                ip_infos[col.lower()] = list(host.os)
            if col == "Ports" or col == "Services" or col == "Banners":
                tcp_ports = {}
                udp_ports = {}
                for service in host.services:
                    service_row = {}
                    for col in columns:
                        if col == "Services":
                            service_row["service_names"] = list(service.service_names)
                        elif col == "Banners":
                            service_row[col.lower()] = list(service.banners)
                    if service.protocol == "tcp":
                        tcp_ports[service.port] = service_row
                    elif service.protocol == "udp":
                        udp_ports[service.port] = service_row

                ip_infos["tcp_ports"] = tcp_ports
                ip_infos["udp_ports"] = udp_ports

    return host_dict


def create_dataframe_unmerged(
    infra: Infrastructure,
    *,
    columns: tuple[str, ...],
) -> pd.DataFrame:
    host_dict = create_data_unmerged(infra, columns=columns)
    return pd.DataFrame(host_dict)
