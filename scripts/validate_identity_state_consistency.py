#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate identity state consistency: catalog is source-of-truth; META.status must match (if present)."
    )
    ap.add_argument("--catalog", default=str(Path.home() / ".codex" / "identity" / "catalog.local.yaml"))
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1

    try:
        catalog = _load_yaml(catalog_path)
    except Exception as e:
        print(f"[FAIL] invalid catalog yaml: {e}")
        return 1

    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    if not identities:
        print(f"[FAIL] no identities in catalog: {catalog_path}")
        return 1

    active_ids = [str(x.get("id", "")).strip() for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    active_ids = [x for x in active_ids if x]

    rc = 0
    checked = 0
    for row in identities:
        iid = str(row.get("id", "")).strip()
        if not iid:
            continue
        expected = str(row.get("status", "inactive")).strip().lower()
        if expected not in {"active", "inactive"}:
            print(f"[FAIL] invalid catalog status for {iid}: {expected!r}")
            rc = 1
            continue
        pack_path = str(row.get("pack_path", "")).strip()
        if not pack_path:
            print(f"[FAIL] missing pack_path for identity: {iid}")
            rc = 1
            continue
        meta_path = Path(pack_path).expanduser().resolve() / "META.yaml"
        if not meta_path.exists():
            print(f"[FAIL] META.yaml missing for identity={iid}: {meta_path}")
            rc = 1
            continue
        try:
            meta = _load_yaml(meta_path)
        except Exception as e:
            print(f"[FAIL] invalid META.yaml for identity={iid}: {e}")
            rc = 1
            continue
        checked += 1
        meta_status = str(meta.get("status", "")).strip().lower()
        if not meta_status:
            print(f"[FAIL] META.status missing for identity={iid}: {meta_path}")
            rc = 1
            continue
        if meta_status != expected:
            print(
                "[FAIL] state mismatch: "
                f"identity={iid} catalog.status={expected} META.status={meta_status} meta={meta_path}"
            )
            rc = 1

    if rc != 0:
        return 1
    print("[OK] identity state consistency validated")
    print(f"     catalog={catalog_path}")
    print(f"     active_identities={active_ids}")
    print(f"     active_count={len(active_ids)}")
    print(f"     checked_meta_files={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
