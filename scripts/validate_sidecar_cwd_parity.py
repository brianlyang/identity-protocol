#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from protocol_feedback_sidecar_projection_common import (
    build_protocol_feedback_sidecar_passthrough_projection,
)
from runtime_temp_path_common import runtime_temp_dir
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SIDECAR_EXEC_FAIL = "IP-SIDECWD-001"
ERR_PARITY_MISMATCH = "IP-SIDECWD-002"
ERR_REQUIRED_PAYLOAD_MISSING = "IP-SIDECWD-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "sidecar_cwd_invariance_contract_v1",
        "sidecar_cwd_invariance_contract",
        "rq_005_sidecar_cwd_invariance_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _passthrough_digest(payload: dict[str, Any]) -> str:
    stable = build_protocol_feedback_sidecar_passthrough_projection(payload)
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _run_sidecar_validator(*, cwd: Path, catalog: Path, repo_catalog: Path, identity_id: str, operation: str) -> tuple[int, str, str, dict[str, Any]]:
    cmd = [
        "python3",
        str((Path(__file__).resolve().parent / "validate_protocol_feedback_sidecar_contract.py").resolve()),
        "--catalog",
        str(catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--json-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))
    payload = _parse_json_payload(proc.stdout)
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip(), payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate sidecar passthrough/cwd invariance contract (RQ-005).")
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
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "repo_catalog_path": str(repo_catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "sidecar_cwd_parity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "cwd_parity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "passthrough_digest": "",
        "root_digest": "",
        "temp_digest": "",
        "sidecar_contract_status": "",
        "sidecar_error_code": "",
        "error_code": "",
        "root_validator_rc": 0,
        "temp_validator_rc": 0,
        "root_validator_tail": "",
        "temp_validator_tail": "",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    repo_root = Path(__file__).resolve().parent.parent
    temp_root = runtime_temp_dir(channel="sidecar-cwd-parity", operation=args.operation, identity_id=args.identity_id)
    rc_root, out_root, err_root, root_doc = _run_sidecar_validator(
        cwd=repo_root,
        catalog=catalog_path,
        repo_catalog=repo_catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )
    rc_tmp, out_tmp, err_tmp, tmp_doc = _run_sidecar_validator(
        cwd=temp_root,
        catalog=catalog_path,
        repo_catalog=repo_catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )

    payload["root_validator_rc"] = rc_root
    payload["temp_validator_rc"] = rc_tmp
    payload["root_validator_tail"] = out_root.splitlines()[-1] if out_root else (err_root.splitlines()[-1] if err_root else "")
    payload["temp_validator_tail"] = out_tmp.splitlines()[-1] if out_tmp else (err_tmp.splitlines()[-1] if err_tmp else "")
    payload["sidecar_contract_status"] = str(root_doc.get("sidecar_contract_status", "")).strip()
    payload["sidecar_error_code"] = str(root_doc.get("sidecar_error_code", "")).strip()
    payload["producer_readiness"] = bool(root_doc)
    payload["evidence_ref"] = str(root_doc.get("evidence_ref", "")) if isinstance(root_doc, dict) else ""
    linked = bool(root_doc.get("requiredization_current_round_linked", False)) or bool(
        tmp_doc.get("requiredization_current_round_linked", False)
    )
    payload["requiredization_current_round_linked"] = linked

    if not root_doc or not tmp_doc:
        payload["sidecar_cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_PAYLOAD_MISSING
        payload["stale_reasons"] = ["sidecar_payload_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if not linked:
        payload["sidecar_cwd_parity_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["cwd_parity_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["required_contract_not_applicable_current_round_unlinked"]
        _emit(payload, json_only=args.json_only)
        return 0

    if rc_root != 0 or rc_tmp != 0:
        payload["sidecar_cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SIDECAR_EXEC_FAIL
        payload["stale_reasons"] = ["sidecar_validator_execution_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    root_digest = _passthrough_digest(root_doc)
    tmp_digest = _passthrough_digest(tmp_doc)
    payload["root_digest"] = root_digest
    payload["temp_digest"] = tmp_digest
    payload["passthrough_digest"] = root_digest

    if root_digest != tmp_digest:
        payload["sidecar_cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["cwd_parity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PARITY_MISMATCH
        payload["stale_reasons"] = ["root_temp_digest_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["sidecar_cwd_parity_status"] = STATUS_PASS_REQUIRED
    payload["cwd_parity_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
