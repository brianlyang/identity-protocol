#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experience_writeback_closure_projection_common import build_experience_writeback_closure_projection
from runtime_temp_path_common import runtime_temp_root

ERR_MISSING = "IP-HEAL-001"
ERR_REF_MISMATCH = "IP-HEAL-002"
ERR_POST_VALIDATE = "IP-HEAL-003"


def _latest_for_identity(report_dir: Path, identity_id: str) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-heal-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return rows[-1] if rows else None


def _emit(payload: dict[str, Any], json_only: bool) -> int:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if payload.get("heal_replay_closure_status") == "PASS_REQUIRED":
            print("[OK] heal replay closure contract validated")
        else:
            print(f"[FAIL] heal replay closure contract invalid (error_code={payload.get('error_code','')})")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("heal_replay_closure_status") == "PASS_REQUIRED" else 1


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _closure_projection(
    doc: dict[str, Any],
    *,
    execution_report: str | Path = "",
) -> dict[str, Any]:
    return build_experience_writeback_closure_projection(doc, execution_report=execution_report)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate health->heal->post-validate replay closure refs.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--heal-report", default="")
    ap.add_argument("--report-dir", default=str(runtime_temp_root() / "identity-heal-reports"))
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    stale_reasons: list[str] = []
    error_code = ""

    if args.heal_report.strip():
        heal_report_path = Path(args.heal_report).expanduser().resolve()
    else:
        latest = _latest_for_identity(Path(args.report_dir).expanduser().resolve(), args.identity_id)
        if latest is None:
            payload = {
                "identity_id": args.identity_id,
                "heal_report_path": "",
                "heal_replay_closure_status": "FAIL_REQUIRED",
                "error_code": ERR_MISSING,
                "stale_reasons": ["heal_report_not_found"],
            }
            return _emit(payload, args.json_only)
        heal_report_path = latest

    if not heal_report_path.exists():
        payload = {
            "identity_id": args.identity_id,
            "heal_report_path": str(heal_report_path),
            "heal_replay_closure_status": "FAIL_REQUIRED",
            "error_code": ERR_MISSING,
            "stale_reasons": ["heal_report_path_missing"],
        }
        return _emit(payload, args.json_only)

    try:
        heal_doc = _read_json(heal_report_path)
    except Exception:
        payload = {
            "identity_id": args.identity_id,
            "heal_report_path": str(heal_report_path),
            "heal_replay_closure_status": "FAIL_REQUIRED",
            "error_code": ERR_MISSING,
            "stale_reasons": ["heal_report_json_invalid"],
        }
        return _emit(payload, args.json_only)

    if str(heal_doc.get("identity_id", "")).strip() != args.identity_id:
        stale_reasons.append("heal_report_identity_mismatch")
        error_code = ERR_MISSING

    health_ref = str(heal_doc.get("health_report_ref", "")).strip()
    heal_ref = str(heal_doc.get("heal_report_ref", "")).strip()
    post_ref = str(heal_doc.get("post_validate_ref", "")).strip()
    if not health_ref or not heal_ref or not post_ref:
        stale_reasons.append("replay_refs_missing")
        error_code = error_code or ERR_MISSING

    health_path = Path(health_ref).expanduser().resolve() if health_ref else None
    heal_ref_path = Path(heal_ref).expanduser().resolve() if heal_ref else None
    post_path = Path(post_ref).expanduser().resolve() if post_ref else None

    if heal_ref_path and heal_ref_path != heal_report_path:
        stale_reasons.append("heal_report_ref_mismatch")
        error_code = error_code or ERR_REF_MISMATCH

    for tag, candidate in (("health_report_ref", health_path), ("post_validate_ref", post_path)):
        if candidate is None or not candidate.exists():
            stale_reasons.append(f"{tag}_path_missing")
            error_code = error_code or ERR_MISSING

    post_doc: dict[str, Any] = {}
    health_projection: dict[str, Any] = {}
    post_projection: dict[str, Any] = {}
    health_execution_report_ref = ""
    if health_path and health_path.exists():
        try:
            health_doc = _read_json(health_path)
        except Exception:
            stale_reasons.append("health_report_json_invalid")
            error_code = error_code or ERR_MISSING
            health_doc = {}
        if health_doc:
            health_execution_report_ref = _clean_str(health_doc.get("execution_report_ref"))
            health_projection = _closure_projection(
                health_doc,
                execution_report=health_execution_report_ref,
            )
            if not health_projection["status"] or not health_projection["validation_status"]:
                stale_reasons.append("health_report_experience_writeback_projection_missing")
                error_code = error_code or ERR_REF_MISMATCH
            if (
                health_projection.get("validation_status") == "PASS_REQUIRED"
                and not health_projection.get("report_selected_path")
            ):
                stale_reasons.append("health_report_experience_writeback_report_selected_path_missing")
                error_code = error_code or ERR_REF_MISMATCH
            if (
                health_projection.get("validation_status") == "PASS_REQUIRED"
                and health_execution_report_ref
                and not bool(
                    health_projection.get("report_selected_path_matches_execution_report")
                )
            ):
                stale_reasons.append(
                    "health_report_experience_writeback_selected_path_execution_report_ref_mismatch"
                )
                error_code = error_code or ERR_REF_MISMATCH
            if (
                health_projection.get("validation_status") == "PASS_REQUIRED"
                and (
                    not _clean_str(health_projection.get("report_selection_mode"))
                    or not _clean_str(health_projection.get("report_selected_authority_class"))
                    or not _clean_str(health_projection.get("report_pointer_resolution_mode"))
                )
            ):
                stale_reasons.append("health_report_experience_writeback_authority_projection_missing")
                error_code = error_code or ERR_REF_MISMATCH
    if post_path and post_path.exists():
        try:
            post_doc = _read_json(post_path)
        except Exception:
            stale_reasons.append("post_validate_report_json_invalid")
            error_code = error_code or ERR_POST_VALIDATE
    if post_doc:
        post_status = str(post_doc.get("overall_status", "")).strip().upper()
        post_projection = _closure_projection(post_doc)
        if not post_projection["status"] or not post_projection["validation_status"]:
            stale_reasons.append("post_validate_experience_writeback_projection_missing")
            error_code = error_code or ERR_POST_VALIDATE
        if (
            post_projection.get("validation_status") == "PASS_REQUIRED"
            and not _clean_str(post_projection.get("report_selected_path"))
        ):
            stale_reasons.append("post_validate_experience_writeback_report_selected_path_missing")
            error_code = error_code or ERR_POST_VALIDATE
        if (
            post_projection.get("validation_status") == "PASS_REQUIRED"
            and (
                not _clean_str(post_projection.get("report_selection_mode"))
                or not _clean_str(post_projection.get("report_selected_authority_class"))
                or not _clean_str(post_projection.get("report_pointer_resolution_mode"))
            )
        ):
            stale_reasons.append("post_validate_experience_writeback_authority_projection_missing")
            error_code = error_code or ERR_POST_VALIDATE
        if post_status == "FAIL":
            stale_reasons.append("post_validate_health_still_fail")
            error_code = error_code or ERR_POST_VALIDATE
        if post_projection.get("status") == "FAIL" or post_projection.get("validation_status") == "FAIL_REQUIRED":
            stale_reasons.append("post_validate_experience_writeback_still_fail")
            error_code = error_code or ERR_POST_VALIDATE
        # actor-risk closure requires no FAIL rows in actor-risk quartet
        for field in (
            "actor_binding_integrity",
            "actor_lease_freshness",
            "implicit_switch_guard",
            "pointer_drift_guard",
        ):
            row = post_doc.get(field)
            if isinstance(row, dict) and str(row.get("status", "")).strip().upper() == "FAIL":
                stale_reasons.append(f"{field}_still_fail_after_heal")
                error_code = error_code or ERR_POST_VALIDATE

    ok = not stale_reasons
    payload = {
        "identity_id": args.identity_id,
        "heal_report_path": str(heal_report_path),
        "health_report_ref": health_ref,
        "heal_report_ref": heal_ref,
        "post_validate_ref": post_ref,
        "health_report_experience_writeback_closure_status": health_projection.get("status", ""),
        "health_report_experience_writeback_validation_status": health_projection.get("validation_status", ""),
        "health_report_execution_report_ref": health_execution_report_ref,
        "health_report_experience_writeback_report_selected_path": health_projection.get(
            "report_selected_path", ""
        ),
        "health_report_experience_writeback_selected_path_matches_execution_report_ref": bool(
            health_projection.get("report_selected_path_matches_execution_report")
        ),
        "health_report_experience_writeback_report_selection_mode": health_projection.get(
            "report_selection_mode", ""
        ),
        "health_report_experience_writeback_report_selected_authority_class": health_projection.get(
            "report_selected_authority_class", ""
        ),
        "health_report_experience_writeback_report_pointer_resolution_mode": health_projection.get(
            "report_pointer_resolution_mode", ""
        ),
        "health_report_experience_writeback_writeback_status": health_projection.get(
            "writeback_status", ""
        ),
        "health_report_experience_writeback_writeback_rule_id": health_projection.get(
            "writeback_rule_id", ""
        ),
        "post_validate_experience_writeback_closure_status": post_projection.get("status", ""),
        "post_validate_experience_writeback_validation_status": post_projection.get("validation_status", ""),
        "post_validate_experience_writeback_report_selected_path": post_projection.get(
            "report_selected_path", ""
        ),
        "post_validate_experience_writeback_report_selection_mode": post_projection.get(
            "report_selection_mode", ""
        ),
        "post_validate_experience_writeback_report_selected_authority_class": post_projection.get(
            "report_selected_authority_class", ""
        ),
        "post_validate_experience_writeback_report_pointer_resolution_mode": post_projection.get(
            "report_pointer_resolution_mode", ""
        ),
        "post_validate_experience_writeback_writeback_status": post_projection.get(
            "writeback_status", ""
        ),
        "post_validate_experience_writeback_writeback_rule_id": post_projection.get(
            "writeback_rule_id", ""
        ),
        "heal_replay_closure_status": "PASS_REQUIRED" if ok else "FAIL_REQUIRED",
        "error_code": "" if ok else error_code,
        "stale_reasons": stale_reasons,
    }
    return _emit(payload, args.json_only)


if __name__ == "__main__":
    raise SystemExit(main())
