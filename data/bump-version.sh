#!/usr/bin/bash

# This script bumps the version number in the package.json file. Using
# uvx dunamai bump <part> will bump the version number in the package.json file
# and commit the change to the git repository.
# It will replace the version number in the package.json file with the new version number
# as well as in src/scans2any/main.py and data/scan2any.1

set -euo pipefail

# Check that $1 is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <part> [dry-run]"
    echo "  part: major, minor, patch, git"
    exit 1
fi

OLD_VERSION=$(uv run data/bump-version.py get)
NEW_VERSION=$(uv run data/bump-version.py bump "$1")

echo "Version $OLD_VERSION -> $NEW_VERSION"

# Extract only major.minor.patch from version (in case it has additional labels)
OLD_TAG=$(echo "$OLD_VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')
NEW_TAG=$(echo "$NEW_VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')
echo "Tag: $OLD_TAG -> $NEW_TAG"

# Update version in pyproject.toml
sed -i "s/version = \"$OLD_TAG\"/version = \"$NEW_TAG\"/" pyproject.toml

# Update version in src/scans2any/main.py
sed -i 's/__version__ = "[^"]*"/__version__ = "'$NEW_VERSION'"/' src/scans2any/main.py

# Update version in manpage
sed -i "s/Version $OLD_TAG/Version $NEW_TAG/" data/scans2any.1

uv lock

# Check if second argument exists and is "dry-run"
if [ -n "${2:-}" ] && [ "$2" = "dry-run" ]; then
    echo "Dry run, not committing changes"
    exit 0
fi

git add pyproject.toml src/scans2any/main.py data/scans2any.1 uv.lock
git commit -m "Bump version from $OLD_VERSION to $NEW_VERSION"
git tag -a "v$NEW_TAG" -m "Bump version from $OLD_VERSION to $NEW_VERSION"
git push origin "v$NEW_TAG"
