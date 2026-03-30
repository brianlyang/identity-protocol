#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]

GOVERNANCE_PATH = REPO_ROOT / "docs/governance/identity-non-owner-machine-law-reinforcement-admission-governance-v1.6.x.md"
REVIEW_PATH = REPO_ROOT / "docs/review/protocol-remediation-audit-ledger-v1.6.x-non-owner-machine-law-reinforcement-admission.md"
WORKBOOK_PATH = REPO_ROOT / "docs/workbook/protocol-deep-audit-workbook-v1.6.md"
ISSUE_REGISTER_PATH = REPO_ROOT / "docs/workbook/protocol-issue-register-v1.6.md"

ISSUE_ID = "ISSUE-043"
CONTRACT_ID = "non_owner_machine_law_reinforcement_admission_contract_v1"
GOVERNING_LAW = "machine_law_reinforcement_may_be_admitted_from_root_middle_or_consumer_surfaces_without_redefining_accepted_root_law"
UNIQUE_DELTA = (
    "cross-layer whole-lane reinforcement completion may start from root, middle, or "
    "consumer layers and still complete the lane, but only through admitted "
    "reinforcement scope, preserved owner truth, and without redefining accepted root law."
)
FIXED_FIELDS = [
    "reinforcement_entry_surface",
    "reinforcement_authority_source",
    "accepted_root_law_ref",
    "reinforcement_scope_status",
    "whole_lane_completion_target",
    "whole_lane_completion_status",
    "non_owner_reinforcement_status",
    "cross_layer_completion_admission_status",
    "canonical_owner_truth_preservation_status",
    "root_semantic_redefinition_status",
    "stale_reasons",
]
ALLOWED_ENTRY_SURFACES = ["root", "middle", "consumer"]
FORBIDDEN_LEGACY_TOKENS = [
    "legacy_issue_043_forbidden_token_a",
    "legacy_issue_043_forbidden_token_b",
]
FORBIDDEN_SCOPE_TOKENS = [
    "legacy_issue_043_forbidden_token_a",
    "legacy_issue_043_forbidden_token_b",
]

CANONICAL_PAYLOAD: Dict[str, Any] = {
    "issue_id": ISSUE_ID,
    "contract_id": CONTRACT_ID,
    "governing_law": GOVERNING_LAW,
    "unique_delta_vs_issue_045": UNIQUE_DELTA,
    "reinforcement_fields": FIXED_FIELDS,
    "allowed_entry_surfaces": ALLOWED_ENTRY_SURFACES,
    "required_statuses": {
        "reinforcement_authority_source": "accepted_root_law_ref",
        "accepted_root_law_ref": "explicit_required",
        "reinforcement_scope_status": "bounded",
        "whole_lane_completion_target": "complete_whole_lane",
        "whole_lane_completion_status": "admitted",
        "non_owner_reinforcement_status": "admitted",
        "cross_layer_completion_admission_status": "admitted",
        "canonical_owner_truth_preservation_status": "preserved",
        "root_semantic_redefinition_status": "not_redefined",
    },
    "hard_boundaries": [
        "do_not_replace_issue_044_truth",
        "do_not_replace_issue_045_truth",
        "do_not_restate_issue_045_continuation_or_anti_loop_law",
        "do_not_restate_issue_046_runtime_actuator_law",
        "do_not_restate_issue_044_adoption_law",
        "fail_close_on_root_semantic_redefinition",
        "fail_close_on_canonical_owner_truth_replacement",
        "fail_close_on_silent_whole_lane_reopen",
    ],
    "validator_command": "TMPDIR=$PWD/.tmp python3 scripts/validate_non_owner_machine_law_reinforcement_admission.py --json-only",
    "probe_command": "TMPDIR=$PWD/.tmp bash scripts/ci/run_non_owner_machine_law_reinforcement_admission_probes_ci.sh",
}

