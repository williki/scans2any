import textwrap
from typing import Any, Self  # Use class type inside of the same class

from scans2any.internal import printer
from scans2any.internal.service import OverridingNoConflictError, Service
from scans2any.internal.sorted_set import SortedSet


class HostIntegrationError(Exception):
    pass


class HostsUnionError(HostIntegrationError):
    pass


class MergeHostsError(HostIntegrationError):
    pass


class Host:
    """
    Internal representation of an IPv4 host and corresponding information.

    Attributes
    ----------
    address : str | None
        IPv4 Address
    hostnames : SortedSet[str]
        List of corresponding hostnames
    services : list[Service]
        A list of available services
    os : SortedSet[tuple]
        Operating system, if available

    Methods
    -------
    add_service(self, port: str, protocol: str, service: str, banner: str)
        Adds a new service to the host
    """

    def __init__(
        self,
        address: str | None = None,
        *,
        hostnames: SortedSet[str],
        os: SortedSet[tuple[str, str]] | SortedSet[str],
    ):
        """
        Parameters
        ----------
        address : str
            IPv4 address of the host
        hostnames : SortedSet[str], optional
            A list of corresponding hostnames
        os : SortedSet[tuple], optional
            Operating system, if available
        """

        assert type(address) is str or address is None
        assert type(hostnames) is SortedSet
        assert type(os) is SortedSet

        self.address = address
        self.hostnames = hostnames
        self.services: list[Service] = []
        self.os = os

        # A host must always have at least one of address or hostname
        assert self.address is not None or self.hostnames

    def add_service(self, new_service: Service, *, prioritize_self: bool = False):
        """
        Adds the service object to the list of services.

        Makes sure that there are no duplicate services, by combining services
        with the same port immediately.

        Optionally, we can use this host as priority, to to avoid collisions, i.
        e. multiple service names and/or banners.

        Parameters
        ----------
        service : Service
            Service type object to be added to the list of services
        prioritize_self: bool
            Call `merge_with_service` instead of `union_with_service` on
            service, if it has to be integrated into an existing service of
            `self`.
        """

        for service in self.services:
            if (
                service.port == new_service.port
                and service.protocol == new_service.protocol
            ):
                try:
                    if prioritize_self:
                        service.merge_with_service(new_service)
                    else:
                        service.union_with_service(new_service)
                    return
                except OverridingNoConflictError as e:
                    e.print_warning(self.identifier())
                    return

        # No service with the new services port yet
        self.services.append(new_service)

    def add_services(
        self, new_services: list[Service], *, prioritize_self: bool = False
    ):
        """
        Calls `self.add_service()` on every service in the list.

        Parameters
        ----------
        service : list[Service]
            Service objects to be added to the list of services
        prioritize_self: bool
            Passed to calls of `self.add_service()`
        """

        for new_service in new_services:
            self.add_service(new_service, prioritize_self=prioritize_self)

    def remove_service(self, port: int):
        """
        Removes service with the specified port from the host.
        """

        self.services = [service for service in self.services if service.port != port]

    def remove_services(self, ports: tuple[int, int]):
        """
        Removes services with ports in the specified port-range from the host.
        """

        for port in range(ports[0], ports[1] + 1):
            self.remove_service(port)

    def get_service_by_port(self, port: int):
        """
        Returns the service corresponding to the specified port or None.
        """

        for service in self.services:
            if service.port == port:
                return service

        return None

    def merge_with_host(self, other: Self):
        """
        Merges other host with this one.

        Parameters
        ----------
        other: Host
            Host to be merged with self
        """

        if self.address is None:
            self.address = other.address

        # Union hostnames and merge services
        self.hostnames.update(other.hostnames)
        self.add_services(other.services, prioritize_self=True)

        # Use other os if self has none
        if not self.os:
            self.os = other.os

    def union_with_host(self, other: Self):
        """
        Combine other host with this one.

        Parameters
        ----------
        other : Self
            Host to be combined with this one.
        """

        if self.address is None:
            self.address = other.address

        # Union hostnames and services
        self.hostnames.update(other.hostnames)
        self.add_services(other.services)

        # Union os list
        self.os.update(other.os)

    def identifier(self) -> str:
        """
        Identifier of the host, for user interaction (e.g. merge file).

        This will be the hosts address, or if it has none, the hosts hostname.

        Returns
        -------
        str
            IP address or else hostname of the host
        """

        if self.address is not None:
            return self.address
        if len(self.hostnames) > 1:
            printer.warning(
                f"Using first hostname but several available: {self.hostnames}"
            )
        return self.hostnames[0]

    def get_collisions(self) -> dict:
        """
        Returns a dictionary of collisions, ready to be printed into a merge
        file.
        """

        collisions: dict[str, Any] = {}

        if len(self.os) > 1:
            collisions["os"] = self.os

        for service in self.services:
            service_collisions: dict[str, SortedSet[str]] = {}
            # Multiple service names
            if len(service.service_names) > 1:
                service_collisions["service_names"] = service.service_names
            # Multiple banners
            if len(service.banners) > 1:
                service_collisions["banners"] = service.banners

            if service_collisions:
                # Create section for tcp/udp ports if not yet existent
                if f"{service.protocol}_ports" not in collisions:
                    collisions[f"{service.protocol}_ports"] = {}
                # Add section for services port
                collisions[f"{service.protocol}_ports"][service.port] = (
                    service_collisions
                )

        return collisions

    def sort(self):
        """
        Sort services by port.
        """

        self.services.sort(key=lambda s: s.port)

    def __repr__(self) -> str:
        """
        Print host for testing purposes.
        """

        s = "\n"
        s += f"{self.address}\n"
        s += "~ Hostnames:\n" + f"    {self.hostnames}\n"
        s += "~ OS:\n" + f"    {self.os}\n"
        s += "~ Services:\n"
        for service in self.services:
            s += textwrap.indent(f"{service}\n", "    ")

        return s
