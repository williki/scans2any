"""Prints a typst representation of the infrastructure."""

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_dataframes

NAME = "typst"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into Typst table format.
    """
    infra.sort()
    infra.cleanup_names("@#{}\\^_$")

    # Create DataFrames
    dfs = create_dataframes(
        infra, columns=args.columns, multi_table=args.multi_table, merge_symbol=" \\ "
    )

    typst_tables = []
    for df in dfs:
        # Create column headers
        headers = "*], [*".join(col for col in df.columns)

        # Create rows
        rows = []
        for _, row in df.iterrows():
            cells = "], [".join(cell for cell in row)
            rows.append(f"[{cells}]")

        rows_str = ",\n  ".join(rows)

        # Build the Typst table
        typst_table = f"""#table(
  columns: ({len(df.columns)}),
  [*{headers}*],
  {rows_str}
)"""
        typst_tables.append(typst_table)

    # Join all tables with spacing
    result = "#set page(flipped: true)\n\n" + "\n\n#pagebreak()\n\n".join(typst_tables)

    printer.success(
        f"Typst tables with {len(dfs)} tables has been created from parsed input data"
    )

    return result
