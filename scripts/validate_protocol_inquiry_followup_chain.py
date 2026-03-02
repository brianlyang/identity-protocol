#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
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
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_INQ_FOLLOWUP = "IP-LAYER-INQ-001"
ERR_INQ_STALE = "IP-LAYER-INQ-002"
ERR_INQ_LINKAGE = "IP-LAYER-INQ-003"
ERR_INQ_UNSANITIZED = "IP-LAYER-INQ-004"

QUESTION_SET = [
    "which_gate_or_stage_failed",
    "latest_replay_or_evidence_path",
    "expected_protocol_optimization_target",
]

GOVERNANCE_KEYWORDS = (
    "protocol",
    "governance",
    "required gate",
    "validator",
    "audit",
    "route",
    "split",
    "semantic",
    "协议",
    "治理",
    "门禁",
    "审计",
)

BUSINESS_KEYWORDS = (
    "tenant",
    "customer",
    "merchant",
    "shop",
    "sku",
    "order",
    "product",
    "店铺",
    "商品",
    "订单",
    "客户",
    "商家",
)

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
        "protocol_inquiry_followup_chain_contract_v1",
        "protocol_inquiry_followup_chain_contract",
        "protocol_entry_candidate_clarification_bridge_contract_v1",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _classify_signal_origin(text: str) -> str:
    t = str(text or "").strip().lower()
    has_gov = any(k in t for k in GOVERNANCE_KEYWORDS)
    has_biz = any(k in t for k in BUSINESS_KEYWORDS)
    if has_gov and has_biz:
        return "mixed_statement"
    if has_biz:
        return "business_statement"
    return "governance_statement"


def _latest_files(dir_path: Path, pattern: str) -> list[Path]:
    if not dir_path.exists():
        return []
    return sorted([p.resolve() for p in dir_path.glob(pattern) if p.is_file()], key=lambda p: p.stat().st_mtime)


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _linked_feedback_batches(feedback_batches: list[Path], linkage_tokens: list[str]) -> list[Path]:
    tokens = [str(x).strip().lower() for x in linkage_tokens if str(x).strip()]
    if not tokens:
        return []
    linked: list[Path] = []
    for p in feedback_batches:
        text = _safe_read_text(p).lower()
        if any(tok in text for tok in tokens):
            linked.append(p)
    return linked


def _normalize_feedback_ref(raw: str, feedback_root: Path) -> str:
    token = str(raw or "").strip()
    if not token:
        return ""
    p = Path(token).expanduser()
    if p.exists():
        return rel_to_feedback_root(p.resolve(), feedback_root)
    if token.startswith("outbox-to-protocol/") or token.startswith("evidence-index/") or token.startswith("upgrade-proposals/"):
        return token
    return token


def _run_candidate_validator(args: argparse.Namespace, catalog_path: Path, repo_catalog: Path) -> dict[str, Any]:
    candidate_script = (PROTOCOL_ROOT / "scripts" / "validate_protocol_entry_candidate_bridge.py").resolve()
    cmd = [
        "python3",
        str(candidate_script),
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog),
        "--identity-id",
        args.identity_id,
        "--operation",
        args.operation,
        "--force-check",
        "--json-only",
    ]
    if str(args.layer_intent_text or "").strip():
        cmd.extend(["--layer-intent-text", str(args.layer_intent_text).strip()])
    if str(args.stamp_json or "").strip():
        cmd.extend(["--stamp-json", str(args.stamp_json).strip()])
    if str(args.expected_work_layer or "").strip():
        cmd.extend(["--expected-work-layer", str(args.expected_work_layer).strip()])
    if str(args.source_layer or "").strip():
        cmd.extend(["--source-layer", str(args.source_layer).strip()])
    cp = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROTOCOL_ROOT))
    payload = _parse_json_payload(cp.stdout) or {}
    payload["_rc"] = cp.returncode
    return payload


