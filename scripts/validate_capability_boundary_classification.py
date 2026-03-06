#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_PARSE = "IP-CAPBOUND-001"
ERR_MISSING_CLASSIFICATION = "IP-CAPBOUND-002"
ERR_SOURCE_INVALID = "IP-CAPBOUND-003"

STRICT_OPERATIONS = {"readiness", "e2e", "ci", "validate", "update"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _extract_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        obj = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "capability_activation_boundary_contract_v2",
        "capability_activation_boundary_contract",
        "rq_002_capability_boundary_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _classify_boundary(cap_status: str, cap_code: str) -> tuple[str, str]:
    code = str(cap_code or "").strip().upper()
    status = str(cap_status or "").strip().upper()
    if code.startswith("IP-CAP-"):
        return "env_auth_blocker", "error_code:ip-cap-*"
    if status == "ACTIVATED":
        return "protocol_ready", "activation_status:activated"
    if status == "BLOCKED":
        return "protocol_blocker", "activation_status:blocked_non_ip-cap"
    return "unknown", "activation_status:unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability boundary classification contract (RQ-002).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--activation-policy", choices=["strict-union", "route-any-ready"], default="strict-union")
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required and args.operation in STRICT_OPERATIONS),
        "capability_boundary_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "boundary_classification": "",
        "classification_source": "",
        "capability_activation_status": "",
        "capability_activation_error_code": "",
        "capability_activation_notes": [],
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    cmd = [
        "python3",
        "scripts/validate_identity_capability_activation.py",
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(args.repo_catalog),
        "--identity-id",
        args.identity_id,
        "--activation-policy",
        args.activation_policy,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    detail = _extract_json_payload(proc.stdout)
    if not detail:
        payload["capability_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPORT_PARSE
        payload["stale_reasons"] = ["capability_activation_payload_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    activation_status = str(detail.get("capability_activation_status", "")).strip()
    activation_code = str(detail.get("capability_activation_error_code", "")).strip()
    classification, source = _classify_boundary(activation_status, activation_code)
    payload["producer_readiness"] = True
    payload["capability_activation_status"] = activation_status
    payload["capability_activation_error_code"] = activation_code
    payload["capability_activation_notes"] = detail.get("capability_activation_notes", [])
    payload["boundary_classification"] = classification
    payload["classification_source"] = source
    payload["evidence_ref"] = str(detail.get("task_path") or detail.get("pack_path") or task_path)

    if not classification:
        payload["capability_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING_CLASSIFICATION
        payload["stale_reasons"] = ["boundary_classification_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if source not in {
        "error_code:ip-cap-*",
        "activation_status:activated",
        "activation_status:blocked_non_ip-cap",
        "activation_status:unknown",
    }:
        payload["capability_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SOURCE_INVALID
        payload["stale_reasons"] = ["classification_source_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["capability_boundary_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
