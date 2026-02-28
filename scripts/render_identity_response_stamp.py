#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from response_stamp_common import (
    render_external_stamp,
    render_internal_stamp,
    render_structured_context,
    resolve_stamp_context,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render dynamic identity response stamp (external/internal).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--view", choices=["external", "internal", "dual"], default="external")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=args.actor_id,
            explicit_catalog=bool(args.catalog.strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
        return 1

    external = render_external_stamp(ctx)
    internal = render_internal_stamp(ctx)
    payload = {
        "identity_id": ctx.identity_id,
        "catalog_path": str(ctx.catalog_path),
        "pack_path": str(ctx.pack_path),
        "view": args.view,
        "external_stamp": external,
        "internal_stamp": internal,
        "identity_context": render_structured_context(ctx),
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    if args.view in {"external", "dual"}:
        print(external)
    if args.view in {"internal", "dual"}:
        print(internal)
    print(json.dumps({"identity_context": payload["identity_context"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
