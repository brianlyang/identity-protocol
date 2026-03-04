#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dialogue_governance_common import (
    TRACE_REQUIRED_FIELDS,
    contract_required,
    enforce_outcome,
    has_nonempty,
    rate,
    resolve_dialogue_contract,
    resolve_enforcement_mode,
    resolve_pack_and_task,
    resolve_report_path,
    top3_thresholds,
)


def _trace_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("trace_matrix", "cross_validation_matrix", "records"):
        rows = report.get(key)
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, dict)]
    return []


def _changed(row: dict[str, Any]) -> bool:
    if bool(row.get("changed", False)):
        return True
    change_type = str(row.get("change_type", "")).strip().lower()
    return bool(change_type and change_type not in {"none", "unchanged"})


def _reconciled(row: dict[str, Any]) -> bool:
    if bool(row.get("reconciled", False)):
        return True
    state = str(row.get("reconciliation_state", "")).strip().lower()
    return state in {"rebuilt", "resolved", "reconciled"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dialogue cross-validation trace matrix governance contract.")
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
        pattern_keys=("dialogue_cross_validation_report_path_pattern", "report_path_pattern"),
    )
    failures: list[str] = []
    warnings: list[str] = []

    if report_path is None:
        failures.append("IP-DCIC-002 dialogue cross-validation report not found")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"IP-DCIC-002 report json invalid: {report_path} ({exc})")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    rows = _trace_rows(report if isinstance(report, dict) else {})
    if not rows:
        failures.append("IP-DCIC-002 trace matrix must be non-empty list")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    valid_rows = 0
    changed_total = 0
    changed_reconciled = 0
    missing_chain_rows: list[int] = []
    changed_unreconciled_rows: list[int] = []
    for i, row in enumerate(rows):
        missing = [k for k in TRACE_REQUIRED_FIELDS if not has_nonempty(row.get(k))]
        if missing:
            missing_chain_rows.append(i)
        else:
            valid_rows += 1

        if _changed(row):
            changed_total += 1
            if _reconciled(row):
                changed_reconciled += 1
            else:
                changed_unreconciled_rows.append(i)

    if missing_chain_rows:
        failures.append(
            "IP-DCIC-002 trace chain broken for rows: "
            f"{missing_chain_rows[:20]} (total={len(missing_chain_rows)})"
        )
    if changed_unreconciled_rows:
        failures.append(
            "IP-DCIC-002 changed constraints missing reconciliation: "
            f"{changed_unreconciled_rows[:20]} (total={len(changed_unreconciled_rows)})"
        )

    thresholds = top3_thresholds(contract)
    traceability = rate(valid_rows, len(rows))
    change_recon = rate(changed_reconciled, changed_total)

    if traceability < thresholds["dialogue_traceability_rate"]:
        failures.append(
            "IP-DCIC-002 dialogue_traceability_rate below threshold: "
            f"{traceability} < {thresholds['dialogue_traceability_rate']}"
        )
    if change_recon < thresholds["dialogue_change_reconciliation_rate"]:
        failures.append(
            "IP-DCIC-002 dialogue_change_reconciliation_rate below threshold: "
            f"{change_recon} < {thresholds['dialogue_change_reconciliation_rate']}"
        )

    summary = {
        "identity_id": args.identity_id,
        "report_path": str(report_path),
        "rollout_mode": mode,
        "trace_rows_total": len(rows),
        "trace_rows_valid": valid_rows,
        "changed_constraints_total": changed_total,
        "changed_constraints_reconciled": changed_reconciled,
        "metrics": {
            "dialogue_traceability_rate": traceability,
            "dialogue_change_reconciliation_rate": change_recon,
        },
        "thresholds": {
            "dialogue_traceability_rate": thresholds["dialogue_traceability_rate"],
            "dialogue_change_reconciliation_rate": thresholds["dialogue_change_reconciliation_rate"],
        },
    }
    return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary=summary)


if __name__ == "__main__":
    raise SystemExit(main())

