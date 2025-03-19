"""Prints a HTML representation of the infrastructure."""

from textwrap import dedent

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_dataframes

NAME = "html"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into HTML format.
    """
    infra.sort()
    infra.cleanup_names("&<>\"'")

    # Create DataFrames
    dfs = create_dataframes(
        infra, columns=args.columns, multi_table=args.multi_table, merge_symbol="<br>"
    )

    # Convert DataFrames to HTML tables
    html_tables = []
    for df in dfs:
        html_table = df.to_html(
            index=False,
            classes="table table-striped table-hover",
            escape=False,  # Since we've already escaped characters
        )
        html_tables.append(html_table)

    content = "\n".join(
        [f'<div class="container">{table}</div>' for table in html_tables]
    )

    printer.success(
        f"HTML with {len(dfs)} tables has been created from parsed input data"
    )

    return __make_full_html_document(content)


def __make_full_html_document(content: str) -> str:
    html_doc = dedent(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>scans2any</title>
            <style>
                .table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .table th, .table td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                .table-striped tbody tr:nth-of-type(odd) {{ background-color: #f9f9f9; }}
                .table-hover tbody tr:hover {{ background-color: #f5f5f5; }}
                .container {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <h1>scans2any</h1>
            {content}
        </body>
        </html>""").replace("\\n", "<br>")

    return html_doc
