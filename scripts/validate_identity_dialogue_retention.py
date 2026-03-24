#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from identity_dialogue_retention_common import (
    DIALOGUE_RETENTION_CONTRACT_ID,
    DIALOGUE_RETENTION_REPORT_ROOT_REL,
    DIALOGUE_RETENTION_STATE_REL,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    STATUS_NOT_APPLICABLE,
    clean_string,
    detect_delivery_hook_installation,
    dialogue_retention_contract_required,
    dialogue_retention_report_root,
    dialogue_retention_state_path,
    latest_dialogue_retention_supplement,
    load_optional_state,
    resolve_dialogue_retention_reference,
    resolve_dialogue_retention_validation_receipt,
    resolve_pack_task,
    thread_mirror_path,
)

ERR_MISSING = "IP-DRET-001"
ERR_CONTRACT = "IP-DRET-002"
ERR_HOOK = "IP-DRET-003"
ERR_EVIDENCE = "IP-DRET-004"
ERR_MIRROR = "IP-DRET-005"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError(f"json_root_not_object:{path}")
    return raw


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _contract_issues(contract_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if clean_string(contract_doc.get("contract_id")) != DIALOGUE_RETENTION_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    validator = clean_string(contract_doc.get("validator"))
    if validator != "scripts/validate_identity_dialogue_retention.py":
        issues.append("validator_mismatch")
    if clean_string(contract_doc.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")
    families = contract_doc.get("canonical_runtime_families")
    normalized = [clean_string(item) for item in families if clean_string(item)] if isinstance(families, list) else []
    expected = {
        "runtime/reports/dialogue-retention",
        "runtime/state/dialogue-retention",
    }
    if not expected.issubset(set(normalized)):
        issues.append("canonical_runtime_families_incomplete")
    return issues


def _path_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-owned dialogue retention raw truth mirror semantics.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--state", default="")
    ap.add_argument("--receipt", default="")
    ap.add_argument("--mirror", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required_contract, contract_doc, contract_key = dialogue_retention_contract_required(task_doc)
    hook_status, hook_reasons = detect_delivery_hook_installation(pack_root)
    force_validate = bool(clean_string(args.state) or clean_string(args.receipt) or clean_string(args.mirror) or hook_status != STATUS_SKIPPED_NOT_REQUIRED)

    report_root = dialogue_retention_report_root(pack_root)
    state_path = Path(clean_string(args.state)).expanduser().resolve() if clean_string(args.state) else dialogue_retention_state_path(pack_root)
    state_doc = load_optional_state(pack_root, identity_id=args.identity_id)
    receipt_discovery_mode = "explicit_argument" if clean_string(args.receipt) else ""
    if clean_string(args.receipt):
        receipt_path = Path(clean_string(args.receipt)).expanduser().resolve()
    else:
        receipt_path, receipt_discovery_mode = resolve_dialogue_retention_validation_receipt(pack_root, state_doc=state_doc)
    mirror_path = None
    if clean_string(args.mirror):
        mirror_path = Path(clean_string(args.mirror)).expanduser().resolve()
    elif clean_string(state_doc.get("current_thread_id")):
        mirror_path = thread_mirror_path(pack_root, clean_string(state_doc.get("current_thread_id")))

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "required_contract": required_contract,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")),
        "protocol_dialogue_retention_status": STATUS_SKIPPED_NOT_REQUIRED,
        "delivery_hook_status": hook_status,
        "report_root_status": STATUS_SKIPPED_NOT_REQUIRED,
        "state_status": STATUS_SKIPPED_NOT_REQUIRED,
        "source_session_status": STATUS_SKIPPED_NOT_REQUIRED,
        "mirror_status": STATUS_SKIPPED_NOT_REQUIRED,
        "sync_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "delivery_supplement_status": STATUS_SKIPPED_NOT_REQUIRED,
        "source_snapshot_alignment_status": STATUS_SKIPPED_NOT_REQUIRED,
        "source_live_alignment_status": STATUS_SKIPPED_NOT_REQUIRED,
        "source_live_advanced_since_last_sync": False,
        "source_live_drift_reason": "",
        "source_live_binding_mode": "",
        "state_path": str(state_path),
        "receipt_path": str(receipt_path) if receipt_path is not None else "",
        "receipt_discovery_mode": receipt_discovery_mode,
        "mirror_path": str(mirror_path) if mirror_path is not None else "",
        "thread_id": clean_string(state_doc.get("current_thread_id")),
        "source_session_file": clean_string(state_doc.get("source_session_file")),
        "source_session_line_count": int(state_doc.get("latest_source_line_count") or 0),
        "recorded_source_session_sha256": "",
        "recorded_source_session_size_bytes": 0,
        "recorded_source_session_line_count": 0,
        "sync_binding_mode": "",
        "state_binding_update_applied": True,
        "state_binding_status": STATUS_SKIPPED_NOT_REQUIRED,
        "stale_reasons": [],
        "error_code": "",
        "evidence_ref": str(task_path),
    }

    if not required_contract and not force_validate:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    issues: list[str] = []
    error_code = ""

    if required_contract:
        contract_issues = _contract_issues(contract_doc)
        if contract_issues:
            payload["protocol_dialogue_retention_status"] = STATUS_FAIL_REQUIRED
            payload["delivery_hook_status"] = STATUS_FAIL_REQUIRED
            payload["report_root_status"] = STATUS_FAIL_REQUIRED
            payload["state_status"] = STATUS_FAIL_REQUIRED
            payload["source_session_status"] = STATUS_FAIL_REQUIRED
            payload["mirror_status"] = STATUS_FAIL_REQUIRED
            payload["sync_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["delivery_supplement_status"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = contract_issues
            payload["error_code"] = ERR_CONTRACT
            _emit(payload, json_only=args.json_only)
            return 1

    payload["report_root_status"] = STATUS_PASS_REQUIRED if report_root.is_dir() else STATUS_FAIL_REQUIRED
    if payload["report_root_status"] != STATUS_PASS_REQUIRED:
        issues.append("dialogue_retention_report_root_missing")

    if hook_status == STATUS_FAIL_REQUIRED:
        issues.extend(hook_reasons)
        error_code = ERR_HOOK

    state_exists = state_path.is_file()
    payload["state_status"] = STATUS_PASS_REQUIRED if state_exists else STATUS_SKIPPED_NOT_REQUIRED
    if required_contract and not state_exists:
        payload["state_status"] = STATUS_FAIL_REQUIRED
        issues.append("dialogue_retention_state_missing")
        error_code = error_code or ERR_MISSING

    if receipt_path is None:
        if issues:
            payload["protocol_dialogue_retention_status"] = STATUS_FAIL_REQUIRED
            payload["mirror_status"] = STATUS_FAIL_REQUIRED if error_code == ERR_HOOK else payload["mirror_status"]
            payload["sync_receipt_status"] = STATUS_FAIL_REQUIRED if required_contract else STATUS_SKIPPED_NOT_REQUIRED
            payload["delivery_supplement_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["stale_reasons"] = issues
            payload["error_code"] = error_code or ERR_MISSING
            _emit(payload, json_only=args.json_only)
            return 1
        payload["protocol_dialogue_retention_status"] = STATUS_PASS_REQUIRED
        payload["sync_receipt_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["mirror_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["delivery_supplement_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["evidence_ref"] = str(state_path if state_exists else task_path)
        _emit(payload, json_only=args.json_only)
        return 0

    try:
        receipt_doc = _load_json(receipt_path)
    except Exception as exc:
        payload["protocol_dialogue_retention_status"] = STATUS_FAIL_REQUIRED
        payload["sync_receipt_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = [f"receipt_invalid_json:{exc}"]
        payload["error_code"] = ERR_EVIDENCE
        _emit(payload, json_only=args.json_only)
        return 1

    payload["receipt_path"] = str(receipt_path)
    payload["sync_receipt_status"] = STATUS_PASS_REQUIRED
    payload["thread_id"] = clean_string(receipt_doc.get("thread_id") or payload.get("thread_id"))
    payload["source_session_file"] = clean_string(receipt_doc.get("source_session_file") or payload.get("source_session_file"))
    payload["source_session_line_count"] = int(receipt_doc.get("source_session_line_count") or payload.get("source_session_line_count") or 0)
    payload["recorded_source_session_sha256"] = clean_string(receipt_doc.get("source_session_sha256"))
    payload["recorded_source_session_size_bytes"] = int(receipt_doc.get("source_session_size_bytes") or 0)
    payload["recorded_source_session_line_count"] = int(receipt_doc.get("source_session_line_count") or 0)
    payload["sync_binding_mode"] = clean_string(receipt_doc.get("sync_binding_mode")) or "active_current_thread"
    payload["state_binding_update_applied"] = bool(receipt_doc.get("state_binding_update_applied", True))
    payload["evidence_ref"] = str(receipt_path)

    if clean_string(receipt_doc.get("receipt_family")) != "identity_dialogue_retention_sync_receipt_v1":
        issues.append("receipt_family_mismatch")
    if clean_string(receipt_doc.get("current_thread_state_ref")) != DIALOGUE_RETENTION_STATE_REL.as_posix():
        issues.append("state_ref_mismatch")
    mirror_ref = clean_string(receipt_doc.get("mirror_ref"))
    if not mirror_ref:
        issues.append("mirror_ref_missing")
    else:
        resolved_mirror = resolve_dialogue_retention_reference(mirror_ref, pack_root=pack_root)
        if resolved_mirror is None:
            issues.append("mirror_ref_unresolved")
        else:
            mirror_path = resolved_mirror
            payload["mirror_path"] = str(mirror_path)
    if mirror_path is None or not mirror_path.is_file():
        issues.append("mirror_file_missing")
    elif not _path_under(report_root, mirror_path):
        issues.append("mirror_path_not_under_dialogue_retention_root")

    source_session_file = clean_string(payload.get("source_session_file"))
    source_path = Path(source_session_file).expanduser().resolve() if source_session_file else None
    expected_source_sha = clean_string(payload.get("recorded_source_session_sha256"))
    expected_source_size = int(payload.get("recorded_source_session_size_bytes") or 0)
    live_state: dict[str, Any] = {}
    expected_receipt_ref = receipt_path.relative_to(pack_root).as_posix() if _path_under(pack_root, receipt_path) else str(receipt_path)
    state_bound_current_thread = False
    if state_exists:
        try:
            live_state = _load_json(state_path)
        except Exception as exc:
            issues.append(f"state_invalid_json:{exc}")
            payload["state_status"] = STATUS_FAIL_REQUIRED
            live_state = {}
        else:
            payload["state_status"] = STATUS_PASS_REQUIRED
            latest_sync_receipt_ref = clean_string(live_state.get("latest_sync_receipt_ref"))
            state_current_thread_id = clean_string(live_state.get("current_thread_id"))
            state_source_session_file = clean_string(live_state.get("source_session_file"))
            state_mirror_ref = clean_string(live_state.get("current_thread_mirror_ref"))
            state_bound_current_thread = bool(
                payload["state_binding_update_applied"]
                and latest_sync_receipt_ref
                and latest_sync_receipt_ref == expected_receipt_ref
                and state_current_thread_id
                and state_current_thread_id == clean_string(payload.get("thread_id"))
            )
            if payload["state_binding_update_applied"]:
                if latest_sync_receipt_ref and latest_sync_receipt_ref != expected_receipt_ref:
                    issues.append("state_latest_sync_receipt_ref_mismatch")
                if state_current_thread_id and state_current_thread_id != clean_string(payload.get("thread_id")):
                    issues.append("state_thread_id_mismatch")
                if state_mirror_ref and mirror_ref and state_mirror_ref != mirror_ref:
                    issues.append("state_mirror_ref_mismatch")
                if state_source_session_file and source_session_file and state_source_session_file != source_session_file:
                    issues.append("state_source_session_file_mismatch")
            payload["state_binding_status"] = STATUS_PASS_REQUIRED
            if payload["state_binding_update_applied"]:
                payload["state_binding_status"] = STATUS_PASS_REQUIRED if state_bound_current_thread else STATUS_FAIL_REQUIRED

    if source_path is None or not source_path.is_file():
        issues.append("source_session_file_missing")
        payload["source_session_status"] = STATUS_FAIL_REQUIRED
    else:
        payload["source_session_status"] = STATUS_PASS_REQUIRED
        if mirror_path is not None and mirror_path.is_file():
            mirror_size = mirror_path.stat().st_size
            if expected_source_size and mirror_size != expected_source_size:
                issues.append("mirror_size_mismatch")
            else:
                mirror_sha = _file_sha256(mirror_path)
                if expected_source_sha and mirror_sha != expected_source_sha:
                    issues.append("mirror_sha256_mismatch")
                else:
                    payload["source_snapshot_alignment_status"] = STATUS_PASS_REQUIRED

        live_source_size = source_path.stat().st_size
        current_thread_id = clean_string(payload.get("thread_id"))
        active_thread_id = clean_string(os.environ.get("CODEX_THREAD_ID"))
        active_thread_bound = bool(active_thread_id and active_thread_id == current_thread_id)
        if expected_source_size and live_source_size == expected_source_size:
            live_source_sha = _file_sha256(source_path)
            if expected_source_sha and live_source_sha != expected_source_sha:
                issues.append("source_snapshot_sha256_mismatch")
                payload["source_live_alignment_status"] = STATUS_FAIL_REQUIRED
            else:
                payload["source_live_alignment_status"] = STATUS_PASS_REQUIRED
        elif expected_source_size and live_source_size > expected_source_size and (active_thread_bound or state_bound_current_thread):
            payload["source_live_alignment_status"] = STATUS_PASS_REQUIRED
            payload["source_live_advanced_since_last_sync"] = True
            payload["source_live_drift_reason"] = "source_session_advanced_since_last_sync"
            payload["source_live_binding_mode"] = "env_active_thread" if active_thread_bound else "state_bound_current_thread"
        elif expected_source_size and live_source_size < expected_source_size:
            issues.append("source_session_size_regressed_below_snapshot")
            payload["source_live_alignment_status"] = STATUS_FAIL_REQUIRED
        elif expected_source_size:
            payload["source_live_advanced_since_last_sync"] = live_source_size > expected_source_size
            payload["source_live_drift_reason"] = "source_session_advanced_since_last_sync" if live_source_size > expected_source_size else ""
            issues.append("source_session_advanced_since_last_sync_unbound" if live_source_size > expected_source_size else "source_session_size_mismatch")
            payload["source_live_alignment_status"] = STATUS_FAIL_REQUIRED
        else:
            payload["source_live_alignment_status"] = STATUS_NOT_APPLICABLE

    payload["mirror_status"] = STATUS_PASS_REQUIRED if mirror_path is not None and mirror_path.is_file() else STATUS_FAIL_REQUIRED

    supplement_ref = clean_string(receipt_doc.get("delivery_supplement_ref"))
    if supplement_ref:
        supplement_path = resolve_dialogue_retention_reference(supplement_ref, pack_root=pack_root)
        if supplement_path is None or not supplement_path.is_file():
            issues.append("delivery_supplement_missing")
            payload["delivery_supplement_status"] = STATUS_FAIL_REQUIRED
        else:
            payload["delivery_supplement_status"] = STATUS_PASS_REQUIRED
    else:
        latest_supplement = latest_dialogue_retention_supplement(pack_root, thread_id=clean_string(payload.get("thread_id")))
        payload["delivery_supplement_status"] = STATUS_NOT_APPLICABLE if latest_supplement is None else STATUS_PASS_REQUIRED

    if issues:
        payload["protocol_dialogue_retention_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = issues
        payload["error_code"] = error_code or (ERR_MIRROR if any(item.startswith("mirror_") for item in issues) else ERR_EVIDENCE)
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_dialogue_retention_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
