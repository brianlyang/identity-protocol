#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, latest_identity_upgrade_report, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_RECEIPT_MISSING = "IP-PROMO-001"
ERR_REQUIRED_FIELD_MISSING = "IP-PROMO-002"
ERR_DECISION_HASH_MISMATCH = "IP-PROMO-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
REQUIRED_FIELDS = (
    "decision_hash",
    "input_hash",
    "reviewer_role",
    "reviewer_signature_ref",
    "evidence_bundle_refs",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "status_promotion_evidence_contract_v1",
        "status_promotion_evidence_contract",
        "rq_003_promotion_evidence_pipeline_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _resolve_receipt_path(pack_path: Path, identity_id: str, explicit_receipt: str, explicit_report: str) -> tuple[Path | None, dict[str, Any] | None]:
    if explicit_receipt.strip():
        rp = Path(explicit_receipt).expanduser().resolve()
        if rp.exists() and rp.is_file():
            return rp, _load_json_file(rp)
        return None, None

    if explicit_report.strip():
        report_path = Path(explicit_report).expanduser().resolve()
        if report_path.exists() and report_path.is_file():
            report_doc = _load_json_file(report_path)
            return report_path, report_doc
        return None, None

    latest = latest_identity_upgrade_report(identity_id, pack_path)
    if latest and latest.exists():
        return latest.resolve(), _load_json_file(latest.resolve())
    return None, None


def _compute_expected_decision_hash(doc: dict[str, Any]) -> str:
    base = {
        "identity_id": str(doc.get("identity_id", "")),
        "report_path": str(doc.get("report_path", "")),
        "all_ok": bool(doc.get("all_ok", False)),
        "writeback_status": str(doc.get("writeback_status", "")),
        "permission_state": str(doc.get("permission_state", "")),
        "error_code": str(doc.get("error_code", "")),
        "protocol_mode": str(doc.get("protocol_mode", "")),
    }
    return hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _has_promotion_receipt_fields(doc: dict[str, Any]) -> bool:
    return any(str(doc.get(field, "")).strip() for field in ("decision_hash", "reviewer_signature_ref", "reviewer_role"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate promotion evidence pipeline contract (RQ-003).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--receipt", default="")
    ap.add_argument("--report", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
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
        "requiredization_current_round_linked": False,
        "promotion_pipeline_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "decision_hash": "",
        "input_hash": "",
        "reviewer_role": "",
        "reviewer_signature_ref": "",
        "evidence_bundle_refs": [],
        "receipt_path": "",
        "evidence_ref": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    receipt_path, receipt_doc = _resolve_receipt_path(pack_path, args.identity_id, args.receipt, args.report)
    if receipt_doc is None or receipt_path is None:
        payload["stale_reasons"] = ["promotion_receipt_not_found"]
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0

    payload["producer_readiness"] = True
    payload["requiredization_current_round_linked"] = _has_promotion_receipt_fields(receipt_doc)
    payload["receipt_path"] = str(receipt_path)
    payload["evidence_ref"] = str(receipt_path)

    if not payload["requiredization_current_round_linked"]:
        payload["stale_reasons"] = ["no_promotion_event_in_current_run"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_fields: list[str] = []
    for field in REQUIRED_FIELDS:
        value = receipt_doc.get(field)
        if field == "evidence_bundle_refs":
            if not isinstance(value, list) or not value:
                missing_fields.append(field)
            continue
        if not str(value or "").strip():
            missing_fields.append(field)

    decision_hash = str(receipt_doc.get("decision_hash", "")).strip()
    input_hash = str(receipt_doc.get("input_hash", "")).strip()
    reviewer_role = str(receipt_doc.get("reviewer_role", "")).strip()
    reviewer_signature_ref = str(receipt_doc.get("reviewer_signature_ref", "")).strip()
    evidence_bundle_refs = receipt_doc.get("evidence_bundle_refs") if isinstance(receipt_doc.get("evidence_bundle_refs"), list) else []

    payload["decision_hash"] = decision_hash
    payload["input_hash"] = input_hash
    payload["reviewer_role"] = reviewer_role
    payload["reviewer_signature_ref"] = reviewer_signature_ref
    payload["evidence_bundle_refs"] = evidence_bundle_refs

    if missing_fields:
        payload["promotion_pipeline_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = [f"missing_field:{name}" for name in missing_fields]
        _emit(payload, json_only=args.json_only)
        return 1

    expected_decision_hash = _compute_expected_decision_hash(receipt_doc)
    if decision_hash and decision_hash != expected_decision_hash:
        payload["promotion_pipeline_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DECISION_HASH_MISMATCH
        payload["stale_reasons"] = ["decision_hash_not_deterministic"]
        payload["expected_decision_hash"] = expected_decision_hash
        _emit(payload, json_only=args.json_only)
        return 1

    payload["promotion_pipeline_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
