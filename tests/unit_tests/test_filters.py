import copy
import textwrap
from types import SimpleNamespace

from scans2any import filters
from scans2any.filters import column_filter
from scans2any.internal import Host, Infrastructure, Service, SortedSet

#  Test Infrastructure

host = Host(
    address=SortedSet(["127.0.0.1"]),
    hostnames=SortedSet(["localhost"]),
    os=SortedSet(["linux"]),
)

service_1 = Service(
    port=22,
    protocol="tcp",
    service_names=SortedSet(["ssh"]),
    banners=SortedSet(["OpenSSH 1.0"]),
)
service_2 = Service(
    port=80,
    protocol="tcp",
    service_names=SortedSet(["http", "www"]),
    banners=SortedSet(["Apache Web Server"]),
)
service_3 = Service(
    port=443,
    protocol="tcp",
    service_names=SortedSet(["https"]),
    banners=SortedSet(["Apache Web Server"]),
)
service_4 = Service(
    port=1111,
    protocol="udp",
    service_names=SortedSet(["unknown"]),
    banners=SortedSet(["Ok Banner", "", "unknown"]),
)
host.add_services([service_1, service_2, service_3, service_4])

infra = Infrastructure([host], "Test Infrastructure")

assert str(infra) == textwrap.dedent("""
            127.0.0.1
            ~ Hostnames:
                ['localhost']
            ~ OS:
                ['linux']
            ~ Services:
                22/tcp - ['ssh']
                    ['OpenSSH 1.0']
                80/tcp - ['http', 'www']
                    ['Apache Web Server']
                443/tcp - ['https']
                    ['Apache Web Server']
                1111/udp - ['unknown']
                    ['', 'Ok Banner', 'unknown']
        """)


def test_trash_service_names_filter():
    infra_ = copy.deepcopy(infra)

    for host in infra_.hosts:
        for service in host.services:
            filters.trash_service_name.apply_filter(service, None)

    assert str(infra_) == textwrap.dedent("""
            127.0.0.1
            ~ Hostnames:
                ['localhost']
            ~ OS:
                ['linux']
            ~ Services:
                22/tcp - ['ssh']
                    ['OpenSSH 1.0']
                80/tcp - ['http']
                    ['Apache Web Server']
                443/tcp - ['https']
                    ['Apache Web Server']
                1111/udp - []
                    ['', 'Ok Banner', 'unknown']
        """)


def test_trash_banners_filter():
    infra_ = copy.deepcopy(infra)

    for host in infra_.hosts:
        for service in host.services:
            filters.trash_banner.apply_filter(service, None)

    assert str(infra_) == textwrap.dedent("""
            127.0.0.1
            ~ Hostnames:
                ['localhost']
            ~ OS:
                ['linux']
            ~ Services:
                22/tcp - ['ssh']
                    ['OpenSSH 1.0']
                80/tcp - ['http', 'www']
                    ['Apache Web Server']
                443/tcp - ['https']
                    ['Apache Web Server']
                1111/udp - ['unknown']
                    ['Ok Banner']
        """)


# ---------------------------------------------------------------------------
# Helpers for column_filter tests
# ---------------------------------------------------------------------------


def _args(specs, *, value_mode=False, host_mode=False):
    """Build a minimal args namespace for column_filter."""
    return SimpleNamespace(
        column_regex=specs, col_value_mode=value_mode, col_host_mode=host_mode
    )


def _apply_cf(infra_snapshot, specs, *, strict=False):
    infra_ = copy.deepcopy(infra_snapshot)
    column_filter.apply_filter(infra_, _args(specs, value_mode=strict))
    return infra_


def _apply_cf_host(infra_snapshot, specs):
    infra_ = copy.deepcopy(infra_snapshot)
    column_filter.apply_filter(infra_, _args(specs, host_mode=True))
    return infra_


