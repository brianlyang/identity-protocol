#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
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


ALLOWED_DISCLOSURE_LEVELS = {"minimal", "standard", "verbose", "audit"}
DEFAULT_DISCLOSURE_LEVEL = "standard"
ALLOWED_WORK_LAYERS = {"protocol", "instance", "dual"}
ALLOWED_SOURCE_LAYERS = {"project", "global", "env", "auto"}


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


def normalize_disclosure_level(
    level: str,
    *,
    default: str = DEFAULT_DISCLOSURE_LEVEL,
    allow_empty: bool = False,
) -> str:
    raw = str(level or "").strip().lower()
    if not raw and allow_empty:
        return ""
    if raw in {"concise", "short", "lite"}:
        raw = "minimal"
    elif raw in {"default"}:
        raw = "standard"
    elif raw in {"full", "detailed"}:
        raw = "verbose"
    if raw in ALLOWED_DISCLOSURE_LEVELS:
        return raw
    fallback = str(default or "").strip().lower()
    if not fallback and allow_empty:
        return ""
    return fallback if fallback in ALLOWED_DISCLOSURE_LEVELS else DEFAULT_DISCLOSURE_LEVEL


def infer_disclosure_level_from_stamp_fields(fields: dict[str, str]) -> str:
    if str(fields.get("lease", "")).strip():
        return "verbose"
    if str(fields.get("catalog_ref", "")).strip() or str(fields.get("pack_ref", "")).strip():
        return "standard"
    return "minimal"


def _infer_trigger_scope(trigger_text: str) -> str:
    text = str(trigger_text or "").strip().lower()
    if not text:
        return ""
    if any(x in text for x in ("once", "one-time", "one shot", "single response", "本轮", "一次", "单次")):
        return "once"
    if any(x in text for x in ("session", "会话", "持续", "一直", "后续")):
        return "session"
    return ""


def parse_disclosure_level_trigger(trigger_text: str) -> tuple[str, float]:
    text = str(trigger_text or "").strip().lower()
    if not text:
        return "", 0.0
    if any(x in text for x in ("minimal", "concise", "short", "简洁", "简版", "精简")):
        return "minimal", 0.95
    if any(x in text for x in ("standard", "default", "标准", "默认")):
        return "standard", 0.95
    if any(x in text for x in ("verbose", "full", "detailed", "全量", "详细", "完整")):
        return "verbose", 0.95
    if any(x in text for x in ("audit", "internal", "审计", "内部")):
        return "audit", 0.95
    m = re.search(r"(minimal|standard|verbose|audit)", text)
    if m:
        return normalize_disclosure_level(m.group(1)), 0.9
    return "", 0.0


def _response_stamp_profile_state_path(catalog_path: Path, actor_id: str) -> Path:
    token = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(actor_id or "unknown"))
    return (catalog_path.parent / "session" / "response-stamp-profiles" / f"{token}.json").resolve()


def _load_task_response_stamp_profile(ctx: StampContext) -> dict[str, Any]:
    task_path = (ctx.pack_path / "CURRENT_TASK.json").resolve()
    if not task_path.exists():
        return {}
    try:
        doc = load_json(task_path)
    except Exception:
        return {}
    profile = doc.get("response_stamp_profile")
    return profile if isinstance(profile, dict) else {}


def _load_response_stamp_profile_state(ctx: StampContext) -> dict[str, Any]:
    p = _response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)
    if not p.exists():
        return {}
    try:
        data = load_json(p)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _persist_response_stamp_profile_state(ctx: StampContext, *, level: str, trigger_text: str) -> Path:
    p = _response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "actor_id": ctx.actor_id,
        "identity_id": ctx.identity_id,
        "disclosure_level": normalize_disclosure_level(level),
        "trigger_text": str(trigger_text or "").strip(),
        "trigger_source": "natural_language",
        "scope": "session",
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def resolve_disclosure_level(
    ctx: StampContext,
    *,
    explicit_level: str = "",
    trigger_text: str = "",
    trigger_scope: str = "",
    persist_session_trigger: bool = True,
) -> dict[str, Any]:
    normalized_explicit = normalize_disclosure_level(explicit_level, default="", allow_empty=True)
    if normalized_explicit:
        return {
            "disclosure_level": normalized_explicit,
            "disclosure_source": "explicit_arg",
            "trigger_applied": False,
            "trigger_scope": "",
            "trigger_text": "",
            "trigger_confidence": 1.0,
            "session_profile_path": "",
        }

    parsed_level, confidence = parse_disclosure_level_trigger(trigger_text)
    normalized_scope = str(trigger_scope or "").strip().lower()
    if normalized_scope not in {"once", "session"}:
        normalized_scope = _infer_trigger_scope(trigger_text)
    if parsed_level:
        profile_path = ""
        if normalized_scope == "session" and persist_session_trigger:
            profile_path = str(_persist_response_stamp_profile_state(ctx, level=parsed_level, trigger_text=trigger_text))
        return {
            "disclosure_level": parsed_level,
            "disclosure_source": "trigger_session" if normalized_scope == "session" else "trigger_once",
            "trigger_applied": True,
            "trigger_scope": normalized_scope or "once",
            "trigger_text": str(trigger_text or "").strip(),
            "trigger_confidence": confidence,
            "session_profile_path": profile_path,
        }

    session_state = _load_response_stamp_profile_state(ctx)
    session_level = normalize_disclosure_level(
        str(session_state.get("disclosure_level", "")).strip(),
        default="",
        allow_empty=True,
    )
    if session_level:
        return {
            "disclosure_level": session_level,
            "disclosure_source": "session_state",
            "trigger_applied": False,
            "trigger_scope": str(session_state.get("scope", "session")).strip() or "session",
            "trigger_text": str(session_state.get("trigger_text", "")).strip(),
            "trigger_confidence": 1.0,
            "session_profile_path": str(_response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)),
        }

    task_profile = _load_task_response_stamp_profile(ctx)
    task_level = normalize_disclosure_level(
        str(task_profile.get("disclosure_level", "")).strip(),
        default="",
        allow_empty=True,
    )
    if task_level:
        return {
            "disclosure_level": task_level,
            "disclosure_source": "task_profile",
            "trigger_applied": False,
            "trigger_scope": "",
            "trigger_text": "",
            "trigger_confidence": 1.0,
            "session_profile_path": "",
        }

    return {
        "disclosure_level": DEFAULT_DISCLOSURE_LEVEL,
        "disclosure_source": "default",
        "trigger_applied": False,
        "trigger_scope": "",
        "trigger_text": "",
        "trigger_confidence": 1.0,
        "session_profile_path": "",
    }


