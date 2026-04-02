#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ISSUE_ID = "ISSUE-049"
LANE_ID = "protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_v1"
GOVERNING_LAW = "recognized_protocol_feedback_escalation_must_switch_rail_and_enter_canonical_emit_receipt_flow"
SAMPLE_EXPLICIT_REQUEST = "Explicit protocol feedback escalation required for this turn."

REQUIRED_FIELDS = (
    "lane_id",
    "governing_law",
    "fixed_write_set",
    "layer_state",
    "next_exact_action",
    "validation_bundle",
    "reopen_triggers",
    "commit_gate",
)

REQUIRED_MACHINE_VISIBLE_FIELDS = (
    "protocol_feedback_request_detected",
    "protocol_feedback_rule_known",
    "protocol_feedback_rail_selected",
    "protocol_feedback_emission_obligation_status",
    "protocol_feedback_channel_entered",
    "protocol_feedback_emit_invoked",
    "protocol_feedback_artifact_materialized",
    "protocol_feedback_rule_consumption_status",
    "stale_reasons",
)

FIXED_WRITE_SET = (
    "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py",
    "scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py",
    "scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh",
)

VALIDATION_BUNDLE = (
    "TMPDIR=$PWD/.tmp python3 scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh",
)

REOPEN_TRIGGERS = (
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only",
)

RUNTIME_STALE_REASON_FAMILY = (
    "documentation_contract_drift",
    "workbook_closure_drift",
    "explicit_request_not_detected",
    "protocol_feedback_rule_unknown",
    "protocol_feedback_rail_not_selected",
    "protocol_feedback_emission_obligation_unmet",
    "protocol_feedback_channel_not_entered",
    "protocol_feedback_emit_not_invoked",
    "protocol_feedback_artifact_not_materialized",
    "protocol_feedback_rule_not_consumed",
)

EXPECTED_CONTRACT = {
    "lane_id": "protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_v1",
    "governing_law": "recognized_protocol_feedback_escalation_must_switch_rail_and_enter_canonical_emit_receipt_flow",
    "fixed_write_set": [
        "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
        "docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md",
        "docs/workbook/protocol-issue-register-v1.6.md",
        "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
        "scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py",
        "scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py",
        "scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh"
    ],
    "layer_state": "protocol-base-repo",
    "next_exact_action": [
        "formalize explicit protocol-feedback escalation consumption only",
        "require recognized protocol-feedback escalation to select the protocol-feedback rail",
        "require canonical emission / receipt flow and the machine-visible ISSUE-049 state family"
    ],
    "validation_bundle": [
        "TMPDIR=$PWD/.tmp python3 scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py --json-only",
        "TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh"
    ],
    "reopen_triggers": [
        "validator/probe fail",
        "same-file same-line conflict",
        "fixed_write_set insufficiency only"
    ],
    "commit_gate": "one isolated commit for ISSUE-049 only after validator=PASS_REQUIRED and probe=PASS"
}

REQUIRED_SEMANTIC_PHRASES = (
    "Explicit protocol-feedback escalation must be consumed into machine action.",
    "Once `protocol_feedback_request_detected=true`, explanation-only handling is not admitted completion.",
    "Protocol feedback request detection, rule knowledge, rail selection, emission obligation status, channel entry, emit invocation, artifact materialization, rule consumption status, and stale reasons are required machine-visible fields.",
    "Recognized protocol-feedback escalation must switch to the protocol-feedback rail and enter canonical emission / receipt flow.",
    "The shared validator composes bootstrap readiness, atomic emit, and atomic emit validation into one executable proof lane.",
)

DOC_REL_PATHS = {
    "governance": "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
    "review": "docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md",
}

WORKBOOK_REL_PATHS = {
    "issue_register": "docs/workbook/protocol-issue-register-v1.6.md",
    "deep_audit_workbook": "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
}


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_repo_root(repo_root: str | Path | None = None) -> Path:
    return Path(repo_root).resolve() if repo_root else default_repo_root()


def document_paths(repo_root: str | Path | None = None) -> dict[str, Path]:
    root = resolve_repo_root(repo_root)
    return {name: root / relpath for name, relpath in DOC_REL_PATHS.items()}


def workbook_paths(repo_root: str | Path | None = None) -> dict[str, Path]:
    root = resolve_repo_root(repo_root)
    return {name: root / relpath for name, relpath in WORKBOOK_REL_PATHS.items()}


def extract_contract_payload(text: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError("missing_json_contract_block")
    return json.loads(match.group(1))


def validate_required_fields(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    extra = [field for field in payload if field not in REQUIRED_FIELDS]
    if missing:
        errors.append("missing_required_fields:" + ",".join(missing))
    if extra:
        errors.append("unexpected_contract_fields:" + ",".join(extra))
    return errors


def validate_contract_payload(payload: dict[str, Any]) -> list[str]:
    errors = validate_required_fields(payload)
    if payload != EXPECTED_CONTRACT:
        errors.append("contract_payload_drift")
    return errors


def validate_document_text(label: str, text: str) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    for phrase in REQUIRED_SEMANTIC_PHRASES:
        if phrase not in text:
            errors.append(f"{label}:missing_semantic_phrase:{phrase}")
    for field_name in REQUIRED_MACHINE_VISIBLE_FIELDS:
        if not re.search(rf"\b{re.escape(field_name)}\b", text):
            errors.append(f"{label}:missing_machine_visible_field:{field_name}")
    try:
        payload = extract_contract_payload(text)
    except Exception as exc:  # pragma: no cover
        errors.append(f"{label}:contract_extract_error:{exc}")
        return errors, None
    for payload_error in validate_contract_payload(payload):
        errors.append(f"{label}:{payload_error}")
    return errors, payload


def validate_contract_documents(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_repo_root(repo_root)
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    docs_meta: dict[str, dict[str, str]] = {}
    for label, path in document_paths(root).items():
        docs_meta[label] = {"path": str(path)}
        if not path.exists():
            errors.append(f"{label}:missing_document:{path}")
            continue
        text = path.read_text(encoding="utf-8")
        doc_errors, payload = validate_document_text(label, text)
        errors.extend(doc_errors)
        if payload is not None:
            payloads[label] = payload
    if {"governance", "review"}.issubset(payloads) and payloads["governance"] != payloads["review"]:
        errors.append("governance_review_contract_mismatch")
    return {
        "status": STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED,
        "issue_id": ISSUE_ID,
        "lane_id": LANE_ID,
        "governing_law": GOVERNING_LAW,
        "repo_root": str(root),
        "documents": docs_meta,
        "required_fields": list(REQUIRED_FIELDS),
        "required_machine_visible_fields": list(REQUIRED_MACHINE_VISIBLE_FIELDS),
        "errors": errors,
    }


def render_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False, sort_keys=False)
