"""Prints a Markdown representation of the infrastructure."""

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_dataframes, create_flat_dataframe

NAME = "markdown"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def add_arguments(parser):
    """
    Add flattened argument to the parser.
    """
    parser.add_argument(
        "--flattened",
        action="store_true",
        default=False,
        help="Creates flattened table format",
    )
    parser.add_argument(
        "--merge-symbol",
        type=str,
        default="<br>",
        help="Merge symbol for columns with multiple values",
    )


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into a Markdown table.
    """
    infra.cleanup_names("~#_{}*`\\|")

    # Create DataFrames from the internal infrastructure object
    dfs = create_dataframes(
        infra,
        columns=args.columns,
        multi_table=args.multi_table,
        merge_symbol=args.merge_symbol,
    )

    if args.flattened:
        # Create a flattened DataFrame (one row per service)
        df = create_flat_dataframe(infra, columns=args.columns, merge_symbol="\n")
        markdown_table = df.to_markdown(index=False)
        printer.success(f"Markdown table created with {len(df)} rows")
        return markdown_table

    # Convert DataFrames to markdown tables
    markdown_tables = []
    for df in dfs:
        markdown_table = df.to_markdown(index=False)
        markdown_tables.append(markdown_table)

    printer.success("Markdown tables have been created from parsed input data")

    # Separate each host table with extra newlines
    return "\n\n\n".join(markdown_tables)
