from typing import Self

from scans2any.internal import printer
from scans2any.internal.sorted_set import SortedSet


class OverridingNoConflictError(Exception):
    """
    No conflict in service name / banner, yet trying to override in merge.
    """

    def __init__(self, port: int, *, service_name: bool, banners: bool, msg: str = ""):
        super().__init__(msg)

        self.port = port
        self.service_name = service_name
        self.banners = banners

    def print_warning(self, hostname: str):
        if self.service_name:
            printer.warning(
                f"Overriding {hostname} port {self.port}'s service name during merge, even though there were no conflicts."
            )
        if self.banners:
            printer.warning(
                f"Overriding {hostname} port {self.port}'s banners during merge, even though there were no conflicts."
            )


class Service:
    """
    Internal representation of a service run by a host.

    Attributes
    ----------
    port : int
        Numerical port of the service
    protocol: str
        tcp/udp
    service_names: SortedSet[str]
        Service names, e.g. `http`, `ssh`. A SortedSet of service names, containing
        multiple entries when there have been service name collisions.
    banners: SortedSet[str]
        Additional information about the service, e.g. `Apache httpd x.y`
    """

    def __init__(
        self,
        port: int,
        protocol: str,
        *,
        service_names: SortedSet[str],
        banners: SortedSet[str],
    ):
        assert type(port) is int
        assert type(protocol) is str
        assert type(service_names) is SortedSet
        assert type(banners) is SortedSet

        self.port = port
        self.protocol = protocol
        self.service_names = service_names
        self.banners = banners

    def merge_with_service(self, other: Self):
        """
        Merges this service with the specified service, using this service
        (self) as priority to solve merge conflicts.

        Conflicting service names and banners from the other service will be
        ignored.

        Should not be called on services with different ports/protocols.

        Parameters
        ----------
        other : Self
            Service object to be merged with this service
        """

        assert self.port == other.port
        assert self.protocol == other.protocol

        raise_service_name_override = False
        raise_banners_override = False

        # Use own service name and banner, if set. Otherwise take from other
        #
        # If other has no conflicting entries, raise warning, because this is
        # probably triggered by a merge file entry, and at least suspicious.

        if not self.service_names:
            self.service_names = other.service_names
        elif len(other.service_names) == 1:
            raise_service_name_override = True

        if not self.banners:
            self.banners = other.banners
        elif len(other.banners) == 1:
            raise_banners_override = True

        # Raise exceptions on override without conflict
        if raise_service_name_override or raise_banners_override:
            raise OverridingNoConflictError(
                port=self.port,
                service_name=raise_service_name_override,
                banners=raise_banners_override,
            )

    def union_with_service(self, other: Self):
        """
        Combine services with same `port` and `protocol`.

        Unions service names.

        Unions banners lists.

        Should not be called on services with different ports/protocols.

        Parameters
        ----------
        other : Self
            Other host instance to be integrated into this one
        """

        assert self.port == other.port
        assert self.protocol == other.protocol

        # Merge services names by updating the set
        self.service_names.update(other.service_names)

        # Merge banners by updating the set
        self.banners.update(other.banners)

    def __repr__(self) -> str:
        """
        Print service for testing purposes.
        """

        s = f"{self.port}/{self.protocol} - {self.service_names}"
        if self.banners:
            s += f"\n    {self.banners}"
        return s


def get_port_by_service(service: str, protocol: str) -> int:
    """
    Get default port associated with the specified service + protocol.

    Parameters
    ----------
    service : str
        e.g. `https`
    protocol : str
        `tcp`/`udp`

    Returns
    -------
    int
        Default port, associated with the specified service + protocol
    """

    tcp_map = {"http": 80, "https": 443}

    if protocol == "tcp":
        return tcp_map[service]
    raise Exception("protocol not defined")
