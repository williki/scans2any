#!/usr/bin/env python

import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from scans2any.main import main

# Define repository paths
REPO_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = REPO_ROOT / "tests/artifacts"


def load_test_calls() -> list[str]:
    test_calls_path = ARTIFACTS_DIR / "test-calls.txt"
    assert test_calls_path.exists(), f"Test calls file not found at {test_calls_path}"
    with open(test_calls_path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


@pytest.mark.parametrize("call", load_test_calls())
def test_artifact(call: str):
    # Parse the command arguments from the test call
    args = call.split()

    # Extract input type, writer format, multi_table & option_str
    input_type = None
    writer_format = "markdown"
    multi_table = False
    option_str = "default"

    # Extract input type from the first argument (starts with --)
    if args and args[0].startswith("--"):
        input_type = args[0][2:]  # Remove leading '--'

    for i, arg in enumerate(args):
        if arg == "-w" and i + 1 < len(args):
            writer_format = args[i + 1]
        elif arg == "--multi-table":
            multi_table = True
            option_str = "multi-table"

    assert input_type, f"Could not determine input type for command: {call}"

    # Expected output file path
    ipv4_prefix = "ipv6_" if "ipv6" in call else ""
    expected_output_path = Path(
        f"{ARTIFACTS_DIR}/{ipv4_prefix}{input_type}_{option_str}.{writer_format}"
    )
    assert expected_output_path.exists(), (
        f"Expected output file not found: {expected_output_path}"
    )

    # Build the command arguments
    cmd_args = [
        f"--{input_type}",
        args[1],
        "-w",
        writer_format,
    ]
    if multi_table:
        cmd_args.append("--multi-table")
    # Include any additional arguments (e.g. -c for columns) (not used in this test)
    for i, arg in enumerate(args):
        if arg == "-c" and i + 1 < len(args):
            cmd_args.extend(["-c", args[i + 1]])

    stdout = StringIO()
    stderr = StringIO()
    stderr.fileno = lambda: 2  # type: ignore[method-assign]  # Mock fileno for os.write

    old_cwd = os.getcwd()
    os.chdir(REPO_ROOT)

    returncode = 0
    try:
        with (
            patch("sys.argv", ["scans2any", *cmd_args]),
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
            patch("os.write"),
        ):
            try:
                main()
            except SystemExit as e:
                returncode = e.code
    except Exception as e:
        returncode = 1
        stderr.write(f"\nException: {e}")
    finally:
        os.chdir(old_cwd)

    assert returncode == 0, (
        f"Command failed: {cmd_args} {call}\nError: {stderr.getvalue()}"
    )

    with open(expected_output_path) as f:
        expected_output = f.read()

    assert stdout.getvalue().strip() == expected_output.strip(), (
        f"Output for '{' '.join(cmd_args)}' doesn't match expected artifact: {expected_output_path}"
    )
