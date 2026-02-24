#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resolve_identity_context import resolve_identity


def _probe_existing_instance_dirs(identity_id: str) -> list[Path]:
    repo = Path.cwd().resolve()
    for p in [repo, *repo.parents]:
        if (p / ".git").exists():
            repo = p
            break
    user_home = Path.home() / ".codex" / "identity"
    roots = [
        user_home,
        user_home / "instances",
        user_home / "identity",
        user_home / "identities",
        repo / ".agents" / "identity",
        repo / ".agents" / "identity" / "instances",
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        p = (root / identity_id).expanduser().resolve()
        if p.exists() and p.is_dir():
            key = str(p)
            if key not in seen:
                out.append(p)
                seen.add(key)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity scope resolution is deterministic and conflict-safe.")
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
        print(f"[FAIL] scope resolution failed: {exc}")
        return 1

    resolved_scope = str(ctx.get("resolved_scope", "")).strip()
    resolved_pack_path = str(ctx.get("resolved_pack_path", "")).strip()
    if not resolved_scope:
        print("[FAIL] resolved_scope missing")
        return 1
    if not resolved_pack_path:
        print("[FAIL] resolved_pack_path missing")
        return 1
    if not Path(resolved_pack_path).expanduser().exists():
        print(f"[FAIL] resolved_pack_path does not exist: {resolved_pack_path}")
        return 1
    if bool(ctx.get("conflict_detected")):
        print("[FAIL] conflict_detected=true; explicit arbitration required before running gates")
        return 1

    scope = str(ctx.get("resolved_scope", "")).upper()
    if scope in {"USER", "REPO", "ADMIN"}:
        existing = _probe_existing_instance_dirs(args.identity_id)
        if len(existing) > 1:
            print(
                "[FAIL] duplicate runtime instance directories detected; "
                "run identity_installer scan/adopt/lock first: "
                f"{[str(x) for x in existing]}"
            )
            return 1

    print(
        "[OK] scope resolution deterministic: "
        f"identity={args.identity_id}, scope={resolved_scope}, pack={resolved_pack_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
