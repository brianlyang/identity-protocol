#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
ERR_ROUTING_LEARNING_STRENGTHENING_INVALID = "IP-RLSTR-001"

ROUTE_DISCOVERY_DEFAULT = {
    "contract_ref": "route_discovery_convergence_contract_v1",
    "validator": "scripts/validate_capability_fit_roundtable_evidence.py",
    "supporting_validators": [
        "scripts/validate_discovery_requiredization.py",
        "scripts/validate_identity_orchestration_contract.py",
        "scripts/validate_identity_knowledge_contract.py",
    ],
    "candidate_rows_required": True,
    "selected_candidate_field": "selected_candidate_id",
    "selection_basis_field": "selection_basis",
    "serial_convergence_required": True,
    "convergence_status_field": "convergence_status",
    "fallback_route_field": "fallback_route_if_selected_fails",
}

FEEDBACK_OPERATIONAL_PROMPT_DEFAULT = {
    "contract_ref": "feedback_operational_prompt_contract_v1",
    "validator": "scripts/validate_identity_experience_feedback_governance.py",
    "supporting_validators": [
        "scripts/validate_identity_experience_feedback.py",
    ],
    "rulebook_delta_required": True,
    "operational_prompt_ref_field": "operational_prompt_ref",
    "prompt_injection_status_field": "prompt_injection_status",
    "replay_status_field": "replay_status",
    "rollback_prompt_ref_required": True,
    "ttl_rounds_required": True,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path).expanduser()
        if not p.is_absolute():
            p = (catalog_path.expanduser().resolve().parent / p).resolve()
        task_path = (p / "CURRENT_TASK.json").resolve()
        if task_path.exists():
            return task_path
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _validate_hook(
    *,
    node: Any,
    defaults: dict[str, Any],
    status_prefix: str,
    required: bool,
) -> tuple[str, list[str], dict[str, Any]]:
    stale_reasons: list[str] = []
    if not required and not isinstance(node, dict):
        return STATUS_SKIPPED_NOT_REQUIRED, stale_reasons, {}
    if not isinstance(node, dict) or not node:
        return STATUS_FAIL_REQUIRED, [f"{status_prefix}_missing"], {}

    projection: dict[str, Any] = {}
    for key, expected in defaults.items():
        current = node.get(key)
        if key == "supporting_validators":
            current_list = _as_list(current)
            expected_list = _as_list(expected)
            if set(expected_list) - set(current_list):
                stale_reasons.append(f"{status_prefix}_{key}_missing_required_entries")
            projection[key] = current_list
            continue
        if current != expected:
            stale_reasons.append(f"{status_prefix}_{key}_mismatch")
        projection[key] = current

    return (STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED), stale_reasons, projection


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate v1.6.17 routing/learning strengthening symmetry.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--operation", default="", help="accepted for gate-runner compatibility")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as exc:
        payload = {
            "routing_learning_strengthening_status": STATUS_FAIL_REQUIRED,
            "route_discovery_convergence_status": STATUS_FAIL_REQUIRED,
            "feedback_operational_prompt_status": STATUS_FAIL_REQUIRED,
            "required_contract": True,
            "error_code": ERR_ROUTING_LEARNING_STRENGTHENING_INVALID,
            "stale_reasons": [f"current_task_resolve_failed:{type(exc).__name__}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    task = _load_json(task_path)
    arbitration = task.get("capability_arbitration_contract") or {}
    orchestration = task.get("capability_orchestration_contract") or {}
    knowledge = task.get("knowledge_acquisition_contract") or {}
    feedback = task.get("experience_feedback_contract") or {}

    arbitration_required = isinstance(arbitration, dict) and arbitration.get("required") is True
    route_required = (
        arbitration_required
        and isinstance(orchestration, dict)
        and orchestration.get("required") is True
        and isinstance(knowledge, dict)
        and knowledge.get("required") is True
    )
    feedback_required = (
        arbitration_required
        and isinstance(feedback, dict)
        and feedback.get("required") is True
    )

    route_status, route_reasons, route_projection = _validate_hook(
        node=(arbitration.get("route_discovery_enforcement") if isinstance(arbitration, dict) else {}),
        defaults=ROUTE_DISCOVERY_DEFAULT,
        status_prefix="route_discovery_enforcement",
        required=route_required,
    )
    feedback_status, feedback_reasons, feedback_projection = _validate_hook(
        node=(arbitration.get("feedback_operational_prompt_enforcement") if isinstance(arbitration, dict) else {}),
        defaults=FEEDBACK_OPERATIONAL_PROMPT_DEFAULT,
        status_prefix="feedback_operational_prompt_enforcement",
        required=feedback_required,
    )

    stale_reasons = [*route_reasons, *feedback_reasons]
    overall_status = STATUS_PASS_REQUIRED
    if route_status == STATUS_FAIL_REQUIRED or feedback_status == STATUS_FAIL_REQUIRED:
        overall_status = STATUS_FAIL_REQUIRED
    elif route_status == STATUS_SKIPPED_NOT_REQUIRED and feedback_status == STATUS_SKIPPED_NOT_REQUIRED:
        overall_status = STATUS_SKIPPED_NOT_REQUIRED

    payload = {
        "routing_learning_strengthening_status": overall_status,
        "route_discovery_convergence_status": route_status,
        "feedback_operational_prompt_status": feedback_status,
        "required_contract": bool(route_required or feedback_required),
        "error_code": "" if overall_status != STATUS_FAIL_REQUIRED else ERR_ROUTING_LEARNING_STRENGTHENING_INVALID,
        "identity_id": args.identity_id,
        "task_path": str(task_path),
        "route_discovery_enforcement": route_projection,
        "feedback_operational_prompt_enforcement": feedback_projection,
        "selected_candidate_id": str(route_projection.get("selected_candidate_field", "")).strip(),
        "selection_basis": str(route_projection.get("selection_basis_field", "")).strip(),
        "convergence_status": (
            "strengthening_linked"
            if route_status == STATUS_PASS_REQUIRED
            else ("not_required" if route_status == STATUS_SKIPPED_NOT_REQUIRED else "strengthening_missing_or_invalid")
        ),
        "prompt_injection_status": (
            "strengthening_linked"
            if feedback_status == STATUS_PASS_REQUIRED
            else ("not_required" if feedback_status == STATUS_SKIPPED_NOT_REQUIRED else "strengthening_missing_or_invalid")
        ),
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if overall_status != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
