#!/usr/bin/env bash

uv run scans2any \
  --aquatone tests/data/aquatone/goad-light-aquatone_session.json \
  --bloodhound tests/data/bloodhound/goad-light-sevenkingdoms_computers.json \
  --bloodhound tests/data/bloodhound/goad-light-north.sevenkingdoms_computers.json \
  --nessus tests/data/nessus/goad-light.nessus \
  --nmap tests/data/nmap/goad-light.xml \
  --nxc tests/data/nxc/goad-light-smb.db \
  --masscan tests/data/masscan/goad-light.json \
  --txt tests/data/txt/goad-light.txt \
  "$@"
