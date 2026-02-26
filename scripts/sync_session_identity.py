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


def _default_canonical_out(catalog: Path) -> Path:
    return (catalog.parent / "session" / "active_identity.json").resolve()


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync active identity into session evidence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--out",
        default="",
        help="canonical session pointer output path; default: <catalog_dir>/session/active_identity.json",
    )
    ap.add_argument(
        "--mirror-out",
        default="/tmp/identity-session/current.json",
        help="optional legacy mirror pointer path; empty string disables mirror write",
    )
    ap.add_argument(
        "--require-mirror",
        action="store_true",
        help="treat mirror write failure as fatal (default mirror failure is warning-only)",
    )
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

    canonical_out = Path(args.out).expanduser().resolve() if args.out.strip() else _default_canonical_out(catalog)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(target.get("pack_path", "")),
        "status": status,
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_pointer_type": "canonical",
    }
    try:
        _write_payload(canonical_out, payload)
    except Exception as exc:
        print(f"[FAIL] canonical session sync failed: {canonical_out} ({exc})")
        return 1
    print(f"[OK] session identity synced (canonical): {canonical_out}")

    mirror_raw = args.mirror_out.strip()
    if mirror_raw:
        mirror_out = Path(mirror_raw).expanduser().resolve()
        if mirror_out != canonical_out:
            mirror_payload = dict(payload)
            mirror_payload["session_pointer_type"] = "mirror"
            mirror_payload["canonical_session_pointer"] = str(canonical_out)
            try:
                _write_payload(mirror_out, mirror_payload)
                print(f"[OK] session identity mirrored: {mirror_out}")
            except Exception as exc:
                msg = f"mirror session sync failed: {mirror_out} ({exc})"
                if args.require_mirror:
                    print(f"[FAIL] {msg}")
                    return 1
                print(f"[WARN] {msg}")
        else:
            print("[INFO] mirror path equals canonical path; mirror write skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
