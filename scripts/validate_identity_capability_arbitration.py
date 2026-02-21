#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "priority_order",
    "conflict_rules",
    "trigger_thresholds",
    "decision_record_required_fields",
    "sample_report_path_pattern",
    "fail_action",
]

REQ_PRIORITY = ["accurate_judgement", "governance", "latency", "exploration"]
REQ_CONFLICTS = [
    "judgement_vs_routing",
    "reasoning_vs_latency",
    "routing_vs_learning",
    "learning_vs_hotfix",
]
REQ_DECISION_FIELDS = [
    "arbitration_id",
    "task_id",
    "identity_id",
    "conflict_pair",
    "inputs",
    "decision",
    "impact",
    "rationale",
    "decided_at",
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


def _validate_record(rec: dict[str, Any], identity_id: str, *, strict_identity: bool) -> list[str]:
    issues: list[str] = []
    miss = [k for k in REQ_DECISION_FIELDS if k not in rec]
    if miss:
        issues.append(f"missing fields: {miss}")
        return issues
    if strict_identity and str(rec.get("identity_id", "")).strip() != identity_id:
        issues.append("identity_id mismatch")
    if str(rec.get("conflict_pair", "")) not in REQ_CONFLICTS:
        issues.append(f"conflict_pair must be one of {REQ_CONFLICTS}")
    if not isinstance(rec.get("inputs"), dict) or not rec.get("inputs"):
        issues.append("inputs must be non-empty object")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability arbitration contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--metrics-path", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate capability arbitration for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("capability_arbitration_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing capability_arbitration_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] capability_arbitration_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] capability_arbitration_contract.required must be true")
        return 1

    priority = c.get("priority_order") or []
    if priority != REQ_PRIORITY:
        print(f"[FAIL] priority_order must equal: {REQ_PRIORITY}")
        return 1

    conflicts = c.get("conflict_rules") or {}
    if not isinstance(conflicts, dict):
        print("[FAIL] conflict_rules must be object")
        return 1

    rc = 0
    for k in REQ_CONFLICTS:
        r = conflicts.get(k)
        if not isinstance(r, dict):
            print(f"[FAIL] conflict_rules.{k} must be object")
            rc = 1
            continue
        if not isinstance(r.get("when"), list) or not r.get("when"):
            print(f"[FAIL] conflict_rules.{k}.when must be non-empty list")
            rc = 1
        if not str(r.get("decision", "")).strip():
            print(f"[FAIL] conflict_rules.{k}.decision must be non-empty string")
            rc = 1

    thresholds = c.get("trigger_thresholds") or {}
    for k in ("misroute_rate_percent", "replay_failure_rate_percent", "first_pass_success_drop_percent"):
        v = thresholds.get(k)
        if not isinstance(v, (int, float)) or v <= 0:
            print(f"[FAIL] trigger_thresholds.{k} must be > 0")
            rc = 1

    decision_fields = c.get("decision_record_required_fields") or []
    if any(x not in decision_fields for x in REQ_DECISION_FIELDS):
        print(f"[FAIL] decision_record_required_fields missing required fields: {REQ_DECISION_FIELDS}")
        rc = 1

    report_path = Path(args.report) if args.report else Path("identity/runtime/examples") / f"{args.identity_id}-capability-arbitration-sample.json"
    if not report_path.exists():
        files = sorted(Path(".").glob(c.get("sample_report_path_pattern", "")))
        if files:
            report_path = files[-1]
    if not report_path.exists():
        print(f"[FAIL] missing capability arbitration sample report: {report_path}")
        return 1

    report = _load_json(report_path)
    records = report.get("records") or []
    if not isinstance(records, list) or not records:
        print("[FAIL] report.records must be non-empty list")
        return 1
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            print(f"[FAIL] records[{i}] must be object")
            rc = 1
            continue
        for issue in _validate_record(rec, args.identity_id, strict_identity=True):
            print(f"[FAIL] records[{i}] {issue}")
            rc = 1

    # Optional threshold/metrics linkage validation (enabled when metrics artifact exists)
    route_quality = task.get("route_quality_contract") or {}
    metrics_path = Path(args.metrics_path) if args.metrics_path else Path(
        route_quality.get("metrics_output_path", f"identity/runtime/metrics/{args.identity_id}-route-quality.json")
    )
    if metrics_path.exists():
        try:
            metrics = _load_json(metrics_path)
        except Exception as e:
            print(f"[FAIL] metrics artifact invalid json: {metrics_path} ({e})")
            rc = 1
            metrics = {}
        if metrics:
            misroute = float(metrics.get("misroute_rate", 0))
            replay_fail = max(0.0, 100.0 - float(metrics.get("replay_success_rate", 100.0)))
            first_pass_drop = max(0.0, 100.0 - float(metrics.get("first_pass_success_rate", 100.0)))
            should_trigger = (
                misroute >= float(thresholds.get("misroute_rate_percent", 999))
                or replay_fail >= float(thresholds.get("replay_failure_rate_percent", 999))
                or first_pass_drop >= float(thresholds.get("first_pass_success_drop_percent", 999))
            )
            if "upgrade_required" in report:
                reported_trigger = bool(report.get("upgrade_required", False))
                if should_trigger != reported_trigger:
                    print(
                        "[FAIL] metrics/threshold linkage mismatch: "
                        f"should_trigger={should_trigger}, report.upgrade_required={reported_trigger}"
                    )
                    rc = 1
                else:
                    print(
                        "[OK] metrics/threshold linkage aligned: "
                        f"should_trigger={should_trigger}, report.upgrade_required={reported_trigger}"
                    )
            else:
                print(
                    "[OK] metrics/threshold linkage check skipped: report has no 'upgrade_required' field "
                    f"(computed should_trigger={should_trigger})"
                )

    if args.self_test:
        pos = sorted(Path("identity/runtime/examples/arbitration/positive").glob("*.json"))
        neg = sorted(Path("identity/runtime/examples/arbitration/negative").glob("*.json"))
        if len(pos) < 2 or len(neg) < 1:
            print("[FAIL] arbitration self-test requires >=2 positive and >=1 negative samples")
            return 1
        for p in pos:
            r = _load_json(p)
            recs = r.get("records") or []
            if not recs:
                print(f"[FAIL] positive arbitration sample missing records: {p}")
                return 1
            for i, rec in enumerate(recs):
                issues = _validate_record(rec, args.identity_id, strict_identity=False)
                if issues:
                    print(f"[FAIL] positive arbitration sample {p}#{i}: {issues}")
                    return 1
        for p in neg:
            r = _load_json(p)
            recs = r.get("records") or []
            if not recs:
                print(f"[FAIL] negative arbitration sample missing records: {p}")
                return 1
            has_invalid = False
            for rec in recs:
                if not isinstance(rec, dict):
                    has_invalid = True
                    break
                if _validate_record(rec, args.identity_id, strict_identity=False):
                    has_invalid = True
                    break
            if not has_invalid:
                print(f"[FAIL] negative arbitration sample did not contain invalid condition: {p}")
                return 1
        print("[OK] arbitration self-test passed")

    if rc:
        return 1

    print("Capability arbitration contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
