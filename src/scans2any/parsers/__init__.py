"""
Writers for different output formats.
"""

import re
from importlib import import_module
from pathlib import Path
from typing import Any

module_files = (
    mod_file
    for mod_file in Path(__file__).parent.glob("*_parser.py")
    if mod_file.is_file()
)

avail_parsers: dict[str, Any] = {}

for mod_file in module_files:
    mod_name = mod_file.stem
    if re.match(r"^[a-zA-Z]+_parser$", mod_name):
        pkg_name = f"{__package__}.{mod_name}"
        try:
            mod = import_module(pkg_name)
            avail_parsers[mod_name] = mod
        except ImportError as e:
            print(f"Failed to import {pkg_name}: {e}")  # noqa: T201