def render_external_stamp(ctx: StampContext, *, disclosure_level: str = DEFAULT_DISCLOSURE_LEVEL) -> str:
    return render_external_stamp_with_layer_context(ctx, disclosure_level=disclosure_level)


def render_external_stamp_with_layer_context(
    ctx: StampContext,
    *,
    disclosure_level: str = DEFAULT_DISCLOSURE_LEVEL,
    work_layer: str = "protocol",
    source_layer: str = "",
) -> str:
    level = normalize_disclosure_level(disclosure_level)
    wl = str(work_layer or "").strip().lower() or "protocol"
    if wl not in ALLOWED_WORK_LAYERS:
        wl = "protocol"
    sl = str(source_layer or "").strip().lower() or ctx.source_domain
    if sl not in ALLOWED_SOURCE_LAYERS:
        sl = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"
    parts = [
        f"actor_id={ctx.actor_id}",
        f"identity_id={ctx.identity_id}",
    ]
    if level in {"standard", "verbose", "audit"}:
        parts.append(f"catalog_ref={ctx.catalog_ref}")
        parts.append(f"pack_ref={ctx.pack_ref}")
    parts.extend(
        [
            f"scope={ctx.resolved_scope}",
            f"lock={ctx.lock_state}",
            f"source={ctx.source_domain}",
        ]
    )
    if level in {"verbose", "audit"}:
        parts.append(f"lease={lease_id_short(ctx.lease_id)}")
    return (
        "Identity-Context: "
        + "; ".join(parts)
        + f" | Layer-Context: work_layer={wl}; source_layer={sl}"
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


def render_structured_context(
    ctx: StampContext,
    *,
    work_layer: str = "protocol",
    source_layer: str = "",
) -> dict[str, Any]:
    wl = str(work_layer or "").strip().lower() or "protocol"
    if wl not in ALLOWED_WORK_LAYERS:
        wl = "protocol"
    sl = str(source_layer or "").strip().lower() or ctx.source_domain
    if sl not in ALLOWED_SOURCE_LAYERS:
        sl = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"
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
        "work_layer": wl,
        "source_layer": sl,
        "source_domain": ctx.source_domain,
    }


def _parse_kv_pairs(fragment: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pairs = [x.strip() for x in str(fragment or "").split(";") if x.strip()]
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def parse_identity_context_stamp(stamp_line: str) -> dict[str, Any]:
    raw = str(stamp_line or "").strip()
    if not raw.startswith("Identity-Context:"):
        return {}

    tail_marker = "| Layer-Context:"
    identity_segment = raw
    layer_segment = ""
    has_layer_context = False
    if tail_marker in raw:
        identity_segment, layer_segment = raw.split(tail_marker, 1)
        has_layer_context = True

    identity_body = identity_segment.split(":", 1)[1].strip()
    fields = _parse_kv_pairs(identity_body)
    layer_fields = _parse_kv_pairs(layer_segment.strip()) if layer_segment else {}
    fields.update(layer_fields)

    # Legacy compatibility: old stamps may only carry source_layer in the main block.
    if not str(fields.get("source", "")).strip() and str(fields.get("source_layer", "")).strip():
        fields["source"] = str(fields.get("source_layer", "")).strip()
    if not str(fields.get("source_layer", "")).strip() and str(fields.get("source", "")).strip():
        fields["source_layer"] = str(fields.get("source", "")).strip()

    fields["_has_layer_context"] = has_layer_context
    fields["_raw_identity_segment"] = identity_segment.strip()
    fields["_raw_layer_segment"] = layer_segment.strip()
    return fields


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
