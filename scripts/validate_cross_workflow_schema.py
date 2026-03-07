#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from normalize_cross_workflow_evidence import STATUS_FAIL_REQUIRED, STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED, compute_cross_workflow_receipt
from tool_vendor_governance_common import (
    contract_required,
    latest_identity_upgrade_report,
    load_json,
    load_yaml,
    resolve_pack_and_task,
    resolve_report_path,
)

ERR_EVIDENCE_SOURCE_MISSING = "IP-XWF-001"
ERR_REQUIRED_FIELD_MISSING = "IP-XWF-002"
ERR_HASH_MISMATCH = "IP-XWF-004"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

OBSERVATION_OPERATIONS = {
    "scan",
    "three-plane",
    "inspection",
    "validate",
}

CONTRACT_KEYS = (
    "cross_workflow_evidence_schema_contract_v1",
    "cross_workflow_evidence_schema_contract",
    "rq_019_cross_workflow_evidence_schema_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _nonempty(*vals: Any) -> str:
    for v in vals:
        s = str(v or "").strip()
        if s:
            return s
    return ""


def _has_route_signal(doc: Any) -> bool:
    if not isinstance(doc, dict):
        return False
    if _nonempty(doc.get("route_action"), doc.get("route_selected"), doc.get("task_route")):
        return True
    route_decision = doc.get("route_decision")
    if isinstance(route_decision, dict):
        if _nonempty(route_decision.get("route"), route_decision.get("action"), route_decision.get("route_action")):
            return True
        return bool(route_decision)
    return route_decision is not None


def _has_dedup_signal(doc: Any) -> bool:
    if not isinstance(doc, dict):
        return False
    if _nonempty(doc.get("dedup_state")):
        return True
    return any(doc.get(k) is not None for k in ("dedup", "dedup_monotonicity", "winner"))


def _resolve_evidence_path(*, explicit_evidence: str, pack_path: Path, identity_id: str, contract: dict[str, Any]) -> Path | None:
    if explicit_evidence.strip():
        p = Path(explicit_evidence).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    pattern = _nonempty(
        contract.get("evidence_path_pattern"),
        contract.get("report_path_pattern"),
        contract.get("source_pattern"),
    )
    if pattern:
        p = resolve_report_path(report="", pattern=pattern, pack_root=pack_path)
        if p and p.exists() and p.is_file():
            return p.resolve()

    latest = latest_identity_upgrade_report(identity_id, pack_path)
    if latest and latest.exists() and latest.is_file():
        return latest.resolve()

    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate canonical cross-workflow schema receipt (RQ-019).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--route-action", default="")
    ap.add_argument("--quality-meta-state", default="")
    ap.add_argument("--dedup-state", default="")
    ap.add_argument("--schema-version", default="v1")
    ap.add_argument("--expected-evidence-hash", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "run_profile": "observation" if args.operation in OBSERVATION_OPERATIONS else "enforcement",
        "required_contract": False,
        "auto_required_signal": False,
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "cross_workflow_schema_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "evidence_ref": "",
        "run_id": "",
        "route_action": "",
        "quality_meta_state": "",
        "dedup_state": "",
        "schema_version": "",
        "evidence_hash": "",
        "expected_evidence_hash": str(args.expected_evidence_hash or "").strip(),
        "hash_consistency_status": STATUS_SKIPPED_NOT_REQUIRED,
        "route_action_required": False,
        "dedup_state_required": False,
        "stale_reasons": [],
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False
    auto_required = False

    explicit_current_round_linked = any(
        _nonempty(v)
        for v in (
            args.evidence,
            args.run_id,
            args.route_action,
            args.quality_meta_state,
            args.dedup_state,
            args.expected_evidence_hash,
        )
    )
    if explicit_current_round_linked:
        required = True
        auto_required = True
    elif args.operation in STRICT_OPERATIONS:
        auto_required = False

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required
    payload["requiredization_current_round_linked"] = explicit_current_round_linked

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    evidence_path = _resolve_evidence_path(
        explicit_evidence=args.evidence,
        pack_path=pack_path,
        identity_id=args.identity_id,
        contract=contract if isinstance(contract, dict) else {},
    )
    payload["producer_readiness"] = evidence_path is not None
    if evidence_path is not None:
        payload["evidence_ref"] = str(evidence_path)
    if evidence_path is not None and not payload["requiredization_current_round_linked"]:
        payload["cross_workflow_schema_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["hash_consistency_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0
    if evidence_path is None:
        if not payload["requiredization_current_round_linked"] and args.operation in STRICT_OPERATIONS:
            payload["cross_workflow_schema_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["hash_consistency_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["cross_workflow_schema_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_EVIDENCE_SOURCE_MISSING
        payload["hash_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["evidence_source_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        raw = evidence_path.read_text(encoding="utf-8", errors="ignore")
        try:
            doc = json.loads(raw)
        except Exception:
            doc = load_yaml(evidence_path)
    except Exception:
        payload["cross_workflow_schema_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_EVIDENCE_SOURCE_MISSING
        payload["hash_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["evidence_read_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    row = compute_cross_workflow_receipt(
        doc=doc,
        overrides={
            "run_id": args.run_id,
            "route_action": args.route_action,
            "quality_meta_state": args.quality_meta_state,
            "dedup_state": args.dedup_state,
            "schema_version": args.schema_version,
        },
        default_schema_version=args.schema_version or "v1",
    )
    payload.update(row)

    route_action_required = bool(_nonempty(args.route_action)) or _has_route_signal(doc)
    dedup_state_required = bool(_nonempty(args.dedup_state)) or _has_dedup_signal(doc)
    payload["route_action_required"] = route_action_required
    payload["dedup_state_required"] = dedup_state_required

    if (not route_action_required) and (not dedup_state_required) and not auto_required:
        payload["cross_workflow_schema_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["hash_consistency_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["cross_workflow_not_applicable_no_route_or_dedup_signal"]
        _emit(payload, json_only=args.json_only)
        return 0

    required_fields = ["run_id", "quality_meta_state", "schema_version", "evidence_hash"]
    if route_action_required:
        required_fields.append("route_action")
    if dedup_state_required:
        required_fields.append("dedup_state")
    missing = [k for k in required_fields if not _nonempty(row.get(k))]
    if missing:
        payload["cross_workflow_schema_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["hash_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = [f"missing_{k}" for k in missing]
        _emit(payload, json_only=args.json_only)
        return 1

    expected_hash = _nonempty(args.expected_evidence_hash)
    if expected_hash and row.get("evidence_hash") != expected_hash:
        payload["cross_workflow_schema_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_HASH_MISMATCH
        payload["hash_consistency_status"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["evidence_hash_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["cross_workflow_schema_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["hash_consistency_status"] = STATUS_PASS_REQUIRED
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
