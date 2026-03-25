#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_corpus_governance_common import find_missing_markers
from root_corpus_law_bundle_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    bundle_anchor_checks_from_doc,
    bundle_components_from_doc,
    load_mapping_descriptor,
    load_root_corpus_law_bundle,
    required_component_descriptor_fields_from_doc,
    require_component_descriptor_concordance,
)

STATUS_KEY = "protocol_root_corpus_law_bundle_status"
ERR_REGISTRY = "IP-RCLB-001"
ERR_STRUCTURE = "IP-RCLB-002"
ERR_BUNDLE = "IP-RCLB-003"

EXPECTED_COMPONENTS = {
    "root_corpus_governance": {
        "component_role": "root_admission_and_corpus_structure",
        "current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_governance.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh",
        "common_script": "scripts/root_corpus_governance_common.py",
        "status_key": "protocol_root_corpus_governance_status",
    },
    "root_corpus_ordering": {
        "component_role": "source_order_reading_order_and_adjudication_surface_roles",
        "current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_ordering.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh",
        "common_script": "scripts/root_corpus_ordering_common.py",
        "status_key": "protocol_root_corpus_ordering_status",
    },
    "root_corpus_authority": {
        "component_role": "authority_layering_and_terminality_split",
        "current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_authority.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh",
        "common_script": "scripts/root_corpus_authority_common.py",
        "status_key": "protocol_root_corpus_authority_status",
    },
    "root_corpus_question_routing": {
        "component_role": "question_class_and_answer_surface_pairing",
        "current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_question_routing.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh",
        "common_script": "scripts/root_corpus_question_routing_common.py",
        "status_key": "protocol_root_corpus_question_routing_status",
    },
    "root_constitutional_spine": {
        "component_role": "constitutional_entry_order_and_bridge_coherence",
        "current_file": "identity/protocol/mappings/root-constitutional-spine.current.yaml",
        "validator_script": "scripts/validate_protocol_root_constitutional_spine.py",
        "probe_script": "scripts/ci/run_protocol_root_constitutional_spine_probes_ci.sh",
        "common_script": "scripts/root_constitutional_spine_common.py",
        "status_key": "protocol_root_constitutional_spine_status",
    },
    "root_corpus_derivation": {
        "component_role": "one_way_derivation_and_non_reverse_authorship",
        "current_file": "identity/protocol/mappings/root-corpus-derivation.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_derivation.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh",
        "common_script": "scripts/root_corpus_derivation_common.py",
        "status_key": "protocol_root_corpus_derivation_status",
    },
    "root_corpus_transition": {
        "component_role": "promotion_demotion_and_reentry_governance",
        "current_file": "identity/protocol/mappings/root-corpus-transition.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_transition.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh",
        "common_script": "scripts/root_corpus_transition_common.py",
        "status_key": "protocol_root_corpus_transition_status",
    },
    "root_corpus_gateway_admissibility": {
        "component_role": "gateway_input_and_effect_target_scope",
        "current_file": "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_gateway_admissibility.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh",
        "common_script": "scripts/root_corpus_gateway_admissibility_common.py",
        "status_key": "protocol_root_corpus_gateway_admissibility_status",
    },
    "root_machine_registry_completeness": {
        "component_role": "registry_admission_of_root_mapping_families",
        "current_file": "identity/protocol/mappings/root-machine-registry-completeness.current.yaml",
        "validator_script": "scripts/validate_protocol_root_machine_registry_completeness.py",
        "probe_script": "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh",
        "common_script": "scripts/root_machine_registry_completeness_common.py",
        "status_key": "protocol_root_machine_registry_completeness_status",
    },
    "root_corpus_precedence": {
        "component_role": "conflict_precedence_and_terminal_machine_enforcement",
        "current_file": "identity/protocol/mappings/root-corpus-precedence.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_precedence.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh",
        "common_script": "scripts/root_corpus_precedence_common.py",
        "status_key": "protocol_root_corpus_precedence_status",
    },
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _run_component_validator(repo_root, validator_script: str, status_key: str) -> tuple[int, dict[str, Any], str]:
    cmd = ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()
    if not stdout:
        return proc.returncode, {}, "validator_output_missing"
    try:
        payload = json.loads(stdout)
    except Exception:
        return proc.returncode, {}, "validator_output_invalid_json"
    if status_key not in payload:
        return proc.returncode, payload, "validator_status_key_missing"
    return proc.returncode, payload, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the governed root-corpus law bundle.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    bundle_doc, bundle_entry_path, bundle_active_path, bundle_alias_error = load_root_corpus_law_bundle(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    bundle_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    component_status_rows: list[dict[str, Any]] = []
    error_code = ""

    if bundle_alias_error:
        stale_reasons.append(f"root_corpus_law_bundle_alias_error:{bundle_alias_error}")
        error_code = ERR_REGISTRY
    elif not bundle_doc:
        stale_reasons.append("root_corpus_law_bundle_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = bundle_anchor_checks_from_doc(bundle_doc) if bundle_doc else ()
    components = bundle_components_from_doc(bundle_doc) if bundle_doc else ()
    descriptor_concordance_required = require_component_descriptor_concordance(bundle_doc) if bundle_doc else False
    required_component_descriptor_fields = (
        required_component_descriptor_fields_from_doc(bundle_doc) if bundle_doc else ()
    )
    component_map = {row.component_id: row for row in components}
    sorted_components = sorted(components, key=lambda row: row.order)
    component_orders = [row.order for row in components]

    if not stale_reasons:
        if str(bundle_doc.get("law_bundle_family") or "").strip() != "protocol_root_corpus_law_bundle":
            stale_reasons.append("root_corpus_law_bundle_family_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("law_bundle_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_law_bundle_version_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("root_dir") or "").strip() != "identity/protocol":
            stale_reasons.append("root_corpus_law_bundle_root_dir_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_law_bundle.py":
            stale_reasons.append("root_corpus_law_bundle_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_law_bundle_probes_ci.sh":
            stale_reasons.append("root_corpus_law_bundle_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("common_script") or "").strip() != "scripts/root_corpus_law_bundle_common.py":
            stale_reasons.append("root_corpus_law_bundle_common_script_invalid")
            error_code = ERR_REGISTRY
        if bundle_doc.get("require_component_descriptor_concordance") is not True:
            stale_reasons.append("root_corpus_law_bundle_descriptor_concordance_rule_invalid")
            error_code = ERR_REGISTRY
        if tuple(required_component_descriptor_fields) != ("validator_script", "probe_script", "common_script", "status_key"):
            stale_reasons.append("root_corpus_law_bundle_required_component_descriptor_fields_invalid")
            error_code = ERR_REGISTRY
        if descriptor_concordance_required and not required_component_descriptor_fields:
            stale_reasons.append("root_corpus_law_bundle_required_component_descriptor_fields_missing")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(bundle_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_law_bundle_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_law_bundle_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not components:
            stale_reasons.append("root_corpus_law_bundle_components_missing")
            error_code = ERR_REGISTRY

    if not stale_reasons:
        if len(component_map) != len(components):
            structure_violations.append({"field": "component_rows", "reason": "duplicate_component_id"})
        if len(set(component_orders)) != len(component_orders) or not _contiguous_orders(sorted(component_orders)):
            structure_violations.append({"field": "component_rows", "reason": "component_order_non_contiguous"})

        missing_components = sorted(set(EXPECTED_COMPONENTS) - set(component_map))
        extra_components = sorted(set(component_map) - set(EXPECTED_COMPONENTS))
        if missing_components:
            structure_violations.append(
                {"field": "component_rows", "reason": "missing_expected_components", "component_ids": missing_components}
            )
        if extra_components:
            structure_violations.append(
                {"field": "component_rows", "reason": "extra_components", "component_ids": extra_components}
            )

        for row in sorted_components:
            expected = EXPECTED_COMPONENTS.get(row.component_id)
            if expected is None:
                continue
            for field in ("component_role", "current_file", "validator_script", "probe_script", "common_script", "status_key"):
                if getattr(row, field) != expected[field]:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": f"{field}_mismatch",
                            "expected": expected[field],
                            "actual": getattr(row, field),
                        }
                    )

            current_path = (repo_root / row.current_file).resolve()
            if not current_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_current_file_missing"})
            else:
                active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, row.current_file)
                if alias_error:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_current_alias_error",
                            "alias_error": alias_error,
                        }
                    )
                elif not active_path.exists():
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_active_file_missing",
                            "active_path": str(active_path),
                        }
                    )

            validator_path = (repo_root / row.validator_script).resolve()
            if not validator_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_validator_missing"})
                continue

            probe_path = (repo_root / row.probe_script).resolve()
            if not probe_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_probe_missing"})

            common_path = (repo_root / row.common_script).resolve()
            if not common_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_common_missing"})

            rc, payload, run_error = _run_component_validator(repo_root, row.validator_script, row.status_key)
            component_status = str(payload.get(row.status_key) or "")
            descriptor_field_rows: list[dict[str, str]] = []
            component_status_rows.append(
                {
                    "order": row.order,
                    "component_id": row.component_id,
                    "status_key": row.status_key,
                    "validator_script": row.validator_script,
                    "probe_script": row.probe_script,
                    "common_script": row.common_script,
                    "validator_rc": rc,
                    "component_status": component_status,
                    "validator_error": run_error,
                    "descriptor_concordance_required": descriptor_concordance_required,
                    "required_component_descriptor_fields": list(required_component_descriptor_fields),
                    "descriptor_field_rows": descriptor_field_rows,
                }
            )
            if run_error:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": run_error,
                        "validator_rc": rc,
                    }
                )
            elif rc != 0:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_validator_nonzero_rc",
                        "validator_rc": rc,
                        "component_status": component_status,
                    }
                )
            elif component_status != STATUS_PASS_REQUIRED:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_status_not_pass_required",
                        "component_status": component_status,
                    }
                )

            if descriptor_concordance_required and current_path.exists():
                active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, row.current_file)
                if not alias_error and active_path.exists():
                    active_doc = load_mapping_descriptor(active_path)
                    if not active_doc:
                        bundle_violations.append(
                            {
                                "component_id": row.component_id,
                                "reason": "component_active_descriptor_invalid",
                                "active_path": str(active_path),
                            }
                        )
                    else:
                        for descriptor_field in required_component_descriptor_fields:
                            bundle_rel_path = str(getattr(row, descriptor_field) or "")
                            active_rel_path = str(active_doc.get(descriptor_field) or "").strip()
                            descriptor_field_rows.append(
                                {
                                    "field": descriptor_field,
                                    "bundle_rel_path": bundle_rel_path,
                                    "active_rel_path": active_rel_path,
                                    "status": (
                                        STATUS_PASS_REQUIRED
                                        if active_rel_path == bundle_rel_path and active_rel_path
                                        else STATUS_FAIL_REQUIRED
                                    ),
                                }
                            )
                            if not active_rel_path:
                                bundle_violations.append(
                                    {
                                        "component_id": row.component_id,
                                        "reason": "component_descriptor_field_missing",
                                        "descriptor_field": descriptor_field,
                                    }
                                )
                            elif active_rel_path != bundle_rel_path:
                                bundle_violations.append(
                                    {
                                        "component_id": row.component_id,
                                        "reason": "component_descriptor_concordance_failure",
                                        "descriptor_field": descriptor_field,
                                        "bundle_rel_path": bundle_rel_path,
                                        "active_rel_path": active_rel_path,
                                    }
                                )

        for check in anchor_checks:
            path = (repo_root / check.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append({"rel_path": check.rel_path, "reason": "anchor_file_missing"})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in find_missing_markers(text, check.required_markers):
                anchor_violations.append(
                    {
                        "rel_path": check.rel_path,
                        "reason": "required_marker_missing",
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (bundle_violations or anchor_violations):
        error_code = ERR_BUNDLE

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"bundle_violation:{row['component_id']}:{row['reason']}" for row in bundle_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_BUNDLE),
        "bundle_entry_path": str(bundle_entry_path),
        "bundle_active_path": str(bundle_active_path),
        "root_dir": str(bundle_doc.get("root_dir") or ""),
        "bundle_anchor_check_count": len(anchor_checks),
        "component_count": len(components),
        "component_ids": [row.component_id for row in sorted_components],
        "component_status_rows": component_status_rows,
        "structure_violations": structure_violations,
        "bundle_violations": bundle_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
