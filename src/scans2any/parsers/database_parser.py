"""
Parse scan data from SQLite database.

Reads infrastructure data from a project-specific SQLite database.
Supports efficient filtering at the SQL level.
"""

from scans2any.internal import Infrastructure, printer
from scans2any.internal.database import Database

CONFIG = {
    "extensions": [".db", ".sqlite", ".sqlite3"],
}


def add_arguments(parser):
    """
    Add arguments to the parser for database input.

    Database can be loaded with just --project flag.
    If --project is specified without other inputs, data is loaded from database.
    If --project is specified WITH other inputs, new data is merged into database.
    """
    # No additional arguments needed - --project already exists in main CLI
    pass


def _parse_column_filters(col_filters: list[str]) -> dict[str, str]:
    """
    Parse column:regex filters into database filter dict.

    Parameters
    ----------
    col_filters : list[str]
        List of "column:regex" strings

    Returns
    -------
    dict[str, str]
        Filter dict with SQL LIKE patterns
    """
    filters = {}
    column_map = {
        "IP-Addresses": "address",
        "IP": "address",
        "Hostnames": "hostname",
        "Hostname": "hostname",
        "Ports": "port",
        "Port": "port",
        "Services": "service",
        "Service": "service",
        "Banners": "banner",
        "Banner": "banner",
    }

    for col_filter in col_filters:
        if ":" not in col_filter:
            continue

        col, pattern = col_filter.split(":", 1)
        db_col = column_map.get(col)

        if not db_col:
            continue

        # Convert regex to SQL LIKE pattern (simple conversion)
        # For exact matches or simple patterns
        if db_col == "port":
            # Port should be exact match
            try:
                filters[db_col] = int(pattern)
            except ValueError:
                continue
        else:
            # Convert to SQL LIKE pattern
            # Replace .* with %, . with _, etc.
            like_pattern = pattern.replace(".*", "%").replace(".", "_")
            if not like_pattern.startswith("%"):
                like_pattern = "%" + like_pattern
            if not like_pattern.endswith("%"):
                like_pattern = like_pattern + "%"
            filters[db_col] = like_pattern

    return filters


def parse(project: str = "default", args=None) -> Infrastructure:
    """
    Parses SQLite database and generates an Infrastructure object.

    Parameters
    ----------
    project : str
        Project name to read from database (default: "default")
        Database file is {project}.db
    args : argparse.Namespace, optional
        Command line arguments for filtering and verbosity

    Returns
    -------
    Infrastructure
        Scan data as `Infrastructure` object.
    """

    db_path = (
        project if project.endswith(tuple(CONFIG["extensions"])) else f"{project}.db"
    )

    printer.status(f"Database: {db_path}")

    # Parse column filters from args if provided
    filters = None
    if args and hasattr(args, "col") and args.col:
        filters = _parse_column_filters(args.col)
        if filters:
            printer.info(f"Applying database filters: {filters}")

    verbose = args and hasattr(args, "verbose") and args.verbose > 0

    with Database(db_path, project) as db:
        stats = db.get_statistics()

        if verbose:
            printer.info(f"Project '{project}' contains:")
            printer.info(f"  - {stats['hosts']} hosts")
            printer.info(f"  - {stats['services']} services")
            if stats["protocols"]:
                printer.info(f"  - Protocols: {', '.join(stats['protocols'])}")

        if not filters and stats["hosts"] > 0:
            printer.info(
                f"Loading {stats['hosts']} hosts with {stats['services']} services"
            )

        infra = db.read_infrastructure(filters=filters)

    printer.success(f"Successfully loaded project '{project}' from database")
    return infra
