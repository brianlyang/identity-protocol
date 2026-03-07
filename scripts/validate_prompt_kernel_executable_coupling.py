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

ERR_ACTOR_REQUIRED = "IP-PKX-001"
ERR_ROUTING_VALIDATOR_FAILED = "IP-PKX-002"
ERR_KERNEL_REF_MISSING = "IP-PKX-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "prompt_import_executable_coupling_contract_v1",
        "prompt_import_executable_coupling_contract",
        "rq_031_prompt_import_executable_coupling_contract_v1",
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
    ap = argparse.ArgumentParser(description="Validate prompt import executable coupling contract (RQ-031).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--source-layer", default="")
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

    kernel_contract_ref = str(contract.get("kernel_contract_ref", "")).strip() or "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md#rq_031_prompt_import_executable_coupling_contract_v1"
    validator_ref = str(contract.get("validator_ref", "")).strip() or "scripts/validate_work_layer_gate_set_routing.py"
    require_actor = bool(contract.get("require_explicit_actor", True))
    actor_id = str(args.actor_id or "").strip()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": True,
        "prompt_kernel_executable_coupling_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "kernel_contract_ref": kernel_contract_ref,
        "validator_ref": validator_ref,
        "evidence_ref": "",
        "actor_context_explicit": bool(actor_id),
        "routing_validator_rc": 0,
        "routing_validator_tail": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    kernel_path = kernel_contract_ref.split("#", 1)[0]
    if not kernel_path:
        payload["prompt_kernel_executable_coupling_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_KERNEL_REF_MISSING
        payload["stale_reasons"] = ["kernel_contract_ref_missing"]
        _emit(payload, json_only=args.json_only)
        return 1
    if not Path(kernel_path).expanduser().resolve().exists():
        payload["prompt_kernel_executable_coupling_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_KERNEL_REF_MISSING
        payload["stale_reasons"] = ["kernel_contract_ref_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    if require_actor and args.operation in STRICT_OPERATIONS and not actor_id:
        payload["prompt_kernel_executable_coupling_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ACTOR_REQUIRED
        payload["stale_reasons"] = ["actor_id_required_for_strict_operation"]
        _emit(payload, json_only=args.json_only)
        return 1

    cmd = [
        "python3",
        "scripts/validate_work_layer_gate_set_routing.py",
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(Path(args.repo_catalog).expanduser().resolve()),
        "--identity-id",
        args.identity_id,
        "--operation",
        args.operation,
        "--source-layer",
        str(args.source_layer or "project"),
        "--json-only",
    ]
    if actor_id:
        cmd += ["--actor-id", actor_id]
    if str(args.expected_work_layer or "").strip():
        cmd += ["--expected-work-layer", str(args.expected_work_layer).strip()]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    detail = _parse_json(proc.stdout)
    payload["producer_readiness"] = bool(detail)
    payload["routing_validator_rc"] = proc.returncode
    payload["routing_validator_tail"] = (proc.stdout or proc.stderr or "").strip().splitlines()[-1] if (proc.stdout or proc.stderr) else ""
    payload["evidence_ref"] = str(detail.get("evidence_ref", "")).strip()

    if proc.returncode != 0:
        payload["prompt_kernel_executable_coupling_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ROUTING_VALIDATOR_FAILED
        payload["stale_reasons"] = ["work_layer_gate_set_routing_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["prompt_kernel_executable_coupling_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
