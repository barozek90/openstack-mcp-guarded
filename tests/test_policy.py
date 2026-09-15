"""Unit tests for the policy engine (modes, globs, YAML loading)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from openstack_mcp_guarded.policy import (
    MODE_CUSTOM,
    MODE_READ_ONLY,
    SESSION_TOOLS,
    Policy,
)


class TestReadOnlyMode:
    def test_default_policy_is_read_only(self):
        policy = Policy()
        assert policy.mode == MODE_READ_ONLY

    def test_read_tools_allowed(self):
        policy = Policy()
        for tool in ("get_servers", "get_volumes", "get_networks", "get_images"):
            assert policy.is_allowed(tool), tool

    def test_write_tools_blocked(self):
        policy = Policy()
        for tool in (
            "create_server",
            "delete_server",
            "update_server",
            "action_server",
            "create_volume",
            "delete_volume",
            "extend_volume",
            "attach_volume",
            "detach_volume",
            "set_port_binding",
            "add_router_interface",
            "remove_router_interface",
            "assign_first_available_floating_ip",
            "create_floating_ips_bulk",
        ):
            assert not policy.is_allowed(tool), tool

    def test_session_tools_always_allowed(self):
        policy = Policy()
        for tool in SESSION_TOOLS:
            assert policy.is_allowed(tool), tool

    def test_unknown_future_tool_blocked(self):
        """Default-deny: a tool added upstream in the future is blocked."""
        policy = Policy()
        assert not policy.is_allowed("reboot_hypervisor")
        assert not policy.is_allowed("wipe_everything")


class TestCustomMode:
    def test_custom_allowlist(self):
        policy = Policy(mode=MODE_CUSTOM, allow=("get_*", "create_volume"))
        assert policy.is_allowed("get_servers")
        assert policy.is_allowed("create_volume")
        assert not policy.is_allowed("delete_volume")

    def test_custom_default_deny(self):
        policy = Policy(mode=MODE_CUSTOM, allow=())
        assert not policy.is_allowed("get_servers")
        assert not policy.is_allowed("delete_server")

    def test_deny_wins_over_allow(self):
        policy = Policy(
            mode=MODE_CUSTOM,
            allow=("get_*", "create_*"),
            deny=("delete_*", "create_server"),
        )
        assert policy.is_allowed("create_volume")
        assert not policy.is_allowed("create_server")  # explicit deny
        assert not policy.is_allowed("delete_volume")

    def test_deny_applies_in_read_only_mode(self):
        policy = Policy(mode=MODE_READ_ONLY, deny=("get_projects",))
        assert policy.is_allowed("get_servers")
        assert not policy.is_allowed("get_projects")

    def test_session_tools_survive_deny(self):
        policy = Policy(mode=MODE_CUSTOM, allow=(), deny=("*",))
        for tool in SESSION_TOOLS:
            assert policy.is_allowed(tool), tool


class TestInvalidMode:
    def test_invalid_mode_rejected(self):
        with pytest.raises(ValueError, match="Invalid policy mode"):
            Policy(mode="yolo")


class TestYamlLoading:
    def _write(self, tmp_path: Path, content: str) -> Path:
        path = tmp_path / "policy.yaml"
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return path

    def test_load_read_only_file(self, tmp_path, monkeypatch):
        path = self._write(tmp_path, "mode: read-only\n")
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(path))
        policy = Policy.load()
        assert policy.mode == MODE_READ_ONLY
        assert policy.is_allowed("get_servers")
        assert not policy.is_allowed("delete_server")

    def test_load_custom_file(self, tmp_path, monkeypatch):
        path = self._write(
            tmp_path,
            """
            mode: custom
            allow:
              - "get_*"
              - create_volume
            deny:
              - delete_*
            """,
        )
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(path))
        policy = Policy.load()
        assert policy.mode == MODE_CUSTOM
        assert policy.is_allowed("create_volume")
        assert not policy.is_allowed("delete_volume")

    def test_missing_file_falls_back_to_read_only(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(tmp_path / "nope.yaml"))
        policy = Policy.load()
        assert policy.mode == MODE_READ_ONLY

    def test_invalid_mode_in_file_fails_safe(self, tmp_path, monkeypatch):
        path = self._write(tmp_path, "mode: full-control\n")
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(path))
        policy = Policy.load()
        assert policy.mode == MODE_READ_ONLY

    def test_broken_yaml_fails_safe(self, tmp_path, monkeypatch):
        path = tmp_path / "policy.yaml"
        path.write_text("mode: [unclosed\n  - {", encoding="utf-8")
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(path))
        policy = Policy.load()
        assert policy.mode == MODE_READ_ONLY

    def test_empty_file_fails_safe(self, tmp_path, monkeypatch):
        path = self._write(tmp_path, "")
        monkeypatch.setenv("OS_MCP_GUARD_POLICY", str(path))
        policy = Policy.load()
        assert policy.mode == MODE_READ_ONLY
