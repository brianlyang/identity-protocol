#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    actor_session_path,
    load_actor_binding,
    load_actor_binding_store,
    resolve_actor_id,
    select_actor_global_compatibility_projection,
)

ERR_ACTOR_BINDING = "IP-ASB-201"
STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}


def _inspection_identity_fallback(catalog_path: Path, actor_id: str, session_id: str | None) -> tuple[str, dict[str, object]]:
    binding = load_actor_binding(catalog_path, actor_id=actor_id, identity_id="", session_id=session_id)
    if binding:
        identity_id = str(binding.get("identity_id") or "").strip()
        effective_session_id = str(binding.get("session_id") or session_id or "").strip()
        if identity_id:
            return identity_id, {
                "identity_id_requested": "",
                "identity_id_effective": identity_id,
                "session_id_requested": session_id or "",
                "session_id_effective": effective_session_id,
                "identity_resolution_mode": "requested_bound",
                "session_id_resolution_mode": "requested_bound" if session_id else "binding_default",
                "session_id_requested_bound": bool(session_id and effective_session_id == session_id),
            }
    actor_store = load_actor_binding_store(catalog_path, actor_id)
    last_mutation = actor_store.get("last_mutation") if isinstance(actor_store, dict) else {}
    if isinstance(last_mutation, dict):
        identity_id = str(last_mutation.get("identity_id") or "").strip()
        effective_session_id = str(last_mutation.get("session_id") or session_id or "").strip()
        if identity_id:
            return identity_id, {
                "identity_id_requested": "",
                "identity_id_effective": identity_id,
                "session_id_requested": session_id or "",
                "session_id_effective": effective_session_id,
                "identity_resolution_mode": "actor_store_last_mutation",
                "session_id_resolution_mode": "requested_bound" if session_id and effective_session_id == session_id else "actor_store_last_mutation",
                "session_id_requested_bound": bool(session_id and effective_session_id == session_id),
            }
    compatibility = select_actor_global_compatibility_projection(catalog_path, actor_id=actor_id)
    if compatibility:
        identity_id = str(compatibility.get("identity_id") or "").strip()
        if identity_id:
            return identity_id, {
                "identity_id_requested": "",
                "identity_id_effective": identity_id,
                "session_id_requested": session_id or "",
                "session_id_effective": session_id or "",
                "identity_resolution_mode": "global_compatibility_projection",
                "session_id_resolution_mode": "requested_preserved" if session_id else "unbound",
                "session_id_requested_bound": False,
            }
    return "", {
        "identity_id_requested": "",
        "identity_id_effective": "",
        "session_id_requested": session_id or "",
        "session_id_effective": session_id or "",
        "identity_resolution_mode": "unresolved",
        "session_id_resolution_mode": "unresolved",
        "session_id_requested_bound": False,
    }


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    data = _load_catalog(catalog_path)
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _is_fixture_identity(row: dict[str, Any] | None) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate actor-scoped session binding truth source.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--actor-id", default="")
    ap.add_argument(
        "--operation",
        choices=sorted(STRICT_OPS | INSPECTION_OPS),
        default="validate",
        help="strict operations fail on missing actor binding; inspection operations can skip",
    )
    ap.add_argument("--session-id", default="", help="optional explicit session binding selector")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    actor_id = resolve_actor_id(args.actor_id)
    operation = str(args.operation or "validate").strip().lower()
    inspection_mode = operation in INSPECTION_OPS
    requested_identity_id = str(args.identity_id or "").strip()
    requested_session_id = str(args.session_id or "").strip()
    effective_identity_id = requested_identity_id
    resolution_payload = {
        "identity_id_requested": requested_identity_id,
        "identity_id_effective": requested_identity_id,
        "session_id_requested": requested_session_id,
        "session_id_effective": requested_session_id,
        "identity_resolution_mode": "requested",
        "session_id_resolution_mode": "requested" if requested_session_id else "unbound",
        "session_id_requested_bound": False,
    }
    if inspection_mode and not effective_identity_id:
        effective_identity_id, resolution_payload = _inspection_identity_fallback(
            catalog_path,
            actor_id,
            requested_session_id or None,
        )
    effective_session_id = str(resolution_payload.get("session_id_effective") or requested_session_id).strip()

    row = _identity_row(catalog_path, effective_identity_id)
    if row is None:
        payload = {
            "identity_id": effective_identity_id,
            "catalog_path": str(catalog_path),
            "actor_id": actor_id,
            "actor_session_path": "",
            "bound_identity_id": "",
            "catalog_identity_status": "",
            "actor_binding_status": "FAIL_REQUIRED",
            "error_code": ERR_ACTOR_BINDING,
            "stale_reasons": ["identity_not_found_in_catalog"],
            **resolution_payload,
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERR_ACTOR_BINDING} identity not found in catalog: {effective_identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    actor_path = actor_session_path(catalog_path, actor_id)
    actor_store = load_actor_binding_store(catalog_path, actor_id)
    actor_binding = load_actor_binding(
        catalog_path,
        actor_id,
        identity_id=effective_identity_id,
        session_id=effective_session_id,
    )
    status = str(row.get("status", "")).strip().lower() or "inactive"
    fixture_mode = _is_fixture_identity(row)
    stale_reasons: list[str] = []
    error_code = ""
    actor_binding_status = "PASS_REQUIRED"
    bound_identity = str(actor_binding.get("identity_id", "")).strip()
    session_entry_count = int(actor_store.get("session_entry_count", 0) or 0)
    binding_key_mode = str(actor_store.get("binding_key_mode", "")).strip()
    store_stale = [str(x).strip() for x in (actor_store.get("stale_reasons") or []) if str(x).strip()]

    if fixture_mode:
        actor_binding_status = "SKIPPED_NOT_REQUIRED"
        stale_reasons.append("fixture_profile_scope")
    elif session_entry_count <= 0:
        stale_reasons.append("actor_session_binding_missing")
        if inspection_mode:
            actor_binding_status = "SKIPPED_NOT_REQUIRED"
            stale_reasons.append("inspection_scope_missing_actor_binding")
        else:
            error_code = ERR_ACTOR_BINDING
            actor_binding_status = "FAIL_REQUIRED"
    elif not actor_binding:
        stale_reasons.append("target_identity_binding_missing_for_actor")
        if status == "active":
            if inspection_mode:
                actor_binding_status = "SKIPPED_NOT_REQUIRED"
            else:
                actor_binding_status = "FAIL_REQUIRED"
                error_code = ERR_ACTOR_BINDING
        else:
            actor_binding_status = "SKIPPED_NOT_REQUIRED"
    else:
        if str(actor_binding.get("actor_id", "")).strip() != actor_id:
            stale_reasons.append("actor_id_mismatch")
            error_code = ERR_ACTOR_BINDING
            actor_binding_status = "FAIL_REQUIRED"
        if str(actor_binding.get("catalog_path", "")).strip() != str(catalog_path):
            stale_reasons.append("catalog_path_mismatch")
            error_code = ERR_ACTOR_BINDING
            actor_binding_status = "FAIL_REQUIRED"
        if not error_code and bound_identity != effective_identity_id:
            if status == "active":
                stale_reasons.append("active_identity_not_bound_to_actor")
                error_code = ERR_ACTOR_BINDING
                actor_binding_status = "FAIL_REQUIRED"
            else:
                stale_reasons.append("actor_bound_to_different_identity")
                actor_binding_status = "SKIPPED_NOT_REQUIRED"

    payload = {
        "identity_id": effective_identity_id,
        "catalog_path": str(catalog_path),
        "actor_id": actor_id,
        "operation": operation,
        "actor_session_path": str(actor_path),
        "bound_identity_id": bound_identity,
        "bound_session_id": str(actor_binding.get("session_id", "")).strip(),
        "binding_key_mode": binding_key_mode,
        "session_entry_count": session_entry_count,
        "catalog_identity_status": status,
        "actor_binding_status": actor_binding_status,
        "error_code": error_code,
        "stale_reasons": sorted(set([*stale_reasons, *store_stale])),
        **resolution_payload,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if actor_binding_status == "PASS_REQUIRED":
            print(
                f"[OK] actor session binding validated: actor={actor_id} identity={args.identity_id} "
                f"path={actor_path}"
            )
        elif actor_binding_status == "SKIPPED_NOT_REQUIRED":
            print(
                f"[OK] actor session binding skipped: actor={actor_id} bound_identity={bound_identity} "
                f"target={effective_identity_id}"
            )
        else:
            print(
                f"[FAIL] {error_code or ERR_ACTOR_BINDING} actor session binding validation failed: "
                f"actor={actor_id} target={effective_identity_id}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if actor_binding_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
