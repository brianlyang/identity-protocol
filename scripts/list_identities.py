#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="List identities from catalog with basic health signals")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--json", action="store_true", help="output json")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    catalog = _load_yaml(catalog_path)
    default_id = str(catalog.get("default_identity", "")).strip()
    rows = []
    for item in catalog.get("identities", []) or []:
        if not isinstance(item, dict):
            continue
        pack_path = str(item.get("pack_path", "")).strip()
        pack_ok = bool(pack_path and Path(pack_path).exists())
        rows.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "default": str(item.get("id")) == default_id,
                "pack_path": pack_path,
                "pack_exists": pack_ok,
                "activation_priority": ((item.get("policy") or {}).get("activation_priority")),
            }
        )

    if args.json:
        print(json.dumps({"default_identity": default_id, "identities": rows}, ensure_ascii=False, indent=2))
        return 0

    print(f"default_identity={default_id}")
    for i, r in enumerate(rows, start=1):
        star = "*" if r["default"] else " "
        print(
            f"{i}. [{star}] id={r['id']} status={r['status']} pack_exists={r['pack_exists']} "
            f"priority={r['activation_priority']} path={r['pack_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
