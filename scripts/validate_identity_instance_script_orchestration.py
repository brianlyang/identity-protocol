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
    build_route_orchestration_matrix,
    load_manifest_doc,
    normalize_source_layer,
    orchestration_required,
    resolve_pack_task,
    validate_manifest_doc,
)

ERR_ORCHESTRATION_INVALID = "IP-ISORCH-001"
ERR_MANIFEST_INVALID = "IP-ISORCH-002"
ERR_MANIFEST_MISSING = "IP-ISORCH-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate route-to-instance-script orchestration join.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--work-layer", default="instance")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = str(args.catalog or "").strip()
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    work_layer = str(args.work_layer or "instance").strip().lower() or "instance"
    source_layer = str(args.source_layer or "").strip().lower() or normalize_source_layer(catalog_path)

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=str(args.current_task or ""),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required = orchestration_required(task_doc)
    manifest_path, manifest_doc = load_manifest_doc(pack_root)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
        "work_layer": work_layer,
        "source_layer": source_layer,
        "orchestration_required": required,
        "instance_script_orchestration_status": STATUS_SKIPPED_NOT_REQUIRED,
        "manifest_status": STATUS_SKIPPED_NOT_REQUIRED,
        "route_total_count": 0,
        "route_adopted_count": 0,
        "route_ready_count": 0,
        "route_rows": [],
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if manifest_doc is None:
        payload["instance_script_orchestration_status"] = STATUS_FAIL_REQUIRED
        payload["manifest_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANIFEST_MISSING
        payload["stale_reasons"] = ["manifest_missing_for_adopted_routes"]
        _emit(payload, json_only=args.json_only)
        return 1

    manifest_validation = validate_manifest_doc(
        manifest_doc=manifest_doc,
        manifest_path=manifest_path,
        pack_root=pack_root,
        identity_id=args.identity_id,
    )
    payload["manifest_status"] = str(manifest_validation.get("status", "")).strip() or STATUS_FAIL_REQUIRED
    if payload["manifest_status"] != STATUS_PASS_REQUIRED:
        payload["instance_script_orchestration_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANIFEST_INVALID
        payload["stale_reasons"] = list(manifest_validation.get("stale_reasons") or [])
        _emit(payload, json_only=args.json_only)
        return 1

    route_validation = build_route_orchestration_matrix(
        task_doc=task_doc,
        manifest_validation=manifest_validation,
        identity_id=args.identity_id,
        work_layer=work_layer,
        source_layer=source_layer,
    )
    payload["route_total_count"] = int(route_validation.get("route_total_count", 0))
    payload["route_adopted_count"] = int(route_validation.get("route_adopted_count", 0))
    payload["route_ready_count"] = int(route_validation.get("route_ready_count", 0))
    payload["route_rows"] = list(route_validation.get("route_rows") or [])
    payload["stale_reasons"] = list(route_validation.get("stale_reasons") or [])

    if str(route_validation.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        payload["instance_script_orchestration_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ORCHESTRATION_INVALID
        _emit(payload, json_only=args.json_only)
        return 1

    payload["instance_script_orchestration_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
