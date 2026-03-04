#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import actor_session_path, load_actor_binding, load_actor_binding_store, resolve_actor_id

ERR_ACTOR_BINDING = "IP-ASB-201"
STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    data = _load_catalog(catalog_path)
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


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

    row = _identity_row(catalog_path, args.identity_id)
    if row is None:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "actor_id": resolve_actor_id(args.actor_id),
            "actor_session_path": "",
            "bound_identity_id": "",
            "catalog_identity_status": "",
            "actor_binding_status": "FAIL_REQUIRED",
            "error_code": ERR_ACTOR_BINDING,
            "stale_reasons": ["identity_not_found_in_catalog"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {ERR_ACTOR_BINDING} identity not found in catalog: {args.identity_id}")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    actor_id = resolve_actor_id(args.actor_id)
    actor_path = actor_session_path(catalog_path, actor_id)
    actor_store = load_actor_binding_store(catalog_path, actor_id)
    actor_binding = load_actor_binding(
        catalog_path,
        actor_id,
        identity_id=args.identity_id,
        session_id=args.session_id,
    )
    status = str(row.get("status", "")).strip().lower() or "inactive"
    operation = str(args.operation or "validate").strip().lower()
    inspection_mode = operation in INSPECTION_OPS
    stale_reasons: list[str] = []
    error_code = ""
    actor_binding_status = "PASS_REQUIRED"
    bound_identity = str(actor_binding.get("identity_id", "")).strip()
    session_entry_count = int(actor_store.get("session_entry_count", 0) or 0)
    binding_key_mode = str(actor_store.get("binding_key_mode", "")).strip()
    store_stale = [str(x).strip() for x in (actor_store.get("stale_reasons") or []) if str(x).strip()]

    if session_entry_count <= 0:
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
        if not error_code and bound_identity != args.identity_id:
            if status == "active":
                stale_reasons.append("active_identity_not_bound_to_actor")
                error_code = ERR_ACTOR_BINDING
                actor_binding_status = "FAIL_REQUIRED"
            else:
                stale_reasons.append("actor_bound_to_different_identity")
                actor_binding_status = "SKIPPED_NOT_REQUIRED"

    payload = {
        "identity_id": args.identity_id,
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
                f"target={args.identity_id}"
            )
        else:
            print(
                f"[FAIL] {error_code or ERR_ACTOR_BINDING} actor session binding validation failed: "
                f"actor={actor_id} target={args.identity_id}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if actor_binding_status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
