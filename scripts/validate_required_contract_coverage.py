#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import (
    contract_required,
    load_json,
    resolve_pack_and_task,
    resolve_report_path,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"

REASON_PASS = "IP-COV-000"
REASON_SKIPPED = "IP-COV-001"
REASON_FAIL = "IP-COV-999"

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")
STATUS_FIELD_BY_SCRIPT = {
    "scripts/validate_semantic_routing_guard.py": "semantic_routing_status",
    "scripts/validate_instance_protocol_split_receipt.py": "instance_protocol_split_status",
    "scripts/validate_vendor_namespace_separation.py": "vendor_namespace_status",
    "scripts/validate_protocol_feedback_sidecar_contract.py": "sidecar_contract_status",
}


@dataclass
class ContractTarget:
    name: str
    contract_keys: tuple[str, ...]
    validator_script: str
    validator_args: tuple[str, ...] = ()


TARGETS = (
    ContractTarget(
        name="tool_installation",
        contract_keys=("tool_installation_contract",),
        validator_script="scripts/validate_identity_tool_installation.py",
    ),
    ContractTarget(
        name="vendor_api_discovery",
        contract_keys=("vendor_api_discovery_contract",),
        validator_script="scripts/validate_identity_vendor_api_discovery.py",
    ),
    ContractTarget(
        name="vendor_api_solution",
        contract_keys=("vendor_api_solution_contract",),
        validator_script="scripts/validate_identity_vendor_api_solution.py",
    ),
    ContractTarget(
        name="semantic_routing_guard",
        contract_keys=("semantic_routing_guard_contract_v1", "semantic_routing_guard_contract"),
        validator_script="scripts/validate_semantic_routing_guard.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="instance_protocol_split_receipt",
        contract_keys=("instance_protocol_split_receipt_contract_v1", "instance_protocol_split_receipt_contract"),
        validator_script="scripts/validate_instance_protocol_split_receipt.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="vendor_namespace_separation",
        contract_keys=("semantic_routing_guard_contract_v1", "semantic_routing_guard_contract"),
        validator_script="scripts/validate_vendor_namespace_separation.py",
        validator_args=("--json-only",),
    ),
    ContractTarget(
        name="protocol_feedback_sidecar",
        contract_keys=("protocol_feedback_sidecar_contract_v1", "protocol_feedback_sidecar_contract"),
        validator_script="scripts/validate_protocol_feedback_sidecar_contract.py",
        validator_args=("--json-only",),
    ),
)


def _extract_reason(out: str, err: str, default_reason: str) -> str:
    text = f"{out}\n{err}".strip()
    m = ERR_RE.search(text)
    if m:
        return m.group(1)
    return default_reason


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _classify_from_payload(
    *,
    script: str,
    payload: dict[str, Any],
    required: bool,
    fallback_rc: int,
) -> tuple[str, str]:
    status_key = STATUS_FIELD_BY_SCRIPT.get(script, "")
    validator_status = str(payload.get(status_key, "")).strip().upper() if status_key else ""
    if not validator_status:
        return _classify(required, fallback_rc)
    if validator_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED, REASON_PASS
    if validator_status == STATUS_SKIPPED_NOT_REQUIRED:
        return STATUS_SKIPPED_NOT_REQUIRED, REASON_SKIPPED
    if validator_status == STATUS_FAIL_REQUIRED:
        return STATUS_FAIL_REQUIRED, REASON_FAIL
    if validator_status == "WARN_NON_BLOCKING":
        return (STATUS_FAIL_REQUIRED if required else STATUS_FAIL_OPTIONAL), REASON_FAIL
    return _classify(required, fallback_rc)


def _run_validator(
    script: str,
    catalog: str,
    identity_id: str,
    *,
    repo_catalog: str,
    operation: str,
    extra_args: tuple[str, ...],
) -> tuple[int, str, str]:
    cmd = ["python3", script, "--catalog", catalog, "--identity-id", identity_id]
    if script in {
        "scripts/validate_semantic_routing_guard.py",
        "scripts/validate_vendor_namespace_separation.py",
    }:
        cmd += ["--operation", operation]
    if script == "scripts/validate_instance_protocol_split_receipt.py":
        cmd += ["--operation", operation, "--repo-catalog", repo_catalog]
    if script == "scripts/validate_protocol_feedback_sidecar_contract.py":
        cmd += ["--repo-catalog", repo_catalog, "--operation", operation]
    cmd += list(extra_args)
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _classify(required: bool, rc: int) -> tuple[str, str]:
    if rc == 0 and required:
        return STATUS_PASS_REQUIRED, REASON_PASS
    if rc == 0 and not required:
        return STATUS_SKIPPED_NOT_REQUIRED, REASON_SKIPPED
    if rc != 0 and required:
        return STATUS_FAIL_REQUIRED, REASON_FAIL
    return STATUS_FAIL_OPTIONAL, REASON_FAIL


