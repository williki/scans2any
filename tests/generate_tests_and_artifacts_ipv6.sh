#!/usr/bin/env bash
uv run src/scans2any/main.py -a tests/data/ipv6/aquatone/aquatone_session.json -o tests/artifacts/ipv6_aquatone_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/json/infra.json                -o tests/artifacts/ipv6_json_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/masscan/masscan.json           -o tests/artifacts/ipv6_masscan_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/nessus/                        -o tests/artifacts/ipv6_nessus_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/nmap/                          -o tests/artifacts/ipv6_nmap_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/nxc/                           -o tests/artifacts/ipv6_nxc_default.terminal
uv run src/scans2any/main.py -a tests/data/ipv6/txt/                           -o tests/artifacts/ipv6_txt_default.terminal
