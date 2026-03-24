#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

WEAK_LIVE_LINKAGE_CONTRACT_KEY = "identity_weak_live_linkage_contract_v1"
WEAK_LIVE_LINKAGE_CONTRACT_ID = "rq_055_identity_weak_live_linkage_differential_audit_contract_v1"
WEAK_LIVE_LINKAGE_VALIDATOR_ID = "scripts/validate_identity_weak_live_linkage.py"
WEAK_LIVE_LINKAGE_PROBE_RUNNER_ID = "scripts/ci/run_identity_weak_live_linkage_probes_ci.sh"
ROUNDTABLE_SHARED_PRIMITIVE = "roundtable_four_track_cross_validation_contract_v1"

TRUTH_LIFECYCLE_ORDER: tuple[str, ...] = (
    "truth_exists",
    "truth_discoverable",
    "truth_admissible",
    "truth_bound",
    "truth_consumed",
)

PRIMARY_FALSE_GREEN_FAMILIES: tuple[str, ...] = (
    "prompt_presence_only",
    "sample_report_only",
    "loop_meta_only",
)

SECONDARY_FALSE_GREEN_FAMILIES: tuple[str, ...] = (
    "latest_log_no_run_binding",
)

ALLOWED_VERDICT_CLASSES: tuple[str, ...] = (
    "structure_green",
    "sample_or_history_green",
    "unabsorbed_green",
    "full_operational_closure",
)

REQUIRED_LAYER_FIELDS: tuple[str, ...] = (
    "contract_layer_status",
    "artifact_layer_status",
    "run_binding_layer_status",
    "consumption_layer_status",
)

REQUIRED_REPORT_FIELDS: tuple[str, ...] = (
    "identity_weak_live_linkage_status",
    "weak_live_linkage_contract_status",
    "contract_layer_status",
    "artifact_layer_status",
    "run_binding_layer_status",
    "consumption_layer_status",
    "overall_linkage_status",
    "operational_closure_class",
    "false_green_family",
    "evidence_origin",
    "live_binding_strength",
    "next_hop_consumption_status",
    "semantic_center_status",
    "live_bridge_status",
    "roundtable_alignment_status",
    "philosophy_truth_lifecycle_status",
    "stale_reasons",
    "error_code",
)

REQUIRED_COMPONENT_VALIDATORS: tuple[str, ...] = (
    "scripts/validate_prompt_bootstrap_capability.py",
    "scripts/validate_prompt_capability_matrix.py",
    "scripts/validate_prompt_derivation_conformance.py",
    "scripts/validate_identity_routing_learning_strengthening.py",
    "scripts/validate_feedback_to_judgement_loopback.py",
    "scripts/validate_capability_fit_roundtable_evidence.py",
    "scripts/validate_identity_experience_feedback_governance.py",
)


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def weak_live_linkage_contract_skeleton() -> dict[str, Any]:
    return {
        "required": True,
        "contract_id": WEAK_LIVE_LINKAGE_CONTRACT_ID,
        "validator": WEAK_LIVE_LINKAGE_VALIDATOR_ID,
        "probe_runner": WEAK_LIVE_LINKAGE_PROBE_RUNNER_ID,
        "fail_mode": "fail_required",
        "shared_cross_validation_primitive_refs": [ROUNDTABLE_SHARED_PRIMITIVE],
        "truth_lifecycle_order": list(TRUTH_LIFECYCLE_ORDER),
        "primary_false_green_families": list(PRIMARY_FALSE_GREEN_FAMILIES),
        "secondary_false_green_families": list(SECONDARY_FALSE_GREEN_FAMILIES),
        "allowed_verdict_classes": list(ALLOWED_VERDICT_CLASSES),
        "required_layer_fields": list(REQUIRED_LAYER_FIELDS),
        "required_report_fields": list(REQUIRED_REPORT_FIELDS),
        "required_component_validators": list(REQUIRED_COMPONENT_VALIDATORS),
        "strict_current_run_required": True,
        "distinguish_semantic_center_vs_live_bridge": True,
        "history_or_sample_not_strict_truth": True,
        "philosophy_anchor_refs": [
            "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "identity/protocol/README.md",
        ],
    }


def resolve_pack_task(
    *,
    catalog_path: Path | None,
    current_task: str,
    identity_id: str,
) -> tuple[Path, Path, dict[str, Any]]:
    if clean_string(current_task):
        task_path = Path(clean_string(current_task)).expanduser().resolve()
        if not task_path.is_file():
            raise FileNotFoundError(f"current_task_not_found:{task_path}")
        task_doc = load_json(task_path)
        return task_path.parent.resolve(), task_path.resolve(), task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = load_json(task_path)
    return pack_root.resolve(), task_path.resolve(), task_doc


