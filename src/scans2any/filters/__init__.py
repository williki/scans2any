"""
Filters for multiple purposes.
"""

import inspect
import re
from importlib import import_module
from pathlib import Path
from typing import Any

module_files = (
    mod_file for mod_file in Path(__file__).parent.glob("*.py") if mod_file.is_file()
)

avail_filters: list[tuple[str, Any, str]] = []

for mod_file in module_files:
    mod_name = mod_file.stem
    if re.match(r"^(?!__init__$)[a-zA-Z_]*$", mod_name):
        pkg_name = f"{__package__}.{mod_name}"
        try:
            mod = import_module(pkg_name)
            sig = inspect.signature(mod.apply_filter)
            first_param_name = next(iter(sig.parameters))
            avail_filters.append((mod_name, mod, first_param_name))
        except ImportError as e:
            print(f"Failed to import {pkg_name}: {e}")  # noqa: T201
