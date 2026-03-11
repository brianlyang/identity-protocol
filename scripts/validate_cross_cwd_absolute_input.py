#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime_temp_path_common import runtime_temp_dir
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_ABSOLUTE_REQUIRED = "IP-CWD-004"
ERR_PATH_MISSING = "IP-CWD-003"
ERR_PARITY_MISMATCH = "IP-CWD-005"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "cross_cwd_absolute_input_contract_v1",
        "cross_cwd_absolute_input_contract",
        "rq_007_cross_cwd_absolute_input_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _resolve_from(base: Path, target: str) -> Path:
    value = str(target or "").strip()
    if not value:
        return Path("")
    p = Path(value).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (base / p).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate cross-cwd absolute-input contract (RQ-007).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
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

    repo_catalog_input = str(args.repo_catalog).strip()
    repo_root = Path(__file__).resolve().parent.parent
    tmp_root = runtime_temp_dir(channel="cross-cwd-absolute-input", operation=args.operation, identity_id=args.identity_id)
    repo_resolved = _resolve_from(repo_root, repo_catalog_input)
    tmp_resolved = _resolve_from(tmp_root, repo_catalog_input)

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
        "cross_cwd_absolute_input_status": STATUS_SKIPPED_NOT_REQUIRED,
        "cwd_parity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "repo_catalog_input": repo_catalog_input,
        "repo_catalog_is_absolute": bool(Path(repo_catalog_input).expanduser().is_absolute()) if repo_catalog_input else False,
        "repo_cwd_resolved_repo_catalog": str(repo_resolved) if str(repo_resolved) else "",
        "tmp_cwd_resolved_repo_catalog": str(tmp_resolved) if str(tmp_resolved) else "",
        "repo_catalog_exists": bool(repo_resolved.exists()) if str(repo_resolved) else False,
        "evidence_ref": str(repo_resolved) if str(repo_resolved) else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    linked = bool(repo_catalog_input)
    payload["requiredization_current_round_linked"] = linked
    if not linked:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_repo_catalog_input"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["cross_cwd_absolute_input_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ABSOLUTE_REQUIRED
        payload["stale_reasons"] = ["repo_catalog_input_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["producer_readiness"] = True

    if not Path(repo_catalog_input).expanduser().is_absolute():
        payload["cross_cwd_absolute_input_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ABSOLUTE_REQUIRED
        payload["stale_reasons"] = ["repo_catalog_not_absolute"]
        _emit(payload, json_only=args.json_only)
        return 1

    if not repo_resolved.exists():
        payload["cross_cwd_absolute_input_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PATH_MISSING
        payload["stale_reasons"] = ["repo_catalog_path_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if repo_resolved != tmp_resolved:
        payload["cross_cwd_absolute_input_status"] = STATUS_FAIL_REQUIRED
        payload["cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PARITY_MISMATCH
        payload["stale_reasons"] = ["root_tmp_resolution_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["cwd_parity_status"] = STATUS_PASS_REQUIRED
    payload["cross_cwd_absolute_input_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
