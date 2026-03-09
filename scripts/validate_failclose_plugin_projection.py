#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_PLUGIN_PROJECTION_CONFIG = "IP-PLUGIN-PROJ-001"
ERR_PLUGIN_PROJECTION_RUNTIME = "IP-PLUGIN-PROJ-002"
BUNDLE_RUNNER_SCRIPT = "scripts/required_gate_bundle_runner.py"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return int(proc.returncode), proc.stdout or "", proc.stderr or ""


def _parse_payload(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in reversed(lines):
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _write_payload(path: str, payload: dict[str, Any]) -> None:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    return [str(x).strip() for x in _as_list(value) if str(x).strip()]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate fail-close plugin projection via governance-driven target probes."
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--operation", default="readiness")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report-selected-path", default="")
    ap.add_argument("--send-time-gate-status", default="")
    ap.add_argument("--outlet-bypass-detected", default="")
    ap.add_argument("--final-emit-contract-status", default="")
    ap.add_argument("--final-emit-policy-mode", default="")
    ap.add_argument("--final-emit-schema-status", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--resolved-work-layer", default="")
    ap.add_argument("--resolved-source-layer", default="")
    ap.add_argument("--lock-state", default="")
    ap.add_argument("--surface-label", default="projection")
    ap.add_argument(
        "--plugin-governance-file",
        default="identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml",
    )
    ap.add_argument("--out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    governance_path = (repo_root / str(args.plugin_governance_file)).resolve()
    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if not governance_path.exists():
        stale_reasons.append(f"plugin_governance_file_missing:{governance_path}")
    governance_doc = _load_yaml(governance_path) if governance_path.exists() else {}
    profiles = _as_list(governance_doc.get("plugin_failclose_profiles"))
    if not profiles:
        stale_reasons.append("plugin_failclose_profiles_empty")

    run_id = str(args.run_id or "").strip()
    if not run_id:
        stale_reasons.append("run_id_missing")

    for profile in profiles:
        if not isinstance(profile, dict):
            violations.append(
                {
                    "field": "plugin_failclose_profiles",
                    "reason": "profile_row_not_object",
                }
            )
            continue

        plugin_id = str(profile.get("plugin_id", "")).strip()
        target_name = str(profile.get("target_name", "")).strip()
        required_fields = _as_str_list(profile.get("required_report_fields"))
        if not target_name:
            violations.append(
                {
                    "field": "plugin_failclose_profiles",
                    "reason": "target_name_missing",
                    "plugin_id": plugin_id,
                }
            )
            continue
        if not required_fields:
            violations.append(
                {
                    "field": "plugin_failclose_profiles",
                    "reason": "required_report_fields_missing",
                    "plugin_id": plugin_id,
                    "target_name": target_name,
                }
            )
            continue

        cmd = [
            sys.executable,
            BUNDLE_RUNNER_SCRIPT,
            "--catalog",
            str(args.catalog),
            "--identity-id",
            str(args.identity_id),
            "--operation",
            str(args.operation),
            "--run-id",
            run_id,
            "--target-name",
            target_name,
            "--send-time-gate-status",
            str(args.send_time_gate_status),
            "--outlet-bypass-detected",
            str(args.outlet_bypass_detected),
            "--final-emit-contract-status",
            str(args.final_emit_contract_status),
            "--final-emit-policy-mode",
            str(args.final_emit_policy_mode),
            "--final-emit-schema-status",
            str(args.final_emit_schema_status),
            "--actor-id",
            str(args.actor_id),
            "--resolved-work-layer",
            str(args.resolved_work_layer),
            "--resolved-source-layer",
            str(args.resolved_source_layer),
            "--lock-state",
            str(args.lock_state),
            "--surface-label",
            str(args.surface_label),
            "--json-only",
        ]
        report_selected_path = str(args.report_selected_path or "").strip()
        if report_selected_path:
            cmd.extend(["--report-selected-path", report_selected_path])

        rc, out, err = _run_capture(cmd)
        payload = _parse_payload(out)
        missing_fields = [field for field in required_fields if field not in payload]
        status_candidates = [
            str(payload.get("multimodal_plugin_enforcement_status", "")).strip().upper(),
            str(payload.get("status", "")).strip().upper(),
        ]
        row_status = next((x for x in status_candidates if x), "")
        row_fail = rc != 0 or bool(missing_fields) or row_status == STATUS_FAIL_REQUIRED
        if row_fail:
            violations.append(
                {
                    "field": "plugin_projection",
                    "reason": "plugin_projection_target_failed",
                    "plugin_id": plugin_id,
                    "target_name": target_name,
                    "validator_rc": rc,
                    "missing_report_fields": missing_fields,
                    "target_status": row_status or "UNKNOWN",
                    "stderr_tail": (err.splitlines()[-1] if err else ""),
                }
            )
        rows.append(
            {
                "plugin_id": plugin_id,
                "target_name": target_name,
                "required_report_field_count": len(required_fields),
                "missing_report_fields": missing_fields,
                "validator_rc": rc,
                "target_status": row_status or "UNKNOWN",
                "report_selected_path": str(payload.get("report_selected_path", "")),
                "payload": payload,
            }
        )

    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PLUGIN_PROJECTION_CONFIG if stale_reasons else ERR_PLUGIN_PROJECTION_RUNTIME
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    result = {
        "failclose_plugin_projection_status": status,
        "error_code": error_code,
        "plugin_governance_file": str(governance_path),
        "identity_id": str(args.identity_id),
        "operation": str(args.operation),
        "run_id": run_id,
        "surface_label": str(args.surface_label),
        "profile_count": len([x for x in profiles if isinstance(x, dict)]),
        "checked_target_count": len(rows),
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
        "results": rows,
    }
    if str(args.out or "").strip():
        _write_payload(str(args.out), result)
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"[FAILCLOSE-PLUGIN-PROJECTION] status={status} "
            f"targets={len(rows)} violations={len(violations)} stale={len(stale_reasons)}"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
