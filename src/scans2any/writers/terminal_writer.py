"""Prints a nice Terminal table format of the infrastructure."""

import platform

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_dataframes

NAME = "terminal"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def add_arguments(parser):
    """
    Add table format argument to the parser.
    """
    default_format = "grid" if platform.system() == "Windows" else "fancy_grid"
    parser.add_argument(
        "--table-fmt",
        type=str,
        default=default_format,
        help="Table format for terminal output, see tabulate python package",
    )


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into a nice Terminal table format with fancy_grid format
    using pandas df.to_markdown function.
    """
    infra.sort()

    # For pandoc, we use newline character (\n) as merge symbol
    # with zero-width space to maintain proper alignment
    merge_symbol = "\u200b\n"

    # Create DataFrames
    dfs = create_dataframes(
        infra,
        columns=args.columns,
        multi_table=args.multi_table,
        merge_symbol=merge_symbol,
    )

    # Convert DataFrames to pandoc-compatible tables
    terminal_tables = []
    for df in dfs:
        markdown_table = df.to_markdown(index=False, tablefmt=args.table_fmt)
        terminal_tables.append(markdown_table)

    printer.success("Terminal tables have been created from parsed input data")

    # Separate each host table with extra newlines
    return "\n\n".join(terminal_tables).replace("\u200b", "")  # remove placeholders
