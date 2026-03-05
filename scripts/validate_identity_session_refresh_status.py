#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REFRESH_PAYLOAD = "IP-ASB-RFS-001"
ERR_REFRESH_POINTER = "IP-ASB-RFS-002"
ERR_REFRESH_CONTEXT = "IP-ASB-RFS-003"
ERR_REFRESH_BASELINE = "IP-ASB-RFS-004"

STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

REQUIRED_FIELDS = (
    "identity_id",
    "actor_id",
    "catalog_path",
    "resolved_pack_path",
    "resolved_scope",
    "lease_status",
    "pointer_consistency",
    "risk_flags",
    "next_action",
    "report_protocol_commit_sha",
    "protocol_head_sha_at_run_start",
    "baseline_reference_mode",
    "current_protocol_head_sha",
    "head_drift_detected",
    "baseline_status",
    "baseline_error_code",
    "lag_commits",
)


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _identity_row(catalog: dict[str, Any], identity_id: str) -> dict[str, Any] | None:
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)


def _is_fixture_identity(row: dict[str, Any] | None) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_refresh_payload(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], int]:
    stale_reasons: list[str] = []
    if args.refresh_json.strip():
        p = Path(args.refresh_json).expanduser().resolve()
        if not p.exists():
            stale_reasons.append("refresh_json_not_found")
            return {}, stale_reasons, 1
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            stale_reasons.append("refresh_json_invalid")
            return {}, stale_reasons, 1
        if not isinstance(data, dict):
            stale_reasons.append("refresh_json_not_object")
            return {}, stale_reasons, 1
        return data, stale_reasons, 0

    cmd = [
        "python3",
        "scripts/refresh_identity_session_status.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--actor-id",
        args.actor_id,
        "--baseline-policy",
        args.baseline_policy,
        "--json-only",
    ]
    if args.execution_report.strip():
        cmd.extend(["--execution-report", args.execution_report.strip()])

    rc, out, err = _run_capture(cmd)
    payload = _parse_json_payload(out) or {}
    if rc != 0:
        stale_reasons.append("refresh_command_nonzero")
        if err:
            stale_reasons.append(f"refresh_command_stderr:{err.splitlines()[-1]}")
    if not payload:
        stale_reasons.append("refresh_payload_missing")
    return payload, stale_reasons, rc


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity session refresh status contract and gate semantics.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--refresh-json", default="", help="optional refresh payload json path")
    ap.add_argument("--baseline-policy", choices=["strict", "warn"], default="warn")
    ap.add_argument(
        "--operation",
        choices=sorted(STRICT_OPERATIONS | INSPECTION_OPERATIONS),
        default="validate",
        help="strict operations fail on hard refresh drift; inspection operations downgrade to WARN where possible",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    catalog = _load_catalog(catalog_path)
    if _is_fixture_identity(_identity_row(catalog, args.identity_id)):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "session_refresh_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "actor_id": "",
            "lease_status": "",
            "pointer_consistency": "",
            "risk_flags": [],
            "next_action": "",
            "baseline_status": "",
            "baseline_error_code": "",
            "report_protocol_commit_sha": "",
            "protocol_head_sha_at_run_start": "",
            "baseline_reference_mode": "",
            "current_protocol_head_sha": "",
            "head_drift_detected": False,
            "lag_commits": None,
            "report_selected_path": "",
            "required_contract": False,
            "stale_reasons": ["fixture_profile_scope"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    refresh_payload, stale_reasons, refresh_rc = _load_refresh_payload(args)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "session_refresh_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "actor_id": "",
        "lease_status": "",
        "pointer_consistency": "",
        "risk_flags": [],
        "next_action": "",
        "baseline_status": "",
        "baseline_error_code": "",
        "report_protocol_commit_sha": "",
        "protocol_head_sha_at_run_start": "",
        "baseline_reference_mode": "",
        "current_protocol_head_sha": "",
        "head_drift_detected": False,
        "lag_commits": None,
        "report_selected_path": "",
        "required_contract": True,
        "stale_reasons": [],
    }

    missing_fields: list[str] = []
    if refresh_payload:
        for key in REQUIRED_FIELDS:
            if key not in refresh_payload:
                missing_fields.append(key)

        payload.update(
            {
                "actor_id": str(refresh_payload.get("actor_id", "")).strip(),
                "lease_status": str(refresh_payload.get("lease_status", "")).strip().upper(),
                "pointer_consistency": str(refresh_payload.get("pointer_consistency", "")).strip().upper(),
                "risk_flags": refresh_payload.get("risk_flags", []),
                "next_action": str(refresh_payload.get("next_action", "")).strip(),
                "baseline_status": str(refresh_payload.get("baseline_status", "")).strip().upper(),
                "baseline_error_code": str(refresh_payload.get("baseline_error_code", "")).strip(),
                "report_protocol_commit_sha": str(refresh_payload.get("report_protocol_commit_sha", "")).strip(),
                "protocol_head_sha_at_run_start": str(refresh_payload.get("protocol_head_sha_at_run_start", "")).strip(),
                "baseline_reference_mode": str(refresh_payload.get("baseline_reference_mode", "")).strip(),
                "current_protocol_head_sha": str(refresh_payload.get("current_protocol_head_sha", "")).strip(),
                "head_drift_detected": bool(refresh_payload.get("head_drift_detected", False)),
                "lag_commits": refresh_payload.get("lag_commits"),
                "report_selected_path": str(refresh_payload.get("report_selected_path", "")).strip(),
            }
        )

    if missing_fields:
        stale_reasons.append(f"missing_required_fields:{','.join(missing_fields)}")

    if str(refresh_payload.get("identity_id", "")).strip() and str(refresh_payload.get("identity_id", "")).strip() != args.identity_id:
        stale_reasons.append("refresh_identity_id_mismatch")

    if str(refresh_payload.get("catalog_path", "")).strip() and str(Path(str(refresh_payload.get("catalog_path", "")).strip()).expanduser().resolve()) != str(catalog_path):
        stale_reasons.append("refresh_catalog_path_mismatch")

    lease_status = payload.get("lease_status", "")
    pointer_consistency = payload.get("pointer_consistency", "")
    baseline_status = payload.get("baseline_status", "")

    allowed_lease = {"ACTIVE", "STALE", "MISSING"}
    allowed_pointer = {"PASS", "WARN", "FAIL"}
    allowed_baseline = {"PASS", "WARN", "FAIL"}

    if lease_status and lease_status not in allowed_lease:
        stale_reasons.append("lease_status_invalid")
    if pointer_consistency and pointer_consistency not in allowed_pointer:
        stale_reasons.append("pointer_consistency_invalid")
    if baseline_status and baseline_status not in allowed_baseline:
        stale_reasons.append("baseline_status_invalid")
    baseline_reference_mode = str(payload.get("baseline_reference_mode", "")).strip().lower()
    if baseline_reference_mode and baseline_reference_mode not in {"run_pinned", "live_head"}:
        stale_reasons.append("baseline_reference_mode_invalid")

    if not isinstance(payload.get("risk_flags", []), list):
        stale_reasons.append("risk_flags_not_array")

    operation = str(args.operation or "validate").strip().lower()
    inspection_mode = operation in INSPECTION_OPERATIONS

    error_code = ""
    status = STATUS_PASS_REQUIRED

    if stale_reasons:
        error_code = ERR_REFRESH_PAYLOAD
        status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    if refresh_rc != 0 and not error_code:
        error_code = ERR_REFRESH_PAYLOAD
        status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    if not error_code and pointer_consistency == "FAIL":
        error_code = ERR_REFRESH_POINTER
        status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    if not error_code and lease_status in {"MISSING", "STALE"}:
        error_code = ERR_REFRESH_POINTER
        status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    if not error_code and baseline_status == "FAIL":
        error_code = ERR_REFRESH_BASELINE
        status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    if (
        not error_code
        and not inspection_mode
        and baseline_reference_mode
        and baseline_reference_mode != "run_pinned"
        and operation in STRICT_OPERATIONS
    ):
        error_code = ERR_REFRESH_BASELINE
        status = STATUS_FAIL_REQUIRED
        stale_reasons.append("baseline_reference_mode_not_run_pinned_under_strict")

    if not error_code and baseline_status == "" and not inspection_mode:
        error_code = ERR_REFRESH_BASELINE
        status = STATUS_FAIL_REQUIRED

    if not error_code:
        actor_id = str(payload.get("actor_id", "")).strip()
        if not actor_id:
            error_code = ERR_REFRESH_CONTEXT
            status = STATUS_WARN_NON_BLOCKING if inspection_mode else STATUS_FAIL_REQUIRED

    payload["session_refresh_status"] = status
    payload["error_code"] = error_code
    payload["stale_reasons"] = stale_reasons

    _emit(payload, json_only=args.json_only)

    if status == STATUS_FAIL_REQUIRED:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
