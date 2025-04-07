"""Prints a YAML representation of the infrastructure."""

import yaml

from scans2any.internal import Infrastructure, printer
from scans2any.writers.dataframe_creator import create_data_unmerged

NAME = "yaml"
PROPERTIES = {
    "binary": False,
    "ignore-conflicts": False,
}


def write(infra: Infrastructure, args) -> str:
    """
    Convert the internal representation of the infrastructure
    into the yaml format.
    """
    infra.cleanup_names('"\\')

    host_dict = create_data_unmerged(infra, columns=args.columns)

    printer.success(
        f"YAML with {len(host_dict)} hosts has been created from parsed input data"
    )

    # Fixes strange behaviour:
    # https://stackoverflow.com/questions/51272814/python-yaml-dumping-pointer-references
    # yaml.Dumper.ignore_aliases = lambda *args: True
    class NoAliasDumper(yaml.Dumper):
        def ignore_aliases(self, data):
            return True

    return yaml.dump(host_dict, Dumper=NoAliasDumper, indent=4, sort_keys=False)
