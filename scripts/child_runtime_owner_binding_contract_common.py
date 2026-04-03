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

REQUIRED_OWNER_BINDING_FIELDS = (
    "child_runtime_owner_binding_status",
    "child_runtime_owner",
    "child_runtime_root_scope",
    "child_runtime_root_kinds",
    "live_runtime_exclusion_status",
)

EXPECTED_CONTRACT = {
    "lane_id": "issue_041b_child_runtime_owner_binding_admission_contract_v1",
    "governing_law": "unowned_child_tmp_probe_runtime_not_admitted",
    "fixed_write_set": [
        "docs/governance/identity-child-runtime-owner-binding-governance-v1.6.x.md",
        "docs/review/protocol-remediation-audit-ledger-v1.6.x-child-runtime-owner-binding.md",
        "scripts/child_runtime_owner_binding_contract_common.py",
        "scripts/validate_child_runtime_owner_binding_contract.py",
        "scripts/ci/run_child_runtime_owner_binding_probes_ci.sh",
    ],
    "layer_state": "protocol-base-repo",
    "next_exact_action": [
        "formalize child tmp/probe/runtime owner binding admission only",
        "fail-close child tmp/probe/runtime roots with no admitted owner binding",
        "keep live-runtime exclusion machine-visible where required by the contract",
    ],
    "validation_bundle": [
        "TMPDIR=$PWD/.tmp python3 scripts/validate_child_runtime_owner_binding_contract.py --json-only",
        "TMPDIR=$PWD/.tmp bash scripts/ci/run_child_runtime_owner_binding_probes_ci.sh",
    ],
    "reopen_triggers": [
        "validator/probe fail",
        "same-file same-line conflict",
        "fixed_write_set insufficiency only",
    ],
    "commit_gate": "one isolated commit for ISSUE-041B only",
}

REQUIRED_SEMANTIC_PHRASES = (
    "Child tmp, probe, and runtime roots require admitted owner binding before admission.",
    "Unowned child tmp, probe, and runtime roots are not admitted.",
    "Child runtime owner binding status, owner, root scope, root kinds, and live runtime exclusion status are required admission fields.",
    "Admission must fail-close whenever child owner binding is missing.",
    "Live runtime exclusion must remain machine-visible wherever child residue admission is evaluated.",
)

DOC_REL_PATHS = {
    "governance": "docs/governance/identity-child-runtime-owner-binding-governance-v1.6.x.md",
    "review": "docs/review/protocol-remediation-audit-ledger-v1.6.x-child-runtime-owner-binding.md",
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
    for field_name in REQUIRED_OWNER_BINDING_FIELDS:
        if field_name not in text:
            errors.append(f"{label}:missing_owner_binding_field:{field_name}")
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
        "required_owner_binding_fields": list(REQUIRED_OWNER_BINDING_FIELDS),
        "errors": errors,
    }


def render_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False, sort_keys=False)
