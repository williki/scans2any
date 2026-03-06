import pytest
from pydantic import ValidationError

from scans2any.internal import Host, Infrastructure, Service, SortedSet


def test_service_creation():
    s = Service(
        port=80,
        protocol="tcp",
        service_names=SortedSet(["http"]),
        banners=SortedSet(["Apache"]),
    )
    assert s.port == 80
    assert "http" in s.service_names


def test_host_creation():
    h = Host(address={"192.168.1.1"}, hostnames=set(), os=set())
    assert "192.168.1.1" in h.address


def test_host_validation():
    with pytest.raises(ValidationError):
        Host(address=set(), hostnames=set(), os=set())


def test_infrastructure_creation():
    infra = Infrastructure(identifier="test")
    assert infra.identifier == "test"
    assert infra.hosts == []


def test_infrastructure_add_host():
    infra = Infrastructure()
    h = Host(address={"1.1.1.1"}, hostnames=set(), os=set())
    infra.add_host(h)
    assert len(infra.hosts) == 1
    assert infra.hosts[0].address == {"1.1.1.1"}
