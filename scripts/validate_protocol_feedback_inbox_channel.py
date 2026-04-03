#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    ALLOWED_FEEDBACK_DIRS,
    is_strict_operation,
    list_feedback_files,
    rel_to_feedback_root,
    resolve_feedback_root,
)
from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CH_MISSING = "IP-PFB-INBOX-001"
ERR_NON_STANDARD_PRIMARY = "IP-PFB-INBOX-002"
ERR_MIRROR_WITHOUT_PRIMARY = "IP-PFB-INBOX-003"

def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_canonical_inbox_channel_contract_v1",
        "protocol_feedback_canonical_inbox_channel_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate canonical protocol-feedback inbox channel contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
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
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    strict = is_strict_operation(args.operation)
    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "auto_required_signal": False,
            "strict_operation": strict,
            "protocol_feedback_inbox_channel_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "primary_channel_root": str(feedback_root),
            "missing_required_dirs": [],
            "protocol_feedback_inbox_activity_detected": False,
            "protocol_feedback_inbox_activity_refs": [],
            "non_standard_primary_refs": [],
            "mirror_reference_refs": [],
            "stale_reasons": ["fixture_profile_scope"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required_contract = bool(args.force_check or contract_required(contract))

    files = list_feedback_files(feedback_root)
    inbox_dir = (feedback_root / "inbox-from-protocol").resolve()
    evidence_dir = (feedback_root / "evidence-index").resolve()
    index_path = (evidence_dir / "INDEX.md").resolve()

    inbox_activity_refs = sorted(
        [
            rel_to_feedback_root(p, feedback_root)
            for p in files
            if rel_to_feedback_root(p, feedback_root).startswith("inbox-from-protocol/")
        ]
    )
    activity_detected = bool(inbox_activity_refs)
    auto_required_signal = bool(activity_detected)
    required = bool(required_contract or auto_required_signal)

    missing_required_dirs: list[str] = []
    for d in (inbox_dir, evidence_dir):
        if not d.exists():
            missing_required_dirs.append(str(d))

    non_standard_primary_refs: list[str] = []
    mirror_reference_refs: list[str] = []
    for p in files:
        rel = rel_to_feedback_root(p, feedback_root)
        first = rel.split("/", 1)[0] if "/" in rel else rel
        name = p.name
        if first not in ALLOWED_FEEDBACK_DIRS and (
            name.startswith("PROTOCOL_INBOX_") or name.startswith("PROTOCOL_INBOX_RECEIPT_") or name == "INDEX.md"
        ):
            non_standard_primary_refs.append(rel)
        if name.startswith("PROTOCOL_INBOX_") and first != "inbox-from-protocol":
            non_standard_primary_refs.append(rel)
            mirror_reference_refs.append(rel)
        if name.startswith("PROTOCOL_INBOX_RECEIPT_") and first != "inbox-from-protocol":
            non_standard_primary_refs.append(rel)
            mirror_reference_refs.append(rel)
        if name == "INDEX.md" and first != "evidence-index":
            non_standard_primary_refs.append(rel)

    inbox_batches = sorted(
        [
            rel_to_feedback_root(p, feedback_root)
            for p in files
            if p.name.startswith("PROTOCOL_INBOX_") and "inbox-from-protocol/" in rel_to_feedback_root(p, feedback_root)
        ]
    )
    canonical_primary_ready = bool(inbox_batches) and index_path.exists()

    stale_reasons: list[str] = []
    error_code = ""

    if not required:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "auto_required_signal": auto_required_signal,
            "strict_operation": strict,
            "protocol_feedback_inbox_channel_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "primary_channel_root": str(feedback_root),
            "missing_required_dirs": [],
            "protocol_feedback_inbox_activity_detected": False,
            "protocol_feedback_inbox_activity_refs": [],
            "non_standard_primary_refs": [],
            "mirror_reference_refs": [],
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    if missing_required_dirs:
        stale_reasons.append("missing_protocol_feedback_inbox_standard_channel")
        error_code = ERR_CH_MISSING
    if non_standard_primary_refs and not error_code:
        stale_reasons.append("non_standard_inbox_channel_as_primary")
        error_code = ERR_NON_STANDARD_PRIMARY
    if mirror_reference_refs and not canonical_primary_ready and not error_code:
        stale_reasons.append("inbox_mirror_reference_without_ssot_primary")
        error_code = ERR_MIRROR_WITHOUT_PRIMARY

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
        "auto_required_signal": auto_required_signal,
        "strict_operation": strict,
        "protocol_feedback_inbox_channel_status": status,
        "error_code": error_code,
        "primary_channel_root": str(feedback_root),
        "missing_required_dirs": missing_required_dirs,
        "protocol_feedback_inbox_activity_detected": activity_detected,
        "protocol_feedback_inbox_activity_refs": inbox_activity_refs,
        "non_standard_primary_refs": sorted(set(non_standard_primary_refs)),
        "mirror_reference_refs": sorted(set(mirror_reference_refs)),
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
