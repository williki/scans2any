from scans2any.helpers.infrastructure import combine_infrastructure_scans
from scans2any.internal import Infrastructure
from scans2any.parsers import json_parser


def test_simple_merge():
    # Three complicated hosts are combined and compared
    infra_a = json_parser.parse_string("""
{
    "192.168.1.1": {
        "hostnames": [
           "host_A"
        ],
        "tcp_ports": {
          "22": {
            "service_names": [
              "ssh"
            ],
            "banners": [
              "Dropbear sshd"
            ]
          }
        },
        "os": [
          "linux"
        ]
    }
}
""")
    infra_b = json_parser.parse_string("""
{
    "192.168.1.1": {
        "tcp_ports": {
          "23": {
            "service_names": [
              "ftp"
            ]
          }
        },
        "os": [
          "windows"
        ]
    }
}
""")
    infra_c = json_parser.parse_string("""
{
    "192.168.1.1": {
        "tcp_ports": {
            "23": {
                "service_names": [
                    "ftp"
                ]
            }
        },
        "os": [
            "windows"
        ]
    }
}
""")
    infra_combi = combine_infrastructure_scans([infra_a, infra_b, infra_c])
    infra_combi.merge_os_sources()
    infra_combi_goal = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames": [
            "host_A"
        ],
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ],
                "banners": [
                    "Dropbear sshd"
                ]
            },
            "23": {
                "service_names": [
                    "ftp"
                ]
            }
        },
        "os": [
            "linux",
            "windows"
        ]
    }
}""")
    infra_combi_goal.merge_os_sources()
    assert infra_combi.__str__() == infra_combi_goal.__str__()


def test_merge_simple():
    # infra_a has services, infra_b has OSinfo, the combination should have both
    infra_a = json_parser.parse_string("""{
    "192.168.1.1": {
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        }
    }
}""")
    infra_a.merge_os_sources()
    infra_b = json_parser.parse_string("""{
    "192.168.1.1": {
        "os":[
            "os_B"
        ]
    }
}""")
    infra_b.merge_os_sources()

    infra_combi = combine_infrastructure_scans([infra_a, infra_b])

    infra_combi_goal = json_parser.parse_string("""{
    "192.168.1.1": {
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        },
        "os": [
            "os_B"
        ]
    }
}""")
    infra_combi_goal.merge_os_sources()

    assert infra_combi.__str__() == infra_combi_goal.__str__()


def test_merge_vote_mix():
    # Nmap gives infrastructure with service and os info, Nessus only has os
    # information. The service info is taken from Nmap and the os info is taken
    # from Nessus
    infra_a = infra_a = json_parser.parse_string("""{
    "192.168.1.1":{
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        },
        "os":[
            "os_A"
        ]
    }
}""")
    infra_a = change_os_identifier(infra_a, "Nmap")

    infra_b = json_parser.parse_string("""{
    "192.168.1.1":{
        "os":[
            "os_B"
        ]
    }
}""")
    infra_b = change_os_identifier(infra_b, "Nessus")

    infra_combi = combine_infrastructure_scans([infra_a, infra_b])
    infra_combi.merge_os_sources()
    infra_combi.auto_merge()

    infra_combi_goal = json_parser.parse_string("""{
        "192.168.1.1": {
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        },
        "os":[
            "os_B"
        ]
        }
    }""")
    infra_combi_goal.merge_os_sources()
    assert infra_combi_goal.__str__() == infra_combi.__str__()


def write_compare(scan: str, goal: str):
    with open("scan.txt", "w") as a:
        a.write(scan.__str__())
    with open("goal.txt", "w") as a:
        a.write(goal)


def test_merge_vote():
    # Nmap says OS is os_A, but Nessus says it's os_B, Nessus has a higher
    # trustworthyness, so os_B is chosen.
    infra_a = json_parser.parse_string("""{
    "192.168.1.1":{
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        },
        "os":[
            "os_A"
        ]
    }
}""")
    infra_a = change_os_identifier(infra_a, "Nmap")

    infra_b = json_parser.parse_string("""{
    "192.168.1.1":{
        "tcp_ports": {
            "22": {
                "service_names": [
                    "open-ssh"
                ]
            }
        },
        "os":[
            "os_B"
        ]
    }
}""")
    infra_b = change_os_identifier(infra_b, "Nessus")

    infra_combi = combine_infrastructure_scans([infra_a, infra_b])
    infra_combi.merge_os_sources()
    infra_combi.auto_merge()

    infra_combi_goal = json_parser.parse_string("""{
    "192.168.1.1":{
        "tcp_ports": {
            "22": {
                "service_names": [
                    "open-ssh",
                    "ssh"
                ]
            }
        },
        "os":[
            "os_B"
        ]
    }
}""")
    infra_combi_goal.merge_os_sources()

    assert infra_combi_goal.__str__() == infra_combi.__str__()


def test_merge_address_name():
    # One host has IP and hostname, the other has the same hostname, but no IP.
    # They are not merged, but kept as separate hosts
    infra_a = json_parser.parse_string("""{
    "192.168.1.1":{
        "hostnames":[
            "host_A"
        ],
        "tcp_ports":{
            "22":{
                "service_names":[
                    "ssh"
                ]
            }
        }
    }
}""")
    # The json parser generates a host with 'None' address, if the address is
    # given as /unknown_\d+/
    infra_b = json_parser.parse_string("""{
    "unknown_0":{
        "hostnames":[
            "host_A"
        ],
        "tcp_ports":{
            "22":{
                "service_names":[
                    "ssh"
                ]
            }
        }
    }
}""")
    infra_combi = combine_infrastructure_scans([infra_a, infra_b])
    infra_combi_not_goal = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames": [
            "host_A"
        ],
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        }
    },
    "unknown_0": {
        "hostnames": [
            "host_X"
        ],
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        }
    }
}
""")
    infra_combi_not_goal.hosts[1].hostnames = set("host_A")
    assert len(infra_combi_not_goal.hosts) == 2
    assert infra_combi.__str__() != infra_combi_not_goal.__str__()
    infra_combi_goal = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames": [
            "host_A"
        ],
        "tcp_ports": {
            "22": {
                "service_names": [
                    "ssh"
                ]
            }
        }
    }
}""")
    assert infra_combi.__str__() == infra_combi_goal.__str__()


def change_os_identifier(infra: Infrastructure, identifier: str) -> Infrastructure:
    for host_index, host in enumerate(infra.hosts):
        host_os = list(host.os)
        for index, item in enumerate(host_os):
            host_os[index] = (item[0], identifier)
        host.os = set(host_os)
        infra.hosts[host_index] = host
    return infra


def test_merge_differing_dns():
    # two hosts have different services and different hostnames, but because
    # they have the same ip, they are merged.
    infra_a = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames":[
            "host_A"
        ],
        "tcp_ports": {
            "22":{
                "servce_name":[
                    "ssh"
                ]
            }
        }
    }
}""")
    infra_b = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames": [
            "host_B"
        ],
        "tcp_ports": {
            "23": {
                "servce_name": [
                    "ftp"
                ]
            }
        }
    }
}""")
    infra_combi = combine_infrastructure_scans([infra_a, infra_b])
    infra_combi_goal = json_parser.parse_string("""{
    "192.168.1.1": {
        "hostnames": [
            "host_A",
            "host_B"
        ],
        "tcp_ports": {
            "22": {
                "servce_name": [
                    "ssh"
                ]
            },
            "23": {
                "servce_name": [
                    "ftp"
                ]
            }
        }
    }
}""")
    assert infra_combi.__str__() == infra_combi_goal.__str__()


if __name__ == "__main__":
    # test_merge_vote()
    test_merge_differing_dns()
