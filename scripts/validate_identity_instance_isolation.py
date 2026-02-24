#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resolve_identity_context import resolve_identity, resolve_protocol_root


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate runtime identity instance isolation boundary.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="USER")
    ap.add_argument("--protocol-root", default="")
    ap.add_argument("--allow-protocol-root-pack", action="store_true")
    args = ap.parse_args()

    ctx = resolve_identity(
        args.identity_id,
        Path(args.repo_catalog).expanduser().resolve(),
        Path(args.catalog).expanduser().resolve(),
        preferred_scope=args.scope,
        allow_conflict=True,
    )
    pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    if not pack.exists():
        print(f"[FAIL] resolved pack path does not exist: {pack}")
        return 1

    protocol_root = resolve_protocol_root(args.protocol_root).resolve()
    if _is_within(pack, protocol_root) and not args.allow_protocol_root_pack:
        print(
            "[FAIL] identity instance isolation violated: "
            f"pack_path inside protocol_root identity={args.identity_id} pack_path={pack} protocol_root={protocol_root}"
        )
        print("[HINT] migrate with identity_installer adopt+lock, then rerun.")
        return 1

    print(f"[OK] instance isolation validated: identity={args.identity_id} pack_path={pack}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

