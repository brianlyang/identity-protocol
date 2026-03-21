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
    build_route_receipt_join_matrix,
    load_manifest_doc,
    normalize_source_layer,
    orchestration_required,
    resolve_pack_task,
    validate_manifest_doc,
)

ERR_PREREQ_INVALID = "IP-ISREC-001"
ERR_RECEIPT_JOIN_INVALID = "IP-ISREC-002"
ERR_TARGET_NOT_FOUND = "IP-ISREC-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate route/script to receipt-family join integrity.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--work-layer", default="instance")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--route", default="")
    ap.add_argument("--script-id", default="")
    ap.add_argument("--receipt", default="")
    ap.add_argument("--require-observed", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = str(args.catalog or "").strip()
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    work_layer = str(args.work_layer or "instance").strip().lower() or "instance"
    source_layer = str(args.source_layer or "").strip().lower() or normalize_source_layer(catalog_path)
    target_route = str(args.route or "").strip()
    target_script_id = str(args.script_id or "").strip()
    receipt_override = str(args.receipt or "").strip()

    if receipt_override and (not target_route or not target_script_id):
        try:
            receipt_doc = json.loads(Path(receipt_override).expanduser().resolve().read_text(encoding="utf-8"))
        except Exception:
            receipt_doc = {}
        if isinstance(receipt_doc, dict):
            target_route = target_route or str(receipt_doc.get("route_selected", "")).strip()
            target_script_id = target_script_id or str(receipt_doc.get("script_id", "")).strip()

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
    required = orchestration_required(task_doc)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
        "work_layer": work_layer,
        "source_layer": source_layer,
        "route": target_route,
        "script_id": target_script_id,
        "receipt_path": str(Path(receipt_override).expanduser().resolve()) if receipt_override else "",
        "require_observed": bool(args.require_observed),
        "orchestration_required": required,
        "route_script_receipt_join_status": STATUS_SKIPPED_NOT_REQUIRED,
        "manifest_status": STATUS_SKIPPED_NOT_REQUIRED,
        "orchestration_status": STATUS_SKIPPED_NOT_REQUIRED,
        "route_total_count": 0,
        "route_checked_count": 0,
        "route_observed_count": 0,
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
        payload["manifest_status"] = STATUS_FAIL_REQUIRED
        payload["orchestration_status"] = STATUS_FAIL_REQUIRED
        payload["route_script_receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PREREQ_INVALID
        payload["stale_reasons"] = ["manifest_missing_for_receipt_join"]
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
        payload["route_script_receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["orchestration_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PREREQ_INVALID
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
    payload["orchestration_status"] = str(route_validation.get("status", "")).strip() or STATUS_FAIL_REQUIRED
    if payload["orchestration_status"] != STATUS_PASS_REQUIRED:
        payload["route_total_count"] = int(route_validation.get("route_total_count", 0))
        payload["route_rows"] = list(route_validation.get("route_rows") or [])
        payload["route_script_receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PREREQ_INVALID
        payload["stale_reasons"] = [
            f"orchestration_prerequisite:{reason}"
            for reason in (route_validation.get("stale_reasons") or [])
        ]
        _emit(payload, json_only=args.json_only)
        return 1

    receipt_validation = build_route_receipt_join_matrix(
        pack_root=pack_root,
        task_doc=task_doc,
        manifest_validation=manifest_validation,
        route_validation=route_validation,
        identity_id=args.identity_id,
        require_observed=bool(args.require_observed),
        receipt_override=receipt_override,
        target_route=target_route,
        target_script_id=target_script_id,
    )
    payload["route_total_count"] = int(receipt_validation.get("route_total_count", 0))
    payload["route_checked_count"] = int(receipt_validation.get("route_checked_count", 0))
    payload["route_observed_count"] = int(receipt_validation.get("route_observed_count", 0))
    payload["route_rows"] = list(receipt_validation.get("route_rows") or [])
    payload["stale_reasons"] = list(receipt_validation.get("stale_reasons") or [])

    if (target_route or target_script_id) and payload["route_checked_count"] == 0:
        payload["route_script_receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TARGET_NOT_FOUND
        payload["stale_reasons"] = ["target_route_or_script_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    if str(receipt_validation.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        payload["route_script_receipt_join_status"] = str(receipt_validation.get("status", "")).strip() or STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_JOIN_INVALID
        _emit(payload, json_only=args.json_only)
        return 1

    payload["route_script_receipt_join_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
