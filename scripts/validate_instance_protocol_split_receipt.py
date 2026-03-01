#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import boolish, contract_required, load_json, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SPLIT_NOTICE_MISSING = "IP-SPLIT-001"
ERR_TRIGGER_FIELD_INVALID = "IP-SPLIT-002"
ERR_SSOT_PATH_MISSING = "IP-SPLIT-003"
ERR_MIXED_LANE = "IP-SPLIT-004"
ERR_PROTOCOL_SANITIZATION = "IP-SPLIT-005"

LANE_INSTANCE_DECL = "instance_lane=business_execution"
LANE_PROTOCOL_DECL = "protocol_lane=governance_feedback"

ALIAS_KEYS = {
    "split_notice": "split_reminder",
    "instance_actions": "instance_action_receipt",
    "protocol_actions": "protocol_action_receipt",
    "feedback_triggered": "protocol_feedback_triggered",
    "evidence_index": "evidence_index_receipt",
}

PROTOCOL_LANE_HINTS = (
    "protocol-feedback",
    "governance",
    "required-gates",
    "validator",
    "ssot",
    "outbox-to-protocol",
    "evidence-index",
)
INSTANCE_LANE_HINTS = (
    "delivery",
    "business_execution",
    "业务执行",
    "runtime action",
    "execute user task",
)

