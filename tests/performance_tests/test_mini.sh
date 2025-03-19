#!/usr/bin/env bash

set -e

# Check if hyperfine is installed
if ! command -v hyperfine >/dev/null 2>&1; then
    echo "Error: 'hyperfine' is not installed. Please install it to proceed." >&2
    exit 1
fi

# Run hyperfine from project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

(
    cd "$SCRIPT_DIR/../.."
    hyperfine --warmup 1 "$@" 'uv run scans2any \
    --aquatone tests/data/aquatone/goad-mini-aquatone_session.json \
    --bloodhound tests/data/bloodhound/goad-mini-computers.json \
    --masscan tests/data/masscan/goad-mini.json \
    --nmap tests/data/nmap/goad-mini.xml \
    --nxc tests/data/nxc/goad-mini-smb.db'
)
