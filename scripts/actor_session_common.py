#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "actor_session_multibinding_v1"
DEFAULT_BINDING_KEY_MODE = "actor_id+identity_id+session_id"
SESSION_ONLY_BINDING_KEY_MODE = "actor_id+session_id"
LEGACY_BINDING_KEY_MODE = "legacy_single_object"
AUTHORITY_MODEL = "actor_session_multibinding_session_primary_v2"
AUTHORITATIVE_BINDING_RULE = "(actor_id,session_id)->identity_id"
ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE = "actor_global_compatibility_only"
COMPATIBILITY_PROJECTION_STATUS_AVAILABLE = "AVAILABLE"
COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY = "SUPPRESSED_MULTI_IDENTITY"
COMPATIBILITY_PROJECTION_STATUS_UNAVAILABLE = "UNAVAILABLE"


def resolve_protocol_actor_id(
    explicit_actor_id: str = "",
    *,
    allow_host_fallback: bool = False,
) -> str:
    actor = str(explicit_actor_id or "").strip()
    if actor:
        return actor
    env_actor = str(os.environ.get("CODEX_ACTOR_ID", "")).strip()
    if env_actor:
        return env_actor
    if not allow_host_fallback:
        return ""
    user = str(os.environ.get("USER", "unknown")).strip() or "unknown"
    return f"user:{user}"


def resolve_actor_id(explicit_actor_id: str = "") -> str:
    return resolve_protocol_actor_id(explicit_actor_id, allow_host_fallback=True)


def resolve_required_protocol_actor_id(explicit_actor_id: str = "") -> str:
    actor = resolve_protocol_actor_id(explicit_actor_id, allow_host_fallback=False)
    if actor:
        return actor
    raise ValueError("actor-id required: pass --actor-id or set CODEX_ACTOR_ID")


def actor_session_dir(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "actors").resolve()


def actor_session_filename(actor_id: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(actor_id or "").strip()).strip("._")
    if not token:
        token = "unknown_actor"
    return f"{token}.json"


def actor_session_path(catalog_path: Path, actor_id: str) -> Path:
    return (actor_session_dir(catalog_path) / actor_session_filename(actor_id)).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        return int(text)
    except Exception:
        return None


