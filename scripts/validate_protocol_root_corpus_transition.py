#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_derivation_common import derivation_class_profiles_from_doc, load_root_corpus_derivation
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_question_routing_common import adjudication_redirect_from_doc, load_root_corpus_question_routing
from root_row_family_projection_common import aggregate_row_family_status, project_row_family
from root_corpus_transition_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    load_root_corpus_transition,
    transition_anchor_checks_from_doc,
    transition_surface_profiles_from_doc,
)

STATUS_KEY = "protocol_root_corpus_transition_status"
ERR_REGISTRY = "IP-RCT-001"
ERR_STRUCTURE = "IP-RCT-002"
ERR_TRANSITION = "IP-RCT-003"

OUTER_SURFACE_EXPECTATIONS = {
    "outer_governance_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "outer_review_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "outer_workbook_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "outer_reference_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("root_contract", "machine_registry_directory"),
    },
    "outer_evidence_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "outer_runtime_state_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "outer_receipt_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("root_contract", "machine_registry_directory"),
    },
    "outer_implementation_surface": {
        "surface_scope": "outer",
        "law_bearing": False,
        "transition_mode": "governed_motivation_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("root_contract", "machine_registry_directory"),
    },
}

ROOT_TRANSITION_EXPECTATIONS = {
    "bottom_theory": {
        "surface_scope": "root",
        "transition_mode": "generative_origin",
        "direct_root_targets": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory", "governed_subdomain_extension"),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": (),
    },
    "root_index": {
        "surface_scope": "root",
        "transition_mode": "navigational_projection_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "constitution": {
        "surface_scope": "root",
        "transition_mode": "constitutional_freeze",
        "direct_root_targets": ("runtime_constitution", "root_contract", "machine_registry_directory", "governed_subdomain_extension"),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": (),
    },
    "runtime_constitution": {
        "surface_scope": "root",
        "transition_mode": "runtime_constitutional_freeze",
        "direct_root_targets": ("root_contract", "machine_registry_directory", "governed_subdomain_extension"),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": (),
    },
    "root_contract": {
        "surface_scope": "root",
        "transition_mode": "domain_contract_freeze",
        "direct_root_targets": ("machine_registry_directory", "governed_subdomain_extension"),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": (),
    },
    "machine_registry_directory": {
        "surface_scope": "root",
        "transition_mode": "machine_registry_projection",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": True,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract"),
    },
    "governed_subdomain_extension": {
        "surface_scope": "root",
        "transition_mode": "governed_extension_projection",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
    "demoted_support_directory": {
        "surface_scope": "root",
        "transition_mode": "demoted_support_only",
        "direct_root_targets": (),
        "direct_current_turn_legality_allowed": False,
        "strengthening_gateways": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
    },
}

