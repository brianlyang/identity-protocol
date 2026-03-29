#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_root_doc_anchor_registry_structure_violations,
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_contract_row_validation_common import validate_contract_row_batches
from root_corpus_derivation_common import derivation_class_profiles_from_doc, load_root_corpus_derivation
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_question_routing_common import adjudication_redirect_from_doc, load_root_corpus_question_routing
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_corpus_transition_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    load_root_corpus_transition,
    transition_anchor_checks_from_doc,
    transition_completeness_rows_from_doc,
    transition_surface_profiles_from_doc,
    readme_transition_completeness_surface,
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
EXPECTED_TRANSITION_COMPLETENESS_ROWS = {
    "explicit_transition_row_families": {
        "order": 1,
        "contract_phrase": "required surface-class-profile, direct-root-target-edge, and strengthening-gateway-edge rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_transition_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_transition_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_transition_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize transition legality while missing or unexpected surface, promotion-edge, or re-entry-gateway identities remain known only internally;",
    },
    "fail_close_preserves_transition_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Root promotion-demotion discipline",
        "outer governance, review, workbook, reference, evidence, runtime, receipt, and implementation surfaces may motivate strengthening, but they do not directly promote themselves into root law;",
        "demoted support material cannot directly climb back into law-bearing root status;",
        "## Root transition completeness discipline",
        "These transition-completeness rules must remain bound to canonical transition-completeness rows rather than drifting into soft summary prose.",
        "1. required surface-class-profile, direct-root-target-edge, and strengthening-gateway-edge rows must remain explicit as separate machine-readable row families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Promotion, demotion, and re-entry must stay governed",
        "demotion removes law-bearing authority; it does not preserve a suspended sovereignty that can silently reclaim root status later;",
        "outer governance, review, workbook, reference, evidence, runtime, receipt, and implementation surfaces may motivate strengthening, but they do not directly author root law by themselves;",
        "### Transition row-family completeness must stay explicit",
        "README root transition completeness discipline must therefore stay congruent with admitted transition-completeness rows rather than becoming a freehand completeness summary.",
        "The machine world must not finalize transition legality while required surface, promotion-edge, or re-entry-gateway identity drift remains known only internally.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root-law promotion and re-entry boundary",
        "Promotion into root law without governed refreezing is non-compliant, even if the motivating surface contains true evidence.",
        "## Root transition completeness boundary",
        "1. Transition law must remain machine-readable as separate surface-class-profile, direct-root-target-edge, and strengthening-gateway-edge row families.",
        "4. Protocol legality must not finalize transition legality while missing or unexpected surface, promotion-edge, or re-entry-gateway identities remain known only inside validator logic.",
        "6. README root transition completeness discipline rendered at protocol root must remain congruent with admitted transition-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime-to-root promotion boundary",
        "Runtime-origin evidence must re-enter shared law only through governed refreezing at constitutional, runtime-constitutional, root-contract, or machine-registry gateways.",
        "## Runtime transition consumption boundary",
        "1. Runtime consumes transition law as separate surface-class-profile, direct-root-target-edge, and strengthening-gateway-edge row families rather than as undifferentiated transition prose.",
        "4. Runtime must not finalize transition legality while missing or unexpected surface, promotion-edge, or re-entry-gateway identities remain known only inside validator machinery.",
        "6. Runtime consumes README root transition completeness discipline as a governed completeness projection bound to admitted transition-completeness rows rather than as a freehand completeness summary.",
    ),
}


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
    transition_completeness_rows = transition_completeness_rows_from_doc(transition_doc) if transition_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    derivation_profiles = derivation_class_profiles_from_doc(derivation_doc) if derivation_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})
    transition_completeness_surface = readme_transition_completeness_surface(repo_root)

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
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_transition",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
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
        if not transition_completeness_rows:
            stale_reasons.append("root_corpus_transition_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not surface_profiles:
            stale_reasons.append("root_corpus_transition_surface_profiles_missing")
            error_code = ERR_REGISTRY

    registry_class_law_bearing = {entry.corpus_class: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    derivation_upstream_map = {row.corpus_class: set(row.allowed_upstream_classes) for row in derivation_profiles}
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
        append_root_doc_anchor_registry_structure_violations(
            structure_violations,
            anchor_checks,
            field_name="transition_anchor_checks",
            registry_paths={entry.rel_path for entry in registry_entries},
        )

        append_membership_delta_violations(
            structure_violations,
            field_name="surface_class_profiles",
            expected_ids=expected_surface_classes,
            actual_ids=surface_profile_map,
            payload_key="surface_classes",
            missing_reason="missing_expected_surface_classes",
            extra_reason="extra_surface_classes",
            duplicate_reason="duplicate_surface_class",
            actual_total_count=len(surface_profiles),
        )
        for reason in transition_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "transition_completeness_surface",
                    "reason": f"transition_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": transition_completeness_rows,
                    "expected_rows": EXPECTED_TRANSITION_COMPLETENESS_ROWS,
                    "field_name": "transition_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                },
                {
                    "actual_rows": transition_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_TRANSITION_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "transition_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_transition_completeness_surface_phrase",
                    "non_contiguous_reason": "transition_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_transition_completeness_surface_rows",
                    "extra_reason": "extra_transition_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "transition_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=transition_violations,
        )
        expected_transition_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_TRANSITION_COMPLETENESS_ROWS.values()
        ]
        actual_transition_completeness_phrases = [
            row.contract_phrase for row in transition_completeness_surface.rows
        ]
        expected_transition_completeness_orders = [
            int(row["order"]) for row in EXPECTED_TRANSITION_COMPLETENESS_ROWS.values()
        ]
        actual_transition_completeness_orders = [
            row.order for row in transition_completeness_surface.rows
        ]
        if actual_transition_completeness_phrases and tuple(actual_transition_completeness_phrases) != tuple(
            expected_transition_completeness_phrases
        ):
            transition_violations.append(
                {
                    "field": "transition_completeness_surface",
                    "reason": "transition_completeness_surface_phrase_order_mismatch",
                    "expected": expected_transition_completeness_phrases,
                    "actual": actual_transition_completeness_phrases,
                }
            )
        if actual_transition_completeness_orders and tuple(actual_transition_completeness_orders) != tuple(
            expected_transition_completeness_orders
        ):
            transition_violations.append(
                {
                    "field": "transition_completeness_surface",
                    "reason": "transition_completeness_surface_order_mismatch",
                    "expected": expected_transition_completeness_orders,
                    "actual": actual_transition_completeness_orders,
                }
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

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name=None,
                missing_target_reason="anchor_target_missing",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (transition_violations or anchor_violations):
        error_code = ERR_TRANSITION

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"transition_violation:{row['field']}:{row['reason']}" for row in transition_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "surface_class_profiles",
                "member_id_key": "surface_class",
                "actual_rows": [SimpleNamespace(surface_class=row.surface_class) for row in sorted_profiles],
                "expected_rows": {surface_class: {} for surface_class in expected_surface_classes},
                "id_attr": "surface_class",
            },
            {
                "family_id": "direct_root_target_edges",
                "member_id_key": "edge_id",
                "actual_rows": direct_root_target_edges,
                "expected_rows": expected_direct_root_target_edges,
                "id_attr": "edge_id",
            },
            {
                "family_id": "strengthening_gateway_edges",
                "member_id_key": "edge_id",
                "actual_rows": strengthening_gateway_edges,
                "expected_rows": expected_strengthening_gateway_edges,
                "id_attr": "edge_id",
            },
            {
                "family_id": "transition_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": transition_completeness_rows,
                "expected_rows": {
                    completeness_id: {}
                    for completeness_id in EXPECTED_TRANSITION_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "transition_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": transition_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {}
                    for row in EXPECTED_TRANSITION_COMPLETENESS_ROWS.values()
                },
                "id_attr": "contract_phrase",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    row_family_projection_by_id = {row["family_id"]: row for row in row_family_projection_rows}
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
        "transition_completeness_row_count": len(transition_completeness_rows),
        **project_root_contract_support_projection(
            prefix="transition",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "transition_completeness_row_coverage_status": row_family_projection_by_id["transition_completeness_rows"]["coverage_status"],
        "transition_completeness_row_identity_projection_status": row_family_projection_by_id["transition_completeness_rows"]["identity_projection_status"],
        "transition_completeness_surface_coverage_status": row_family_projection_by_id["transition_completeness_surface"]["coverage_status"],
        "transition_completeness_surface_identity_projection_status": row_family_projection_by_id["transition_completeness_surface"]["identity_projection_status"],
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
        "transition_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(transition_completeness_rows, key=lambda item: item.order)
        ],
        "transition_completeness_surface": {
            "rel_path": transition_completeness_surface.rel_path,
            "entry_count": len(transition_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in transition_completeness_surface.rows
            ],
            "extraction_violations": list(transition_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "transition_violations": transition_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
