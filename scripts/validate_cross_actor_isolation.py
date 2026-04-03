#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import list_actor_bindings, resolve_actor_id

ERR_CROSS_ACTOR_ISOLATION = "IP-ASB-203"
STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}
SCOPE_MODE_CATALOG_ALL = "catalog_all"
SCOPE_MODE_ACTOR_PRIMARY = "actor_primary"
SCOPE_MODE_ACTOR_ONLY = "actor_only"
SCOPE_MODES = {
    SCOPE_MODE_CATALOG_ALL,
    SCOPE_MODE_ACTOR_PRIMARY,
    SCOPE_MODE_ACTOR_ONLY,
}


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be object: {path}")
    return raw


def _evaluate_binding_staleness(
    *,
    bindings: list[dict[str, Any]],
    known_ids: set[str],
    catalog_path: Path,
) -> list[str]:
    stale_reasons: list[str] = []
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
    return sorted(set(stale_reasons))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate cross-actor isolation for actor-scoped session bindings.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument(
        "--scope-mode",
        choices=sorted(SCOPE_MODES),
        default=SCOPE_MODE_CATALOG_ALL,
        help=(
            "catalog_all=strictly validate all actor bindings; "
            "actor_primary=fail-close on target actor scope + keep non-target anomalies as warnings; "
            "actor_only=validate target actor scope only."
        ),
    )
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
    actor_id_input = str(args.actor_id or "").strip()
    actor_id = resolve_actor_id(actor_id_input) if actor_id_input else ""
    scope_mode_requested = str(args.scope_mode or SCOPE_MODE_CATALOG_ALL).strip().lower()
    scope_mode_effective = scope_mode_requested

    all_bindings = list_actor_bindings(catalog_path)
    scope_stale_reasons: list[str] = []
    if scope_mode_effective in {SCOPE_MODE_ACTOR_PRIMARY, SCOPE_MODE_ACTOR_ONLY} and not actor_id:
        scope_stale_reasons.append("scope_mode_requires_actor_id")
        if inspection_mode:
            scope_mode_effective = SCOPE_MODE_CATALOG_ALL
            scope_stale_reasons.append("inspection_scope_fallback_to_catalog_all_without_actor_id")
        else:
            scope_mode_effective = SCOPE_MODE_ACTOR_ONLY

    if scope_mode_effective == SCOPE_MODE_CATALOG_ALL:
        bindings = all_bindings
        non_target_bindings: list[dict[str, Any]] = []
    else:
        bindings = [b for b in all_bindings if str(b.get("actor_id", "")).strip() == actor_id]
        non_target_bindings = [b for b in all_bindings if str(b.get("actor_id", "")).strip() != actor_id]

    scoped_stale_reasons = _evaluate_binding_staleness(
        bindings=bindings,
        known_ids=known_ids,
        catalog_path=catalog_path,
    )
    global_observation_stale_reasons: list[str] = []
    if scope_mode_effective == SCOPE_MODE_ACTOR_PRIMARY:
        global_observation_stale_reasons = _evaluate_binding_staleness(
            bindings=non_target_bindings,
            known_ids=known_ids,
            catalog_path=catalog_path,
        )

    stale_reasons: list[str] = []
    error_code = ""
    status = "PASS_REQUIRED"
    global_observation_status = "SKIPPED_NOT_REQUIRED"

    if not active_ids:
        status = "SKIPPED_NOT_REQUIRED"
        stale_reasons.append("no_active_identities_in_catalog")
    elif scope_stale_reasons and scope_mode_requested in {SCOPE_MODE_ACTOR_PRIMARY, SCOPE_MODE_ACTOR_ONLY} and not actor_id:
        stale_reasons.extend(scope_stale_reasons)
        if inspection_mode:
            status = "SKIPPED_NOT_REQUIRED"
        else:
            status = "FAIL_REQUIRED"
            error_code = ERR_CROSS_ACTOR_ISOLATION
    elif not bindings:
        if scope_mode_effective == SCOPE_MODE_CATALOG_ALL:
            stale_reasons.append("actor_session_bindings_missing")
            if inspection_mode:
                status = "SKIPPED_NOT_REQUIRED"
                stale_reasons.append("inspection_scope_missing_actor_binding_set")
            else:
                status = "FAIL_REQUIRED"
                error_code = ERR_CROSS_ACTOR_ISOLATION
        else:
            stale_reasons.append(f"actor_session_bindings_missing_for_actor:{actor_id}")
            if inspection_mode:
                status = "SKIPPED_NOT_REQUIRED"
                stale_reasons.append("inspection_scope_missing_actor_binding_set")
            else:
                status = "FAIL_REQUIRED"
                error_code = ERR_CROSS_ACTOR_ISOLATION
    else:
        stale_reasons.extend(scoped_stale_reasons)
        if stale_reasons:
            status = "FAIL_REQUIRED"
            error_code = ERR_CROSS_ACTOR_ISOLATION

    stale_reasons = sorted(set(stale_reasons))
    scope_stale_reasons = sorted(set(scope_stale_reasons))

    if scope_mode_effective == SCOPE_MODE_ACTOR_PRIMARY:
        if global_observation_stale_reasons:
            global_observation_status = "WARN_NON_BLOCKING"
        else:
            global_observation_status = "PASS_REQUIRED"
    elif scope_mode_effective == SCOPE_MODE_CATALOG_ALL:
        global_observation_status = "PASS_REQUIRED" if status != "FAIL_REQUIRED" else "FAIL_REQUIRED"

    payload = {
        "catalog_path": str(catalog_path),
        "identity_id": str(args.identity_id or "").strip(),
        "actor_id": actor_id,
        "operation": operation,
        "scope_mode_requested": scope_mode_requested,
        "scope_mode_effective": scope_mode_effective,
        "scope_stale_reasons": scope_stale_reasons,
        "active_identities": active_ids,
        "actor_binding_count": len(bindings),
        "actor_binding_count_total": len(all_bindings),
        "actor_binding_count_non_target": len(non_target_bindings),
        "cross_actor_isolation_status": status,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
        "global_observation_status": global_observation_status,
        "global_observation_stale_reasons": global_observation_stale_reasons,
        "actor_bindings": [
            {
                "actor_id": str(b.get("actor_id", "")).strip(),
                "identity_id": str(b.get("identity_id", "")).strip(),
                "session_id": str(b.get("session_id", "")).strip(),
                "binding_key_mode": str(b.get("binding_key_mode", "")).strip(),
                "session_entry_count": int(b.get("session_entry_count", 0) or 0),
                "actor_session_path": str(b.get("actor_session_path", "")),
            }
            for b in bindings
        ],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"}:
            print(
                "[OK] cross-actor isolation validated: "
                f"catalog={catalog_path} scope={scope_mode_effective} actor={actor_id or 'n/a'} "
                f"actor_bindings={len(bindings)} active_identities={active_ids} status={status}"
            )
        else:
            print(f"[FAIL] {error_code or ERR_CROSS_ACTOR_ISOLATION} cross-actor isolation validation failed")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