def _hours_since(path: Path) -> float:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return 0.0
    delta = datetime.now(timezone.utc) - mtime
    return max(0.0, delta.total_seconds() / 3600.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol inquiry follow-up chain contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--stamp-json", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--auto-sanitize", action="store_true")
    ap.add_argument("--no-auto-sanitize", action="store_true")
    ap.add_argument("--auto-trigger-requiredization", action="store_true")
    ap.add_argument("--no-auto-trigger-requiredization", action="store_true")
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

    contract = _select_contract(task)
    required_contract = bool(args.force_check or contract_required(contract))
    strict = is_strict_operation(args.operation)
    auto_sanitize = not bool(args.no_auto_sanitize)
    if args.auto_sanitize:
        auto_sanitize = True
    auto_trigger_requiredization = not bool(args.no_auto_trigger_requiredization)
    if args.auto_trigger_requiredization:
        auto_trigger_requiredization = True

    max_followup_rounds = int(contract.get("max_followup_rounds", 2) if isinstance(contract, dict) else 2)
    if max_followup_rounds <= 0:
        max_followup_rounds = 2
    evidence_ttl_hours = int(contract.get("evidence_ttl_hours", 24) if isinstance(contract, dict) else 24)
    if evidence_ttl_hours <= 0:
        evidence_ttl_hours = 24

    candidate_payload = _run_candidate_validator(args, catalog_path, repo_catalog_path)
    candidate_rc = int(candidate_payload.get("_rc", 0) or 0)
    candidate_decision = str(candidate_payload.get("protocol_entry_decision", "")).strip() or "INSTANCE_DEFAULT"
    candidate_status = str(candidate_payload.get("protocol_entry_candidate_status", "")).strip().upper()
    candidate_runtime_failed = bool(candidate_rc != 0 or not candidate_status)
    followup_question_set = list(QUESTION_SET)
    inquiry_required = candidate_decision == "PROTOCOL_CANDIDATE" or candidate_runtime_failed

    intent_text = str(args.layer_intent_text or "").strip()
    signal_origin = _classify_signal_origin(intent_text)

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    d = canonical_dirs(feedback_root)
    outbox_dir = d["outbox_dir"]
    index_path = d["index_path"]
    outbox_dir.mkdir(parents=True, exist_ok=True)

    seed_ref = str(candidate_payload.get("candidate_seed_outbox_ref", "")).strip()
    seed_index_ref = str(candidate_payload.get("candidate_seed_index_ref", "")).strip()
    candidate_receipt_ref = _normalize_feedback_ref(str(candidate_payload.get("candidate_receipt_path", "")).strip(), feedback_root)
    has_seed_linkage = bool(seed_ref and seed_index_ref and Path(seed_index_ref).exists())
    feedback_batches = _latest_files(outbox_dir, "FEEDBACK_BATCH_*.md")
    feedback_linkage_refs: list[str] = [seed_ref, candidate_receipt_ref]
    linked_feedback_batches = _linked_feedback_batches(feedback_batches, feedback_linkage_refs)
    feedback_emitted = len(linked_feedback_batches) > 0

    inquiry_receipts = _latest_files(outbox_dir, "INQUIRY_RECEIPT_*.json")
    round_count = len(inquiry_receipts)
    latest_age_hours = _hours_since(inquiry_receipts[-1]) if inquiry_receipts else 0.0

    sanitization_receipts = _latest_files(outbox_dir, "SANITIZATION_PARAPHRASE_*.json")
    sanitization_ref = rel_to_feedback_root(sanitization_receipts[-1], feedback_root) if sanitization_receipts else ""
    if signal_origin in {"business_statement", "mixed_statement"} and not sanitization_ref and auto_sanitize:
        ts = utc_now_z().replace("-", "").replace(":", "")
        sanitization_path = (outbox_dir / f"SANITIZATION_PARAPHRASE_{ts}.json").resolve()
        write_json(
            sanitization_path,
            {
                "event": "protocol_inquiry_sanitization_paraphrase",
                "identity_id": args.identity_id,
                "signal_origin": signal_origin,
                "paraphrase": "business-origin inquiry sanitized for protocol governance evidence chain",
                "generated_at": utc_now_z(),
            },
        )
        sanitization_ref = rel_to_feedback_root(sanitization_path, feedback_root)
        ensure_index_linkage(index_path, [sanitization_ref], section_title="Inquiry sanitization paraphrase")

    inquiry_requiredization_triggered = False
    inquiry_requiredization_receipt_path = ""
    trigger_receipts = _latest_files(outbox_dir, "INQUIRY_REQUIREDIZATION_TRIGGER_*.json")
    if trigger_receipts:
        inquiry_requiredization_receipt_path = str(trigger_receipts[-1])
        inquiry_requiredization_triggered = True

    inquiry_state = "NOT_REQUIRED"
    if inquiry_required:
        inquiry_state = "QUESTION_REQUIRED"
        if followup_question_set:
            inquiry_state = "EVIDENCE_PENDING"
        if has_seed_linkage:
            inquiry_state = "READY_FOR_PROTOCOL_FEEDBACK"
        if feedback_emitted:
            inquiry_state = "FEEDBACK_EMITTED"

    # Persist inquiry receipt for machine-auditable chain.
    if inquiry_required:
        ts = utc_now_z().replace("-", "").replace(":", "")
        inquiry_receipt_path = (outbox_dir / f"INQUIRY_RECEIPT_{ts}.json").resolve()
        inquiry_receipt_ref = rel_to_feedback_root(inquiry_receipt_path, feedback_root)
        write_json(
            inquiry_receipt_path,
            {
                "event": "protocol_inquiry_followup_receipt",
                "identity_id": args.identity_id,
                "candidate_decision": candidate_decision,
                "inquiry_state": inquiry_state,
                "followup_question_set": followup_question_set,
                "signal_origin": signal_origin,
                "candidate_receipt_ref": candidate_receipt_ref,
                "protocol_feedback_seed_ref": seed_ref,
                "protocol_feedback_index_ref": seed_index_ref,
                "generated_at": utc_now_z(),
            },
        )
        ensure_index_linkage(index_path, [inquiry_receipt_ref], section_title="Inquiry follow-up receipts")
        inquiry_receipts = _latest_files(outbox_dir, "INQUIRY_RECEIPT_*.json")
        round_count = len(inquiry_receipts)
        latest_age_hours = _hours_since(inquiry_receipts[-1]) if inquiry_receipts else 0.0
        feedback_linkage_refs.append(inquiry_receipt_ref)
        linked_feedback_batches = _linked_feedback_batches(feedback_batches, feedback_linkage_refs)
        feedback_emitted = len(linked_feedback_batches) > 0
        if feedback_emitted:
            inquiry_state = "FEEDBACK_EMITTED"

    stale_reasons: list[str] = []
    error_code = ""

    if candidate_runtime_failed:
        stale_reasons.append("candidate_validator_runtime_failed")
        error_code = ERR_INQ_FOLLOWUP

    if inquiry_required and not followup_question_set:
        stale_reasons.append("deterministic_followup_question_set_missing")
        error_code = ERR_INQ_FOLLOWUP

    if inquiry_required and feedback_emitted and not has_seed_linkage and not error_code:
        stale_reasons.append("canonical_protocol_feedback_seed_or_index_missing_before_conclusion")
        error_code = ERR_INQ_LINKAGE

    if inquiry_required and signal_origin in {"business_statement", "mixed_statement"} and not sanitization_ref and not error_code:
        stale_reasons.append("unsanitized_business_statement_promoted")
        error_code = ERR_INQ_UNSANITIZED

    unresolved_exceeded = inquiry_required and inquiry_state != "FEEDBACK_EMITTED" and (
        round_count >= max_followup_rounds or latest_age_hours > evidence_ttl_hours
    )
    if unresolved_exceeded and not inquiry_requiredization_triggered and auto_trigger_requiredization:
        ts = utc_now_z().replace("-", "").replace(":", "")
        trigger_path = (outbox_dir / f"INQUIRY_REQUIREDIZATION_TRIGGER_{ts}.json").resolve()
        write_json(
            trigger_path,
            {
                "event": "inquiry_chain_unresolved_requiredization_trigger",
                "identity_id": args.identity_id,
                "trigger_class": "inquiry_chain_unresolved",
                "followup_round_count": round_count,
                "max_followup_rounds": max_followup_rounds,
                "latest_evidence_age_hours": round(latest_age_hours, 3),
                "evidence_ttl_hours": evidence_ttl_hours,
                "generated_at": utc_now_z(),
            },
        )
        trigger_ref = rel_to_feedback_root(trigger_path, feedback_root)
        _, linked = ensure_index_linkage(index_path, [trigger_ref], section_title="Inquiry requiredization triggers")
        if linked:
            inquiry_requiredization_triggered = True
            inquiry_requiredization_receipt_path = str(trigger_path)

    if unresolved_exceeded and not inquiry_requiredization_triggered and not error_code:
        stale_reasons.append("inquiry_evidence_missing_or_stale_and_requiredization_trigger_absent")
        error_code = ERR_INQ_STALE

    if error_code and strict:
        status = STATUS_FAIL_REQUIRED
        rc = 1
    elif error_code:
        status = STATUS_WARN_NON_BLOCKING
        rc = 0
    else:
        status = STATUS_PASS_REQUIRED if (inquiry_required or candidate_decision == "PROTOCOL_DIRECT") else STATUS_SKIPPED_NOT_REQUIRED
        rc = 0

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": bool((candidate_decision == "PROTOCOL_CANDIDATE") and not required_contract),
        "strict_operation": strict,
        "protocol_inquiry_followup_chain_status": status,
        "candidate_decision": candidate_decision,
        "candidate_status": candidate_status,
        "candidate_validator_rc": candidate_rc,
        "candidate_runtime_failed": candidate_runtime_failed,
        "inquiry_state": inquiry_state,
        "followup_question_set": followup_question_set if inquiry_required else [],
        "signal_origin": signal_origin,
        "sanitization_paraphrase_ref": sanitization_ref,
        "protocol_feedback_seed_ref": seed_ref,
        "protocol_feedback_index_ref": seed_index_ref,
        "candidate_receipt_ref": candidate_receipt_ref,
        "feedback_batch_count": len(feedback_batches),
        "feedback_linked_batch_count": len(linked_feedback_batches),
        "feedback_linked_batch_refs": [rel_to_feedback_root(p, feedback_root) for p in linked_feedback_batches],
        "followup_round_count": round_count,
        "max_followup_rounds": max_followup_rounds,
        "latest_evidence_age_hours": round(latest_age_hours, 3),
        "evidence_ttl_hours": evidence_ttl_hours,
        "inquiry_requiredization_triggered": inquiry_requiredization_triggered,
        "inquiry_requiredization_receipt_path": inquiry_requiredization_receipt_path,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
