#!/usr/bin/env python3
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

STREAM_ID = "protocol_feedback_promotion_taxonomy_hardening"
LANE_ID = "protocol_feedback_promotion_decision_receipt_hardening"
ISSUE_CANDIDATE_ID = "protocol_feedback_promotion_decision_and_inquiry_requiredization_contract_v1"
BLOCKER_ID = "protocol_feedback_promotion_trigger_coverage_gap"
GOVERNING_LAW = (
    "matched_protocol_feedback_promotion_trigger_must_not_end_as_ordinary_answer_without_machine_artifact"
)

FIXED_WRITE_SET = (
    "scripts/protocol_feedback_promotion_decision_common.py",
    "scripts/validate_protocol_feedback_promotion_decision.py",
    "scripts/ci/run_protocol_feedback_promotion_decision_probes_ci.sh",
)

VALIDATION_BUNDLE = (
    "TMPDIR=${TMPDIR:-/tmp} python3 scripts/validate_protocol_feedback_promotion_decision.py --json-only",
    "TMPDIR=${TMPDIR:-/tmp} bash scripts/ci/run_protocol_feedback_promotion_decision_probes_ci.sh",
)

ADMITTED_TRIGGER_CLASSES = (
    "user_explicit_protocol_review_request",
    "assistant_identified_protocol_owner_gap",
    "protocol_root_cause_explanation_started",
    "recurrent_protocol_drift_detected",
)

ALLOWED_MACHINE_OUTPUTS = (
    "inquiry_requiredization_trigger",
    "promotion_decision_receipt",
    "protocol_feedback_atomic_receipt",
    "protocol_feedback_batch_receipt",
    "promotion_blocker_receipt",
)

ALLOWED_DECISIONS = (
    "emit_now",
    "pending_requiredization",
    "blocked",
    "not_required",
)

MACHINE_STATES = (
    "not_required",
    "pending",
    "emitted",
    "blocked",
    "promotion_expected",
)

REQUIRED_INQUIRY_FIELDS = (
    "trigger_class",
    "promotion_expected",
    "promotion_reason",
    "evidence_ref",
    "next_action",
    "canonical_channel_ref",
)

REQUIRED_DECISION_FIELDS = (
    "promotion_expected",
    "decision",
    "exact_trigger_classes",
    "canonical_channel_selected",
    "emission_target",
    "evidence_refs",
    "decision_identity_surface",
)

DECISION_CONDITIONAL_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "blocked": (
        "blocker_id",
        "blocker_reason",
    ),
}

REQUIRED_EMIT_RECEIPT_FIELDS = (
    "receipt_type",
    "outbox_ref",
    "evidence_ref",
    "turn_binding",
)

REQUIRED_BLOCKER_FIELDS = (
    "blocker_id",
    "blocker_reason",
    "missing_contract_surface",
    "evidence_ref",
)

TRIGGER_REASON_HINTS = {
    "user_explicit_protocol_review_request": "user explicitly requested protocol review / protocol feedback escalation",
    "assistant_identified_protocol_owner_gap": "assistant determined the root cause belongs to protocol owner side",
    "protocol_root_cause_explanation_started": "assistant already started protocol-level root-cause explanation",
    "recurrent_protocol_drift_detected": "same protocol drift class recurred within the review window",
}

NEGATIVE_REASON_HINTS = {
    "matched_trigger_without_artifact": "trigger matched but no machine-visible artifact exists",
    "promotion_expected_but_decision_receipt_absent": "promotion was expected but promotion_decision_receipt is absent",
    "emit_now_without_emit_receipt": "decision=emit_now without atomic or batch receipt",
    "blocked_without_blocker_receipt": "decision=blocked without promotion_blocker_receipt",
    "pending_without_inquiry_requiredization": "decision=pending_requiredization without inquiry_requiredization_trigger",
}


def render_json(payload: dict[str, Any], *, pretty: bool = True) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None, sort_keys=False)


