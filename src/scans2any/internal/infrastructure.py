import ipaddress
import os
import tempfile
import textwrap
from typing import Self

import yaml

from scans2any.internal import Host, printer
from scans2any.internal.host import HostIntegrationError
from scans2any.internal.sorted_set import SortedSet


class Infrastructure:
    """
    Internal representation of parsed infrastructure scans.

    No two hosts with the same ip address possible.

    Attributes
    ----------
    hosts : list[Host]
        List of scanned and available hosts
    identifier : str
        Additional information, like `Nmap scan infrastructure`
    """

    def __init__(self, hosts: list[Host] | None = None, identifier: str = ""):
        self.hosts: list[Host] = []
        self.identifier: str = identifier

        if hosts is not None:
            self.add_hosts(hosts)

    def add_host(self, new_host: Host, *, prioritize_self: bool = False):
        """
        Adds a new host to the infrastructure OR integrates it to an existing
        host with the same ip address or at most one ip address and matching
        hostnames.

        Optionally, we can use this infrastructure as priority, to avoid
        collisions, i. e. multiple service names and/or banners.

        Parameters
        ----------
        new_host: Host
            Host to be added/integrated
        prioritize_self : bool
            Call `merge_with_host` instead of `union_with_host` on host, if it
            has to be integrated into an existing host of `self`.
        """

        try:
            assert type(new_host) is Host
        except AssertionError:
            printer.warning(f"Skipped attempt to add host of type {type(new_host)}")
            return

        for host in self.hosts:
            # Same IP address or common hostname
            if (host.address & new_host.address) or (
                host.hostnames & new_host.hostnames
            ):
                try:
                    if prioritize_self:
                        host.merge_with_host(new_host)
                        return
                    host.union_with_host(new_host)
                    return
                except HostIntegrationError as e:
                    printer.warning(str(e))
                    printer.warning(f"self: {host.address!s}, {host.hostnames!s}")
                    printer.warning(
                        f"other: {new_host.address!s}, " + f"{new_host.hostnames!s}"
                    )

        # No integration, just append the new host
        self.hosts.append(new_host)

    def add_hosts(self, new_hosts: list[Host], *, prioritize_self: bool = False):
        """
        Add new hosts to the infrastructure. Calls `self.add_host()` on every
        item in the list.

        Parameters
        ----------
        new_hosts: list[Host]
            List of hosts to be added
        prioritize_self: bool
            Passed to calls of `self.add_host()`
        """

        for new_host in new_hosts:
            self.add_host(new_host, prioritize_self=prioritize_self)

    def remove_host(self, hostip: str):
        """
        Remove host with given ip from the infrastructure if it has only one
        address. If it has multiple addresses, remove the specific address from
        the host.

        Parameters
        ----------
        hostip : str
            IP addresses
        """

        new_hosts = []
        for host in self.hosts:
            if hostip in host.address:
                if len(host.address) == 1:
                    continue
                else:
                    host.address.remove(hostip)
            new_hosts.append(host)
        self.hosts = new_hosts

    def get_host_by_address(self, hostip: str):
        """
        Returns host with the specified address or None.

        Parameters
        ----------
        hostip : str
            IP addresses
        """

        for host in self.hosts:
            if hostip in host.address:
                return host

        return None

    def union_with_infrastructure(self, other: Self):
        """
        Infrastructures are combined, i.e. contained hosts with

        1. the same ip address or
        2. the same list of hostnames

        are combined.

        Parameters
        ----------
        other : Self
            Infrastructure to be combined with this one.
        """

        self.add_hosts(other.hosts)

    def merge_with_infrastructure(self, other: Self, ruleset: list[dict] | None = None):
        """
        Infrastructures are merged, using this infrastructure (self) as priority
        to solve merge conflicts.

        Primarily intended to resolve conflicts using the infrastructure created
        from a merge file as priority (self).

        An option ruleset can be passed, to automatically resolve reoccurring
        conflicts. E.g. "for port `443` and service names `http` or `https`,
        always choose `https`". See `config.yaml` or automatically created merge
        file for examples on how to define rules.

        Parameters
        ----------
        other : Self
            Infrastructure to be merged into this one.
        ruleset: list[dict]
            List of merging rules as in `config.yaml` to be applied.
        """

        # Currently, merge file holds
        #
        #   1. service name prios
        #   2. banner prios
        #
        # In the future, hostname to ip associations might be part of it too
        #
        self.add_hosts(other.hosts, prioritize_self=True)

        # Apply rules from ruleset
        if ruleset is not None:
            self.auto_merge(ruleset)

    def auto_merge(self, ruleset: list[dict] | None = None):
        """
        Automatic conflict solving using internal ruleset from config.

        If an optional ruleset is passed, it is used instead of the internal ruleset
        from the config.

        ruleset: list[dict]
            List of merging rules as in `config.yaml` to be applied.
        """
        printer.section("Automatic Merging")

        if ruleset is None:
            printer.status("Solving conflicts based on internal ruleset.")
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

            with open(config_path) as file:
                config = yaml.safe_load(file)
                ruleset = config.get("auto-merge", [])
        else:
            printer.status("Solving conflicts based on provided ruleset.")

        # Counters for success message
        cnt_service = 0
        cnt_banner = 0
        cnt_os = 0

        for rule in ruleset:
            # Validate the rule
            if "key" not in rule:
                printer.failure(f"Malformed rule in ruleset: {rule}")
                printer.failure("'key' is required in each rule. Skipping...")
                continue

            if not any(k in rule for k in ("service-names", "os", "banners")):
                printer.failure(f"Malformed rule in ruleset: {rule}")
                printer.failure(
                    "At least one of 'service-names', 'os', or 'banners' is needed. Skipping..."
                )
                continue

            rule_key = rule["key"]
            rule_os = set(rule.get("os", []))
            rule_ports = set(rule.get("ports", []))
            rule_port = rule.get("port")
            rule_service_names = set(rule.get("service-names", []))
            rule_banners: SortedSet[str] = SortedSet(rule.get("banners", []))

            for host in self.hosts:
                # Apply 'os' rule if applicable
                if "os" in rule and set(host.os) == rule_os:
                    host.os = rule_key
                    cnt_os += 1

                # Apply 'service-names' and 'port(s)' rules if applicable
                elif "service-names" in rule:
                    for service in host.services:
                        if rule_port is not None and service.port != rule_port:
                            continue
                        if rule_ports and service.port not in rule_ports:
                            continue
                        if (
                            rule_service_names
                            and set(service.service_names) != rule_service_names
                        ):
                            continue
                        service.service_names = rule_key
                        cnt_service += 1

                # Apply 'banners' rule if applicable
                if "banners" in rule:
                    for service in host.services:
                        if SortedSet(service.banners) == rule_banners:
                            service.banners = rule_key
                            cnt_banner += 1

        if cnt_os or cnt_service or cnt_banner:
            printer.success(
                f"Successfully applied {cnt_os} OS, {cnt_service} service, and {cnt_banner} banner merge rules."
            )
        else:
            printer.warning("No merge rules were applied.")

    def make_merge_file(self, *, passed_merge_file: bool):
        """
        Create merge file if necessary.

        Checks for multiple service names or banners for the same port.

        If so, create a merge file where these collisions can be resolved
        manually.

        Parameters
        ----------
        passed_merge_file:
            `True` if a merge file was passed. Needed for merge file creation.

        Raises
        ------
        ExistingMergeFile
            Merge file exists already and user did choose not to override it.
        NoCollisions
            No collisions found (probably called with `--merge-file` or with
            only a single input)
        """

        file_name = "MERGE_FILE.yaml"
        temp_merge_file = os.path.join(tempfile.gettempdir(), file_name)

        collisions = {}

        for host in self.hosts:
            host_collisions = host.get_collisions()
            if host_collisions:
                collisions[host.identifier()] = host_collisions

        if not collisions:
            return False

        printer.warning("Conflicts found in infrastructure.")

        # Don't override merge file without explicit consent
        if os.path.exists(file_name):
            # If the existing merge file was not passed, there are probably not
            # many solved conflicts in it and the user may either override it
            # completely or leave it as it is.
            if not passed_merge_file:
                file_name = temp_merge_file
                printer.warning(f"Existing '{file_name}', writing to temporary file.")
            else:
                printer.warning(f"Existing '{file_name}' with conflicts. Exiting.")
                exit(1)

        target_dir = os.path.dirname(os.path.abspath(file_name)) or "."
        if not os.access(target_dir, os.W_OK):
            printer.warning(
                "No write access to current directory. Using temporary file."
            )
            file_name = temp_merge_file

        auto_merge_rules = None
        manual_merge_rules: dict[str, dict] = {
            "preserved_rules": {},
            "altered_rules": {},
        }

        for host_collision in collisions:
            if host_collision in manual_merge_rules["preserved_rules"]:
                # 'still' makes sense for rules, that have been preserved from
                # the merge file
                printer.status(f"{host_collision} still has collisions")
                for key in collisions[host_collision]:
                    manual_merge_rules["preserved_rules"][host_collision][key] = (
                        collisions[host_collision][key]
                    )
                # Move to 'altered rules'
                manual_merge_rules["altered_rules"][host_collision] = (
                    manual_merge_rules["preserved_rules"][host_collision]
                )
                del manual_merge_rules["preserved_rules"][host_collision]
            else:
                manual_merge_rules["altered_rules"][host_collision] = collisions[
                    host_collision
                ]

        self.__write_merge_file(
            auto_merge_rules,
            manual_merge_rules["altered_rules"],
            manual_merge_rules["preserved_rules"],
            file_name,
        )

        return True

    def sort(self):
        """
        Sort hosts, i.e. sort services for each host and sort hosts by IP.
        """

        # Sorts the host attributes.
        for host in self.hosts:
            host.sort()
        # There might be hosts with only hostnames, they have to be sorted
        # separately. Sort by first hostname.
        only_hostname_hosts = [host for host in self.hosts if not host.address]
        for host in only_hostname_hosts:
            assert host.hostnames, "Host with no ip and no hostnames detected!!!"
        only_hostname_hosts.sort(key=lambda x: min(x.hostnames))
        # Sort remaining hosts by IP
        address_hosts = [host for host in self.hosts if host.address]
        address_hosts.sort(
            key=lambda x: min(
                map(
                    lambda addr: (
                        ipaddress.ip_address(addr).version,
                        int(ipaddress.ip_address(addr)),
                    ),
                    x.address,
                )
            )
        )
        # re-combine hosts
        self.hosts = address_hosts + only_hostname_hosts

    def cleanup_names(self, chars_to_escape: str):
        # Import cleanup locally to break circular dependency
        from scans2any.helpers.utils import cleanup

        # Function to clean and update names
        def clean_names(items, chars_to_escape):
            return SortedSet([cleanup(item, chars_to_escape) for item in items])

        # Apply cleanup to all hostnames and services
        for host in self.hosts:
            # Clean up hostnames using a list comprehension
            host.hostnames = clean_names(host.hostnames, chars_to_escape)

            # Clean up service names and banner in each service
            for service in host.services:
                service.service_names = clean_names(
                    service.service_names, chars_to_escape
                )
                service.banners = clean_names(service.banners, chars_to_escape)

    def __repr__(self) -> str:
        """
        Print infrastructure, for testing purposes.
        """

        s = ""
        for host in self.hosts:
            s += str(host)
        return s

    def __write_merge_file(
        self,
        auto_merge_rules,
        manual_merge_altered_rules,
        manual_merge_preserved_rules,
        file_name="MERGE_FILE.yaml",
    ):
        """
        Write collisions to merge file in `yaml` format
        """

        def represent_sortedset(dumper, data):
            return dumper.represent_list(list(data))

        yaml.add_representer(SortedSet, represent_sortedset, Dumper=yaml.SafeDumper)

        with open(file_name, "w") as merge_file:
            merge_file.write("# scans2any: merge file\n\n\n")
            # Automatic merge rules
            merge_file.write(
                "# Automatic merging rules.\n#\n"
                + "# if any of the listed combinations of service names "
                + "[and port] (e.g. `http` and\n"
                + "# `www`) are found as service names for the same port, "
                + "the key is used as the\n"
                + "# conflict solving service name.\n"
            )
            if auto_merge_rules is not None:
                yaml.safe_dump(
                    {"auto-merge": auto_merge_rules},
                    merge_file,
                    indent=4,
                    sort_keys=False,
                )
            else:
                merge_file.write(
                    "auto-merge:\n"
                    + "#-   service-names:\n"
                    + "#    - http\n"
                    + "#    - https\n"
                    + "#    port: 443\n"
                    + "#    key:\n"
                    + "#    - https\n"
                    + "#-   service-names:\n"
                    + "#    - http\n"
                    + "#    - https\n"
                    + "#    port: 80\n"
                    + "#    key:\n"
                    + "#    - http\n"
                )
            # Manual Merge Rules
            merge_file.write(
                "\n\n# Manual merging rules.\n"
                + "#\n# Make sure there is only one service name and banner "
                + "for each port left\n"
                + "# then execute scans2any again with option "
                + "`--merge-file filename`\n"
            )
            yaml.safe_dump(
                {"manual-merge": manual_merge_altered_rules},
                merge_file,
                indent=4,
                sort_keys=True,
            )
            if manual_merge_preserved_rules:
                merge_file.write(
                    textwrap.indent(
                        yaml.safe_dump(
                            manual_merge_preserved_rules, indent=4, sort_keys=True
                        ),
                        prefix="    ",
                    )
                )
            # Custom entries
            merge_file.write(
                "\n\n# Custom entries\n"
                + "#\n"
                + "# Add custom entries in this way:\n"
                + "custom-entries:\n"
                + "#    1.1.1.1:\n"
                + "#        hostnames:\n"
                + "#           -   test.company.com\n"
                + "#           -   test2.company.com\n"
                + "#        os: linux\n"
                + "#        ports:\n"
                + "#           -   port: 1111/tcp\n"
                + "#               service-name: test\n"
                + "#               banner: Test description\n"
                + "#           -   port: 2222/udp\n"
                + "#               service-name: test2\n"
                + "#               banner: Test description 2\n"
                + "#    2.2.2.2:\n"
                + "#        hostnames:\n"
                + "#           -   asdf.company.local\n"
                + "#        os: bsd\n"
                + "#        ports:\n"
                + "#           -   port: 333/tcp\n"
                + "#               service-name: test\n"
                + "#               banner: Test description 3"
            )

            printer.warning(f"Merge file written for manual edit: {file_name}")

    def merge_os_sources(self):
        from scans2any.helpers.utils import (
            trustworthiness_os,  # Local import to break circular dependency
        )

        """
        Merge os sources for each host using trustworthiness_os function. If a
        host has only one os source, it is kept. If a host has multiple os
        sources, the one with the highest trustworthiness is kept. If multiple
        sources have the same trustworthiness, all are kept.

        Attributes
        ----------
        host : Host
            Host with os votes.
        """

        for host in self.hosts:
            if not host.os:
                host.os = SortedSet()
                continue

            if len(host.os) == 1:
                host.os = SortedSet([next(iter(host.os))[0]])
            else:
                tally: dict[str, int] = {}
                for os in host.os:
                    if os[0] in tally:
                        tally[os[0]] += trustworthiness_os(os[1])
                    else:
                        tally[os[0]] = trustworthiness_os(os[1])

                max_score = max(tally.values())
                host.os = SortedSet(
                    [os for os, score in tally.items() if score == max_score]
                )
