#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dialogue_governance_common import (
    DONE_BLOCKER_KEY,
    contract_required,
    done_blocker_max,
    enforce_outcome,
    extract_counts,
    hard_subset_threshold,
    has_nonempty,
    rate,
    redline_thresholds,
    resolve_dialogue_contract,
    resolve_enforcement_mode,
    resolve_pack_and_task,
    resolve_report_path,
    top3_thresholds,
)

REQ_SYNTHESIS_FIELDS = (
    "user_objective",
    "hard_constraints",
    "soft_preferences",
    "acceptance_criteria",
    "ambiguities",
    "resolved_decisions",
)


def _synthesis_root(report: dict[str, Any]) -> dict[str, Any]:
    s = report.get("synthesis")
    if isinstance(s, dict):
        return s
    return report


def _derive_counts(report: dict[str, Any], synthesis: dict[str, Any]) -> dict[str, int]:
    counts = extract_counts(report)

    hard_constraints = synthesis.get("hard_constraints")
    if not isinstance(hard_constraints, list):
        hard_constraints = []
    soft_constraints = synthesis.get("soft_preferences")
    if not isinstance(soft_constraints, list):
        soft_constraints = []
    extracted_constraints = report.get("extracted_constraints")
    if not isinstance(extracted_constraints, list):
        extracted_constraints = []

    changed_constraints = report.get("changed_constraints")
    if not isinstance(changed_constraints, list):
        changed_constraints = []
    reconciled_constraints = report.get("reconciled_constraints")
    if not isinstance(reconciled_constraints, list):
        reconciled_constraints = []

    if counts["required_constraints"] <= 0:
        counts["required_constraints"] = len(hard_constraints) + len(soft_constraints)
    if counts["required_hard_constraints"] <= 0:
        counts["required_hard_constraints"] = len(hard_constraints)
    if counts["extracted_constraints"] <= 0:
        counts["extracted_constraints"] = len(extracted_constraints)

    if counts["extracted_hard_constraints"] <= 0 and extracted_constraints:
        counts["extracted_hard_constraints"] = sum(
            1 for x in extracted_constraints if isinstance(x, dict) and bool(x.get("is_hard_constraint", False))
        )
    if counts["changed_constraints"] <= 0:
        counts["changed_constraints"] = len(changed_constraints)
    if counts["reconciled_constraints"] <= 0:
        counts["reconciled_constraints"] = len(reconciled_constraints)

    if counts["hard_constraint_missing_artifact_count"] <= 0 and hard_constraints:
        miss = 0
        for item in hard_constraints:
            if not isinstance(item, dict):
                continue
            if not has_nonempty(item.get("artifact_ref")):
                miss += 1
        counts["hard_constraint_missing_artifact_count"] = miss

    if counts["unresolved_ambiguity_count"] <= 0:
        ambiguities = synthesis.get("ambiguities")
        if isinstance(ambiguities, list):
            unresolved = 0
            for item in ambiguities:
                if isinstance(item, dict):
                    state = str(item.get("status", "")).strip().lower()
                    if state in {"resolved", "closed"}:
                        continue
                unresolved += 1
            counts["unresolved_ambiguity_count"] = unresolved

    if counts["traceable_constraints"] <= 0 and counts["extracted_constraints"] > 0:
        # keep optimistic fallback to avoid accidental zeroing in rollout warn mode.
        counts["traceable_constraints"] = counts["extracted_constraints"]

    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dialogue synthesis content governance contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="")
    ap.add_argument("--enforce-mode", choices=["auto", "warn", "enforce"], default="auto")
    args = ap.parse_args()

    try:
        pack_path, task_path = resolve_pack_and_task(Path(args.catalog).expanduser().resolve(), args.identity_id)
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = resolve_dialogue_contract(task)
    if not contract_required(contract):
        print(f"[OK] dialogue governance contract not required for identity={args.identity_id}; skipped")
        return 0

    mode = resolve_enforcement_mode(contract, args.enforce_mode)
    report_path = resolve_report_path(
        identity_id=args.identity_id,
        pack_path=pack_path,
        contract=contract,
        report=args.report,
        report_dir=args.report_dir,
        pattern_keys=("dialogue_content_report_path_pattern", "report_path_pattern"),
    )
    failures: list[str] = []
    warnings: list[str] = []

    if report_path is None:
        failures.append("IP-DCIC-001 dialogue content report not found")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"IP-DCIC-001 report json invalid: {report_path} ({exc})")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    synthesis = _synthesis_root(report if isinstance(report, dict) else {})
    if not isinstance(synthesis, dict):
        failures.append("IP-DCIC-001 synthesis payload must be object")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    missing_fields = [k for k in REQ_SYNTHESIS_FIELDS if k not in synthesis]
    if missing_fields:
        failures.append(f"IP-DCIC-001 synthesis missing required fields: {missing_fields}")

    counts = _derive_counts(report if isinstance(report, dict) else {}, synthesis)
    thresholds = top3_thresholds(contract)
    hard_min = hard_subset_threshold(contract)
    redline = redline_thresholds(contract)
    done_max = done_blocker_max(contract)

    coverage = rate(counts["extracted_constraints"], counts["required_constraints"])
    hard_coverage = rate(counts["extracted_hard_constraints"], counts["required_hard_constraints"])
    traceability = rate(counts["traceable_constraints"], counts["required_constraints"])
    change_recon = rate(counts["reconciled_constraints"], counts["changed_constraints"])

    if coverage < thresholds["dialogue_constraint_coverage_rate"]:
        failures.append(
            "IP-DCIC-001 dialogue_constraint_coverage_rate below threshold: "
            f"{coverage} < {thresholds['dialogue_constraint_coverage_rate']}"
        )
    if traceability < thresholds["dialogue_traceability_rate"]:
        failures.append(
            "IP-DCIC-001 dialogue_traceability_rate below threshold: "
            f"{traceability} < {thresholds['dialogue_traceability_rate']}"
        )
    if change_recon < thresholds["dialogue_change_reconciliation_rate"]:
        failures.append(
            "IP-DCIC-001 dialogue_change_reconciliation_rate below threshold: "
            f"{change_recon} < {thresholds['dialogue_change_reconciliation_rate']}"
        )
    if hard_coverage < hard_min:
        failures.append(f"IP-DCIC-001 hard subset coverage below threshold: {hard_coverage} < {hard_min}")

    for key, max_v in redline.items():
        v = counts.get(key, 0)
        if v > int(max_v):
            code = "IP-DCIC-001"
            if key == "hard_constraint_missing_artifact_count":
                code = "IP-DCIC-002"
            if key == "untraceable_final_claim_count":
                code = "IP-DCIC-003"
            failures.append(f"{code} redline violated: {key}={v} > {max_v}")
    unresolved = counts.get(DONE_BLOCKER_KEY, 0)
    if unresolved > done_max:
        failures.append(f"IP-DCIC-004 done-state blocker violated: {DONE_BLOCKER_KEY}={unresolved} > {done_max}")

    summary = {
        "identity_id": args.identity_id,
        "report_path": str(report_path),
        "rollout_mode": mode,
        "top3_thresholds": thresholds,
        "hard_subset_min": hard_min,
        "redline_thresholds": redline,
        "done_state_blocker_max": done_max,
        "counts": counts,
        "metrics": {
            "dialogue_constraint_coverage_rate": coverage,
            "dialogue_traceability_rate": traceability,
            "dialogue_change_reconciliation_rate": change_recon,
            "hard_constraint_subset_coverage_rate": hard_coverage,
        },
    }
    return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary=summary)


if __name__ == "__main__":
    raise SystemExit(main())

