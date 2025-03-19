#!/usr/bin/env python3

import argparse

import tomli
from dunamai import Style, Version


def get_version():
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject = tomli.load(f)
        return pyproject.get("project", {}).get("version", "unknown")
    except (FileNotFoundError, KeyError):
        return "unknown"


def bump_version(level):
    version = Version.from_git()
    if level == "major":
        version = version.bump(index=0)
    elif level == "minor":
        version = version.bump(index=1)
    elif level == "patch":
        version = version.bump(index=2)
    elif level == "git":
        pass  # No need to bump, just use git version
    else:
        raise ValueError(f"Unknown bump level: {level}")
    return version.serialize(
        style=Style.Pep440, format="{base}.post{distance}+{commit}"
    )


def main():
    parser = argparse.ArgumentParser(description="Version management tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    _ = subparsers.add_parser("get", help="Get the current version")

    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "level",
        choices=["git", "major", "minor", "patch"],
        help="Version level to bump",
    )

    args = parser.parse_args()

    if args.command == "get":
        print(get_version())  # noqa
    elif args.command == "bump":
        print(bump_version(args.level))  # noqa
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
