#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_contract_row_validation_common import contiguous_orders
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_corpus_governance_common import (
    load_root_corpus_registry,
    root_corpus_entries_from_registry,
)
from root_corpus_ordering_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    adjudication_order_rows_from_doc,
    adjudication_surface_profiles_from_doc,
    load_root_corpus_ordering,
    ordering_anchor_checks_from_doc,
    reading_order_rows_from_doc,
    source_order_rows_from_doc,
)
from root_corpus_precedence_common import load_root_corpus_precedence, precedence_profiles_from_doc
from root_corpus_question_routing_common import adjudication_redirect_from_doc, load_root_corpus_question_routing

STATUS_KEY = "protocol_root_corpus_ordering_status"
ERR_REGISTRY = "IP-RCO-001"
ERR_STRUCTURE = "IP-RCO-002"
ERR_COVERAGE = "IP-RCO-003"
ROOT_INDEX_ENTRY_ROLE = "root_index_entry_surface"
CURRENT_TURN_LEGALITY_CONFLICT = "current_turn_legality_conflict"
EXPECTED_ADJUDICATION_SURFACE_PROFILES = {
    "mappings": {
        "phase_order": 1,
        "surface_role": "admissible_law_resolution",
        "closure_terminal": False,
    },
    "validators": {
        "phase_order": 2,
        "surface_role": "governed_legality_evaluation",
        "closure_terminal": False,
    },
    "probes": {
        "phase_order": 3,
        "surface_role": "fail_close_drift_negation",
        "closure_terminal": False,
    },
    "runtime_state": {
        "phase_order": 4,
        "surface_role": "live_state_truth_binding",
        "closure_terminal": False,
    },
    "receipts": {
        "phase_order": 5,
        "surface_role": "adjudicated_verdict_closure",
        "closure_terminal": True,
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Root adjudication-surface discipline",
        "mappings admit applicable machine law and registry truth for current-turn legality;",
        "validators test legality against that admitted law rather than inventing new origin law;",
        "probes negate drift by fail-closing weakened or hidden legality assumptions;",
        "runtime state binds live current-turn truth only after prior legality phases have remained lawful;",
        "receipts close the adjudicated verdict and must not back-author earlier legality phases.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Adjudication surfaces are phase-governed, not interchangeable",
        "mappings admit applicable law into the current-turn legality path;",
        "validators evaluate legality against admitted law rather than inventing new origin law;",
        "probes negate hidden drift by fail-closing weakened legality assumptions;",
        "runtime state binds live present-turn truth only after the earlier legality phases remain lawful;",
        "receipts close the adjudicated verdict rather than back-authoring the earlier legality phases they summarize.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root adjudication-surface boundary",
        "mappings admit machine-consumed law and registry truth into current-turn legality;",
        "validators evaluate legality against that admitted law rather than authoring new source law;",
        "probes fail-close hidden drift instead of softening legality expectations;",
        "runtime state binds live truth only after prior legality phases remain satisfied;",
        "receipts close the adjudicated verdict and do not replace the earlier legality phases they report.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime adjudication-surface consumption boundary",
        "Runtime consumes mappings as admissible law-resolution surfaces rather than as optional lookup hints.",
        "Runtime consumes validators as legality-evaluation surfaces rather than as replaceable commentary.",
        "Runtime consumes probes as fail-close drift-negation surfaces rather than soft diagnostics.",
        "Runtime consumes runtime state as live-truth binding only after prior legality phases remain satisfied.",
        "Runtime consumes receipts as adjudicated verdict closure rather than as upstream law-authoring surfaces.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))



def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus source-order and reading-order governance.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    question_routing_doc, question_routing_entry_path, question_routing_active_path, question_routing_alias_error = (
        load_root_corpus_question_routing(repo_root)
    )
    precedence_doc, precedence_entry_path, precedence_active_path, precedence_alias_error = load_root_corpus_precedence(
        repo_root
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    coverage_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY
    if question_routing_alias_error:
        stale_reasons.append(f"root_corpus_question_routing_alias_error:{question_routing_alias_error}")
        error_code = ERR_REGISTRY
    elif not question_routing_doc:
        stale_reasons.append("root_corpus_question_routing_empty_or_invalid")
        error_code = ERR_REGISTRY
    if precedence_alias_error:
        stale_reasons.append(f"root_corpus_precedence_alias_error:{precedence_alias_error}")
        error_code = ERR_REGISTRY
    elif not precedence_doc:
        stale_reasons.append("root_corpus_precedence_empty_or_invalid")
        error_code = ERR_REGISTRY

    source_rows = source_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    adjudication_rows = adjudication_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    adjudication_surface_profiles = adjudication_surface_profiles_from_doc(ordering_doc) if ordering_doc else ()
    ordering_anchor_checks = ordering_anchor_checks_from_doc(ordering_doc) if ordering_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})
    precedence_profiles = precedence_profiles_from_doc(precedence_doc) if precedence_doc else ()

    if not stale_reasons:
        if str(ordering_doc.get("ordering_family") or "").strip() != "protocol_root_corpus_ordering":
            stale_reasons.append("root_corpus_ordering_family_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("ordering_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_ordering_version_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_ordering_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_ordering_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("question_routing_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-question-routing.current.yaml":
            stale_reasons.append("root_corpus_ordering_question_routing_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("precedence_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-precedence.current.yaml":
            stale_reasons.append("root_corpus_ordering_precedence_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_ordering.py":
            stale_reasons.append("root_corpus_ordering_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh":
            stale_reasons.append("root_corpus_ordering_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("common_script") or "").strip() != "scripts/root_corpus_ordering_common.py":
            stale_reasons.append("root_corpus_ordering_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(ordering_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_ordering_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not str(ordering_doc.get("root_index_entry") or "").strip():
            stale_reasons.append("root_corpus_ordering_root_index_entry_missing")
            error_code = ERR_REGISTRY
        if not source_rows:
            stale_reasons.append("root_corpus_ordering_source_order_missing")
            error_code = ERR_REGISTRY
        if not reading_rows:
            stale_reasons.append("root_corpus_ordering_reading_order_missing")
            error_code = ERR_REGISTRY
        if not adjudication_rows:
            stale_reasons.append("root_corpus_ordering_adjudication_order_missing")
            error_code = ERR_REGISTRY
        if not adjudication_surface_profiles:
            stale_reasons.append("root_corpus_ordering_adjudication_surface_profiles_missing")
            error_code = ERR_REGISTRY
        if not ordering_anchor_checks:
            stale_reasons.append("root_corpus_ordering_anchor_checks_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                ordering_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_ordering",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    expected_source_classes = sorted({entry.corpus_class for entry in registry_entries if entry.corpus_class != "root_index"})
    registry_class_law_bearing = {
        cls: any(entry.corpus_class == cls and entry.law_bearing for entry in registry_entries) for cls in registry_classes
    }

    source_orders = [row.order for row in source_rows]
    source_classes = [row.corpus_class for row in source_rows]
    reading_orders = [row.order for row in reading_rows]
    reading_paths = [row.rel_path for row in reading_rows]
    adjudication_orders = [row.order for row in adjudication_rows]
    adjudication_surfaces = [row.machine_surface for row in adjudication_rows]
    adjudication_surface_profile_map = {row.machine_surface: row for row in adjudication_surface_profiles}
    adjudication_phase_orders = [row.phase_order for row in adjudication_surface_profiles]
    sorted_source_rows = sorted(source_rows, key=lambda item: item.order)
    sorted_reading_rows = sorted(reading_rows, key=lambda item: item.order)
    sorted_adjudication_rows = sorted(adjudication_rows, key=lambda item: item.order)
    sorted_adjudication_surface_profiles = sorted(adjudication_surface_profiles, key=lambda item: item.phase_order)
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip()
    precedence_profile_map = {row.conflict_class: row for row in precedence_profiles}
    precedence_legality_profile = precedence_profile_map.get(CURRENT_TURN_LEGALITY_CONFLICT)

    if not stale_reasons:
        if len(set(source_orders)) != len(source_orders) or not contiguous_orders(sorted(source_orders)):
            structure_violations.append({"field": "source_order", "reason": "source_order_non_contiguous"})
        if "root_index" in source_classes:
            structure_violations.append({"field": "source_order", "reason": "root_index_must_not_be_generative_source"})
        if len(set(reading_orders)) != len(reading_orders) or not contiguous_orders(sorted(reading_orders)):
            structure_violations.append({"field": "reading_order", "reason": "reading_order_non_contiguous"})
        if len(set(adjudication_orders)) != len(adjudication_orders) or not contiguous_orders(sorted(adjudication_orders)):
            structure_violations.append({"field": "adjudication_order", "reason": "adjudication_order_non_contiguous"})
        if len(set(adjudication_surfaces)) != len(adjudication_surfaces):
            structure_violations.append({"field": "adjudication_order", "reason": "adjudication_order_duplicate_machine_surface"})
        if len(set(adjudication_phase_orders)) != len(adjudication_phase_orders) or not contiguous_orders(sorted(adjudication_phase_orders)):
            structure_violations.append({"field": "adjudication_surface_profiles", "reason": "phase_order_non_contiguous"})
        if (
            not sorted_reading_rows
            or sorted_reading_rows[0].rel_path != root_index_entry
            or sorted_reading_rows[0].entry_role != ROOT_INDEX_ENTRY_ROLE
        ):
            structure_violations.append(
                {
                    "field": "reading_order",
                    "reason": "root_index_entry_not_first",
                    "expected_rel_path": root_index_entry,
                    "expected_entry_role": ROOT_INDEX_ENTRY_ROLE,
                }
            )
        if root_index_entry and registry_entry_class_map.get(root_index_entry) != "root_index":
            structure_violations.append(
                {
                    "field": "root_index_entry",
                    "reason": "root_index_entry_not_registered_as_root_index",
                    "rel_path": root_index_entry,
                }
            )

        append_membership_delta_violations(
            coverage_violations,
            field_name="source_order",
            expected_ids=expected_source_classes,
            actual_ids=source_classes,
            payload_key="corpus_classes",
            missing_reason="missing_source_classes",
            extra_reason="extra_source_classes",
            duplicate_reason="source_order_duplicate_corpus_class",
            actual_total_count=len(source_classes),
        )
        for row in sorted_source_rows:
            expected_law_bearing = registry_class_law_bearing.get(row.corpus_class)
            if expected_law_bearing is None:
                continue
            if bool(row.law_bearing_required) != bool(expected_law_bearing):
                coverage_violations.append(
                    {
                        "field": "source_order",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected_law_bearing),
                        "actual": bool(row.law_bearing_required),
                    }
                )

        append_membership_delta_violations(
            coverage_violations,
            field_name="reading_order",
            expected_ids=registry_paths,
            actual_ids=reading_paths,
            payload_key="rel_paths",
            missing_reason="missing_registered_entries",
            extra_reason="extra_unregistered_entries",
            duplicate_reason="reading_order_duplicate_rel_path",
            actual_total_count=len(reading_paths),
        )

        redirect_surfaces = tuple(adjudication_redirect.terminal_machine_surfaces)
        ordering_adjudication_surfaces = tuple(row.machine_surface for row in sorted_adjudication_rows)
        if ordering_adjudication_surfaces != redirect_surfaces:
            coverage_violations.append(
                {
                    "field": "adjudication_order",
                    "reason": "terminal_machine_surfaces_mismatch",
                    "expected": list(redirect_surfaces),
                    "actual": list(ordering_adjudication_surfaces),
                }
            )
        precedence_terminal_surfaces = tuple(precedence_legality_profile.terminal_machine_surfaces) if precedence_legality_profile else ()
        if not precedence_legality_profile:
            coverage_violations.append(
                {
                    "field": "adjudication_order",
                    "reason": "current_turn_legality_profile_missing",
                    "conflict_class": CURRENT_TURN_LEGALITY_CONFLICT,
                }
            )
        elif ordering_adjudication_surfaces != precedence_terminal_surfaces:
            coverage_violations.append(
                {
                    "field": "adjudication_order",
                    "reason": "precedence_terminal_machine_surfaces_mismatch",
                    "expected": list(precedence_terminal_surfaces),
                    "actual": list(ordering_adjudication_surfaces),
                }
            )
        expected_adjudication_surfaces = tuple(EXPECTED_ADJUDICATION_SURFACE_PROFILES)
        if ordering_adjudication_surfaces != expected_adjudication_surfaces:
            coverage_violations.append(
                {
                    "field": "adjudication_surface_profiles",
                    "reason": "adjudication_surface_set_mismatch",
                    "expected": list(expected_adjudication_surfaces),
                    "actual": list(ordering_adjudication_surfaces),
                }
            )
        append_membership_delta_violations(
            coverage_violations,
            field_name="adjudication_surface_profiles",
            expected_ids=expected_adjudication_surfaces,
            actual_ids=adjudication_surface_profile_map,
            payload_key="machine_surfaces",
            missing_reason="missing_machine_surfaces",
            extra_reason="extra_machine_surfaces",
            duplicate_reason="duplicate_machine_surface",
            actual_total_count=len(adjudication_surface_profiles),
        )
        for row in sorted_adjudication_surface_profiles:
            expected = EXPECTED_ADJUDICATION_SURFACE_PROFILES.get(row.machine_surface)
            if expected is None:
                continue
            if row.phase_order != expected["phase_order"]:
                coverage_violations.append(
                    {
                        "field": "adjudication_surface_profiles",
                        "reason": "phase_order_mismatch",
                        "machine_surface": row.machine_surface,
                        "expected": expected["phase_order"],
                        "actual": row.phase_order,
                    }
                )
            if row.surface_role != expected["surface_role"]:
                coverage_violations.append(
                    {
                        "field": "adjudication_surface_profiles",
                        "reason": "surface_role_mismatch",
                        "machine_surface": row.machine_surface,
                        "expected": expected["surface_role"],
                        "actual": row.surface_role,
                    }
                )
            if bool(row.closure_terminal) != bool(expected["closure_terminal"]):
                coverage_violations.append(
                    {
                        "field": "adjudication_surface_profiles",
                        "reason": "closure_terminal_mismatch",
                        "machine_surface": row.machine_surface,
                        "expected": bool(expected["closure_terminal"]),
                        "actual": bool(row.closure_terminal),
                    }
                )
            order_row = next((item for item in sorted_adjudication_rows if item.machine_surface == row.machine_surface), None)
            if order_row is None:
                coverage_violations.append(
                    {
                        "field": "adjudication_surface_profiles",
                        "reason": "machine_surface_missing_from_adjudication_order",
                        "machine_surface": row.machine_surface,
                    }
                )
            elif order_row.order != row.phase_order:
                coverage_violations.append(
                    {
                        "field": "adjudication_surface_profiles",
                        "reason": "phase_order_vs_adjudication_order_mismatch",
                        "machine_surface": row.machine_surface,
                        "expected": row.phase_order,
                        "actual": order_row.order,
                    }
                )
        closure_terminal_surfaces = [row.machine_surface for row in sorted_adjudication_surface_profiles if row.closure_terminal]
        if closure_terminal_surfaces != ["receipts"]:
            coverage_violations.append(
                {
                    "field": "adjudication_surface_profiles",
                    "reason": "closure_terminal_surface_set_mismatch",
                    "expected": ["receipts"],
                    "actual": closure_terminal_surfaces,
                }
            )

        source_rank_by_class = {row.corpus_class: row.order for row in sorted_source_rows}
        previous_rank = 0
        for row in sorted_reading_rows[1:]:
            corpus_class = registry_entry_class_map.get(row.rel_path, "")
            if not corpus_class:
                continue
            current_rank = source_rank_by_class.get(corpus_class)
            if current_rank is None:
                coverage_violations.append(
                    {
                        "field": "reading_order",
                        "reason": "reading_entry_class_not_in_source_order",
                        "rel_path": row.rel_path,
                        "corpus_class": corpus_class,
                    }
                )
                continue
            if current_rank < previous_rank:
                coverage_violations.append(
                    {
                        "field": "reading_order",
                        "reason": "reading_order_inverts_source_order",
                        "rel_path": row.rel_path,
                        "corpus_class": corpus_class,
                        "source_rank": current_rank,
                        "previous_source_rank": previous_rank,
                    }
                )
            previous_rank = current_rank

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                ordering_anchor_checks,
                field_name="ordering_anchor_checks",
                missing_target_reason="anchor_missing",
                missing_marker_reason="missing_required_markers",
                aggregate_missing_markers=True,
                require_file=False,
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (coverage_violations or anchor_violations):
        error_code = ERR_COVERAGE

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"coverage_violation:{row['field']}:{row['reason']}" for row in coverage_violations)
    stale_reasons.extend(f"coverage_violation:{row['field']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    expected_adjudication_surfaces = tuple(EXPECTED_ADJUDICATION_SURFACE_PROFILES)
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "source_order",
                "member_id_key": "corpus_class",
                "actual_rows": source_rows,
                "expected_rows": {corpus_class: {} for corpus_class in expected_source_classes},
                "id_attr": "corpus_class",
            },
            {
                "family_id": "reading_order",
                "member_id_key": "rel_path",
                "actual_rows": reading_rows,
                "expected_rows": {rel_path: {} for rel_path in registry_paths},
                "id_attr": "rel_path",
            },
            {
                "family_id": "adjudication_order",
                "member_id_key": "machine_surface",
                "actual_rows": adjudication_rows,
                "expected_rows": {surface: {} for surface in expected_adjudication_surfaces},
                "id_attr": "machine_surface",
            },
            {
                "family_id": "adjudication_surface_profiles",
                "member_id_key": "machine_surface",
                "actual_rows": adjudication_surface_profiles,
                "expected_rows": {surface: {} for surface in expected_adjudication_surfaces},
                "id_attr": "machine_surface",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_COVERAGE),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "question_routing_entry_path": str(question_routing_entry_path),
        "question_routing_active_path": str(question_routing_active_path),
        "precedence_entry_path": str(precedence_entry_path),
        "precedence_active_path": str(precedence_active_path),
        "root_dir": str(ordering_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "registry_class_ids": registry_classes,
        "expected_source_classes": expected_source_classes,
        **project_root_contract_support_projection(
            prefix="ordering",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=ordering_anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "source_order": [
            {
                "order": row.order,
                "corpus_class": row.corpus_class,
                "source_role": row.source_role,
                "law_bearing_required": row.law_bearing_required,
            }
            for row in sorted_source_rows
        ],
        "reading_order": [
            {
                "order": row.order,
                "rel_path": row.rel_path,
                "entry_role": row.entry_role,
                "corpus_class": registry_entry_class_map.get(row.rel_path, ""),
            }
            for row in sorted_reading_rows
        ],
        "adjudication_order": [
            {
                "order": row.order,
                "machine_surface": row.machine_surface,
            }
            for row in sorted_adjudication_rows
        ],
        "adjudication_surface_profiles": [
            {
                "machine_surface": row.machine_surface,
                "phase_order": row.phase_order,
                "surface_role": row.surface_role,
                "closure_terminal": row.closure_terminal,
            }
            for row in sorted_adjudication_surface_profiles
        ],
        "expected_adjudication_order": list(adjudication_redirect.terminal_machine_surfaces),
        "precedence_adjudication_order": list(precedence_legality_profile.terminal_machine_surfaces) if precedence_legality_profile else [],
        "source_order_class_count": len(source_rows),
        "reading_order_entry_count": len(reading_rows),
        "adjudication_order_surface_count": len(adjudication_rows),
        "adjudication_surface_profile_count": len(adjudication_surface_profiles),
        "registered_entry_count": len(registry_entries),
        "structure_violations": structure_violations,
        "coverage_violations": coverage_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
