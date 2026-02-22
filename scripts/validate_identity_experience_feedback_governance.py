#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "redaction_policy_required",
    "retention_days",
    "sensitive_fields_denylist",
    "export_scope",
    "max_log_age_days",
    "minimum_logs_required",
    "feedback_log_path_pattern",
    "promotion_requires_replay_pass",
]

REQ_FEEDBACK_FIELDS = [
    "feedback_id",
    "identity_id",
    "task_id",
    "run_id",
    "timestamp",
    "context_signature",
    "outcome",
    "failure_type",
    "decision_trace_ref",
    "artifacts",
    "rulebook_delta",
    "replay_status",
]

ALLOWED_EXPORT_SCOPE = {"instance-only", "aggregated-only"}


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


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience feedback governance controls")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate experience feedback governance for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    task = _load_json(task_path)
    c = task.get("experience_feedback_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing experience_feedback_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] experience_feedback_contract missing governance fields: {missing}")
        return 1

    rc = 0
    if c.get("required") is not True:
        print("[FAIL] experience_feedback_contract.required must be true")
        rc = 1
    if c.get("redaction_policy_required") is not True:
        print("[FAIL] redaction_policy_required must be true")
        rc = 1
    if not isinstance(c.get("retention_days"), int) or int(c.get("retention_days")) <= 0:
        print("[FAIL] retention_days must be positive integer")
        rc = 1
    denylist = c.get("sensitive_fields_denylist") or []
    if not isinstance(denylist, list) or len(denylist) == 0:
        print("[FAIL] sensitive_fields_denylist must be non-empty list")
        rc = 1
    if str(c.get("export_scope", "")).strip() not in ALLOWED_EXPORT_SCOPE:
        print(f"[FAIL] export_scope must be one of {sorted(ALLOWED_EXPORT_SCOPE)}")
        rc = 1
    max_age = c.get("max_log_age_days")
    if not isinstance(max_age, int) or max_age <= 0:
        print("[FAIL] max_log_age_days must be positive integer")
        rc = 1
    min_logs = c.get("minimum_logs_required")
    if not isinstance(min_logs, int) or min_logs < 1:
        print("[FAIL] minimum_logs_required must be integer >= 1")
        rc = 1
    if c.get("promotion_requires_replay_pass") is not True:
        print("[FAIL] promotion_requires_replay_pass must be true")
        rc = 1

    pattern = str(c.get("feedback_log_path_pattern", "")).strip()
    if not pattern:
        print("[FAIL] feedback_log_path_pattern missing")
        return 1

    logs = sorted(Path(".").glob(pattern))
    if len(logs) < min_logs:
        print(f"[FAIL] feedback logs count {len(logs)} < minimum_logs_required {min_logs}")
        return 1

    latest = logs[-1]
    latest_row = _load_json(latest)
    missing_feedback_fields = [k for k in REQ_FEEDBACK_FIELDS if k not in latest_row]
    if missing_feedback_fields:
        print(f"[FAIL] latest feedback log missing fields: {missing_feedback_fields}")
        rc = 1

    if str(latest_row.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] latest feedback identity_id mismatch")
        rc = 1

    try:
        ts = _parse_ts(str(latest_row.get("timestamp", "")))
        age_days = (datetime.now(timezone.utc) - ts).days
        if age_days > max_age:
            print(f"[FAIL] latest feedback log too old: {age_days}d > max_log_age_days={max_age}")
            rc = 1
        else:
            print(f"[OK] latest feedback log freshness: {age_days}d <= {max_age}")
    except Exception as e:
        print(f"[FAIL] invalid feedback timestamp: {e}")
        rc = 1

    # ensure no sensitive fields are present in top-level keys
    top_keys = {str(k).lower() for k in latest_row.keys()}
    hit = [k for k in denylist if str(k).lower() in top_keys]
    if hit:
        print(f"[FAIL] feedback log contains denylisted top-level keys: {hit}")
        rc = 1

    # Optional report path can override sample, else use existing sample path pattern
    report_path = Path(args.report) if args.report else None
    if not report_path or not report_path.exists():
        sample_pattern = str(c.get("sample_report_path_pattern", "")).strip()
        if sample_pattern:
            samples = sorted(Path(".").glob(sample_pattern))
            if samples:
                report_path = samples[-1]
    if report_path and report_path.exists():
        report = _load_json(report_path)
        updates = (report.get("positive_updates") or []) + (report.get("negative_updates") or [])
        if c.get("promotion_requires_replay_pass") is True:
            for i, u in enumerate(updates):
                if isinstance(u, dict) and str(u.get("replay_status", "")).strip() != "PASS":
                    print(f"[FAIL] report update[{i}] replay_status must be PASS for promotion")
                    rc = 1
        print(f"[OK] feedback sample report checked: {report_path}")

    if rc:
        return 1
    print(f"[OK] feedback logs validated: {len(logs)} file(s), latest={latest}")
    print("Experience feedback governance validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
