"""
Database management for scans2any using SQLite.

Provides functionality to store and retrieve scan data efficiently.
Each project gets its own set of tables (hosts_<project>, services_<project>).
"""

import sqlite3
from pathlib import Path
from typing import Any

from scans2any.internal import Host, Infrastructure, Service, SortedSet, printer


class Database:
    """
    SQLite database handler for scans2any.

    Manages host and service data with project-based table separation.
    """

    def __init__(self, db_path: str | Path = "scans2any.db", project: str = "default"):
        """
        Initialize database connection.

        Parameters
        ----------
        db_path : str | Path
            Path to SQLite database file
        project : str
            Project name (used for display/reference only, each project has own .db file)
        """
        self.db_path = Path(db_path)
        self.project = project
        self.conn: sqlite3.Connection | None = None
        self.hosts_table = "hosts"
        self.services_table = "services"

    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def create_tables(self):
        """
        Create tables if they don't exist.

        Creates hosts and services tables with appropriate indexes.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()

        # Create hosts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE,
                hostnames TEXT,
                os TEXT,
                custom_fields TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                service_names TEXT,
                banners TEXT,
                custom_fields TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
                UNIQUE(host_id, port, protocol)
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_host_address
            ON hosts(address)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_host_hostname
            ON hosts(hostnames)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_service_port
            ON services(port)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_service_name
            ON services(service_names)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_service_host
            ON services(host_id)
        """)

        self.conn.commit()

    def clear_project_data(self):
        """
        Delete all data from the database.

        Useful for replacing data rather than merging.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM services")
        cursor.execute("DELETE FROM hosts")
        self.conn.commit()

    def write_infrastructure(self, infra: Infrastructure, *, clear: bool = False):
        """
        Write infrastructure data to database.

        Parameters
        ----------
        infra : Infrastructure
            Infrastructure object to store
        clear : bool
            If True, clear existing project data before writing
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        self.create_tables()

        if clear:
            self.clear_project_data()

        cursor = self.conn.cursor()

        for host in infra.hosts:
            # Serialize sets/lists to comma-separated strings
            addresses = ",".join(sorted(host.address)) if host.address else ""
            hostnames = ",".join(sorted(host.hostnames)) if host.hostnames else ""
            os_list = (
                ",".join(
                    sorted(
                        [os[0] if isinstance(os, tuple) else str(os) for os in host.os]
                    )
                )
                if host.os
                else ""
            )

            import json

            custom_fields_json = (
                json.dumps({k: list(v) for k, v in host.custom_fields.items()})
                if host.custom_fields
                else None
            )

            # Use first address as primary identifier for the host
            # Check if host already exists by checking any of its addresses
            existing_host_id = None
            if addresses:
                # Check if any address in this host already exists in database
                for addr in addresses.split(","):
                    cursor.execute(
                        f"SELECT id, address FROM {self.hosts_table} WHERE address LIKE ?",
                        (f"%{addr}%",),
                    )
                    row = cursor.fetchone()
                    if row:
                        existing_host_id = row["id"]
                        # Merge addresses: combine old and new
                        old_addresses = (
                            set(row["address"].split(",")) if row["address"] else set()
                        )
                        new_addresses = set(addresses.split(","))
                        addresses = ",".join(sorted(old_addresses | new_addresses))
                        break

            if existing_host_id:
                # Update existing host
                cursor.execute(
                    f"""
                    UPDATE {self.hosts_table}
                    SET address = ?, hostnames = ?, os = ?, custom_fields = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        addresses,
                        hostnames,
                        os_list,
                        custom_fields_json,
                        existing_host_id,
                    ),
                )
                host_id = existing_host_id
            else:
                # Insert new host
                cursor.execute(
                    f"""
                    INSERT INTO {self.hosts_table} (address, hostnames, os, custom_fields)
                    VALUES (?, ?, ?, ?)
                """,
                    (addresses, hostnames, os_list, custom_fields_json),
                )
                host_id = cursor.lastrowid

            # Handle services
            for service in host.services:
                service_names = (
                    ",".join(sorted(service.service_names))
                    if service.service_names
                    else ""
                )
                banners = ",".join(sorted(service.banners)) if service.banners else ""
                service_custom_fields_json = (
                    json.dumps({k: list(v) for k, v in service.custom_fields.items()})
                    if service.custom_fields
                    else None
                )

                # Check if service exists for this host
                cursor.execute(
                    f"""
                    SELECT id FROM {self.services_table}
                    WHERE host_id = ? AND port = ? AND protocol = ?
                """,
                    (host_id, service.port, service.protocol),
                )

                existing_service = cursor.fetchone()

                if existing_service:
                    # Update existing service
                    cursor.execute(
                        f"""
                        UPDATE {self.services_table}
                        SET service_names = ?, banners = ?, custom_fields = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """,
                        (
                            service_names,
                            banners,
                            service_custom_fields_json,
                            existing_service["id"],
                        ),
                    )
                else:
                    # Insert new service
                    cursor.execute(
                        f"""
                        INSERT INTO {self.services_table}
                        (host_id, port, protocol, service_names, banners, custom_fields)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            host_id,
                            service.port,
                            service.protocol,
                            service_names,
                            banners,
                            service_custom_fields_json,
                        ),
                    )

        self.conn.commit()

    def read_infrastructure(
        self, identifier: str | None = None, *, filters: dict[str, str] | None = None
    ) -> Infrastructure:
        """
        Read infrastructure data from database.

        Parameters
        ----------
        identifier : str, optional
            Custom identifier for the infrastructure object
        filters : dict[str, str], optional
            Column filters to apply at database level.
            Keys can be: 'address', 'hostname', 'port', 'service', 'banner'
            Values are SQL LIKE patterns (use % for wildcards)

        Returns
        -------
        Infrastructure
            Infrastructure object with all hosts and services
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()

        # Check if tables exist
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """,
            (self.hosts_table,),
        )

        if not cursor.fetchone():
            printer.warning(f"No data found for project '{self.project}'")
            return Infrastructure([], identifier or f"Database:{self.project}")

        # Build WHERE clauses for filtering
        host_where = []
        host_params = []
        service_where = []
        service_params = []

        if filters:
            if "address" in filters:
                host_where.append("address LIKE ?")
                host_params.append(filters["address"])
            if "hostname" in filters:
                host_where.append("hostnames LIKE ?")
                host_params.append(filters["hostname"])
            if "port" in filters:
                service_where.append("port = ?")
                service_params.append(filters["port"])
            if "service" in filters:
                service_where.append("service_names LIKE ?")
                service_params.append(filters["service"])
            if "banner" in filters:
                service_where.append("banners LIKE ?")
                service_params.append(filters["banner"])

        # If filtering by services, we need to join to get matching hosts
        if service_where:
            # Get host IDs that have matching services
            service_filter_sql = " AND ".join(service_where)
            cursor.execute(
                f"""
                SELECT DISTINCT host_id
                FROM {self.services_table}
                WHERE {service_filter_sql}
            """,
                service_params,
            )
            matching_host_ids = [row["host_id"] for row in cursor.fetchall()]

            if not matching_host_ids:
                return Infrastructure([], identifier or f"Database:{self.project}")

            # Add host ID filter
            placeholders = ",".join("?" * len(matching_host_ids))
            host_where.append(f"id IN ({placeholders})")
            host_params.extend(matching_host_ids)

        # Build final host query
        host_query = f"""
            SELECT id, address, hostnames, os, custom_fields
            FROM {self.hosts_table}
        """
        if host_where:
            host_query += " WHERE " + " AND ".join(host_where)
        host_query += " ORDER BY address"

        # Fetch filtered hosts
        cursor.execute(host_query, host_params)
        host_rows = cursor.fetchall()
        hosts = []

        import json

        for host_row in host_rows:
            # Parse comma-separated values back to sets
            addresses = (
                set(host_row["address"].split(",")) if host_row["address"] else set()
            )
            hostnames = (
                set(host_row["hostnames"].split(","))
                if host_row["hostnames"]
                else set()
            )
            os_list = (
                set((os, "database") for os in host_row["os"].split(","))
                if host_row["os"]
                else set()
            )
            custom_fields = (
                {k: set(v) for k, v in json.loads(host_row["custom_fields"]).items()}
                if host_row["custom_fields"]
                else {}
            )

            host = Host(
                address=addresses,
                hostnames=hostnames,
                os=os_list,
                custom_fields=custom_fields,
            )

            # Fetch services for this host (apply service filters)
            service_query = f"""
                SELECT port, protocol, service_names, banners, custom_fields
                FROM {self.services_table}
                WHERE host_id = ?
            """
            query_params = [host_row["id"]]

            if service_where:
                service_query += " AND " + " AND ".join(service_where)
                query_params.extend(service_params)

            service_query += " ORDER BY port"

            cursor.execute(service_query, query_params)
            service_rows = cursor.fetchall()

            for service_row in service_rows:
                service_names = (
                    SortedSet(service_row["service_names"].split(","))
                    if service_row["service_names"]
                    else SortedSet()
                )
                banners = (
                    SortedSet(service_row["banners"].split(","))
                    if service_row["banners"]
                    else SortedSet()
                )
                service_custom_fields = (
                    {
                        k: set(v)
                        for k, v in json.loads(service_row["custom_fields"]).items()
                    }
                    if service_row["custom_fields"]
                    else {}
                )

                service = Service(
                    port=service_row["port"],
                    protocol=service_row["protocol"],
                    service_names=service_names,
                    banners=banners,
                    custom_fields=service_custom_fields,
                )

                host.add_service(service)

            hosts.append(host)

        return Infrastructure(hosts, identifier or f"Database:{self.project}")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the current project.

        Returns
        -------
        dict
            Statistics including host count, service count, etc.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()

        # Check if tables exist
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """,
            (self.hosts_table,),
        )

        if not cursor.fetchone():
            return {"project": self.project, "hosts": 0, "services": 0, "protocols": []}

        # Count hosts
        cursor.execute(f"SELECT COUNT(*) as count FROM {self.hosts_table}")
        host_count = cursor.fetchone()["count"]

        # Count services
        cursor.execute(f"SELECT COUNT(*) as count FROM {self.services_table}")
        service_count = cursor.fetchone()["count"]

        # Get protocols
        cursor.execute(f"SELECT DISTINCT protocol FROM {self.services_table}")
        protocols = [row["protocol"] for row in cursor.fetchall()]

        return {
            "project": self.project,
            "hosts": host_count,
            "services": service_count,
            "protocols": protocols,
        }