BASELINE_REINFORCEMENT_PAYLOAD: Dict[str, Any] = {
    "reinforcement_entry_surface": "consumer",
    "reinforcement_authority_source": "accepted_root_law_ref",
    "accepted_root_law_ref": "ISSUE-045 accepted root law",
    "reinforcement_scope_status": "bounded",
    "whole_lane_completion_target": "complete_whole_lane",
    "whole_lane_completion_status": "admitted",
    "non_owner_reinforcement_status": "admitted",
    "cross_layer_completion_admission_status": "admitted",
    "canonical_owner_truth_preservation_status": "preserved",
    "root_semantic_redefinition_status": "not_redefined",
    "stale_reasons": [],
}


def json_block(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def render_governance_doc() -> str:
    return f"""# ISSUE-043 — Non-Owner Machine-Law Reinforcement Admission Governance v1.6.x

## Governing law
`{GOVERNING_LAW}`

## Unique delta vs ISSUE-045
{UNIQUE_DELTA}

## Machine-visible fields
{"".join(f"- `{field}`\n" for field in FIXED_FIELDS)}
## Hard boundaries
- Reinforcement may start from `root`, `middle`, or `consumer` surfaces.
- Reinforcement must preserve canonical owner truth.
- Reinforcement must keep `accepted_root_law_ref` explicit.
- Reinforcement must not redefine accepted root law.
- Reinforcement must not silently whole-lane reopen.
- Reinforcement must not overwrite ISSUE-044 or ISSUE-045 tracking truth.

## Canonical contract payload
<!-- CONTRACT_PAYLOAD_START -->
{json_block(canonical_contract_payload())}
<!-- CONTRACT_PAYLOAD_END -->
"""


def render_review_doc() -> str:
    return f"""# ISSUE-043 — Protocol Remediation Audit Ledger (Non-Owner Machine-Law Reinforcement Admission)

## Review focus
- confirm ISSUE-043 stays architecture reinforcement only
- confirm ISSUE-045 / ISSUE-046 / ISSUE-044 truths remain untouched
- confirm whole-lane completion is admitted only with preserved owner truth and explicit root-law reference

## Acceptance checklist
- governance and review payloads are identical
- all 11 machine-visible fields are present
- `accepted_root_law_ref` is explicit and required
- `whole_lane_completion_target` is explicit and bounded
- `canonical_owner_truth_preservation_status` prevents replacing owner truth
- `root_semantic_redefinition_status` fail-closes root semantic rewrite
- workbook/register add or rewrite ISSUE-043 only, without overwriting ISSUE-044 / ISSUE-045 truth

## Canonical contract payload
<!-- CONTRACT_PAYLOAD_START -->
{json_block(canonical_contract_payload())}
<!-- CONTRACT_PAYLOAD_END -->
"""


def build_workbook_block() -> str:
    field_lines = "\n".join(
        [
            "- reinforcement_entry_surface: `root|middle|consumer`",
            "- reinforcement_authority_source: `accepted_root_law_ref`",
            "- accepted_root_law_ref: `explicit_required`",
            "- reinforcement_scope_status: `bounded`",
            "- whole_lane_completion_target: `complete_whole_lane`",
            "- whole_lane_completion_status: `admitted`",
            "- non_owner_reinforcement_status: `admitted`",
            "- cross_layer_completion_admission_status: `admitted`",
            "- canonical_owner_truth_preservation_status: `preserved`",
            "- root_semantic_redefinition_status: `not_redefined`",
            "- stale_reasons: `[]`",
        ]
    )
    return f"""## ISSUE-043 — {CONTRACT_ID}

- status: `CLOSED`
- governing_law: `{GOVERNING_LAW}`
- unique_delta_vs_issue_045: {UNIQUE_DELTA}
{field_lines}

### Hard boundaries
- preserve canonical owner truth
- preserve accepted root law semantics
- fail-close on silent whole-lane reopen
- do not overwrite ISSUE-044 / ISSUE-045 truth
- do not restate ISSUE-045 continuation / anti-loop law
- do not restate ISSUE-046 runtime actuator law
- do not restate ISSUE-044 adoption law

"""


def build_issue_register_row(existing_row: str) -> str:
    cells = existing_row.strip().strip("|").split("|")
    cell_count = max(1, len(cells))
    values = [
        " ISSUE-043 ",
        " CLOSED ",
        f" {CONTRACT_ID} ",
        " cross-layer whole-lane reinforcement completion ",
        f" {GOVERNING_LAW} ",
        " accepted_root_law_ref required; whole_lane_completion_status admitted ",
        " canonical_owner_truth_preservation_status preserved; root_semantic_redefinition_status not_redefined ",
        " do not overwrite ISSUE-044/045 truth; silent whole-lane reopen fail-close ",
    ]
    if cell_count < len(values):
        merged = values[: cell_count - 1]
        merged.append(" ".join(v.strip() for v in values[cell_count - 1 :]))
        values = merged
    elif cell_count > len(values):
        values.extend([" "] * (cell_count - len(values)))
    return "|" + "|".join(values[:cell_count]) + "|"


def _replace_section(text: str, start_pattern: str, end_pattern: str, replacement: str) -> str:
    pattern = re.compile(start_pattern + r".*?(?=" + end_pattern + r")", re.S | re.M)
    if not pattern.search(text):
        raise ValueError("issue_043_section_anchor_not_found")
    return pattern.sub(replacement, text, count=1)


def rewrite_workbook(path: Path = WORKBOOK_PATH) -> None:
    text = path.read_text(encoding="utf-8")
    block = build_workbook_block()
    if re.search(r"^## ISSUE-043\b", text, re.M):
        new_text = _replace_section(text, r"^## ISSUE-043\b", r"^## ISSUE-044\b", block)
    elif re.search(r"^## ISSUE-044\b", text, re.M):
        new_text = re.sub(r"^## ISSUE-044\b", block + "## ISSUE-044", text, count=1, flags=re.M)
    else:
        raise ValueError("issue_044_section_anchor_not_found")
    path.write_text(new_text, encoding="utf-8")


def rewrite_issue_register(path: Path = ISSUE_REGISTER_PATH) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issue_043_index = next((i for i, line in enumerate(lines) if line.startswith("| ISSUE-043 ")), None)
    issue_044_index = next((i for i, line in enumerate(lines) if line.startswith("| ISSUE-044 ")), None)
    if issue_044_index is None:
        raise ValueError("issue_register_issue_044_anchor_not_found")
    template_row = lines[issue_043_index] if issue_043_index is not None else lines[issue_044_index]
    new_row = build_issue_register_row(template_row)
    if issue_043_index is None:
        lines.insert(issue_044_index, new_row)
    elif issue_043_index < issue_044_index:
        lines[issue_043_index] = new_row
    else:
        raise ValueError("issue_register_issue_043_anchor_not_found")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")



def canonical_contract_payload() -> Dict[str, Any]:
    return {**CANONICAL_PAYLOAD, **baseline_payload()}


def write_artifacts() -> None:
    GOVERNANCE_PATH.write_text(render_governance_doc(), encoding="utf-8")
    REVIEW_PATH.write_text(render_review_doc(), encoding="utf-8")
    rewrite_workbook()
    rewrite_issue_register()


def extract_payload(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return extract_payload_from_text(text, str(path))


def extract_payload_from_text(text: str, source: str) -> Dict[str, Any]:
    match = re.search(
        r"<!-- CONTRACT_PAYLOAD_START -->\s*(\{.*?\})\s*<!-- CONTRACT_PAYLOAD_END -->",
        text,
        re.S,
    )
    if not match:
        raise ValueError(f"missing_contract_payload:{source}")
    return json.loads(match.group(1))


def validate_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    expected_payload = canonical_contract_payload()
    if payload != expected_payload:
        errors.append("canonical_payload_mismatch")
    if payload.get("reinforcement_fields") != FIXED_FIELDS:
        errors.append("reinforcement_fields_mismatch")
    if payload.get("allowed_entry_surfaces") != ALLOWED_ENTRY_SURFACES:
        errors.append("allowed_entry_surfaces_mismatch")
    statuses = payload.get("required_statuses", {})
    for key, expected_value in expected_payload["required_statuses"].items():
        if statuses.get(key) != expected_value:
            errors.append(f"required_status_mismatch:{key}")
    for forbidden in FORBIDDEN_LEGACY_TOKENS:
        if forbidden in json.dumps(payload, sort_keys=True):
            errors.append(f"forbidden_legacy_token_present:{forbidden}")
    return errors


def extract_workbook_issue_043_block(text: str) -> str:
    match = re.search(r"(^## ISSUE-043\b.*?)(?=^## ISSUE-044\b)", text, re.S | re.M)
    if not match:
        raise ValueError("workbook_issue_043_block_missing")
    return match.group(1)


def validate_workbook(path: Path) -> List[str]:
    return validate_workbook_text(path.read_text(encoding="utf-8"))


def find_issue_register_row(text: str, issue_id: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"| {issue_id} "):
            return line
    raise ValueError(f"issue_register_row_missing:{issue_id}")


def validate_issue_register(path: Path) -> List[str]:
    return validate_issue_register_text(path.read_text(encoding="utf-8"))


def validate_contract(
    governance_path: Path = GOVERNANCE_PATH,
    review_path: Path = REVIEW_PATH,
    workbook_path: Path = WORKBOOK_PATH,
    issue_register_path: Path = ISSUE_REGISTER_PATH,
) -> Dict[str, Any]:
    errors: List[str] = []
    checks: Dict[str, Any] = {}
    try:
        governance_payload = extract_payload(governance_path)
        review_payload = extract_payload(review_path)
        checks["governance_payload"] = "present"
        checks["review_payload"] = "present"
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        governance_payload = None
        review_payload = None
    if governance_payload is not None and review_payload is not None:
        if governance_payload != review_payload:
            errors.append("governance_review_payload_mismatch")
        errors.extend(validate_payload(governance_payload))
    errors.extend(validate_workbook(workbook_path))
    errors.extend(validate_issue_register(issue_register_path))
    status = "PASS_REQUIRED" if not errors else "FAIL_REQUIRED"
    return {
        "issue_id": ISSUE_ID,
        "contract_id": CONTRACT_ID,
        "status": status,
        "errors": errors,
        "checks": checks,
    }


def evaluate_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    if candidate.get("reinforcement_entry_surface") not in ALLOWED_ENTRY_SURFACES:
        errors.append("reinforcement_entry_surface_not_admitted")
    if candidate.get("reinforcement_authority_source") != "accepted_root_law_ref":
        errors.append("reinforcement_authority_source_not_admitted")
    if not candidate.get("accepted_root_law_ref"):
        errors.append("accepted_root_law_ref_missing")
    if candidate.get("reinforcement_scope_status") != "bounded":
        errors.append("reinforcement_scope_not_bounded")
    if candidate.get("whole_lane_completion_target") != "complete_whole_lane":
        errors.append("whole_lane_completion_target_invalid")
    if candidate.get("whole_lane_completion_status") != "admitted":
        errors.append("whole_lane_completion_status_not_admitted")
    if candidate.get("non_owner_reinforcement_status") != "admitted":
        errors.append("non_owner_reinforcement_not_admitted")
    if candidate.get("cross_layer_completion_admission_status") != "admitted":
        errors.append("cross_layer_completion_admission_not_admitted")
    if candidate.get("canonical_owner_truth_preservation_status") != "preserved":
        errors.append("canonical_owner_truth_not_preserved")
    if candidate.get("root_semantic_redefinition_status") != "not_redefined":
        errors.append("root_semantic_redefinition_attempted")
    if candidate.get("stale_reasons") not in ([], None):
        errors.append("stale_reasons_not_empty")
    return {"status": "PASS_REQUIRED" if not errors else "FAIL_REQUIRED", "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--print-payload", action="store_true")
    args = parser.parse_args()
    if args.write_artifacts:
        write_artifacts()
    if args.print_payload:
        print(json.dumps(canonical_contract_payload(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def default_surface_paths() -> Dict[str, str]:
    return {
        "governance": str(GOVERNANCE_PATH),
        "review": str(REVIEW_PATH),
        "workbook": str(WORKBOOK_PATH),
        "issue_register": str(ISSUE_REGISTER_PATH),
    }


def baseline_payload() -> Dict[str, Any]:
    return json.loads(json.dumps(BASELINE_REINFORCEMENT_PAYLOAD))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_doc_tokens(label: str, text: str) -> List[str]:
    errors: List[str] = []
    try:
        payload = extract_payload_from_text(text, label)
    except ValueError as exc:
        return [str(exc)]
    errors.extend(validate_payload(payload))
    if GOVERNING_LAW not in text:
        errors.append(f"{label}_governing_law_missing")
    if label == "governance" and UNIQUE_DELTA not in text:
        errors.append("governance_unique_delta_missing")
    for forbidden in FORBIDDEN_SCOPE_TOKENS:
        if forbidden in text:
            errors.append(f"{label}_forbidden_scope_token:{forbidden}")
    return errors


def validate_workbook_text(text: str) -> List[str]:
    errors: List[str] = []
    if "## ISSUE-044" not in text:
        errors.append("workbook_issue_044_missing")
    if "## ISSUE-045" not in text:
        errors.append("workbook_issue_045_missing")
    try:
        block = extract_workbook_issue_043_block(text)
    except ValueError as exc:
        return [str(exc)]
    required_tokens = [
        CONTRACT_ID,
        GOVERNING_LAW,
        "reinforcement_entry_surface",
        "reinforcement_authority_source",
        "accepted_root_law_ref",
        "reinforcement_scope_status",
        "whole_lane_completion_target",
        "whole_lane_completion_status",
        "non_owner_reinforcement_status",
        "cross_layer_completion_admission_status",
        "canonical_owner_truth_preservation_status",
        "root_semantic_redefinition_status",
        "stale_reasons",
        "preserve canonical owner truth",
        "do not overwrite ISSUE-044 / ISSUE-045 truth",
    ]
    for token in required_tokens:
        if token not in block:
            errors.append(f"workbook_missing_token:{token}")
    for forbidden in FORBIDDEN_LEGACY_TOKENS + FORBIDDEN_SCOPE_TOKENS:
        if forbidden in block:
            errors.append(f"workbook_forbidden_token:{forbidden}")
    if text.find("## ISSUE-043") > text.find("## ISSUE-044"):
        errors.append("workbook_issue_043_not_before_issue_044")
    return errors


def validate_issue_register_text(text: str) -> List[str]:
    errors: List[str] = []
    try:
        row_043 = find_issue_register_row(text, ISSUE_ID)
        row_044 = find_issue_register_row(text, "ISSUE-044")
        find_issue_register_row(text, "ISSUE-045")
    except ValueError as exc:
        return [str(exc)]
    required_tokens = [
        CONTRACT_ID,
        "cross-layer whole-lane reinforcement completion",
        GOVERNING_LAW,
        "accepted_root_law_ref",
        "whole_lane_completion_status",
        "canonical_owner_truth_preservation_status",
        "root_semantic_redefinition_status",
        "do not overwrite ISSUE-044/045 truth",
    ]
    for token in required_tokens:
        if token not in row_043:
            errors.append(f"issue_register_missing_token:{token}")
    for forbidden in FORBIDDEN_LEGACY_TOKENS + FORBIDDEN_SCOPE_TOKENS:
        if forbidden in row_043:
            errors.append(f"issue_register_forbidden_token:{forbidden}")
    if text.find(row_043) > text.find(row_044):
        errors.append("issue_register_issue_043_not_before_issue_044")
    return errors


def validate_reinforcement_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    payload_text = json.dumps(payload, sort_keys=True)
    for forbidden in FORBIDDEN_LEGACY_TOKENS:
        if forbidden in payload_text:
            errors.append(f"payload_forbidden_legacy_token:{forbidden}")
    for field in FIXED_FIELDS:
        if field not in payload:
            errors.append(f"payload_missing_field:{field}")
    errors.extend(evaluate_candidate(payload)["errors"])
    return errors


if __name__ == "__main__":
    sys.exit(main())