# ---------------------------------------------------------------------------
# column_filter tests
# ---------------------------------------------------------------------------


def test_column_filter_service_column_match_keeps_matching_services():
    """Services:ssh keeps only the ssh service row."""
    infra_ = _apply_cf(infra, ["Services:ssh"])
    assert len(infra_.hosts) == 1
    services = infra_.hosts[0].services
    assert len(services) == 1
    assert services[0].port == 22


def test_column_filter_service_column_drops_non_matching_host():
    """Services:nonexistent drops the host entirely."""
    infra_ = _apply_cf(infra, ["Services:nonexistent"])
    assert len(infra_.hosts) == 0


def test_column_filter_service_column_negation_drops_matched_services():
    """Services:!ssh drops the ssh service, keeps the others."""
    infra_ = _apply_cf(infra, ["Services:!ssh"])
    assert len(infra_.hosts) == 1
    ports = [s.port for s in infra_.hosts[0].services]
    assert 22 not in ports
    assert 80 in ports
    assert 443 in ports


def test_column_filter_host_column_match():
    """IP-Addresses:127.0.0.1 keeps the host; IP-Addresses:10.0.0.1 drops it."""
    infra_match = _apply_cf(infra, ["IP-Addresses:127.0.0.1"])
    assert len(infra_match.hosts) == 1

    infra_no = _apply_cf(infra, ["IP-Addresses:10.0.0.1"])
    assert len(infra_no.hosts) == 0


def test_column_filter_host_column_negation():
    """IP-Addresses:!127.0.0.1 should drop the only host."""
    infra_ = _apply_cf(infra, ["IP-Addresses:!127.0.0.1"])
    assert len(infra_.hosts) == 0


def test_column_filter_global_match():
    """'Apache' (global) keeps the host (matches banner)."""
    infra_ = _apply_cf(infra, ["Apache"])
    assert len(infra_.hosts) == 1


def test_column_filter_global_negation_global():
    """Global '!somepattern' — '!nonexistent' should NOT drop anything."""
    infra_ = _apply_cf(infra, ["!nonexistent_xyz"])
    # "nonexistent_xyz" appears nowhere, so negation passes for every row
    assert len(infra_.hosts) == 1


def test_column_filter_case_insensitive_via_inline_flag():
    """(?i)SSH matches the ssh service name."""
    infra_ = _apply_cf(infra, ["Services:(?i)SSH"])
    assert len(infra_.hosts) == 1
    assert infra_.hosts[0].services[0].port == 22


def test_column_filter_chaining_and_semantics():
    """Two specs are ANDed: Services:ssh AND Banners:OpenSSH keeps port 22 only."""
    infra_ = _apply_cf(infra, ["Services:ssh", "Banners:OpenSSH"])
    assert len(infra_.hosts) == 1
    assert infra_.hosts[0].services[0].port == 22


def test_column_filter_chaining_no_match():
    """Services:ssh AND Services:http can never both be true → host dropped."""
    infra_ = _apply_cf(infra, ["Services:^ssh$", "Services:^http$"])
    assert len(infra_.hosts) == 0


def test_column_filter_normal_mode_global_host_match_passes_all_services():
    """Normal mode: global IP match → all services of the host survive."""
    infra_ = _apply_cf(infra, ["127\\.0\\.0\\.1"], strict=False)
    assert len(infra_.hosts) == 1
    # All 4 services survive because the host matched
    assert len(infra_.hosts[0].services) == 4


def test_column_filter_value_mode_global_pattern():
    """Test that value mode (-Cv) forces global patterns to match service fields directly."""
    # 127.0.0.1 only appears in host.address, not in any service field.
    # So in value mode every service fails the global pattern → host is dropped.
    infra_ = _apply_cf(infra, ["127\\.0\\.0\\.1"], strict=True)
    assert len(infra_.hosts) == 0


