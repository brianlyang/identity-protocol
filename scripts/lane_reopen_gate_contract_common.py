#!/usr/bin/env python3
"""Shared primitives for ISSUE-040C lane reopen gate contract validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

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

EXPECTED_LANE_ID = "issue_040c_lane_reopen_gate_contract_v1"
EXPECTED_GOVERNING_LAW = (
    "reopen_must_be_machine_triggered__no_freeform_reinterpretation_after_handoff"
)
EXPECTED_FIXED_WRITE_SET = [
    "docs/governance/identity-lane-reopen-gate-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-reopen-gate.md",
    "scripts/lane_reopen_gate_contract_common.py",
    "scripts/validate_lane_reopen_gate_contract.py",
    "scripts/ci/run_lane_reopen_gate_probes_ci.sh",
]
EXPECTED_LAYER_STATE = "protocol-base-repo"
EXPECTED_NEXT_EXACT_ACTION = [
    "formalize lane_reopen_gate_contract_v1 only",
    "freeze reopen triggers as machine-admitted conditions only",
    "fail-close freeform takeover / freeform reinterpretation / broad reopen without admitted trigger",
]
EXPECTED_VALIDATION_BUNDLE = [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_lane_reopen_gate_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_lane_reopen_gate_probes_ci.sh",
]
EXPECTED_REOPEN_TRIGGERS = [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only",
]
EXPECTED_COMMIT_GATE = "one isolated commit for ISSUE-040C only"

EXPECTED_CONTRACT = {
    "lane_id": EXPECTED_LANE_ID,
    "governing_law": EXPECTED_GOVERNING_LAW,
    "fixed_write_set": EXPECTED_FIXED_WRITE_SET,
    "layer_state": EXPECTED_LAYER_STATE,
    "next_exact_action": EXPECTED_NEXT_EXACT_ACTION,
    "validation_bundle": EXPECTED_VALIDATION_BUNDLE,
    "reopen_triggers": EXPECTED_REOPEN_TRIGGERS,
    "commit_gate": EXPECTED_COMMIT_GATE,
}

CONTRACT_START_MARKER = "<!-- lane-reopen-gate-contract:start -->"
CONTRACT_END_MARKER = "<!-- lane-reopen-gate-contract:end -->"

REQUIRED_SEMANTIC_PHRASES = (
    "Reopen must be machine-triggered after handoff.",
    "Freeform reinterpretation cannot reopen a closed lane.",
    "Freeform takeover cannot replace admitted reopen triggers.",
    "Broad reopen without admitted trigger is fail-close.",
    "Only the closed trigger set frozen in the lane reopen gate contract may reopen the lane.",
)

DEFAULT_GOVERNANCE_DOC_RELATIVE = (
    "docs/governance/identity-lane-reopen-gate-governance-v1.6.x.md"
)
DEFAULT_REVIEW_DOC_RELATIVE = (
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-reopen-gate.md"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_doc_paths() -> tuple[Path, Path]:
    root = repo_root()
    return (
        root / DEFAULT_GOVERNANCE_DOC_RELATIVE,
        root / DEFAULT_REVIEW_DOC_RELATIVE,
    )


def extract_contract_payload(markdown: str) -> dict[str, Any]:
    pattern = re.compile(
        re.escape(CONTRACT_START_MARKER)
        + r"\s*```json\s*(\{.*?\})\s*```\s*"
        + re.escape(CONTRACT_END_MARKER),
        re.DOTALL,
    )
    match = pattern.search(markdown)
    if not match:
        raise ValueError("lane reopen gate contract block is missing")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"lane reopen gate contract block is not valid JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("lane reopen gate contract payload must be a JSON object")
    return payload


def replace_contract_payload(markdown: str, payload: dict[str, Any]) -> str:
    pattern = re.compile(
        re.escape(CONTRACT_START_MARKER)
        + r"\s*```json\s*\{.*?\}\s*```\s*"
        + re.escape(CONTRACT_END_MARKER),
        re.DOTALL,
    )
    replacement = (
        f"{CONTRACT_START_MARKER}\n"
        "```json\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
        "```\n"
        f"{CONTRACT_END_MARKER}"
    )
    if not pattern.search(markdown):
        raise ValueError("cannot replace missing lane reopen gate contract block")
    return pattern.sub(replacement, markdown, count=1)


def validate_required_fields(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    payload_keys = set(payload.keys())
    required_keys = set(REQUIRED_FIELDS)
    missing = sorted(required_keys - payload_keys)
    extra = sorted(payload_keys - required_keys)
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected fields present: {', '.join(extra)}")
    return errors


def validate_expected_contract(payload: dict[str, Any]) -> list[str]:
    errors = validate_required_fields(payload)
    if payload.get("lane_id") != EXPECTED_LANE_ID:
        errors.append("lane_id does not match canonical ISSUE-040C value")
    if payload.get("governing_law") != EXPECTED_GOVERNING_LAW:
        errors.append("governing_law does not match canonical ISSUE-040C value")
    if payload.get("fixed_write_set") != EXPECTED_FIXED_WRITE_SET:
        errors.append("fixed_write_set does not match canonical ISSUE-040C write set")
    if payload.get("layer_state") != EXPECTED_LAYER_STATE:
        errors.append("layer_state does not match protocol-base-repo")
    if payload.get("next_exact_action") != EXPECTED_NEXT_EXACT_ACTION:
        errors.append("next_exact_action does not match canonical ISSUE-040C action bundle")
    if payload.get("validation_bundle") != EXPECTED_VALIDATION_BUNDLE:
        errors.append("validation_bundle does not match canonical ISSUE-040C validation bundle")
    if payload.get("reopen_triggers") != EXPECTED_REOPEN_TRIGGERS:
        errors.append("reopen_triggers does not match the closed ISSUE-040C trigger set")
    if payload.get("commit_gate") != EXPECTED_COMMIT_GATE:
        errors.append("commit_gate does not match the isolated ISSUE-040C commit gate")
    return errors


def validate_semantic_phrases(markdown: str) -> list[str]:
    missing = [phrase for phrase in REQUIRED_SEMANTIC_PHRASES if phrase not in markdown]
    if not missing:
        return []
    return [f"missing semantic phrase: {phrase}" for phrase in missing]