def resolve_weak_live_linkage_contract(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract_doc = task_doc.get(WEAK_LIVE_LINKAGE_CONTRACT_KEY)
    if not isinstance(contract_doc, dict):
        contract_doc = {}
    return contract_required(contract_doc), contract_doc, WEAK_LIVE_LINKAGE_CONTRACT_KEY


def weak_live_linkage_contract_issues(contract_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if clean_string(contract_doc.get("contract_id")) != WEAK_LIVE_LINKAGE_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if clean_string(contract_doc.get("validator")) != WEAK_LIVE_LINKAGE_VALIDATOR_ID:
        issues.append("validator_mismatch")
    if clean_string(contract_doc.get("probe_runner")) != WEAK_LIVE_LINKAGE_PROBE_RUNNER_ID:
        issues.append("probe_runner_mismatch")
    if bool(contract_doc.get("required")) is not True:
        issues.append("required_flag_not_true")
    if clean_string(contract_doc.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")

    primitive_refs = {
        clean_string(item)
        for item in (contract_doc.get("shared_cross_validation_primitive_refs") or [])
        if clean_string(item)
    }
    if ROUNDTABLE_SHARED_PRIMITIVE not in primitive_refs:
        issues.append("roundtable_shared_primitive_missing")

    truth_lifecycle = [clean_string(item) for item in (contract_doc.get("truth_lifecycle_order") or []) if clean_string(item)]
    if truth_lifecycle != list(TRUTH_LIFECYCLE_ORDER):
        issues.append("truth_lifecycle_order_mismatch")

    primary_families = [clean_string(item) for item in (contract_doc.get("primary_false_green_families") or []) if clean_string(item)]
    if primary_families != list(PRIMARY_FALSE_GREEN_FAMILIES):
        issues.append("primary_false_green_families_mismatch")

    secondary_families = [clean_string(item) for item in (contract_doc.get("secondary_false_green_families") or []) if clean_string(item)]
    if secondary_families != list(SECONDARY_FALSE_GREEN_FAMILIES):
        issues.append("secondary_false_green_families_mismatch")

    verdict_classes = [clean_string(item) for item in (contract_doc.get("allowed_verdict_classes") or []) if clean_string(item)]
    if verdict_classes != list(ALLOWED_VERDICT_CLASSES):
        issues.append("allowed_verdict_classes_mismatch")

    layer_fields = [clean_string(item) for item in (contract_doc.get("required_layer_fields") or []) if clean_string(item)]
    if layer_fields != list(REQUIRED_LAYER_FIELDS):
        issues.append("required_layer_fields_mismatch")

    report_fields = [clean_string(item) for item in (contract_doc.get("required_report_fields") or []) if clean_string(item)]
    if report_fields != list(REQUIRED_REPORT_FIELDS):
        issues.append("required_report_fields_mismatch")

    component_validators = [
        clean_string(item)
        for item in (contract_doc.get("required_component_validators") or [])
        if clean_string(item)
    ]
    if component_validators != list(REQUIRED_COMPONENT_VALIDATORS):
        issues.append("required_component_validators_mismatch")

    philosophy_refs = [clean_string(item) for item in (contract_doc.get("philosophy_anchor_refs") or []) if clean_string(item)]
    if philosophy_refs != [
        "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "identity/protocol/README.md",
    ]:
        issues.append("philosophy_anchor_refs_mismatch")

    if bool(contract_doc.get("strict_current_run_required")) is not True:
        issues.append("strict_current_run_required_not_true")
    if bool(contract_doc.get("distinguish_semantic_center_vs_live_bridge")) is not True:
        issues.append("semantic_center_live_bridge_boundary_missing")
    if bool(contract_doc.get("history_or_sample_not_strict_truth")) is not True:
        issues.append("history_or_sample_boundary_missing")
    return issues


def derive_operational_closure_class(
    *,
    contract_layer_status: str,
    artifact_layer_status: str,
    run_binding_layer_status: str,
    consumption_layer_status: str,
) -> str:
    contract_ok = clean_string(contract_layer_status).upper() == STATUS_PASS_REQUIRED
    artifact_ok = clean_string(artifact_layer_status).upper() == STATUS_PASS_REQUIRED
    binding_ok = clean_string(run_binding_layer_status).upper() == STATUS_PASS_REQUIRED
    consumption_ok = clean_string(consumption_layer_status).upper() == STATUS_PASS_REQUIRED

    if contract_ok and artifact_ok and binding_ok and consumption_ok:
        return "full_operational_closure"
    if contract_ok and artifact_ok and binding_ok and not consumption_ok:
        return "unabsorbed_green"
    if contract_ok and artifact_ok and not binding_ok:
        return "sample_or_history_green"
    return "structure_green"


def overall_linkage_status_from_class(closure_class: str) -> str:
    token = clean_string(closure_class)
    return STATUS_PASS_REQUIRED if token == "full_operational_closure" else STATUS_FAIL_REQUIRED


def bool_to_status(value: bool) -> str:
    return STATUS_PASS_REQUIRED if value else STATUS_FAIL_REQUIRED


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))
