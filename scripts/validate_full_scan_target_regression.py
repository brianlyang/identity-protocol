#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_P0_REGRESSION = "IP-SCAN-REG-001"
ERR_SCAN_CMD_FAILED = "IP-SCAN-REG-002"
ERR_REPORT_INVALID = "IP-SCAN-REG-003"
ERR_M2M_REGRESSION = "IP-SCAN-REG-004"
ERR_THREE_PLANE_SUMMARY_CONFLICT = "IP-SCAN-REG-005"

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _extract_p0_rows(report_doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for catalog in report_doc.get("catalogs") or []:
        if not isinstance(catalog, dict):
            continue
        layer = str(catalog.get("layer", "")).strip()
        for item in catalog.get("identities") or []:
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "")).strip().upper()
            if severity != "P0":
                continue
            rows.append(
                {
                    "layer": layer,
                    "identity_id": str(item.get("identity_id", "")).strip(),
                    "severity": severity,
                    "m2m_binding_closure_status": str(
                        ((item.get("m2m_projection") or {}).get("m2m_binding_closure_status", ""))
                    ).strip(),
                    "summary_error_codes": [
                        str(x.get("error_code", "")).strip()
                        for x in (((item.get("summary") or {}).get("failed") or []))
                        if isinstance(x, dict) and str(x.get("error_code", "")).strip()
                    ],
                }
            )
    return rows


