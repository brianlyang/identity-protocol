#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_scope_isolation_common import (
    analyze_cross_layer_identity_uniqueness,
    load_yaml,
    resolve_global_catalog,
    resolve_project_catalog_from_repo,
)
from resolve_identity_context import (
    default_local_catalog_path,
    resolve_local_catalog_path,
    resolve_identity,
    resolve_repo_catalog_path,
)


def _find_identity_row(catalog: dict, identity_id: str) -> dict:
    for row in catalog.get("identities", []) or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() == identity_id:
            return row
    return {}


def _is_runtime_row(row: dict) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile != "fixture" and runtime_mode != "demo_only"


def _is_active_row(row: dict) -> bool:
    return str((row or {}).get("status", "")).strip().lower() in {"active", "enabled", "on"}

def main() -> int:
    script_ref = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Validate scope-isolation for an identity.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument(
        "--allow-cross-layer-runtime-duplicate",
        action="store_true",
        help="allow runtime duplicate identity_id across project/global catalogs (non-default; for migration only)",
    )
    args = ap.parse_args()

    def _emit_failure(reason: str, *, error_code: str = "IP-SCOPE-LAYER-001", extra: dict | None = None) -> int:
        payload = {
            "scope_isolation_status": "FAIL_REQUIRED",
            "error_code": error_code,
            "identity_id": args.identity_id,
            "stale_reasons": [reason],
        }
        if extra:
            payload.update(extra)
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[FAIL] {reason}")
        return 1

    local_catalog = (
        resolve_local_catalog_path(args.catalog, start=script_ref)
        if args.catalog
        else default_local_catalog_path(start=script_ref).resolve()
    )
    repo_catalog = resolve_repo_catalog_path(args.repo_catalog, start=script_ref)

    resolve_errors: list[str] = []
    resolve_catalog_candidates: list[Path] = [local_catalog]
    global_catalog = resolve_global_catalog()
    if global_catalog not in resolve_catalog_candidates:
        resolve_catalog_candidates.append(global_catalog)

    ctx: dict | None = None
    effective_catalog = local_catalog
    for candidate_catalog in resolve_catalog_candidates:
        try:
            ctx = resolve_identity(
                args.identity_id,
                repo_catalog,
                candidate_catalog,
                preferred_scope=args.scope,
                allow_conflict=False,
            )
            effective_catalog = candidate_catalog
            break
        except Exception as exc:
            resolve_errors.append(f"{candidate_catalog}:{exc}")

    if ctx is None:
        tail = resolve_errors[-1] if resolve_errors else "unknown_resolve_error"
        return _emit_failure(
            "resolve_failed",
            extra={
                "resolve_error_tail": tail,
                "resolve_errors": resolve_errors,
            },
        )

    explicit_scope = bool(str(args.scope or "").strip())
    if bool(ctx.get("conflict_detected")) and not explicit_scope:
        return _emit_failure("scope_conflict_detected")

    scope = str(ctx.get("resolved_scope", "")).upper()
    profile = str(ctx.get("profile", "")).lower()
    runtime_mode = str(ctx.get("runtime_mode", "")).lower()

    if profile == "runtime" and scope == "SYSTEM":
        return _emit_failure("runtime_identity_resolved_to_system_scope")
    if runtime_mode == "local_only" and scope == "SYSTEM":
        return _emit_failure("local_only_identity_resolved_to_system_scope")

    resolved = Path(str(ctx.get("resolved_pack_path", ""))).expanduser().resolve()
    if args.identity_id not in resolved.as_posix():
        return _emit_failure(
            "resolved_pack_path_missing_identity_id",
            extra={"resolved_pack_path": str(resolved)},
        )

    # no other identity may point to exact same pack path
    catalog = load_yaml(effective_catalog if effective_catalog.exists() else repo_catalog)
    collisions = []
    for row in catalog.get("identities", []) or []:
        if not isinstance(row, dict):
            continue
        iid = str(row.get("id", "")).strip()
        p = str(row.get("pack_path", "")).strip()
        if not iid or not p:
            continue
        if iid != args.identity_id and Path(p).expanduser().resolve() == resolved:
            collisions.append(iid)
    if collisions:
        return _emit_failure(
            "pack_path_collision_detected",
            extra={"collisions": sorted(collisions)},
        )

    global_catalog = resolve_global_catalog()
    project_catalog = effective_catalog if effective_catalog != global_catalog else resolve_project_catalog_from_repo(repo_catalog)
    uniqueness = analyze_cross_layer_identity_uniqueness(
        args.identity_id,
        project_catalog=project_catalog,
        global_catalog=global_catalog,
    )
    duplicate_detected = bool(uniqueness.get("runtime_duplicate_detected"))

    payload = {
        "scope_isolation_status": "PASS_REQUIRED",
        "error_code": "",
        "identity_id": args.identity_id,
        "resolved_scope": scope,
        "resolved_pack_path": str(resolved),
        "effective_catalog": str(effective_catalog),
        "runtime_duplicate_detected": duplicate_detected,
        "active_runtime_duplicate_detected": bool(uniqueness.get("active_runtime_duplicate_detected")),
        "duplicate_layers": uniqueness.get("runtime_duplicate_layers", []),
        "entries": uniqueness.get("entries", []),
        "stale_reasons": [],
    }
    if duplicate_detected and not args.allow_cross_layer_runtime_duplicate:
        payload["scope_isolation_status"] = "FAIL_REQUIRED"
        payload["error_code"] = "IP-SCOPE-LAYER-001"
        payload["stale_reasons"].append("cross_layer_runtime_identity_id_duplicate_detected")
        if payload["active_runtime_duplicate_detected"]:
            payload["stale_reasons"].append("cross_layer_active_runtime_duplicate_detected")
        message = (
            "[FAIL] cross-layer runtime duplicate identity_id detected; "
            "same runtime identity_id appears in both project/global catalogs. "
            f"details={uniqueness.get('entries', [])}"
        )
        hint = (
            "[HINT] keep a single runtime owner for this identity_id and archive/remove "
            "the duplicate layer entry via repair_identity_cross_layer_uniqueness.py."
        )
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(message)
            print(hint)
        return 1

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"[OK] scope isolation validated: identity={args.identity_id}, scope={scope}, pack={resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
