"""Writes infrastructure data to SQLite database."""

from pathlib import Path
from sqlite3 import IntegrityError

from scans2any.internal import Infrastructure, printer
from scans2any.internal.database import Database

NAME = "database"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def add_arguments(parser):
    """
    Add arguments to the parser for database output.
    """
    parser.add_argument(
        "--db-clear",
        action="store_true",
        default=False,
        help="Clear existing project data before writing to database",
    )


def write(infra: Infrastructure, args) -> str:
    """
    Write the infrastructure data to SQLite database.

    Parameters
    ----------
    infra : Infrastructure
        Infrastructure object to write
    args : argparse.Namespace
        Command line arguments

    Returns
    -------
    str
        Success message
    """
    # Get project from args
    project = getattr(args, "project", "default")
    if not project:
        project = "default"

    db_path = Path(f"{project}.db")
    clear = getattr(args, "db_clear", False)
    verbose = hasattr(args, "verbose") and args.verbose > 0

    printer.section("Writing to Database")
    printer.status(f"Database: {db_path}")
    printer.status(f"Project: {project}")

    with Database(db_path, project) as db:
        if clear:
            printer.info("Clearing existing project data")
            if verbose:
                old_stats = db.get_statistics()
                printer.info(
                    f"Removing {old_stats['hosts']} hosts and {old_stats['services']} services"
                )

        if verbose:
            printer.info(f"Writing {len(infra.hosts)} hosts...")
            service_count = sum(len(h.services) for h in infra.hosts)
            printer.info(f"Writing {service_count} services...")
        try:
            db.write_infrastructure(infra, clear=clear)
        except IntegrityError as e:
            printer.failure(f"Failed to write to database: {e}")
            printer.failure("Try to re-rerun with -F empty_host")
            exit(1)
        except Exception as e:
            printer.failure(f"Failed to write to database: {e}")
            raise
        stats = db.get_statistics()

    if verbose:
        printer.info("Database now contains:")
        printer.info(f"  - {stats['hosts']} hosts")
        printer.info(f"  - {stats['services']} services")
        if stats["protocols"]:
            printer.info(f"  - Protocols: {', '.join(stats['protocols'])}")

    printer.success(
        f"Successfully wrote {stats['hosts']} hosts with {stats['services']} services "
        f"to project '{project}'"
    )

    return f"Data written to database: {db_path} (project: {project})"
