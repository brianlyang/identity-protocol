#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from identity_artifact_family_routing_common import (
    ARTIFACT_FAMILY_ROUTING_CONTRACT_ID,
    ARTIFACT_FAMILY_ROUTING_CONTRACT_KEY,
    ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID,
    CANONICAL_FAMILY_MATRIX,
    CONTINUITY_REPORT_ROOT_REL,
    CONTINUITY_STATE_ROOT_REL,
    DIALOGUE_RETENTION_REPORT_ROOT_REL,
    DIALOGUE_RETENTION_STATE_ROOT_REL,
    EXPERIENCE_EXAMPLES_DIR_REL,
    EXPERIENCE_LOGS_DIR_REL,
    EXPERIENCE_RULEBOOK_DIR_REL,
    MEMORY_ABSORPTION_ROOT_REL,
    PROTOCOL_FEEDBACK_ROOT_REL,
    RULEBOOK_REL,
    STATUS_FAIL_REQUIRED,
    STATUS_NOT_APPLICABLE,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    TASK_HISTORY_REL,
    any_payload_under,
    clean_string,
    family_roots,
    path_under,
    resolve_artifact_family_routing_contract,
    resolve_pack_path,
    resolve_pack_task,
)
from identity_context_continuity_common import CONTEXT_CONTINUITY_CONTRACT_KEY, REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY
from identity_dialogue_retention_common import DIALOGUE_RETENTION_CONTRACT_KEY

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

ERR_CONTRACT = "IP-AFR-001"
ERR_FAMILY = "IP-AFR-002"
ERR_COLLISION = "IP-AFR-003"
ERR_MEMORY = "IP-AFR-004"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = clean_string(raw)
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _run_json_validator(cmd: list[str], status_field: str) -> dict[str, Any]:
    rc, stdout, stderr = _run(cmd)
    payload = _parse_json_payload(stdout)
    status = clean_string((payload or {}).get(status_field))
    if not status:
        status = STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    return {
        "cmd": cmd,
        "rc": rc,
        "status": status,
        "payload": payload or {},
        "stdout_tail": stdout[-400:],
        "stderr_tail": stderr[-400:],
    }


def _run_plain_validator(cmd: list[str]) -> dict[str, Any]:
    rc, stdout, stderr = _run(cmd)
    status = STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    return {
        "cmd": cmd,
        "rc": rc,
        "status": status,
        "stdout_tail": stdout[-400:],
        "stderr_tail": stderr[-400:],
    }


