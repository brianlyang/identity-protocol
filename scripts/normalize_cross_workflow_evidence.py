#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import (
    build_identity_upgrade_evidence_selection_projection,
    contract_required,
    load_json,
    load_yaml,
    resolve_pack_and_task,
    resolve_report_evidence_selection,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_EVIDENCE_SOURCE_MISSING = "IP-XWF-001"
ERR_REQUIRED_FIELD_MISSING = "IP-XWF-002"
ERR_OUTPUT_WRITE_FAILED = "IP-XWF-003"

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


def _json_stable(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        return str(value)


def _extract_from_doc(doc: Any) -> dict[str, str]:
    if not isinstance(doc, dict):
        return {
            "run_id": "",
            "route_action": "",
            "quality_meta_state": "",
            "dedup_state": "",
            "schema_version": "",
        }

    run_id = _nonempty(
        doc.get("run_id"),
        doc.get("activity_run_id"),
        doc.get("execution_run_id"),
        doc.get("execution_id"),
        doc.get("runId"),
    )

    route_action = _nonempty(
        doc.get("route_action"),
        doc.get("route_selected"),
        doc.get("route_decision"),
        (doc.get("route_decision") or {}).get("route"),
        (doc.get("route_decision") or {}).get("action"),
        doc.get("task_route"),
    )
    if not route_action and isinstance(doc.get("route_decision"), dict):
        route_action = _json_stable(doc.get("route_decision"))

    qms = doc.get("quality_meta_state")
    if qms is None:
        qms = doc.get("quality_state")
    if qms is None:
        qms = {
            "all_ok": doc.get("all_ok"),
            "permission_state": doc.get("permission_state"),
            "writeback_status": doc.get("writeback_status"),
            "capability_activation_status": doc.get("capability_activation_status"),
        }
    quality_meta_state = _json_stable(qms)

    dedup_state = _nonempty(
        doc.get("dedup_state"),
        _json_stable(doc.get("dedup")) if doc.get("dedup") is not None else "",
        _json_stable(doc.get("dedup_monotonicity")) if doc.get("dedup_monotonicity") is not None else "",
        _json_stable(doc.get("winner")) if doc.get("winner") is not None else "",
    )

    schema_version = _nonempty(
        doc.get("schema_version"),
        doc.get("evidence_schema_version"),
    )

    return {
        "run_id": run_id,
        "route_action": route_action,
        "quality_meta_state": quality_meta_state,
        "dedup_state": dedup_state,
        "schema_version": schema_version,
    }


def compute_cross_workflow_receipt(*, doc: Any, overrides: dict[str, str], default_schema_version: str = "v1") -> dict[str, str]:
    row = _extract_from_doc(doc)
    run_id = _nonempty(overrides.get("run_id"), row.get("run_id"))
    route_action = _nonempty(overrides.get("route_action"), row.get("route_action"))
    quality_meta_state = _nonempty(overrides.get("quality_meta_state"), row.get("quality_meta_state"))
    dedup_state = _nonempty(overrides.get("dedup_state"), row.get("dedup_state"))
    schema_version = _nonempty(overrides.get("schema_version"), row.get("schema_version"), default_schema_version)

    canonical = {
        "run_id": run_id,
        "route_action": route_action,
        "quality_meta_state": quality_meta_state,
        "dedup_state": dedup_state,
        "schema_version": schema_version,
    }
    canonical_json = _json_stable(canonical)
    evidence_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    return {
        "run_id": run_id,
        "route_action": route_action,
        "quality_meta_state": quality_meta_state,
        "dedup_state": dedup_state,
        "schema_version": schema_version,
        "evidence_hash": evidence_hash,
    }


def _resolve_evidence_selection(
    *,
    explicit_evidence: str,
    pack_path: Path,
    identity_id: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    pattern = _nonempty(
        contract.get("evidence_path_pattern"),
        contract.get("report_path_pattern"),
        contract.get("source_pattern"),
    )
    resolution = resolve_report_evidence_selection(
        report=explicit_evidence,
        pattern=pattern,
        pack_root=pack_path,
        identity_id=identity_id,
        fallback_to_identity_upgrade_report=not bool(explicit_evidence.strip()),
    )
    payload = build_identity_upgrade_evidence_selection_projection(
        resolution,
        field_prefix="evidence",
    )
    payload["_selected_evidence_path"] = resolution.selected_path
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize cross-workflow evidence into canonical RQ-019 schema receipt.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--route-action", default="")
    ap.add_argument("--quality-meta-state", default="")
    ap.add_argument("--dedup-state", default="")
    ap.add_argument("--schema-version", default="v1")
    ap.add_argument("--out", default="")
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
        "required_contract": False,
        "auto_required_signal": False,
        "cross_workflow_evidence_normalization_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "evidence_selected_path": "",
        "evidence_logical_identity_key": "",
        "evidence_selection_mode": "",
        "evidence_selected_authority_class": "",
        "evidence_pointer_resolution_mode": "",
        "evidence_pointer_path": "",
        "evidence_kind": "",
        "evidence_ref": "",
        "normalized_receipt_path": "",
        "run_id": "",
        "route_action": "",
        "quality_meta_state": "",
        "dedup_state": "",
        "schema_version": "",
        "evidence_hash": "",
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

    if any(
        _nonempty(v)
        for v in (
            args.evidence,
            args.run_id,
            args.route_action,
            args.quality_meta_state,
            args.dedup_state,
            args.out,
        )
    ):
        required = True
        auto_required = True
    elif args.operation in STRICT_OPERATIONS:
        auto_required = False

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    evidence_selection = _resolve_evidence_selection(
        explicit_evidence=args.evidence,
        pack_path=pack_path,
        identity_id=args.identity_id,
        contract=contract if isinstance(contract, dict) else {},
    )
    payload.update({k: v for k, v in evidence_selection.items() if not k.startswith("_")})
    evidence_path = evidence_selection.get("_selected_evidence_path")
    if evidence_path is not None:
        payload["evidence_selected_path"] = str(evidence_path)
    if evidence_path is None:
        payload["cross_workflow_evidence_normalization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_EVIDENCE_SOURCE_MISSING
        payload["stale_reasons"] = ["evidence_source_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["evidence_ref"] = str(evidence_path)

    try:
        raw = evidence_path.read_text(encoding="utf-8", errors="ignore")
        try:
            doc = json.loads(raw)
        except Exception:
            doc = load_yaml(evidence_path)
    except Exception:
        payload["cross_workflow_evidence_normalization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_EVIDENCE_SOURCE_MISSING
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

    route_action_required = bool(_nonempty(args.route_action)) or _has_route_signal(doc)
    dedup_state_required = bool(_nonempty(args.dedup_state)) or _has_dedup_signal(doc)
    payload["route_action_required"] = route_action_required
    payload["dedup_state_required"] = dedup_state_required

    if (not route_action_required) and (not dedup_state_required) and not auto_required:
        payload.update(row)
        payload["cross_workflow_evidence_normalization_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["error_code"] = ""
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
        payload.update(row)
        payload["cross_workflow_evidence_normalization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = [f"missing_{k}" for k in missing]
        _emit(payload, json_only=args.json_only)
        return 1

    payload.update(row)

    if args.out.strip():
        out_path = Path(args.out).expanduser().resolve()
        receipt = {
            "identity_id": args.identity_id,
            "operation": args.operation,
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            **row,
            "source_evidence_ref": str(evidence_path),
        }
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            payload["normalized_receipt_path"] = str(out_path)
        except Exception:
            payload["cross_workflow_evidence_normalization_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_OUTPUT_WRITE_FAILED
            payload["stale_reasons"] = ["normalized_receipt_write_failed"]
            _emit(payload, json_only=args.json_only)
            return 1

    payload["cross_workflow_evidence_normalization_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
