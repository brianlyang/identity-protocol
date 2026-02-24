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


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync pack META.yaml status from catalog identities status.")
    ap.add_argument("--catalog", default=str(Path.home() / ".codex" / "identity" / "catalog.local.yaml"))
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1

    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    active_ids = [str(x.get("id", "")).strip() for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    if len([x for x in active_ids if x]) > 1:
        print(f"[FAIL] catalog has multiple active identities: {active_ids}")
        return 1

    changed = 0
    checked = 0
    for row in identities:
        iid = str(row.get("id", "")).strip()
        if not iid:
            continue
        pack_path = str(row.get("pack_path", "")).strip()
        if not pack_path:
            continue
        meta_path = Path(pack_path).expanduser().resolve() / "META.yaml"
        if not meta_path.exists():
            continue
        checked += 1
        target = str(row.get("status", "inactive")).strip().lower()
        if target not in {"active", "inactive"}:
            target = "inactive"
        meta = _load_yaml(meta_path)
        current = str(meta.get("status", "")).strip().lower()
        if current != target:
            meta["status"] = target
            _dump_yaml(meta_path, meta)
            changed += 1
            print(f"[FIX] {iid}: META.status {current or '<empty>'} -> {target}")

    print(f"[OK] meta status sync complete: checked={checked}, changed={changed}, active={active_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
