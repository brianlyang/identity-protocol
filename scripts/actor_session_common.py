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
DEFAULT_BINDING_KEY_MODE = "actor_id+session_id"
LEGACY_BINDING_KEY_MODE = "legacy_single_object"


def resolve_actor_id(explicit_actor_id: str = "") -> str:
    actor = str(explicit_actor_id or "").strip()
    if actor:
        return actor
    env_actor = str(os.environ.get("CODEX_ACTOR_ID", "")).strip()
    if env_actor:
        return env_actor
    user = str(os.environ.get("USER", "unknown")).strip() or "unknown"
    return f"user:{user}"


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
        sid = str(row.get("session_id", "")).strip()
        if not sid:
            continue
        old = dedup.get(sid)
        if old is None or _entry_sort_key(row) >= _entry_sort_key(old):
            dedup[sid] = row
    bindings = sorted(dedup.values(), key=lambda x: str(x.get("session_id", "")))

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
    return {
        "schema_version": SCHEMA_VERSION,
        "actor_id": actor_id,
        "catalog_path": str(catalog_path),
        "binding_key_mode": key_mode,
        "binding_version": version,
        "compare_token": compare_token,
        "session_entry_count": len(bindings),
        "bindings": bindings,
        "rebind_receipts": receipts,
        "last_mutation": payload.get("last_mutation", {}) if isinstance(payload.get("last_mutation"), dict) else {},
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
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
