"""Prints a JSON representation of the infrastructure."""

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_dataframe_unmerged

NAME = "json"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into the JSON format.
    """

    df = create_dataframe_unmerged(infra, columns=args.columns)

    # to_json does implicit escaping
    json_output = df.to_json(index=False)

    printer.success(
        f"JSON with {len(json_output)} lines has been created from parsed input data"
    )
    return json_output
