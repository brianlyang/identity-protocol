#!/usr/bin/env python3
"""Validate ISSUE-044 instance protocol delta adoption surfaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from instance_protocol_delta_adoption_contract_common import (
    ABSORBED_LAW_ID,
    ABSORBED_PROTOCOL_DELTA_COMMIT,
    ABSORBED_PROTOCOL_DELTA_SUBJECT,
    ADOPTED_PROTOCOL_DELTA_LAWS,
    CAPABILITY_FAMILIES,
    FAIL_CLOSE_REASON_FAMILY,
    FAIL_MODE,
    FAIL_STATUS,
    FALLBACK_PATH,
    GOVERNANCE_DOC,
    ISSUE_ID,
    LANE_ID,
    PASS_STATUS,
    POLICY_PATH,
    REQUIRED_MACHINE_FIELDS,
    RELEVANT_PROTOCOL_DELTA_LAWS,
    REVIEW_DOC,
    STATE_PATH,
    SUCCESS_MODE,
    repo_root_from_script,
)


def _contains(text: str, needle: str) -> bool:
    return needle in text


def build_result(repo_root: Path) -> dict:
    governance_text = (repo_root / GOVERNANCE_DOC).read_text(encoding="utf-8")
    review_text = (repo_root / REVIEW_DOC).read_text(encoding="utf-8")

    stale_reasons: list[str] = []

    if not _contains(governance_text, ABSORBED_LAW_ID):
        stale_reasons.append(f"protocol_owner_surface_not_ready:{ABSORBED_LAW_ID}")
    if not _contains(governance_text, ABSORBED_PROTOCOL_DELTA_COMMIT):
        stale_reasons.append("protocol_authority_resolution_failed")
    if not _contains(governance_text, "protocol_delta_adoption != runtime_enforcement_semantics"):
        stale_reasons.append("instance_local_adoption_markers_missing:adoption_enforcement_boundary")
    if not _contains(review_text, ABSORBED_LAW_ID):
        stale_reasons.append(f"runtime_guard_law_not_adopted:{ABSORBED_LAW_ID}")
    if not _contains(review_text, ABSORBED_PROTOCOL_DELTA_COMMIT):
        stale_reasons.append(f"relevant_unadopted_protocol_commits:{ABSORBED_LAW_ID}")

    adopted_protocol_delta_laws = list(ADOPTED_PROTOCOL_DELTA_LAWS)
    relevant_protocol_delta_laws = list(RELEVANT_PROTOCOL_DELTA_LAWS)
    relevant_unadopted_commits: list[str] = []

    if ABSORBED_LAW_ID not in relevant_protocol_delta_laws:
        stale_reasons.append(f"protocol_owner_surface_not_ready:{ABSORBED_LAW_ID}")
    if ABSORBED_LAW_ID not in adopted_protocol_delta_laws:
        stale_reasons.append(f"runtime_guard_law_not_adopted:{ABSORBED_LAW_ID}")
        relevant_unadopted_commits.append(ABSORBED_PROTOCOL_DELTA_COMMIT)

    if stale_reasons:
        status = FAIL_STATUS
        mode = FAIL_MODE
        protocol_delta_state_written = False
        last_adopted_protocol_commit = ""
        if ABSORBED_PROTOCOL_DELTA_COMMIT not in relevant_unadopted_commits:
            relevant_unadopted_commits.append(ABSORBED_PROTOCOL_DELTA_COMMIT)
    else:
        status = PASS_STATUS
        mode = SUCCESS_MODE
        protocol_delta_state_written = True
        last_adopted_protocol_commit = ABSORBED_PROTOCOL_DELTA_COMMIT

    result = {
        "issue_id": ISSUE_ID,
        "lane_id": LANE_ID,
        "protocol_current_head": ABSORBED_PROTOCOL_DELTA_COMMIT,
        "protocol_current_head_short": ABSORBED_PROTOCOL_DELTA_COMMIT,
        "protocol_current_head_subject": ABSORBED_PROTOCOL_DELTA_SUBJECT,
        "last_seen_protocol_commit": ABSORBED_PROTOCOL_DELTA_COMMIT,
        "last_adopted_protocol_commit": last_adopted_protocol_commit,
        "capability_family_count": len(CAPABILITY_FAMILIES),
        "capability_families": list(CAPABILITY_FAMILIES),
        "relevant_protocol_delta_laws": relevant_protocol_delta_laws,
        "adopted_protocol_delta_laws": adopted_protocol_delta_laws,
        "scanned_commit_count": 1,
        "relevant_unadopted_commit_count": len(relevant_unadopted_commits),
        "relevant_unadopted_commits": relevant_unadopted_commits,
        "protocol_delta_adoption_status": status,
        "protocol_delta_adoption_mode": mode,
        "protocol_delta_state_written": protocol_delta_state_written,
        "protocol_root": str(repo_root),
        "policy_path": POLICY_PATH,
        "fallback_path": FALLBACK_PATH,
        "state_path": STATE_PATH,
        "stale_reasons": stale_reasons,
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "fail_close_reason_family": list(FAIL_CLOSE_REASON_FAMILY),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = repo_root_from_script(Path(__file__))
    result = build_result(repo_root)

    payload = json.dumps(result, ensure_ascii=False, indent=None if args.json_only else 2)
    if args.json_only:
        print(payload)
    else:
        print(payload)

    return 0 if result["protocol_delta_adoption_status"] == PASS_STATUS else 1


if __name__ == "__main__":
    sys.exit(main())
