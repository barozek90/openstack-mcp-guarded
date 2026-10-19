"""Compatibility shims for known upstream (``python-openstackmcp-server``) bugs.

Upstream's ``Server.VolumeAttachment.delete_on_termination`` is typed as a
required ``bool``, but Nova can legitimately return ``null`` for it (seen in
practice on WAW4-1, for at least one attached volume). That turns any
``get_servers``/``get_server`` call touching such a server into a hard
``pydantic.ValidationError`` with no way to filter it out client-side.

This module patches the response model's field **in place** (mutating
``VolumeAttachment.model_fields`` and calling ``model_rebuild``), rather
than swapping in a patched subclass. Every existing reference to the class
object — including ``openstack_mcp_server.tools.compute_tools``'s own
``from openstack_mcp_server.tools.response.compute import Server``, bound
at *its* import time — keeps pointing at the same, now-patched, class. That
makes the patch immune to import order: it is safe to call this before,
after, or interleaved with any other import of ``compute_tools`` /
``response.compute``, unlike a subclass-and-rebind approach.
"""

from __future__ import annotations

import logging

from pydantic.fields import FieldInfo

logger = logging.getLogger("openstack-mcp-guarded")


def patch_upstream_quirks() -> None:
    """Apply all known upstream compatibility patches. Idempotent."""
    _patch_volume_attachment_delete_on_termination()


def _patch_volume_attachment_delete_on_termination() -> None:
    from openstack_mcp_server.tools.response import compute as _compute

    volume_attachment = _compute.Server.VolumeAttachment
    field = volume_attachment.model_fields["delete_on_termination"]
    if field.default is None and not field.is_required():
        return  # already patched

    volume_attachment.model_fields["delete_on_termination"] = FieldInfo(
        annotation=bool | None, default=None
    )
    volume_attachment.model_rebuild(force=True)
    _compute.Server.model_rebuild(force=True)
    logger.debug(
        "openstack-mcp-guarded: patched Server.VolumeAttachment."
        "delete_on_termination to tolerate null"
    )
