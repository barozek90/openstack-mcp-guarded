"""Policy middleware for the OpenStack MCP guarded server.

Enforces the tool policy at the MCP protocol level:

- ``on_list_tools``: tools outside the policy are hidden from the model
  entirely, so the model cannot even attempt to call them.
- ``on_call_tool``: direct invocation of a blocked tool is rejected with a
  ``ToolError`` *before* any cloud operation is performed. Every block is
  logged to stderr (audit trail).

Additionally a "no cloud selected" guard: when no cloud is selected
(``CLOUD_NAME`` empty), only cloud-session tools are allowed, so the model
must first call ``set_cloud_name``.
"""

from __future__ import annotations

import logging
import sys

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from openstack_mcp_guarded.policy import SESSION_TOOLS, Policy

logger = logging.getLogger("openstack-mcp-guarded")


def _stderr(msg: str) -> None:
    """Write an audit line to stderr (never stdout: stdio transport)."""
    print(msg, file=sys.stderr, flush=True)


class PolicyMiddleware(Middleware):
    """FastMCP middleware enforcing the read-only / custom tool policy."""

    def __init__(self, policy: Policy) -> None:
        self._policy = policy

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _selected_cloud(self) -> str | None:
        """Name of the selected cloud if it is valid, else ``None``.

        The upstream ConnectionManager defaults to ``"openstack"`` when
        ``CLOUD_NAME`` is unset, which may not exist in the user's
        clouds.yaml - so the name must be validated against the actual
        config, not just checked for emptiness.
        """
        from openstack_mcp_server.tools.connection import ConnectionManager

        name = ConnectionManager.get_cloud_name()
        if not name:
            return None
        clouds = self._available_clouds()
        if not clouds:
            return None
        return name if name in clouds else None

    def _available_clouds(self) -> list[str]:
        """Cloud names from the user's clouds.yaml (for error hints)."""
        try:
            from openstack.config.loader import OpenStackConfig

            return list(OpenStackConfig().get_cloud_names())
        except Exception:  # noqa: BLE001 - hint is best-effort
            return []

    def _deny(
        self,
        tool_name: str,
        reason: str,
        hint: str | None = None,
    ) -> ToolError:
        """Build the ToolError and emit the audit line."""
        _stderr(
            f"[openstack-mcp-guarded] BLOCKED tool='{tool_name}' "
            f"mode='{self._policy.mode}' reason='{reason}'"
        )
        msg = (
            f"Blocked by openstack-mcp-guarded policy (mode: "
            f"{self._policy.mode}): tool '{tool_name}' is not permitted. "
            f"{reason}"
        )
        if hint:
            msg += f" {hint}"
        return ToolError(msg)

    # ------------------------------------------------------------------
    # middleware hooks
    # ------------------------------------------------------------------

    async def on_list_tools(self, context, call_next):  # noqa: ANN001, ANN201
        """Hide tools outside the policy from the model's tool list."""
        tools = await call_next(context)
        visible = []
        for tool in tools:
            if self._policy.is_allowed(tool.name):
                visible.append(tool)
            else:
                logger.debug(
                    "policy: hiding tool '%s' (mode=%s)",
                    tool.name,
                    self._policy.mode,
                )
        return visible

    async def on_call_tool(self, context, call_next):  # noqa: ANN001, ANN201
        """Hard-block disallowed tools before any cloud interaction."""
        tool_name = context.message.name

        if not self._policy.is_allowed(tool_name):
            raise self._deny(
                tool_name,
                f"not on the '{self._policy.mode}' allowlist",
                hint=(
                    "Read-only tools (get_*) are available. Ask the user to "
                    "extend the policy file (~/.config/openstack-mcp-guarded/"
                    "policy.yaml) if write access is intended."
                ),
            )

        # No-cloud guard: force cloud selection before any cloud tool runs.
        if tool_name not in SESSION_TOOLS and self._selected_cloud() is None:
            clouds = self._available_clouds()
            clouds_hint = (
                f"Available clouds: {', '.join(clouds)}. "
                if clouds
                else "No clouds found in clouds.yaml. "
            )
            raise self._deny(
                tool_name,
                "no OpenStack cloud is selected",
                hint=(
                    clouds_hint
                    + "Call the 'set_cloud_name' tool first (e.g. with one "
                    "of the clouds listed above), then retry."
                ),
            )

        return await call_next(context)