def _contract_issues(contract_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if clean_string(contract_doc.get("contract_id")) != ARTIFACT_FAMILY_ROUTING_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if clean_string(contract_doc.get("validator")) != ARTIFACT_FAMILY_ROUTING_VALIDATOR_ID:
        issues.append("validator_mismatch")
    if bool(contract_doc.get("required")) is not True:
        issues.append("required_flag_not_true")
    if clean_string(contract_doc.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")
    if clean_string(contract_doc.get("family_matrix_version")) != "v1.6.18":
        issues.append("family_matrix_version_mismatch")
    runtime_families = contract_doc.get("canonical_runtime_families")
    normalized_runtime = [clean_string(item) for item in runtime_families if clean_string(item)] if isinstance(runtime_families, list) else []
    if not normalized_runtime:
        issues.append("canonical_runtime_families_missing")
    forbid_names = contract_doc.get("forbid_generic_sink_names")
    normalized_forbid = {clean_string(item).lower() for item in forbid_names if clean_string(item)} if isinstance(forbid_names, list) else set()
    if "memory" not in normalized_forbid:
        issues.append("forbid_generic_sink_names_missing_memory")
    if bool(contract_doc.get("declaration_gate_not_artifact_family")) is not True:
        issues.append("declaration_gate_boundary_missing")
    rows = contract_doc.get("family_matrix")
    normalized_rows = {clean_string((row or {}).get("family")) for row in rows if isinstance(row, dict)} if isinstance(rows, list) else set()
    expected_rows = {row.name for row in CANONICAL_FAMILY_MATRIX}
    if not expected_rows.issubset(normalized_rows):
        issues.append("family_matrix_incomplete")
    return issues


def _path_status(path: Path, *, file_required: bool = False) -> str:
    if file_required:
        return STATUS_PASS_REQUIRED if path.is_file() else STATUS_FAIL_REQUIRED
    return STATUS_PASS_REQUIRED if path.exists() else STATUS_FAIL_REQUIRED


def _coerce_contract(task_doc: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        node = task_doc.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _has_dialogue_governance_reports(pack_root: Path, identity_id: str) -> bool:
    report_root = (pack_root / "runtime" / "reports").resolve()
    patterns = (
        f"dialogue-content-synthesis-{identity_id}-*.json",
        f"dialogue-cross-validation-matrix-{identity_id}-*.json",
        f"dialogue-result-support-{identity_id}-*.json",
    )
    return any(any(report_root.glob(pattern)) for pattern in patterns)


# NOTE: experience family subvalidators are injected from main so catalog paths can stay authoritative.


def _check_family_separation(pack_root: Path, identity_id: str, task_doc: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    roots = family_roots(pack_root)
    issues: list[str] = []
    continuity_roots = roots["runtime_continuity_reentry_family"]
    dialogue_roots = roots["runtime_dialogue_retention_family"]
    protocol_root = roots["runtime_protocol_feedback_family"][0]
    memory_root = roots["runtime_memory_absorption_family"][0]
    for left in dialogue_roots:
        for right in continuity_roots:
            if left == right or path_under(left, right) or path_under(right, left):
                issues.append("dialogue_retention_and_continuity_roots_not_separate")
    for root in (*dialogue_roots, *continuity_roots):
        if root == protocol_root or path_under(root, protocol_root) or path_under(protocol_root, root):
            issues.append("protocol_feedback_root_overlaps_with_dialogue_or_continuity")
        if root == memory_root or path_under(root, memory_root) or path_under(memory_root, root):
            issues.append("memory_absorption_root_overlaps_with_active_family")
    if protocol_root == memory_root or path_under(protocol_root, memory_root) or path_under(memory_root, protocol_root):
        issues.append("protocol_feedback_root_overlaps_with_memory_absorption_root")
    payload = {
        "dialogue_retention_roots": [str(path) for path in dialogue_roots],
        "continuity_roots": [str(path) for path in continuity_roots],
        "protocol_feedback_root": str(protocol_root),
        "memory_absorption_root": str(memory_root),
    }
    return (STATUS_FAIL_REQUIRED if issues else STATUS_PASS_REQUIRED), issues, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-owned artifact family routing matrix closure for one identity pack.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    repo_catalog_path = Path(clean_string(args.repo_catalog)).expanduser().resolve()
    if repo_catalog_path and not repo_catalog_path.is_absolute():
        repo_catalog_path = (REPO_ROOT / repo_catalog_path).resolve()

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required_contract, contract_doc, contract_key = resolve_artifact_family_routing_contract(task_doc)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "repo_catalog_path": str(repo_catalog_path),
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "required_contract": required_contract,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")),
        "artifact_family_routing_status": STATUS_SKIPPED_NOT_REQUIRED,
        "contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "declaration_gate_boundary_status": STATUS_SKIPPED_NOT_REQUIRED,
        "family_root_separation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pack_rulebook_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pack_task_history_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_dialogue_retention_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_dialogue_governance_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_experience_feedback_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_protocol_feedback_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_continuity_reentry_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_memory_absorption_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "family_rows": [],
        "stale_reasons": [],
        "error_code": "",
        "evidence_ref": str(task_path),
    }

    contract_declared = isinstance(task_doc.get(contract_key), dict)
    if not contract_declared and not args.force_check:
        payload["contract_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_family_routing_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["artifact_family_routing_contract_missing"]
        payload["error_code"] = ERR_CONTRACT
        _emit(payload, json_only=args.json_only)
        return 1
    if not required_contract and not args.force_check:
        payload["contract_status"] = STATUS_FAIL_REQUIRED
        payload["artifact_family_routing_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["artifact_family_routing_contract_not_required"]
        payload["error_code"] = ERR_CONTRACT
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    contract_issues = _contract_issues(contract_doc if isinstance(contract_doc, dict) else {})
    payload["contract_status"] = STATUS_FAIL_REQUIRED if contract_issues else STATUS_PASS_REQUIRED
    if contract_issues:
        issues.extend(contract_issues)

    gates = task_doc.get("gates") or {}
    if str(gates.get("reject_memory_gate", "")).strip().lower() != "required":
        payload["declaration_gate_boundary_status"] = STATUS_FAIL_REQUIRED
        issues.append("reject_memory_gate_not_required")
    else:
        payload["declaration_gate_boundary_status"] = STATUS_PASS_REQUIRED

    rulebook_path = (pack_root / RULEBOOK_REL).resolve()
    task_history_path = (pack_root / TASK_HISTORY_REL).resolve()
    payload["pack_rulebook_family_status"] = _path_status(rulebook_path, file_required=True)
    payload["pack_task_history_family_status"] = _path_status(task_history_path, file_required=True)
    if payload["pack_rulebook_family_status"] != STATUS_PASS_REQUIRED:
        issues.append("pack_rulebook_missing")
    if payload["pack_task_history_family_status"] != STATUS_PASS_REQUIRED:
        issues.append("pack_task_history_missing")

    separation_status, separation_issues, separation_detail = _check_family_separation(pack_root, args.identity_id, task_doc)
    payload["family_root_separation_status"] = separation_status
    payload["family_root_separation_detail"] = separation_detail
    issues.extend(separation_issues)

    runtime_rows: list[dict[str, Any]] = []

    # Dialogue retention family
    dret_contract = _coerce_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY)
    dret_active = bool(dret_contract.get("required")) or any_payload_under((pack_root / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve()) or any_payload_under((pack_root / DIALOGUE_RETENTION_STATE_ROOT_REL).resolve())
    if dret_active:
        dret = _run_json_validator(
            [
                "python3",
                "scripts/validate_identity_dialogue_retention.py",
                "--identity-id",
                args.identity_id,
                "--catalog",
                str(catalog_path) if catalog_path is not None else str((pack_root.parent / "catalog.local.yaml").resolve()),
                "--json-only",
            ],
            "protocol_dialogue_retention_status",
        )
        payload["runtime_dialogue_retention_family_status"] = dret["status"]
        runtime_rows.append({"family": "runtime_dialogue_retention_family", **dret})
        if dret["status"] == STATUS_FAIL_REQUIRED:
            issues.append("runtime_dialogue_retention_family_invalid")
        for field_name in ("canonical_thread_mirror_glob", "canonical_delivery_supplement_glob", "canonical_sync_receipt_glob", "canonical_state_path"):
            anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(dret_contract.get(field_name)))
            if anchor is None:
                continue
            expected_root = (pack_root / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve() if field_name != "canonical_state_path" else (pack_root / DIALOGUE_RETENTION_STATE_ROOT_REL).resolve()
            if not path_under(expected_root, anchor):
                issues.append(f"dialogue_retention_{field_name}_not_under_canonical_family")
    else:
        payload["runtime_dialogue_retention_family_status"] = STATUS_SKIPPED_NOT_REQUIRED

    # Dialogue governance family
    dgov_contract = _coerce_contract(task_doc, "dialogue_governance_contract")
    dgov_active = bool(dgov_contract) or _has_dialogue_governance_reports(pack_root, args.identity_id)
    dgov_issues: list[str] = []
    dgov_detail: dict[str, Any] = {}
    if dgov_active:
        patterns = {
            "dialogue_content_report_path_pattern": clean_string(dgov_contract.get("dialogue_content_report_path_pattern")) or f"runtime/reports/dialogue-content-synthesis-{args.identity_id}-*.json",
            "dialogue_cross_validation_report_path_pattern": clean_string(dgov_contract.get("dialogue_cross_validation_report_path_pattern")) or f"runtime/reports/dialogue-cross-validation-matrix-{args.identity_id}-*.json",
            "dialogue_result_support_report_path_pattern": clean_string(dgov_contract.get("dialogue_result_support_report_path_pattern")) or f"runtime/reports/dialogue-result-support-{args.identity_id}-*.json",
        }
        for key, raw in patterns.items():
            anchor = resolve_pack_path(pack_root, args.identity_id, raw)
            dgov_detail[key] = str(anchor) if anchor is not None else ""
            if anchor is None or not path_under((pack_root / "runtime" / "reports").resolve(), anchor):
                dgov_issues.append(f"{key}_not_under_runtime_reports")
            if anchor is not None and path_under((pack_root / DIALOGUE_RETENTION_REPORT_ROOT_REL).resolve(), anchor):
                dgov_issues.append(f"{key}_collides_with_dialogue_retention_family")
            if anchor is not None and path_under((pack_root / CONTINUITY_REPORT_ROOT_REL).resolve(), anchor):
                dgov_issues.append(f"{key}_collides_with_continuity_family")
            if anchor is not None and path_under((pack_root / PROTOCOL_FEEDBACK_ROOT_REL).resolve(), anchor):
                dgov_issues.append(f"{key}_collides_with_protocol_feedback_family")
        payload["runtime_dialogue_governance_family_status"] = STATUS_FAIL_REQUIRED if dgov_issues else STATUS_PASS_REQUIRED
        runtime_rows.append({"family": "runtime_dialogue_governance_family", "status": payload["runtime_dialogue_governance_family_status"], "detail": dgov_detail})
        issues.extend(dgov_issues)
    else:
        payload["runtime_dialogue_governance_family_status"] = STATUS_SKIPPED_NOT_REQUIRED

    # Experience feedback family
    exp_contract = _coerce_contract(task_doc, "experience_feedback_contract")
    exp_active = bool(exp_contract) or (pack_root / EXPERIENCE_RULEBOOK_DIR_REL / "positive.jsonl").exists() or (pack_root / EXPERIENCE_RULEBOOK_DIR_REL / "negative.jsonl").exists() or any_payload_under((pack_root / EXPERIENCE_LOGS_DIR_REL).resolve())
    exp_issues: list[str] = []
    exp_detail: dict[str, Any] = {}
    if exp_active:
        positive_path = resolve_pack_path(pack_root, args.identity_id, clean_string(exp_contract.get("positive_rulebook_path")) or EXPERIENCE_RULEBOOK_DIR_REL.joinpath("positive.jsonl").as_posix())
        negative_path = resolve_pack_path(pack_root, args.identity_id, clean_string(exp_contract.get("negative_rulebook_path")) or EXPERIENCE_RULEBOOK_DIR_REL.joinpath("negative.jsonl").as_posix())
        sample_anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(exp_contract.get("sample_report_path_pattern")) or EXPERIENCE_EXAMPLES_DIR_REL.as_posix())
        log_anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(exp_contract.get("feedback_log_path_pattern")) or EXPERIENCE_LOGS_DIR_REL.as_posix())
        exp_detail = {
            "positive_rulebook_path": str(positive_path) if positive_path is not None else "",
            "negative_rulebook_path": str(negative_path) if negative_path is not None else "",
            "sample_anchor_path": str(sample_anchor) if sample_anchor is not None else "",
            "log_anchor_path": str(log_anchor) if log_anchor is not None else "",
            "subvalidators": {},
        }
        if positive_path is None or positive_path.resolve() != (pack_root / EXPERIENCE_RULEBOOK_DIR_REL / "positive.jsonl").resolve():
            exp_issues.append("experience_positive_rulebook_not_canonical")
        if negative_path is None or negative_path.resolve() != (pack_root / EXPERIENCE_RULEBOOK_DIR_REL / "negative.jsonl").resolve():
            exp_issues.append("experience_negative_rulebook_not_canonical")
        if sample_anchor is None or not path_under((pack_root / EXPERIENCE_EXAMPLES_DIR_REL).resolve(), sample_anchor):
            exp_issues.append("experience_sample_anchor_not_under_runtime_examples")
        if log_anchor is None or not path_under((pack_root / EXPERIENCE_LOGS_DIR_REL).resolve(), log_anchor):
            exp_issues.append("experience_log_anchor_not_under_runtime_logs_feedback")
        if positive_path is not None and positive_path.resolve() == rulebook_path:
            exp_issues.append("experience_positive_rulebook_collides_with_pack_rulebook")
        if negative_path is not None and negative_path.resolve() == rulebook_path:
            exp_issues.append("experience_negative_rulebook_collides_with_pack_rulebook")
        if positive_path is not None and positive_path.resolve() == task_history_path:
            exp_issues.append("experience_positive_rulebook_collides_with_task_history")
        if negative_path is not None and negative_path.resolve() == task_history_path:
            exp_issues.append("experience_negative_rulebook_collides_with_task_history")
        payload["runtime_experience_feedback_family_status"] = STATUS_FAIL_REQUIRED if exp_issues else STATUS_PASS_REQUIRED
        runtime_rows.append({"family": "runtime_experience_feedback_family", "status": payload["runtime_experience_feedback_family_status"], "detail": exp_detail})
        issues.extend(exp_issues)
    else:
        payload["runtime_experience_feedback_family_status"] = STATUS_SKIPPED_NOT_REQUIRED

    # Protocol feedback family
    pfb_active = bool(any_payload_under((pack_root / PROTOCOL_FEEDBACK_ROOT_REL).resolve())) or bool(
        _coerce_contract(
            task_doc,
            "protocol_feedback_sidecar_contract_v1",
            "protocol_feedback_canonical_reply_channel_contract_v1",
            "protocol_feedback_canonical_inbox_channel_contract_v1",
            "protocol_feedback_bootstrap_ready_contract_v1",
        )
    )
    if pfb_active:
        pfb_root = (pack_root / PROTOCOL_FEEDBACK_ROOT_REL).resolve()
        pfb_detail: dict[str, Any] = {
            "protocol_feedback_root": str(pfb_root),
            "path_checks": {},
        }
        pfb_issues: list[str] = []
        path_fields: tuple[tuple[str, str], ...] = (
            ("protocol_feedback_canonical_reply_channel_contract_v1", "primary_outbox_glob"),
            ("protocol_feedback_canonical_reply_channel_contract_v1", "required_index_path"),
            ("protocol_feedback_canonical_inbox_channel_contract_v1", "primary_inbox_glob"),
            ("protocol_feedback_canonical_inbox_channel_contract_v1", "required_index_path"),
        )
        for contract_key, field_name in path_fields:
            contract = _coerce_contract(task_doc, contract_key)
            anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(contract.get(field_name))) if contract else None
            pfb_detail["path_checks"][f"{contract_key}.{field_name}"] = str(anchor) if anchor is not None else ""
            if anchor is None:
                continue
            if not path_under(pfb_root, anchor):
                pfb_issues.append(f"{contract_key}_{field_name}_not_under_protocol_feedback_root")
        payload["runtime_protocol_feedback_family_status"] = STATUS_FAIL_REQUIRED if pfb_issues else STATUS_PASS_REQUIRED
        runtime_rows.append({"family": "runtime_protocol_feedback_family", "status": payload["runtime_protocol_feedback_family_status"], "detail": pfb_detail})
        issues.extend(pfb_issues)
    else:
        payload["runtime_protocol_feedback_family_status"] = STATUS_SKIPPED_NOT_REQUIRED

    # Continuity family
    continuity_active = bool(task_doc.get(CONTEXT_CONTINUITY_CONTRACT_KEY)) or bool(task_doc.get(REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)) or any_payload_under((pack_root / CONTINUITY_REPORT_ROOT_REL).resolve()) or any_payload_under((pack_root / CONTINUITY_STATE_ROOT_REL).resolve())
    if continuity_active:
        continuity_report_root = (pack_root / CONTINUITY_REPORT_ROOT_REL).resolve()
        migration_receipt_path = (continuity_report_root / "migration-receipt.json").resolve()
        reentry_consumption_receipt_path = (continuity_report_root / "reentry-consumption-receipt.json").resolve()
        cont_detail = {
            "context_continuity": _run_json_validator([
                "python3", "scripts/validate_identity_context_continuity.py", "--identity-id", args.identity_id, "--catalog", str(catalog_path) if catalog_path is not None else str((pack_root.parent / "catalog.local.yaml").resolve()), "--json-only"
            ], "identity_context_continuity_status"),
            "reentry_brief": _run_json_validator([
                "python3", "scripts/validate_identity_reentry_brief.py", "--identity-id", args.identity_id, "--catalog", str(catalog_path) if catalog_path is not None else str((pack_root.parent / "catalog.local.yaml").resolve()), "--json-only"
            ], "identity_reentry_brief_status"),
            "reentry_consumption": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "reason": "reentry_consumption_receipt_not_present",
                "receipt_path": str(reentry_consumption_receipt_path),
            },
            "continuity_receipts": {
                "status": STATUS_SKIPPED_NOT_REQUIRED,
                "reason": "routing_validator_defers_full_receipt_family_closure_to_rq_046",
                "checkpoint_or_migration_receipt_path": str(migration_receipt_path),
                "reentry_consumption_receipt_path": str(reentry_consumption_receipt_path),
            },
        }
        cont_issues = [
            f"continuity_{name}_failed"
            for name in ("context_continuity", "reentry_brief")
            if cont_detail[name]["status"] != STATUS_PASS_REQUIRED
        ]
        if reentry_consumption_receipt_path.is_file():
            cont_detail["reentry_consumption"] = _run_json_validator([
                "python3", "scripts/validate_identity_reentry_consumption.py", "--identity-id", args.identity_id, "--catalog", str(catalog_path) if catalog_path is not None else str((pack_root.parent / "catalog.local.yaml").resolve()), "--json-only"
            ], "identity_reentry_consumption_status")
            if cont_detail["reentry_consumption"]["status"] != STATUS_PASS_REQUIRED:
                cont_issues.append("continuity_reentry_consumption_failed")
        if migration_receipt_path.is_file() and reentry_consumption_receipt_path.is_file():
            cont_detail["continuity_receipts"] = _run_json_validator([
                "python3", "scripts/validate_identity_context_continuity_receipts.py", "--identity-id", args.identity_id, "--catalog", str(catalog_path) if catalog_path is not None else str((pack_root.parent / "catalog.local.yaml").resolve()), "--json-only"
            ], "identity_context_continuity_receipt_family_status")
            if cont_detail["continuity_receipts"]["status"] != STATUS_PASS_REQUIRED:
                cont_issues.append("continuity_continuity_receipts_failed")
        cont_contract = _coerce_contract(task_doc, CONTEXT_CONTINUITY_CONTRACT_KEY)
        checkpoint_anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(cont_contract.get("canonical_checkpoint_glob"))) if cont_contract else None
        reentry_anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(cont_contract.get("canonical_reentry_brief_path"))) if cont_contract else None
        if checkpoint_anchor is not None and not path_under((pack_root / CONTINUITY_REPORT_ROOT_REL).resolve(), checkpoint_anchor):
            cont_issues.append("continuity_checkpoint_glob_not_under_canonical_report_root")
        if reentry_anchor is not None and not path_under((pack_root / CONTINUITY_STATE_ROOT_REL).resolve(), reentry_anchor):
            cont_issues.append("continuity_reentry_brief_not_under_canonical_state_root")
        reentry_contract = _coerce_contract(task_doc, REENTRY_BRIEF_CONSUMPTION_CONTRACT_KEY)
        bind_anchor = resolve_pack_path(pack_root, args.identity_id, clean_string(((reentry_contract.get("bind_object") or {}).get("artifact_ref")))) if reentry_contract else None
        if bind_anchor is not None and not path_under((pack_root / CONTINUITY_STATE_ROOT_REL).resolve(), bind_anchor):
            cont_issues.append("reentry_bind_object_not_under_canonical_continuity_state_root")
        payload["runtime_continuity_reentry_family_status"] = STATUS_FAIL_REQUIRED if cont_issues else STATUS_PASS_REQUIRED
        runtime_rows.append({"family": "runtime_continuity_reentry_family", "status": payload["runtime_continuity_reentry_family_status"], "detail": cont_detail})
        issues.extend(cont_issues)
    else:
        payload["runtime_continuity_reentry_family_status"] = STATUS_SKIPPED_NOT_REQUIRED

    # Memory absorption family
    memory_root = (pack_root / MEMORY_ABSORPTION_ROOT_REL).resolve()
    memory_issues: list[str] = []
    active_contract_paths = {
        "dialogue_retention_mirror": resolve_pack_path(pack_root, args.identity_id, clean_string((_coerce_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY).get("canonical_thread_mirror_glob") if _coerce_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY) else ""))),
        "dialogue_retention_state": resolve_pack_path(pack_root, args.identity_id, clean_string((_coerce_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY).get("canonical_state_path") if _coerce_contract(task_doc, DIALOGUE_RETENTION_CONTRACT_KEY) else ""))),
        "experience_positive": positive_path if exp_active else None,
        "experience_negative": negative_path if exp_active else None,
        "experience_sample": sample_anchor if exp_active else None,
        "experience_log": log_anchor if exp_active else None,
        "continuity_checkpoint": checkpoint_anchor if continuity_active else None,
        "continuity_reentry": reentry_anchor if continuity_active else None,
        "protocol_feedback_root": (pack_root / PROTOCOL_FEEDBACK_ROOT_REL).resolve(),
    }
    for label, path in active_contract_paths.items():
        if path is not None and path_under(memory_root, path):
            memory_issues.append(f"{label}_routes_into_memory_absorption")
    if memory_root.exists():
        payload["runtime_memory_absorption_family_status"] = STATUS_FAIL_REQUIRED if memory_issues else STATUS_PASS_REQUIRED
    else:
        payload["runtime_memory_absorption_family_status"] = STATUS_NOT_APPLICABLE if not memory_issues else STATUS_FAIL_REQUIRED
    if memory_issues:
        issues.extend(memory_issues)
    runtime_rows.append({
        "family": "runtime_memory_absorption_family",
        "status": payload["runtime_memory_absorption_family_status"],
        "detail": {
            "memory_root": str(memory_root),
            "memory_root_exists": memory_root.exists(),
            "memory_payload_present": any_payload_under(memory_root),
        },
    })

    payload["family_rows"] = runtime_rows

    if issues:
        payload["artifact_family_routing_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = sorted(dict.fromkeys(issues))
        if contract_issues:
            payload["error_code"] = ERR_CONTRACT
        elif any(reason.endswith("memory_absorption") or "memory_" in reason for reason in issues):
            payload["error_code"] = ERR_MEMORY
        elif any("collides" in reason or "overlap" in reason for reason in issues):
            payload["error_code"] = ERR_COLLISION
        else:
            payload["error_code"] = ERR_FAMILY
        _emit(payload, json_only=args.json_only)
        return 1

    payload["artifact_family_routing_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
