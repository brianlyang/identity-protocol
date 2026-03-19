#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    AUTHORITY_MODEL,
    AUTHORITATIVE_BINDING_RULE,
    COMPATIBILITY_PROJECTION_STATUS_AVAILABLE,
    COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY,
    actor_session_dir,
    load_actor_global_compatibility_projection_state,
    normalize_actor_binding_store,
    select_actor_global_compatibility_projection,
    write_actor_binding_store,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
POINTER_SEMANTICS_VERSION = "session_pointer_compatibility_v2"


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _default_canonical_pointer(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "active_identity.json").resolve()


def _default_mirror_pointer(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "mirror" / "current.json").resolve()


def _pointer_metadata(
    *,
    catalog_path: Path,
    canonical_pointer_path: Path,
    projection_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = projection_state if isinstance(projection_state, dict) else {}
    raw = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    payload = {
        "authority_role": "compatibility_mirror",
        "authority_model": AUTHORITY_MODEL,
        "authoritative_binding_rule": AUTHORITATIVE_BINDING_RULE,
        "authoritative_binding_store_root": str(actor_session_dir(catalog_path)),
        "authoritative_decision_allowed": False,
        "pointer_semantics_version": POINTER_SEMANTICS_VERSION,
        "authoritative_source": "actor_session_store",
        "canonical_session_pointer": str(canonical_pointer_path),
        "compatibility_projection_status": str(state.get("projection_status", "")).strip(),
        "compatibility_projection_reason": str(state.get("projection_reason", "")).strip(),
        "compatibility_projection_candidate_identity_ids": [
            str(item).strip()
            for item in (state.get("projection_candidate_identity_ids") or [])
            if str(item).strip()
        ],
    }
    payload.update(
        {
            "compatibility_projection_scope": str(raw.get("projection_scope", "")).strip(),
            "compatibility_projection_role": str(raw.get("projection_role", "")).strip(),
            "compatibility_projection_actor_id": str(raw.get("actor_id", "")).strip(),
            "compatibility_projection_identity_id": str(raw.get("identity_id", "")).strip(),
            "compatibility_projection_session_id": str(raw.get("session_id", "")).strip(),
            "compatibility_projection_binding_ref": str(raw.get("binding_ref", "")).strip(),
            "compatibility_projection_run_id": str(raw.get("run_id", "")).strip(),
            "compatibility_projection_compare_token": str(raw.get("compare_token", "")).strip(),
            "compatibility_projection_binding_version": int(raw.get("binding_version", 0) or 0),
            "compatibility_projection_switch_reason": str(raw.get("switch_reason", "")).strip(),
            "compatibility_projection_applied_at": str(raw.get("applied_at", "")).strip(),
            "compatibility_projection_updated_at": str(raw.get("updated_at", "")).strip(),
        }
    )
    return payload


def _pointer_surface_fields(projection_state: dict[str, Any] | None, raw: dict[str, Any]) -> dict[str, str]:
    state = projection_state if isinstance(projection_state, dict) else {}
    projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    projection_status = str(state.get("projection_status", "")).strip()
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_AVAILABLE and projection:
        return {
            "identity_id": str(projection.get("identity_id", "")).strip(),
            "pack_path": str(raw.get("pack_path", "")).strip(),
            "status": str(raw.get("status", "")).strip() or "active",
        }
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY:
        return {
            "identity_id": "",
            "pack_path": "",
            "status": "compatibility_projection_suppressed",
        }
    return {
        "identity_id": "",
        "pack_path": "",
        "status": "compatibility_projection_unavailable",
    }


def _repair_actor_store(path: Path, *, catalog_path: Path) -> dict[str, Any]:
    raw = _load_json(path)
    actor_id = str(raw.get("actor_id", "")).strip() or path.stem.replace("_", ":")
    normalized = normalize_actor_binding_store(
        data=raw,
        actor_id=actor_id,
        catalog_path=catalog_path,
        actor_session_file=path,
    )
    residue_fields: list[str] = []
    if not str(raw.get("authority_model", "")).strip():
        residue_fields.append("authority_model")
    if not str(raw.get("authoritative_binding_rule", "")).strip():
        residue_fields.append("authoritative_binding_rule")
    if not isinstance(raw.get("last_mutation_by_session"), dict):
        residue_fields.append("last_mutation_by_session")
    if not str(raw.get("last_mutation_projection_scope", "")).strip():
        residue_fields.append("last_mutation_projection_scope")
    return {
        "actor_id": actor_id,
        "path": str(path),
        "binding_count": len([x for x in (normalized.get("bindings") or []) if isinstance(x, dict)]),
        "last_mutation_by_session_count": len(
            normalized.get("last_mutation_by_session")
            if isinstance(normalized.get("last_mutation_by_session"), dict)
            else {}
        ),
        "authority_model": str(normalized.get("authority_model", "")).strip(),
        "authoritative_binding_rule": str(normalized.get("authoritative_binding_rule", "")).strip(),
        "residue_fields": residue_fields,
        "changed": raw != normalized,
        "normalized_payload": normalized,
    }


def _repair_pointer(
    path: Path,
    *,
    pointer_name: str,
    catalog_path: Path,
    canonical_pointer_path: Path,
    actor_id_hint: str = "",
) -> dict[str, Any]:
    raw = _load_json(path)
    if not raw:
        return {
            "pointer_name": pointer_name,
            "path": str(path),
            "missing": not path.exists(),
            "residue_fields": ["pointer_missing_or_invalid_json"],
            "changed": False,
            "normalized_payload": {},
        }

    actor_id = str(raw.get("compatibility_projection_actor_id", "")).strip() or str(raw.get("actor_id", "")).strip()
    explicit_actor_id = str(actor_id_hint or "").strip()
    if not actor_id:
        inferred = select_actor_global_compatibility_projection(
            catalog_path,
            identity_id=str(raw.get("identity_id", "")).strip(),
        )
        actor_id = str(inferred.get("actor_id", "")).strip()
    if not actor_id:
        # Projection-unavailable pointers intentionally blank actor/id fields, so prefer the
        # explicitly requested actor (or a single scanned actor) before treating reason/status as residue.
        actor_id = explicit_actor_id
    projection_state = load_actor_global_compatibility_projection_state(catalog_path, actor_id) if actor_id else {}
    surface = _pointer_surface_fields(projection_state, raw)
    normalized = dict(raw)
    normalized["identity_id"] = surface["identity_id"]
    normalized["pack_path"] = surface["pack_path"]
    normalized["status"] = surface["status"]
    normalized.update(
        _pointer_metadata(
            catalog_path=catalog_path,
            canonical_pointer_path=canonical_pointer_path,
            projection_state=projection_state,
        )
    )
    normalized["session_pointer_type"] = "canonical" if pointer_name == "canonical" else "mirror"
    residue_fields: list[str] = []
    for field, expected in _pointer_metadata(
        catalog_path=catalog_path,
        canonical_pointer_path=canonical_pointer_path,
        projection_state=projection_state,
    ).items():
        if raw.get(field) != expected:
            residue_fields.append(field)
    for field in ("identity_id", "pack_path", "status"):
        if raw.get(field) != normalized.get(field):
            residue_fields.append(field)
    if str(raw.get("session_pointer_type", "")).strip().lower() != normalized["session_pointer_type"]:
        residue_fields.append("session_pointer_type")
    return {
        "pointer_name": pointer_name,
        "path": str(path),
        "missing": False,
        "residue_fields": sorted(set(residue_fields)),
        "changed": raw != normalized,
        "normalized_payload": normalized,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair actor-session authority residue and compatibility pointer metadata.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--actor-id", default="", help="optional actor id to restrict actor-session scan")
    ap.add_argument(
        "--all-actors",
        action="store_true",
        help="scan every actor session store under <catalog_dir>/session/actors",
    )
    ap.add_argument(
        "--canonical-out",
        default="",
        help="canonical pointer path (default: <catalog_dir>/session/active_identity.json)",
    )
    ap.add_argument(
        "--mirror-out",
        default="",
        help="mirror pointer path (default: <catalog_dir>/session/mirror/current.json)",
    )
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    _ = _load_yaml(catalog_path)
    actors_root = actor_session_dir(catalog_path)
    actor_paths: list[Path] = []
    if args.all_actors:
        actor_paths = sorted(actors_root.glob("*.json"))
    elif str(args.actor_id or "").strip():
        actor_token = str(args.actor_id or "").strip().replace(":", "_")
        actor_paths = [actors_root / f"{actor_token}.json"]
    else:
        print("[FAIL] pass --actor-id or --all-actors")
        return 2

    canonical_pointer = (
        Path(args.canonical_out).expanduser().resolve()
        if str(args.canonical_out or "").strip()
        else _default_canonical_pointer(catalog_path)
    )
    mirror_pointer = (
        Path(args.mirror_out).expanduser().resolve()
        if str(args.mirror_out or "").strip()
        else _default_mirror_pointer(catalog_path)
    )

    actor_results = [_repair_actor_store(path, catalog_path=catalog_path) for path in actor_paths if path.exists()]
    actor_missing = [str(path) for path in actor_paths if not path.exists()]
    pointer_actor_hint = str(args.actor_id or "").strip()
    if not pointer_actor_hint and len(actor_results) == 1:
        pointer_actor_hint = str(actor_results[0].get("actor_id", "")).strip()
    pointer_results = [
        _repair_pointer(
            canonical_pointer,
            pointer_name="canonical",
            catalog_path=catalog_path,
            canonical_pointer_path=canonical_pointer,
            actor_id_hint=pointer_actor_hint,
        ),
        _repair_pointer(
            mirror_pointer,
            pointer_name="mirror",
            catalog_path=catalog_path,
            canonical_pointer_path=canonical_pointer,
            actor_id_hint=pointer_actor_hint,
        ),
    ]

    actor_residue_count = sum(1 for item in actor_results if item.get("residue_fields") or item.get("changed"))
    pointer_residue_count = sum(1 for item in pointer_results if item.get("residue_fields") or item.get("changed"))
    residue_detected = bool(actor_residue_count or pointer_residue_count or actor_missing)
    applied_actor_store_count = 0
    applied_pointer_count = 0
    if args.apply:
        for item in actor_results:
            if item.get("changed"):
                write_actor_binding_store(Path(str(item["path"])), item.get("normalized_payload") or {})
                applied_actor_store_count += 1
        for item in pointer_results:
            normalized_payload = item.get("normalized_payload") or {}
            if item.get("changed") and normalized_payload:
                _write_json(Path(str(item["path"])), normalized_payload)
                applied_pointer_count += 1

    status = STATUS_PASS_REQUIRED
    if residue_detected and not args.apply:
        status = STATUS_FAIL_REQUIRED
    elif not residue_detected:
        status = STATUS_SKIPPED_NOT_REQUIRED

    payload = {
        "actor_session_authority_residue_status": status,
        "catalog_path": str(catalog_path),
        "actor_store_scan_count": len(actor_results),
        "actor_store_missing_paths": actor_missing,
        "actor_store_residue_count": actor_residue_count,
        "pointer_residue_count": pointer_residue_count,
        "applied": bool(args.apply),
        "applied_actor_store_count": applied_actor_store_count,
        "applied_pointer_count": applied_pointer_count,
        "canonical_pointer_path": str(canonical_pointer),
        "mirror_pointer_path": str(mirror_pointer),
        "pointer_semantics_version": POINTER_SEMANTICS_VERSION,
        "authority_model": AUTHORITY_MODEL,
        "authoritative_binding_rule": AUTHORITATIVE_BINDING_RULE,
        "actor_store_results": [{k: v for k, v in item.items() if k != "normalized_payload"} for item in actor_results],
        "pointer_results": [{k: v for k, v in item.items() if k != "normalized_payload"} for item in pointer_results],
        "stale_reasons": [],
    }
    if actor_missing:
        payload["stale_reasons"].append("actor_session_store_missing")
    if residue_detected and not args.apply:
        payload["stale_reasons"].append("authority_residue_detected")

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