def _coverage_rate(passed: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((passed / total) * 100.0, 2)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate required-contract coverage semantics for tool/vendor closures "
            "(PASS_REQUIRED / SKIPPED_NOT_REQUIRED / FAIL_REQUIRED)."
        )
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--min-required-contract-coverage",
        type=float,
        default=-1.0,
        help="optional minimum required-contract coverage rate (0-100). default disabled",
    )
    ap.add_argument(
        "--json-only",
        action="store_true",
        help="emit payload JSON only",
    )
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
        help="operation context passed to operation-aware validators",
    )
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity runtime task: {exc}")
        return 2

    rows: list[dict[str, Any]] = []
    required_total = 0
    required_passed = 0
    skipped_count = 0
    failed_required = 0
    failed_optional = 0

    for target in TARGETS:
        contract: dict[str, Any] = {}
        contract_key_used = ""
        for key in target.contract_keys:
            raw = task.get(key)
            if isinstance(raw, dict):
                contract = raw
                contract_key_used = key
                break
        if not contract_key_used:
            contract_key_used = target.contract_keys[0]
        required = contract_required(contract)

        report_pattern = str(contract.get("report_path_pattern", "")).strip()
        evidence = resolve_report_path(report="", pattern=report_pattern, pack_root=pack_path) if report_pattern else None
        evidence_ref = str(evidence) if evidence else ""

        rc, out, err = _run_validator(
            target.validator_script,
            str(catalog_path),
            args.identity_id,
            repo_catalog=args.repo_catalog,
            operation=args.operation,
            extra_args=target.validator_args,
        )
        payload = _parse_json_payload(out) if target.validator_args else None
        required_effective = required
        if isinstance(payload, dict):
            payload_required = payload.get("required_contract")
            if isinstance(payload_required, bool):
                required_effective = payload_required
        required_total += 1 if required_effective else 0

        if isinstance(payload, dict):
            validator_status, reason_code = _classify_from_payload(
                script=target.validator_script,
                payload=payload,
                required=required_effective,
                fallback_rc=rc,
            )
            if reason_code == REASON_FAIL:
                payload_reason = str(payload.get("error_code") or payload.get("sidecar_error_code") or "").strip()
                reason_code = payload_reason or _extract_reason(out, err, reason_code)
        else:
            validator_status, reason_code = _classify(required_effective, rc)
            if reason_code == REASON_FAIL:
                reason_code = _extract_reason(out, err, reason_code)

        if validator_status == STATUS_PASS_REQUIRED:
            required_passed += 1
        elif validator_status == STATUS_SKIPPED_NOT_REQUIRED:
            skipped_count += 1
        elif validator_status == STATUS_FAIL_REQUIRED:
            failed_required += 1
        elif validator_status == STATUS_FAIL_OPTIONAL:
            failed_optional += 1

        rows.append(
            {
                "name": target.name,
                "contract_key": contract_key_used,
                "validator": target.validator_script,
                "validator_status": validator_status,
                "required_contract_declared": required,
                "required_contract": required_effective,
                "auto_required_signal": (payload.get("auto_required_signal") if isinstance(payload, dict) else False),
                "reason_code": reason_code,
                "evidence_ref": evidence_ref,
                "validator_rc": rc,
                "operation": args.operation,
                "validator_tail": (out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")),
            }
        )

    coverage_rate = _coverage_rate(required_passed, required_total)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_path),
        "operation": args.operation,
        "contracts": rows,
        "required_contract_total": required_total,
        "required_contract_passed": required_passed,
        "required_contract_coverage_rate": coverage_rate,
        "skipped_contract_count": skipped_count,
        "failed_required_contract_count": failed_required,
        "failed_optional_contract_count": failed_optional,
    }

    min_cov = args.min_required_contract_coverage
    coverage_gate_enabled = min_cov >= 0.0
    coverage_gate_failed = coverage_gate_enabled and coverage_rate < min_cov
    if coverage_gate_enabled:
        payload["min_required_contract_coverage"] = min_cov
        payload["coverage_gate_failed"] = coverage_gate_failed

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for row in rows:
            print(
                f"[COVERAGE] {row['name']}: status={row['validator_status']} "
                f"required={row['required_contract']} reason={row['reason_code']} "
                f"evidence_ref={row['evidence_ref'] or '-'}"
            )
        print(
            "[COVERAGE] summary: "
            f"required_contract_total={required_total} "
            f"required_contract_passed={required_passed} "
            f"required_contract_coverage_rate={coverage_rate} "
            f"skipped_contract_count={skipped_count} "
            f"failed_required_contract_count={failed_required} "
            f"failed_optional_contract_count={failed_optional}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    if failed_required > 0:
        return 1
    if coverage_gate_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
