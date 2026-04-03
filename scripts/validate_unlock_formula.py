#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from contract_binding_doc_defaults_common import resolve_validator_doc_defaults
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING_REQUIRED_OUTPUT = "IP-UNLOCK-001"
ERR_GATE_TABLE_MISSING = "IP-UNLOCK-002"
ERR_P0_LEDGER_MISSING = "IP-UNLOCK-003"
ERR_DOC_READ_FAILED = "IP-UNLOCK-004"

STRICT_OPERATIONS = {
    "readiness",
    "e2e",
    "ci",
    "validate",
}

DEFAULT_GOV_DOC = ""
DEFAULT_REVIEW_DOC = ""


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "release_unlock_formula_automation_contract_v1",
        "release_unlock_formula_automation_contract",
        "rq_001_unlock_formula_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _resolve_doc_paths(
    *,
    repo_root: Path,
    contract: dict[str, Any],
    governance_doc_arg: str,
    review_doc_arg: str,
) -> tuple[Path | None, Path | None]:
    derived_governance_doc, derived_review_doc = resolve_validator_doc_defaults(
        repo_root,
        validator_script="scripts/validate_unlock_formula.py",
    )
    governance_doc_rel = (
        str(governance_doc_arg or "").strip()
        or str(contract.get("governance_doc", "")).strip()
        or derived_governance_doc
    )
    review_doc_rel = (
        str(review_doc_arg or "").strip()
        or str(contract.get("review_doc", "")).strip()
        or derived_review_doc
    )
    gov_doc_path = (repo_root / governance_doc_rel).resolve() if governance_doc_rel else None
    review_doc_path = (repo_root / review_doc_rel).resolve() if review_doc_rel else None
    return gov_doc_path, review_doc_path


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    start_idx = text.find(start_marker)
    if start_idx < 0:
        return ""
    end_idx = text.find(end_marker, start_idx + len(start_marker))
    if end_idx < 0:
        return text[start_idx:]
    return text[start_idx:end_idx]


def _split_markdown_row(row: str) -> list[str]:
    body = row.strip().strip("|")
    if not body:
        return []
    return [part.strip() for part in body.split("|")]


def _normalize_state(raw_state: str) -> str:
    token = str(raw_state or "").strip().strip("`").upper()
    if token.startswith("PASS"):
        return "PASS"
    return token


def _parse_decision_gates(governance_text: str) -> dict[str, str]:
    section = _extract_section(
        governance_text,
        "### 0.3 Release lock table",
        "### 0.4",
    )
    gate_map: dict[str, str] = {}
    for line in section.splitlines():
        if not line.lstrip().startswith("| D"):
            continue
        cols = _split_markdown_row(line)
        if len(cols) < 3:
            continue
        gate_match = re.match(r"^(D[1-6])\b", str(cols[0]).strip(), flags=re.IGNORECASE)
        if not gate_match:
            continue
        gate = gate_match.group(1).upper()
        gate_map[gate] = _normalize_state(cols[2])
    return gate_map


def _parse_p0_ledger(governance_text: str) -> tuple[int, int, list[str], list[str]]:
    section = _extract_section(
        governance_text,
        "## 5) Requirement Mapping",
        "## 6)",
    )
    p0_total = 0
    p0_done = 0
    p0_not_done_refs: list[str] = []
    env_blockers: list[str] = []
    for line in section.splitlines():
        if not line.lstrip().startswith("| ASB16-RQ-"):
            continue
        cols = _split_markdown_row(line)
        if len(cols) < 6:
            continue
        rq = str(cols[0]).strip()
        priority = str(cols[3]).strip().upper()
        lifecycle = _normalize_state(cols[4])
        evidence_baseline = str(cols[5]).strip()
        if priority != "P0":
            continue
        p0_total += 1
        if lifecycle == "DONE":
            p0_done += 1
        else:
            p0_not_done_refs.append(rq)
        if "BLOCKED_BY_ENV_AUDIT" in evidence_baseline.upper() or "ENV/AUTH" in evidence_baseline.upper():
            env_blockers.append(rq)
    return p0_total, p0_done, p0_not_done_refs, sorted(set(env_blockers))


