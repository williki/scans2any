import os
from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest

from scans2any.parsers import merge_file_parser, nessus_parser, nmap_parser


@pytest.fixture
def test_env():
    """Set up test environment data"""

    class TestEnv:
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent
        data_dir = project_root / "tests/data"

    return TestEnv()


def expected_output(goalfile: str):
    """Get expected output from file or update it in healing mode"""
    script_path = Path(__file__).parent
    output_path = script_path / Path("expected-outputs") / (goalfile + ".txt")

    # If we're in healing mode, we return None to signal that
    # the test should update the expected output
    if os.environ.get("HEAL_TESTS") == "1":
        return None, output_path

    # Normal mode: read and return the expected output
    with output_path.open() as f:
        return f.read(), None


def assert_or_heal(actual_output: str, goalfile: str):
    """Compare output with expected or update the expected output in healing mode"""
    expected, output_path = expected_output(goalfile)

    if expected is None and output_path is not None:
        # Healing mode: update the expected output
        output_path.parent.mkdir(exist_ok=True)
        with output_path.open("w") as f:
            f.write(actual_output)
    else:
        # Normal mode: compare with expected output
        assert actual_output == expected


def test_merge_file_parser(test_env):
    infra, _ = merge_file_parser.parse(test_env.data_dir / "MERGE_FILE.yaml")
    infra.sort()
    assert_or_heal(str(infra), "MERGE_FILE.yaml")


def test_nmap_parser_complete(test_env):
    """
    Complete scan: all hosts and services are present.
    """
    infra = nmap_parser.parse(test_env.data_dir / "nmap/goad-light.xml")
    infra.merge_os_sources()
    infra.sort()
    assert_or_heal(infra.__repr__(), "goad-light.xml")


def test_nmap_parser_incomplete(test_env):
    """
    Incomplete scan: missing closing tag but hosts should be intact.
    """
    infra = nmap_parser.parse(test_env.data_dir / "nmap/goad-mini-incomplete.xml")
    infra.merge_os_sources()
    infra.sort()
    assert_or_heal(str(infra), "goad-light-incomplete.xml")


def test_nmap_parser_corrupted(test_env):
    """
    Corrupted scan: expect parsing exception.
    """
    with pytest.raises(UnicodeDecodeError):
        infra = nmap_parser.parse(test_env.data_dir / "nmap/goad-mini-corrupted.xml")
        infra.sort()


def test_nessus_parser_valid(test_env):
    """
    Valid Nessus scan parsing.
    """
    infra = nessus_parser.parse(test_env.data_dir / "nessus/goad-light.nessus")
    infra.sort()
    assert_or_heal(str(infra), "goad-light.nessus")


def test_nessus_parser_corrupted(test_env):
    """
    Corrupted Nessus XML should raise an exception.
    """
    with pytest.raises(ParseError):
        _ = nessus_parser.parse(test_env.data_dir / "nessus/goad-mini-corrupted.nessus")