def _normalize_binding_entry(
    row: Any,
    *,
    actor_id: str,
    catalog_path: Path,
    fallback_session_id: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    stale_reasons: list[str] = []
    if not isinstance(row, dict):
        return None, ["binding_entry_not_object"]
    entry = copy.deepcopy(row)
    entry_actor = str(entry.get("actor_id", "")).strip()
    if entry_actor and entry_actor != actor_id:
        stale_reasons.append("binding_entry_actor_id_mismatch")
    entry["actor_id"] = actor_id

    entry_catalog = str(entry.get("catalog_path", "")).strip()
    if entry_catalog:
        try:
            if Path(entry_catalog).expanduser().resolve() != catalog_path:
                stale_reasons.append("binding_entry_catalog_path_mismatch")
        except Exception:
            stale_reasons.append("binding_entry_catalog_path_invalid")
    entry["catalog_path"] = str(catalog_path)

    session_id = str(entry.get("session_id", "")).strip()
    if not session_id:
        run_id = str(entry.get("run_id", "")).strip()
        if run_id:
            session_id = f"run:{run_id}"
            stale_reasons.append("session_id_derived_from_run_id")
        else:
            session_id = fallback_session_id
            stale_reasons.append("session_id_missing")
    entry["session_id"] = session_id
    if "bound_at" not in entry or not str(entry.get("bound_at", "")).strip():
        entry["bound_at"] = _utc_now()
    if "updated_at" not in entry or not str(entry.get("updated_at", "")).strip():
        entry["updated_at"] = str(entry.get("bound_at", "")).strip() or _utc_now()
    return entry, stale_reasons


def _entry_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    version = _as_int(row.get("binding_version"))
    if version is None:
        version = 0
    updated = str(row.get("updated_at", "")).strip() or str(row.get("bound_at", "")).strip()
    return (version, updated)


def _binding_entry_key(row: dict[str, Any], *, key_mode: str) -> str:
    sid = str(row.get("session_id", "")).strip()
    identity = str(row.get("identity_id", "")).strip()
    mode = str(key_mode or "").strip() or DEFAULT_BINDING_KEY_MODE
    if mode == SESSION_ONLY_BINDING_KEY_MODE:
        return sid
    # default: actor + identity + session tuple
    return f"{identity}::{sid}"


def _binding_mutation_projection(row: dict[str, Any]) -> dict[str, Any]:
    binding = copy.deepcopy(row) if isinstance(row, dict) else {}
    updated_at = str(binding.get("updated_at", "")).strip() or str(binding.get("bound_at", "")).strip()
    projection = {
        "session_id": str(binding.get("session_id", "")).strip(),
        "identity_id": str(binding.get("identity_id", "")).strip(),
        "binding_ref": str(binding.get("binding_ref", "")).strip(),
        "binding_version": _as_int(binding.get("binding_version")) or 0,
        "mutation_lane": str(binding.get("mutation_lane", "")).strip(),
        "run_id": str(binding.get("run_id", "")).strip(),
        "switch_reason": str(binding.get("switch_reason", "")).strip(),
        "approved_by": str(binding.get("approved_by", "")).strip(),
        "governance_override_receipt": str(binding.get("governance_override_receipt", "")).strip(),
        "compatibility_projection_allowed": bool(binding.get("compatibility_projection_allowed")),
        "compatibility_projection_reason": str(binding.get("compatibility_projection_reason", "")).strip(),
        "compatibility_projection_receipt": str(binding.get("compatibility_projection_receipt", "")).strip(),
        "compatibility_projection_previous_identity_id": str(
            binding.get("compatibility_projection_previous_identity_id", "")
        ).strip(),
        "updated_at": updated_at,
        "applied_at": updated_at,
        "projection_source": "binding_latest",
    }
    return projection


def _merge_projection_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base) if isinstance(base, dict) else {}
    if not isinstance(overlay, dict):
        return merged
    for key, value in overlay.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def _derive_last_mutation_by_session(
    bindings: list[dict[str, Any]],
    *,
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    derived: dict[str, dict[str, Any]] = {}
    for row in bindings:
        if not isinstance(row, dict):
            continue
        session_id = str(row.get("session_id", "")).strip()
        if not session_id:
            continue
        current = derived.get(session_id)
        if current is None or _entry_sort_key(row) >= _entry_sort_key(current):
            derived[session_id] = copy.deepcopy(row)

    projected: dict[str, dict[str, Any]] = {}
    raw_map = payload.get("last_mutation_by_session")
    raw_map = raw_map if isinstance(raw_map, dict) else {}
    raw_last_mutation = payload.get("last_mutation") if isinstance(payload.get("last_mutation"), dict) else {}
    for session_id, row in derived.items():
        projection = _binding_mutation_projection(row)
        raw_projection = raw_map.get(session_id)
        if isinstance(raw_projection, dict):
            projection = _merge_projection_overlay(projection, raw_projection)
        if session_id and str(raw_last_mutation.get("session_id", "")).strip() == session_id:
            projection = _merge_projection_overlay(projection, raw_last_mutation)
        projection["session_id"] = session_id
        projection["projection_scope"] = "session_primary"
        projected[session_id] = projection
    return projected


def _derive_actor_global_last_mutation(
    last_mutation_by_session: dict[str, dict[str, Any]],
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    candidates = [copy.deepcopy(v) for v in last_mutation_by_session.values() if isinstance(v, dict)]
    candidates.sort(
        key=lambda row: (
            _as_int(row.get("binding_version")) or 0,
            str(row.get("applied_at", "")).strip() or str(row.get("updated_at", "")).strip(),
        )
    )
    projected = candidates[-1] if candidates else {}
    raw_last_mutation = payload.get("last_mutation") if isinstance(payload.get("last_mutation"), dict) else {}
    if raw_last_mutation:
        raw_session_id = str(raw_last_mutation.get("session_id", "")).strip()
        if raw_session_id and raw_session_id in last_mutation_by_session:
            projected = _merge_projection_overlay(projected, raw_last_mutation)
        elif not projected:
            projected = copy.deepcopy(raw_last_mutation)
    if projected:
        projected["projection_scope"] = ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE
        projected["projection_role"] = "compatibility_projection"
    return projected


def binding_compatibility_projection_allowed(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    raw_allowed = row.get("compatibility_projection_allowed")
    if isinstance(raw_allowed, bool):
        return raw_allowed
    lane = str(row.get("mutation_lane", "")).strip().lower()
    if not lane:
        return True
    return lane == "activate"


def _actor_global_projection_state(
    *,
    store: dict[str, Any],
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    last_mutation_by_session = (
        store.get("last_mutation_by_session") if isinstance(store.get("last_mutation_by_session"), dict) else {}
    )
    projection_candidates = sorted(
        (
            copy.deepcopy(item)
            for item in last_mutation_by_session.values()
            if isinstance(item, dict) and binding_compatibility_projection_allowed(item)
        ),
        key=_projection_sort_key,
    )
    session_primary_identity_ids = sorted(
        {
            str(item.get("identity_id", "")).strip()
            for item in projection_candidates
            if str(item.get("identity_id", "")).strip()
        }
    )
    if len(session_primary_identity_ids) > 1:
        return {
            "projection_status": COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY,
            "projection_reason": "multiple_session_primary_identity_ids",
            "projection_candidate_identity_ids": session_primary_identity_ids,
            "projection": {},
        }
    if projection_candidates:
        projection = copy.deepcopy(projection_candidates[-1])
        projection["projection_scope"] = ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE
        projection["projection_role"] = "compatibility_projection"
    decorated = _decorate_actor_global_compatibility_projection(store=store, projection=projection)
    if decorated:
        return {
            "projection_status": COMPATIBILITY_PROJECTION_STATUS_AVAILABLE,
            "projection_reason": "ok",
            "projection_candidate_identity_ids": session_primary_identity_ids,
            "projection": decorated,
        }
    return {
        "projection_status": COMPATIBILITY_PROJECTION_STATUS_UNAVAILABLE,
        "projection_reason": "projection_missing",
        "projection_candidate_identity_ids": session_primary_identity_ids,
        "projection": {},
    }


def normalize_actor_binding_store(
    *,
    data: dict[str, Any] | None,
    actor_id: str,
    catalog_path: Path,
    actor_session_file: Path,
) -> dict[str, Any]:
    payload = copy.deepcopy(data) if isinstance(data, dict) else {}
    stale_reasons: list[str] = []

    key_mode = str(payload.get("binding_key_mode", "")).strip() or DEFAULT_BINDING_KEY_MODE
    bindings_raw = payload.get("bindings")
    normalized: list[dict[str, Any]] = []
    if isinstance(bindings_raw, list):
        for idx, row in enumerate(bindings_raw):
            entry, reasons = _normalize_binding_entry(
                row,
                actor_id=actor_id,
                catalog_path=catalog_path,
                fallback_session_id=f"legacy:{idx}",
            )
            stale_reasons.extend(reasons)
            if entry is not None:
                normalized.append(entry)
    elif payload:
        # Legacy single-record adapter.
        legacy_entry, reasons = _normalize_binding_entry(
            payload,
            actor_id=actor_id,
            catalog_path=catalog_path,
            fallback_session_id="legacy:0",
        )
        stale_reasons.extend(reasons)
        if legacy_entry is not None:
            normalized.append(legacy_entry)
            stale_reasons.append("legacy_single_object_shape")
            key_mode = LEGACY_BINDING_KEY_MODE

    dedup: dict[str, dict[str, Any]] = {}
    for row in normalized:
        key = _binding_entry_key(row, key_mode=key_mode)
        if not key or key.endswith("::"):
            continue
        old = dedup.get(key)
        if old is None or _entry_sort_key(row) >= _entry_sort_key(old):
            dedup[key] = row
    bindings = sorted(
        dedup.values(),
        key=lambda x: (
            str(x.get("identity_id", "")).strip(),
            str(x.get("session_id", "")).strip(),
        ),
    )

    has_binding_version_field = "binding_version" in payload
    version = _as_int(payload.get("binding_version"))
    if version is None:
        version = 0
        if payload and bindings and not has_binding_version_field:
            stale_reasons.append("binding_version_missing")
    for row in bindings:
        row_version = _as_int(row.get("binding_version"))
        if row_version is not None and row_version > version:
            version = row_version
    raw_compare_token = str(payload.get("compare_token", "")).strip()
    compare_token = raw_compare_token or str(version)
    if payload and bindings and not raw_compare_token:
        stale_reasons.append("compare_token_missing")

    receipts_raw = payload.get("rebind_receipts")
    receipts = [x for x in receipts_raw if isinstance(x, dict)] if isinstance(receipts_raw, list) else []
    last_mutation_by_session = _derive_last_mutation_by_session(bindings, payload=payload)
    actor_global_last_mutation = _derive_actor_global_last_mutation(last_mutation_by_session, payload=payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "authority_model": str(payload.get("authority_model", "")).strip() or AUTHORITY_MODEL,
        "authoritative_binding_rule": str(payload.get("authoritative_binding_rule", "")).strip()
        or AUTHORITATIVE_BINDING_RULE,
        "actor_id": actor_id,
        "catalog_path": str(catalog_path),
        "binding_key_mode": key_mode,
        "binding_version": version,
        "compare_token": compare_token,
        "session_entry_count": len(bindings),
        "bindings": bindings,
        "rebind_receipts": receipts,
        "last_mutation": actor_global_last_mutation,
        "last_mutation_projection_scope": ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE,
        "last_mutation_by_session": last_mutation_by_session,
        "updated_at": str(payload.get("updated_at", "")).strip(),
        "actor_session_path": str(actor_session_file),
        "stale_reasons": sorted(set(stale_reasons)),
    }


def load_actor_binding_store(catalog_path: Path, actor_id: str) -> dict[str, Any]:
    p = actor_session_path(catalog_path, actor_id)
    if not p.exists():
        return normalize_actor_binding_store(
            data={},
            actor_id=actor_id,
            catalog_path=catalog_path.resolve(),
            actor_session_file=p.resolve(),
        )
    data = _load_json(p)
    return normalize_actor_binding_store(
        data=data,
        actor_id=actor_id,
        catalog_path=catalog_path.resolve(),
        actor_session_file=p.resolve(),
    )


def _select_binding(
    store: dict[str, Any],
    *,
    identity_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
    if not bindings:
        return {}
    identity_id = str(identity_id or "").strip()
    session_id = str(session_id or "").strip()
    candidates = bindings
    if session_id:
        candidates = [x for x in candidates if str(x.get("session_id", "")).strip() == session_id]
    if identity_id:
        candidates = [x for x in candidates if str(x.get("identity_id", "")).strip() == identity_id]
    # actor/session scoped latest binding is ambiguous when identity is omitted and multiple identities are present.
    if not identity_id:
        identity_set = {str(x.get("identity_id", "")).strip() for x in candidates if str(x.get("identity_id", "")).strip()}
        if len(identity_set) > 1:
            return {}
    if not candidates:
        return {}
    selected = sorted(candidates, key=_entry_sort_key)[-1]
    out = copy.deepcopy(selected)
    out["actor_session_path"] = store.get("actor_session_path", "")
    out["binding_key_mode"] = store.get("binding_key_mode", DEFAULT_BINDING_KEY_MODE)
    out["binding_version_store"] = store.get("binding_version", 0)
    out["compare_token"] = store.get("compare_token", "")
    out["session_entry_count"] = store.get("session_entry_count", len(bindings))
    return out


def load_actor_binding(
    catalog_path: Path,
    actor_id: str,
    *,
    identity_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    store = load_actor_binding_store(catalog_path, actor_id)
    return _select_binding(store, identity_id=identity_id, session_id=session_id)


def resolve_bound_session_id_for_identity(
    catalog_path: Path,
    actor_id: str,
    identity_id: str,
    *,
    explicit_session_id: str = "",
) -> tuple[str, str]:
    explicit = str(explicit_session_id or "").strip()
    if explicit:
        return explicit, "explicit_session_id"
    actor = str(actor_id or "").strip()
    target_identity = str(identity_id or "").strip()
    if not actor:
        return "", "actor_missing"
    if not target_identity:
        return "", "identity_missing"
    try:
        binding = load_actor_binding(
            catalog_path,
            actor,
            identity_id=target_identity,
        )
    except Exception:
        binding = {}
    bound_session_id = str((binding or {}).get("session_id", "")).strip()
    if bound_session_id:
        return bound_session_id, "actor_binding_identity"
    return "", "binding_missing"


def _decorate_actor_global_compatibility_projection(
    *,
    store: dict[str, Any],
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    raw = copy.deepcopy(projection) if isinstance(projection, dict) else {}
    if not raw:
        return {}
    if str(raw.get("projection_scope", "")).strip() != ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE:
        return {}
    raw["projection_role"] = str(raw.get("projection_role", "")).strip() or "compatibility_projection"
    raw["actor_id"] = str(raw.get("actor_id", "")).strip() or str(store.get("actor_id", "")).strip()
    raw["actor_session_path"] = str(store.get("actor_session_path", "")).strip()
    raw["binding_key_mode"] = str(store.get("binding_key_mode", "")).strip() or DEFAULT_BINDING_KEY_MODE
    raw["binding_version_store"] = _as_int(store.get("binding_version")) or 0
    raw["compare_token"] = str(store.get("compare_token", "")).strip()
    raw["session_entry_count"] = _as_int(store.get("session_entry_count")) or 0
    return raw


def _projection_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    version = _as_int(row.get("binding_version"))
    if version is None:
        version = _as_int(row.get("binding_version_store")) or 0
    applied = str(row.get("applied_at", "")).strip() or str(row.get("updated_at", "")).strip()
    return (version, applied)


def load_actor_global_compatibility_projection(catalog_path: Path, actor_id: str) -> dict[str, Any]:
    store = load_actor_binding_store(catalog_path, actor_id)
    state = _actor_global_projection_state(
        store=store,
        projection=store.get("last_mutation") if isinstance(store.get("last_mutation"), dict) else {},
    )
    projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    return copy.deepcopy(projection)


def load_actor_global_compatibility_projection_state(catalog_path: Path, actor_id: str) -> dict[str, Any]:
    store = load_actor_binding_store(catalog_path, actor_id)
    return _actor_global_projection_state(
        store=store,
        projection=store.get("last_mutation") if isinstance(store.get("last_mutation"), dict) else {},
    )


def list_actor_global_compatibility_projections(catalog_path: Path) -> list[dict[str, Any]]:
    root = actor_session_dir(catalog_path)
    if not root.exists():
        return []
    projections: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        store = load_actor_binding_store(catalog_path, path.stem.replace("_", ":"))
        state = _actor_global_projection_state(
            store=store,
            projection=store.get("last_mutation") if isinstance(store.get("last_mutation"), dict) else {},
        )
        projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
        if projection:
            projections.append(projection)
    return sorted(projections, key=_projection_sort_key)


def select_actor_global_compatibility_projection(
    catalog_path: Path,
    *,
    identity_id: str = "",
    actor_id: str = "",
) -> dict[str, Any]:
    target_identity = str(identity_id or "").strip()
    target_actor = str(actor_id or "").strip()
    projections = list_actor_global_compatibility_projections(catalog_path)
    if target_actor:
        actor_matches = [
            item for item in projections if str(item.get("actor_id", "")).strip() == target_actor
        ]
        if actor_matches:
            projections = actor_matches
    if target_identity:
        identity_matches = [
            item for item in projections if str(item.get("identity_id", "")).strip() == target_identity
        ]
        if identity_matches:
            projections = identity_matches
    if not projections:
        return {}
    return copy.deepcopy(sorted(projections, key=_projection_sort_key)[-1])


def list_session_primary_conflicts(
    store: dict[str, Any],
    *,
    session_id: str = "",
) -> list[dict[str, Any]]:
    bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
    filter_session_id = str(session_id or "").strip()
    by_session: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in bindings:
        sid = str(row.get("session_id", "")).strip()
        identity = str(row.get("identity_id", "")).strip()
        if not sid or not identity:
            continue
        if filter_session_id and sid != filter_session_id:
            continue
        session_bucket = by_session.setdefault(sid, {})
        identity_bucket = session_bucket.setdefault(identity, [])
        identity_bucket.append(copy.deepcopy(row))

    conflicts: list[dict[str, Any]] = []
    for sid, identity_map in sorted(by_session.items()):
        identity_ids = sorted(identity_map.keys())
        if len(identity_ids) <= 1:
            continue
        entries: list[dict[str, Any]] = []
        for identity in identity_ids:
            rows = sorted(identity_map.get(identity, []), key=_entry_sort_key)
            latest = copy.deepcopy(rows[-1]) if rows else {}
            entries.append(
                {
                    "identity_id": identity,
                    "binding_ref": str(latest.get("binding_ref", "")).strip(),
                    "binding_version": _as_int(latest.get("binding_version")) or 0,
                    "mutation_lane": str(latest.get("mutation_lane", "")).strip(),
                    "run_id": str(latest.get("run_id", "")).strip(),
                    "updated_at": str(latest.get("updated_at", "")).strip()
                    or str(latest.get("bound_at", "")).strip(),
                    "entry_count": len(rows),
                }
            )
        conflicts.append(
            {
                "session_id": sid,
                "identity_ids": identity_ids,
                "entries": entries,
            }
        )
    return conflicts


def list_actor_bindings(catalog_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = actor_session_dir(catalog_path)
    if not root.exists():
        return out
    for p in sorted(root.glob("*.json")):
        data = _load_json(p)
        actor_id = str(data.get("actor_id", "")).strip() if isinstance(data, dict) else ""
        if not actor_id:
            actor_id = p.stem
        store = normalize_actor_binding_store(
            data=data,
            actor_id=actor_id,
            catalog_path=catalog_path.resolve(),
            actor_session_file=p.resolve(),
        )
        bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
        if not bindings:
            continue
        for row in bindings:
            entry = copy.deepcopy(row)
            entry["actor_session_path"] = str(p.resolve())
            entry["binding_key_mode"] = store.get("binding_key_mode", DEFAULT_BINDING_KEY_MODE)
            entry["binding_version_store"] = store.get("binding_version", 0)
            entry["compare_token"] = store.get("compare_token", "")
            entry["session_entry_count"] = store.get("session_entry_count", len(bindings))
            entry["store_stale_reasons"] = store.get("stale_reasons", [])
            out.append(entry)
    return out


def write_actor_binding_store(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    actor_id = str((payload or {}).get("actor_id", "")).strip()
    catalog_raw = str((payload or {}).get("catalog_path", "")).strip()
    if actor_id and catalog_raw:
        try:
            normalized = normalize_actor_binding_store(
                data=payload,
                actor_id=actor_id,
                catalog_path=Path(catalog_raw).expanduser().resolve(),
                actor_session_file=path.resolve(),
            )
        except Exception:
            normalized = payload
    else:
        normalized = payload
    tmp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
