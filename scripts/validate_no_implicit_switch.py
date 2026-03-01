#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ERR_NO_IMPLICIT_SWITCH = "IP-ASB-202"
STRICT_OPS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPS = {"scan", "three-plane", "inspection"}
ACTIVATION_AUDIT_SCHEMAS = {
    "single_active_catalog_with_actor_scoped_session_binding",
    "actor_scoped_catalog_with_multi_active",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _latest_switch_report(identity_id: str) -> Path | None:
    root = Path("/tmp/identity-activation-reports")
    if not root.exists():
        return None
    candidates = sorted(root.glob(f"identity-activation-switch-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate no implicit switch / no silent cross-actor demotion.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--switch-report", default="")
    ap.add_argument(
        "--operation",
        choices=sorted(STRICT_OPS | INSPECTION_OPS),
        default="validate",
        help="operation context for machine-readable routing semantics",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    operation = str(args.operation or "validate").strip().lower()
    report_path = Path(args.switch_report).expanduser().resolve() if args.switch_report.strip() else _latest_switch_report(args.identity_id)
    if not report_path or not report_path.exists():
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "operation": operation,
            "switch_report_path": str(report_path) if report_path else "",
            "implicit_switch_status": "SKIPPED_NOT_REQUIRED",
            "error_code": "",
            "stale_reasons": ["switch_report_not_found"],
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[OK] no switch report found for identity={args.identity_id}; skipped")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    report = _load_json(report_path)
    stale_reasons: list[str] = []
    error_code = ""
    status = "PASS_REQUIRED"

    if not report:
        stale_reasons.append("switch_report_invalid_json")
        error_code = ERR_NO_IMPLICIT_SWITCH
        status = "FAIL_REQUIRED"
    else:
        activation_model = str(report.get("activation_model", "")).strip()
        is_hotfix_schema = activation_model in ACTIVATION_AUDIT_SCHEMAS
        required = ("actor_id", "run_id", "entrypoint_pid", "switch_reason")
        for key in required:
            if not str(report.get(key, "")).strip():
                stale_reasons.append(f"missing_switch_field:{key}")
        if stale_reasons and is_hotfix_schema:
            error_code = ERR_NO_IMPLICIT_SWITCH
            status = "FAIL_REQUIRED"
        elif stale_reasons and not is_hotfix_schema:
            status = "SKIPPED_NOT_REQUIRED"
            stale_reasons.insert(0, "legacy_switch_report_schema_without_actor_audit_fields")
            error_code = ""

        cross_actor = bool(report.get("cross_actor_demotion_detected"))
        override = report.get("cross_actor_override") if isinstance(report.get("cross_actor_override"), dict) else {}
        if status != "SKIPPED_NOT_REQUIRED" and cross_actor and not bool(override.get("applied")):
            stale_reasons.append("cross_actor_demotion_without_explicit_override")
            error_code = ERR_NO_IMPLICIT_SWITCH
            status = "FAIL_REQUIRED"
        if (
            status != "SKIPPED_NOT_REQUIRED"
            and cross_actor
            and bool(override.get("applied"))
            and not str(override.get("receipt_path", "")).strip()
        ):
            stale_reasons.append("cross_actor_override_receipt_path_missing")
            error_code = ERR_NO_IMPLICIT_SWITCH
            status = "FAIL_REQUIRED"

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "operation": operation,
        "switch_report_path": str(report_path),
        "implicit_switch_status": status,
        "error_code": error_code,
        "stale_reasons": stale_reasons,
        "switch_id": str(report.get("switch_id", "")) if report else "",
        "actor_id": str(report.get("actor_id", "")) if report else "",
        "run_id": str(report.get("run_id", "")) if report else "",
        "cross_actor_demotion_detected": bool(report.get("cross_actor_demotion_detected")) if report else False,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if status == "PASS_REQUIRED":
            print(f"[OK] no implicit switch validated: report={report_path}")
        elif status == "SKIPPED_NOT_REQUIRED":
            print(f"[OK] no implicit switch skipped: report_missing for identity={args.identity_id}")
        else:
            print(f"[FAIL] {error_code or ERR_NO_IMPLICIT_SWITCH} implicit switch validation failed: report={report_path}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if status in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
