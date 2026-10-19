"""Octavia (Load Balancer as a Service) tools.

Read tools follow the upstream convention (``get_*``) and are allowed by
the read-only policy. Write tools (``create_/update_/delete_/failover_*``)
are registered so the escalation path only needs a policy change - they
are hard-blocked by default.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from openstack_mcp_server.tools.base import get_openstack_conn


def _pick(obj: Any, *fields: str) -> dict[str, Any]:
    """Project selected attributes of an SDK resource into a dict."""
    out: dict[str, Any] = {}
    for f in fields:
        out[f] = getattr(obj, f, None)
    return out


def _lb_ref(lb: Any) -> list[str]:
    return [item.get("id") for item in (getattr(lb, "load_balancers", None) or []) if isinstance(item, dict)]


class OctaviaTools:
    """Load balancer tools backed by the openstacksdk load_balancer proxy."""

    def register_tools(self, mcp: FastMCP) -> None:
        # read
        mcp.tool()(self.get_load_balancers)
        mcp.tool()(self.get_load_balancer_detail)
        mcp.tool()(self.get_load_balancer_statistics)
        mcp.tool()(self.get_listeners)
        mcp.tool()(self.get_listener_statistics)
        mcp.tool()(self.get_pools)
        mcp.tool()(self.get_pool_members)
        mcp.tool()(self.get_health_monitors)
        mcp.tool()(self.get_load_balancer_providers)
        mcp.tool()(self.get_load_balancer_flavors)
        mcp.tool()(self.get_amphorae)
        # write (blocked by default policy)
        mcp.tool()(self.create_load_balancer)
        mcp.tool()(self.update_load_balancer)
        mcp.tool()(self.delete_load_balancer)
        mcp.tool()(self.failover_load_balancer)
        mcp.tool()(self.create_listener)
        mcp.tool()(self.delete_listener)
        mcp.tool()(self.create_pool)
        mcp.tool()(self.delete_pool)
        mcp.tool()(self.create_pool_member)
        mcp.tool()(self.update_pool_member)
        mcp.tool()(self.delete_pool_member)
        mcp.tool()(self.create_health_monitor)
        mcp.tool()(self.delete_health_monitor)

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def get_load_balancers(
        self,
        provisioning_status: str | None = None,
        operating_status: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        """List load balancers with optional status/name filters."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if provisioning_status:
            query["provisioning_status"] = provisioning_status.upper()
        if operating_status:
            query["operating_status"] = operating_status.upper()
        if name:
            query["name"] = name
        return [
            _pick(
                lb,
                "id", "name", "description", "operating_status",
                "provisioning_status", "vip_address", "vip_network_id",
                "vip_subnet_id", "provider", "flavor_id", "created_at",
                "updated_at", "tags",
            )
            for lb in conn.load_balancer.load_balancers(**query)
        ]

    def get_load_balancer_detail(self, load_balancer_id: str) -> dict:
        """Get detailed information about a specific load balancer."""
        conn = get_openstack_conn()
        lb = conn.load_balancer.find_load_balancer(
            load_balancer_id, ignore_missing=False
        )
        return _pick(
            lb,
            "id", "name", "description", "operating_status",
            "provisioning_status", "vip_address", "vip_port_id",
            "vip_network_id", "vip_subnet_id", "provider", "flavor_id",
            "admin_state_up", "created_at", "updated_at", "tags",
        ) | {"listeners": _lb_ref(lb)}

    def get_load_balancer_statistics(self, load_balancer_id: str) -> dict:
        """Get traffic statistics (bytes, connections, errors) for a load balancer."""
        conn = get_openstack_conn()
        stats = conn.load_balancer.get_load_balancer_statistics(
            load_balancer_id
        )
        return _pick(
            stats, "bytes_in", "bytes_out", "active_connections",
            "total_connections", "request_errors",
        )

    def get_listeners(
        self,
        load_balancer_id: str | None = None,
        protocol: str | None = None,
    ) -> list[dict]:
        """List listeners, optionally filtered by load balancer or protocol."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if load_balancer_id:
            query["load_balancer_id"] = load_balancer_id
        if protocol:
            query["protocol"] = protocol.upper()
        return [
            _pick(
                lst,
                "id", "name", "description", "protocol", "protocol_port",
                "operating_status", "provisioning_status",
                "default_pool_id", "connection_limit",
                "insert_headers", "created_at", "updated_at",
            )
            | {"load_balancers": _lb_ref(lst)}
            for lst in conn.load_balancer.listeners(**query)
        ]

    def get_listener_statistics(self, listener_id: str) -> dict:
        """Get traffic statistics for a specific listener."""
        conn = get_openstack_conn()
        stats = conn.load_balancer.get_listener_statistics(listener_id)
        return _pick(
            stats, "bytes_in", "bytes_out", "active_connections",
            "total_connections", "request_errors",
        )

    def get_pools(
        self,
        load_balancer_id: str | None = None,
        protocol: str | None = None,
    ) -> list[dict]:
        """List pools, optionally filtered by load balancer or protocol."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if load_balancer_id:
            query["load_balancer_id"] = load_balancer_id
        if protocol:
            query["protocol"] = protocol.upper()
        return [
            _pick(
                pool,
                "id", "name", "description", "protocol", "lb_algorithm",
                "operating_status", "provisioning_status",
                "healthmonitor_id", "session_persistence", "created_at",
            )
            | {"load_balancers": _lb_ref(pool)}
            for pool in conn.load_balancer.pools(**query)
        ]

    def get_pool_members(self, pool_id: str) -> list[dict]:
        """List members of a specific pool."""
        conn = get_openstack_conn()
        return [
            _pick(
                member,
                "id", "name", "address", "protocol_port", "weight",
                "operating_status", "provisioning_status",
                "admin_state_up", "subnet_id", "backup",
            )
            for member in conn.load_balancer.members(pool_id)
        ]

    def get_health_monitors(
        self,
        pool_id: str | None = None,
    ) -> list[dict]:
        """List health monitors, optionally filtered by pool."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if pool_id:
            query["pool_id"] = pool_id
        return [
            _pick(
                hm,
                "id", "name", "type", "delay", "timeout", "max_retries",
                "max_retries_down", "http_method", "url_path",
                "expected_codes", "operating_status",
                "provisioning_status", "admin_state_up", "pools",
            )
            for hm in conn.load_balancer.health_monitors(**query)
        ]

    def get_load_balancer_providers(self) -> list[dict]:
        """List available load balancer providers (e.g. amphora, ovn)."""
        conn = get_openstack_conn()
        return [
            _pick(p, "name", "description") for p in conn.load_balancer.providers()
        ]

    def get_load_balancer_flavors(self) -> list[dict]:
        """List load balancer flavors."""
        conn = get_openstack_conn()
        return [
            _pick(f, "id", "name", "description", "enabled", "providers")
            for f in conn.load_balancer.flavors()
        ]

    def get_amphorae(
        self,
        load_balancer_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """List amphora instances (requires admin role)."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if load_balancer_id:
            query["load_balancer_id"] = load_balancer_id
        if status:
            query["status"] = status.upper()
        return [
            _pick(
                amp,
                "id", "loadbalancer_id", "compute_id", "status", "role",
                "lb_network_ip", "ha_ip", "vrrp_id", "created_at",
                "updated_at", "image_id", "compute_name",
            )
            for amp in conn.load_balancer.amphorae(**query)
        ]

    # ------------------------------------------------------------------
    # write (blocked by the default read-only policy)
    # ------------------------------------------------------------------

    def create_load_balancer(
        self,
        name: str,
        vip_subnet_id: str | None = None,
        vip_network_id: str | None = None,
        vip_address: str | None = None,
        provider: str | None = None,
        flavor_id: str | None = None,
        description: str | None = None,
        admin_state_up: bool = True,
    ) -> dict:
        """Create a new load balancer."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {"name": name, "admin_state_up": admin_state_up}
        for key, value in (
            ("vip_subnet_id", vip_subnet_id),
            ("vip_network_id", vip_network_id),
            ("vip_address", vip_address),
            ("provider", provider),
            ("flavor_id", flavor_id),
            ("description", description),
        ):
            if value is not None:
                attrs[key] = value
        lb = conn.load_balancer.create_load_balancer(**attrs)
        return _pick(lb, "id", "name", "provisioning_status", "operating_status")

    def update_load_balancer(
        self,
        load_balancer_id: str,
        name: str | None = None,
        description: str | None = None,
        admin_state_up: bool | None = None,
    ) -> dict:
        """Update load balancer attributes."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {}
        if name is not None:
            attrs["name"] = name
        if description is not None:
            attrs["description"] = description
        if admin_state_up is not None:
            attrs["admin_state_up"] = admin_state_up
        lb = conn.load_balancer.update_load_balancer(load_balancer_id, **attrs)
        return _pick(lb, "id", "name", "provisioning_status", "operating_status")

    def delete_load_balancer(
        self,
        load_balancer_id: str,
        cascade: bool = False,
    ) -> None:
        """Delete a load balancer (cascade also removes listeners/pools/members)."""
        conn = get_openstack_conn()
        conn.load_balancer.delete_load_balancer(
            load_balancer_id, cascade=cascade
        )

    def failover_load_balancer(self, load_balancer_id: str) -> None:
        """Trigger failover of a load balancer (rebuilds its amphorae)."""
        conn = get_openstack_conn()
        conn.load_balancer.failover_load_balancer(load_balancer_id)

    def create_listener(
        self,
        name: str,
        load_balancer_id: str,
        protocol: str,
        protocol_port: int,
        default_pool_id: str | None = None,
        connection_limit: int | None = None,
        tls_container_ref: str | None = None,
        description: str | None = None,
    ) -> dict:
        """Create a listener on a load balancer (protocol: TCP/HTTP/HTTPS/TERMINATED_HTTPS/UDP)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "name": name,
            "load_balancer_id": load_balancer_id,
            "protocol": protocol.upper(),
            "protocol_port": protocol_port,
        }
        for key, value in (
            ("default_pool_id", default_pool_id),
            ("connection_limit", connection_limit),
            ("tls_container_ref", tls_container_ref),
            ("description", description),
        ):
            if value is not None:
                attrs[key] = value
        lst = conn.load_balancer.create_listener(**attrs)
        return _pick(lst, "id", "name", "protocol", "protocol_port")

    def delete_listener(self, listener_id: str) -> None:
        """Delete a listener."""
        conn = get_openstack_conn()
        conn.load_balancer.delete_listener(listener_id, ignore_missing=False)

    def create_pool(
        self,
        name: str,
        load_balancer_id: str,
        protocol: str,
        lb_algorithm: str,
        listener_id: str | None = None,
        description: str | None = None,
    ) -> dict:
        """Create a pool on a load balancer (lb_algorithm: ROUND_ROBIN/LEAST_CONNECTIONS/SOURCE_IP)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "name": name,
            "load_balancer_id": load_balancer_id,
            "protocol": protocol.upper(),
            "lb_algorithm": lb_algorithm.upper(),
        }
        if listener_id:
            attrs["listener_id"] = listener_id
        if description:
            attrs["description"] = description
        pool = conn.load_balancer.create_pool(**attrs)
        return _pick(pool, "id", "name", "protocol", "lb_algorithm")

    def delete_pool(self, pool_id: str) -> None:
        """Delete a pool."""
        conn = get_openstack_conn()
        conn.load_balancer.delete_pool(pool_id, ignore_missing=False)

    def create_pool_member(
        self,
        pool_id: str,
        address: str,
        protocol_port: int,
        name: str | None = None,
        subnet_id: str | None = None,
        weight: int = 1,
        admin_state_up: bool = True,
    ) -> dict:
        """Add a member (backend server) to a pool."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "address": address,
            "protocol_port": protocol_port,
            "weight": weight,
            "admin_state_up": admin_state_up,
        }
        if name:
            attrs["name"] = name
        if subnet_id:
            attrs["subnet_id"] = subnet_id
        member = conn.load_balancer.create_member(pool_id, **attrs)
        return _pick(member, "id", "name", "address", "protocol_port", "weight")

    def update_pool_member(
        self,
        pool_id: str,
        member_id: str,
        weight: int | None = None,
        admin_state_up: bool | None = None,
        name: str | None = None,
    ) -> dict:
        """Update a pool member (e.g. drain by admin_state_up=False)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {}
        if weight is not None:
            attrs["weight"] = weight
        if admin_state_up is not None:
            attrs["admin_state_up"] = admin_state_up
        if name is not None:
            attrs["name"] = name
        member = conn.load_balancer.update_member(
            member_id, pool_id, **attrs
        )
        return _pick(member, "id", "name", "weight", "admin_state_up")

    def delete_pool_member(self, pool_id: str, member_id: str) -> None:
        """Remove a member from a pool."""
        conn = get_openstack_conn()
        conn.load_balancer.delete_member(
            member_id, pool_id, ignore_missing=False
        )

    def create_health_monitor(
        self,
        pool_id: str,
        type: str,
        delay: int,
        timeout: int,
        max_retries: int,
        url_path: str = "/",
        expected_codes: str = "200",
        http_method: str = "GET",
        max_retries_down: int = 3,
        name: str | None = None,
    ) -> dict:
        """Create a health monitor for a pool (type: HTTP/HTTPS/TCP/UDP/TLS-HELLO/PING)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "pool_id": pool_id,
            "type": type.upper(),
            "delay": delay,
            "timeout": timeout,
            "max_retries": max_retries,
            "max_retries_down": max_retries_down,
        }
        if type.upper() in ("HTTP", "HTTPS", "TLS-HELLO"):
            attrs["url_path"] = url_path
            attrs["expected_codes"] = expected_codes
            attrs["http_method"] = http_method.upper()
        if name:
            attrs["name"] = name
        hm = conn.load_balancer.create_health_monitor(**attrs)
        return _pick(hm, "id", "type", "delay", "timeout", "operating_status")

    def delete_health_monitor(self, health_monitor_id: str) -> None:
        """Delete a health monitor."""
        conn = get_openstack_conn()
        conn.load_balancer.delete_health_monitor(
            health_monitor_id, ignore_missing=False
        )
