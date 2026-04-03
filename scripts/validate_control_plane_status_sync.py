#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from repo_root_resolution_common import resolve_repo_root
from typing import Any

import yaml

from render_control_plane_status import (
    STATUS_FAIL_REQUIRED as CONTROL_PLANE_STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED as CONTROL_PLANE_STATUS_PASS_REQUIRED,
    STATUS_PASS_WITH_BLOCKERS as CONTROL_PLANE_STATUS_PASS_WITH_BLOCKERS,
    STATUS_WARN_NON_BLOCKING as CONTROL_PLANE_STATUS_WARN_NON_BLOCKING,
    build_status,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STATUS_SYNC = "IP-CP-STATUS-001"

VOLATILE_TOP_LEVEL_KEYS = {"generated_at_utc", "git_head_short"}
VOLATILE_PAYLOAD_KEY_SUFFIXES = (
    "_path",
    "_file",
    "_entry",
    "_ref",
    "_sha",
)
VOLATILE_PAYLOAD_KEY_TOKENS = (
    "timestamp",
    "generated_at",
    "current_last_updated_utc",
    "live_last_updated_utc",
    "stdout_tail",
    "stderr_tail",
    "catalog_path",
    "pack_path",
    "resolved_pack_path",
    "task_path",
    "status_file",
    "status_entry_file",
    "status_file_entry",
    "current_file",
    "resolved_file",
    "active_file",
    "configured_file",
    "workflow_file_sha",
    "run_workflow_file_sha",
    "run_url",
    "evidence_ref",
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _canonicalize(doc: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in doc.items() if k not in VOLATILE_TOP_LEVEL_KEYS}
    return out


def _index_checks(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = doc.get("checks")
    if not isinstance(checks, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for node in checks:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name", "")).strip()
        if not name:
            continue
        out[name] = node
    return out


def _derive_filtered_overall_status(checks: list[dict[str, Any]]) -> tuple[str, bool, list[str]]:
    statuses = [str(item.get("status", "")).strip() for item in checks]
    reasons: list[str] = []
    if any(status == CONTROL_PLANE_STATUS_FAIL_REQUIRED for status in statuses):
        for item in checks:
            if item.get("status") == CONTROL_PLANE_STATUS_FAIL_REQUIRED:
                reasons.append(f"{item.get('name')}:FAIL_REQUIRED")
        return CONTROL_PLANE_STATUS_FAIL_REQUIRED, False, reasons
    if any(status == CONTROL_PLANE_STATUS_WARN_NON_BLOCKING for status in statuses):
        for item in checks:
            if item.get("status") == CONTROL_PLANE_STATUS_WARN_NON_BLOCKING:
                reasons.append(f"{item.get('name')}:WARN_NON_BLOCKING")
        return CONTROL_PLANE_STATUS_PASS_WITH_BLOCKERS, False, reasons
    return CONTROL_PLANE_STATUS_PASS_REQUIRED, True, reasons


def _filter_doc_to_check_subset(doc: dict[str, Any], check_names: tuple[str, ...]) -> dict[str, Any]:
    if not check_names:
        return doc
    include_set = set(check_names)
    filtered = dict(doc)
    checks = [row for row in (doc.get("checks") or []) if isinstance(row, dict) and str(row.get("name", "")).strip() in include_set]
    overall_status, promotion_ready, reasons = _derive_filtered_overall_status(checks)
    filtered["checks"] = checks
    filtered["summary"] = {
        "check_count": len(checks),
        "fail_count": sum(1 for row in checks if row.get("status") == CONTROL_PLANE_STATUS_FAIL_REQUIRED),
        "warn_count": sum(1 for row in checks if row.get("status") == CONTROL_PLANE_STATUS_WARN_NON_BLOCKING),
        "pass_count": sum(1 for row in checks if row.get("status") == CONTROL_PLANE_STATUS_PASS_REQUIRED),
    }
    filtered["control_plane_status"] = overall_status
    filtered["promotion_ready"] = promotion_ready
    filtered["promotion_block_reasons"] = reasons
    filtered["selected_check_names"] = list(check_names)
    return filtered


def _is_volatile_payload_key(key: str) -> bool:
    lowered = key.strip().lower()
    if not lowered:
        return False
    if any(lowered.endswith(suffix) for suffix in VOLATILE_PAYLOAD_KEY_SUFFIXES):
        return True
    if any(token in lowered for token in VOLATILE_PAYLOAD_KEY_TOKENS):
        return True
    return False


def _canonicalize_payload(value: Any, repo_root: Path) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, node in value.items():
            key_str = str(key)
            if _is_volatile_payload_key(key_str):
                continue
            normalized[key_str] = _canonicalize_payload(node, repo_root)
        return normalized
    if isinstance(value, list):
        return [_canonicalize_payload(item, repo_root) for item in value]
    if isinstance(value, str):
        text = value
        repo_root_text = str(repo_root)
        if repo_root_text:
            text = text.replace(repo_root_text, "${REPO_ROOT}")
        text = re.sub(r"/home/runner/work/[^/\s]+/[^/\s]+", "${REPO_ROOT}", text)
        text = re.sub(
            r"/Users/[^/\s]+/claude/codex_project/[^/\s]+/identity-protocol-local",
            "${REPO_ROOT}",
            text,
        )
        return text
    return value


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate machine-generated control-plane status artifact is in sync.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument(
        "--status-file",
        default="identity/protocol/mappings/control-plane-status.current.yaml",
    )
    parser.add_argument("--check-name", action="append", default=[])
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    selected_check_names = tuple(
        str(name).strip() for name in (args.check_name or []) if str(name).strip()
    )

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    status_entry_path = (repo_root / str(args.status_file)).resolve()
    status_path, status_active_file, status_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.status_file)
    )
    stale_reasons: list[str] = []
    mismatches: list[dict[str, Any]] = []

    if not status_entry_path.exists():
        stale_reasons.append(f"status_entry_file_missing:{status_entry_path}")
        current_doc: dict[str, Any] = {}
    elif status_alias_error:
        stale_reasons.append(f"status_file_alias_error:{status_alias_error}:{status_active_file}")
        current_doc = {}
    elif not status_path.exists():
        stale_reasons.append(f"status_file_missing:{status_path}")
        current_doc: dict[str, Any] = {}
    else:
        current_doc = _load_json(status_path)

    live_doc = build_status(repo_root, include_check_names=selected_check_names)
    current_doc = _filter_doc_to_check_subset(current_doc, selected_check_names)
    current_norm = _canonicalize(current_doc)
    live_norm = _canonicalize(live_doc)

    if current_doc:
        if current_norm.get("summary") != live_norm.get("summary"):
            mismatches.append(
                {
                    "field": "summary",
                    "reason": "summary_drift",
                }
            )
        if current_norm.get("promotion_block_reasons") != live_norm.get("promotion_block_reasons"):
            mismatches.append(
                {
                    "field": "promotion_block_reasons",
                    "reason": "promotion_block_reasons_drift",
                }
            )
        if current_norm.get("selected_check_names") != live_norm.get("selected_check_names"):
            mismatches.append(
                {
                    "field": "selected_check_names",
                    "reason": "selected_check_scope_drift",
                }
            )
        if current_norm.get("control_plane_status") != live_norm.get("control_plane_status"):
            mismatches.append(
                {
                    "field": "control_plane_status",
                    "expected": live_norm.get("control_plane_status"),
                    "actual": current_norm.get("control_plane_status"),
                    "reason": "status_drift",
                }
            )
        if bool(current_norm.get("promotion_ready")) != bool(live_norm.get("promotion_ready")):
            mismatches.append(
                {
                    "field": "promotion_ready",
                    "expected": bool(live_norm.get("promotion_ready")),
                    "actual": bool(current_norm.get("promotion_ready")),
                    "reason": "promotion_flag_drift",
                }
            )

        current_checks = _index_checks(current_norm)
        live_checks = _index_checks(live_norm)
        if set(current_checks.keys()) != set(live_checks.keys()):
            mismatches.append(
                {
                    "field": "checks.name_set",
                    "expected": sorted(live_checks.keys()),
                    "actual": sorted(current_checks.keys()),
                    "reason": "check_set_drift",
                }
            )
        for name in sorted(set(current_checks.keys()) & set(live_checks.keys())):
            current_check = current_checks[name]
            live_check = live_checks[name]
            for key in ("status", "error_code", "rc"):
                if current_check.get(key) != live_check.get(key):
                    mismatches.append(
                        {
                            "field": f"checks.{name}.{key}",
                            "expected": live_check.get(key),
                            "actual": current_check.get(key),
                            "reason": "check_result_drift",
                        }
                    )
            current_payload = _canonicalize_payload(current_check.get("payload"), repo_root)
            live_payload = _canonicalize_payload(live_check.get("payload"), repo_root)
            if current_payload != live_payload:
                mismatches.append(
                    {
                        "field": f"checks.{name}.payload",
                        "reason": "check_payload_drift",
                    }
                )

    if stale_reasons or mismatches:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_STATUS_SYNC
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "control_plane_status_sync_status": status,
        "error_code": error_code,
        "status_entry_file": str(status_entry_path),
        "status_file": str(status_path),
        "status_active_file": status_active_file,
        "status_file_alias_error": status_alias_error,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "stale_reasons": stale_reasons,
        "live_control_plane_status": live_norm.get("control_plane_status"),
        "file_control_plane_status": current_norm.get("control_plane_status"),
        "selected_check_names": list(selected_check_names),
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-STATUS-SYNC] status={status} "
            f"mismatches={len(mismatches)} "
            f"stale={len(stale_reasons)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
