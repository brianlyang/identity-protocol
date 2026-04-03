#!/usr/bin/env python3
from __future__ import annotations

# ISSUE-045 machine-visible execution-loop freeze:
# execution_loop_not_entering_mutation_phase
# planning_budget_status
# scope_lock_status
# mutation_phase_entry_status
# repeated_plan_restatement_status
# repeated_reanchor_status
# repeated_compaction_without_progress_status
# execution_loop_status
# stale_reasons
# ordered_execution_sequence=common -> governance/review -> validator -> probe -> workbook/register

import argparse
import json
from pathlib import Path

from lane_segmented_infrastructure_admission_contract_common import (
    DOC_EXPECTATIONS,
    EXECUTION_LOOP_STATE_FIELDS,
    FAIL_CLOSE_REASON,
    FAIL_REQUIRED,
    FIXED_WRITE_SET,
    ISSUE_ID,
    LANE_ID,
    ORDERED_EXECUTION_SEQUENCE,
    PASS_REQUIRED,
    canonical_payload,
    repo_root,
)


def validate(root: Path) -> dict[str, object]:
    stale_reasons: list[str] = []

    for rel_path in FIXED_WRITE_SET:
        target = root / rel_path
        if not target.exists():
            stale_reasons.append(f"missing_file:{rel_path}")
            continue

        if rel_path in DOC_EXPECTATIONS:
            text = target.read_text(encoding="utf-8")
            for token in DOC_EXPECTATIONS[rel_path]:
                if token not in text:
                    stale_reasons.append(f"missing_token:{rel_path}:{token}")

    common_path = root / "scripts/lane_segmented_infrastructure_admission_contract_common.py"
    validator_path = root / "scripts/validate_lane_segmented_infrastructure_admission.py"
    probe_path = root / "scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh"
    for rel_path, target in (
        ("scripts/lane_segmented_infrastructure_admission_contract_common.py", common_path),
        ("scripts/validate_lane_segmented_infrastructure_admission.py", validator_path),
        ("scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh", probe_path),
    ):
        if not target.exists():
            stale_reasons.append(f"missing_file:{rel_path}")
            continue
        text = target.read_text(encoding="utf-8")
        for token in (
            FAIL_CLOSE_REASON,
            *EXECUTION_LOOP_STATE_FIELDS,
            *ORDERED_EXECUTION_SEQUENCE,
        ):
            if token not in text:
                stale_reasons.append(f"missing_token:{rel_path}:{token}")

    payload = canonical_payload()
    expected_write_set = list(FIXED_WRITE_SET)
    if payload.get("fixed_write_set") != expected_write_set:
        stale_reasons.append("fixed_write_set_drift")

    ok = not stale_reasons
    return {
        "ok": ok,
        "status": PASS_REQUIRED if ok else FAIL_REQUIRED,
        "issue": ISSUE_ID,
        "lane_id": LANE_ID,
        "mode": "lane_segmented_infrastructure_admission_ready" if ok else FAIL_CLOSE_REASON,
        "checked_file_count": len(FIXED_WRITE_SET),
        "ordered_execution_sequence": list(ORDERED_EXECUTION_SEQUENCE),
        "execution_loop_state_fields": list(EXECUTION_LOOP_STATE_FIELDS),
        "fixed_write_set": expected_write_set,
        "stale_reasons": stale_reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    result = validate(repo_root(args.root))
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['status']} {result['issue']} {result['mode']} stale_reasons={len(result['stale_reasons'])}"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
