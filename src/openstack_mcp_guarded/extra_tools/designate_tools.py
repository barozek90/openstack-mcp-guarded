"""Designate (DNS as a Service) tools.

Read tools follow the upstream convention (``get_*``) and are allowed by
the read-only policy. Write tools (``create_/update_/delete_*``) are
registered so the escalation path only needs a policy change - they are
hard-blocked by default.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from openstack_mcp_server.tools.base import get_openstack_conn

from .helpers import _pick


class DesignateTools:
    """DNS zone / recordset tools backed by the openstacksdk dns proxy."""

    def register_tools(self, mcp: FastMCP) -> None:
        # read
        mcp.tool()(self.get_dns_zones)
        mcp.tool()(self.get_dns_zone_detail)
        mcp.tool()(self.get_dns_zone_nameservers)
        mcp.tool()(self.get_dns_recordsets)
        mcp.tool()(self.get_dns_recordset_detail)
        mcp.tool()(self.get_dns_zone_exports)
        mcp.tool()(self.get_dns_zone_imports)
        mcp.tool()(self.get_dns_zone_transfer_requests)
        mcp.tool()(self.get_dns_limits)
        mcp.tool()(self.get_dns_quota)
        # write (blocked by default policy)
        mcp.tool()(self.create_dns_zone)
        mcp.tool()(self.update_dns_zone)
        mcp.tool()(self.delete_dns_zone)
        mcp.tool()(self.create_dns_recordset)
        mcp.tool()(self.update_dns_recordset)
        mcp.tool()(self.delete_dns_recordset)

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def get_dns_zones(
        self,
        name: str | None = None,
        zone_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """List DNS zones with optional filters."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if name:
            query["name"] = name
        if zone_type:
            query["type"] = zone_type.upper()
        if status:
            query["status"] = status.upper()
        return [
            _pick(
                z,
                "id", "name", "description", "type", "status", "action",
                "serial", "email", "ttl", "masters", "attributes",
                "transferred_at", "version", "created_at", "updated_at",
                "project_id", "pool_id",
            )
            for z in conn.dns.zones(**query)
        ]

    def get_dns_zone_detail(self, zone_id: str) -> dict:
        """Get detailed information about a specific DNS zone."""
        conn = get_openstack_conn()
        zone = conn.dns.find_zone(zone_id, ignore_missing=False)
        return _pick(
            zone,
            "id", "name", "description", "type", "status", "action",
            "serial", "email", "ttl", "masters", "attributes",
            "created_at", "updated_at", "project_id", "pool_id",
        )

    def get_dns_zone_nameservers(self, zone_id: str) -> list[dict]:
        """List nameservers assigned to a DNS zone."""
        conn = get_openstack_conn()
        return [
            _pick(ns, "hostname", "priority")
            for ns in conn.dns.zone_nameservers(zone_id)
        ]

    def get_dns_recordsets(
        self,
        zone_id: str | None = None,
        record_type: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        """List recordsets, optionally filtered by zone, type (A/AAAA/CNAME/MX/TXT/SRV/PTR/CAA/NS) or name."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if record_type:
            query["type"] = record_type.upper()
        if name:
            query["name"] = name
        return [
            _pick(
                rs,
                "id", "zone_id", "zone_name", "name", "type", "records",
                "description", "ttl", "status", "action", "created_at",
                "updated_at", "version",
            )
            for rs in conn.dns.recordsets(zone=zone_id, **query)
        ]

    def get_dns_recordset_detail(self, zone_id: str, recordset_id: str) -> dict:
        """Get detailed information about a specific recordset."""
        conn = get_openstack_conn()
        rs = conn.dns.get_recordset(recordset_id, zone=zone_id)
        return _pick(
            rs,
            "id", "zone_id", "zone_name", "name", "type", "records",
            "description", "ttl", "status", "action", "created_at",
            "updated_at", "version",
        )

    def get_dns_zone_exports(self) -> list[dict]:
        """List DNS zone export jobs."""
        conn = get_openstack_conn()
        return [
            _pick(e, "id", "zone_id", "status", "created_at", "updated_at", "message")
            for e in conn.dns.zone_exports()
        ]

    def get_dns_zone_imports(self) -> list[dict]:
        """List DNS zone import jobs."""
        conn = get_openstack_conn()
        return [
            _pick(i, "id", "status", "created_at", "updated_at", "message")
            for i in conn.dns.zone_imports()
        ]

    def get_dns_zone_transfer_requests(self) -> list[dict]:
        """List DNS zone transfer requests."""
        conn = get_openstack_conn()
        return [
            _pick(
                t,
                "id", "zone_id", "zone_name", "target_project_id",
                "description", "status", "created_at", "updated_at",
            )
            for t in conn.dns.zone_transfer_requests()
        ]

    def get_dns_limits(self) -> list[dict]:
        """List Designate API limits."""
        conn = get_openstack_conn()
        return [
            _pick(l, "name", "value", "resource", "verb")
            for l in conn.dns.limits()
        ]

    def get_dns_quota(self, project_id: str) -> dict:
        """Get Designate quotas for a project."""
        conn = get_openstack_conn()
        quota = conn.dns.get_quota(project_id)
        return _pick(
            quota,
            "zones", "recordset_records", "zone_records", "zone_recordsets",
            "api_export_size", "api_page_size_default", "api_page_size_max",
            "min_ttl",
        )

    # ------------------------------------------------------------------
    # write (blocked by the default read-only policy)
    # ------------------------------------------------------------------

    def create_dns_zone(
        self,
        name: str,
        email: str,
        zone_type: str = "PRIMARY",
        ttl: int | None = None,
        description: str | None = None,
        attributes: dict | None = None,
        masters: list[str] | None = None,
    ) -> dict:
        """Create a DNS zone (e.g. name='example.com.', email='hostmaster@example.com.')."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "name": name,
            "email": email,
            "type": zone_type.upper(),
        }
        if ttl is not None:
            attrs["ttl"] = ttl
        if description:
            attrs["description"] = description
        if attributes:
            attrs["attributes"] = attributes
        if masters:
            attrs["masters"] = masters
        zone = conn.dns.create_zone(**attrs)
        return _pick(zone, "id", "name", "type", "status", "ttl")

    def update_dns_zone(
        self,
        zone_id: str,
        email: str | None = None,
        ttl: int | None = None,
        description: str | None = None,
    ) -> dict:
        """Update DNS zone attributes."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {}
        if email is not None:
            attrs["email"] = email
        if ttl is not None:
            attrs["ttl"] = ttl
        if description is not None:
            attrs["description"] = description
        zone = conn.dns.update_zone(zone_id, **attrs)
        return _pick(zone, "id", "name", "ttl", "email", "description")

    def delete_dns_zone(self, zone_id: str, delete_shares: bool = False) -> None:
        """Delete a DNS zone."""
        conn = get_openstack_conn()
        conn.dns.delete_zone(zone_id, delete_shares=delete_shares)

    def create_dns_recordset(
        self,
        zone_id: str,
        name: str,
        record_type: str,
        records: list[str],
        ttl: int | None = None,
        description: str | None = None,
    ) -> dict:
        """Create a recordset in a zone (type: A/AAAA/CNAME/MX/TXT/SRV/PTR/NS/CAA)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "name": name,
            "type": record_type.upper(),
            "records": records,
        }
        if ttl is not None:
            attrs["ttl"] = ttl
        if description:
            attrs["description"] = description
        rs = conn.dns.create_recordset(zone_id, **attrs)
        return _pick(rs, "id", "name", "type", "records", "ttl", "status")

    def update_dns_recordset(
        self,
        zone_id: str,
        recordset_id: str,
        records: list[str] | None = None,
        ttl: int | None = None,
        description: str | None = None,
    ) -> dict:
        """Update a recordset (e.g. change records or TTL)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {}
        if records is not None:
            attrs["records"] = records
        if ttl is not None:
            attrs["ttl"] = ttl
        if description is not None:
            attrs["description"] = description
        rs = conn.dns.update_recordset(recordset_id, **attrs)
        return _pick(rs, "id", "name", "type", "records", "ttl")

    def delete_dns_recordset(self, zone_id: str, recordset_id: str) -> None:
        """Delete a recordset."""
        conn = get_openstack_conn()
        conn.dns.delete_recordset(recordset_id, zone=zone_id, ignore_missing=False)
