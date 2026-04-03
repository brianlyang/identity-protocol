#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from single_owner_two_phase_execution_governance_contract_common import (
    CANONICAL_TRUE_RE,
    DOC_EXPECTATIONS,
    FAIL_CLOSE_REASON,
    FAIL_CLOSE_REASON_FAMILY,
    FAIL_REQUIRED,
    FIXED_WRITE_SET,
    ISSUE_ID,
    CONTRACT_ID,
    READ_ONLY_INPUT_EXPECTATIONS,
    READ_ONLY_INPUT_SURFACES,
    REQUIRED_MACHINE_FIELDS,
    PASS_REQUIRED,
    ROLE_FIELD_IDENTITY_RE,
    ROLE_FIELD_NAMES,
    SCRIPT_EXPECTATIONS,
    canonical_payload,
    default_machine_state,
    extract_json_payload,
    repo_root,
)


GOVERNANCE_DOC = FIXED_WRITE_SET[0]
REVIEW_DOC = FIXED_WRITE_SET[1]


def _missing_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [token for token in tokens if token not in text]


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        token = str(item or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _validate_doc_payload(label: str, text: str, expected: dict[str, Any]) -> list[str]:
    stale_reasons: list[str] = []
    try:
        payload = extract_json_payload(text)
    except Exception as exc:
        return [f"{label}_contract_extract_error:{exc}"]

    if payload != expected:
        stale_reasons.append(f"{label}_contract_payload_drift")

    if payload.get("truth_class") != "protocol_feedback_packet":
        stale_reasons.append("execution_governance_scope_reopen_not_admitted")
    if payload.get("canonical") is not False:
        stale_reasons.append("feedback_packet_must_not_be_canonical")
    if payload.get("portable") is not True:
        stale_reasons.append("execution_governance_scope_reopen_not_admitted")
    if payload.get("runtime_binding_not_authoritative") is not True:
        stale_reasons.append("execution_governance_scope_reopen_not_admitted")
    if payload.get("canonical_truth_invariant") != expected.get("canonical_truth_invariant"):
        stale_reasons.append("runtime_evidence_reentry_into_canonical_truth")
    for field in ROLE_FIELD_NAMES:
        value = str(payload.get(field, "")).strip()
        if ROLE_FIELD_IDENTITY_RE.match(value):
            stale_reasons.append("role_identity_field_pollution")
    if payload.get("lane_execution_model") != "single_owner_two_phase":
        stale_reasons.append("execution_governance_scope_reopen_not_admitted")
    phase_b = payload.get("phase_b") or {}
    if phase_b.get("precondition_receipt") != "execution_governance_contract_freeze_receipt":
        stale_reasons.append("phase_b_requires_phase_a_receipt")
    handoff = payload.get("handoff_policy") or {}
    if handoff.get("default_mode") != "single_owner_no_handoff":
        stale_reasons.append("second_owner_without_handoff_receipt_not_admitted")
    if handoff.get("exception_mode") != "explicit_blocker_or_handoff_receipt_only":
        stale_reasons.append("second_owner_without_handoff_receipt_not_admitted")
    if payload.get("fixed_write_set") != list(FIXED_WRITE_SET):
        stale_reasons.append("exact_write_set_lock_not_machine_visible")
    if payload.get("read_only_input_surfaces") != list(READ_ONLY_INPUT_SURFACES):
        stale_reasons.append("execution_governance_scope_reopen_not_admitted")
    return stale_reasons


def validate(root: Path) -> dict[str, object]:
    stale_reasons: list[str] = []

    for rel in FIXED_WRITE_SET:
        path = root / rel
        if not path.exists():
            stale_reasons.append(f"missing_fixed_write_path:{rel}")

    for rel in READ_ONLY_INPUT_SURFACES:
        path = root / rel
        if not path.exists():
            stale_reasons.append(f"missing_read_only_input:{rel}")

    for rel, tokens in DOC_EXPECTATIONS.items():
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                stale_reasons.append(f"missing_token:{rel}:{token}")
        if rel in (GOVERNANCE_DOC, REVIEW_DOC) and CANONICAL_TRUE_RE.search(text):
            stale_reasons.append("feedback_packet_must_not_be_canonical")

    for rel, tokens in READ_ONLY_INPUT_EXPECTATIONS.items():
        path = root / rel
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            stale_reasons.append(f"missing_read_only_token:{rel}:{token}")

    for rel, tokens in SCRIPT_EXPECTATIONS.items():
        path = root / rel
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            stale_reasons.append(f"missing_script_token:{rel}:{token}")

    expected_payload = canonical_payload()
    governance_payload = None
    review_payload = None
    governance_path = root / GOVERNANCE_DOC
    review_path = root / REVIEW_DOC

    if governance_path.exists():
        governance_text = governance_path.read_text(encoding="utf-8")
        doc_errors = _validate_doc_payload("governance", governance_text, expected_payload)
        stale_reasons.extend(doc_errors)
        try:
            governance_payload = extract_json_payload(governance_text)
        except Exception:
            governance_payload = None
    if review_path.exists():
        review_text = review_path.read_text(encoding="utf-8")
        doc_errors = _validate_doc_payload("review", review_text, expected_payload)
        stale_reasons.extend(doc_errors)
        try:
            review_payload = extract_json_payload(review_text)
        except Exception:
            review_payload = None
    if governance_payload is not None and review_payload is not None and governance_payload != review_payload:
        stale_reasons.append("governance_review_contract_mismatch")

    machine_state = default_machine_state()
    for field in REQUIRED_MACHINE_FIELDS:
        if field not in machine_state:
            stale_reasons.append(f"missing_machine_field:{field}")
    if machine_state.get("phase_a_completion_receipt_status") != "REQUIRED_BEFORE_PHASE_B":
        stale_reasons.append("phase_b_requires_phase_a_receipt")
    if machine_state.get("phase_b_precondition_status") != "BLOCKED_UNTIL_FREEZE_RECEIPT":
        stale_reasons.append("phase_b_requires_phase_a_receipt")
    if machine_state.get("monotonic_progress_status") != "REQUIRED":
        stale_reasons.append("monotonic_progress_not_machine_visible")
    if machine_state.get("repeated_inspection_budget_status") != "BOUNDED":
        stale_reasons.append("repeat_budget_not_machine_visible")
    if machine_state.get("compaction_continuation_receipt_status") != "REQUIRED_AFTER_COMPACTION":
        stale_reasons.append("compaction_continuation_receipt_not_machine_visible")
    if machine_state.get("exact_write_set_lock_status") != "REQUIRED_IN_PHASE_B":
        stale_reasons.append("exact_write_set_lock_not_machine_visible")
    if machine_state.get("canonical_truth_projection_status") != "ROLE_LEVEL_PORTABLE_ONLY":
        stale_reasons.append("runtime_evidence_reentry_into_canonical_truth")
    if machine_state.get("runtime_evidence_reentry_status") != "FAIL_CLOSE_ON_REENTRY":
        stale_reasons.append("runtime_evidence_reentry_into_canonical_truth")
    handoff = machine_state.get("handoff_policy") or {}
    if handoff.get("default_mode") != "single_owner_no_handoff":
        stale_reasons.append("second_owner_without_handoff_receipt_not_admitted")
    if handoff.get("exception_mode") != "explicit_blocker_or_handoff_receipt_only":
        stale_reasons.append("second_owner_without_handoff_receipt_not_admitted")

    stale_reasons = _dedupe(stale_reasons)
    ok = not stale_reasons
    return {
        "ok": ok,
        "status": PASS_REQUIRED if ok else FAIL_REQUIRED,
        "issue": ISSUE_ID,
        "contract_id": CONTRACT_ID,
        "mode": "single_owner_two_phase_execution_governance_ready" if ok else FAIL_CLOSE_REASON,
        "checked_file_count": len(FIXED_WRITE_SET),
        "read_only_input_surface_count": len(READ_ONLY_INPUT_SURFACES),
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "fail_close_reason_family": list(FAIL_CLOSE_REASON_FAMILY),
        "stale_reasons": stale_reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    result = validate(repo_root(args.root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
