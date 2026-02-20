#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity learning loop evidence (reasoning + rulebook linkage)")
    ap.add_argument("--current-task", default="identity/store-manager/CURRENT_TASK.json")
    ap.add_argument("--run-report", default="identity/runtime/examples/store-manager-learning-sample.json")
    ap.add_argument("--rulebook", default="")
    args = ap.parse_args()

    task_path = Path(args.current_task)
    if not task_path.exists():
        return _fail(f"missing current task file: {task_path}")
    task = _load_json(task_path)

    lvc = task.get("learning_verification_contract") or {}
    rlc = task.get("reasoning_loop_contract") or {}
    rb_contract = task.get("rulebook_contract") or {}

    if not lvc:
        return _fail("learning_verification_contract missing in CURRENT_TASK")

    run_report_path = Path(args.run_report)
    if not run_report_path.exists():
        return _fail(f"missing run report: {run_report_path}")
    run = _load_json(run_report_path)

    rc = 0

    run_id = str(run.get("run_id") or "").strip()
    if lvc.get("run_id_required", False) and not run_id:
        print("[FAIL] run_id is required by learning_verification_contract")
        rc = 1
    else:
        print(f"[OK]   run_id={run_id}")

    attempts = run.get("reasoning_attempts") or []
    if lvc.get("reasoning_trace_required", False):
        if not isinstance(attempts, list) or not attempts:
            print("[FAIL] reasoning_trace_required=true but reasoning_attempts is empty")
            rc = 1
        else:
            print(f"[OK]   reasoning_attempts count={len(attempts)}")

    required_attempt_fields = set(rlc.get("mandatory_fields_per_attempt") or [])
    for i, att in enumerate(attempts, start=1):
        if not isinstance(att, dict):
            print(f"[FAIL] attempt[{i}] must be object")
            rc = 1
            continue
        missing = [k for k in required_attempt_fields if k not in att]
        if missing:
            print(f"[FAIL] attempt[{i}] missing fields: {missing}")
            rc = 1
        else:
            print(f"[OK]   attempt[{i}] fields complete")

    rulebook_path = Path(args.rulebook) if args.rulebook else Path(rb_contract.get("rulebook_path") or "")
    if lvc.get("rulebook_update_required", False):
        if not rulebook_path.exists():
            print(f"[FAIL] rulebook not found: {rulebook_path}")
            rc = 1
        else:
            link_field = str(lvc.get("rulebook_link_field") or "evidence_run_id")
            matched = 0
            lines = [ln.strip() for ln in rulebook_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            for ln in lines:
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                if str(row.get(link_field) or "").strip() == run_id:
                    matched += 1
            if matched <= 0:
                print(f"[FAIL] no rulebook records linked by {link_field}={run_id}")
                rc = 1
            else:
                print(f"[OK]   linked rulebook records found: {matched}")

    if rc == 0:
        print("Identity learning-loop validation PASSED")
    else:
        print("Identity learning-loop validation FAILED")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
