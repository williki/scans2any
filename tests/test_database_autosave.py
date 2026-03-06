"""Test database auto-save functionality."""

import os
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scans2any.main import main


def run_scans2any(args: list[str]) -> tuple[int, str, str]:
    """Helper to run scans2any main function directly and capture output."""
    stdout = StringIO()
    stderr = StringIO()
    stderr.fileno = lambda: 2  # type: ignore[method-assign]  # Mock fileno for os.write

    try:
        with (
            patch("sys.argv", ["scans2any", *args]),
            patch("sys.stdout", stdout),
            patch("sys.stderr", stderr),
            patch("os.write"),
        ):  # Mock os.write to avoid writing to actual stderr
            try:
                main()
                return 0, stdout.getvalue(), stderr.getvalue()
            except SystemExit as e:
                return (
                    e.code if isinstance(e.code, int) else 1,
                    stdout.getvalue(),
                    stderr.getvalue(),
                )
    except Exception as e:
        return 1, stdout.getvalue(), stderr.getvalue() + f"\nException: {e}"


def test_database_autosave_with_input_files():
    """Test that database auto-saves when --project is used with input files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            nmap_file = original_cwd / "tests" / "data" / "nmap" / "goad-light.xml"
            project_name = "test-autosave"
            db_file = Path(f"{project_name}.db")

            # Run scans2any with --project and input file
            returncode, _stdout, stderr = run_scans2any(
                [
                    "--nmap",
                    str(nmap_file),
                    "--project",
                    project_name,
                    "-w",
                    "json",
                    "-vv",
                ]
            )

            # Check that the command succeeded
            assert returncode == 0, f"Command failed: {stderr}"

            # Check that database file was created in the temp directory
            assert db_file.exists(), f"Database file {db_file} was not created"

            # Check that "Auto-saving to Database" appears in verbose output
            assert "Auto-saving to Database" in stderr, (
                "Auto-save message not found in verbose output"
            )

            # Verify database contains data
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Check hosts table exists and has data
            cursor.execute("SELECT COUNT(*) FROM hosts")
            host_count = cursor.fetchone()[0]
            assert host_count > 0, "No hosts found in database"

            # Check services table exists and has data
            cursor.execute("SELECT COUNT(*) FROM services")
            service_count = cursor.fetchone()[0]
            assert service_count > 0, "No services found in database"

            conn.close()

        finally:
            os.chdir(original_cwd)


def test_database_no_autosave_when_loading():
    """Test that database does NOT auto-save when only loading from database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            nmap_file = original_cwd / "tests" / "data" / "nmap" / "goad-light.xml"
            project_name = "test-no-autosave"
            db_file = Path(f"{project_name}.db")

            # First, create a database by scanning with --project
            returncode1, _stdout1, _stderr1 = run_scans2any(
                [
                    "--nmap",
                    str(nmap_file),
                    "--project",
                    project_name,
                    "-w",
                    "json",
                ]
            )
            assert returncode1 == 0, "Initial scan failed"
            assert db_file.exists(), "Database not created"

            # Get modification time
            mtime_before = db_file.stat().st_mtime

            # Now load from database only (no input files)
            returncode2, _stdout2, stderr2 = run_scans2any(
                [
                    "--project",
                    project_name,
                    "-w",
                    "json",
                    "-vv",
                ]
            )

            assert returncode2 == 0, f"Database load failed: {stderr2}"

            # Check that "Auto-saving to Database" does NOT appear
            assert "Auto-saving to Database" not in stderr2, (
                "Auto-save should not occur when only loading from database"
            )

            # Check that database was not modified
            mtime_after = db_file.stat().st_mtime
            assert mtime_before == mtime_after, (
                "Database file was modified when it shouldn't have been"
            )

        finally:
            os.chdir(original_cwd)


def test_database_project_isolation():
    """Test that different projects create separate database files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            nmap_file = original_cwd / "tests" / "data" / "nmap" / "goad-light.xml"
            project1 = "project-one"
            project2 = "project-two"

            # Create two projects
            for project in [project1, project2]:
                returncode, _stdout, _stderr = run_scans2any(
                    [
                        "--nmap",
                        str(nmap_file),
                        "--project",
                        project,
                        "-w",
                        "json",
                    ]
                )
                assert returncode == 0, f"Failed to create project {project}"

            # Check that both database files exist
            db1 = Path(f"{project1}.db")
            db2 = Path(f"{project2}.db")

            assert db1.exists(), f"Database {db1} not created"
            assert db2.exists(), f"Database {db2} not created"

            # Verify they are separate files
            assert db1.stat().st_size > 0, f"Database {db1} is empty"
            assert db2.stat().st_size > 0, f"Database {db2} is empty"

            # Verify each database contains data
            for db_file in [db1, db2]:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Check this database has data
                cursor.execute("SELECT COUNT(*) FROM hosts")
                count = cursor.fetchone()[0]
                assert count > 0, f"No hosts found in {db_file}"

                conn.close()

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    test_database_autosave_with_input_files()
    test_database_no_autosave_when_loading()
    test_database_project_isolation()
