#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding, resolve_actor_id
from resolve_identity_context import resolve_identity
from tool_vendor_governance_common import load_json


@dataclass
class StampContext:
    actor_id: str
    identity_id: str
    catalog_path: Path
    pack_path: Path
    resolved_scope: str
    lock_state: str
    lease_id: str
    source_domain: str
    catalog_ref: str
    pack_ref: str


def _detect_repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    for parent in [base, *base.parents]:
        if (parent / ".git").exists():
            return parent.resolve()
    return base


def _project_identity_home(repo_root: Path) -> Path:
    if repo_root.name == "identity-protocol-local":
        return (repo_root.parent / ".agents" / "identity").resolve()
    return (repo_root / ".agents" / "identity").resolve()


def _global_identity_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "identity").resolve()
    return (Path.home() / ".codex" / "identity").resolve()


def _source_domain(catalog_path: Path, explicit_catalog: bool) -> str:
    repo_root = _detect_repo_root(catalog_path.parent)
    project_home = _project_identity_home(repo_root)
    global_home = _global_identity_home()
    c = catalog_path.resolve()
    try:
        c.relative_to(project_home)
        return "project"
    except Exception:
        pass
    try:
        c.relative_to(global_home)
        return "global"
    except Exception:
        pass
    return "env" if explicit_catalog else "auto"


def _ref_token(path: Path) -> str:
    norm = str(path.resolve())
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]
    return f"{path.name}#{h}"


def _session_pointer_path(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "active_identity.json").resolve()


def _session_data(catalog_path: Path, actor_id: str) -> dict[str, Any]:
    actor_binding = load_actor_binding(catalog_path, actor_id)
    if actor_binding:
        payload = dict(actor_binding)
        payload["session_pointer_source"] = "actor"
        return payload
    p = _session_pointer_path(catalog_path)
    if not p.exists():
        return {}
    try:
        data = load_json(p)
    except Exception:
        return {}
    if isinstance(data, dict):
        data["session_pointer_source"] = "canonical"
        return data
    return {}


def _lock_state(identity_id: str, pointer: dict[str, Any]) -> str:
    if not pointer:
        return "UNKNOWN"
    active_id = str(pointer.get("identity_id", "")).strip()
    if not active_id:
        return "UNKNOWN"
    if active_id == identity_id:
        return "LOCK_MATCH"
    return "LOCK_MISMATCH"


def _lease_id(pointer: dict[str, Any]) -> str:
    lease = str(pointer.get("lease_id", "")).strip()
    if lease:
        return lease
    run_id = str(pointer.get("run_id", "")).strip()
    if run_id:
        return f"lease-{run_id[:16]}"
    lock_hash = str(pointer.get("state_hash", "")).strip()
    if lock_hash:
        return f"lease-{lock_hash[:10]}"
    return "lease-unknown"


def resolve_stamp_context(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    actor_id: str = "",
    explicit_catalog: bool = True,
) -> StampContext:
    actor = resolve_actor_id(actor_id)
    resolved = resolve_identity(
        identity_id,
        repo_catalog_path.resolve(),
        catalog_path.resolve(),
        allow_conflict=True,
    )
    pack_path = Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve()
    resolved_scope = str(resolved.get("resolved_scope", "")).strip().upper() or "UNKNOWN"
    pointer = _session_data(catalog_path, actor)
    lock_state = _lock_state(identity_id, pointer)
    lease_id = _lease_id(pointer)
    source = _source_domain(catalog_path, explicit_catalog=explicit_catalog)
    return StampContext(
        actor_id=actor,
        identity_id=identity_id,
        catalog_path=catalog_path.resolve(),
        pack_path=pack_path,
        resolved_scope=resolved_scope,
        lock_state=lock_state,
        lease_id=lease_id,
        source_domain=source,
        catalog_ref=_ref_token(catalog_path.resolve()),
        pack_ref=_ref_token(pack_path),
    )


def lease_id_short(lease_id: str) -> str:
    token = str(lease_id or "").strip()
    if not token:
        return "lease-unknown"
    return token[:12]


def render_external_stamp(ctx: StampContext) -> str:
    return (
        "Identity-Context: "
        f"actor_id={ctx.actor_id}; "
        f"identity_id={ctx.identity_id}; "
        f"catalog_ref={ctx.catalog_ref}; "
        f"pack_ref={ctx.pack_ref}; "
        f"scope={ctx.resolved_scope}; "
        f"lock={ctx.lock_state}; "
        f"lease={lease_id_short(ctx.lease_id)}; "
        f"source={ctx.source_domain}"
    )


def render_internal_stamp(ctx: StampContext) -> str:
    return (
        "Identity-Context-Internal: "
        f"actor_id={ctx.actor_id}; "
        f"identity_id={ctx.identity_id}; "
        f"catalog_path={ctx.catalog_path}; "
        f"resolved_pack_path={ctx.pack_path}; "
        f"scope={ctx.resolved_scope}; "
        f"lock={ctx.lock_state}; "
        f"lease={lease_id_short(ctx.lease_id)}; "
        f"source={ctx.source_domain}"
    )


def render_structured_context(ctx: StampContext) -> dict[str, Any]:
    return {
        "actor_id": ctx.actor_id,
        "identity_id": ctx.identity_id,
        "catalog_ref": ctx.catalog_ref,
        "pack_ref": ctx.pack_ref,
        "catalog_path": str(ctx.catalog_path),
        "resolved_pack_path": str(ctx.pack_path),
        "scope": ctx.resolved_scope,
        "lock_state": ctx.lock_state,
        "lease_id": ctx.lease_id,
        "lease_id_short": lease_id_short(ctx.lease_id),
        "source_domain": ctx.source_domain,
    }


def blocker_receipt(
    *,
    error_code: str,
    expected_identity_id: str,
    actual_identity_id: str,
    source_domain: str,
    resolver_ref: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "error_code": str(error_code).strip(),
        "expected_identity_id": str(expected_identity_id).strip(),
        "actual_identity_id": str(actual_identity_id).strip(),
        "source_domain": str(source_domain).strip(),
        "resolver_ref": str(resolver_ref).strip(),
        "next_action": str(next_action).strip(),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
