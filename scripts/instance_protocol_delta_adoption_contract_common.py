#!/usr/bin/env python3
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

REQUIRED_ADOPTION_FIELDS = (
    "protocol_current_head",
    "last_seen_protocol_commit",
    "last_adopted_protocol_commit",
    "relevant_unadopted_commit_count",
    "relevant_unadopted_commits",
    "protocol_delta_adoption_status",
    "protocol_delta_adoption_mode",
    "capability_families",
    "protocol_root",
    "state_path",
    "stale_reasons",
)

REQUIRED_ADOPTION_STATUSES = (
    STATUS_PASS_REQUIRED,
    STATUS_FAIL_REQUIRED,
)

REQUIRED_ADOPTION_MODES = (
    "continuous_protocol_delta_adoption_ready",
    "relevant_protocol_delta_pending_adoption",
    "protocol_owner_surface_not_ready",
    "instance_local_adoption_markers_missing",
    "protocol_authority_resolution_failed",
)

EXPECTED_CONTRACT = {
    "lane_id": "instance_protocol_delta_adoption_contract_v1",
    "governing_law": "relevant_protocol_delta_adoption_requires_protocol_and_local_readiness",
    "fixed_write_set": [
        "docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md",
        "docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md",
        "scripts/instance_protocol_delta_adoption_contract_common.py",
        "scripts/validate_instance_protocol_delta_adoption.py",
        "scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh",
    ],
    "layer_state": "protocol-instance-bridge",
    "next_exact_action": [
        "formalize instance protocol delta adoption only",
        "freeze authoritative protocol head, last seen head, and last adopted head as separate machine-visible states",
        "fail-close relevant protocol deltas when protocol owner surfaces or instance-local adoption markers are not ready",
    ],
    "validation_bundle": [
        "TMPDIR=$PWD/.tmp python3 scripts/validate_instance_protocol_delta_adoption.py --json-only",
        "TMPDIR=$PWD/.tmp bash scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh",
    ],
    "reopen_triggers": [
        "validator/probe fail",
        "same-file same-line conflict",
        "fixed_write_set insufficiency only",
    ],
    "commit_gate": "one isolated commit for instance_protocol_delta_adoption_contract_v1 only",
}

REQUIRED_SEMANTIC_PHRASES = (
    "Instance protocol delta adoption must be machine-visible, writable, and reviewable.",
    "Protocol authority must resolve to a single authoritative protocol root before adoption can pass.",
    "Current protocol head, last seen protocol commit, and last adopted protocol commit must remain distinct.",
    "Only relevant capability families are scanned for delta adoption.",
    "Relevant protocol deltas must fail-close when authoritative protocol owner surfaces are not ready.",
    "Relevant protocol deltas must fail-close when instance-local adoption markers are missing.",
    "protocol_delta_adoption and instance_script_protocol_adoption must remain distinct.",
)

DOC_REL_PATHS = {
    "governance": "docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md",
    "review": "docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md",
}


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_repo_root(repo_root: str | Path | None = None) -> Path:
    return Path(repo_root).resolve() if repo_root else default_repo_root()


def document_paths(repo_root: str | Path | None = None) -> dict[str, Path]:
    root = resolve_repo_root(repo_root)
    return {name: root / relpath for name, relpath in DOC_REL_PATHS.items()}


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
    for field_name in REQUIRED_ADOPTION_FIELDS:
        if not re.search(rf"\b{re.escape(field_name)}\b", text):
            errors.append(f"{label}:missing_adoption_field:{field_name}")
    for status in REQUIRED_ADOPTION_STATUSES:
        if not re.search(rf"\b{re.escape(status)}\b", text):
            errors.append(f"{label}:missing_adoption_status:{status}")
    for mode in REQUIRED_ADOPTION_MODES:
        if not re.search(rf"\b{re.escape(mode)}\b", text):
            errors.append(f"{label}:missing_adoption_mode:{mode}")
    try:
        payload = extract_contract_payload(text)
    except Exception as exc:  # pragma: no cover - exercised by probe cases
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
        "lane_id": EXPECTED_CONTRACT["lane_id"],
        "governing_law": EXPECTED_CONTRACT["governing_law"],
        "repo_root": str(root),
        "documents": docs_meta,
        "required_fields": list(REQUIRED_FIELDS),
        "required_adoption_fields": list(REQUIRED_ADOPTION_FIELDS),
        "required_adoption_statuses": list(REQUIRED_ADOPTION_STATUSES),
        "required_adoption_modes": list(REQUIRED_ADOPTION_MODES),
        "errors": errors,
    }


def render_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False, sort_keys=False)
