#!/usr/bin/env python3

"""
Utility script to regenerate the expected output files used by unit tests.

This script can be used to update all expected outputs or specific ones.

Usage:
  python tests/heal_test_data.py              # Update all expected outputs
  python tests/heal_test_data.py file1 file2  # Update specific outputs

You can also set HEAL_TESTS=1 when running pytest to automatically
update failing test data:
  HEAL_TESTS=1 pytest tests/unit_tests/test_parsers.py
"""

import argparse
import sys
from os import environ
from pathlib import Path
from subprocess import run

from scans2any.internal import printer

# Add the project root to the path so we can import test modules
project_root = Path(__file__).parent.parent.parent
unit_test_dir = project_root / "tests" / "unit_tests"
sys.path.insert(0, str(project_root))


def heal_expected_output(module_path: str, test_name: str | None = None) -> list[str]:
    """
    Execute tests with pytest and generate expected output files.

    Args:
        module_path: Path to the test module (e.g. 'tests/unit_tests/test_parsers.py')
        test_name: Optional specific test function to run

    Returns:
        List of paths to updated files
    """
    # Set environment variable to activate healing mode
    env = environ.copy()
    env["HEAL_TESTS"] = "1"

    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest"]

    # Add specific test if provided
    if test_name:
        pytest_cmd.append(f"{module_path}::{test_name}")
    else:
        pytest_cmd.append(module_path)

    # Add -v for more verbose output
    pytest_cmd.append("-v")

    printer.info(f"Running: {' '.join(pytest_cmd)}")

    # Run pytest with the healing environment variable
    try:
        result = run(
            pytest_cmd,
            env=env,
            text=True,
            capture_output=True,
        )

        # Extract test names that were run
        test_names = []
        for line in result.stdout.split("\n"):
            if "PASSED" in line and "::" in line:
                test_name = line.split("::")[1].split()[0]
                test_names.append(test_name)

        # Print output for visibility
        printer.info(result.stdout)
        if result.stderr:
            printer.error(f"Errors: {result.stderr}")

        return test_names
    except Exception as e:
        printer.failure(f"Error running pytest: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Regenerate expected test outputs")
    parser.add_argument(
        "tests", nargs="*", help="Specific test names to heal (default: all)"
    )
    args = parser.parse_args()

    # Default test modules to heal
    modules = [
        f"{unit_test_dir}/test_parsers.py",
        f"{unit_test_dir}/test_filters.py",
        # Add more test modules here as needed
    ]

    if args.tests:
        # Heal specific tests
        for test_name in args.tests:
            for module_path in modules:
                printer.section(f"Healing test: {test_name} in {module_path}")
                healed = heal_expected_output(module_path, test_name)
                if healed:
                    printer.success(f"Healed test: {test_name}")
                    break
            else:
                printer.warning(f"Test not found: {test_name}")
    else:
        # Heal all tests in all modules
        for module_path in modules:
            printer.section(f"Healing all tests in {module_path}")
            healed = heal_expected_output(module_path)
            printer.success(f"Healed {len(healed)} tests in {module_path}")


if __name__ == "__main__":
    main()
