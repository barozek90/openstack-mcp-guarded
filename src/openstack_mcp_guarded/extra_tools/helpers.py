"""Shared helpers for extra tool modules."""

from __future__ import annotations

from typing import Any


def _pick(obj: Any, *fields: str) -> dict[str, Any]:
    """Project selected attributes of an SDK resource into a dict.

    Missing attributes are set to ``None`` instead of raising, so the
    tool output stays stable across OpenStack releases that add or drop
    response fields.
    """
    return {f: getattr(obj, f, None) for f in fields}