def _dedupe(items: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items or []:
        token = str(item or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _field_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _missing_fields(payload: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for field in required_fields:
        if field not in payload or not _field_present(payload.get(field)):
            missing.append(field)
    return missing


def make_decision_receipt(
    *,
    trigger_classes: list[str],
    decision: str,
    emission_target: str,
    blocker_id: str = "",
    blocker_reason: str = "",
    evidence_refs: list[str] | None = None,
    decision_identity_surface: str = "instance/project",
) -> dict[str, Any]:
    return {
        "promotion_expected": bool(trigger_classes),
        "decision": decision,
        "exact_trigger_classes": _dedupe(trigger_classes),
        "canonical_channel_selected": "protocol_feedback",
        "emission_target": emission_target,
        "blocker_id": blocker_id,
        "blocker_reason": blocker_reason,
        "evidence_refs": _dedupe(evidence_refs or ["evidence://promotion/decision"]),
        "decision_identity_surface": decision_identity_surface,
    }


def make_inquiry_requiredization_trigger(
    *,
    trigger_class: str,
    evidence_ref: str,
    next_action: str = "emit_promotion_decision_receipt",
) -> dict[str, Any]:
    return {
        "trigger_class": trigger_class,
        "promotion_expected": True,
        "promotion_reason": TRIGGER_REASON_HINTS.get(trigger_class, "matched protocol feedback promotion trigger"),
        "evidence_ref": evidence_ref,
        "next_action": next_action,
        "canonical_channel_ref": "protocol_feedback",
    }


def make_atomic_receipt(*, outbox_ref: str, evidence_ref: str, turn_binding: str) -> dict[str, Any]:
    return {
        "receipt_type": "protocol_feedback_atomic_receipt",
        "outbox_ref": outbox_ref,
        "evidence_ref": evidence_ref,
        "turn_binding": turn_binding,
    }


def make_batch_receipt(*, outbox_ref: str, evidence_ref: str, turn_binding: str) -> dict[str, Any]:
    return {
        "receipt_type": "protocol_feedback_batch_receipt",
        "outbox_ref": outbox_ref,
        "evidence_ref": evidence_ref,
        "turn_binding": turn_binding,
    }


def make_blocker_receipt(
    *,
    blocker_id: str,
    blocker_reason: str,
    missing_contract_surface: str,
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "blocker_reason": blocker_reason,
        "missing_contract_surface": missing_contract_surface,
        "evidence_ref": evidence_ref,
    }


def fixture_cases() -> dict[str, dict[str, Any]]:
    ordinary = {
        "case_id": "ordinary_protocol_discussion",
        "description": "Ordinary protocol discussion that does not hit promotion trigger taxonomy.",
        "trigger_classes": [],
        "discussion_text": "This is ordinary protocol discussion and should not auto-promote.",
    }

    pending = {
        "case_id": "explicit_request_pending",
        "description": "Explicit protocol review request enters pending requiredization and emits inquiry trigger.",
        "trigger_classes": ["user_explicit_protocol_review_request"],
        "inquiry_requiredization_trigger": make_inquiry_requiredization_trigger(
            trigger_class="user_explicit_protocol_review_request",
            evidence_ref="evidence://explicit-request/pending",
        ),
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["user_explicit_protocol_review_request"],
            decision="pending_requiredization",
            emission_target="pending",
            evidence_refs=["evidence://explicit-request/pending", "evidence://explicit-request/decision"],
        ),
    }

    emitted_atomic = {
        "case_id": "owner_gap_emitted_atomic",
        "description": "Owner-gap detection emits atomic protocol feedback receipt.",
        "trigger_classes": ["assistant_identified_protocol_owner_gap"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["assistant_identified_protocol_owner_gap"],
            decision="emit_now",
            emission_target="atomic",
            evidence_refs=["evidence://owner-gap/decision", "evidence://owner-gap/emit"],
        ),
        "protocol_feedback_atomic_receipt": make_atomic_receipt(
            outbox_ref="outbox://owner-gap/atomic",
            evidence_ref="evidence://owner-gap/atomic",
            turn_binding="turn://owner-gap/1",
        ),
    }

    emitted_batch = {
        "case_id": "root_cause_emitted_batch",
        "description": "Protocol root-cause explanation promotion emits batch receipt.",
        "trigger_classes": ["protocol_root_cause_explanation_started"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["protocol_root_cause_explanation_started"],
            decision="emit_now",
            emission_target="batch",
            evidence_refs=["evidence://root-cause/decision", "evidence://root-cause/batch"],
        ),
        "protocol_feedback_batch_receipt": make_batch_receipt(
            outbox_ref="outbox://root-cause/batch",
            evidence_ref="evidence://root-cause/batch",
            turn_binding="turn://root-cause/1",
        ),
    }

    blocked = {
        "case_id": "recurrent_drift_blocked",
        "description": "Recurrent protocol drift is promoted but canonical emission is blocked and produces blocker receipt.",
        "trigger_classes": ["recurrent_protocol_drift_detected"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["recurrent_protocol_drift_detected"],
            decision="blocked",
            emission_target="blocked",
            blocker_id="protocol_feedback_emit_path_blocked",
            blocker_reason="canonical protocol channel unavailable",
            evidence_refs=["evidence://drift/decision", "evidence://drift/blocker"],
        ),
        "promotion_blocker_receipt": make_blocker_receipt(
            blocker_id="protocol_feedback_emit_path_blocked",
            blocker_reason="canonical protocol channel unavailable",
            missing_contract_surface="protocol_feedback_channel",
            evidence_ref="evidence://drift/blocker",
        ),
    }

    missing_decision = {
        "case_id": "trigger_missing_decision_receipt",
        "description": "Trigger matched but the turn stayed ordinary-answer-only with zero artifact.",
        "trigger_classes": ["user_explicit_protocol_review_request"],
    }

    missing_emit_receipt = {
        "case_id": "emit_now_missing_emit_receipt",
        "description": "Decision emits now but no atomic or batch receipt exists.",
        "trigger_classes": ["assistant_identified_protocol_owner_gap"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["assistant_identified_protocol_owner_gap"],
            decision="emit_now",
            emission_target="atomic",
            evidence_refs=["evidence://owner-gap/decision"],
        ),
    }

    missing_blocker = {
        "case_id": "blocked_missing_blocker_receipt",
        "description": "Decision blocked but no blocker receipt exists.",
        "trigger_classes": ["recurrent_protocol_drift_detected"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["recurrent_protocol_drift_detected"],
            decision="blocked",
            emission_target="blocked",
            blocker_id="protocol_feedback_emit_path_blocked",
            blocker_reason="canonical protocol channel unavailable",
            evidence_refs=["evidence://drift/decision"],
        ),
    }

    missing_inquiry = {
        "case_id": "pending_missing_inquiry_requiredization",
        "description": "Pending promotion without inquiry requiredization trigger.",
        "trigger_classes": ["protocol_root_cause_explanation_started"],
        "promotion_decision_receipt": make_decision_receipt(
            trigger_classes=["protocol_root_cause_explanation_started"],
            decision="pending_requiredization",
            emission_target="pending",
            evidence_refs=["evidence://root-cause/decision"],
        ),
    }

    cases = {
        ordinary["case_id"]: ordinary,
        pending["case_id"]: pending,
        emitted_atomic["case_id"]: emitted_atomic,
        emitted_batch["case_id"]: emitted_batch,
        blocked["case_id"]: blocked,
        missing_decision["case_id"]: missing_decision,
        missing_emit_receipt["case_id"]: missing_emit_receipt,
        missing_blocker["case_id"]: missing_blocker,
        missing_inquiry["case_id"]: missing_inquiry,
    }
    return deepcopy(cases)


def fixture_case(case_id: str) -> dict[str, Any]:
    cases = fixture_cases()
    if case_id not in cases:
        raise KeyError(case_id)
    return deepcopy(cases[case_id])


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    stale_reasons: list[str] = []

    case_id = str(case.get("case_id", "ad_hoc_case")).strip() or "ad_hoc_case"
    trigger_classes = _dedupe(case.get("trigger_classes", []))
    matched_trigger_classes = [item for item in trigger_classes if item in ADMITTED_TRIGGER_CLASSES]
    unknown_trigger_classes = [item for item in trigger_classes if item not in ADMITTED_TRIGGER_CLASSES]
    if unknown_trigger_classes:
        errors.append("unknown_trigger_class_present:" + ",".join(unknown_trigger_classes))
        stale_reasons.append("unknown_trigger_class_present")

    computed_promotion_expected = bool(matched_trigger_classes)
    declared_promotion_expected = case.get("promotion_expected")
    if declared_promotion_expected is None:
        promotion_expected = computed_promotion_expected
    else:
        promotion_expected = bool(declared_promotion_expected)
        if promotion_expected != computed_promotion_expected:
            errors.append("promotion_expected_trigger_mismatch")
            stale_reasons.append("promotion_expected_trigger_mismatch")

    inquiry = case.get("inquiry_requiredization_trigger")
    decision = case.get("promotion_decision_receipt")
    atomic = case.get("protocol_feedback_atomic_receipt")
    batch = case.get("protocol_feedback_batch_receipt")
    blocker = case.get("promotion_blocker_receipt")

    artifact_types_present = [
        name
        for name, payload in (
            ("inquiry_requiredization_trigger", inquiry),
            ("promotion_decision_receipt", decision),
            ("protocol_feedback_atomic_receipt", atomic),
            ("protocol_feedback_batch_receipt", batch),
            ("promotion_blocker_receipt", blocker),
        )
        if isinstance(payload, dict) and payload
    ]

    decision_value = ""
    if decision is not None and not isinstance(decision, dict):
        errors.append("promotion_decision_receipt_not_object")
        stale_reasons.append("promotion_decision_receipt_not_object")
    if isinstance(decision, dict):
        decision_value = str(decision.get("decision", "")).strip()
        missing = _missing_fields(
            decision,
            REQUIRED_DECISION_FIELDS + DECISION_CONDITIONAL_REQUIRED_FIELDS.get(decision_value, ()),
        )
        if missing:
            errors.append("promotion_decision_receipt_missing_fields:" + ",".join(missing))
            stale_reasons.append("promotion_decision_receipt_missing_fields")
        if decision_value not in ALLOWED_DECISIONS:
            errors.append("invalid_promotion_decision")
            stale_reasons.append("invalid_promotion_decision")
        decision_promotion_expected = decision.get("promotion_expected")
        if decision_promotion_expected is None or bool(decision_promotion_expected) != promotion_expected:
            errors.append("promotion_decision_receipt_promotion_expected_mismatch")
            stale_reasons.append("promotion_decision_receipt_promotion_expected_mismatch")
        decision_triggers = _dedupe(decision.get("exact_trigger_classes", []))
        if set(decision_triggers) != set(matched_trigger_classes):
            errors.append("promotion_decision_receipt_trigger_set_mismatch")
            stale_reasons.append("promotion_decision_receipt_trigger_set_mismatch")

    if isinstance(inquiry, dict):
        missing = _missing_fields(inquiry, REQUIRED_INQUIRY_FIELDS)
        if missing:
            errors.append("inquiry_requiredization_trigger_missing_fields:" + ",".join(missing))
            stale_reasons.append("inquiry_requiredization_trigger_missing_fields")
        inquiry_trigger_class = str(inquiry.get("trigger_class", "")).strip()
        if promotion_expected and inquiry_trigger_class not in matched_trigger_classes:
            errors.append("inquiry_requiredization_trigger_class_mismatch")
            stale_reasons.append("inquiry_requiredization_trigger_class_mismatch")
    elif inquiry is not None:
        errors.append("inquiry_requiredization_trigger_not_object")
        stale_reasons.append("inquiry_requiredization_trigger_not_object")

    if isinstance(atomic, dict):
        missing = _missing_fields(atomic, REQUIRED_EMIT_RECEIPT_FIELDS)
        if missing:
            errors.append("protocol_feedback_atomic_receipt_missing_fields:" + ",".join(missing))
            stale_reasons.append("protocol_feedback_atomic_receipt_missing_fields")
    elif atomic is not None:
        errors.append("protocol_feedback_atomic_receipt_not_object")
        stale_reasons.append("protocol_feedback_atomic_receipt_not_object")

    if isinstance(batch, dict):
        missing = _missing_fields(batch, REQUIRED_EMIT_RECEIPT_FIELDS)
        if missing:
            errors.append("protocol_feedback_batch_receipt_missing_fields:" + ",".join(missing))
            stale_reasons.append("protocol_feedback_batch_receipt_missing_fields")
    elif batch is not None:
        errors.append("protocol_feedback_batch_receipt_not_object")
        stale_reasons.append("protocol_feedback_batch_receipt_not_object")

    if isinstance(blocker, dict):
        missing = _missing_fields(blocker, REQUIRED_BLOCKER_FIELDS)
        if missing:
            errors.append("promotion_blocker_receipt_missing_fields:" + ",".join(missing))
            stale_reasons.append("promotion_blocker_receipt_missing_fields")
    elif blocker is not None:
        errors.append("promotion_blocker_receipt_not_object")
        stale_reasons.append("promotion_blocker_receipt_not_object")

    if promotion_expected:
        if not artifact_types_present:
            errors.append("matched_trigger_without_artifact")
            stale_reasons.append("matched_trigger_without_artifact")
        if not isinstance(decision, dict):
            errors.append("promotion_expected_but_decision_receipt_absent")
            stale_reasons.append("promotion_expected_but_decision_receipt_absent")
        elif decision_value == "emit_now":
            if not isinstance(atomic, dict) and not isinstance(batch, dict):
                errors.append("emit_now_without_emit_receipt")
                stale_reasons.append("emit_now_without_emit_receipt")
            emission_target = str(decision.get("emission_target", "")).strip()
            if emission_target == "atomic" and not isinstance(atomic, dict):
                errors.append("emit_now_target_atomic_missing_receipt")
                stale_reasons.append("emit_now_without_emit_receipt")
            if emission_target == "batch" and not isinstance(batch, dict):
                errors.append("emit_now_target_batch_missing_receipt")
                stale_reasons.append("emit_now_without_emit_receipt")
        elif decision_value == "blocked":
            if not isinstance(blocker, dict):
                errors.append("blocked_without_blocker_receipt")
                stale_reasons.append("blocked_without_blocker_receipt")
        elif decision_value == "pending_requiredization":
            if not isinstance(inquiry, dict):
                errors.append("pending_without_inquiry_requiredization")
                stale_reasons.append("pending_without_inquiry_requiredization")
        elif decision_value == "not_required":
            errors.append("trigger_matched_but_decision_not_required")
            stale_reasons.append("trigger_matched_but_decision_not_required")

    if not promotion_expected and isinstance(decision, dict) and decision_value and decision_value != "not_required":
        errors.append("ordinary_discussion_unexpected_promotion_decision")
        stale_reasons.append("ordinary_discussion_unexpected_promotion_decision")

    if not promotion_expected:
        machine_state = "not_required"
    elif decision_value == "pending_requiredization":
        machine_state = "pending"
    elif decision_value == "emit_now":
        machine_state = "emitted" if isinstance(atomic, dict) or isinstance(batch, dict) else "promotion_expected"
    elif decision_value == "blocked":
        machine_state = "blocked" if isinstance(blocker, dict) else "promotion_expected"
    else:
        machine_state = "promotion_expected"

    deduped_reasons = _dedupe(stale_reasons)
    return {
        "status": STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED,
        "stream_id": STREAM_ID,
        "lane_id": LANE_ID,
        "issue_candidate_id": ISSUE_CANDIDATE_ID,
        "blocker_id": BLOCKER_ID,
        "governing_law": GOVERNING_LAW,
        "case_id": case_id,
        "description": str(case.get("description", "")).strip(),
        "admitted_trigger_classes": list(ADMITTED_TRIGGER_CLASSES),
        "matched_trigger_classes": matched_trigger_classes,
        "unknown_trigger_classes": unknown_trigger_classes,
        "promotion_expected": promotion_expected,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "allowed_machine_outputs": list(ALLOWED_MACHINE_OUTPUTS),
        "machine_states": list(MACHINE_STATES),
        "machine_state": machine_state,
        "artifact_types_present": artifact_types_present,
        "fixed_write_set": list(FIXED_WRITE_SET),
        "validation_bundle": list(VALIDATION_BUNDLE),
        "negative_reason_hints": NEGATIVE_REASON_HINTS,
        "errors": errors,
        "stale_reasons": deduped_reasons,
    }
