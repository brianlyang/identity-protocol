#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dialogue_governance_common import (
    DONE_BLOCKER_KEY,
    FINAL_CLAIM_REQUIRED_FIELDS,
    contract_required,
    done_blocker_max,
    enforce_outcome,
    extract_counts,
    has_nonempty,
    redline_thresholds,
    resolve_dialogue_contract,
    resolve_enforcement_mode,
    resolve_pack_and_task,
    resolve_report_path,
)


def _trace_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("trace_matrix")
    if isinstance(rows, list):
        return [x for x in rows if isinstance(x, dict)]
    return []


def _claim_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("final_claims")
    if isinstance(rows, list):
        return [x for x in rows if isinstance(x, dict)]

    # fallback from trace matrix: unique by final_claim_ref
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _trace_rows(report):
        ref = str(row.get("final_claim_ref", "")).strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        out.append(
            {
                "final_claim_ref": ref,
                "user_turn_ref": row.get("user_turn_ref"),
                "artifact_ref": row.get("artifact_ref"),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dialogue result-support evidence governance contract.")
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
        pattern_keys=("dialogue_result_support_report_path_pattern", "report_path_pattern"),
    )
    failures: list[str] = []
    warnings: list[str] = []

    if report_path is None:
        failures.append("IP-DCIC-003 dialogue result-support report not found")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"IP-DCIC-003 report json invalid: {report_path} ({exc})")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    data = report if isinstance(report, dict) else {}
    claims = _claim_rows(data)
    if not claims:
        failures.append("IP-DCIC-003 final_claims must be non-empty list")
        return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary={"identity_id": args.identity_id})

    trace = _trace_rows(data)
    trace_keys = {
        (
            str(x.get("final_claim_ref", "")).strip(),
            str(x.get("user_turn_ref", "")).strip(),
            str(x.get("artifact_ref", "")).strip(),
        )
        for x in trace
    }
    missing_claim_rows: list[int] = []
    unsupported_rows: list[int] = []
    for i, row in enumerate(claims):
        ref = str(row.get("final_claim_ref", "")).strip()
        if not ref:
            missing_claim_rows.append(i)
            continue
        missing = [k for k in FINAL_CLAIM_REQUIRED_FIELDS if not has_nonempty(row.get(k))]
        if missing:
            missing_claim_rows.append(i)
            continue
        key = (
            ref,
            str(row.get("user_turn_ref", "")).strip(),
            str(row.get("artifact_ref", "")).strip(),
        )
        if trace and key not in trace_keys:
            unsupported_rows.append(i)

    if missing_claim_rows:
        failures.append(
            "IP-DCIC-003 final claims missing upstream refs: "
            f"{missing_claim_rows[:20]} (total={len(missing_claim_rows)})"
        )
    if unsupported_rows:
        failures.append(
            "IP-DCIC-003 final claims not backed by trace matrix rows: "
            f"{unsupported_rows[:20]} (total={len(unsupported_rows)})"
        )

    counts = extract_counts(data)
    untraceable = counts.get("untraceable_final_claim_count", 0)
    # keep counts and computed evidence aligned (computed result is authoritative floor)
    untraceable = max(untraceable, len(missing_claim_rows) + len(unsupported_rows))
    redline = redline_thresholds(contract)
    if untraceable > int(redline.get("untraceable_final_claim_count", 0)):
        failures.append(
            "IP-DCIC-003 redline violated: "
            f"untraceable_final_claim_count={untraceable} > {redline.get('untraceable_final_claim_count', 0)}"
        )

    done_max = done_blocker_max(contract)
    unresolved = counts.get(DONE_BLOCKER_KEY, 0)
    if unresolved > done_max:
        failures.append(f"IP-DCIC-004 done-state blocker violated: {DONE_BLOCKER_KEY}={unresolved} > {done_max}")

    summary = {
        "identity_id": args.identity_id,
        "report_path": str(report_path),
        "rollout_mode": mode,
        "final_claims_total": len(claims),
        "trace_rows_total": len(trace),
        "missing_upstream_refs_count": len(missing_claim_rows),
        "unsupported_claim_count": len(unsupported_rows),
        "untraceable_final_claim_count": untraceable,
        "unresolved_ambiguity_count": unresolved,
        "redline_thresholds": redline,
        "done_state_blocker_max": done_max,
    }
    return enforce_outcome(mode=mode, failures=failures, warnings=warnings, summary=summary)


if __name__ == "__main__":
    raise SystemExit(main())

