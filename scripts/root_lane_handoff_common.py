#!/usr/bin/env python3
"""Shared primitives for root_lane_handoff artifact reconciliation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

EXPECTED_GOVERNING_LAW = (
    "canonical_lane_card_handoff_family_must_not_compete_with_parallel_root_handoff_artifacts"
)
EXPECTED_ARTIFACT_CLASSIFICATION = "compatibility"
EXPECTED_CANONICAL_CONTRACT_TYPE = "lane_card_handoff_contract_v1"
EXPECTED_CANONICAL_GOVERNANCE_DOC = (
    "docs/governance/identity-lane-card-handoff-governance-v1.6.x.md"
)
EXPECTED_CANONICAL_REVIEW_DOC = (
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-card-handoff.md"
)
EXPECTED_ACCEPTED_ISSUE_COMMIT = "c09a3a6"
EXPECTED_ACTIVE_FILE = "identity/protocol/mappings/root-lane-handoff.v1.yaml"
EXPECTED_CLASSIFICATION_OPTIONS = (
    "canonical",
    "derived",
    "compatibility",
    "residual",
)

EXPECTED_CURRENT_PAYLOAD = {
    "active_file": EXPECTED_ACTIVE_FILE,
}

REQUIRED_CONTRACT_PAYLOAD = {
    "artifact_family": "root_lane_handoff",
    "artifact_classification": EXPECTED_ARTIFACT_CLASSIFICATION,
    "canonical_contract_type": EXPECTED_CANONICAL_CONTRACT_TYPE,
    "canonical_governance_doc": EXPECTED_CANONICAL_GOVERNANCE_DOC,
    "canonical_review_doc": EXPECTED_CANONICAL_REVIEW_DOC,
    "governing_law": EXPECTED_GOVERNING_LAW,
    "non_competition_rule": "competing canonical handoff semantics fail-close",
    "accepted_issue_commit": EXPECTED_ACCEPTED_ISSUE_COMMIT,
}

REQUIRED_CONTRACT_PHRASES = (
    "This file records the pre-existing `root-lane-handoff` artifact family as a",
    "The canonical handoff law remains the accepted `ISSUE-040A`",
    "Parallel root-lane-handoff artifacts must not compete with that canonical",
    "Chat remains navigation-only, not durable handoff state.",
    "No card, no handoff.",
    "No card, no takeover.",
    "This file is compatibility-only.",
    "It must not originate or claim an alternate canonical handoff law.",
    "Validators must fail-close if this artifact family claims canonical handoff authority.",
)

FORBIDDEN_CONTRACT_PHRASES = (
    "This file remains the authoritative root-domain contract for governed lane-handoff law.",
    "authoritative root-domain contract for governed lane-handoff law",
)

REQUIRED_MAPPING_PAYLOAD = {
    "schema_version": 1,
    "artifact_family": "root_lane_handoff",
    "artifact_classification": EXPECTED_ARTIFACT_CLASSIFICATION,
    "governing_law": EXPECTED_GOVERNING_LAW,
    "canonical_contract_type": EXPECTED_CANONICAL_CONTRACT_TYPE,
    "canonical_governance_doc": EXPECTED_CANONICAL_GOVERNANCE_DOC,
    "canonical_review_doc": EXPECTED_CANONICAL_REVIEW_DOC,
    "contract_file": "identity/protocol/LANE_HANDOFF_CONTRACT.md",
    "current_file": "identity/protocol/mappings/root-lane-handoff.current.yaml",
    "validator_script": "scripts/validate_protocol_root_lane_handoff.py",
    "probe_script": "scripts/ci/run_protocol_root_lane_handoff_probes_ci.sh",
    "common_script": "scripts/root_lane_handoff_common.py",
    "accepted_issue_commit": EXPECTED_ACCEPTED_ISSUE_COMMIT,
}

CONTRACT_START_MARKER = "<!-- root-lane-handoff-contract:start -->"
CONTRACT_END_MARKER = "<!-- root-lane-handoff-contract:end -->"

DEFAULT_CONTRACT_DOC_RELATIVE = "identity/protocol/LANE_HANDOFF_CONTRACT.md"
DEFAULT_CURRENT_MAPPING_RELATIVE = "identity/protocol/mappings/root-lane-handoff.current.yaml"
DEFAULT_VERSIONED_MAPPING_RELATIVE = "identity/protocol/mappings/root-lane-handoff.v1.yaml"


CONTRACT_BLOCK_RE = re.compile(
    rf"{re.escape(CONTRACT_START_MARKER)}\s*```json\s*(.*?)\s*```\s*{re.escape(CONTRACT_END_MARKER)}",
    re.DOTALL,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent



def default_paths() -> tuple[Path, Path, Path]:
    root = repo_root()
    return (
        root / DEFAULT_CONTRACT_DOC_RELATIVE,
        root / DEFAULT_CURRENT_MAPPING_RELATIVE,
        root / DEFAULT_VERSIONED_MAPPING_RELATIVE,
    )



def load_json_like_yaml(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def extract_contract_payload(markdown: str) -> dict[str, Any]:
    match = CONTRACT_BLOCK_RE.search(markdown)
    if not match:
        raise ValueError("missing root-lane-handoff contract payload block")
    return json.loads(match.group(1))



def validate_dict(expected: dict[str, Any], actual: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for key, value in expected.items():
        if actual.get(key) != value:
            errors.append(f"{label}: expected {key}={value!r}, found {actual.get(key)!r}")
    return errors



def validate_contract_phrases(markdown: str) -> list[str]:
    errors: list[str] = []
    for phrase in REQUIRED_CONTRACT_PHRASES:
        if phrase not in markdown:
            errors.append(f"missing required contract phrase: {phrase}")
    for phrase in FORBIDDEN_CONTRACT_PHRASES:
        if phrase in markdown:
            errors.append(f"forbidden competing contract phrase present: {phrase}")
    return errors
