#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family
from root_corpus_authority_common import authority_class_profiles_from_doc, load_root_corpus_authority
from root_corpus_gateway_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    gateway_anchor_checks_from_doc,
    gateway_effect_targets_from_doc,
    gateway_order_rows_from_doc,
    gateway_profiles_from_doc,
    load_root_corpus_gateway_admissibility,
)
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, source_order_rows_from_doc
from root_corpus_question_routing_common import adjudication_redirect_from_doc, load_root_corpus_question_routing
from root_corpus_question_routing_common import question_class_profiles_from_doc
from root_corpus_transition_common import load_root_corpus_transition, transition_surface_profiles_from_doc

STATUS_KEY = "protocol_root_corpus_gateway_admissibility_status"
ERR_REGISTRY = "IP-RGA-001"
ERR_STRUCTURE = "IP-RGA-002"
ERR_ADMISSIBILITY = "IP-RGA-003"

EXPECTED_GATEWAY_METADATA = {
    "constitution": {
        "gateway_scope": "root",
        "admissibility_mode": "governed_refreeze_gateway",
        "gateway_effect_scope": "constitutional_law_refreeze",
        "current_turn_legality_terminal": False,
        "expected_effect_target_class": "constitution",
        "expected_effect_target_transition_mode": "constitutional_freeze",
        "expected_authority_mode": "frozen_law_only",
        "expected_effect_target_question_class": "frozen_protocol_law",
        "expected_effect_target_answer_mode": "frozen_law_answer",
    },
    "runtime_constitution": {
        "gateway_scope": "root",
        "admissibility_mode": "governed_refreeze_gateway",
        "gateway_effect_scope": "runtime_constitutional_law_refreeze",
        "current_turn_legality_terminal": False,
        "expected_effect_target_class": "runtime_constitution",
        "expected_effect_target_transition_mode": "runtime_constitutional_freeze",
        "expected_authority_mode": "frozen_law_only",
        "expected_effect_target_question_class": "frozen_runtime_law",
        "expected_effect_target_answer_mode": "frozen_law_answer",
    },
    "root_contract": {
        "gateway_scope": "root",
        "admissibility_mode": "governed_refreeze_gateway",
        "gateway_effect_scope": "root_contract_law_refreeze",
        "current_turn_legality_terminal": False,
        "expected_effect_target_class": "root_contract",
        "expected_effect_target_transition_mode": "domain_contract_freeze",
        "expected_authority_mode": "frozen_law_only",
        "expected_effect_target_question_class": "frozen_domain_contract_law",
        "expected_effect_target_answer_mode": "frozen_law_answer",
    },
    "machine_registry_directory": {
        "gateway_scope": "root",
        "admissibility_mode": "governed_projection_gateway",
        "gateway_effect_scope": "machine_registry_projection",
        "current_turn_legality_terminal": True,
        "expected_effect_target_class": "machine_registry_directory",
        "expected_effect_target_transition_mode": "machine_registry_projection",
        "expected_authority_mode": "machine_consumed_family",
        "expected_effect_target_question_class": "registry_resolution",
        "expected_effect_target_answer_mode": "machine_registry_answer",
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Root gateway-admissibility discipline",
        "gateway admission decides which non-origin surfaces may legally motivate each root gateway;",
        "admission only permits governed re-entry at that gateway's own effect scope and effect target class;",
        "gateway effect target stays fixed by gateway class itself; incoming motivation may not choose a different root output class;",
        "gateway effect target also keeps the question class governed for that target layer; incoming motivation may not retag gateway output as a different answer class;",
        "gateway admission does not let an incoming surface inherit the gateway's authorship.",
        "The governed re-entry chain stays explicit as: constitution -> runtime constitution -> root contract -> machine-registry.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Gateway admission must preserve source order",
        "a gateway is a legal re-entry port, not an origin substitute;",
        "entering a gateway does not let an incoming surface inherit bottom-theory or constitutional authorship;",
        "gateway effect target stays fixed by gateway kind; entering one gateway does not let incoming motivation choose a different downstream root class;",
        "gateway output must also retain the question class governed for that target layer, rather than inheriting a new answer class from incoming motivation;",
        "The governed re-entry chain must stay explicit as: constitution -> runtime constitution -> root contract -> machine-registry.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root gateway-admissibility boundary",
        "Gateway admission is narrower than general motivation to strengthen.",
        "Gateway effect target is fixed by gateway class itself; gateway admission cannot directly emit a different root target class than the one governed for that gateway.",
        "Gateway effect target also retains the question class governed for that target layer rather than inheriting a new answer class from incoming motivation.",
        "Machine-registry gateway may terminate current-turn legality, but that does not let incoming motivation surfaces author upstream law.",
        "- governed re-entry chain: constitution -> runtime constitution -> root contract -> machine-registry",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime-origin gateway-admissibility boundary",
        "Runtime-origin material may motivate only the gateways whose admissibility contract explicitly allows it;",
        "Runtime-origin admission cannot choose a different gateway effect target than the class governed for that gateway.",
        "Runtime-origin admission also cannot retag gateway output into a different question class than the one governed for that target layer.",
        "Runtime motivation entering a gateway still requires governed refreezing or governed projection before it becomes shared law.",
        "Runtime-origin gateway progression still follows the explicit re-entry chain: constitution -> runtime constitution -> root contract -> machine-registry.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _build_expected_gateway_inputs(transition_profiles: tuple[Any, ...]) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    expected: dict[str, list[str]] = {gateway: [] for gateway in EXPECTED_GATEWAY_METADATA}
    unknown_gateways: list[str] = []
    for profile in transition_profiles:
        for gateway in getattr(profile, "strengthening_gateways", ()):
            if gateway not in expected:
                unknown_gateways.append(gateway)
                continue
            surface_class = str(getattr(profile, "surface_class", "") or "").strip()
            if surface_class and surface_class not in expected[gateway]:
                expected[gateway].append(surface_class)
    normalized = {gateway: tuple(sorted(values)) for gateway, values in expected.items()}
    return normalized, sorted(set(unknown_gateways))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus gateway admissibility law.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = (
        load_root_corpus_gateway_admissibility(repo_root)
    )
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    transition_doc, transition_entry_path, transition_active_path, transition_alias_error = load_root_corpus_transition(
        repo_root
    )
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(
        repo_root
    )
    question_routing_doc, question_routing_entry_path, question_routing_active_path, question_routing_alias_error = (
        load_root_corpus_question_routing(repo_root)
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    admissibility_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if admissibility_alias_error:
        stale_reasons.append(f"root_corpus_gateway_admissibility_alias_error:{admissibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not admissibility_doc:
        stale_reasons.append("root_corpus_gateway_admissibility_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    if transition_alias_error:
        stale_reasons.append(f"root_corpus_transition_alias_error:{transition_alias_error}")
        error_code = ERR_REGISTRY
    elif not transition_doc:
        stale_reasons.append("root_corpus_transition_empty_or_invalid")
        error_code = ERR_REGISTRY

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
        error_code = ERR_REGISTRY

    if question_routing_alias_error:
        stale_reasons.append(f"root_corpus_question_routing_alias_error:{question_routing_alias_error}")
        error_code = ERR_REGISTRY
    elif not question_routing_doc:
        stale_reasons.append("root_corpus_question_routing_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = gateway_anchor_checks_from_doc(admissibility_doc) if admissibility_doc else ()
    gateway_order_rows = gateway_order_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    gateway_effect_targets = gateway_effect_targets_from_doc(admissibility_doc) if admissibility_doc else ()
    gateway_profiles = gateway_profiles_from_doc(admissibility_doc) if admissibility_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    source_rows = source_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    transition_profiles = transition_surface_profiles_from_doc(transition_doc) if transition_doc else ()
    authority_profiles = authority_class_profiles_from_doc(authority_doc) if authority_doc else ()
    question_profiles = question_class_profiles_from_doc(question_routing_doc) if question_routing_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})

    if not stale_reasons:
        if str(admissibility_doc.get("admissibility_family") or "").strip() != "protocol_root_corpus_gateway_admissibility":
            stale_reasons.append("root_corpus_gateway_admissibility_family_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("admissibility_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_gateway_admissibility_version_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_gateway_admissibility_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_gateway_admissibility_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_gateway_admissibility_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("transition_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-transition.current.yaml":
            stale_reasons.append("root_corpus_gateway_admissibility_transition_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("authority_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-authority.current.yaml":
            stale_reasons.append("root_corpus_gateway_admissibility_authority_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("question_routing_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-question-routing.current.yaml":
            stale_reasons.append("root_corpus_gateway_admissibility_question_routing_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_gateway_admissibility.py":
            stale_reasons.append("root_corpus_gateway_admissibility_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh":
            stale_reasons.append("root_corpus_gateway_admissibility_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(admissibility_doc.get("common_script") or "").strip() != "scripts/root_corpus_gateway_admissibility_common.py":
            stale_reasons.append("root_corpus_gateway_admissibility_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(admissibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_gateway_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_gateway_admissibility_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not gateway_order_rows:
            stale_reasons.append("root_corpus_gateway_admissibility_gateway_order_missing")
            error_code = ERR_REGISTRY
        if not gateway_effect_targets:
            stale_reasons.append("root_corpus_gateway_admissibility_gateway_effect_targets_missing")
            error_code = ERR_REGISTRY
        if not gateway_profiles:
            stale_reasons.append("root_corpus_gateway_admissibility_profiles_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_gateway_admissibility",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = {entry.rel_path for entry in registry_entries}
    authority_profile_map = {row.corpus_class: row for row in authority_profiles}
    question_profile_map = {row.question_class: row for row in question_profiles}
    gateway_profile_map = {row.gateway_class: row for row in gateway_profiles}
    gateway_effect_target_map = {row.gateway_class: row for row in gateway_effect_targets}
    expected_gateway_inputs, unknown_transition_gateways = _build_expected_gateway_inputs(transition_profiles)
    transition_profile_map = {row.surface_class: row for row in transition_profiles}
    transition_current_turn_allowed = sorted(
        row.surface_class for row in transition_profiles if getattr(row, "direct_current_turn_legality_allowed", False)
    )
    sorted_source_rows = sorted(source_rows, key=lambda item: item.order)
    expected_gateway_order = tuple(
        row.corpus_class for row in sorted_source_rows if row.corpus_class in EXPECTED_GATEWAY_METADATA
    )
    gateway_order_map = {row.gateway_class: row for row in gateway_order_rows}
    gateway_order_values = [row.order for row in gateway_order_rows]
    sorted_gateway_order_rows = sorted(gateway_order_rows, key=lambda item: item.order)
    actual_gateway_order = tuple(row.gateway_class for row in sorted_gateway_order_rows)

    if not stale_reasons:
        if len(gateway_profile_map) != len(gateway_profiles):
            structure_violations.append({"field": "gateway_profiles", "reason": "duplicate_gateway_class"})
        if len(gateway_order_map) != len(gateway_order_rows):
            structure_violations.append({"field": "gateway_order", "reason": "duplicate_gateway_class"})
        if len(gateway_effect_target_map) != len(gateway_effect_targets):
            structure_violations.append({"field": "gateway_effect_targets", "reason": "duplicate_gateway_class"})
        if len(set(gateway_order_values)) != len(gateway_order_values) or not _contiguous_orders(sorted(gateway_order_values)):
            structure_violations.append({"field": "gateway_order", "reason": "gateway_order_non_contiguous"})
        anchor_rel_paths = [row.rel_path for row in anchor_checks]
        if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
            structure_violations.append({"field": "gateway_anchor_checks", "reason": "duplicate_rel_path"})
        missing_anchors = sorted(set(anchor_rel_paths) - registry_paths)
        if missing_anchors:
            structure_violations.append(
                {"field": "gateway_anchor_checks", "reason": "unregistered_anchor_entries", "rel_paths": missing_anchors}
            )
        expected_gateway_classes = sorted(EXPECTED_GATEWAY_METADATA)
        missing_gateway_classes = sorted(set(expected_gateway_classes) - set(gateway_profile_map))
        extra_gateway_classes = sorted(set(gateway_profile_map) - set(expected_gateway_classes))
        if missing_gateway_classes:
            structure_violations.append(
                {"field": "gateway_profiles", "reason": "missing_gateway_classes", "gateway_classes": missing_gateway_classes}
            )
        if extra_gateway_classes:
            structure_violations.append(
                {"field": "gateway_profiles", "reason": "extra_gateway_classes", "gateway_classes": extra_gateway_classes}
            )
        missing_gateway_order_classes = sorted(set(expected_gateway_classes) - set(gateway_order_map))
        extra_gateway_order_classes = sorted(set(gateway_order_map) - set(expected_gateway_classes))
        missing_gateway_effect_target_classes = sorted(set(expected_gateway_classes) - set(gateway_effect_target_map))
        extra_gateway_effect_target_classes = sorted(set(gateway_effect_target_map) - set(expected_gateway_classes))
        if missing_gateway_order_classes:
            structure_violations.append(
                {"field": "gateway_order", "reason": "missing_gateway_classes", "gateway_classes": missing_gateway_order_classes}
            )
        if extra_gateway_order_classes:
            structure_violations.append(
                {"field": "gateway_order", "reason": "extra_gateway_classes", "gateway_classes": extra_gateway_order_classes}
            )
        if missing_gateway_effect_target_classes:
            structure_violations.append(
                {
                    "field": "gateway_effect_targets",
                    "reason": "missing_gateway_classes",
                    "gateway_classes": missing_gateway_effect_target_classes,
                }
            )
        if extra_gateway_effect_target_classes:
            structure_violations.append(
                {
                    "field": "gateway_effect_targets",
                    "reason": "extra_gateway_classes",
                    "gateway_classes": extra_gateway_effect_target_classes,
                }
            )
        if unknown_transition_gateways:
            structure_violations.append(
                {
                    "field": "transition_surface_profiles",
                    "reason": "unknown_transition_strengthening_gateways",
                    "gateways": unknown_transition_gateways,
                }
            )

        for row in gateway_profiles:
            expected = EXPECTED_GATEWAY_METADATA.get(row.gateway_class)
            if expected is None:
                continue
            effect_target = gateway_effect_target_map.get(row.gateway_class)
            if row.gateway_scope != expected["gateway_scope"]:
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "gateway_scope_mismatch",
                        "gateway_class": row.gateway_class,
                        "expected": expected["gateway_scope"],
                        "actual": row.gateway_scope,
                    }
                )
            if row.admissibility_mode != expected["admissibility_mode"]:
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "admissibility_mode_mismatch",
                        "gateway_class": row.gateway_class,
                        "expected": expected["admissibility_mode"],
                        "actual": row.admissibility_mode,
                    }
                )
            if row.gateway_effect_scope != expected["gateway_effect_scope"]:
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "gateway_effect_scope_mismatch",
                        "gateway_class": row.gateway_class,
                        "expected": expected["gateway_effect_scope"],
                        "actual": row.gateway_effect_scope,
                    }
                )
            if bool(row.current_turn_legality_terminal) != bool(expected["current_turn_legality_terminal"]):
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "current_turn_legality_terminal_mismatch",
                        "gateway_class": row.gateway_class,
                        "expected": bool(expected["current_turn_legality_terminal"]),
                    "actual": bool(row.current_turn_legality_terminal),
                    }
                )
            if row.gateway_class not in actual_gateway_order:
                admissibility_violations.append(
                    {
                        "field": "gateway_order",
                        "reason": "gateway_profile_missing_from_gateway_order",
                        "gateway_class": row.gateway_class,
                    }
                )
            expected_inputs = expected_gateway_inputs.get(row.gateway_class, ())
            actual_inputs = tuple(sorted(row.admissible_nonorigin_surface_classes))
            if actual_inputs != expected_inputs:
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "admissible_nonorigin_surface_classes_mismatch",
                        "gateway_class": row.gateway_class,
                        "expected": list(expected_inputs),
                        "actual": list(actual_inputs),
                    }
                )
            if len(set(row.admissible_nonorigin_surface_classes)) != len(row.admissible_nonorigin_surface_classes):
                admissibility_violations.append(
                    {
                        "field": "gateway_profiles",
                        "reason": "duplicate_admissible_nonorigin_surface_classes",
                        "gateway_class": row.gateway_class,
                    }
                )
            authority_profile = authority_profile_map.get(row.gateway_class)
            if authority_profile is None:
                admissibility_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "missing_gateway_authority_profile",
                        "gateway_class": row.gateway_class,
                    }
                )
            else:
                if not bool(authority_profile.law_bearing_required):
                    admissibility_violations.append(
                        {
                            "field": "authority_class_profiles",
                            "reason": "gateway_must_be_law_bearing",
                            "gateway_class": row.gateway_class,
                        }
                    )
                if authority_profile.authority_mode != expected["expected_authority_mode"]:
                    admissibility_violations.append(
                        {
                            "field": "authority_class_profiles",
                            "reason": "gateway_authority_mode_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_authority_mode"],
                        "actual": authority_profile.authority_mode,
                    }
                )
            if effect_target is None:
                admissibility_violations.append(
                    {
                        "field": "gateway_effect_targets",
                        "reason": "missing_gateway_effect_target",
                        "gateway_class": row.gateway_class,
                    }
                )
            else:
                if effect_target.effect_target_class != expected["expected_effect_target_class"]:
                    admissibility_violations.append(
                        {
                            "field": "gateway_effect_targets",
                            "reason": "effect_target_class_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_effect_target_class"],
                            "actual": effect_target.effect_target_class,
                        }
                    )
                if effect_target.effect_target_transition_mode != expected["expected_effect_target_transition_mode"]:
                    admissibility_violations.append(
                        {
                            "field": "gateway_effect_targets",
                            "reason": "effect_target_transition_mode_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_effect_target_transition_mode"],
                            "actual": effect_target.effect_target_transition_mode,
                        }
                    )
                if effect_target.effect_target_authority_mode != expected["expected_authority_mode"]:
                    admissibility_violations.append(
                        {
                            "field": "gateway_effect_targets",
                            "reason": "effect_target_authority_mode_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_authority_mode"],
                            "actual": effect_target.effect_target_authority_mode,
                        }
                    )
                if effect_target.effect_target_question_class != expected["expected_effect_target_question_class"]:
                    admissibility_violations.append(
                        {
                            "field": "gateway_effect_targets",
                            "reason": "effect_target_question_class_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_effect_target_question_class"],
                            "actual": effect_target.effect_target_question_class,
                        }
                    )
                if effect_target.effect_target_answer_mode != expected["expected_effect_target_answer_mode"]:
                    admissibility_violations.append(
                        {
                            "field": "gateway_effect_targets",
                            "reason": "effect_target_answer_mode_mismatch",
                            "gateway_class": row.gateway_class,
                            "expected": expected["expected_effect_target_answer_mode"],
                            "actual": effect_target.effect_target_answer_mode,
                        }
                    )
                transition_profile = transition_profile_map.get(effect_target.effect_target_class)
                if transition_profile is None:
                    admissibility_violations.append(
                        {
                            "field": "transition_surface_profiles",
                            "reason": "missing_effect_target_transition_profile",
                            "gateway_class": row.gateway_class,
                            "effect_target_class": effect_target.effect_target_class,
                        }
                    )
                else:
                    if transition_profile.transition_mode != effect_target.effect_target_transition_mode:
                        admissibility_violations.append(
                            {
                                "field": "transition_surface_profiles",
                                "reason": "effect_target_transition_profile_mismatch",
                                "gateway_class": row.gateway_class,
                                "effect_target_class": effect_target.effect_target_class,
                                "expected": effect_target.effect_target_transition_mode,
                                "actual": transition_profile.transition_mode,
                            }
                        )
                    if bool(transition_profile.direct_current_turn_legality_allowed) != bool(row.current_turn_legality_terminal):
                        admissibility_violations.append(
                            {
                                "field": "transition_surface_profiles",
                                "reason": "effect_target_current_turn_legality_alignment_mismatch",
                                "gateway_class": row.gateway_class,
                                "effect_target_class": effect_target.effect_target_class,
                                "expected": bool(row.current_turn_legality_terminal),
                                "actual": bool(transition_profile.direct_current_turn_legality_allowed),
                            }
                        )
                effect_authority_profile = authority_profile_map.get(effect_target.effect_target_class)
                if effect_authority_profile is None:
                    admissibility_violations.append(
                        {
                            "field": "authority_class_profiles",
                            "reason": "missing_effect_target_authority_profile",
                            "gateway_class": row.gateway_class,
                            "effect_target_class": effect_target.effect_target_class,
                        }
                    )
                elif effect_authority_profile.authority_mode != effect_target.effect_target_authority_mode:
                    admissibility_violations.append(
                        {
                            "field": "authority_class_profiles",
                            "reason": "effect_target_authority_profile_mismatch",
                            "gateway_class": row.gateway_class,
                            "effect_target_class": effect_target.effect_target_class,
                            "expected": effect_target.effect_target_authority_mode,
                            "actual": effect_authority_profile.authority_mode,
                        }
                    )
                question_profile = question_profile_map.get(effect_target.effect_target_question_class)
                if question_profile is None:
                    admissibility_violations.append(
                        {
                            "field": "question_class_profiles",
                            "reason": "missing_effect_target_question_profile",
                            "gateway_class": row.gateway_class,
                            "effect_target_question_class": effect_target.effect_target_question_class,
                        }
                    )
                else:
                    if question_profile.answer_mode != effect_target.effect_target_answer_mode:
                        admissibility_violations.append(
                            {
                                "field": "question_class_profiles",
                                "reason": "effect_target_answer_profile_mismatch",
                                "gateway_class": row.gateway_class,
                                "effect_target_question_class": effect_target.effect_target_question_class,
                                "expected": effect_target.effect_target_answer_mode,
                                "actual": question_profile.answer_mode,
                            }
                        )
                    if bool(question_profile.current_turn_authority_allowed) != bool(row.current_turn_legality_terminal):
                        admissibility_violations.append(
                            {
                                "field": "question_class_profiles",
                                "reason": "effect_target_current_turn_authority_alignment_mismatch",
                                "gateway_class": row.gateway_class,
                                "effect_target_question_class": effect_target.effect_target_question_class,
                                "expected": bool(row.current_turn_legality_terminal),
                                "actual": bool(question_profile.current_turn_authority_allowed),
                            }
                        )
                    if question_profile.root_entry_required is not True:
                        admissibility_violations.append(
                            {
                                "field": "question_class_profiles",
                                "reason": "effect_target_question_must_remain_root_entry_required",
                                "gateway_class": row.gateway_class,
                                "effect_target_question_class": effect_target.effect_target_question_class,
                            }
                        )

        if actual_gateway_order != expected_gateway_order:
            admissibility_violations.append(
                {
                    "field": "gateway_order",
                    "reason": "gateway_order_mismatch",
                    "expected": list(expected_gateway_order),
                    "actual": list(actual_gateway_order),
                }
            )

        if transition_current_turn_allowed != ["machine_registry_directory"]:
            admissibility_violations.append(
                {
                    "field": "transition_surface_profiles",
                    "reason": "transition_current_turn_allowed_surface_set_mismatch",
                    "expected": ["machine_registry_directory"],
                    "actual": transition_current_turn_allowed,
                }
            )

        if adjudication_redirect.question_class != "current_turn_legality":
            admissibility_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "adjudication_redirect_question_class_invalid",
                    "expected": "current_turn_legality",
                    "actual": adjudication_redirect.question_class,
                }
            )
        if actual_gateway_order and actual_gateway_order[-1] != "machine_registry_directory":
            admissibility_violations.append(
                {
                    "field": "gateway_order",
                    "reason": "machine_registry_directory_must_terminate_gateway_order",
                    "actual_terminal_gateway": actual_gateway_order[-1],
                }
            )
        current_turn_terminal_gateway = next(
            (row.gateway_class for row in gateway_profiles if row.current_turn_legality_terminal),
            "",
        )
        if actual_gateway_order and current_turn_terminal_gateway and actual_gateway_order[-1] != current_turn_terminal_gateway:
            admissibility_violations.append(
                {
                    "field": "gateway_order",
                    "reason": "current_turn_terminal_gateway_mismatch",
                    "expected_terminal_gateway": current_turn_terminal_gateway,
                    "actual_terminal_gateway": actual_gateway_order[-1],
                }
            )
        if "machine_registry_directory" in adjudication_redirect.forbidden_root_corpus_classes:
            admissibility_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "machine_registry_directory_must_not_be_forbidden_for_current_turn_legality",
                }
            )
        for forbidden_gateway in ("constitution", "runtime_constitution", "root_contract"):
            if forbidden_gateway not in adjudication_redirect.forbidden_root_corpus_classes:
                admissibility_violations.append(
                    {
                        "field": "adjudication_redirect",
                        "reason": "upstream_gateway_must_remain_forbidden_for_current_turn_legality",
                        "gateway_class": forbidden_gateway,
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

    violation_count = len(structure_violations) + len(admissibility_violations) + len(anchor_violations) + len(stale_reasons)
    status = STATUS_PASS_REQUIRED if violation_count == 0 else STATUS_FAIL_REQUIRED
    if status == STATUS_FAIL_REQUIRED and not error_code:
        error_code = ERR_STRUCTURE if structure_violations else ERR_ADMISSIBILITY
    row_family_projection_rows = [
        project_row_family(
            family_id="gateway_order",
            member_id_key="gateway_class",
            actual_rows=gateway_order_rows,
            expected_rows={gateway_class: {} for gateway_class in EXPECTED_GATEWAY_METADATA},
            id_attr="gateway_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="gateway_effect_targets",
            member_id_key="gateway_class",
            actual_rows=gateway_effect_targets,
            expected_rows={gateway_class: {} for gateway_class in EXPECTED_GATEWAY_METADATA},
            id_attr="gateway_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="gateway_profiles",
            member_id_key="gateway_class",
            actual_rows=gateway_profiles,
            expected_rows={gateway_class: {} for gateway_class in EXPECTED_GATEWAY_METADATA},
            id_attr="gateway_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
    ]

    payload = {
        STATUS_KEY: status,
        "error_code": error_code,
        "admissibility_entry_path": str(admissibility_entry_path),
        "admissibility_active_path": str(admissibility_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "transition_entry_path": str(transition_entry_path),
        "transition_active_path": str(transition_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "question_routing_entry_path": str(question_routing_entry_path),
        "question_routing_active_path": str(question_routing_active_path),
        "root_dir": str(admissibility_doc.get("root_dir") or ""),
        "gateway_anchor_check_count": len(anchor_checks),
        "gateway_order_count": len(gateway_order_rows),
        "gateway_effect_target_count": len(gateway_effect_targets),
        "gateway_profile_count": len(gateway_profiles),
        **project_root_contract_support_projection(
            prefix="gateway_admissibility",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "current_turn_terminal_gateway": next(
            (row.gateway_class for row in gateway_profiles if row.current_turn_legality_terminal),
            "",
        ),
        "gateway_order": [
            {
                "order": row.order,
                "gateway_class": row.gateway_class,
            }
            for row in sorted_gateway_order_rows
        ],
        "gateway_effect_targets": [
            {
                "gateway_class": row.gateway_class,
                "effect_target_class": row.effect_target_class,
                "effect_target_transition_mode": row.effect_target_transition_mode,
                "effect_target_authority_mode": row.effect_target_authority_mode,
                "effect_target_question_class": row.effect_target_question_class,
                "effect_target_answer_mode": row.effect_target_answer_mode,
            }
            for row in sorted(gateway_effect_targets, key=lambda item: item.gateway_class)
        ],
        "expected_gateway_order": list(expected_gateway_order),
        "derived_gateway_inputs": {
            gateway: list(surface_classes) for gateway, surface_classes in expected_gateway_inputs.items()
        },
        "gateway_profiles": [
            {
                "gateway_class": row.gateway_class,
                "gateway_scope": row.gateway_scope,
                "admissibility_mode": row.admissibility_mode,
                "gateway_effect_scope": row.gateway_effect_scope,
                "current_turn_legality_terminal": row.current_turn_legality_terminal,
                "admissible_nonorigin_surface_classes": list(row.admissible_nonorigin_surface_classes),
            }
            for row in sorted(gateway_profiles, key=lambda item: item.gateway_class)
        ],
        "structure_violations": structure_violations,
        "admissibility_violations": admissibility_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
