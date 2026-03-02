#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    CANONICAL_REQUIRED_DIRS,
    collect_activity_refs,
    is_strict_operation,
    list_feedback_files,
    rel_to_feedback_root,
    resolve_feedback_root,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CH_MISSING = "IP-PFB-CH-001"
ERR_NON_STANDARD_PRIMARY = "IP-PFB-CH-002"
ERR_MIRROR_WITHOUT_PRIMARY = "IP-PFB-CH-003"
ERR_SPLIT_REQUIREDIZATION = "IP-PFB-CH-006"

ALLOWED_FEEDBACK_DIRS = {
    "outbox-to-protocol",
    "evidence-index",
    "upgrade-proposals",
    "issues",
    "roundtables",
    "protocol-vendor-intel",
    "business-partner-intel",
    "vendor-intel",
    "review-notes",
}

PROTOCOL_ROOT = Path(__file__).resolve().parent.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_canonical_reply_channel_contract_v1",
        "protocol_feedback_canonical_reply_channel_contract",
        "protocol_feedback_robustness_contract_v1",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _run_split_validator(*, identity_id: str, catalog: Path, repo_catalog: Path, operation: str) -> dict[str, Any]:
    split_script = (PROTOCOL_ROOT / "scripts" / "validate_instance_protocol_split_receipt.py").resolve()
    cmd = [
        "python3",
        str(split_script),
        "--catalog",
        str(catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--json-only",
    ]
    cp = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROTOCOL_ROOT))
    payload = _parse_json_payload(cp.stdout) or {}
    payload["_rc"] = cp.returncode
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate canonical protocol-feedback reply channel contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required_contract = bool(args.force_check or contract_required(contract))

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    files = list_feedback_files(feedback_root)
    activity_refs = collect_activity_refs(feedback_root)
    activity_detected = bool(activity_refs)
    required = bool(required_contract or activity_detected)
    strict = is_strict_operation(args.operation)

    outbox_dir = (feedback_root / "outbox-to-protocol").resolve()
    evidence_dir = (feedback_root / "evidence-index").resolve()
    upgrade_dir = (feedback_root / "upgrade-proposals").resolve()
    index_path = (evidence_dir / "INDEX.md").resolve()

    missing_required_dirs: list[str] = []
    for d in (outbox_dir, evidence_dir, upgrade_dir):
        if not d.exists():
            missing_required_dirs.append(str(d))

    non_standard_primary_refs: list[str] = []
    mirror_reference_refs: list[str] = []
    protocol_feedback_activity_refs: list[str] = []
    for p in files:
        rel = rel_to_feedback_root(p, feedback_root)
        protocol_feedback_activity_refs.append(rel)
        first = rel.split("/", 1)[0] if "/" in rel else rel
        name = p.name
        if first not in ALLOWED_FEEDBACK_DIRS and (
            name.startswith("FEEDBACK_BATCH_") or name == "INDEX.md" or name.startswith("SPLIT_RECEIPT_")
        ):
            non_standard_primary_refs.append(rel)
        if first == "review-notes":
            mirror_reference_refs.append(rel)
        if name.startswith("FEEDBACK_BATCH_") and first != "outbox-to-protocol":
            non_standard_primary_refs.append(rel)
            mirror_reference_refs.append(rel)
        if name == "INDEX.md" and first != "evidence-index":
            non_standard_primary_refs.append(rel)

    outbox_batches = sorted([rel_to_feedback_root(p, feedback_root) for p in files if p.name.startswith("FEEDBACK_BATCH_") and "outbox-to-protocol/" in rel_to_feedback_root(p, feedback_root)])
    canonical_primary_ready = bool(outbox_batches) and index_path.exists()

    split_payload = _run_split_validator(
        identity_id=args.identity_id,
        catalog=catalog_path,
        repo_catalog=repo_catalog_path,
        operation=args.operation,
    )
    split_payload_rc = int(split_payload.get("_rc", 0) or 0)
    split_error_code = str(split_payload.get("error_code", "")).strip()
    split_status = str(split_payload.get("instance_protocol_split_status", "")).strip().upper()
    split_requiredized = split_status not in {"", STATUS_SKIPPED_NOT_REQUIRED}

    stale_reasons: list[str] = []
    error_code = ""

    if not required:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "auto_required_signal": False,
            "strict_operation": strict,
            "protocol_feedback_reply_channel_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "primary_channel_root": str(feedback_root),
            "protocol_feedback_activity_detected": False,
            "protocol_feedback_activity_refs": [],
            "non_standard_primary_refs": [],
            "mirror_reference_refs": [],
            "split_receipt_requiredized": False,
            "split_receipt_status": split_status,
            "split_receipt_error_code": str(split_payload.get("error_code", "")).strip(),
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    if missing_required_dirs:
        stale_reasons.append("missing_protocol_feedback_standard_channel")
        error_code = ERR_CH_MISSING
    if non_standard_primary_refs and not error_code:
        stale_reasons.append("non_standard_channel_as_primary")
        error_code = ERR_NON_STANDARD_PRIMARY
    if mirror_reference_refs and not canonical_primary_ready and not error_code:
        stale_reasons.append("mirror_reference_without_ssot_primary")
        error_code = ERR_MIRROR_WITHOUT_PRIMARY
    if activity_detected and split_status == STATUS_SKIPPED_NOT_REQUIRED and not error_code:
        stale_reasons.append("split_receipt_requiredization_missing_under_activity")
        error_code = ERR_SPLIT_REQUIREDIZATION
    if split_payload_rc != 0 and not error_code:
        stale_reasons.append("split_receipt_validator_nonzero_rc")
        error_code = split_error_code or ERR_SPLIT_REQUIREDIZATION
    if split_status == STATUS_FAIL_REQUIRED and not error_code:
        stale_reasons.append("split_receipt_fail_required")
        error_code = split_error_code or ERR_SPLIT_REQUIREDIZATION
    if strict and split_status == STATUS_WARN_NON_BLOCKING and not error_code:
        stale_reasons.append("split_receipt_warn_non_blocking_not_allowed_in_strict")
        error_code = split_error_code or ERR_SPLIT_REQUIREDIZATION

    if error_code and strict:
        status = STATUS_FAIL_REQUIRED
        rc = 1
    elif error_code:
        status = STATUS_WARN_NON_BLOCKING
        rc = 0
    else:
        status = STATUS_PASS_REQUIRED
        rc = 0

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": bool(activity_detected and not required_contract),
        "strict_operation": strict,
        "protocol_feedback_reply_channel_status": status,
        "error_code": error_code,
        "primary_channel_root": str(feedback_root),
        "missing_required_dirs": missing_required_dirs,
        "protocol_feedback_activity_detected": activity_detected,
        "protocol_feedback_activity_refs": protocol_feedback_activity_refs,
        "non_standard_primary_refs": sorted(set(non_standard_primary_refs)),
        "mirror_reference_refs": sorted(set(mirror_reference_refs)),
        "split_receipt_requiredized": split_requiredized,
        "split_receipt_status": split_status,
        "split_receipt_error_code": split_error_code,
        "split_receipt_payload_rc": split_payload_rc,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
