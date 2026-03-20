#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resolve_identity_context import default_local_catalog_path, resolve_identity, resolve_local_catalog_path, resolve_repo_catalog_path


RUNTIME_SCOPES = {"REPO", "USER", "ADMIN", "UNKNOWN"}


def main() -> int:
    script_ref = Path(__file__).resolve()
    ap = argparse.ArgumentParser(description="Validate scope persistence policy (runtime vs fixture).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    args = ap.parse_args()

    default_catalog = default_local_catalog_path(start=script_ref)
    local_catalog = resolve_local_catalog_path(args.catalog, start=script_ref) if args.catalog else default_catalog
    repo_catalog = resolve_repo_catalog_path(args.repo_catalog, start=script_ref)

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

    scope = str(ctx.get("resolved_scope", "")).upper()
    profile = str(ctx.get("profile", "")).lower()
    runtime_mode = str(ctx.get("runtime_mode", "")).lower()
    pack = Path(str(ctx.get("resolved_pack_path", ""))).expanduser().resolve()

    if not pack.is_absolute():
        print(f"[FAIL] pack path must be absolute: {pack}")
        return 1

    if profile == "fixture" or runtime_mode == "demo_only":
        if scope != "SYSTEM":
            print(f"[FAIL] fixture/demo identity must resolve to SYSTEM scope, got {scope}")
            return 1
    else:
        if scope not in RUNTIME_SCOPES:
            print(f"[FAIL] runtime identity resolved to invalid scope: {scope}")
            return 1
        if runtime_mode == "local_only" and scope == "SYSTEM":
            print("[FAIL] local_only identity cannot persist in SYSTEM scope")
            return 1

    if scope in {"USER", "REPO", "ADMIN"}:
        parent = pack.parent
        if not parent.exists():
            print(f"[FAIL] runtime parent directory missing: {parent}")
            return 1

    print(f"[OK] scope persistence validated: identity={args.identity_id}, scope={scope}, profile={profile}, runtime_mode={runtime_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
