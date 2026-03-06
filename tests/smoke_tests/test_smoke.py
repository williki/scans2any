import os
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
import yaml

from scans2any.main import main


@pytest.fixture
def test_env():
    """Set up test environment data"""

    class TestEnv:
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent
        data_dir = project_root / "tests/data"

        def run_scans2any(self, args, **kwargs):
            """Run scans2any with the given arguments using the development version"""
            stdout = StringIO()
            stderr = StringIO()
            stderr.fileno = lambda: 2  # type: ignore[method-assign]  # Mock fileno for os.write

            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            try:
                with (
                    patch("sys.argv", ["scans2any", *args]),
                    patch("sys.stdout", stdout),
                    patch("sys.stderr", stderr),
                    patch("os.write"),
                ):
                    try:
                        main()
                        return Result(0, stdout.getvalue(), stderr.getvalue())
                    except SystemExit as e:
                        return Result(e.code, stdout.getvalue(), stderr.getvalue())
            except Exception as e:
                return Result(
                    1, stdout.getvalue(), stderr.getvalue() + f"\nException: {e}"
                )

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


def test_buffer(test_env):
    # ensure MERGE_FILE.yaml exists, so we always write to /tmp/MERGE_FILE.yaml.
    # If it does not exist, create it and remove it later.
    default_mergefile = "MERGE_FILE.yaml"
    cleanup_merge_file = False
    if not os.path.isfile(default_mergefile):
        cleanup_merge_file = True
        Path(default_mergefile).touch()

    # create the input files
    with (
        NamedTemporaryFile(mode="w") as f1,
        NamedTemporaryFile(mode="w") as f2,
        NamedTemporaryFile(mode="w", delete=False) as buffer,
    ):
        f1.write('{ "1.1.1.1":{ "tcp_ports":{ "22":{ "service_names":[ "ssh" ] } } } }')
        f2.write(
            '{ "1.1.1.1":{ "tcp_ports":{ "22":{ "service_names":[ "openssh" ] } } } }'
        )
        f1.flush()
        f2.flush()

        # run command with conflict
        test_env.run_scans2any(
            ["--json", f1.name, f2.name, "--buffer", buffer.name],
        )
        buffer_name = buffer.name

    # edit mergefile
    with open("/tmp/MERGE_FILE.yaml") as f:
        data = yaml.safe_load(f)

    data["manual-merge"][next(iter(data["manual-merge"].keys()))]["tcp_ports"][22][
        "service_names"
    ] = data["manual-merge"][next(iter(data["manual-merge"].keys()))]["tcp_ports"][22][
        "service_names"
    ][0]

    with open("/tmp/MERGE_FILE.yaml", "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    # run command without conflict
    test_env.run_scans2any(
        ["--merge-file", "/tmp/MERGE_FILE.yaml", "--json", buffer_name],
    )

    # the temporary MERGE_FILE.yaml and the BUFFER_FILE.json is removed after
    # the test. Also remove the default MERGE_FILE.yaml, if we created it at the
    # start of the test.
    os.remove("/tmp/MERGE_FILE.yaml")
    os.remove(buffer_name)
    if cleanup_merge_file:
        os.remove(default_mergefile)


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