def _extract_m2m_fail_rows(report_doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for catalog in report_doc.get("catalogs") or []:
        if not isinstance(catalog, dict):
            continue
        layer = str(catalog.get("layer", "")).strip()
        for item in catalog.get("identities") or []:
            if not isinstance(item, dict):
                continue
            m2m_projection = item.get("m2m_projection") or {}
            m2m_status = str(
                m2m_projection.get("m2m_binding_closure_status", "")
            ).strip().upper()
            if m2m_status in {"PASS", "PASS_REQUIRED", ""}:
                continue
            rows.append(
                {
                    "layer": layer,
                    "identity_id": str(item.get("identity_id", "")).strip(),
                    "m2m_binding_closure_status": m2m_status,
                    "m2m_failure_scope": str(
                        m2m_projection.get("m2m_failure_scope", "")
                    ).strip(),
                    "m2m_failure_reasons": list(
                        m2m_projection.get("m2m_failure_reasons") or []
                    ),
                    "m2m_failed_validator_count": int(
                        m2m_projection.get("m2m_failed_validator_count", 0) or 0
                    ),
                }
            )
    return rows


def _extract_three_plane_summary_conflicts(report_doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for catalog in report_doc.get("catalogs") or []:
        if not isinstance(catalog, dict):
            continue
        layer = str(catalog.get("layer", "")).strip()
        for item in catalog.get("identities") or []:
            if not isinstance(item, dict):
                continue
            profile = str(item.get("profile", "")).strip().lower()
            status = str(item.get("status", "")).strip().lower()
            if not (status == "active" and profile == "runtime"):
                continue
            severity = str(item.get("severity", "")).strip().upper()
            checks = item.get("checks") or {}
            if not isinstance(checks, dict):
                continue
            three_plane = checks.get("three_plane") or {}
            if not isinstance(three_plane, dict):
                continue
            if bool(three_plane.get("ok", False)):
                continue
            if severity != "OK":
                continue
            rows.append(
                {
                    "layer": layer,
                    "identity_id": str(item.get("identity_id", "")).strip(),
                    "severity": severity,
                    "three_plane_rc": int(three_plane.get("rc", 1) or 1),
                    "three_plane_tail": str(three_plane.get("tail", "")).strip(),
                }
            )
    return rows


def _identity_row_from_catalog(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if not isinstance(doc, dict):
        return {}
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), {})


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    row = _identity_row_from_catalog(catalog_path, identity_id)
    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _resolve_repo_path(path_like: str) -> Path:
    candidate = Path(str(path_like)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def _only_requested_session_binding_p0(report_doc: dict[str, Any]) -> bool:
    catalogs = report_doc.get("catalogs") or []
    if not isinstance(catalogs, list):
        return False
    found_p0 = False
    for catalog in catalogs:
        if not isinstance(catalog, dict):
            continue
        identities = catalog.get("identities") or []
        if not isinstance(identities, list):
            continue
        for item in identities:
            if not isinstance(item, dict):
                continue
            if str(item.get("severity", "")).strip().upper() != "P0":
                continue
            found_p0 = True
            checks = item.get("checks") or {}
            if not isinstance(checks, dict):
                return False
            failed_check_names = sorted(
                key
                for key, raw in checks.items()
                if isinstance(raw, dict) and not bool(raw.get("ok", False))
            )
            if failed_check_names != ["requested_session_binding"]:
                return False
            requested = checks.get("requested_session_binding") or {}
            requested_tail = str((requested or {}).get("tail", "")).strip()
            requested_ok = bool((requested or {}).get("ok", False))
            if requested_ok:
                return False
            if "IP-ASB-SESSION-ENTRY-001" not in requested_tail:
                return False
            m2m_projection = item.get("m2m_projection") or {}
            m2m_failed = m2m_projection.get("m2m_failed_checks") or []
            if not isinstance(m2m_failed, list) or len(m2m_failed) != 1:
                return False
            only_row = m2m_failed[0] if isinstance(m2m_failed[0], dict) else {}
            if str(only_row.get("check", "")).strip() != "requested_session_binding":
                return False
            if str(only_row.get("error_code", "")).strip() != "IP-ASB-SESSION-ENTRY-001":
                return False
    return found_p0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Regression gate: full_identity_protocol_scan --scan-mode target must keep summary.p0 == 0."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--project-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--target-source-layer", choices=["auto", "project", "global", "both"], default="project")
    ap.add_argument("--actor-id", default="assistant:codex")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--expected-work-layer", default="protocol")
    ap.add_argument("--expected-source-layer", default="project")
    ap.add_argument(
        "--allow-fixture-session-skip",
        action="store_true",
        help=(
            "allow fixture/demo-only identities to pass when the only P0 is "
            "requested_session_binding(IP-ASB-SESSION-ENTRY-001)"
        ),
    )
    ap.add_argument(
        "--enforce-m2m-pass",
        action="store_true",
        help="when set, fail-close if summary_m2m.fail != 0",
    )
    ap.add_argument("--out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    session_id = str(args.session_id or "").strip()
    if not session_id:
        session_id = f"run:full-scan-target-regression-{int(datetime.now(timezone.utc).timestamp())}"

    if str(args.out or "").strip():
        out_path = Path(str(args.out).strip()).expanduser().resolve()
    else:
        fd, tmp_path = tempfile.mkstemp(prefix="full-scan-target-regression-", suffix=".json")
        Path(tmp_path).unlink(missing_ok=True)
        out_path = Path(tmp_path).resolve()

    out_path.parent.mkdir(parents=True, exist_ok=True)

    project_catalog_path = _resolve_repo_path(str(args.project_catalog))
    repo_catalog_path = _resolve_repo_path(str(args.repo_catalog))
    full_scan_script_path = (REPO_ROOT / "scripts/full_identity_protocol_scan.py").resolve()

    cmd = [
        "python3",
        str(full_scan_script_path),
        "--scan-mode",
        "target",
        "--identity-ids",
        str(args.identity_id).strip(),
        "--target-source-layer",
        str(args.target_source_layer).strip(),
        "--project-catalog",
        str(project_catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--actor-id",
        str(args.actor_id).strip(),
        "--session-id",
        session_id,
        "--expected-work-layer",
        str(args.expected_work_layer).strip(),
        "--expected-source-layer",
        str(args.expected_source_layer).strip(),
        "--out",
        str(out_path),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))

    payload: dict[str, Any] = {
        "full_scan_target_regression_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "identity_id": str(args.identity_id).strip(),
        "target_source_layer": str(args.target_source_layer).strip(),
        "project_catalog": str(project_catalog_path),
        "repo_catalog": str(repo_catalog_path),
        "actor_id": str(args.actor_id).strip(),
        "session_id": session_id,
        "expected_work_layer": str(args.expected_work_layer).strip(),
        "expected_source_layer": str(args.expected_source_layer).strip(),
        "scan_command": cmd,
        "scan_cwd": str(REPO_ROOT),
        "scan_rc": proc.returncode,
        "scan_stdout_tail": (proc.stdout or "").strip().splitlines()[-1] if (proc.stdout or "").strip() else "",
        "scan_stderr_tail": (proc.stderr or "").strip().splitlines()[-1] if (proc.stderr or "").strip() else "",
        "scan_report_path": str(out_path),
        "summary": {},
        "summary_m2m": {},
        "p0_count": None,
        "p1_count": None,
        "ok_count": None,
        "p0_rows": [],
        "three_plane_summary_conflicts": [],
        "m2m_pass_count": None,
        "m2m_fail_count": None,
        "m2m_fail_rows": [],
        "enforce_m2m_pass": bool(args.enforce_m2m_pass),
        "allow_fixture_session_skip": bool(args.allow_fixture_session_skip),
        "fixture_identity": _is_fixture_identity(project_catalog_path, str(args.identity_id).strip()),
        "fixture_session_skip_applied": False,
        "stale_reasons": [],
    }

    if proc.returncode != 0:
        payload["error_code"] = ERR_SCAN_CMD_FAILED
        _emit(payload, json_only=args.json_only)
        return 1

    if not out_path.exists():
        payload["error_code"] = ERR_REPORT_INVALID
        payload["scan_stderr_tail"] = "full_scan_report_missing"
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        report_doc = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception as exc:
        payload["error_code"] = ERR_REPORT_INVALID
        payload["scan_stderr_tail"] = f"full_scan_report_parse_failed:{exc}"
        _emit(payload, json_only=args.json_only)
        return 1

    if not isinstance(report_doc, dict):
        payload["error_code"] = ERR_REPORT_INVALID
        payload["scan_stderr_tail"] = "full_scan_report_invalid_root"
        _emit(payload, json_only=args.json_only)
        return 1

    summary = report_doc.get("summary")
    if not isinstance(summary, dict):
        payload["error_code"] = ERR_REPORT_INVALID
        payload["scan_stderr_tail"] = "full_scan_summary_missing"
        _emit(payload, json_only=args.json_only)
        return 1

    p0_count = int(summary.get("p0", 0) or 0)
    payload["summary"] = summary
    payload["p0_count"] = p0_count
    payload["p1_count"] = int(summary.get("p1", 0) or 0)
    payload["ok_count"] = int(summary.get("ok", 0) or 0)
    payload["p0_rows"] = _extract_p0_rows(report_doc)
    payload["three_plane_summary_conflicts"] = _extract_three_plane_summary_conflicts(report_doc)
    summary_m2m = report_doc.get("summary_m2m")
    if isinstance(summary_m2m, dict):
        payload["summary_m2m"] = summary_m2m
        payload["m2m_pass_count"] = int(summary_m2m.get("pass", 0) or 0)
        payload["m2m_fail_count"] = int(summary_m2m.get("fail", 0) or 0)
    else:
        payload["summary_m2m"] = {}
        payload["m2m_pass_count"] = 0
        payload["m2m_fail_count"] = 0
    payload["m2m_fail_rows"] = _extract_m2m_fail_rows(report_doc)

    if p0_count != 0:
        if (
            bool(args.allow_fixture_session_skip)
            and bool(payload.get("fixture_identity"))
            and _only_requested_session_binding_p0(report_doc)
        ):
            payload["full_scan_target_regression_status"] = STATUS_PASS_REQUIRED
            payload["error_code"] = ""
            payload["fixture_session_skip_applied"] = True
            payload["stale_reasons"] = ["fixture_requested_session_binding_skip_applied"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["error_code"] = ERR_P0_REGRESSION
        _emit(payload, json_only=args.json_only)
        return 1

    if bool(args.enforce_m2m_pass) and int(payload["m2m_fail_count"] or 0) != 0:
        payload["error_code"] = ERR_M2M_REGRESSION
        _emit(payload, json_only=args.json_only)
        return 1

    if payload["three_plane_summary_conflicts"]:
        payload["error_code"] = ERR_THREE_PLANE_SUMMARY_CONFLICT
        payload["stale_reasons"] = ["three_plane_failed_but_summary_marked_ok"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["full_scan_target_regression_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
