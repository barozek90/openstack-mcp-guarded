"""openstack-mcp-guarded.

An OpenStack MCP server with server-level safety fuses: a policy
layer that hides and hard-blocks non-read-only tools, regardless of
the MCP client used (opencode, Claude Code, ...).

Built as a wrapper around the upstream ``python-openstackmcp-server``
package.
"""

from openstack_mcp_guarded.middleware import PolicyMiddleware
from openstack_mcp_guarded.policy import Policy
from openstack_mcp_guarded.server import create_mcp, main

__all__ = [
    "Policy",
    "PolicyMiddleware",
    "create_mcp",
    "main",
]
