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
    --aquatone tests/data/aquatone/goad-light-aquatone_session.json \
    --bloodhound tests/data/bloodhound/goad-light-north.sevenkingdoms_computers.json \
    --bloodhound tests/data/bloodhound/goad-light-sevenkingdoms_computers.json \
    --masscan tests/data/masscan/goad-light.json \
    --nessus tests/data/nessus/goad-light.nessus \
    --nmap tests/data/nmap/goad-light.xml \
    --nxc tests/data/nxc/goad-light-smb.db'
)