ALLOWED_REENTRY_GATEWAYS = {"constitution", "runtime_constitution", "root_contract", "machine_registry_directory"}
EXPECTED_CURRENT_TURN_ROOT_CLASS = "machine_registry_directory"
EXPECTED_SURFACE_CLASSES = sorted(set(ROOT_TRANSITION_EXPECTATIONS) | set(OUTER_SURFACE_EXPECTATIONS))


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus promotion/demotion/re-entry topology.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    transition_doc, transition_entry_path, transition_active_path, transition_alias_error = load_root_corpus_transition(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    derivation_doc, derivation_entry_path, derivation_active_path, derivation_alias_error = load_root_corpus_derivation(repo_root)
    question_routing_doc, question_routing_entry_path, question_routing_active_path, question_routing_alias_error = (
        load_root_corpus_question_routing(repo_root)
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    transition_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if transition_alias_error:
        stale_reasons.append(f"root_corpus_transition_alias_error:{transition_alias_error}")
        error_code = ERR_REGISTRY
    elif not transition_doc:
        stale_reasons.append("root_corpus_transition_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if derivation_alias_error:
        stale_reasons.append(f"root_corpus_derivation_alias_error:{derivation_alias_error}")
        error_code = ERR_REGISTRY
    elif not derivation_doc:
        stale_reasons.append("root_corpus_derivation_empty_or_invalid")
        error_code = ERR_REGISTRY

    if question_routing_alias_error:
        stale_reasons.append(f"root_corpus_question_routing_alias_error:{question_routing_alias_error}")
        error_code = ERR_REGISTRY
    elif not question_routing_doc:
        stale_reasons.append("root_corpus_question_routing_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = transition_anchor_checks_from_doc(transition_doc) if transition_doc else ()
    surface_profiles = transition_surface_profiles_from_doc(transition_doc) if transition_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    derivation_profiles = derivation_class_profiles_from_doc(derivation_doc) if derivation_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})

    if not stale_reasons:
        if str(transition_doc.get("transition_family") or "").strip() != "protocol_root_corpus_transition":
            stale_reasons.append("root_corpus_transition_family_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("transition_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_transition_version_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_transition_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_transition_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("derivation_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-derivation.current.yaml":
            stale_reasons.append("root_corpus_transition_derivation_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("question_routing_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-question-routing.current.yaml":
            stale_reasons.append("root_corpus_transition_question_routing_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_transition.py":
            stale_reasons.append("root_corpus_transition_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh":
            stale_reasons.append("root_corpus_transition_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(transition_doc.get("common_script") or "").strip() != "scripts/root_corpus_transition_common.py":
            stale_reasons.append("root_corpus_transition_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(transition_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_transition_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_transition_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not surface_profiles:
            stale_reasons.append("root_corpus_transition_surface_profiles_missing")
            error_code = ERR_REGISTRY

    registry_class_law_bearing = {entry.corpus_class: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    derivation_upstream_map = {row.corpus_class: set(row.allowed_upstream_classes) for row in derivation_profiles}
    anchor_rel_paths = [row.rel_path for row in anchor_checks]
    surface_profile_map = {row.surface_class: row for row in surface_profiles}
    expected_surface_classes = EXPECTED_SURFACE_CLASSES
    sorted_profiles = sorted(surface_profiles, key=lambda item: item.surface_class)
    direct_root_target_edges = sorted(
        (
            SimpleNamespace(
                edge_id=f"{row.surface_class}->{target}",
                surface_class=row.surface_class,
                target=target,
            )
            for row in sorted_profiles
            for target in row.direct_root_targets
        ),
        key=lambda item: item.edge_id,
    )
    strengthening_gateway_edges = sorted(
        (
            SimpleNamespace(
                edge_id=f"{row.surface_class}->{gateway}",
                surface_class=row.surface_class,
                gateway=gateway,
            )
            for row in sorted_profiles
            for gateway in row.strengthening_gateways
        ),
        key=lambda item: item.edge_id,
    )
    expected_direct_root_target_edges = {
        f"{surface_class}->{target}": {"surface_class": surface_class, "target": target}
        for surface_class, expected in {**ROOT_TRANSITION_EXPECTATIONS, **OUTER_SURFACE_EXPECTATIONS}.items()
        for target in expected["direct_root_targets"]
    }
    expected_strengthening_gateway_edges = {
        f"{surface_class}->{gateway}": {"surface_class": surface_class, "gateway": gateway}
        for surface_class, expected in {**ROOT_TRANSITION_EXPECTATIONS, **OUTER_SURFACE_EXPECTATIONS}.items()
        for gateway in expected["strengthening_gateways"]
    }

    if not stale_reasons:
        if len(surface_profile_map) != len(surface_profiles):
            structure_violations.append({"field": "surface_class_profiles", "reason": "duplicate_surface_class"})
        if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
            structure_violations.append({"field": "transition_anchor_checks", "reason": "duplicate_rel_path"})

        missing_surface_classes = sorted(set(expected_surface_classes) - set(surface_profile_map))
        extra_surface_classes = sorted(set(surface_profile_map) - set(expected_surface_classes))
        if missing_surface_classes:
            structure_violations.append(
                {"field": "surface_class_profiles", "reason": "missing_expected_surface_classes", "surface_classes": missing_surface_classes}
            )
        if extra_surface_classes:
            structure_violations.append(
                {"field": "surface_class_profiles", "reason": "extra_surface_classes", "surface_classes": extra_surface_classes}
            )

        registry_paths = {entry.rel_path for entry in registry_entries}
        missing_anchor_entries = sorted(set(anchor_rel_paths) - registry_paths)
        if missing_anchor_entries:
            structure_violations.append(
                {"field": "transition_anchor_checks", "reason": "unregistered_anchor_entries", "rel_paths": missing_anchor_entries}
            )

        for row in surface_profiles:
            expected = ROOT_TRANSITION_EXPECTATIONS.get(row.surface_class, OUTER_SURFACE_EXPECTATIONS.get(row.surface_class))
            if expected is None:
                continue
            if row.surface_scope != expected["surface_scope"]:
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "surface_scope_mismatch",
                        "surface_class": row.surface_class,
                        "expected": expected["surface_scope"],
                        "actual": row.surface_scope,
                    }
                )
            expected_law_bearing = registry_class_law_bearing.get(
                row.surface_class,
                expected.get("law_bearing", False),
            )
            if bool(row.law_bearing) != bool(expected_law_bearing):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "law_bearing_mismatch",
                        "surface_class": row.surface_class,
                        "expected": bool(expected_law_bearing),
                        "actual": bool(row.law_bearing),
                    }
                )
            if row.transition_mode != expected["transition_mode"]:
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "transition_mode_mismatch",
                        "surface_class": row.surface_class,
                        "expected": expected["transition_mode"],
                        "actual": row.transition_mode,
                    }
                )
            if tuple(row.direct_root_targets) != tuple(expected["direct_root_targets"]):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "direct_root_targets_mismatch",
                        "surface_class": row.surface_class,
                        "expected": list(expected["direct_root_targets"]),
                        "actual": list(row.direct_root_targets),
                    }
                )
            if bool(row.direct_current_turn_legality_allowed) != bool(expected["direct_current_turn_legality_allowed"]):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "direct_current_turn_legality_mismatch",
                        "surface_class": row.surface_class,
                        "expected": bool(expected["direct_current_turn_legality_allowed"]),
                        "actual": bool(row.direct_current_turn_legality_allowed),
                    }
                )
            if tuple(row.strengthening_gateways) != tuple(expected["strengthening_gateways"]):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "strengthening_gateways_mismatch",
                        "surface_class": row.surface_class,
                        "expected": list(expected["strengthening_gateways"]),
                        "actual": list(row.strengthening_gateways),
                    }
                )

            if len(set(row.direct_root_targets)) != len(row.direct_root_targets):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "duplicate_direct_root_targets",
                        "surface_class": row.surface_class,
                    }
                )
            if len(set(row.strengthening_gateways)) != len(row.strengthening_gateways):
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "duplicate_strengthening_gateways",
                        "surface_class": row.surface_class,
                    }
                )

            for gateway in row.strengthening_gateways:
                if gateway not in ALLOWED_REENTRY_GATEWAYS:
                    transition_violations.append(
                        {
                            "field": "surface_class_profiles",
                            "reason": "invalid_strengthening_gateway",
                            "surface_class": row.surface_class,
                            "gateway": gateway,
                        }
                    )

            if row.surface_scope == "outer" and row.direct_root_targets:
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "outer_surface_must_not_directly_promote_root_law",
                        "surface_class": row.surface_class,
                    }
                )
            if row.surface_class == "demoted_support_directory" and row.direct_root_targets:
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "demoted_support_must_not_directly_promote_root_law",
                        "surface_class": row.surface_class,
                    }
                )
            if row.surface_class == "root_index" and row.direct_root_targets:
                transition_violations.append(
                    {
                        "field": "surface_class_profiles",
                        "reason": "root_index_must_not_author_root_law",
                        "surface_class": row.surface_class,
                    }
                )

            for target in row.direct_root_targets:
                if target not in registry_class_law_bearing:
                    transition_violations.append(
                        {
                            "field": "surface_class_profiles",
                            "reason": "direct_root_target_not_registered",
                            "surface_class": row.surface_class,
                            "target": target,
                        }
                    )
                    continue
                if not registry_class_law_bearing.get(target, False):
                    transition_violations.append(
                        {
                            "field": "surface_class_profiles",
                            "reason": "direct_root_target_not_law_bearing",
                            "surface_class": row.surface_class,
                            "target": target,
                        }
                    )
                allowed_upstreams = derivation_upstream_map.get(target, set())
                if row.surface_class not in allowed_upstreams:
                    transition_violations.append(
                        {
                            "field": "surface_class_profiles",
                            "reason": "direct_root_target_incompatible_with_derivation",
                            "surface_class": row.surface_class,
                            "target": target,
                        }
                    )

        current_turn_allowed_classes = sorted(
            row.surface_class for row in surface_profiles if row.direct_current_turn_legality_allowed
        )
        expected_current_turn_allowed_classes = [EXPECTED_CURRENT_TURN_ROOT_CLASS]
        if current_turn_allowed_classes != expected_current_turn_allowed_classes:
            transition_violations.append(
                {
                    "field": "surface_class_profiles",
                    "reason": "current_turn_allowed_surface_set_mismatch",
                    "expected": expected_current_turn_allowed_classes,
                    "actual": current_turn_allowed_classes,
                }
            )

        actual_forbidden_root_classes = sorted(set(adjudication_redirect.forbidden_root_corpus_classes))
        expected_forbidden_root_classes = sorted(set(registry_classes) - {EXPECTED_CURRENT_TURN_ROOT_CLASS})
        if actual_forbidden_root_classes != expected_forbidden_root_classes:
            transition_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "forbidden_root_classes_mismatch",
                    "expected": expected_forbidden_root_classes,
                    "actual": actual_forbidden_root_classes,
                }
            )

        for row in anchor_checks:
            path = (repo_root / row.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append({"rel_path": row.rel_path, "reason": "anchor_target_missing"})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in find_missing_markers(text, row.required_markers):
                anchor_violations.append(
                    {
                        "rel_path": row.rel_path,
                        "reason": "required_marker_missing",
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (transition_violations or anchor_violations):
        error_code = ERR_TRANSITION

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"transition_violation:{row['field']}:{row['reason']}" for row in transition_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    row_family_projection_rows = [
        project_row_family(
            family_id="surface_class_profiles",
            member_id_key="surface_class",
            actual_rows=[SimpleNamespace(surface_class=row.surface_class) for row in sorted_profiles],
            expected_rows={surface_class: {} for surface_class in expected_surface_classes},
            id_attr="surface_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="direct_root_target_edges",
            member_id_key="edge_id",
            actual_rows=direct_root_target_edges,
            expected_rows=expected_direct_root_target_edges,
            id_attr="edge_id",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="strengthening_gateway_edges",
            member_id_key="edge_id",
            actual_rows=strengthening_gateway_edges,
            expected_rows=expected_strengthening_gateway_edges,
            id_attr="edge_id",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
    ]
    transition_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    transition_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_TRANSITION),
        "transition_entry_path": str(transition_entry_path),
        "transition_active_path": str(transition_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "derivation_entry_path": str(derivation_entry_path),
        "derivation_active_path": str(derivation_active_path),
        "question_routing_entry_path": str(question_routing_entry_path),
        "question_routing_active_path": str(question_routing_active_path),
        "root_dir": str(transition_doc.get("root_dir") or ""),
        "transition_anchor_check_count": len(anchor_checks),
        "surface_class_profile_count": len(surface_profiles),
        "direct_root_target_edge_count": len(direct_root_target_edges),
        "strengthening_gateway_edge_count": len(strengthening_gateway_edges),
        "transition_row_family_count": len(row_family_projection_rows),
        "transition_row_coverage_status": transition_row_coverage_status,
        "transition_row_identity_projection_status": transition_row_identity_projection_status,
        "row_family_projection_rows": row_family_projection_rows,
        "current_turn_allowed_root_surface": EXPECTED_CURRENT_TURN_ROOT_CLASS,
        "surface_class_profiles": [
            {
                "surface_class": row.surface_class,
                "surface_scope": row.surface_scope,
                "law_bearing": row.law_bearing,
                "transition_mode": row.transition_mode,
                "direct_root_targets": list(row.direct_root_targets),
                "direct_current_turn_legality_allowed": row.direct_current_turn_legality_allowed,
                "strengthening_gateways": list(row.strengthening_gateways),
            }
            for row in sorted_profiles
        ],
        "direct_root_target_edges": [
            {
                "surface_class": row.surface_class,
                "target": row.target,
            }
            for row in direct_root_target_edges
        ],
        "strengthening_gateway_edges": [
            {
                "surface_class": row.surface_class,
                "gateway": row.gateway,
            }
            for row in strengthening_gateway_edges
        ],
        "structure_violations": structure_violations,
        "transition_violations": transition_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
