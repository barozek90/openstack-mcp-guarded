"""Integration tests: policy enforcement through the MCP protocol.

Uses the in-memory fastmcp client (same protocol path as real clients
like opencode / Claude Code) to verify that the middleware actually
cuts the protocol, not just the Python API.
"""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from openstack_mcp_guarded.policy import Policy
from openstack_mcp_guarded.server import create_mcp


@pytest.fixture()
def read_only_policy():
    return Policy(mode="read-only", source="test")


@pytest.fixture()
def no_cloud(monkeypatch):
    """Ensure no cloud is selected (upstream default is 'openstack')."""
    from openstack_mcp_server.tools.connection import ConnectionManager

    monkeypatch.setattr(ConnectionManager, "_cloud_name", "")
    yield
    monkeypatch.setattr(ConnectionManager, "_cloud_name", "")


@pytest.fixture()
def cloud_selected(monkeypatch):
    """Pretend a valid cloud is selected (no network I/O involved)."""
    from openstack_mcp_server.tools.connection import ConnectionManager

    monkeypatch.setattr(ConnectionManager, "_cloud_name", "RegionOne")
    yield
    monkeypatch.setattr(ConnectionManager, "_cloud_name", "")


async def test_read_only_hides_write_tools(read_only_policy, no_cloud):
    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}

    assert "get_servers" in tools
    assert "get_cloud_names" in tools
    assert "set_cloud_name" in tools
    for blocked in (
        "delete_server",
        "create_server",
        "update_server",
        "action_server",
        "attach_volume",
        "detach_volume",
        "create_volume",
        "delete_volume",
        "extend_volume",
        "create_image",
        "delete_image",
        "create_network",
        "delete_network",
        "update_network",
        "create_port",
        "delete_port",
        "update_port",
        "set_port_binding",
        "create_floating_ip",
        "delete_floating_ip",
        "update_floating_ip",
        "create_floating_ips_bulk",
        "assign_first_available_floating_ip",
        "create_router",
        "delete_router",
        "update_router",
        "add_router_interface",
        "remove_router_interface",
        "create_security_group",
        "delete_security_group",
        "create_project",
        "delete_project",
        "update_project",
        "create_domain",
        "delete_domain",
        "update_domain",
        "create_region",
        "delete_region",
        "update_region",
        "update_subnet",
        "delete_subnet",
    ):
        assert blocked not in tools, f"{blocked} should be hidden"


    async def test_read_only_visible_count(read_only_policy, no_cloud):
        """28 read tools (get_*) + 4 session tools = 32 visible in read-only mode."""
        mcp = create_mcp(policy=read_only_policy)
        async with Client(mcp) as client:
            tools = await client.list_tools()
        assert len(tools) == 32


async def test_hard_block_write_tool(read_only_policy, cloud_selected):
    """Calling a hidden tool directly must fail with ToolError."""
    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Blocked by openstack-mcp-guarded"):
            await client.call_tool("delete_server", {"id": "fake-uuid"})


async def test_hard_block_action_server(read_only_policy, cloud_selected):
    """action_server (start/stop/pause VMs) must be blocked too."""
    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Blocked by openstack-mcp-guarded"):
            await client.call_tool(
                "action_server", {"id": "fake-uuid", "action": "stop"}
            )


async def test_no_cloud_guard(read_only_policy, no_cloud):
    """Cloud tools must be blocked until a cloud is selected."""
    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="no OpenStack cloud is selected"):
            await client.call_tool("get_servers", {})


async def test_no_cloud_guard_hint_lists_clouds(read_only_policy, no_cloud):
    """The block message should hint available clouds from clouds.yaml."""
    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="RegionOne"):
            await client.call_tool("get_servers", {})


async def test_session_tools_work_without_cloud(read_only_policy, no_cloud):
    """get_cloud_names / set_cloud_name must work before cloud selection."""
    from openstack_mcp_server.tools.connection import ConnectionManager

    mcp = create_mcp(policy=read_only_policy)
    async with Client(mcp) as client:
        result = await client.call_tool("get_cloud_names", {})
        clouds = result.data
        assert "RegionOne" in clouds

        await client.call_tool("set_cloud_name", {"cloud_name": "RegionOne"})
        assert ConnectionManager.get_cloud_name() == "RegionOne"


async def test_custom_mode_allows_selected_tools():
    """Custom mode: allowlist from policy, deny wins over allow."""
    policy = Policy(
        mode="custom",
        allow=("get_*", "create_volume"),
        deny=("*_domain",),
        source="test",
    )
    mcp = create_mcp(policy=policy)
    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}

    assert "create_volume" in tools
    assert "delete_server" not in tools  # not on allowlist
    assert "create_domain" not in tools  # deny wins


async def test_custom_mode_hard_blocks_denied_tool(cloud_selected):
    policy = Policy(
        mode="custom",
        allow=("get_*", "delete_server"),
        deny=("delete_server",),
        source="test",
    )
    mcp = create_mcp(policy=policy)
    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="Blocked by openstack-mcp-guarded"):
            await client.call_tool("delete_server", {"id": "fake-uuid"})


async def test_default_deny_unknown_tool(read_only_policy, cloud_selected):
    """A tool name matching no pattern is denied (future-proofing)."""
    policy = Policy(mode="read-only", source="test")
    assert not policy.is_allowed("some_future_upstream_tool")
    assert not policy.is_allowed("delete_everything")
