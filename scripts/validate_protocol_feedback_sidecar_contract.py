#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING_FIELDS = "IP-SID-001"
ERR_P0_BLOCKING_REQUIRED = "IP-SID-002"
ERR_VALIDATOR_RUNTIME = "IP-SID-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
REQ_CONTRACT_KEYS = (
    "required",
    "default_mode",
    "blocking_error_prefixes",
    "escalation_policy",
)
DEFAULT_BLOCKING_PREFIXES = ("IP-WRB-", "IP-SEM-")

ERR_RE = re.compile(r"\b(IP-[A-Z0-9-]+)\b")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _extract_error_code(stdout: str, stderr: str) -> str:
    m = ERR_RE.search(f"{stdout}\n{stderr}")
    return m.group(1) if m else ""


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout or "", p.stderr or ""


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_sidecar_contract_v1",
        "protocol_feedback_sidecar_contract",
    ):
        v = task.get(key)
        if isinstance(v, dict):
            return v
    return {}


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    return any(p.is_file() for p in root.rglob("*"))


def _normalize_prefixes(raw: Any) -> list[str]:
    if not isinstance(raw, list) or not raw:
        return list(DEFAULT_BLOCKING_PREFIXES)
    out: list[str] = []
    for x in raw:
        token = str(x).strip().upper()
        if token:
            out.append(token)
    return out or list(DEFAULT_BLOCKING_PREFIXES)


def _is_blocking_code(code: str, prefixes: list[str]) -> bool:
    token = str(code or "").strip().upper()
    if not token:
        return False
    return any(token.startswith(p) for p in prefixes)


