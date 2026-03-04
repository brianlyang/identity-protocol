#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_PASS_NON_BLOCKING = "PASS_NON_BLOCKING"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

ERR_INVENTORY_MISSING = "IP-CFIT-BLD-001"
ERR_MATRIX_WRITE_FAILED = "IP-CFIT-BLD-002"
ERR_SELECTED_PLAN_INVALID = "IP-CFIT-BLD-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "capability_fit_self_drive_optimization_contract_v1",
        "capability_fit_self_drive_optimization_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("capability_fit_self_drive_optimization_contract_v1")
        if isinstance(nested, dict):
            return nested

    return {}


def _inventory_from_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    skills = task.get("required_skills")
    if isinstance(skills, list):
        for s in skills:
            item = str(s).strip()
            if item:
                out.append({"candidate_id": f"skill:{item}", "candidate_type": "existing_composition", "source": "required_skills"})

    mcps = task.get("required_mcp")
    if isinstance(mcps, list):
        for m in mcps:
            item = str(m).strip()
            if item:
                out.append({"candidate_id": f"mcp:{item}", "candidate_type": "existing_composition", "source": "required_mcp"})

    # deterministic de-dup
    uniq: dict[str, dict[str, Any]] = {}
    for row in out:
        uniq[str(row.get("candidate_id", ""))] = row
    return [uniq[k] for k in sorted(uniq.keys())]


