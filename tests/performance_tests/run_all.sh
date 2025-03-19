#!/usr/bin/env bash

# Execute all performance tests and export results to JSON

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

(
    cd "$SCRIPT_DIR"
    for benchmark in test_*.sh; do
        echo "Running $benchmark"
        bash "$benchmark" --export-json "$SCRIPT_DIR/$benchmark-results.json"
        echo "Results exported to $SCRIPT_DIR/$benchmark-results.json"
    done
)
