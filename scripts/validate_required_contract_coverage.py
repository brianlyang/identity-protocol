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


@dataclass
class ContractTarget:
    name: str
    contract_key: str
    validator_script: str


TARGETS = (
    ContractTarget(
        name="tool_installation",
        contract_key="tool_installation_contract",
        validator_script="scripts/validate_identity_tool_installation.py",
    ),
    ContractTarget(
        name="vendor_api_discovery",
        contract_key="vendor_api_discovery_contract",
        validator_script="scripts/validate_identity_vendor_api_discovery.py",
    ),
    ContractTarget(
        name="vendor_api_solution",
        contract_key="vendor_api_solution_contract",
        validator_script="scripts/validate_identity_vendor_api_solution.py",
    ),
)


def _extract_reason(out: str, err: str, default_reason: str) -> str:
    text = f"{out}\n{err}".strip()
    m = ERR_RE.search(text)
    if m:
        return m.group(1)
    return default_reason


def _run_validator(script: str, catalog: str, identity_id: str) -> tuple[int, str, str]:
    p = subprocess.run(
        ["python3", script, "--catalog", catalog, "--identity-id", identity_id],
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
        contract = task.get(target.contract_key)
        if not isinstance(contract, dict):
            contract = {}
        required = contract_required(contract)
        required_total += 1 if required else 0

        report_pattern = str(contract.get("report_path_pattern", "")).strip()
        evidence = resolve_report_path(report="", pattern=report_pattern, pack_root=pack_path) if report_pattern else None
        evidence_ref = str(evidence) if evidence else ""

        rc, out, err = _run_validator(target.validator_script, str(catalog_path), args.identity_id)
        validator_status, reason_code = _classify(required, rc)
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
                "contract_key": target.contract_key,
                "validator": target.validator_script,
                "validator_status": validator_status,
                "required_contract": required,
                "reason_code": reason_code,
                "evidence_ref": evidence_ref,
                "validator_rc": rc,
                "validator_tail": (out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")),
            }
        )

    coverage_rate = _coverage_rate(required_passed, required_total)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_path),
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
