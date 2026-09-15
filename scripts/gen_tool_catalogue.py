#!/usr/bin/env python3
"""Regenerate TOOLS.md - the full tool catalogue of openstack-mcp-guarded.

Enumerates tools per upstream tool class (exact categories), splits them
by the current policy, and rewrites TOOLS.md in the repo root.

Usage:
    uv run python scripts/gen_tool_catalogue.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "TOOLS.md"

# (label, upstream class import path, class name)
TOOL_CLASSES = [
    ("Compute", "openstack_mcp_server.tools.compute_tools", "ComputeTools"),
    ("Image", "openstack_mcp_server.tools.image_tools", "ImageTools"),
    ("Identity", "openstack_mcp_server.tools.identity_tools", "IdentityTools"),
    ("Network", "openstack_mcp_server.tools.network_tools", "NetworkTools"),
    (
        "Block Storage",
        "openstack_mcp_server.tools.block_storage_tools",
        "BlockStorageTools",
    ),
    (
        "Session",
        "openstack_mcp_server.tools.connection",
        "ConnectionManager",
    ),
    # extra tool families (this repo, not upstream)
    (
        "Load Balancer (Octavia)",
        "openstack_mcp_guarded.extra_tools.octavia_tools",
        "OctaviaTools",
    ),
    (
        "DNS (Designate)",
        "openstack_mcp_guarded.extra_tools.designate_tools",
        "DesignateTools",
    ),
    (
        "Ops / Heat",
        "openstack_mcp_guarded.extra_tools.ops_tools",
        "OpsTools",
    ),
]


async def catalogue() -> dict[str, dict[str, str]]:
    """Return {tool_name: {category, description}} from upstream classes."""
    import importlib

    result: dict[str, dict[str, str]] = {}
    for category, module_name, class_name in TOOL_CLASSES:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        mcp = FastMCP("catalogue")
        cls().register_tools(mcp)
        async with Client(mcp) as client:
            for tool in await client.list_tools():
                result[tool.name] = {
                    "category": category,
                    "description": (tool.description or "").strip(),
                }
    return result


def first_sentence(description: str) -> str:
    """Shorten long docstrings to the first sentence."""
    for sep in (".\n", ". "):
        idx = description.find(sep)
        if idx != -1:
            return description[: idx + 1].replace("\n", " ").strip()
    return description.replace("\n", " ").strip()


def main() -> int:
    from openstack_mcp_guarded.policy import Policy

    policy = Policy()  # read-only default
    tools = asyncio.run(catalogue())

    allowed = {n: t for n, t in tools.items() if policy.is_allowed(n)}
    blocked = {n: t for n, t in tools.items() if not policy.is_allowed(n)}

    lines: list[str] = []
    lines.append("# Tool catalogue — openstack-mcp-guarded\n")
    lines.append(
        f"> Full upstream catalogue: **{len(tools)} tools** · "
        f"visible in read-only mode: **{len(allowed)}** · "
        f"blocked: **{len(blocked)}**\n"
    )
    lines.append(
        "Sources: upstream `python-openstackmcp-server` (compute, image, "
        "identity, network, block storage, session) + extra tools in this "
        "repo (Octavia load balancers, Designate DNS, ops/Heat).\n"
    )
    lines.append("---\n")

    lines.append("## ✅ Allowed in read-only mode (default)\n")
    lines.append("| Tool | Category | Description |")
    lines.append("|---|---|---|")
    for name in sorted(allowed):
        t = allowed[name]
        lines.append(
            f"| `{name}` | {t['category']} | {first_sentence(t['description'])} |"
        )
    lines.append("\n---\n")

    lines.append("## ⛔ Blocked by policy\n")
    lines.append(
        "Hidden from the model (`on_list_tools`) and hard-blocked on direct "
        "invocation (`on_call_tool`). Audit line on stderr for every attempt.\n"
    )
    lines.append("| Tool | Category | What it would do |")
    lines.append("|---|---|---|")
    for name in sorted(blocked):
        t = blocked[name]
        lines.append(
            f"| `{name}` | {t['category']} | {first_sentence(t['description'])} |"
        )
    lines.append("\n---\n")

    lines.append("## Regenerate\n")
    lines.append("```bash")
    lines.append("uv run python scripts/gen_tool_catalogue.py")
    lines.append("```\n")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {OUT} ({len(tools)} tools, {len(allowed)} allowed, "
          f"{len(blocked)} blocked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
