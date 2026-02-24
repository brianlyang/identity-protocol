#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from resolve_identity_context import resolve_identity


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate scope-isolation for an identity.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="")
    args = ap.parse_args()

    local_catalog = Path(args.catalog).expanduser().resolve() if args.catalog else (Path.home() / ".codex" / "identity" / "catalog.local.yaml")
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

    if bool(ctx.get("conflict_detected")):
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

    print(f"[OK] scope isolation validated: identity={args.identity_id}, scope={scope}, pack={resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
