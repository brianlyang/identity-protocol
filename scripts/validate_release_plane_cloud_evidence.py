#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_EVIDENCE_MISSING = "IP-RCLOUD-001"
ERR_VALIDATOR_EXEC_FAILED = "IP-RCLOUD-002"
ERR_CONDITION_FAILED = "IP-RCLOUD-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "release_plane_cloud_evidence_contract_v1",
        "release_plane_cloud_evidence_contract",
        "rq_006_release_plane_cloud_evidence_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _parse_json(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate release-plane cloud evidence contract (RQ-006).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--workflow-file-sha", default="")
    ap.add_argument("--run-head-sha", default="")
    ap.add_argument("--run-workflow-file-sha", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    target_branch = str(args.target_branch or contract.get("target_branch", "")).strip()
    release_head_sha = str(args.release_head_sha or contract.get("release_head_sha", "")).strip()
    required_gates_run_id = str(args.required_gates_run_id or contract.get("required_gates_run_id", "")).strip()
    run_url = str(args.run_url or contract.get("run_url", "")).strip()
    workflow_file_sha = str(args.workflow_file_sha or contract.get("workflow_file_sha", "")).strip()
    run_head_sha = str(args.run_head_sha or contract.get("run_head_sha", "")).strip()
    run_workflow_file_sha = str(args.run_workflow_file_sha or contract.get("run_workflow_file_sha", "")).strip()
    checks_json = str(args.checks_json or contract.get("checks_json", "")).strip()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "release_plane_cloud_evidence_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "release_plane_status": "",
        "conditions": {},
        "target_branch": target_branch,
        "release_head_sha": release_head_sha,
        "required_gates_run_id": required_gates_run_id,
        "run_url": run_url,
        "workflow_file_sha": workflow_file_sha,
        "run_head_sha": run_head_sha,
        "run_workflow_file_sha": run_workflow_file_sha,
        "checks_json": checks_json,
        "evidence_ref": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    linked = bool(target_branch and release_head_sha and required_gates_run_id and run_url and workflow_file_sha and run_head_sha and run_workflow_file_sha)
    payload["requiredization_current_round_linked"] = linked
    if not linked:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_missing_release_evidence"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["release_plane_cloud_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_EVIDENCE_MISSING
        payload["stale_reasons"] = ["release_plane_evidence_missing_required_fields"]
        _emit(payload, json_only=args.json_only)
        return 1

    cmd = [
        "python3",
        "scripts/validate_release_plane_cloud_closure.py",
        "--target-branch",
        target_branch,
        "--release-head-sha",
        release_head_sha,
        "--required-gates-run-id",
        required_gates_run_id,
        "--run-url",
        run_url,
        "--workflow-file-sha",
        workflow_file_sha,
        "--run-head-sha",
        run_head_sha,
        "--run-workflow-file-sha",
        run_workflow_file_sha,
    ]
    if checks_json:
        cmd += ["--checks-json", checks_json]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    detail = _parse_json(proc.stdout)
    payload["producer_readiness"] = bool(detail)
    payload["evidence_ref"] = checks_json or run_url
    payload["conditions"] = detail.get("conditions", {}) if isinstance(detail.get("conditions"), dict) else {}
    payload["release_plane_status"] = str(detail.get("release_plane_status", "")).strip()

    if proc.returncode != 0:
        payload["release_plane_cloud_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_VALIDATOR_EXEC_FAILED if not detail else ERR_CONDITION_FAILED
        payload["stale_reasons"] = ["release_plane_condition_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["release_plane_cloud_evidence_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