def test_column_filter_value_mode_service_own_field_match_survives():
    """Value mode: service whose own banner matches the global pattern survives."""
    # "OpenSSH" appears in the banner of port 22 only
    infra_ = _apply_cf(infra, ["OpenSSH"], strict=True)
    assert len(infra_.hosts) == 1
    assert infra_.hosts[0].services[0].port == 22


def test_column_filter_empty_specs_is_noop():
    """Empty spec list must not modify the infrastructure."""
    infra_ = _apply_cf(infra, [])
    assert len(infra_.hosts) == 1
    assert len(infra_.hosts[0].services) == 4


def test_column_filter_port_column():
    """Ports:22/tcp keeps only the ssh service."""
    infra_ = _apply_cf(infra, ["Ports:22/tcp"])
    assert len(infra_.hosts) == 1
    assert infra_.hosts[0].services[0].port == 22


def test_column_filter_banner_negation_drops_matched_banner_services():
    """Banners:!unknown drops port 1111 (its joined banner string contains 'unknown')."""
    # service_4 (1111/udp) banners: {"", "Ok Banner", "unknown"}
    # joined → " \nOk Banner \nunknown"  which contains "unknown" → negation → dropped
    # Other services have banners like "OpenSSH 1.0", "Apache Web Server" → no "unknown" → kept
    infra_ = _apply_cf(infra, ["Banners:!unknown"])
    ports = [s.port for s in infra_.hosts[0].services]
    assert 1111 not in ports
    assert 22 in ports
    assert 80 in ports
    assert 443 in ports


# ---------------------------------------------------------------------------
# Host mode (-Ch) tests
# ---------------------------------------------------------------------------


def test_column_filter_host_mode_keeps_all_services_when_host_matched():
    """Host mode: IP match keeps the host with ALL its services untrimmed."""
    infra_ = _apply_cf_host(infra, ["127\\.0\\.0\\.1"])
    assert len(infra_.hosts) == 1
    assert len(infra_.hosts[0].services) == 4


def test_column_filter_host_mode_service_spec_keeps_whole_host():
    """Host mode: Services:ssh keeps the whole host (all 4 services), not just port 22."""
    infra_ = _apply_cf_host(infra, ["Services:ssh"])
    assert len(infra_.hosts) == 1
    assert len(infra_.hosts[0].services) == 4


def test_column_filter_host_mode_drops_host_when_nothing_matches():
    """Host mode: Services:nonexistent → no service matches → host dropped."""
    infra_ = _apply_cf_host(infra, ["Services:nonexistent"])
    assert len(infra_.hosts) == 0


def test_column_filter_host_mode_vs_normal_mode_differ():
    """Normal mode trims services; host mode preserves them."""
    infra_normal = _apply_cf(infra, ["Services:ssh"])
    assert len(infra_normal.hosts[0].services) == 1  # only port 22

    infra_host = _apply_cf_host(infra, ["Services:ssh"])
    assert len(infra_host.hosts[0].services) == 4  # all services kept


def test_column_filter_host_mode_chaining_any_service_sufficient():
    """Host mode: Services:ssh AND Services:https — no single service satisfies both,
    so the host is dropped (AND logic across service-level patterns is per-service)."""
    infra_ = _apply_cf_host(infra, ["Services:^ssh$", "Services:^https$"])
    # No single service has both names → host dropped
    assert len(infra_.hosts) == 0


def test_column_filter_host_mode_negation_on_host_field():
    """Host mode: IP-Addresses:!127.0.0.1 drops the host."""
    infra_ = _apply_cf_host(infra, ["IP-Addresses:!127.0.0.1"])
    assert len(infra_.hosts) == 0


# ---------------------------------------------------------------------------
# Value mode value-trimming tests (custom_fields / Banners / Services)
# ---------------------------------------------------------------------------


