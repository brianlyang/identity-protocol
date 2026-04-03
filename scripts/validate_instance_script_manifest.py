#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from instance_script_orchestration_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    load_manifest_doc,
    manifest_required,
    resolve_pack_task,
    validate_manifest_doc,
)

ERR_MANIFEST_MISSING = "IP-ISMAN-001"
ERR_MANIFEST_INVALID = "IP-ISMAN-002"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate pack-local instance script manifest structure.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = str(args.catalog or "").strip()
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=str(args.current_task or ""),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    manifest_path, manifest_doc = load_manifest_doc(pack_root)
    required = manifest_required(task_doc, pack_root)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
        "manifest_required": required,
        "instance_script_manifest_status": STATUS_SKIPPED_NOT_REQUIRED,
        "manifest_entry_status": STATUS_SKIPPED_NOT_REQUIRED,
        "manifest_script_count": 0,
        "manifest_entries": [],
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if manifest_doc is None:
        payload["instance_script_manifest_status"] = STATUS_FAIL_REQUIRED
        payload["manifest_entry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANIFEST_MISSING
        payload["stale_reasons"] = ["manifest_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    validation = validate_manifest_doc(
        manifest_doc=manifest_doc,
        manifest_path=manifest_path,
        pack_root=pack_root,
        identity_id=args.identity_id,
    )
    payload["manifest_script_count"] = int(validation.get("manifest_script_count", 0))
    payload["manifest_entries"] = list(validation.get("manifest_entries") or [])
    payload["stale_reasons"] = list(validation.get("stale_reasons") or [])

    if str(validation.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        payload["instance_script_manifest_status"] = STATUS_FAIL_REQUIRED
        payload["manifest_entry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANIFEST_INVALID
        _emit(payload, json_only=args.json_only)
        return 1

    payload["instance_script_manifest_status"] = STATUS_PASS_REQUIRED
    payload["manifest_entry_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
