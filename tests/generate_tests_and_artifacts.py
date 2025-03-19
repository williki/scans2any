#!/usr/bin/env python3

"""
Generate and execute all possible combinations of single input file types and
output writers.

This script will:
1. Find one sample file for each input type in the tests/data directory
2. Execute scans2any with each sample file for all writers
3. Test all combinations of extra format options (currently only --multi-table)
4. Save the outputs as well as stderr to an artifacts directory
"""

import argparse
import subprocess
import time
from pathlib import Path
from sys import executable

from scans2any.internal import printer
from scans2any.writers import avail_writers


def get_scans2any_command():
    """Get the command to run the non system-wide installed version of scans2any"""
    return [executable, "-m", "scans2any.main"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print debug messages",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except the summary",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing artifacts without asking",
    )
    parser.add_argument(
        "-a",
        "--artifacts-dir",
        type=Path,
        default=Path(__file__).parent / "artifacts",
        help="Directory to save the artifacts",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Directory with sample files",
    )
    parser.add_argument(
        "-s",
        "--store-test-calls",
        action="store_true",
        help="Store all calls to scans2any in a file 'test-calls.txt",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Define directories
    project_root = Path(__file__).parent.parent
    data_dir = args.data_dir
    artifacts_dir = args.artifacts_dir

    # Create artifacts directory if it doesn't exist
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        printer.logging.getLogger().setLevel(printer.logging.DEBUG)
    elif args.quiet:
        printer.logging.getLogger().setLevel(printer.logging.WARNING)

    # Check if artifacts directory is not empty
    if any(artifacts_dir.iterdir()) and not args.force:
        printer.warning(f"Artifacts directory ({artifacts_dir}) is not empty!")
        response = input(
            "      Do you want to continue and potentially overwrite files? (y/N): "
        ).lower()
        if response != "y":
            printer.info("Exiting without generating artifacts")
            return

    # Input types and their file extensions
    input_types = {
        "nmap": [".xml"],
        "aquatone": [".json", ".txt"],
        "nessus": [".nessus"],
        "masscan": [".json"],
        "txt": [".txt"],
        "json": [".json"],
        "bloodhound": [".json"],
        "nxc": [".db"],
    }

    scans2any_cmd = get_scans2any_command()
    writers = sorted([obj.NAME for obj in avail_writers])
    writers.remove("excel")  # Skip excel writer, as it is not reproducible
    options_combinations = [
        [],
        ["--multi-table"],
    ]
    # Find one sample file for each input type
    sample_files = {}
    for input_type, extensions in input_types.items():
        type_dir = (
            data_dir / input_type if (data_dir / input_type).exists() else data_dir
        )

        if type_dir.exists():
            for ext in extensions:
                files = sorted(list(type_dir.glob(f"*{ext}")))
                if files:
                    sample_files[input_type] = files[0]
                    break

    printer.info(
        f"Found {len(sample_files)} sample files: {
            ', '.join(
                str(file_path.relative_to(project_root))
                for input_type, file_path in sample_files.items()
            )
        }"
    )
    printer.info(f"Testing with writers: {', '.join(writers)}")

    total_tests = len(sample_files) * len(writers) * len(options_combinations)
    printer.info(f"Total tests to run: {total_tests}")

    # Generate all test calls upfront if requested
    if args.store_test_calls:
        test_calls_file = Path(artifacts_dir / "test-calls.txt")
        if test_calls_file.exists():
            printer.warning("test-calls.txt already exists!")
            response = input("Do you want to overwrite it? (y/N): ").lower()
            if response != "y":
                printer.info("Exiting without generating artifacts")
                return

        # Generate all test calls
        all_test_calls = []
        for input_type, file_path in sorted(sample_files.items()):
            for writer in writers:
                for options in options_combinations:
                    # Only include the arguments, not the command
                    # Use relative path from project_root
                    relative_path = file_path.relative_to(project_root)
                    cmd_args = [
                        f"--{input_type}",
                        str(relative_path),
                        "-w",
                        writer,
                        *options,
                    ]
                    all_test_calls.append(" ".join(cmd_args))

        # Write all test calls at once
        with test_calls_file.open("w") as f:
            f.write("\n".join(all_test_calls))

        printer.info(f"Generated {len(all_test_calls)} test calls in test-calls.txt")

    # Run all combinations
    test_count = 0
    success_count = 0
    error_count = 0
    printer.section("Generating artifacts")
    start_time = time.time()

    for input_type, file_path in sample_files.items():
        for writer in writers:
            for options in options_combinations:
                test_count += 1
                option_str = (
                    "_".join(opt.replace("--", "") for opt in options)
                    if options
                    else "default"
                )
                output_file = artifacts_dir / f"{input_type}_{option_str}.{writer}"
                stderr_file = output_file.as_posix() + ".stderr"

                cmd = [
                    *scans2any_cmd,
                    f"--{input_type}",
                    str(file_path),
                    "-w",
                    writer,
                    *options,
                    "-o",
                    str(output_file),
                ]

                cmd_str = " ".join(cmd)
                try:
                    test_start_time = time.time()
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
                    elapsed_time = time.time() - test_start_time

                    with open(stderr_file, "w") as f:
                        f.write(result.stderr)

                    if result.returncode == 0:
                        printer.success(f"Run #{test_count}: {cmd_str} -> Success")
                    else:
                        printer.warning(
                            f"Run #{test_count}: {cmd_str} -> Error ({result.returncode})"
                        )
                        printer.debug(result.stderr)
                    printer.debug(f"Runtime: {elapsed_time:.2f}s")
                    printer.debug(f"Output File: {output_file}\n")

                    if result.returncode == 0:
                        success_count += 1
                    else:
                        error_count += 1

                except subprocess.TimeoutExpired:
                    printer.warning(f"{cmd_str} -> Timeout after 20 seconds")
                    error_count += 1

                except Exception as e:
                    printer.warning(f"{cmd_str} -> Exception: {e!s}")
                    error_count += 1

    # Write summary
    printer.section("Summary")
    printer.info(f"Total tests: {test_count}")
    printer.info(f"Successful: {success_count}")
    printer.info(f"Errors: {error_count}")
    printer.info(f"Total runtime: {time.time() - start_time:.2f}s")
    printer.info(f"Artifacts saved in: {artifacts_dir}")


if __name__ == "__main__":
    main()
