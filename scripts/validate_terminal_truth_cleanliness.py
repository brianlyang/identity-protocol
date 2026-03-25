#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from terminal_truth_cleanliness_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    TERMINAL_TRUTH_CLEANLINESS_CONTRACT_KEY,
    TERMINAL_TRUTH_CLEANLINESS_CONTRACT_ID,
    TERMINAL_TRUTH_CLEANLINESS_VALIDATOR_ID,
    clean_string,
    derive_terminal_state_projection,
    derive_terminal_truth_projection,
    resolve_pack_task,
    resolve_terminal_truth_cleanliness_contract,
    terminal_truth_cleanliness_contract_issues,
)
from tool_vendor_governance_common import latest_identity_upgrade_report, load_json

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ERR_CONTRACT = "IP-TTC-001"
ERR_RUNTIME = "IP-TTC-002"
STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection", "status"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = clean_string(raw)
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


def _resolve_report(identity_id: str, pack_root: Path, explicit: str) -> Path | None:
    if clean_string(explicit):
        path = Path(clean_string(explicit)).expanduser().resolve()
        return path if path.exists() else None
    return latest_identity_upgrade_report(identity_id, pack_root)


def _run_support_validator(cmd: list[str], *, status_field: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    payload = _parse_json_payload(proc.stdout or "") or {}
    status = clean_string(payload.get(status_field)).upper()
    if not status:
        status = STATUS_PASS_REQUIRED if proc.returncode == 0 else STATUS_FAIL_REQUIRED
    return {
        "cmd": cmd,
        "rc": proc.returncode,
        "status": status,
        "payload": payload,
        "stdout_tail": (proc.stdout or "")[-400:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate clean terminal truth and negative-feedback veto semantics.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--current-task", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "mutation", "scan", "three-plane", "inspection", "status"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--skip-support-validators", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve() if clean_string(args.catalog) else None
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path else "",
        "current_task": clean_string(args.current_task),
        "operation": args.operation,
        "resolved_pack_path": "",
        "resolved_task_path": "",
        "required_contract": False,
        "contract_key": TERMINAL_TRUTH_CLEANLINESS_CONTRACT_KEY,
        "terminal_truth_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_state_machine_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_state_class": "",
        "terminal_state_basis": "",
        "terminal_state_conflict_status": STATUS_SKIPPED_NOT_REQUIRED,
        "state_machine_blockers": [],
        "terminal_clean_alias_surface_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_clean_alias_claimed": False,
        "terminal_clean_alias_claims": [],
        "terminal_clean_alias_blockers": [],
        "identity_terminal_truth_cleanliness_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "report_selected_path": "",
        "post_execution_mandatory_status": STATUS_SKIPPED_NOT_REQUIRED,
        "writeback_continuity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "support_validator_mode": "skipped" if args.skip_support_validators else "required",
        "stale_reasons": [],
    }

    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=args.current_task,
            identity_id=args.identity_id,
        )
    except Exception as exc:
        payload.update(
            {
                "identity_terminal_truth_cleanliness_status": STATUS_FAIL_REQUIRED,
                "terminal_truth_contract_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_CONTRACT,
                "stale_reasons": [f"pack_task_resolution_failed:{exc}"],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    payload["resolved_pack_path"] = str(pack_root)
    payload["resolved_task_path"] = str(task_path)

    required_contract, contract_doc, contract_key = resolve_terminal_truth_cleanliness_contract(task_doc)
    if args.force_required:
        required_contract = True
    payload["required_contract"] = required_contract
    payload["contract_key"] = contract_key
    contract_issues = terminal_truth_cleanliness_contract_issues(contract_doc)
    payload["contract_issues"] = contract_issues
    payload["terminal_truth_contract_status"] = STATUS_PASS_REQUIRED if required_contract and not contract_issues else STATUS_FAIL_REQUIRED

    if not required_contract:
        payload.update(
            {
                "identity_terminal_truth_cleanliness_status": STATUS_SKIPPED_NOT_REQUIRED,
                "terminal_truth_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
                "stale_reasons": ["contract_not_required"],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 0

    if contract_issues:
        payload.update(
            {
                "identity_terminal_truth_cleanliness_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_CONTRACT,
                "stale_reasons": [f"contract_issue:{issue}" for issue in contract_issues],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    report_path = _resolve_report(args.identity_id, pack_root, args.report)
    if report_path is None:
        payload["error_code"] = ERR_RUNTIME
        payload["stale_reasons"] = [
            "required_contract_not_applicable_no_current_round_evidence_source"
            if args.operation in INSPECTION_OPERATIONS
            else "execution_report_not_found"
        ]
        if args.operation in INSPECTION_OPERATIONS:
            payload["identity_terminal_truth_cleanliness_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["identity_terminal_truth_cleanliness_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["report_selected_path"] = str(report_path)
    try:
        report_doc = load_json(report_path)
    except Exception as exc:
        payload.update(
            {
                "identity_terminal_truth_cleanliness_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_RUNTIME,
                "stale_reasons": [f"execution_report_invalid_json:{exc}"],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    support_results: dict[str, dict[str, Any]] = {}
    if not args.skip_support_validators and catalog_path is not None:
        support_results["post_execution_mandatory"] = _run_support_validator(
            [
                "python3",
                "scripts/validate_post_execution_mandatory.py",
                "--catalog",
                str(catalog_path),
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--report",
                str(report_path),
                "--operation",
                args.operation,
                "--json-only",
            ],
            status_field="post_execution_mandatory_status",
        )
        support_results["writeback_continuity"] = _run_support_validator(
            [
                "python3",
                "scripts/validate_writeback_continuity.py",
                "--catalog",
                str(catalog_path),
                "--repo-catalog",
                args.repo_catalog,
                "--identity-id",
                args.identity_id,
                "--report",
                str(report_path),
                "--operation",
                args.operation,
                "--json-only",
            ],
            status_field="writeback_continuity_status",
        )
        payload["post_execution_mandatory_status"] = support_results["post_execution_mandatory"]["status"]
        payload["writeback_continuity_status"] = support_results["writeback_continuity"]["status"]
    else:
        payload["support_validator_mode"] = "skipped"

    support_post_status = payload.get("post_execution_mandatory_status", "") if support_results else ""
    support_writeback_status = payload.get("writeback_continuity_status", "") if support_results else ""
    projection = derive_terminal_truth_projection(
        report_doc,
        post_execution_status=support_post_status,
        writeback_continuity_status=support_writeback_status,
    )
    state_projection = derive_terminal_state_projection(
        report_doc,
        terminal_truth_projection=projection,
    )
    payload.update(projection)
    payload.update(state_projection)
    payload["terminal_truth_contract_id"] = TERMINAL_TRUTH_CLEANLINESS_CONTRACT_ID
    payload["validator_id"] = TERMINAL_TRUTH_CLEANLINESS_VALIDATOR_ID
    if support_results:
        payload["support_validators"] = support_results

    if payload.get("identity_terminal_truth_cleanliness_status") != STATUS_PASS_REQUIRED and not payload.get("error_code"):
        payload["error_code"] = ERR_RUNTIME

    rc = 0 if payload.get("identity_terminal_truth_cleanliness_status") == STATUS_PASS_REQUIRED else 1
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
