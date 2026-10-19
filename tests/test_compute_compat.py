"""Regression test for the upstream ``delete_on_termination`` null bug.

Nova can return ``null`` for a volume attachment's ``delete_on_termination``,
but upstream's ``Server.VolumeAttachment`` model required a ``bool``, so
``get_servers``/``get_server`` raised a hard ``pydantic.ValidationError`` for
any server with such a volume (observed on WAW4-1). See ``compat.py``.
"""

from __future__ import annotations

import pytest
from fastmcp import Client

from openstack_mcp_guarded.policy import Policy
from openstack_mcp_guarded.server import create_mcp


@pytest.fixture(autouse=True)
def fake_clouds(monkeypatch):
    """Hermetic cloud catalogue (see test_server.py for rationale)."""
    import openstack.config.loader as _loader
    import openstack_mcp_server.tools.connection as _conn

    class FakeOpenStackConfig:
        cloud_config: dict = {"clouds": {"RegionOne": {}}}

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def get_cloud_names(self) -> list[str]:
            return list(self.cloud_config["clouds"])

    monkeypatch.setattr(_conn, "OpenStackConfig", FakeOpenStackConfig)
    monkeypatch.setattr(_loader, "OpenStackConfig", FakeOpenStackConfig)


@pytest.fixture()
def cloud_selected(monkeypatch):
    from openstack_mcp_server.tools.connection import ConnectionManager

    # monkeypatch reverts this automatically at teardown; no manual reset.
    monkeypatch.setattr(ConnectionManager, "_cloud_name", "RegionOne")


class _FakeComputeProxy:
    def __init__(self, servers: list[dict]) -> None:
        self._servers = servers

    def servers(self):
        return iter(self._servers)


class _FakeConn:
    def __init__(self, servers: list[dict]) -> None:
        self.compute = _FakeComputeProxy(servers)


_SERVER_WITH_NULL_DELETE_ON_TERMINATION = [
    {
        "id": "srv-1",
        "name": "vm-1",
        "attached_volumes": [
            {"id": "vol-1", "delete_on_termination": None},
        ],
    }
]


async def test_get_servers_tolerates_null_delete_on_termination(
    cloud_selected, monkeypatch
):
    policy = Policy(mode="read-only", source="test")
    mcp = create_mcp(policy=policy)

    import openstack_mcp_server.tools.compute_tools as _compute_tools

    monkeypatch.setattr(
        _compute_tools,
        "get_openstack_conn",
        lambda: _FakeConn(_SERVER_WITH_NULL_DELETE_ON_TERMINATION),
    )

    async with Client(mcp) as client:
        result = await client.call_tool("get_servers", {})

    servers_out = result.data
    assert len(servers_out) == 1
    assert servers_out[0].attached_volumes[0].delete_on_termination is None


async def test_patch_is_order_independent(cloud_selected, monkeypatch):
    """The patch must mutate the shared model class in place.

    Importing compute_tools *before* create_mcp() binds its `Server`
    reference to whatever class object exists at that moment. If the
    patch swapped in a new class instead of mutating in place, this
    reference would stay stale and this test would reproduce the
    original ValidationError.
    """
    import openstack_mcp_server.tools.compute_tools as _compute_tools

    policy = Policy(mode="read-only", source="test")
    mcp = create_mcp(policy=policy)

    monkeypatch.setattr(
        _compute_tools,
        "get_openstack_conn",
        lambda: _FakeConn(_SERVER_WITH_NULL_DELETE_ON_TERMINATION),
    )

    async with Client(mcp) as client:
        result = await client.call_tool("get_servers", {})

    assert result.data[0].attached_volumes[0].delete_on_termination is None
