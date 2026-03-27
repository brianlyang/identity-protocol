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
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family
from root_corpus_authority_common import load_root_corpus_authority
from root_corpus_gateway_admissibility_common import (
    gateway_effect_targets_from_doc,
    gateway_profiles_from_doc,
    load_root_corpus_gateway_admissibility,
)
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, source_order_rows_from_doc
from root_corpus_precedence_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    gateway_authorship_projections_from_doc,
    load_root_corpus_precedence,
    precedence_anchor_checks_from_doc,
    precedence_profiles_from_doc,
)
from root_corpus_question_routing_common import (
    adjudication_redirect_from_doc,
    gateway_question_projections_from_doc,
    load_root_corpus_question_routing,
)
from root_corpus_transition_common import load_root_corpus_transition, transition_surface_profiles_from_doc

STATUS_KEY = "protocol_root_corpus_precedence_status"
ERR_REGISTRY = "IP-RCP-001"
ERR_STRUCTURE = "IP-RCP-002"
ERR_PRECEDENCE = "IP-RCP-003"

EXPECTED_PROFILES = {
    "semantic_meaning_conflict": {
        "conflict_scope": "source_order_meaning",
        "resolution_mode": "source_order_root_law",
    },
    "current_turn_legality_conflict": {
        "conflict_scope": "current_turn_legality",
        "resolution_mode": "machine_enforcement_terminal",
    },
    "gateway_authorship_conflict": {
        "conflict_scope": "gateway_authorship",
        "resolution_mode": "gateway_effect_scope_preserved",
    },
    "demotion_status_conflict": {
        "conflict_scope": "law_bearing_status",
        "resolution_mode": "governed_reclassification_required",
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Root conflict-precedence discipline",
        "semantic-meaning conflict resolves by source order, not by convenience, recency, or current checker vividness;",
        "current-turn legality conflict resolves at machine-consumed enforcement terminals, not at philosophy prose, README text, or frozen contract prose alone;",
        "gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and source order, not by the identity of the incoming motivating surface;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Conflict precedence must preserve both origin and terminality",
        "semantic-origin conflict resolves by source order;",
        "current-turn legality conflict resolves by machine-consumed terminal enforcement;",
        "gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and source order;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root conflict-precedence boundary",
        "Semantic-meaning conflict resolves by source-order law:",
        "Current-turn legality conflict resolves by machine-consumed enforcement terminals, with machine-registry law as the only terminal root gateway.",
        "Gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and preserved source order, not by incoming motivating surface identity.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime conflict-precedence boundary",
        "Runtime current-turn legality still resolves at machine-consumed enforcement terminals rather than philosophy prose or frozen contract prose alone.",
        "Runtime-origin motivation does not gain gateway authorship, target question class, or answer-mode override merely by being admitted into a governed gateway.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus conflict precedence law.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    precedence_doc, precedence_entry_path, precedence_active_path, precedence_alias_error = load_root_corpus_precedence(
        repo_root
    )
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    question_routing_doc, question_routing_entry_path, question_routing_active_path, question_routing_alias_error = (
        load_root_corpus_question_routing(repo_root)
    )
    transition_doc, transition_entry_path, transition_active_path, transition_alias_error = load_root_corpus_transition(
        repo_root
    )
    gateway_doc, gateway_entry_path, gateway_active_path, gateway_alias_error = load_root_corpus_gateway_admissibility(
        repo_root
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    precedence_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    sources = [
        ("root_corpus_precedence", precedence_alias_error, precedence_doc),
        ("root_corpus_registry", registry_alias_error, registry_doc),
        ("root_corpus_ordering", ordering_alias_error, ordering_doc),
        ("root_corpus_authority", authority_alias_error, authority_doc),
        ("root_corpus_question_routing", question_routing_alias_error, question_routing_doc),
        ("root_corpus_transition", transition_alias_error, transition_doc),
        ("root_corpus_gateway_admissibility", gateway_alias_error, gateway_doc),
    ]
    for prefix, alias_error, doc in sources:
        if alias_error:
            stale_reasons.append(f"{prefix}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(f"{prefix}_empty_or_invalid")
            error_code = ERR_REGISTRY

    anchor_checks = precedence_anchor_checks_from_doc(precedence_doc) if precedence_doc else ()
    gateway_authorship_projections = gateway_authorship_projections_from_doc(precedence_doc) if precedence_doc else ()
    precedence_profiles = precedence_profiles_from_doc(precedence_doc) if precedence_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    source_order_rows = source_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})
    gateway_question_projections = gateway_question_projections_from_doc(question_routing_doc) if question_routing_doc else ()
    transition_profiles = transition_surface_profiles_from_doc(transition_doc) if transition_doc else ()
    gateway_profiles = gateway_profiles_from_doc(gateway_doc) if gateway_doc else ()
    gateway_effect_targets = gateway_effect_targets_from_doc(gateway_doc) if gateway_doc else ()

    if not stale_reasons:
        expected_files = {
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
            "transition_current_file": "identity/protocol/mappings/root-corpus-transition.current.yaml",
            "gateway_admissibility_current_file": "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml",
        }
        if str(precedence_doc.get("precedence_family") or "").strip() != "protocol_root_corpus_precedence":
            stale_reasons.append("root_corpus_precedence_family_invalid")
            error_code = ERR_REGISTRY
        if str(precedence_doc.get("precedence_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_precedence_version_invalid")
            error_code = ERR_REGISTRY
        if str(precedence_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_precedence_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(precedence_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_precedence.py":
            stale_reasons.append("root_corpus_precedence_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(precedence_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh":
            stale_reasons.append("root_corpus_precedence_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(precedence_doc.get("common_script") or "").strip() != "scripts/root_corpus_precedence_common.py":
            stale_reasons.append("root_corpus_precedence_common_script_invalid")
            error_code = ERR_REGISTRY
        for field, expected in expected_files.items():
            if str(precedence_doc.get(field) or "").strip() != expected:
                stale_reasons.append(f"{field}_invalid")
                error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(precedence_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_precedence_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_precedence_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not gateway_authorship_projections:
            stale_reasons.append("root_corpus_precedence_gateway_authorship_projection_missing")
            error_code = ERR_REGISTRY
        if not precedence_profiles:
            stale_reasons.append("root_corpus_precedence_profiles_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_precedence",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = {entry.rel_path for entry in registry_entries}
    profile_map = {row.conflict_class: row for row in precedence_profiles}
    gateway_authorship_projection_map = {row.gateway_class: row for row in gateway_authorship_projections}
    gateway_effect_target_map = {row.gateway_class: row for row in gateway_effect_targets}
    gateway_question_projection_map = {row.gateway_class: row for row in gateway_question_projections}

    all_nonorigin_surface_classes = tuple(
        sorted(
            row.surface_class
            for row in transition_profiles
            if row.surface_class not in {"bottom_theory", "constitution", "runtime_constitution", "root_contract"}
        )
    )
    union_gateway_inputs = sorted(
        {
            surface
            for row in gateway_profiles
            for surface in row.admissible_nonorigin_surface_classes
        }
    )
    source_order_chain = [
        row.corpus_class
        for row in sorted(source_order_rows, key=lambda item: item.order)
        if row.corpus_class in {"bottom_theory", "constitution", "runtime_constitution", "root_contract"}
    ]
    expected_precedence = {
        "semantic_meaning_conflict": {
            "semantic_precedence_chain": tuple(source_order_chain),
            "terminal_machine_surfaces": (),
            "motivating_only_surface_classes": all_nonorigin_surface_classes,
            "forbidden_override_surface_classes": all_nonorigin_surface_classes,
        },
        "current_turn_legality_conflict": {
            "semantic_precedence_chain": ("machine_registry_directory",),
            "terminal_machine_surfaces": tuple(adjudication_redirect.terminal_machine_surfaces),
            "motivating_only_surface_classes": tuple(adjudication_redirect.forbidden_root_corpus_classes),
            "forbidden_override_surface_classes": tuple(adjudication_redirect.forbidden_root_corpus_classes),
        },
        "gateway_authorship_conflict": {
            "semantic_precedence_chain": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
            "terminal_machine_surfaces": (),
            "motivating_only_surface_classes": tuple(union_gateway_inputs),
            "forbidden_override_surface_classes": tuple(union_gateway_inputs),
        },
        "demotion_status_conflict": {
            "semantic_precedence_chain": ("constitution", "runtime_constitution", "root_contract", "machine_registry_directory"),
            "terminal_machine_surfaces": (),
            "motivating_only_surface_classes": ("demoted_support_directory",),
            "forbidden_override_surface_classes": ("demoted_support_directory",),
        },
    }

    if not stale_reasons:
        if len(profile_map) != len(precedence_profiles):
            structure_violations.append({"field": "precedence_profiles", "reason": "duplicate_conflict_class"})
        if len(gateway_authorship_projection_map) != len(gateway_authorship_projections):
            structure_violations.append({"field": "gateway_authorship_projection", "reason": "duplicate_gateway_class"})
        anchor_rel_paths = [row.rel_path for row in anchor_checks]
        if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
            structure_violations.append({"field": "precedence_anchor_checks", "reason": "duplicate_rel_path"})
        missing_anchors = sorted(set(anchor_rel_paths) - registry_paths)
        if missing_anchors:
            structure_violations.append(
                {"field": "precedence_anchor_checks", "reason": "unregistered_anchor_entries", "rel_paths": missing_anchors}
            )
        missing_profiles = sorted(set(EXPECTED_PROFILES) - set(profile_map))
        extra_profiles = sorted(set(profile_map) - set(EXPECTED_PROFILES))
        if missing_profiles:
            structure_violations.append(
                {"field": "precedence_profiles", "reason": "missing_conflict_classes", "conflict_classes": missing_profiles}
            )
        if extra_profiles:
            structure_violations.append(
                {"field": "precedence_profiles", "reason": "extra_conflict_classes", "conflict_classes": extra_profiles}
            )
        missing_gateway_projection_classes = sorted(set(gateway_effect_target_map) - set(gateway_authorship_projection_map))
        extra_gateway_projection_classes = sorted(set(gateway_authorship_projection_map) - set(gateway_effect_target_map))
        if missing_gateway_projection_classes:
            structure_violations.append(
                {
                    "field": "gateway_authorship_projection",
                    "reason": "missing_gateway_classes",
                    "gateway_classes": missing_gateway_projection_classes,
                }
            )
        if extra_gateway_projection_classes:
            structure_violations.append(
                {
                    "field": "gateway_authorship_projection",
                    "reason": "extra_gateway_classes",
                    "gateway_classes": extra_gateway_projection_classes,
                }
            )

        for row in precedence_profiles:
            expected_meta = EXPECTED_PROFILES.get(row.conflict_class)
            expected_profile = expected_precedence.get(row.conflict_class)
            if expected_meta is None or expected_profile is None:
                continue
            if row.conflict_scope != expected_meta["conflict_scope"]:
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "conflict_scope_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": expected_meta["conflict_scope"],
                        "actual": row.conflict_scope,
                    }
                )
            if row.resolution_mode != expected_meta["resolution_mode"]:
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "resolution_mode_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": expected_meta["resolution_mode"],
                        "actual": row.resolution_mode,
                    }
                )
            if tuple(row.semantic_precedence_chain) != tuple(expected_profile["semantic_precedence_chain"]):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "semantic_precedence_chain_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": list(expected_profile["semantic_precedence_chain"]),
                        "actual": list(row.semantic_precedence_chain),
                    }
                )
            if tuple(row.terminal_machine_surfaces) != tuple(expected_profile["terminal_machine_surfaces"]):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "terminal_machine_surfaces_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": list(expected_profile["terminal_machine_surfaces"]),
                        "actual": list(row.terminal_machine_surfaces),
                    }
                )
            if tuple(sorted(row.motivating_only_surface_classes)) != tuple(sorted(expected_profile["motivating_only_surface_classes"])):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "motivating_only_surface_classes_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": list(expected_profile["motivating_only_surface_classes"]),
                        "actual": list(row.motivating_only_surface_classes),
                    }
                )
            if tuple(sorted(row.forbidden_override_surface_classes)) != tuple(sorted(expected_profile["forbidden_override_surface_classes"])):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "forbidden_override_surface_classes_mismatch",
                        "conflict_class": row.conflict_class,
                        "expected": list(expected_profile["forbidden_override_surface_classes"]),
                        "actual": list(row.forbidden_override_surface_classes),
                    }
                )
            if len(set(row.semantic_precedence_chain)) != len(row.semantic_precedence_chain):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "duplicate_semantic_precedence_chain_entries",
                        "conflict_class": row.conflict_class,
                    }
                )
            if len(set(row.terminal_machine_surfaces)) != len(row.terminal_machine_surfaces):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "duplicate_terminal_machine_surfaces",
                        "conflict_class": row.conflict_class,
                    }
                )
            if len(set(row.motivating_only_surface_classes)) != len(row.motivating_only_surface_classes):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "duplicate_motivating_only_surface_classes",
                        "conflict_class": row.conflict_class,
                    }
                )
            if len(set(row.forbidden_override_surface_classes)) != len(row.forbidden_override_surface_classes):
                precedence_violations.append(
                    {
                        "field": "precedence_profiles",
                        "reason": "duplicate_forbidden_override_surface_classes",
                        "conflict_class": row.conflict_class,
                    }
                )

        for gateway_class, row in gateway_authorship_projection_map.items():
            effect_target = gateway_effect_target_map.get(gateway_class)
            question_projection = gateway_question_projection_map.get(gateway_class)
            if effect_target is None:
                precedence_violations.append(
                    {
                        "field": "gateway_authorship_projection",
                        "reason": "missing_gateway_effect_target",
                        "gateway_class": gateway_class,
                    }
                )
                continue
            if question_projection is None:
                precedence_violations.append(
                    {
                        "field": "gateway_authorship_projection",
                        "reason": "missing_gateway_question_projection",
                        "gateway_class": gateway_class,
                    }
                )
                continue
            if row.preserved_effect_target_class != effect_target.effect_target_class:
                precedence_violations.append(
                    {
                        "field": "gateway_authorship_projection",
                        "reason": "preserved_effect_target_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": effect_target.effect_target_class,
                        "actual": row.preserved_effect_target_class,
                    }
                )
            if row.preserved_question_class != question_projection.question_class:
                precedence_violations.append(
                    {
                        "field": "gateway_authorship_projection",
                        "reason": "preserved_question_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": question_projection.question_class,
                        "actual": row.preserved_question_class,
                    }
                )
            if row.preserved_answer_mode != question_projection.answer_mode:
                precedence_violations.append(
                    {
                        "field": "gateway_authorship_projection",
                        "reason": "preserved_answer_mode_mismatch",
                        "gateway_class": gateway_class,
                        "expected": question_projection.answer_mode,
                        "actual": row.preserved_answer_mode,
                    }
                )

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name=None,
                missing_target_reason="anchor_path_missing",
                require_file=False,
            )
        )

    violation_count = len(structure_violations) + len(precedence_violations) + len(anchor_violations) + len(stale_reasons)
    status = STATUS_PASS_REQUIRED if violation_count == 0 else STATUS_FAIL_REQUIRED
    if status == STATUS_FAIL_REQUIRED and not error_code:
        error_code = ERR_STRUCTURE if structure_violations else ERR_PRECEDENCE

    row_family_projection_rows = [
        project_row_family(
            family_id="precedence_profiles",
            member_id_key="conflict_class",
            actual_rows=precedence_profiles,
            expected_rows=EXPECTED_PROFILES,
            id_attr="conflict_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="gateway_authorship_projection",
            member_id_key="gateway_class",
            actual_rows=gateway_authorship_projections,
            expected_rows={gateway_class: {} for gateway_class in gateway_effect_target_map},
            id_attr="gateway_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
    ]

    payload = {
        STATUS_KEY: status,
        "error_code": error_code,
        "precedence_entry_path": str(precedence_entry_path),
        "precedence_active_path": str(precedence_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "question_routing_entry_path": str(question_routing_entry_path),
        "question_routing_active_path": str(question_routing_active_path),
        "transition_entry_path": str(transition_entry_path),
        "transition_active_path": str(transition_active_path),
        "gateway_admissibility_entry_path": str(gateway_entry_path),
        "gateway_admissibility_active_path": str(gateway_active_path),
        "root_dir": str(precedence_doc.get("root_dir") or ""),
        "precedence_anchor_check_count": len(anchor_checks),
        "gateway_authorship_projection_count": len(gateway_authorship_projections),
        "precedence_profile_count": len(precedence_profiles),
        **project_root_contract_support_projection(
            prefix="precedence",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "gateway_authorship_projection": [
            {
                "gateway_class": row.gateway_class,
                "preserved_effect_target_class": row.preserved_effect_target_class,
                "preserved_question_class": row.preserved_question_class,
                "preserved_answer_mode": row.preserved_answer_mode,
            }
            for row in sorted(gateway_authorship_projections, key=lambda item: item.gateway_class)
        ],
        "precedence_profiles": [
            {
                "conflict_class": row.conflict_class,
                "conflict_scope": row.conflict_scope,
                "resolution_mode": row.resolution_mode,
                "semantic_precedence_chain": list(row.semantic_precedence_chain),
                "terminal_machine_surfaces": list(row.terminal_machine_surfaces),
                "motivating_only_surface_classes": list(row.motivating_only_surface_classes),
                "forbidden_override_surface_classes": list(row.forbidden_override_surface_classes),
            }
            for row in sorted(precedence_profiles, key=lambda item: item.conflict_class)
        ],
        "structure_violations": structure_violations,
        "precedence_violations": precedence_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
