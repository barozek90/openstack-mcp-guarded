"""Assembly of the guarded OpenStack MCP server.

Reuses tool classes from the upstream ``python-openstackmcp-server``
package (PyPI) and registers them into our own FastMCP instance with
the policy middleware (fuses) applied on top.

The upstream ``serve()`` is NOT reused because we need to inject our
middleware into the pipeline.
"""

from fastmcp import FastMCP

from openstack_mcp_guarded.middleware import PolicyMiddleware
from openstack_mcp_guarded.policy import Policy


def create_mcp(policy: Policy | None = None) -> FastMCP:
    """Build the guarded FastMCP server instance.

    :param policy: Optional pre-loaded policy (tests inject custom ones).
                   When omitted, the policy is loaded from the standard
                   location / environment override.
    :return: Configured FastMCP instance (not yet running).
    """
    if policy is None:
        policy = Policy.load()

    mcp = FastMCP("openstack_mcp_guarded")

    # Upstream tools (compute, image, identity, network, block storage,
    # connection/cloud session) registered into OUR instance.
    from openstack_mcp_server.tools import register_tool

    register_tool(mcp)

    # Fuses: policy middleware added LAST (outermost) so it sees every
    # tools/call before anything else touches it.
    mcp.add_middleware(PolicyMiddleware(policy))

    return mcp


def main() -> None:
    """Console entry point: run the guarded server over stdio."""
    mcp = create_mcp()
    mcp.run(transport="stdio")