def _make_nessus_like_infra():
    """Build an infrastructure that mimics merged Nessus output:
    one service per port containing multiple vulnerability types as a SortedSet
    in custom_fields['Vulnerability-Type'].
    """
    h = Host(
        address=SortedSet(["10.0.0.1"]),
        hostnames=SortedSet([]),
        os=SortedSet([]),
    )
    s_443 = Service(
        port=443,
        protocol="tcp",
        service_names=SortedSet(["https"]),
        banners=SortedSet([]),
        custom_fields={
            "Vulnerability-Type": SortedSet(
                [
                    "SSL Version 2 and 3 Protocol Detection",
                    "SSL Certificate Cannot Be Trusted",
                    "TLS Version 1.0 Protocol Detection",
                ]
            )
        },
    )
    s_80 = Service(
        port=80,
        protocol="tcp",
        service_names=SortedSet(["http"]),
        banners=SortedSet([]),
        custom_fields={
            "Vulnerability-Type": SortedSet(
                [
                    "HTTP TRACE / TRACK Methods Allowed",
                ]
            )
        },
    )
    h.add_services([s_443, s_80])
    return Infrastructure([h], "Nessus-like")


def test_column_filter_value_mode_trims_custom_field_values():
    """Value mode trims Vulnerability-Type to only the matching value."""
    nessus = _make_nessus_like_infra()
    result = _apply_cf(nessus, ["Vulnerability-Type:SSL Version"], strict=True)
    assert len(result.hosts) == 1
    services = result.hosts[0].services
    # Only port 443 has an SSL Version vuln
    assert len(services) == 1
    assert services[0].port == 443
    # Only the matching value survives in the set
    vuln_set = services[0].custom_fields["Vulnerability-Type"]
    assert list(vuln_set) == ["SSL Version 2 and 3 Protocol Detection"]


def test_column_filter_normal_mode_does_not_trim_custom_field_values():
    """Normal mode keeps all values in the set even though only one matched."""
    nessus = _make_nessus_like_infra()
    result = _apply_cf(nessus, ["Vulnerability-Type:SSL Version"], strict=False)
    assert len(result.hosts) == 1
    services = result.hosts[0].services
    assert services[0].port == 443
    # All three values remain untouched
    assert len(services[0].custom_fields["Vulnerability-Type"]) == 3


def test_column_filter_value_mode_trims_values():
    """Test that value mode (-Cv) trims multi-value fields to only matching values."""
    h = Host(address=SortedSet(["1.2.3.4"]), hostnames=SortedSet([]), os=SortedSet([]))
    svc = Service(
        port=80,
        protocol="tcp",
        service_names=SortedSet(["http"]),
        banners=SortedSet(["Apache/2.4", "OpenSSL/1.1", "mod_ssl/2.4"]),
    )
    h.add_services([svc])
    infra_ = Infrastructure([h], "banner-test")
    result = _apply_cf(infra_, ["Banners:Apache"], strict=True)
    assert len(result.hosts) == 1
    assert list(result.hosts[0].services[0].banners) == ["Apache/2.4"]


def test_column_filter_value_mode_trims_service_names():
    """Value mode trims service.service_names to only matching values.

    The Services field is matched as a joined string, so the pattern must match
    the joined representation. Trimming then keeps only individual values that
    each satisfy the pattern.
    """
    h = Host(address=SortedSet(["1.2.3.4"]), hostnames=SortedSet([]), os=SortedSet([]))
    svc = Service(
        port=80,
        protocol="tcp",
        service_names=SortedSet(["http", "www", "http-proxy"]),
        banners=SortedSet([]),
    )
    h.add_services([svc])
    infra_ = Infrastructure([h], "svcname-test")
    # "http-proxy" is present in the joined string → service is kept
    result = _apply_cf(infra_, ["Services:http-proxy"], strict=True)
    assert len(result.hosts) == 1
    # Only "http-proxy" satisfies the pattern → other names trimmed
    assert list(result.hosts[0].services[0].service_names) == ["http-proxy"]