def _load_external_candidates(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists() or not path.is_file():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = doc.get("external_candidates") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for i, x in enumerate(rows):
        if not isinstance(x, dict):
            continue
        cid = str(x.get("candidate_id", "")).strip() or f"external:{i}"
        out.append(
            {
                "candidate_id": cid,
                "candidate_type": "external_candidate",
                "source": str(x.get("source", "external_candidates")).strip() or "external_candidates",
                "fit_score": x.get("fit_score", 0.5),
                "risk_score": x.get("risk_score", 0.5),
                "operational_cost_score": x.get("operational_cost_score", 0.5),
                "provenance_ref": str(x.get("provenance_ref", "external_source")).strip() or "external_source",
                "decision_basis": str(x.get("decision_basis", "not_sufficient")).strip() or "not_sufficient",
            }
        )
    return out


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build deterministic capability-fit matrix (inventory-first + compose-before-discover).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--inventory", default="")
    ap.add_argument("--external-candidates", default="")
    ap.add_argument("--out-root", default="/tmp/capability-fit-matrices")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
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

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "capability_fit_matrix_builder_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "matrix_path": "",
        "matrix_candidate_count": 0,
        "selected_candidate_count": 0,
        "selected_candidate_id": "",
        "selected_candidate_type": "",
        "inventory_snapshot_path": "",
        "external_candidate_source_path": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    inv_path = Path(args.inventory).expanduser().resolve() if args.inventory.strip() else None
    ext_path = Path(args.external_candidates).expanduser().resolve() if args.external_candidates.strip() else None

    if inv_path and inv_path.exists() and inv_path.is_file():
        try:
            inv_doc = json.loads(inv_path.read_text(encoding="utf-8"))
            inventory_rows = inv_doc.get("inventory") if isinstance(inv_doc, dict) else None
            inventory = [x for x in (inventory_rows or []) if isinstance(x, dict)]
        except Exception:
            inventory = []
    else:
        inventory = _inventory_from_task(task)

    if not inventory:
        payload["capability_fit_matrix_builder_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_INVENTORY_MISSING
        payload["stale_reasons"] = ["inventory_candidates_not_found"]
        _emit(payload, json_only=args.json_only)
        return 0

    external = _load_external_candidates(ext_path)

    matrix: list[dict[str, Any]] = []
    for row in inventory:
        cid = str(row.get("candidate_id", "")).strip()
        matrix.append(
            {
                "candidate_id": cid,
                "candidate_type": "existing_composition",
                "fit_score": 0.8,
                "risk_score": 0.2,
                "operational_cost_score": 0.2,
                "provenance_ref": str(row.get("source", "inventory_snapshot")).strip() or "inventory_snapshot",
                "decision": "rejected",
                "decision_basis": "inventory_first_evaluation",
            }
        )

    for row in external:
        matrix.append(
            {
                "candidate_id": str(row.get("candidate_id", "")).strip(),
                "candidate_type": "external_candidate",
                "fit_score": float(row.get("fit_score", 0.5)),
                "risk_score": float(row.get("risk_score", 0.5)),
                "operational_cost_score": float(row.get("operational_cost_score", 0.5)),
                "provenance_ref": str(row.get("provenance_ref", "external_source")).strip() or "external_source",
                "decision": "rejected",
                "decision_basis": str(row.get("decision_basis", "not_sufficient")).strip() or "not_sufficient",
            }
        )

    matrix.sort(key=lambda x: str(x.get("candidate_id", "")))

    # deterministic selection: prefer highest fit among existing composition
    existing = [x for x in matrix if str(x.get("candidate_type", "")) == "existing_composition"]
    if existing:
        selected = sorted(existing, key=lambda x: (-float(x.get("fit_score", 0.0)), str(x.get("candidate_id", ""))))[0]
        selected["decision"] = "selected"
        selected["fallback_ref"] = "fallback:existing_composition"
        selected["rollback_ref"] = "rollback:inventory_snapshot"
        selected["review_interval_days"] = int(contract.get("review_interval_days", 14) or 14)
        next_review = datetime.now(timezone.utc) + timedelta(days=int(selected["review_interval_days"]))
        selected["next_review_at"] = next_review.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        selected["fact_refs"] = [f"inventory:{selected['candidate_id']}"]
        selected["decision_impacts"] = ["tool_routing"]
    else:
        payload["capability_fit_matrix_builder_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SELECTED_PLAN_INVALID
        payload["stale_reasons"] = ["existing_composition_candidate_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    selected_rows = [x for x in matrix if str(x.get("decision", "")).lower() == "selected"]
    if len(selected_rows) != 1:
        payload["capability_fit_matrix_builder_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SELECTED_PLAN_INVALID
        payload["stale_reasons"] = ["selected_candidate_count_not_equal_one"]
        _emit(payload, json_only=args.json_only)
        return 0

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    inv_sha = hashlib.sha256(json.dumps(inventory, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    matrix_id = hashlib.sha256(f"{args.identity_id}|{inv_sha}|v1".encode("utf-8")).hexdigest()[:12]
    matrix_path = out_root / f"capability-fit-matrix-{args.identity_id}-{matrix_id}.json"
    inv_snapshot = out_root / f"capability-inventory-{args.identity_id}-{matrix_id}.json"

    matrix_doc = {
        "identity_id": args.identity_id,
        "generated_at": _now_iso(),
        "matrix_id": matrix_id,
        "inventory_snapshot_sha256": inv_sha,
        "capability_fit_matrix": matrix,
    }

    try:
        inv_snapshot.write_text(json.dumps({"inventory": inventory}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        matrix_path.write_text(json.dumps(matrix_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        payload["capability_fit_matrix_builder_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_MATRIX_WRITE_FAILED
        payload["stale_reasons"] = ["matrix_or_inventory_write_failed"]
        _emit(payload, json_only=args.json_only)
        return 0

    sel = selected_rows[0]
    payload.update(
        {
            "capability_fit_matrix_builder_status": STATUS_PASS_NON_BLOCKING,
            "matrix_path": str(matrix_path),
            "matrix_candidate_count": len(matrix),
            "selected_candidate_count": len(selected_rows),
            "selected_candidate_id": str(sel.get("candidate_id", "")).strip(),
            "selected_candidate_type": str(sel.get("candidate_type", "")).strip(),
            "inventory_snapshot_path": str(inv_snapshot),
            "external_candidate_source_path": str(ext_path) if ext_path else "",
            "stale_reasons": [],
        }
    )
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
