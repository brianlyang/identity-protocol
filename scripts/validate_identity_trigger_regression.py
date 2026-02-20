#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_RUNTIME_KEYS = [
    "required",
    "required_suites",
    "result_enum",
    "sample_report_path_pattern",
    "fail_action",
]
REQ_SUITES = ["positive_cases", "boundary_cases", "negative_cases"]
REQ_CASE_FIELDS = [
    "case_id",
    "input_summary",
    "expected_route",
    "expected_trigger",
    "observed_route",
    "observed_trigger",
    "result",
    "notes",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")

    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p

    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _check_case(case: dict[str, Any], suite: str, idx: int) -> list[str]:
    missing = [k for k in REQ_CASE_FIELDS if k not in case]
    errs: list[str] = []
    if missing:
        errs.append(f"{suite}[{idx}] missing fields: {missing}")
    if case.get("result") not in {"PASS", "FAIL"}:
        errs.append(f"{suite}[{idx}].result must be PASS|FAIL")
    if not isinstance(case.get("expected_trigger"), bool):
        errs.append(f"{suite}[{idx}].expected_trigger must be bool")
    if not isinstance(case.get("observed_trigger"), bool):
        errs.append(f"{suite}[{idx}].observed_trigger must be bool")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity trigger regression contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    try:
        task_path = _resolve_current_task(catalog_path, args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate trigger regression for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    try:
        task = _load_json(task_path)
    except Exception as e:
        print(f"[FAIL] invalid CURRENT_TASK json: {e}")
        return 1

    c = task.get("trigger_regression_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing trigger_regression_contract")
        return 1

    missing_runtime = [k for k in REQ_RUNTIME_KEYS if k not in c]
    if missing_runtime:
        print(f"[FAIL] trigger_regression_contract missing fields: {missing_runtime}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] trigger_regression_contract.required must be true")
        return 1

    suites = c.get("required_suites") or []
    if set(REQ_SUITES) - set(suites):
        print(f"[FAIL] trigger_regression_contract.required_suites missing: {sorted(set(REQ_SUITES) - set(suites))}")
        return 1

    if set(c.get("result_enum") or []) != {"PASS", "FAIL"}:
        print("[FAIL] trigger_regression_contract.result_enum must be [PASS, FAIL]")
        return 1

    report_path = Path(args.report) if args.report else Path("identity/runtime/examples") / f"{args.identity_id}-trigger-regression-sample.json"
    if not report_path.exists():
        print(f"[FAIL] missing trigger regression report: {report_path}")
        return 1

    try:
        report = _load_json(report_path)
    except Exception as e:
        print(f"[FAIL] invalid trigger regression report json: {e}")
        return 1

    rc = 0
    for suite in REQ_SUITES:
        items = report.get(suite)
        if not isinstance(items, list) or not items:
            print(f"[FAIL] report.{suite} must be a non-empty array")
            rc = 1
            continue
        for idx, case in enumerate(items):
            if not isinstance(case, dict):
                print(f"[FAIL] {suite}[{idx}] must be object")
                rc = 1
                continue
            errs = _check_case(case, suite, idx)
            for err in errs:
                print(f"[FAIL] {err}")
                rc = 1

    summary = report.get("summary") or {}
    if summary.get("overall_result") not in {"PASS", "FAIL"}:
        print("[FAIL] report.summary.overall_result must be PASS|FAIL")
        rc = 1

    if rc:
        return 1

    print("Trigger regression contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
