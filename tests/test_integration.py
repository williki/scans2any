import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from scans2any.main import main

REPO_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = REPO_ROOT / "tests/artifacts"


def load_test_calls() -> list[str]:
    test_calls_path = ARTIFACTS_DIR / "test-calls.txt"
    if not test_calls_path.exists():
        return []
    with open(test_calls_path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


@pytest.mark.parametrize("call", load_test_calls())
def test_cli_snapshot(call: str, snapshot):
    args = call.split()

    stdout = StringIO()

    # We need to change cwd to REPO_ROOT because some tests might use relative paths
    old_cwd = os.getcwd()
    os.chdir(REPO_ROOT)

    try:
        with patch("sys.argv", ["scans2any", *args]), patch("sys.stdout", stdout):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0
    finally:
        os.chdir(old_cwd)

    assert stdout.getvalue() == snapshot
