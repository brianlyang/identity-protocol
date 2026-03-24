#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from feedback_current_run_binding_common import (
    derive_feedback_current_run_binding_projection,
    resolve_identity_feedback_logs,
    select_latest_identity_feedback_log,
)

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

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FIELD = "experience_feedback_governance_status"
ERR_TASK = "IP-EXPFB-GOV-001"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


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


def _resolve_identity_row(catalog_path: Path, identity_id: str) -> dict[str, Any] | None:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    return next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)


def _is_fixture_identity(row: dict[str, Any] | None) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _glob_paths(pattern: str, *, pack_root: Path) -> list[Path]:
    raw = str(pattern or "").strip()
    if not raw:
        return []
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    if p.is_absolute():
        if has_magic:
            return sorted(Path(x).resolve() for x in glob.glob(str(p)))
        return [p.resolve()] if p.exists() else []

    local_prefix = f"identity/runtime/local/{pack_root.name}/"
    mapped_raw = raw
    if raw.startswith(local_prefix):
        mapped_raw = f"runtime/{raw[len(local_prefix):]}"
    elif raw.startswith("identity/runtime/"):
        mapped_raw = f"runtime/{raw[len('identity/runtime/'):]}"
    preferred = sorted(pack_root.glob(mapped_raw))
    if preferred:
        return preferred
    if mapped_raw != raw:
        fallback = sorted(Path(".").glob(mapped_raw))
        if fallback:
            return fallback
    return sorted(Path(".").glob(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience feedback governance controls")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    def log(message: str) -> None:
        if not args.json_only:
            print(message)

    catalog_path = Path(args.catalog)
    try:
        task_path = _resolve_current_task(catalog_path, args.identity_id)
    except Exception as e:
        payload = {
            "identity_id": args.identity_id,
            "task_path": "",
            STATUS_FIELD: STATUS_FAIL_REQUIRED,
            "error_code": ERR_TASK,
            "latest_feedback_log": "",
            "latest_feedback_log_age_days": None,
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "required_run_id": "",
            "latest_feedback_run_id": "",
            "latest_feedback_run_id_match_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_same_run_binding_status": STATUS_FAIL_REQUIRED,
            "operational_prompt_receipt_ref": "",
            "operational_prompt_run_join_status": STATUS_FAIL_REQUIRED,
            "feedback_run_id": "",
            "preflight_reentry_receipt_ref": "",
            "loopback_live_binding_status": STATUS_FAIL_REQUIRED,
            "stale_reasons": [str(e)],
        }
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            log(f"[FAIL] {e}")
        return 1
    fixture_mode = _is_fixture_identity(_resolve_identity_row(catalog_path, args.identity_id))

    log(f"[INFO] validate experience feedback governance for identity: {args.identity_id}")
    log(f"[INFO] CURRENT_TASK: {task_path}")
    pack_root = task_path.parent.resolve()

    task = _load_json(task_path)
    c = task.get("experience_feedback_contract") or {}
    if not isinstance(c, dict) or not c:
        payload = {
            "identity_id": args.identity_id,
            "task_path": str(task_path),
            STATUS_FIELD: STATUS_FAIL_REQUIRED,
            "error_code": ERR_TASK,
            "latest_feedback_log": "",
            "latest_feedback_log_age_days": None,
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "required_run_id": "",
            "latest_feedback_run_id": "",
            "latest_feedback_run_id_match_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_same_run_binding_status": STATUS_FAIL_REQUIRED,
            "operational_prompt_receipt_ref": "",
            "operational_prompt_run_join_status": STATUS_FAIL_REQUIRED,
            "feedback_run_id": "",
            "preflight_reentry_receipt_ref": "",
            "loopback_live_binding_status": STATUS_FAIL_REQUIRED,
            "stale_reasons": ["missing_experience_feedback_contract"],
        }
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            log("[FAIL] missing experience_feedback_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        log(f"[FAIL] experience_feedback_contract missing governance fields: {missing}")
        return 1

    rc = 0
    if c.get("required") is not True:
        log("[FAIL] experience_feedback_contract.required must be true")
        rc = 1
    if c.get("redaction_policy_required") is not True:
        log("[FAIL] redaction_policy_required must be true")
        rc = 1
    if not isinstance(c.get("retention_days"), int) or int(c.get("retention_days")) <= 0:
        log("[FAIL] retention_days must be positive integer")
        rc = 1
    denylist = c.get("sensitive_fields_denylist") or []
    if not isinstance(denylist, list) or len(denylist) == 0:
        log("[FAIL] sensitive_fields_denylist must be non-empty list")
        rc = 1
    if str(c.get("export_scope", "")).strip() not in ALLOWED_EXPORT_SCOPE:
        log(f"[FAIL] export_scope must be one of {sorted(ALLOWED_EXPORT_SCOPE)}")
        rc = 1
    max_age = c.get("max_log_age_days")
    if not isinstance(max_age, int) or max_age <= 0:
        log("[FAIL] max_log_age_days must be positive integer")
        rc = 1
    min_logs = c.get("minimum_logs_required")
    if not isinstance(min_logs, int) or min_logs < 1:
        log("[FAIL] minimum_logs_required must be integer >= 1")
        rc = 1
    if c.get("promotion_requires_replay_pass") is not True:
        log("[FAIL] promotion_requires_replay_pass must be true")
        rc = 1

    pattern = str(c.get("feedback_log_path_pattern", "")).strip()
    if not pattern:
        payload = {
            "identity_id": args.identity_id,
            "task_path": str(task_path),
            STATUS_FIELD: STATUS_FAIL_REQUIRED,
            "error_code": ERR_TASK,
            "latest_feedback_log": "",
            "latest_feedback_log_age_days": None,
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "required_run_id": "",
            "latest_feedback_run_id": "",
            "latest_feedback_run_id_match_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_same_run_binding_status": STATUS_FAIL_REQUIRED,
            "operational_prompt_receipt_ref": "",
            "operational_prompt_run_join_status": STATUS_FAIL_REQUIRED,
            "feedback_run_id": "",
            "preflight_reentry_receipt_ref": "",
            "loopback_live_binding_status": STATUS_FAIL_REQUIRED,
            "stale_reasons": ["feedback_log_path_pattern_missing"],
        }
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            log("[FAIL] feedback_log_path_pattern missing")
        return 1

    logs = resolve_identity_feedback_logs(
        pack_root=pack_root,
        pattern=pattern,
        identity_id=args.identity_id,
    )
    if len(logs) < min_logs:
        payload = {
            "identity_id": args.identity_id,
            "task_path": str(task_path),
            STATUS_FIELD: STATUS_FAIL_REQUIRED,
            "error_code": ERR_TASK,
            "latest_feedback_log": "",
            "latest_feedback_log_age_days": None,
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "required_run_id": "",
            "latest_feedback_run_id": "",
            "latest_feedback_run_id_match_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_same_run_binding_status": STATUS_FAIL_REQUIRED,
            "operational_prompt_receipt_ref": "",
            "operational_prompt_run_join_status": STATUS_FAIL_REQUIRED,
            "feedback_run_id": "",
            "preflight_reentry_receipt_ref": "",
            "loopback_live_binding_status": STATUS_FAIL_REQUIRED,
            "stale_reasons": [f"feedback_logs_below_minimum:{len(logs)}<{min_logs}"],
        }
        if args.json_only:
            _emit(payload, json_only=True)
        else:
            log(f"[FAIL] feedback logs count {len(logs)} < minimum_logs_required {min_logs}")
        return 1

    latest = select_latest_identity_feedback_log(
        pack_root=pack_root,
        pattern=pattern,
        identity_id=args.identity_id,
    )
    if latest is None:
        latest = logs[-1]
    latest_row = _load_json(latest)
    missing_feedback_fields = [k for k in REQ_FEEDBACK_FIELDS if k not in latest_row]
    if missing_feedback_fields:
        log(f"[FAIL] latest feedback log missing fields: {missing_feedback_fields}")
        rc = 1

    if str(latest_row.get("identity_id", "")).strip() != args.identity_id:
        log("[FAIL] latest feedback identity_id mismatch")
        rc = 1

    try:
        ts = _parse_ts(str(latest_row.get("timestamp", "")))
        age_days = (datetime.now(timezone.utc) - ts).days
        if (not fixture_mode) and age_days > max_age:
            log(f"[FAIL] latest feedback log too old: {age_days}d > max_log_age_days={max_age}")
            rc = 1
        elif fixture_mode:
            log(f"[OK] latest feedback log freshness check skipped for fixture identity: age_days={age_days}")
        else:
            log(f"[OK] latest feedback log freshness: {age_days}d <= {max_age}")
    except Exception as e:
        log(f"[FAIL] invalid feedback timestamp: {e}")
        rc = 1

    # ensure no sensitive fields are present in top-level keys
    top_keys = {str(k).lower() for k in latest_row.keys()}
    hit = [k for k in denylist if str(k).lower() in top_keys]
    if hit:
        log(f"[FAIL] feedback log contains denylisted top-level keys: {hit}")
        rc = 1

    # Optional report path can override sample, else use existing sample path pattern
    report_path = Path(args.report) if args.report else None
    if not report_path or not report_path.exists():
        sample_pattern = str(c.get("sample_report_path_pattern", "")).strip()
        if sample_pattern:
            samples = _glob_paths(sample_pattern, pack_root=pack_root)
            if samples:
                report_path = samples[-1]
    if report_path and report_path.exists():
        report = _load_json(report_path)
        updates = (report.get("positive_updates") or []) + (report.get("negative_updates") or [])
        if c.get("promotion_requires_replay_pass") is True:
            for i, u in enumerate(updates):
                if isinstance(u, dict) and str(u.get("replay_status", "")).strip() != "PASS":
                    log(f"[FAIL] report update[{i}] replay_status must be PASS for promotion")
                    rc = 1
        log(f"[OK] feedback sample report checked: {report_path}")

    live_projection = derive_feedback_current_run_binding_projection(
        pack_root=pack_root,
        identity_id=args.identity_id,
        contract_doc=c,
    )
    payload = {
        "identity_id": args.identity_id,
        "task_path": str(task_path),
        STATUS_FIELD: STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED,
        "error_code": "" if rc == 0 else ERR_TASK,
        "latest_feedback_log": live_projection.get("latest_feedback_log", str(latest)),
        "latest_feedback_log_age_days": live_projection.get("latest_feedback_log_age_days"),
        "evidence_origin": live_projection.get("evidence_origin", "missing"),
        "report_freshness_status": live_projection.get("report_freshness_status", STATUS_FAIL_REQUIRED),
        "required_run_id": live_projection.get("required_run_id", ""),
        "latest_feedback_run_id": live_projection.get("latest_feedback_run_id", ""),
        "latest_feedback_run_id_match_status": live_projection.get(
            "latest_feedback_run_id_match_status",
            STATUS_FAIL_REQUIRED,
        ),
        "latest_feedback_same_run_binding_status": live_projection.get(
            "latest_feedback_same_run_binding_status",
            STATUS_FAIL_REQUIRED,
        ),
        "operational_prompt_receipt_ref": live_projection.get("operational_prompt_receipt_ref", ""),
        "operational_prompt_run_join_status": live_projection.get(
            "operational_prompt_run_join_status",
            STATUS_FAIL_REQUIRED,
        ),
        "feedback_run_id": live_projection.get("feedback_run_id", ""),
        "preflight_reentry_receipt_ref": live_projection.get("preflight_reentry_receipt_ref", ""),
        "loopback_live_binding_status": live_projection.get("loopback_live_binding_status", STATUS_FAIL_REQUIRED),
        "stale_reasons": sorted(
            set(
                ([] if rc == 0 else ["experience_feedback_governance_validation_failed"])
                + [str(reason).strip() for reason in (live_projection.get("stale_reasons") or []) if str(reason).strip()]
            )
        ),
    }
    if args.json_only:
        _emit(payload, json_only=True)
        return 0 if rc == 0 else 1
    if rc:
        return 1
    log(f"[OK] feedback logs validated: {len(logs)} file(s), latest={latest}")
    log(
        "[INFO] latest-log same-run projection: "
        f"required_run_id={payload['required_run_id']} "
        f"latest_feedback_run_id_match_status={payload['latest_feedback_run_id_match_status']} "
        f"operational_prompt_run_join_status={payload['operational_prompt_run_join_status']}"
    )
    log("Experience feedback governance validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
