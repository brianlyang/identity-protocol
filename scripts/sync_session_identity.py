#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync active identity into session evidence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--out", default="/tmp/identity-session/current.json")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 1
    data = _load_yaml(catalog)
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    target = next((x for x in rows if str(x.get("id", "")).strip() == args.identity_id), None)
    if not target:
        print(f"[FAIL] identity not found in catalog: {args.identity_id}")
        return 1
    status = str(target.get("status", "")).strip().lower()
    if status != "active":
        print(f"[FAIL] identity is not active; status={status}")
        return 1

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(target.get("pack_path", "")),
        "status": status,
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] session identity synced: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

