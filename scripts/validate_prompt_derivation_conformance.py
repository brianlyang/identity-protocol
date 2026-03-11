#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_PROMPT_MISSING = "IP-PDER-001"
ERR_KERNEL_MISSING = "IP-PDER-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "derived_prompt_conformance_contract_v1",
        "derived_prompt_conformance_contract",
        "rq_027_derived_prompt_conformance_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate derived prompt conformance contract (RQ-027).")
    ap.add_argument("--catalog", required=True)
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

    repo_root = Path(__file__).resolve().parent.parent
    kernel_contract_path = (repo_root / "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md").resolve()
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": kernel_contract_path.exists() and prompt_path.exists(),
        "requiredization_current_round_linked": prompt_path.exists(),
        "prompt_derivation_conformance_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "kernel_contract_path": str(kernel_contract_path),
        "prompt_path": str(prompt_path),
        "kernel_contract_version": str(contract.get("kernel_contract_version", "")).strip() or "v1.6",
        "kernel_contract_digest": "",
        "derived_from_contract_ids": contract.get("derived_from_contract_ids", []) if isinstance(contract.get("derived_from_contract_ids"), list) else [],
        "overlay_digest": "",
        "evidence_ref": str(prompt_path) if prompt_path.exists() else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not kernel_contract_path.exists():
        payload["prompt_derivation_conformance_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_KERNEL_MISSING
        payload["stale_reasons"] = ["kernel_prompt_bootstrap_contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1
    if not prompt_path.exists():
        payload["prompt_derivation_conformance_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PROMPT_MISSING
        payload["stale_reasons"] = ["identity_prompt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["kernel_contract_digest"] = _sha256(kernel_contract_path)
    payload["overlay_digest"] = _sha256(prompt_path)
    if not payload["derived_from_contract_ids"]:
        payload["derived_from_contract_ids"] = [
            "rq_014_prompt_bootstrap_capability_contract_v1",
            "rq_015_prompt_capability_matrix_fail_closed_contract_v1",
        ]
    payload["prompt_derivation_conformance_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
