"""Filter hosts and services based on user-defined column regex patterns.

Spec syntax (multiple specs are ANDed together):
  col:regex       keep rows where <col> matches <regex>
  col:!regex      keep rows where <col> does NOT match <regex> (negation)
  regex           match against ALL columns (global)
  !regex          global match, negated

Case-insensitive matching: use inline Python flag, e.g. (?i)http

Valid column names:
  Host-level   : IP-Addresses, Hostnames, OS
  Service-level: Ports, Services, Banners (plus any parser-specific columns)

Granularity Modes:
  -C  / --column-regex  (Service-level): Keep matching services, drop the rest.
  -Ch / --col-host      (Host-level): Keep the whole host if anything matches.
  -Cv / --col-value     (Value-level): Trim multi-value fields (like Banners or
                        Vulnerabilities) to only the exact values that matched.
"""

import re
from dataclasses import dataclass, field
from re import Pattern

from scans2any.internal import Host, Infrastructure, Service, printer
from scans2any.parsers import parser_custom_columns

PRIORITY = 1

HOST_COLUMNS = ("IP-Addresses", "Hostnames", "OS")


@dataclass
class ColumnPattern:
    column: str | None
    pattern: Pattern[str]
    is_service_level: bool
    negated: bool = field(default=False)

    def matches(self, text: str) -> bool:
        """Return True when the pattern passes (match XOR negated)."""
        found = bool(self.pattern.search(text))
        return (not found) if self.negated else found


def add_arguments(parser):
    custom_cols = ", ".join(sorted(parser_custom_columns.values())) or "(none loaded)"
    parser.add_argument(
        "--column-regex",
        nargs="+",
        default=[],
        metavar="col:regex",
        help=(
            "Filter by column regex (ANDed). Syntax: [col:]regex\n"
            "     Use ! for negation, e.g. Services:!ssh to exclude SSH services.\n"
            "     Use (?i) for case-insensitivity.\n"
            "     Granularity: Default is service-level. Use -Ch for host-level, -Cv for value-level.\n"
            f"    Columns: IP-Addresses, Hostnames, OS, Ports, Services, Banners, {custom_cols}"
        ),
    )


def _compile_specs(specs: list[str]) -> list[ColumnPattern]:
    service_cols = {"Ports", "Services", "Banners", *parser_custom_columns.values()}
    valid_cols = {*HOST_COLUMNS, *service_cols}
    canonical = {k.lower(): v for k, v in parser_custom_columns.items()}
    compiled: list[ColumnPattern] = []

    for spec in specs:
        col = None
        if ":" in spec:
            col, spec = spec.split(":", 1)
            col = col.strip()
            col = canonical.get(col.lower(), col)
            if col not in valid_cols:
                printer.warning(
                    f"Ignoring unknown column '{col}' in column-regex filter"
                )
                continue

        negated = spec.startswith("!")
        regex = spec[1:] if negated else spec
        try:
            pat = re.compile(regex)
        except re.error as e:
            ctx = f" for column {col}" if col else ""
            printer.warning(f"Ignoring invalid regex '{regex}'{ctx}: {e}")
            continue

        compiled.append(
            ColumnPattern(
                col, pat, col in service_cols if col else False, negated=negated
            )
        )
    return compiled


def _get_host_field(host: Host, col: str) -> str:
    if col == "IP-Addresses":
        return " ".join(host.address)
    if col == "Hostnames":
        return " ".join(host.hostnames)
    if col == "OS":
        return " ".join(str(o) for o in host.os)
    return ""


def _get_service_field(service: Service, col: str) -> str:
    if col == "Ports":
        return f"{service.port}/{service.protocol}"
    if col == "Services":
        return " ".join(service.service_names)
    if col == "Banners":
        return " \n".join(service.banners)
    return str(service.custom_fields[col]) if col in service.custom_fields else ""


def _matches_any_host_field(host: Host, cp: ColumnPattern) -> bool:
    return any(cp.matches(_get_host_field(host, col)) for col in HOST_COLUMNS)


def _matches_any_service_field(service: Service, cp: ColumnPattern) -> bool:
    return any(
        cp.matches(_get_service_field(service, col))
        for col in ("Ports", "Services", "Banners", *service.custom_fields)
    )


def _trim_service_values(service: Service, patterns: list[ColumnPattern]) -> None:
    """Prune multi-value fields so only matching values remain."""
    for p in patterns:
        col = p.column
        if col in service.custom_fields:
            container = service.custom_fields[col]
            service.custom_fields[col] = type(container)(
                v for v in container if p.matches(str(v))
            )
        elif col == "Banners":
            service.banners = type(service.banners)(
                v for v in service.banners if p.matches(v)
            )
        elif col == "Services":
            service.service_names = type(service.service_names)(
                v for v in service.service_names if p.matches(v)
            )
        # Ports is a single value — no trimming needed (match already confirmed)


def apply_filter(infra: Infrastructure, args):
    """Filter hosts/services by column regex specifications."""
    specs_raw = getattr(args, "column_regex", [])
    if not specs_raw:
        return

    patterns = _compile_specs(specs_raw)
    if not patterns:
        return

    value_mode = getattr(args, "col_value_mode", False)
    host_mode = getattr(args, "col_host_mode", False)

    host_level = [p for p in patterns if p.column and not p.is_service_level]
    service_level = [p for p in patterns if p.column and p.is_service_level]
    global_level = [p for p in patterns if p.column is None]

    def host_matches(host: Host) -> bool:
        # Specific host-column patterns must all match
        for p in host_level:
            assert p.column is not None
            if not p.matches(_get_host_field(host, p.column)):
                return False

        # Global patterns: at least one of (host field, any service field) must match
        for p in global_level:
            if _matches_any_host_field(host, p):
                continue
            if any(_matches_any_service_field(s, p) for s in host.services):
                continue
            return False

        # In host mode, at least one service must satisfy every service-level
        # pattern for the host to be included.
        return not (host_mode and service_level) or any(
            all(
                p.matches(_get_service_field(s, col))
                for p in service_level
                if (col := p.column) is not None
            )
            for s in host.services
        )

    def service_matches(service: Service, host: Host) -> bool:
        # Specific service-column patterns must all match
        for p in service_level:
            assert p.column is not None
            if not p.matches(_get_service_field(service, p.column)):
                return False

        # Global patterns
        for p in global_level:
            if _matches_any_service_field(service, p):
                continue
            # In value mode the service must match on its own fields.
            # In normal mode a match on the host fields is sufficient.
            if not value_mode and _matches_any_host_field(host, p):
                continue
            return False
        return True

    # Apply to infrastructure
    original_count = len(infra.hosts)
    filtered_hosts: list[Host] = []
    for host in infra.hosts:
        if not host_matches(host):
            continue

        # In host mode keep all services — filtering already happened at host level.
        if not host_mode and (service_level or global_level):
            new_services = [s for s in host.services if service_matches(s, host)]
            if not new_services:
                continue
            if value_mode:
                for s in new_services:
                    _trim_service_values(s, service_level)
            host.services = new_services
        filtered_hosts.append(host)

    infra.hosts = filtered_hosts

    printer.status(
        f"column_filter: kept {len(filtered_hosts)} of {original_count} hosts"
    )
