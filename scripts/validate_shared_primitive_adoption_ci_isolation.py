#!/usr/bin/env python3
"""Validate shared primitive adoption CI isolation residual contract."""

# contract_lane_id: shared_primitive_adoption_ci_isolation_residual
# contract_governing_law: shared_primitive_adoption_ci_must_be_isolated_from_preexisting_dirty_state_and_nonlane_context

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared_primitive_adoption_ci_isolation_common import (
    ERR_DIRTY_STATE,
    ERR_MISSING,
    ERR_NONLANE,
    ERR_SCOPE,
    FIXED_WRITE_SET,
    FORBIDDEN_DIRTY_STATE_TOKENS,
    FORBIDDEN_SCOPE_TOKENS,
    GOVERNING_LAW,
    LANE_ID,
    REQUIRED_CI_TOKENS,
    REQUIRED_GOVERNANCE_TOKENS,
    REQUIRED_REVIEW_TOKENS,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    build_contract_row,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    governance_path = repo_root / FIXED_WRITE_SET[1]
    review_path = repo_root / FIXED_WRITE_SET[2]
    ci_path = repo_root / FIXED_WRITE_SET[0]
    common_path = repo_root / FIXED_WRITE_SET[3]
    validator_path = repo_root / FIXED_WRITE_SET[4]

    blocking_reasons: list[str] = []
    contract_rows: list[dict[str, str]] = []

    missing_paths = [rel for rel in FIXED_WRITE_SET if not (repo_root / rel).exists()]
    contract_rows.append(
        build_contract_row(
            "fixed_write_set_present",
            not missing_paths,
            "all fixed write set files present" if not missing_paths else ",".join(missing_paths),
        )
    )
    if missing_paths:
        blocking_reasons.extend(f"missing:{rel}" for rel in missing_paths)

    governance_text = read_text(governance_path) if governance_path.exists() else ""
    review_text = read_text(review_path) if review_path.exists() else ""
    ci_text = read_text(ci_path) if ci_path.exists() else ""
    common_text = read_text(common_path) if common_path.exists() else ""
    validator_text = read_text(validator_path) if validator_path.exists() else ""

    missing_governance_tokens = [
        token for token in REQUIRED_GOVERNANCE_TOKENS if token not in governance_text
    ]
    contract_rows.append(
        build_contract_row(
            "governance_tokens_present",
            not missing_governance_tokens,
            "governance tokens present"
            if not missing_governance_tokens
            else ",".join(missing_governance_tokens),
        )
    )
    if missing_governance_tokens:
        blocking_reasons.append("governance_token_missing")

    missing_review_tokens = [token for token in REQUIRED_REVIEW_TOKENS if token not in review_text]
    contract_rows.append(
        build_contract_row(
            "review_tokens_present",
            not missing_review_tokens,
            "review tokens present"
            if not missing_review_tokens
            else ",".join(missing_review_tokens),
        )
    )
    if missing_review_tokens:
        blocking_reasons.append("review_token_missing")

    fixed_write_set_mentions = [rel for rel in FIXED_WRITE_SET if rel in ci_text]
    ci_scope_ok = len(fixed_write_set_mentions) == len(FIXED_WRITE_SET)
    contract_rows.append(
        build_contract_row(
            "ci_fixed_write_set_scope",
            ci_scope_ok,
            "ci script mirrors fixed write set only"
            if ci_scope_ok
            else f"fixed_write_set_mentions={len(fixed_write_set_mentions)}",
        )
    )
    if not ci_scope_ok:
        blocking_reasons.append("nonlane_scope_missing")

    forbidden_scope_hits = [token for token in FORBIDDEN_SCOPE_TOKENS if token in ci_text]
    contract_rows.append(
        build_contract_row(
            "ambient_scope_dependency_absent",
            not forbidden_scope_hits,
            "no ambient scope dependency"
            if not forbidden_scope_hits
            else ",".join(forbidden_scope_hits),
        )
    )
    if forbidden_scope_hits:
        blocking_reasons.append("ambient_scope_dependency")

    forbidden_dirty_state_hits = [
        token for token in FORBIDDEN_DIRTY_STATE_TOKENS if token in ci_text
    ]
    contract_rows.append(
        build_contract_row(
            "dirty_state_dependency_absent",
            not forbidden_dirty_state_hits,
            "no dirty-state dependency"
            if not forbidden_dirty_state_hits
            else ",".join(forbidden_dirty_state_hits),
        )
    )
    if forbidden_dirty_state_hits:
        blocking_reasons.append("dirty_state_dependency")

    missing_ci_tokens = [token for token in REQUIRED_CI_TOKENS if token not in ci_text]
    contract_rows.append(
        build_contract_row(
            "ci_required_tokens_present",
            not missing_ci_tokens,
            "ci required tokens present"
            if not missing_ci_tokens
            else ",".join(missing_ci_tokens),
        )
    )
    if missing_ci_tokens:
        blocking_reasons.append("ci_token_missing")

    common_ok = LANE_ID in common_text and GOVERNING_LAW in common_text and "FIXED_WRITE_SET" in common_text
    contract_rows.append(
        build_contract_row(
            "common_contract_present",
            common_ok,
            "common contract constants present" if common_ok else "common contract constants missing",
        )
    )
    if not common_ok:
        blocking_reasons.append("common_contract_missing")

    validator_ok = (
        LANE_ID in validator_text
        and GOVERNING_LAW in validator_text
        and "shared_primitive_adoption_ci_isolation_status" in validator_text
    )
    contract_rows.append(
        build_contract_row(
            "validator_contract_present",
            validator_ok,
            "validator contract constants present"
            if validator_ok
            else "validator contract constants missing",
        )
    )
    if not validator_ok:
        blocking_reasons.append("validator_contract_missing")

    if any(reason.startswith("missing:") for reason in blocking_reasons):
        error_code = ERR_MISSING
    elif "ambient_scope_dependency" in blocking_reasons:
        error_code = ERR_SCOPE
    elif "dirty_state_dependency" in blocking_reasons:
        error_code = ERR_DIRTY_STATE
    elif blocking_reasons:
        error_code = ERR_NONLANE
    else:
        error_code = None

    status = STATUS_PASS_REQUIRED if not blocking_reasons else STATUS_FAIL_REQUIRED
    payload = {
        "lane_id": LANE_ID,
        "governing_law": GOVERNING_LAW,
        "shared_primitive_adoption_ci_isolation_status": status,
        "error_code": error_code,
        "fixed_write_set": list(FIXED_WRITE_SET),
        "contract_rows": contract_rows,
        "contract_row_count": len(contract_rows),
        "blocking_reasons": blocking_reasons,
        "ci_scope_isolation_status": STATUS_PASS_REQUIRED
        if "ambient_scope_dependency" not in blocking_reasons and "nonlane_scope_missing" not in blocking_reasons
        else STATUS_FAIL_REQUIRED,
        "dirty_state_isolation_status": STATUS_PASS_REQUIRED
        if "dirty_state_dependency" not in blocking_reasons
        else STATUS_FAIL_REQUIRED,
        "nonlane_context_status": STATUS_PASS_REQUIRED
        if status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED,
    }

    print(json.dumps(payload, indent=None if args.json_only else 2, sort_keys=True))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