SENSITIVE_RE = re.compile(
    r"(?i)(tenant[_-]?id|customer[_-]?id|client[_-]?id|merchant[_-]?id|sku[_-]?id|product[_-]?id|shop[_-]?id|order[_-]?id)"
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_split_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "instance_protocol_split_receipt_contract_v1",
        "instance_protocol_split_receipt_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _select_trigger_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_trigger_hard_condition_contract_v1",
        "protocol_feedback_trigger_hard_condition_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _split_artifacts_present(pack_root: Path) -> bool:
    outbox = (pack_root / "runtime" / "protocol-feedback" / "outbox-to-protocol").resolve()
    if not outbox.exists():
        return False
    return any(p.is_file() for p in outbox.glob("SPLIT_RECEIPT_*"))


def _coerce_bool(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return None


def _stringify(v: Any) -> str:
    if isinstance(v, str):
        return v
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


def _extract_value(doc: dict[str, Any], canonical: str) -> tuple[Any, str]:
    if canonical in doc:
        return doc.get(canonical), canonical
    alias = ALIAS_KEYS.get(canonical, "")
    if alias and alias in doc:
        return doc.get(alias), alias
    return None, ""


def _collect_feedback_paths(protocol_actions: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(protocol_actions, dict):
        raw = protocol_actions.get("feedback_paths")
        if isinstance(raw, list):
            for x in raw:
                token = str(x).strip()
                if token:
                    paths.append(token)
        for k in ("path", "ssot_path", "outbox_path", "evidence_index_path"):
            token = str(protocol_actions.get(k, "")).strip()
            if token:
                paths.append(token)
    elif isinstance(protocol_actions, list):
        for x in protocol_actions:
            token = str(x).strip()
            if token:
                paths.append(token)
    else:
        text = str(protocol_actions or "")
        for m in re.finditer(r"runtime/protocol-feedback/[^\s\"']+", text):
            paths.append(m.group(0).strip())
    return sorted(set(paths))


def _protocol_actions_explicit_none(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in {"none", "no_action", "not_triggered", "n/a"}
    if isinstance(v, dict):
        marker = str(v.get("mode") or v.get("status") or "").strip().lower()
        has_paths = bool(v.get("feedback_paths"))
        return marker in {"none", "not_triggered"} and not has_paths
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate instance/protocol split receipt contract (dual-lane machine-readable receipt).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--receipt", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
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

    split_contract = _select_split_contract(task)
    trigger_contract = _select_trigger_contract(task)
    required = contract_required(split_contract) if split_contract else False
    auto_required_signal = False
    if not required and (args.receipt.strip() or _split_artifacts_present(pack_path)):
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "instance_protocol_split_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "receipt_path": "",
        "split_notice": "",
        "instance_actions_ref": "",
        "protocol_actions_ref": "",
        "feedback_triggered": None,
        "evidence_index_ref": "",
        "feedback_paths": [],
        "trigger_conditions": {
            "recurrence_ge_2": False,
            "false_green_or_red": False,
            "evidence_missing_or_unlinked": False,
            "lane_contamination_detected": False,
            "hard_condition_any": False,
        },
        "alias_fields_used": {},
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(split_contract.get("receipt_path_pattern", "")).strip() if isinstance(split_contract, dict) else ""
    if not pattern:
        pattern = "runtime/protocol-feedback/outbox-to-protocol/SPLIT_RECEIPT_*.json"
    receipt_path = resolve_report_path(report=args.receipt, pattern=pattern, pack_root=pack_path)
    if receipt_path is None:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SPLIT_NOTICE_MISSING
        payload["stale_reasons"] = ["split_receipt_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["receipt_path"] = str(receipt_path)
    try:
        receipt_doc = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(receipt_doc, dict):
            raise ValueError("receipt json root must be object")
    except Exception as exc:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SPLIT_NOTICE_MISSING
        payload["stale_reasons"] = [f"split_receipt_invalid_json:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    split_notice_val, split_key = _extract_value(receipt_doc, "split_notice")
    instance_actions_val, instance_key = _extract_value(receipt_doc, "instance_actions")
    protocol_actions_val, protocol_key = _extract_value(receipt_doc, "protocol_actions")
    feedback_trigger_val, trigger_key = _extract_value(receipt_doc, "feedback_triggered")
    evidence_index_val, evidence_key = _extract_value(receipt_doc, "evidence_index")
    payload["alias_fields_used"] = {
        "split_notice": split_key,
        "instance_actions": instance_key,
        "protocol_actions": protocol_key,
        "feedback_triggered": trigger_key,
        "evidence_index": evidence_key,
    }

    split_notice = str(split_notice_val or "").strip()
    payload["split_notice"] = split_notice
    if not split_notice:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SPLIT_NOTICE_MISSING
        payload["stale_reasons"] = ["split_notice_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if LANE_INSTANCE_DECL not in split_notice or LANE_PROTOCOL_DECL not in split_notice:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SPLIT_NOTICE_MISSING
        payload["stale_reasons"] = ["split_notice_lane_declaration_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    feedback_triggered = _coerce_bool(feedback_trigger_val)
    payload["feedback_triggered"] = feedback_triggered
    if feedback_triggered is None:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TRIGGER_FIELD_INVALID
        payload["stale_reasons"] = ["feedback_triggered_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    instance_actions_ref = str(instance_actions_val or "").strip()
    protocol_actions_ref = str(protocol_actions_val or "").strip()
    evidence_index_ref = str(evidence_index_val or "").strip()
    payload["instance_actions_ref"] = instance_actions_ref
    payload["protocol_actions_ref"] = protocol_actions_ref
    payload["evidence_index_ref"] = evidence_index_ref

    feedback_paths = _collect_feedback_paths(protocol_actions_val)
    payload["feedback_paths"] = feedback_paths

    has_outbox_path = any("runtime/protocol-feedback/outbox-to-protocol/" in p for p in feedback_paths)
    has_index_path = any("runtime/protocol-feedback/evidence-index/" in p for p in feedback_paths) or (
        "runtime/protocol-feedback/evidence-index/" in evidence_index_ref
    )

    if feedback_triggered:
        if not has_outbox_path or not has_index_path:
            payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_SSOT_PATH_MISSING
            payload["stale_reasons"] = [
                "feedback_triggered_true_but_ssot_paths_missing",
                f"has_outbox_path={str(has_outbox_path).lower()}",
                f"has_evidence_index_path={str(has_index_path).lower()}",
            ]
            _emit(payload, json_only=args.json_only)
            return 1
    else:
        if not _protocol_actions_explicit_none(protocol_actions_val):
            payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_TRIGGER_FIELD_INVALID
            payload["stale_reasons"] = ["feedback_triggered_false_requires_protocol_actions_none"]
            _emit(payload, json_only=args.json_only)
            return 1

    instance_text = _stringify(instance_actions_val).lower()
    protocol_text = _stringify(protocol_actions_val).lower()
    lane_contamination = any(tok in instance_text for tok in PROTOCOL_LANE_HINTS) or any(
        tok in protocol_text for tok in INSTANCE_LANE_HINTS
    )
    if boolish(receipt_doc.get("lane_contamination_detected", False)):
        lane_contamination = True

    if lane_contamination:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MIXED_LANE
        payload["stale_reasons"] = ["mixed_lane_content_detected"]
        payload["trigger_conditions"]["lane_contamination_detected"] = True
        _emit(payload, json_only=args.json_only)
        return 1

    protocol_payload_text = f"{split_notice}\n{protocol_text}\n{evidence_index_ref}".strip()
    if SENSITIVE_RE.search(protocol_payload_text):
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PROTOCOL_SANITIZATION
        payload["stale_reasons"] = ["protocol_lane_contains_business_scene_constant"]
        _emit(payload, json_only=args.json_only)
        return 1

    trig_doc = receipt_doc.get("trigger_conditions")
    if not isinstance(trig_doc, dict):
        trig_doc = {}
    recurrence_count = int(trig_doc.get("governance_issue_recurrence_count") or receipt_doc.get("governance_issue_recurrence_count") or 0)
    false_green_red = boolish(trig_doc.get("false_green_or_red_detected", receipt_doc.get("false_green_or_red_detected")))
    evidence_missing = boolish(trig_doc.get("evidence_missing_or_unlinked", receipt_doc.get("evidence_missing_or_unlinked")))
    lane_contamination_flag = boolish(trig_doc.get("lane_contamination_detected", False))

    hard_any = recurrence_count >= 2 or false_green_red or evidence_missing or lane_contamination_flag
    payload["trigger_conditions"] = {
        "recurrence_ge_2": recurrence_count >= 2,
        "false_green_or_red": false_green_red,
        "evidence_missing_or_unlinked": evidence_missing,
        "lane_contamination_detected": lane_contamination_flag,
        "hard_condition_any": hard_any,
        "trigger_contract_declared": bool(trigger_contract),
    }
    if hard_any and not feedback_triggered:
        payload["instance_protocol_split_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TRIGGER_FIELD_INVALID
        payload["stale_reasons"] = ["hard_trigger_condition_met_but_feedback_triggered_false"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["instance_protocol_split_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

