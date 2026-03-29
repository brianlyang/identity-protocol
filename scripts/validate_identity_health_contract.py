#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experience_writeback_closure_projection_common import (
    build_experience_writeback_closure_projection,
    clean_list as common_clean_list,
    clean_str as common_clean_str,
)
from health_report_experience_writeback_projection_common import (
    HEALTH_REPORT_EXPERIENCE_WRITEBACK_BOUNDARY_COMPANION_FIELDS,
)
from runtime_temp_path_common import runtime_temp_root


def _latest_for_identity(report_dir: Path, identity_id: str) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-health-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return rows[-1] if rows else None


def _clean_str(value: object) -> str:
    return common_clean_str(value)


def _clean_list(value: object) -> list[str]:
    return common_clean_list(value)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity health report contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default=str(runtime_temp_root() / "identity-health-reports"))
    ap.add_argument("--require-pass", action="store_true")
    args = ap.parse_args()

    if args.report:
        path = Path(args.report).expanduser().resolve()
    else:
        latest = _latest_for_identity(Path(args.report_dir).expanduser().resolve(), args.identity_id)
        if latest is None:
            print(f"[FAIL] no health report found for identity={args.identity_id} in {args.report_dir}")
            return 1
        path = latest

    if not path.exists():
        print(f"[FAIL] report not found: {path}")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "report_id",
        "generated_at",
        "identity_id",
        "overall_status",
        "warning_count",
        "failed_count",
        "checks",
        "recommendations",
        "experience_writeback_closure",
    ]
    miss = [k for k in required if k not in data]
    if miss:
        print(f"[FAIL] health report missing fields: {miss}")
        return 1

    if str(data.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] health report identity mismatch")
        return 1

    checks = data.get("checks") or []
    if not isinstance(checks, list) or not checks:
        print("[FAIL] health report checks must be non-empty list")
        return 1

    failed: list[dict] = []
    warns: list[dict] = []
    checks_by_name: dict[str, dict] = {}
    for c in checks:
        name = str(c.get("name", "")).strip()
        if name:
            checks_by_name[name] = c
        status = str(c.get("status", "")).strip().upper()
        if not status:
            status = "PASS" if bool(c.get("ok")) else "FAIL"
        if status == "FAIL":
            failed.append(c)
        elif status == "WARN":
            warns.append(c)
        elif status != "PASS":
            print(f"[FAIL] invalid health check status={status!r} in check={c.get('name')}")
            return 1

    experience_writeback_closure = data.get("experience_writeback_closure")
    if not isinstance(experience_writeback_closure, dict):
        print("[FAIL] experience_writeback_closure must be a dict")
        return 1
    execution_report_ref = _clean_str(data.get("execution_report_ref"))
    closure_projection = build_experience_writeback_closure_projection(
        data,
        execution_report=execution_report_ref,
    )
    experience_writeback_check = checks_by_name.get("experience_writeback")
    if not isinstance(experience_writeback_check, dict):
        print("[FAIL] health report missing experience_writeback check row")
        return 1
    experience_writeback_payload = experience_writeback_check.get("payload")
    if not isinstance(experience_writeback_payload, dict):
        print("[FAIL] experience_writeback check row missing payload dict")
        return 1
    check_status = str(experience_writeback_check.get("status", "")).strip().upper()
    if not check_status:
        check_status = "PASS" if bool(experience_writeback_check.get("ok")) else "FAIL"
    closure_status = _clean_str(closure_projection.get("status")).upper()
    if closure_status != check_status:
        print(
            "[FAIL] experience_writeback_closure.status mismatch: "
            f"closure={experience_writeback_closure.get('status')!r} check={experience_writeback_check.get('status')!r}"
        )
        return 1
    validation_status = _clean_str(closure_projection.get("validation_status")).upper()
    if validation_status not in {"PASS_REQUIRED", "SKIPPED_NOT_REQUIRED", "WARN_NON_BLOCKING", "FAIL_REQUIRED"}:
        print(f"[FAIL] invalid experience_writeback_closure.validation_status={validation_status!r}")
        return 1
    if validation_status != _clean_str(
        experience_writeback_payload.get("experience_writeback_validation_status")
    ).upper():
        print("[FAIL] experience_writeback_closure.validation_status mismatch with check payload")
        return 1
    projection_field_pairs = (
        ("report_selected_path", "report_selected_path"),
        ("report_logical_identity_key", "report_logical_identity_key"),
        ("report_selection_mode", "report_selection_mode"),
        ("report_selected_authority_class", "report_selected_authority_class"),
        ("report_pointer_resolution_mode", "report_pointer_resolution_mode"),
        ("report_run_id", "report_run_id"),
        ("writeback_status", "writeback_status"),
        ("writeback_rule_id", "writeback_rule_id"),
        *(
            (field_name, field_name)
            for field_name in HEALTH_REPORT_EXPERIENCE_WRITEBACK_BOUNDARY_COMPANION_FIELDS
        ),
    )
    for closure_field, payload_field in projection_field_pairs:
        if _clean_str(closure_projection.get(closure_field)) != _clean_str(
            experience_writeback_payload.get(payload_field)
        ):
            print(
                "[FAIL] experience_writeback_closure projection mismatch: "
                f"{closure_field} vs payload.{payload_field}"
            )
            return 1
    if int(closure_projection.get("rulebook_match_count", 0) or 0) != int(
        experience_writeback_payload.get("rulebook_match_count", 0) or 0
    ):
        print("[FAIL] experience_writeback_closure.rulebook_match_count mismatch with check payload")
        return 1
    if bool(closure_projection.get("task_history_contains_run_id", False)) != bool(
        experience_writeback_payload.get("task_history_contains_run_id", False)
    ):
        print("[FAIL] experience_writeback_closure.task_history_contains_run_id mismatch with check payload")
        return 1
    stale_reasons = closure_projection.get("stale_reasons")
    if stale_reasons is not None and not isinstance(stale_reasons, list):
        print("[FAIL] experience_writeback_closure.stale_reasons must be a list")
        return 1
    if _clean_list(stale_reasons) != _clean_list(experience_writeback_payload.get("stale_reasons")):
        print("[FAIL] experience_writeback_closure.stale_reasons mismatch with check payload")
        return 1
    if validation_status == "PASS_REQUIRED" and not _clean_str(closure_projection.get("report_selected_path")):
        print("[FAIL] experience_writeback_closure selected path missing for PASS_REQUIRED")
        return 1
    if (
        validation_status == "PASS_REQUIRED"
        and execution_report_ref
        and not bool(closure_projection.get("report_selected_path_matches_execution_report"))
    ):
        print("[FAIL] experience_writeback_closure selected path must match execution_report_ref for PASS_REQUIRED")
        return 1
    if (
        validation_status == "PASS_REQUIRED"
        and execution_report_ref
        and not bool(closure_projection.get("report_logical_identity_key_matches_execution_report"))
    ):
        print("[FAIL] experience_writeback_closure logical identity must match execution_report_ref for PASS_REQUIRED")
        return 1
    if (
        validation_status == "PASS_REQUIRED"
        and (
            not _clean_str(closure_projection.get("report_logical_identity_key"))
            or not _clean_str(closure_projection.get("report_selection_mode"))
            or not _clean_str(closure_projection.get("report_selected_authority_class"))
            or not _clean_str(closure_projection.get("report_pointer_resolution_mode"))
        )
    ):
        print("[FAIL] experience_writeback_closure authority projection incomplete for PASS_REQUIRED")
        return 1
    boundary_companion_statuses = {
        field_name: _clean_str(closure_projection.get(field_name)).upper()
        for field_name in HEALTH_REPORT_EXPERIENCE_WRITEBACK_BOUNDARY_COMPANION_FIELDS
    }
    if (
        validation_status == "PASS_REQUIRED"
        and any(status != "PASS_REQUIRED" for status in boundary_companion_statuses.values())
    ):
        print("[FAIL] experience_writeback_closure boundary bridge incomplete for PASS_REQUIRED")
        return 1
    if (
        validation_status == "SKIPPED_NOT_REQUIRED"
        and any(status != "SKIPPED_NOT_REQUIRED" for status in boundary_companion_statuses.values())
    ):
        print("[FAIL] experience_writeback_closure boundary bridge must stay skipped when validation is skipped")
        return 1
    if closure_status in {"WARN", "FAIL"}:
        if not str(experience_writeback_closure.get("error_code", "")).strip():
            print("[FAIL] non-pass experience_writeback_closure requires error_code")
            return 1
        if not str(experience_writeback_closure.get("suggestion", "")).strip():
            print("[FAIL] non-pass experience_writeback_closure requires suggestion")
            return 1

    recs = data.get("recommendations") or []
    if (failed or warns) and not recs:
        print("[FAIL] non-pass health checks require non-empty recommendations")
        return 1

    overall = str(data.get("overall_status", "")).upper()
    if overall not in {"PASS", "WARN", "FAIL"}:
        print(f"[FAIL] invalid overall_status in health report: {data.get('overall_status')!r}")
        return 1
    if args.require_pass and failed:
        print(f"[FAIL] health report contains failed checks (overall_status={overall})")
        return 2

    if int(data.get("warning_count", -1)) != len(warns):
        print(
            f"[FAIL] warning_count mismatch: report={data.get('warning_count')} computed={len(warns)}"
        )
        return 1
    if int(data.get("failed_count", -1)) != len(failed):
        print(
            f"[FAIL] failed_count mismatch: report={data.get('failed_count')} computed={len(failed)}"
        )
        return 1

    print(f"[OK] health report contract validated: {path}")
    print(f"     overall_status={overall} warning_checks={len(warns)} failed_checks={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
