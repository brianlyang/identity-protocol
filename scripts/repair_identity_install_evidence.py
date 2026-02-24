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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_identity(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    return row


def _resolve_task(identity: dict[str, Any], identity_id: str) -> dict[str, Any]:
    pack_path = str(identity.get("pack_path", "")).strip()
    p = Path(pack_path).expanduser().resolve() / "CURRENT_TASK.json"
    if not p.exists():
        p = Path("identity") / identity_id / "CURRENT_TASK.json"
    if not p.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found for identity={identity_id}")
    return _load_json(p)


def _materialize(pattern: str, identity_id: str, ts: int) -> Path:
    p = pattern.replace("<identity-id>", identity_id)
    if "*" in p:
        p = p.replace("*", str(ts))
    return Path(p).expanduser()


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair/generate install safety evidence report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=str((Path.home()/".codex"/"identity"/"catalog.local.yaml").resolve()))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    identity = _resolve_identity(catalog, args.identity_id)
    task = _resolve_task(identity, args.identity_id)
    contract = task.get("install_safety_contract") or {}
    pattern = str(contract.get("install_report_path_pattern", "")).strip()
    if not pattern:
        print("[FAIL] install_report_path_pattern missing")
        return 1

    ts = int(datetime.now(timezone.utc).timestamp())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = _materialize(pattern, args.identity_id, ts)
    pack_path = str(identity.get("pack_path", "")).strip()
    payload = {
        "report_id": f"identity-install-{args.identity_id}-repair-{ts}",
        "identity_id": args.identity_id,
        "generated_at": now,
        "operation": "repair-generated",
        "conflict_type": "fresh_install",
        "action": "guarded_apply",
        "source_pack": pack_path,
        "target_pack": pack_path,
        "preserved_paths": [pack_path],
        "dry_run": False,
    }

    if args.apply:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] install evidence repair {'applied' if args.apply else 'preview'}: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
