"""
File processing utilities for scans2any.
"""

import concurrent.futures
import os

from tqdm import tqdm

from scans2any.helpers.utils import is_special_fd
from scans2any.internal import Infrastructure, printer
from scans2any.parsers import avail_parsers


def process_file(parser_func, filename, progress_bar=None):
    """Process a single file with the given parser function."""
    try:
        return parser_func(filename)
    except Exception as e:
        if progress_bar:
            progress_bar.write(printer.warning(e, return_msg=True))
        return None


def create_progress_bar(*, quiet=False) -> tqdm:
    """Create a standardized progress bar."""
    return tqdm(
        ascii=" ▁▂▃▄▅▆▇█",
        colour="green",
        position=0,
        leave=True,
        disable=quiet,
    )


def process_scan_files(
    executor: concurrent.futures.ThreadPoolExecutor,
    files: list[str],
    parser_func,
    scan_type: str,
    *,
    quiet: bool = False,
) -> list[Infrastructure]:
    """Process scan files with progress bar and return infrastructure objects."""
    if not files:
        return []

    pbar = create_progress_bar(quiet=quiet)
    pbar.total = len(files)
    pbar.set_description(f"Parsing {scan_type} scans")
    futures = {executor.submit(process_file, parser_func, f, pbar): f for f in files}

    results: list[Infrastructure] = []
    error_files: list[str] = []
    successful: int = 0
    hosts: int = 0

    try:
        for future in concurrent.futures.as_completed(futures):
            filename = futures[future]
            result = future.result()
            if result:
                results.append(result)
                successful += 1
                hosts += len(result.hosts)
            else:
                error_files.append(filename)
                pbar.write(
                    printer.error(
                        f"Failed to parse {scan_type} scan: {filename}", return_msg=True
                    )
                )
            pbar.update(1)
    finally:
        pbar.close()

    errors = len(error_files)
    if errors > 0:
        printer.warning(
            f"Parsing of {len(files)} {scan_type} scans: {successful} "
            f"successful, {errors} with errors:"
        )
        for f in error_files:
            printer.warning(f"  - {f}")

    printer.success(
        f"Succesfull parsed {successful} {scan_type} scan(s) with {hosts} hosts."
    )
    return results


def parse_input_files(
    args,
    parser,
    executor: concurrent.futures.ThreadPoolExecutor,
) -> list[Infrastructure]:
    """Parse all input files based on command line arguments."""
    input_args = {}

    # Get scan_group from parser
    scan_group = next(
        (
            group
            for group in parser._action_groups
            if group.title.startswith("input files")
        ),
        None,
    )

    # Check if any input file argument is provided and get name and value
    provided = False
    if scan_group:
        for action in scan_group._group_actions:
            value = getattr(args, action.dest, None)
            if value is not None:
                input_args[str(action.dest)] = value
                provided = True

    if not provided:
        parser.error("At least one input file argument must be provided.")

    def find_all_files(paths: list | str, fileextensions: list[str]) -> list[str]:
        def find_all_files_from_path(
            path: str, fileextensions: list[str], *, toplevel: bool = True
        ) -> list[str]:
            if os.path.isfile(path):
                if toplevel:
                    return [path]
                for extension in fileextensions:
                    if path.endswith(extension):
                        return [path]
                return []
            elif is_special_fd(path):
                return [path]
            output = []
            if os.path.isdir(path):
                for f in os.listdir(path):
                    output += find_all_files_from_path(
                        os.path.join(path, f), fileextensions, toplevel=False
                    )
            return output

        def flatten_list(nested_list):
            flat_list = []
            for item in nested_list:
                if isinstance(item, list):
                    flat_list.extend(flatten_list(item))
                else:
                    flat_list.append(item)
            return flat_list

        paths = flatten_list(paths)
        output = []
        for path in paths:
            output += find_all_files_from_path(path, fileextensions)
        return output

    all_infras = []

    # Process each input type if provided
    for input_type, files in input_args.items():
        if not files:
            continue

        # For provided types with dedicated parser modules use the CONFIG from the parser
        parser_name = f"{input_type}_parser"
        if parser_name not in avail_parsers:
            printer.warning(f"No parser available for {input_type} reports. Skipping.")
            continue

        config = avail_parsers[parser_name].CONFIG
        printer.section(f"Parsing {input_type.capitalize()} Reports")

        input_files = find_all_files(files, config["extensions"])

        all_infras += process_scan_files(
            executor=executor,
            files=input_files,
            parser_func=avail_parsers[parser_name].parse,
            scan_type=input_type,
            quiet=args.quiet,
        )

    return all_infras
