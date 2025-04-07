import argparse

from scans2any.parsers import (
    aquatone_parser,
    bloodhound_parser,
    json_parser,
    masscan_parser,
    nessus_parser,
    nmap_parser,
)
from scans2any.writers import json_writer


def test_json_from_masscan():
    for filename in [
        "tests/data/masscan/goad-mini.json",
    ]:
        data_ok(filename, masscan_parser.parse)


def test_json_from_nmap():
    for filename in [
        "tests/data/nmap/goad-light.xml",
        "tests/data/nmap/goad-mini-incomplete.xml",
        "tests/data/nmap/goad-mini.xml",
    ]:
        data_ok(filename, nmap_parser.parse)


def test_json_from_bloodhound():
    for filename in [
        "tests/data/bloodhound/goad-light-north.sevenkingdoms_computers.json",
        "tests/data/bloodhound/goad-light-sevenkingdoms_computers.json",
        "tests/data/bloodhound/goad-mini-computers.json",
    ]:
        data_ok(filename, bloodhound_parser.parse)


def test_json_from_nessus():
    for filename in [
        "tests/data/nessus/goad-light.nessus",
        "tests/data/nessus/goad-mini.nessus",
    ]:
        data_ok(filename, nessus_parser.parse)


def test_json_from_aquatone():
    data_ok(
        "tests/data/aquatone/goad-mini-aquatone_session.json", aquatone_parser.parse
    )


# Parse the infrastructure from filename using the provided parser. Then we send
# it through the json writer, giving us a json string, which we send through the
# json parser, that output we send through the writer again, giving us another
# json string. This will give us two json strings, that should have the same
# value. Their equality is asserted.
#
# This is done for different scans and associated parsers in the test functions
# above.
def data_ok(filename: str, parser):
    # use provided parser to read the file into an infrastructure
    mas_infra = parser(filename)
    mas_infra.merge_os_sources()
    mas_infra.sort()

    args = argparse.Namespace(
        columns=("IP-Addresses", "Hostnames", "Ports", "Services", "Banners", "OS")
    )

    # turn that infrastructure into a json string
    json_string = json_writer.write(mas_infra, args)

    json_infra = json_parser.parse_string(json_string)
    json_infra.merge_os_sources()
    json_infra.sort()

    # after another transformation back to json, we should arrive at the same
    # output as the first json string
    json_string2 = json_writer.write(json_infra, args)
    assert json_string == json_string2
