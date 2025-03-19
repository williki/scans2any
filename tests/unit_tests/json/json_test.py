import argparse

from scans2any.parsers import json_parser
from scans2any.writers import json_writer


# Create json file from data and parse it
# input and output should be the same
def data_ok(data: str):
    # parse the data
    infra = json_parser.parse_string(data)

    # remove Tuple, that store where the info of the os came from
    infra.merge_os_sources()

    args = argparse.Namespace(
        columns=("IP-Addresses", "Hostnames", "Ports", "Services", "Banners", "OS")
    )

    # Create the json from the created infrastructure
    string = json_writer.write(infra, args)

    assert string == data


def test_json():
    for data in test_data:
        data_ok(data)


# Here the data for the object is stored
# It was created from
test_data = [
    # nmap
    r"""{"192.168.1.1":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":["Dropbearsshd"]},"53":{"service_names":["domain"],"banners":["CloudflarepublicDNS"]},"80":{"service_names":["http"],"banners":[""]},"443":{"service_names":["https"],"banners":[""]}},"udp_ports":{},"os":["linux"]},"192.168.1.2":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":["OpenSSH\/9.2p1Debian2"]},"25":{"service_names":["smtp"],"banners":["Postfixsmtpd"]},"53":{"service_names":["domain"],"banners":["ISCBIND\/9.18.16-1~deb12u1"]},"80":{"service_names":["http"],"banners":["nginx\/1.22.1"]},"139":{"service_names":["netbios-ssn"],"banners":["Sambasmbd\/4.6.2"]},"443":{"service_names":["http"],"banners":["nginx\/1.22.1"]},"445":{"service_names":["netbios-ssn"],"banners":["Sambasmbd\/4.6.2"]},"465":{"service_names":["smtp"],"banners":["Postfixsmtpd"]},"993":{"service_names":["imaps"],"banners":[""]},"4000":{"service_names":["ssh"],"banners":[""]},"8080":{"service_names":["http-proxy"],"banners":[""]}},"udp_ports":{},"os":["linux"]},"192.168.1.3":{"hostnames":[],"tcp_ports":{"443":{"service_names":["http"],"banners":["SamsungSyncThruWebService(printer)"]},"631":{"service_names":["http"],"banners":["SamsungSyncThruWebService(printer)"]},"9100":{"service_names":["jetdirect"],"banners":[""]}},"udp_ports":{},"os":[]},"192.168.1.10":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":["OpenSSH\/8.9p1Ubuntu3ubuntu0.3"]},"25":{"service_names":["smtp"],"banners":["Postfixsmtpd"]},"443":{"service_names":["http"],"banners":["Apachehttpd"]}},"udp_ports":{},"os":["linux"]},"192.168.1.11":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":["OpenSSH\/9.0p1Ubuntu1ubuntu8.4"]},"80":{"service_names":["http"],"banners":[""]},"443":{"service_names":["http"],"banners":["nginx\/1.22.0"]},"9999":{"service_names":["abyss"],"banners":[""]}},"udp_ports":{},"os":["linux"]},"192.168.1.12":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":["OpenSSH\/9.3"]},"443":{"service_names":["http"],"banners":["nginx\/1.24.0"]}},"udp_ports":{},"os":["linux"]},"192.168.1.102":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":[""]}},"udp_ports":{},"os":["linux"]},"192.168.1.116":{"hostnames":[],"tcp_ports":{"22":{"service_names":["ssh"],"banners":[""]}},"udp_ports":{},"os":["linux"]}}""",
    # aquatone
    """{"192.168.1.1":{"hostnames":[],"tcp_ports":{"80":{"service_names":["http"],"banners":[""]},"443":{"service_names":["https"],"banners":[""]}},"udp_ports":{},"os":[]},"192.168.1.2":{"hostnames":[],"tcp_ports":{"80":{"service_names":["http"],"banners":["Braceyourself,mergeconflictsahead.|nginx\\/1.22.1"]},"443":{"service_names":["https"],"banners":["nginx\\/1.22.1"]},"8080":{"service_names":["https"],"banners":[""]}},"udp_ports":{},"os":[]},"192.168.1.3":{"hostnames":[],"tcp_ports":{"443":{"service_names":["https"],"banners":[""]},"631":{"service_names":["http"],"banners":[""]}},"udp_ports":{},"os":[]},"192.168.1.10":{"hostnames":[],"tcp_ports":{"443":{"service_names":["https"],"banners":["AllgeierITSolutions,JULIAMailOffice|Apache"]}},"udp_ports":{},"os":[]},"192.168.1.11":{"hostnames":[],"tcp_ports":{"443":{"service_names":["https"],"banners":["FileBrowser|nginx\\/1.22.0(Ubuntu)"]},"9999":{"service_names":["http"],"banners":["FileBrowser"]}},"udp_ports":{},"os":[]},"192.168.1.12":{"hostnames":[],"tcp_ports":{"443":{"service_names":["https"],"banners":["nginx\\/1.24.0|sAURier\\u2013acme'sAURRepository"]}},"udp_ports":{},"os":[]}}""",
]
