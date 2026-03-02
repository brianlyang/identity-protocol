#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    canonical_dirs,
    ensure_index_linkage,
    is_strict_operation,
    rel_to_feedback_root,
    resolve_feedback_root,
    utc_now_z,
    write_json,
)
from response_stamp_common import resolve_layer_intent
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SILENT_DOWNGRADE = "IP-LAYER-CAND-001"
ERR_QUESTIONS_MISSING = "IP-LAYER-CAND-002"
ERR_SEED_MISSING = "IP-LAYER-CAND-003"
ERR_SEED_UNLINKED = "IP-LAYER-CAND-004"

QUESTION_SET = [
    "which_gate_or_stage_failed",
    "latest_replay_or_evidence_path",
    "expected_protocol_optimization_target",
]

PROTOCOL_CONCERN_KEYWORDS = (
    "protocol",
    "governance",
    "required gate",
    "required-gate",
    "validator",
    "audit",
    "routing",
    "semantic",
    "protocol-feedback",
    "ssot",
    "协议",
    "治理",
    "门禁",
    "审计",
    "回传",
    "反馈",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_entry_candidate_clarification_bridge_contract_v1",
        "protocol_entry_candidate_clarification_bridge_contract",
        "protocol_inquiry_followup_chain_contract_v1",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _contains_protocol_concern(text: str) -> bool:
    t = str(text or "").strip().lower()
    if not t:
        return False
    return any(k in t for k in PROTOCOL_CONCERN_KEYWORDS)


def _resolve_intent(
    *,
    layer_intent_text: str,
    work_layer: str,
    expected_work_layer: str,
    source_layer: str,
    stamp_json: str,
) -> dict[str, Any]:
    stamp_doc: dict[str, Any] = {}
    if str(stamp_json or "").strip():
        stamp_doc = _parse_json_payload(Path(stamp_json).expanduser().resolve())
    wl = str(expected_work_layer or "").strip().lower() or str(work_layer or "").strip().lower()
    if not wl:
        wl = str(stamp_doc.get("resolved_work_layer", "")).strip().lower() or str(stamp_doc.get("work_layer", "")).strip().lower()
    if not wl:
        resolved = resolve_layer_intent(
            explicit_work_layer=work_layer,
            explicit_source_layer=source_layer,
            intent_text=layer_intent_text,
            default_work_layer="instance",
            default_source_layer="global",
        )
        return {
            "resolved_work_layer": str(resolved.get("resolved_work_layer", "")).strip().lower() or "instance",
            "resolved_source_layer": str(resolved.get("resolved_source_layer", "")).strip().lower() or "global",
            "protocol_triggered": bool(resolved.get("protocol_triggered", False)),
            "intent_confidence": float(resolved.get("intent_confidence", 0.0) or 0.0),
            "fallback_reason": str(resolved.get("fallback_reason", "")).strip(),
        }
    return {
        "resolved_work_layer": wl,
        "resolved_source_layer": str(stamp_doc.get("resolved_source_layer", "")).strip().lower() or "global",
        "protocol_triggered": bool(stamp_doc.get("protocol_triggered", False)),
        "intent_confidence": float(stamp_doc.get("intent_confidence", 0.0) or 0.0),
        "fallback_reason": str(stamp_doc.get("fallback_reason", "")).strip(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-entry candidate clarification bridge.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--stamp-json", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--auto-seed", action="store_true")
    ap.add_argument("--no-auto-seed", action="store_true")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
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

    strict = is_strict_operation(args.operation)
    auto_seed = not bool(args.no_auto_seed)
    if args.auto_seed:
        auto_seed = True

    contract = _select_contract(task)
    required_contract = bool(args.force_check or contract_required(contract))
    intent_text = str(args.layer_intent_text or "").strip()
    concern_present = _contains_protocol_concern(intent_text)
    intent = _resolve_intent(
        layer_intent_text=intent_text,
        work_layer=str(args.work_layer or "").strip(),
        expected_work_layer=str(args.expected_work_layer or "").strip(),
        source_layer=str(args.source_layer or "").strip(),
        stamp_json=str(args.stamp_json or "").strip(),
    )
    resolved_work_layer = str(intent.get("resolved_work_layer", "")).strip().lower() or "instance"
    protocol_triggered = bool(intent.get("protocol_triggered", False))
    if resolved_work_layer in {"protocol", "dual"} and protocol_triggered:
        decision = "PROTOCOL_DIRECT"
    elif concern_present:
        decision = "PROTOCOL_CANDIDATE"
    else:
        decision = "INSTANCE_DEFAULT"

    required = bool(required_contract or concern_present or decision in {"PROTOCOL_DIRECT", "PROTOCOL_CANDIDATE"})

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": bool((concern_present or decision == "PROTOCOL_CANDIDATE") and not required_contract),
        "strict_operation": strict,
        "layer_intent_text": intent_text,
        "resolved_work_layer": resolved_work_layer,
        "protocol_triggered": protocol_triggered,
        "protocol_entry_candidate_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_entry_decision": decision,
        "candidate_reason": "",
        "candidate_confidence": float(intent.get("intent_confidence", 0.0) or 0.0),
        "clarification_required": False,
        "clarification_questions": [],
        "candidate_seed_outbox_ref": "",
        "candidate_seed_index_ref": "",
        "candidate_receipt_path": "",
        "candidate_seed_path": "",
        "candidate_promotion_status": "NOT_REQUIRED",
        "error_code": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if decision == "INSTANCE_DEFAULT" and concern_present:
        payload["protocol_entry_candidate_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SILENT_DOWNGRADE
        payload["stale_reasons"] = ["candidate_silently_downgraded_without_receipt"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    if decision == "PROTOCOL_DIRECT":
        payload["protocol_entry_candidate_status"] = STATUS_PASS_REQUIRED
        payload["candidate_promotion_status"] = "PROTOCOL_DIRECT"
        payload["candidate_reason"] = "direct_protocol_signal"
        payload["stale_reasons"] = []
        _emit(payload, json_only=args.json_only)
        return 0

    if decision != "PROTOCOL_CANDIDATE":
        payload["protocol_entry_candidate_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["candidate_promotion_status"] = "NOT_REQUIRED"
        payload["stale_reasons"] = ["no_protocol_candidate_signal"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["clarification_required"] = True
    payload["clarification_questions"] = list(QUESTION_SET)
    payload["candidate_reason"] = str(intent.get("fallback_reason", "")).strip() or "weak_protocol_signal_without_direct_trigger"
    payload["candidate_promotion_status"] = "CANDIDATE_PENDING"
    if set(QUESTION_SET) - set(payload["clarification_questions"]):
        payload["protocol_entry_candidate_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_QUESTIONS_MISSING
        payload["stale_reasons"] = ["candidate_clarification_questions_missing"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    d = canonical_dirs(feedback_root)
    outbox_dir = d["outbox_dir"]
    index_path = d["index_path"]
    outbox_dir.mkdir(parents=True, exist_ok=True)

    existing_seeds = sorted([p for p in outbox_dir.glob("CANDIDATE_SEED_*.md") if p.is_file()])
    existing_receipts = sorted([p for p in outbox_dir.glob("CANDIDATE_RECEIPT_*.json") if p.is_file()])
    seed_path = existing_seeds[-1].resolve() if existing_seeds else None
    receipt_path = existing_receipts[-1].resolve() if existing_receipts else None

    if (seed_path is None or receipt_path is None) and not auto_seed:
        payload["protocol_entry_candidate_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SEED_MISSING
        payload["stale_reasons"] = ["candidate_seed_not_archived_to_canonical_channel"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    if seed_path is None or receipt_path is None:
        ts = utc_now_z().replace("-", "").replace(":", "")
        if seed_path is None:
            seed_path = (outbox_dir / f"CANDIDATE_SEED_{ts}.md").resolve()
            seed_path.write_text(
                (
                    "# Protocol Entry Candidate Seed\n\n"
                    f"- identity_id: {args.identity_id}\n"
                    f"- candidate_reason: {payload['candidate_reason']}\n"
                    f"- clarification_questions: {', '.join(QUESTION_SET)}\n"
                    f"- generated_at: {utc_now_z()}\n"
                ),
                encoding="utf-8",
            )
        if receipt_path is None:
            receipt_payload = {
                "event": "protocol_entry_candidate_receipt",
                "identity_id": args.identity_id,
                "protocol_entry_decision": decision,
                "candidate_reason": payload["candidate_reason"],
                "candidate_confidence": payload["candidate_confidence"],
                "clarification_required": True,
                "clarification_questions": QUESTION_SET,
                "candidate_seed_ref": rel_to_feedback_root(seed_path, feedback_root),
                "generated_at": utc_now_z(),
            }
            receipt_path = (outbox_dir / f"CANDIDATE_RECEIPT_{ts}.json").resolve()
            write_json(receipt_path, receipt_payload)

    seed_ref = rel_to_feedback_root(seed_path, feedback_root) if seed_path else ""
    receipt_ref = rel_to_feedback_root(receipt_path, feedback_root) if receipt_path else ""
    _, linked = ensure_index_linkage(index_path, [seed_ref, receipt_ref], section_title="Protocol candidate bridge")
    payload["candidate_seed_outbox_ref"] = seed_ref
    payload["candidate_seed_index_ref"] = str(index_path)
    payload["candidate_receipt_path"] = str(receipt_path) if receipt_path else ""
    payload["candidate_seed_path"] = str(seed_path) if seed_path else ""

    if not seed_ref or not receipt_ref:
        payload["protocol_entry_candidate_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SEED_MISSING
        payload["stale_reasons"] = ["candidate_seed_or_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    if not linked:
        payload["protocol_entry_candidate_status"] = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SEED_UNLINKED
        payload["stale_reasons"] = ["candidate_seed_index_linkage_missing"]
        _emit(payload, json_only=args.json_only)
        return 1 if strict else 0

    payload["protocol_entry_candidate_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
