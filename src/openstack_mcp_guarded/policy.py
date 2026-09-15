"""Policy engine for openstack-mcp-guarded.

Defines which MCP tools are allowed to be listed and executed.

Two modes:
- ``read-only`` (default): allowlist = read tools (``get_*``) + cloud-session
  tools. Default-deny: any tool not on the list (including future upstream
  additions) is blocked.
- ``custom``: allowlist taken from the policy file (``allow`` section).
  ``deny`` always wins over ``allow``.

Policy file location (first match wins):
1. ``$OS_MCP_GUARD_POLICY``
2. ``~/.config/openstack-mcp-guarded/policy.yaml``
"""

from __future__ import annotations

import fnmatch
import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("openstack-mcp-guarded")

# Tools that manage the cloud session itself. They never touch cloud
# resources, so they are always allowed (also needed for the no-cloud
# bootstrap flow: without them the model could not select a cloud at all).
SESSION_TOOLS: frozenset[str] = frozenset(
    {
        "get_cloud_names",
        "get_cloud_config",
        "get_cloud_name",
        "set_cloud_name",
    }
)

# Read-only tools in read-only mode: everything that only reads state.
# Kept as a prefix glob so that new upstream read tools are covered
# automatically; anything not matching is denied (default-deny).
READ_ONLY_ALLOW: tuple[str, ...] = ("get_*",)

MODE_READ_ONLY = "read-only"
MODE_CUSTOM = "custom"
_VALID_MODES = (MODE_READ_ONLY, MODE_CUSTOM)

DEFAULT_POLICY_PATH = (
    Path.home() / ".config" / "openstack-mcp-guarded" / "policy.yaml"
)
POLICY_PATH_ENV = "OS_MCP_GUARD_POLICY"


class Policy:
    """Immutable tool-access policy resolved from mode + YAML file."""

    def __init__(
        self,
        mode: str = MODE_READ_ONLY,
        allow: tuple[str, ...] = (),
        deny: tuple[str, ...] = (),
        source: str = "default",
    ) -> None:
        if mode not in _VALID_MODES:
            raise ValueError(
                f"Invalid policy mode: {mode!r} (valid: {', '.join(_VALID_MODES)})"
            )
        self.mode = mode
        self.allow = tuple(allow)
        self.deny = tuple(deny)
        self.source = source

    @classmethod
    def load(cls) -> "Policy":
        """Load policy from file (or defaults when no file exists)."""
        path = cls._policy_path()
        if path is None or not path.is_file():
            return cls(source="default (no policy file)")

        try:
            raw = _read_yaml(path)
        except Exception:
            logger.exception(
                "Failed to parse policy file %s - falling back to "
                "read-only mode (fail-safe)",
                path,
            )
            return cls(source=f"{path} (parse error -> read-only)")

        mode = str(raw.get("mode", MODE_READ_ONLY)).strip().lower()
        if mode not in _VALID_MODES:
            logger.error(
                "Invalid mode %r in %s - falling back to read-only",
                mode,
                path,
            )
            return cls(source=f"{path} (invalid mode -> read-only)")

        allow = _as_str_tuple(raw.get("allow"))
        deny = _as_str_tuple(raw.get("deny"))
        return cls(
            mode=mode,
            allow=allow,
            deny=deny,
            source=str(path),
        )

    @staticmethod
    def _policy_path() -> Path | None:
        env = os.environ.get(POLICY_PATH_ENV, "").strip()
        if env:
            return Path(env).expanduser()
        return DEFAULT_POLICY_PATH

    def is_allowed(self, tool_name: str) -> bool:
        """Decide whether ``tool_name`` may be listed and executed.

        Order of evaluation:
        1. Session tools are always allowed.
        2. ``deny`` patterns win over everything else.
        3. ``read-only`` mode: allowlist is the built-in read-only set.
        4. ``custom`` mode: allowlist comes from the policy file; a tool
           not matching any ``allow`` pattern is denied (default-deny).
        """
        if tool_name in SESSION_TOOLS:
            return True

        if _matches(tool_name, self.deny):
            return False

        patterns = (
            READ_ONLY_ALLOW if self.mode == MODE_READ_ONLY else self.allow
        )
        return _matches(tool_name, patterns)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"Policy(mode={self.mode!r}, allow={self.allow!r}, "
            f"deny={self.deny!r}, source={self.source!r})"
        )


def _matches(tool_name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(tool_name, p) for p in patterns)


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}