def _validator_payload(
    *,
    cmd: list[str],
    status_key: str,
    default_status: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rc, out, err = _run(cmd)
    payload = _parse_json_payload(out) or {}
    status = str(payload.get(status_key, "")).strip().upper() or default_status
    error_code = str(payload.get("error_code", "")).strip() or _extract_error_code(out, err)
    result = {
        "rc": rc,
        "status": status,
        "error_code": error_code,
        "ok": rc == 0 and status != STATUS_FAIL_REQUIRED,
        "stdout_tail": (out.strip().splitlines()[-1] if out.strip() else ""),
        "stderr_tail": (err.strip().splitlines()[-1] if err.strip() else ""),
        "payload": payload,
        "command": cmd,
    }
    return result, payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-feedback sidecar escalation contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--enforce-blocking", action="store_true")
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
    required = contract_required(contract) if contract else False
    auto_required_signal = False
    if not required and _feedback_artifacts_present(pack_path):
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "sidecar_default_mode": "NON_BLOCKING",
        "enforce_blocking": bool(args.enforce_blocking),
        "sidecar_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "sidecar_error_code": "",
        "escalation_required": False,
        "escalation_decision": "NON_BLOCKING_DEFAULT",
        "blocking_error_codes": [],
        "p0_violations": [],
        "track_a": {},
        "track_b": {},
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if missing_contract:
        payload["sidecar_contract_status"] = STATUS_FAIL_REQUIRED
        payload["sidecar_error_code"] = ERR_CONTRACT_MISSING_FIELDS
        payload["stale_reasons"] = [f"contract_missing_fields:{','.join(missing_contract)}"]
        _emit(payload, json_only=args.json_only)
        return 1

    default_mode = str(contract.get("default_mode", "non_blocking")).strip().lower() or "non_blocking"
    if default_mode != "non_blocking":
        payload["sidecar_contract_status"] = STATUS_FAIL_REQUIRED
        payload["sidecar_error_code"] = ERR_CONTRACT_MISSING_FIELDS
        payload["stale_reasons"] = ["default_mode_must_be_non_blocking"]
        _emit(payload, json_only=args.json_only)
        return 1

    escalation_policy = str(contract.get("escalation_policy", "p0_governance_boundary")).strip().lower()
    if escalation_policy != "p0_governance_boundary":
        payload["sidecar_contract_status"] = STATUS_FAIL_REQUIRED
        payload["sidecar_error_code"] = ERR_CONTRACT_MISSING_FIELDS
        payload["stale_reasons"] = ["escalation_policy_must_be_p0_governance_boundary"]
        _emit(payload, json_only=args.json_only)
        return 1

    blocking_prefixes = _normalize_prefixes(contract.get("blocking_error_prefixes"))

    sem_cmd = [
        "python3",
        "scripts/validate_semantic_routing_guard.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--operation",
        args.operation,
        "--json-only",
    ]
    ns_cmd = [
        "python3",
        "scripts/validate_vendor_namespace_separation.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--operation",
        args.operation,
        "--json-only",
    ]
    wb_cmd = [
        "python3",
        "scripts/validate_writeback_continuity.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        args.operation,
        "--json-only",
    ]
    post_cmd = [
        "python3",
        "scripts/validate_post_execution_mandatory.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        args.operation,
        "--json-only",
    ]
    report = args.report.strip()
    if report:
        wb_cmd += ["--report", report]
        post_cmd += ["--report", report]

    sem_result, sem_payload = _validator_payload(cmd=sem_cmd, status_key="semantic_routing_status", default_status=STATUS_FAIL_REQUIRED)
    ns_result, ns_payload = _validator_payload(cmd=ns_cmd, status_key="vendor_namespace_status", default_status=STATUS_FAIL_REQUIRED)
    wb_result, wb_payload = _validator_payload(cmd=wb_cmd, status_key="writeback_continuity_status", default_status=STATUS_FAIL_REQUIRED)
    post_result, post_payload = _validator_payload(cmd=post_cmd, status_key="post_execution_mandatory_status", default_status=STATUS_FAIL_REQUIRED)

    payload["track_a"] = {
        "writeback_continuity_status": wb_result["status"],
        "writeback_error_code": wb_result["error_code"],
        "post_execution_mandatory_status": post_result["status"],
        "post_execution_error_code": post_result["error_code"],
        "writeback_required_contract": wb_payload.get("required_contract"),
        "post_execution_required_contract": post_payload.get("required_contract"),
        "writeback_report_selected_path": wb_payload.get("report_selected_path"),
        "post_execution_report_selected_path": post_payload.get("report_selected_path"),
    }
    payload["track_b"] = {
        "semantic_routing_status": sem_result["status"],
        "semantic_error_code": sem_result["error_code"],
        "vendor_namespace_status": ns_result["status"],
        "vendor_namespace_error_code": ns_result["error_code"],
        "semantic_required_contract": sem_payload.get("required_contract"),
        "namespace_required_contract": ns_payload.get("required_contract"),
        "semantic_auto_required_signal": sem_payload.get("auto_required_signal"),
        "namespace_auto_required_signal": ns_payload.get("auto_required_signal"),
    }

    p0_violations: list[dict[str, Any]] = []

    def _append(track: str, validator: str, result: dict[str, Any]) -> None:
        status = str(result.get("status", "")).upper()
        code = str(result.get("error_code", "")).strip()
        rc = int(result.get("rc", 1))
        if status == STATUS_FAIL_REQUIRED:
            if (not code) and rc != 0:
                code = ERR_VALIDATOR_RUNTIME
            if _is_blocking_code(code, blocking_prefixes) or code == ERR_VALIDATOR_RUNTIME:
                p0_violations.append(
                    {
                        "track": track,
                        "validator": validator,
                        "status": status,
                        "error_code": code,
                        "rc": rc,
                    }
                )

    _append("track_a", "validate_writeback_continuity", wb_result)
    _append("track_a", "validate_post_execution_mandatory", post_result)
    _append("track_b", "validate_semantic_routing_guard", sem_result)
    _append("track_b", "validate_vendor_namespace_separation", ns_result)

    payload["p0_violations"] = p0_violations
    blocking_codes = sorted({str(v.get("error_code", "")).strip() for v in p0_violations if str(v.get("error_code", "")).strip()})
    payload["blocking_error_codes"] = blocking_codes

    escalation_required = len(p0_violations) > 0
    payload["escalation_required"] = escalation_required

    strict_operation = args.operation in STRICT_OPERATIONS
    enforce = bool(args.enforce_blocking) or strict_operation

    if escalation_required:
        payload["escalation_decision"] = "BLOCKING_P0_GOVERNANCE"
        payload["sidecar_error_code"] = ERR_P0_BLOCKING_REQUIRED
        payload["stale_reasons"] = ["p0_governance_boundary_violation"]
        if enforce:
            payload["sidecar_contract_status"] = STATUS_FAIL_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 1
        payload["sidecar_contract_status"] = STATUS_WARN_NON_BLOCKING
        _emit(payload, json_only=args.json_only)
        return 0

    payload["sidecar_contract_status"] = STATUS_PASS_REQUIRED
    payload["sidecar_error_code"] = ""
    payload["escalation_decision"] = "NON_BLOCKING_DEFAULT"
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
