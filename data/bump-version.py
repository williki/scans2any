#!/usr/bin/env python3
"""Version management tool for scans2any.

Replaces bump-version.sh. All version bumping, file updating, and git
tagging is handled here.

Usage:
    uv run data/bump-version.py get                         # print version from pyproject.toml
    uv run data/bump-version.py compute <level>             # print new version, no file changes
    uv run data/bump-version.py bump <level> [--dry-run]    # update files (and optionally git)
"""

import argparse
import logging
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from dunamai import Style, Version

PYPROJECT = Path("pyproject.toml")
MAIN_PY = Path("src/scans2any/main.py")
MANPAGE = Path("data/scans2any.1")


def get_version_from_pyproject() -> str:
    try:
        with PYPROJECT.open("rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (FileNotFoundError, KeyError):
        logging.error("Could not read version from %s", PYPROJECT)
        sys.exit(1)


def compute_new_version(current_base: str, level: str) -> str:
    """Compute the new full version string.

    For major/minor/patch: bumps the component in *current_base* (read from
    pyproject.toml) and appends git distance + commit as metadata.
    For git: uses the version derived purely from git tags (legacy behaviour).
    """
    git_ver = Version.from_git()
    distance = git_ver.distance or 0
    commit = git_ver.commit or "unknown"

    if level == "git":
        return git_ver.serialize(
            style=Style.Pep440, format="{base}.post{distance}+{commit}"
        )

    parts = [int(x) for x in current_base.split(".")]
    while len(parts) < 3:
        parts.append(0)

    if level == "major":
        parts = [parts[0] + 1, 0, 0]
    elif level == "minor":
        parts = [parts[0], parts[1] + 1, 0]
    elif level == "patch":
        parts = [parts[0], parts[1], parts[2] + 1]
    else:
        raise ValueError(f"Unknown bump level: {level}")

    new_base = ".".join(str(p) for p in parts)
    return f"{new_base}.post{distance}+{commit}"


def base_tag(version: str) -> str:
    """Extract major.minor.patch from a version string."""
    m = re.match(r"^(\d+\.\d+\.\d+)", version)
    if not m:
        logging.error("Cannot extract base tag from version: %s", version)
        sys.exit(1)
    return m.group(1)


def replace_in_file(path: Path, old: str, new: str) -> None:
    content = path.read_text()
    updated = content.replace(old, new, 1)
    if updated == content:
        logging.error("String %r not found in %s", old, path)
        sys.exit(1)
    path.write_text(updated)
    logging.info("Updated %s", path)


def run(cmd: list[str]) -> None:
    logging.info("$ %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def cmd_get() -> None:
    print(get_version_from_pyproject())  # noqa: T201


def cmd_compute(level: str) -> None:
    """Print the new version that *would* result from bumping, with no side effects."""
    old_tag = base_tag(get_version_from_pyproject())
    print(compute_new_version(old_tag, level))  # noqa: T201


def cmd_bump(level: str, *, dry_run: bool) -> None:
    old_version = get_version_from_pyproject()
    old_tag = base_tag(old_version)
    new_version = compute_new_version(old_tag, level)
    new_tag = base_tag(new_version)

    logging.info("Version: %s -> %s", old_version, new_version)
    logging.info("Tag:     %s -> %s", old_tag, new_tag)

    # Only update files that embed the base tag when the base tag actually changes.
    if new_tag != old_tag:
        replace_in_file(PYPROJECT, f'version = "{old_tag}"', f'version = "{new_tag}"')
        replace_in_file(MANPAGE, f"Version {old_tag}", f"Version {new_tag}")
    else:
        logging.info(
            "Base tag unchanged (%s) — skipping pyproject.toml and manpage", old_tag
        )

    # Always update __version__ in main.py (carries full git metadata string)
    content = MAIN_PY.read_text()
    updated = re.sub(
        r'__version__ = "[^"]*"', f'__version__ = "{new_version}"', content
    )
    if updated == content:
        logging.error("__version__ not found in %s", MAIN_PY)
        sys.exit(1)
    MAIN_PY.write_text(updated)
    logging.info("Updated %s", MAIN_PY)

    run(["uv", "lock"])

    if dry_run:
        logging.info("Dry run — skipping git commit and tag")
        return

    run(["git", "add", str(PYPROJECT), str(MAIN_PY), str(MANPAGE), "uv.lock"])
    run(["git", "commit", "-m", f"Bump version from {old_version} to {new_version}"])
    run(
        [
            "git",
            "tag",
            "-a",
            f"v{new_tag}",
            "-m",
            f"Bump version from {old_version} to {new_version}",
        ]
    )
    run(["git", "push", "origin", f"v{new_tag}"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="Version management tool for scans2any",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("get", help="Print the current version from pyproject.toml")

    compute_parser = subparsers.add_parser(
        "compute",
        help="Print the new version that would result from bumping (no file changes)",
    )
    compute_parser.add_argument(
        "level",
        choices=["git", "major", "minor", "patch"],
        help="Version component to compute",
    )

    bump_parser = subparsers.add_parser(
        "bump", help="Bump version and update all relevant files"
    )
    bump_parser.add_argument(
        "level",
        choices=["git", "major", "minor", "patch"],
        help="Version component to bump (git = append git distance/commit metadata only)",
    )
    bump_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Update files but skip git commit, tag, and push",
    )

    args = parser.parse_args()

    if args.command == "get":
        cmd_get()
    elif args.command == "compute":
        cmd_compute(args.level)
    elif args.command == "bump":
        cmd_bump(args.level, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
