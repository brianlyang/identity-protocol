#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import list_actor_bindings

ERR_CROSS_ACTOR_ISOLATION = "IP-ASB-203"
STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate cross-actor isolation for actor-scoped session bindings.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", default="")
    ap.add_argument(
        "--operation",
        choices=sorted(STRICT_OPS | INSPECTION_OPS),
        default="validate",
        help="strict operations fail when actor binding set missing; inspection operations can skip",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        catalog = _load_catalog(catalog_path)
    except Exception as exc:
        print(f"[FAIL] invalid catalog yaml: {exc}")
        return 1

    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    known_ids = {str(x.get("id", "")).strip() for x in identities if str(x.get("id", "")).strip()}
    active_ids = [str(x.get("id", "")).strip() for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    active_ids = [x for x in active_ids if x]
    operation = str(args.operation or "validate").strip().lower()
    inspection_mode = operation in INSPECTION_OPS

    bindings = list_actor_bindings(catalog_path)
    stale_reasons: list[str] = []
    error_code = ""
    status = "PASS_REQUIRED"

    if not bindings:
        stale_reasons.append("actor_session_bindings_missing")
        if inspection_mode:
            status = "SKIPPED_NOT_REQUIRED"
            stale_reasons.append("inspection_scope_missing_actor_binding_set")
        else:
            status = "FAIL_REQUIRED"
            error_code = ERR_CROSS_ACTOR_ISOLATION
    else:
        for b in bindings:
            actor = str(b.get("actor_id", "")).strip()
            bound_identity = str(b.get("identity_id", "")).strip()
            b_catalog = str(b.get("catalog_path", "")).strip()
            if not actor:
                stale_reasons.append("binding_missing_actor_id")
            if not bound_identity:
                stale_reasons.append(f"binding_missing_identity_id:{actor or 'unknown_actor'}")
            elif bound_identity not in known_ids:
                stale_reasons.append(f"binding_identity_not_in_catalog:{bound_identity}")
            if b_catalog != str(catalog_path):
                stale_reasons.append(f"binding_catalog_mismatch:{actor or 'unknown_actor'}")
        if stale_reasons:
            status = "FAIL_REQUIRED"
            error_code = ERR_CROSS_ACTOR_ISOLATION

    payload = {
        "catalog_path": str(catalog_path),
        "identity_id": str(args.identity_id or "").strip(),
        "operation": operation,
        "active_identities": active_ids,
        "actor_binding_count": len(bindings),
        "cross_actor_isolation_status": status,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
        "actor_bindings": [
            {
                "actor_id": str(b.get("actor_id", "")).strip(),
                "identity_id": str(b.get("identity_id", "")).strip(),
                "actor_session_path": str(b.get("actor_session_path", "")),
            }
            for b in bindings
        ],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if status == "PASS_REQUIRED":
            print(
                "[OK] cross-actor isolation validated: "
                f"catalog={catalog_path} actor_bindings={len(bindings)} active_identities={active_ids}"
            )
        else:
            print(f"[FAIL] {error_code or ERR_CROSS_ACTOR_ISOLATION} cross-actor isolation validation failed")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
