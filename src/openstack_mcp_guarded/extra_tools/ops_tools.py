"""Operational read tools + Heat orchestration tools.

Covers the day-2 operations surface that upstream 1.0.0 lacks:
keypairs, server groups, availability zones, hypervisors, compute
services, quotas, server actions/events, plus Heat stacks (read-only
view). Write tools follow the same convention: registered, but
hard-blocked by the default read-only policy.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from openstack_mcp_server.tools.base import get_openstack_conn

from .helpers import _pick


class OpsTools:
    """Operational & orchestration tools on top of openstacksdk."""

    def register_tools(self, mcp: FastMCP) -> None:
        # read: compute ops
        mcp.tool()(self.get_keypairs)
        mcp.tool()(self.get_server_groups)
        mcp.tool()(self.get_availability_zones)
        mcp.tool()(self.get_hypervisors)
        mcp.tool()(self.get_hypervisor_uptime)
        mcp.tool()(self.get_compute_services)
        mcp.tool()(self.get_compute_quotas)
        mcp.tool()(self.get_server_actions)
        # read: heat
        mcp.tool()(self.get_heat_stacks)
        mcp.tool()(self.get_heat_stack_detail)
        mcp.tool()(self.get_heat_stack_resources)
        mcp.tool()(self.get_heat_stack_events)
        mcp.tool()(self.get_heat_stack_template)
        # write (blocked by default policy)
        mcp.tool()(self.create_keypair)
        mcp.tool()(self.delete_keypair)
        mcp.tool()(self.create_server_group)
        mcp.tool()(self.delete_server_group)
        mcp.tool()(self.create_heat_stack)
        mcp.tool()(self.update_heat_stack)
        mcp.tool()(self.delete_heat_stack)

    # ------------------------------------------------------------------
    # read: compute ops
    # ------------------------------------------------------------------

    def get_keypairs(self, name: str | None = None) -> list[dict]:
        """List key pairs (optionally filter by name)."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if name:
            query["name"] = name
        return [
            _pick(k, "id", "name", "fingerprint", "type", "created_at")
            for k in conn.compute.keypairs(**query)
        ]

    def get_server_groups(self) -> list[dict]:
        """List server groups (affinity/anti-affinity scheduling)."""
        conn = get_openstack_conn()
        return [
            _pick(g, "id", "name", "policies", "members", "project_id", "user_id")
            for g in conn.compute.server_groups()
        ]

    def get_availability_zones(self, detailed: bool = False) -> list[dict]:
        """List compute availability zones (detailed=True adds host info, admin only)."""
        conn = get_openstack_conn()
        return [
            _pick(az, "zoneName", "zoneState", "hosts")
            for az in conn.compute.availability_zones(details=detailed)
        ]

    def get_hypervisors(
        self,
        hypervisor_hostname_pattern: str | None = None,
    ) -> list[dict]:
        """List hypervisors with CPU/memory/disk stats (admin only)."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if hypervisor_hostname_pattern:
            query["hypervisor_hostname_pattern"] = hypervisor_hostname_pattern
        return [
            _pick(
                h,
                "id", "hypervisor_hostname", "hostname", "state", "status",
                "vcpus", "vcpus_used", "memory_mb", "memory_mb_used",
                "local_gb", "local_gb_used", "running_vms", "cpu_info",
                "service",
            )
            for h in conn.compute.hypervisors(details=True, **query)
        ]

    def get_hypervisor_uptime(self, hypervisor_id: str) -> dict:
        """Get uptime of a hypervisor (admin only)."""
        conn = get_openstack_conn()
        h = conn.compute.get_hypervisor_uptime(hypervisor_id)
        return _pick(h, "id", "hypervisor_hostname", "uptime")

    def get_compute_services(self, binary: str | None = None) -> list[dict]:
        """List compute services (nova-compute, scheduler...) with status (admin only)."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if binary:
            query["binary"] = binary
        return [
            _pick(
                s,
                "id", "binary", "host", "zone", "status", "state",
                "updated_at", "disabled_reason", "forced_down",
            )
            for s in conn.compute.services(**query)
        ]

    def get_compute_quotas(self, project_id: str, usage: bool = False) -> dict:
        """Get compute quotas for a project (optionally with usage)."""
        conn = get_openstack_conn()
        quota = conn.compute.get_quota_set(project, usage=usage)
        return _pick(
            quota,
            "instances", "cores", "ram", "floating_ips", "fixed_ips",
            "security_groups", "security_group_rules", "key_pairs",
            "server_groups", "server_group_members", "total_instances_used",
            "total_cores_used", "total_ram_used",
        )

    def get_server_actions(self, server_id: str) -> list[dict]:
        """List lifecycle actions/events of a server (audit trail)."""
        conn = get_openstack_conn()
        return [
            _pick(
                a,
                "request_id", "action", "user_id", "project_id",
                "start_time", "finish_time", "message", "instance_id",
            )
            for a in conn.compute.server_actions(server_id)
        ]

    # ------------------------------------------------------------------
    # read: heat
    # ------------------------------------------------------------------

    def get_heat_stacks(
        self,
        status: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        """List Heat stacks with optional status/name filters."""
        conn = get_openstack_conn()
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.upper()
        if name:
            query["name"] = name
        return [
            _pick(
                s,
                "id", "stack_name", "stack_status", "stack_status_reason",
                "description", "creation_time", "updated_time",
                "tags", "project_id",
            )
            for s in conn.orchestration.stacks(**query)
        ]

    def get_heat_stack_detail(self, stack_id: str) -> dict:
        """Get detailed information about a stack (incl. outputs)."""
        conn = get_openstack_conn()
        stack = conn.orchestration.find_stack(
            stack_id, ignore_missing=False, resolve_outputs=True
        )
        return _pick(
            stack,
            "id", "stack_name", "stack_status", "stack_status_reason",
            "description", "creation_time", "updated_time", "tags",
            "parameters", "outputs", "capabilities", "notification_topics",
            "timeout_mins", "disable_rollback",
        )

    def get_heat_stack_resources(self, stack_id: str) -> list[dict]:
        """List resources of a stack."""
        conn = get_openstack_conn()
        return [
            _pick(
                r,
                "resource_name", "resource_type", "resource_status",
                "resource_status_reason", "physical_resource_id",
                "updated_time", "links",
            )
            for r in conn.orchestration.resources(stack_id)
        ]

    def get_heat_stack_events(
        self,
        stack_id: str,
        resource_name: str | None = None,
    ) -> list[dict]:
        """List events of a stack (optionally of a single resource)."""
        conn = get_openstack_conn()
        return [
            _pick(
                e,
                "id", "resource_name", "resource_type", "resource_status",
                "resource_status_reason", "event_time", "logical_resource_id",
            )
            for e in conn.orchestration.stack_events(
                stack_id, resource_name=resource_name
            )
        ]

    def get_heat_stack_template(self, stack_id: str) -> dict:
        """Get the template of a stack."""
        conn = get_openstack_conn()
        template = conn.orchestration.get_stack_template(stack_id)
        return {"template": template}

    # ------------------------------------------------------------------
    # write (blocked by the default read-only policy)
    # ------------------------------------------------------------------

    def create_keypair(self, name: str, key_type: str = "ssh") -> dict:
        """Create an SSH keypair (returns the private key ONCE)."""
        conn = get_openstack_conn()
        kp = conn.compute.create_keypair(name=name, type=key_type)
        return _pick(kp, "id", "name", "type", "fingerprint", "private_key")

    def delete_keypair(self, name: str) -> None:
        """Delete an SSH keypair."""
        conn = get_openstack_conn()
        conn.compute.delete_keypair(name, ignore_missing=False)

    def create_server_group(
        self,
        name: str,
        policies: list[str],
    ) -> dict:
        """Create a server group (policies: affinity/anti-affinity/soft-*, ...)."""
        conn = get_openstack_conn()
        group = conn.compute.create_server_group(name=name, policies=policies)
        return _pick(group, "id", "name", "policies", "members")

    def delete_server_group(self, server_group_id: str) -> None:
        """Delete a server group."""
        conn = get_openstack_conn()
        conn.compute.delete_server_group(server_group_id, ignore_missing=False)

    def create_heat_stack(
        self,
        stack_name: str,
        template: dict,
        environment: dict | None = None,
        parameters: dict | None = None,
        timeout_mins: int | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Create a Heat stack from a template dict (YAML parsed)."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {
            "stack_name": stack_name,
            "template": template,
        }
        if environment is not None:
            attrs["environment"] = environment
        if parameters is not None:
            attrs["parameters"] = parameters
        if timeout_mins is not None:
            attrs["timeout_mins"] = timeout_mins
        if tags is not None:
            attrs["tags"] = tags
        stack = conn.orchestration.create_stack(**attrs)
        return _pick(stack, "id", "stack_name", "stack_status")

    def update_heat_stack(
        self,
        stack_id: str,
        template: dict,
        environment: dict | None = None,
        parameters: dict | None = None,
        timeout_mins: int | None = None,
    ) -> dict:
        """Update an existing Heat stack with a new template."""
        conn = get_openstack_conn()
        attrs: dict[str, Any] = {"template": template}
        if environment is not None:
            attrs["environment"] = environment
        if parameters is not None:
            attrs["parameters"] = parameters
        if timeout_mins is not None:
            attrs["timeout_mins"] = timeout_mins
        stack = conn.orchestration.update_stack(stack_id, **attrs)
        return _pick(stack, "id", "stack_name", "stack_status")

    def delete_heat_stack(self, stack_id: str) -> None:
        """Delete a Heat stack."""
        conn = get_openstack_conn()
        conn.orchestration.delete_stack(stack_id, ignore_missing=False)
