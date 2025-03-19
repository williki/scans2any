from pathlib import Path
from subprocess import run
from sys import executable
from tempfile import NamedTemporaryFile

import pytest


@pytest.fixture
def test_env():
    """Set up test environment data"""

    class TestEnv:
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent
        data_dir = project_root / "tests/data"

        def get_scans2any_command(self):
            """Get the command to run scans2any from the development directory"""
            return [executable, "-m", "scans2any.main"]

        def run_scans2any(self, args, **kwargs):
            """Run scans2any with the given arguments using the development version"""
            cmd = self.get_scans2any_command() + args
            return run(cmd, **kwargs)

    return TestEnv()


def test_help_command(test_env):
    """Test that the help command runs without errors"""
    result = test_env.run_scans2any(["-h"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage: scans2any" in result.stdout


def test_version_command(test_env):
    """Test that the version command runs without errors"""
    result = test_env.run_scans2any(["--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "scans2any v." in result.stdout


def test_process_json_input(test_env):
    """Test that a simple JSON input can be processed"""
    json_file = test_env.data_dir / "json/simple.json"
    result = test_env.run_scans2any(
        ["--json", str(json_file)], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "1.1.1.1" in result.stdout
    assert "22/tcp" in result.stdout


@pytest.mark.parametrize("fmt", ["json", "yaml", "csv", "markdown", "html"])
def test_output_formats(test_env, fmt):
    """Test that different output formats work"""
    json_file = test_env.data_dir / "json/simple.json"

    with NamedTemporaryFile(suffix=f".{fmt}") as tmp:
        result = test_env.run_scans2any(
            ["--json", str(json_file), "-w", fmt, "-o", tmp.name],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed with format {fmt}: {result.stderr}"

        # Check that output file exists and is not empty
        assert Path(tmp.name).exists()
        assert Path(tmp.name).stat().st_size > 0


def test_filter_application(test_env):
    """Test that filters can be applied"""
    json_file = test_env.data_dir / "json/filter_test.json"

    # Test with and without filter
    result_without_filter = test_env.run_scans2any(
        ["--json", str(json_file), "--disable-filters", "empty_host"],
        capture_output=True,
        text=True,
    )

    result_with_filter = test_env.run_scans2any(
        ["--json", str(json_file), "--enable-filters", "empty_host"],
        capture_output=True,
        text=True,
    )

    assert result_without_filter.returncode == 0
    assert result_with_filter.returncode == 0

    # The empty_hosts filter should remove hosts without ports
    # so the output should be different
    assert result_without_filter.stdout != result_with_filter.stdout


def test_combine_multiple_inputs(test_env):
    """Test that multiple inputs can be combined"""
    json_file1 = test_env.data_dir / "json/input1.json"
    json_file2 = test_env.data_dir / "json/input2.json"

    result = test_env.run_scans2any(
        ["--json", str(json_file1), "--json", str(json_file2)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Both IPs should be present in the output
    assert "1.1.1.1" in result.stdout
    assert "2.2.2.2" in result.stdout