def _required_output_missing(payload: dict[str, Any]) -> list[str]:
    required_fields = (
        "unlock_allowed",
        "decision_gates",
        "p0_total",
        "p0_done",
        "p0_not_done_refs",
        "audit_signoff_status",
        "env_blockers",
        "protocol_blockers",
        "evidence_refs",
    )
    missing: list[str] = []
    for field in required_fields:
        if field not in payload or payload.get(field) is None:
            missing.append(field)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate release unlock formula automation contract (RQ-001).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--governance-doc", default=DEFAULT_GOV_DOC)
    ap.add_argument("--review-doc", default=DEFAULT_REVIEW_DOC)
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required and args.operation in STRICT_OPERATIONS),
        "unlock_formula_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "unlock_allowed": False,
        "decision_gates": {},
        "p0_total": 0,
        "p0_done": 0,
        "p0_not_done_refs": [],
        "audit_signoff_status": "",
        "env_blockers": [],
        "protocol_blockers": [],
        "evidence_refs": [],
        "d6_derived_from_inputs": True,
        "formula_input_digest": "",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    repo_root = Path(__file__).resolve().parent.parent
    gov_doc_path, review_doc_path = _resolve_doc_paths(
        repo_root=repo_root,
        contract=contract,
        governance_doc_arg=args.governance_doc,
        review_doc_arg=args.review_doc,
    )
    payload["evidence_refs"] = [str(path) for path in (gov_doc_path, review_doc_path) if path is not None]
    payload["evidence_ref"] = str(gov_doc_path) if gov_doc_path is not None else ""

    if gov_doc_path is None or review_doc_path is None or not gov_doc_path.exists() or not review_doc_path.exists():
        payload["unlock_formula_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DOC_READ_FAILED
        missing_docs = []
        if gov_doc_path is None or not gov_doc_path.exists():
            missing_docs.append("governance_doc_missing")
        if review_doc_path is None or not review_doc_path.exists():
            missing_docs.append("review_doc_missing")
        payload["stale_reasons"] = missing_docs
        _emit(payload, json_only=args.json_only)
        return 1

    governance_text = gov_doc_path.read_text(encoding="utf-8", errors="ignore")
    review_text = review_doc_path.read_text(encoding="utf-8", errors="ignore")
    payload["producer_readiness"] = bool(governance_text.strip()) and bool(review_text.strip())

    decision_gates_input = _parse_decision_gates(governance_text)
    if not all(g in decision_gates_input for g in ("D1", "D2", "D3", "D4", "D5")):
        payload["unlock_formula_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_GATE_TABLE_MISSING
        payload["stale_reasons"] = ["decision_gate_table_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    p0_total, p0_done, p0_not_done_refs, env_blockers = _parse_p0_ledger(governance_text)
    if p0_total <= 0:
        payload["unlock_formula_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_P0_LEDGER_MISSING
        payload["stale_reasons"] = ["p0_requirement_ledger_parse_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    d1_to_d5_all_pass = all(decision_gates_input.get(g) == "PASS" for g in ("D1", "D2", "D3", "D4", "D5"))
    unlock_allowed = bool(d1_to_d5_all_pass and p0_total == p0_done)
    decision_gates = {
        "D1": decision_gates_input.get("D1", ""),
        "D2": decision_gates_input.get("D2", ""),
        "D3": decision_gates_input.get("D3", ""),
        "D4": decision_gates_input.get("D4", ""),
        "D5": decision_gates_input.get("D5", ""),
        "D6": "PASS" if unlock_allowed else "LOCKED",
    }

    protocol_blockers: list[str] = []
    for gate in ("D1", "D2", "D3", "D4", "D5"):
        gate_state = decision_gates.get(gate, "")
        if gate_state != "PASS":
            protocol_blockers.append(f"{gate}:{gate_state or 'UNKNOWN'}")
    protocol_blockers.extend([f"P0_NOT_DONE:{rq}" for rq in p0_not_done_refs])
    protocol_blockers = sorted(set(protocol_blockers))

    payload["unlock_allowed"] = unlock_allowed
    payload["decision_gates"] = decision_gates
    payload["p0_total"] = p0_total
    payload["p0_done"] = p0_done
    payload["p0_not_done_refs"] = p0_not_done_refs
    payload["audit_signoff_status"] = decision_gates.get("D5", "")
    payload["env_blockers"] = env_blockers
    payload["protocol_blockers"] = protocol_blockers
    payload["formula_input_digest"] = hashlib.sha256(
        json.dumps(
            {
                "decision_gates_input": {k: decision_gates_input.get(k, "") for k in ("D1", "D2", "D3", "D4", "D5")},
                "p0_total": p0_total,
                "p0_done": p0_done,
                "p0_not_done_refs": p0_not_done_refs,
                "audit_signoff_status": decision_gates.get("D5", ""),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    missing_required = _required_output_missing(payload)
    if missing_required:
        payload["unlock_formula_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING_REQUIRED_OUTPUT
        payload["stale_reasons"] = [f"missing_field:{field}" for field in missing_required]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["unlock_formula_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
