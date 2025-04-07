#!/usr/bin/env python

from pathlib import Path
from subprocess import run
from sys import executable

import pytest

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

    # Build the command
    cmd = [
        executable,
        "-m",
        "scans2any.main",
        f"--{input_type}",
        args[1],
        "-w",
        writer_format,
    ]
    if multi_table:
        cmd.append("--multi-table")
    # Include any additional arguments (e.g. -c for columns) (not used in this test)
    for i, arg in enumerate(args):
        if arg == "-c" and i + 1 < len(args):
            cmd.extend(["-c", args[i + 1]])

    result = run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"Command failed: {cmd} {call}\nError: {result.stderr}"
    )

    with open(expected_output_path) as f:
        expected_output = f.read()

    assert result.stdout.strip() == expected_output.strip(), (
        f"Output for '{' '.join(cmd)}' doesn't match expected artifact: {expected_output_path}"
    )
