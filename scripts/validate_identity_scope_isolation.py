#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from resolve_identity_context import (
    _default_user_identity_home,
    _detect_repo_root,
    _project_identity_home_from_repo_catalog,
    default_identity_home,
    default_local_catalog_path,
    resolve_identity,
)


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


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


def _resolve_project_catalog_from_repo(repo_catalog: Path) -> Path:
    repo_catalog = repo_catalog.expanduser().resolve()
    repo_root = _detect_repo_root(repo_catalog.parent)
    project_identity_home = _project_identity_home_from_repo_catalog(repo_root, repo_catalog)
    return (project_identity_home / "catalog.local.yaml").resolve()


def _resolve_global_catalog() -> Path:
    return (_default_user_identity_home() / "catalog.local.yaml").resolve()


def _cross_layer_duplicate_details(identity_id: str, local_catalog: Path, repo_catalog: Path) -> list[dict]:
    local_catalog = local_catalog.expanduser().resolve()
    project_catalog = _resolve_project_catalog_from_repo(repo_catalog)
    global_catalog = _resolve_global_catalog()
    candidates = []
    for p in [project_catalog, global_catalog]:
        rp = p.expanduser().resolve()
        if rp == local_catalog:
            continue
        if rp.exists():
            candidates.append(rp)

    if not local_catalog.exists():
        return []
    local_doc = _load_yaml(local_catalog)
    local_row = _find_identity_row(local_doc, identity_id)
    if not local_row:
        return []

    out: list[dict] = []
    for other_catalog in candidates:
        try:
            other_doc = _load_yaml(other_catalog)
        except Exception:
            continue
        other_row = _find_identity_row(other_doc, identity_id)
        if not other_row:
            continue
        out.append(
            {
                "other_catalog": str(other_catalog),
                "other_pack_path": str(other_row.get("pack_path", "")),
                "other_status": str(other_row.get("status", "")),
                "other_profile": str(other_row.get("profile", "")),
                "other_runtime_mode": str(other_row.get("runtime_mode", "")),
                "other_runtime_identity": _is_runtime_row(other_row),
                "other_active": _is_active_row(other_row),
                "local_catalog": str(local_catalog),
                "local_pack_path": str(local_row.get("pack_path", "")),
                "local_status": str(local_row.get("status", "")),
                "local_profile": str(local_row.get("profile", "")),
                "local_runtime_mode": str(local_row.get("runtime_mode", "")),
                "local_runtime_identity": _is_runtime_row(local_row),
                "local_active": _is_active_row(local_row),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate scope-isolation for an identity.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    ap.add_argument(
        "--allow-cross-layer-runtime-duplicate",
        action="store_true",
        help="allow runtime duplicate identity_id across project/global catalogs (non-default; for migration only)",
    )
    args = ap.parse_args()

    local_catalog = (
        Path(args.catalog).expanduser().resolve()
        if args.catalog
        else default_local_catalog_path(default_identity_home()).resolve()
    )
    repo_catalog = Path(args.repo_catalog).expanduser().resolve()

    try:
        ctx = resolve_identity(
            args.identity_id,
            repo_catalog,
            local_catalog,
            preferred_scope=args.scope,
            allow_conflict=False,
        )
    except Exception as exc:
        print(f"[FAIL] resolve failed: {exc}")
        return 1

    explicit_scope = bool(str(args.scope or "").strip())
    if bool(ctx.get("conflict_detected")) and not explicit_scope:
        print("[FAIL] scope conflict detected")
        return 1

    scope = str(ctx.get("resolved_scope", "")).upper()
    profile = str(ctx.get("profile", "")).lower()
    runtime_mode = str(ctx.get("runtime_mode", "")).lower()

    if profile == "runtime" and scope == "SYSTEM":
        print("[FAIL] runtime identity cannot resolve to SYSTEM scope")
        return 1
    if runtime_mode == "local_only" and scope == "SYSTEM":
        print("[FAIL] local_only identity resolved to SYSTEM scope")
        return 1

    resolved = Path(str(ctx.get("resolved_pack_path", ""))).expanduser().resolve()
    if args.identity_id not in resolved.as_posix():
        print(f"[FAIL] resolved pack path does not include identity id: {resolved}")
        return 1

    # no other identity may point to exact same pack path
    catalog = _load_yaml(local_catalog if local_catalog.exists() else repo_catalog)
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
        print(f"[FAIL] pack-path collision detected with identities: {sorted(collisions)}")
        return 1

    duplicate_rows = _cross_layer_duplicate_details(args.identity_id, local_catalog, repo_catalog)
    if duplicate_rows and not args.allow_cross_layer_runtime_duplicate:
        blocking_rows = [
            row
            for row in duplicate_rows
            if row.get("local_runtime_identity")
            and row.get("other_runtime_identity")
            and row.get("local_active")
            and row.get("other_active")
        ]
        if blocking_rows:
            details = [
                {
                    "local_catalog": r["local_catalog"],
                    "local_pack_path": r["local_pack_path"],
                    "other_catalog": r["other_catalog"],
                    "other_pack_path": r["other_pack_path"],
                    "identity_id": args.identity_id,
                }
                for r in blocking_rows
            ]
            print(
                "[FAIL] cross-layer runtime duplicate identity_id detected; "
                "same active runtime identity appears in both project/global catalogs. "
                f"details={details}"
            )
            print(
                "[HINT] keep a single active runtime owner for this identity_id "
                "and deactivate/quarantine the duplicate layer entry."
            )
            return 1

    print(f"[OK] scope isolation validated: identity={args.identity_id}, scope={scope}, pack={resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
