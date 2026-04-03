#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_root_doc_anchor_registry_structure_violations,
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_contract_row_validation_common import validate_contract_row_batches
from root_row_family_projection_common import (
    NamedRowFamilyStatusProjectionSpec,
    index_row_family_projection_rows,
    project_named_row_family_statuses,
    project_root_contract_support_projection,
    project_row_families,
)
from root_corpus_authority_common import authority_class_profiles_from_doc, load_root_corpus_authority
from root_corpus_derivation_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    derivation_anchor_checks_from_doc,
    derivation_class_profiles_from_doc,
    derivation_completeness_rows_from_doc,
    load_root_corpus_derivation,
    readme_derivation_completeness_surface,
)
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, source_order_rows_from_doc
from root_corpus_question_routing_common import adjudication_redirect_from_doc, load_root_corpus_question_routing

STATUS_KEY = "protocol_root_corpus_derivation_status"
ERR_REGISTRY = "IP-RCD-001"
ERR_STRUCTURE = "IP-RCD-002"
ERR_DERIVATION = "IP-RCD-003"

EXPECTED_CLASS_RULES = {
    "bottom_theory": {
        "derivation_mode": "generative_origin",
        "allowed_upstream_classes": (),
        "law_bearing_required": True,
        "expected_authority_mode": "interpretive_only",
    },
    "root_index": {
        "derivation_mode": "navigational_projection",
        "allowed_upstream_classes": (
            "bottom_theory",
            "constitution",
            "runtime_constitution",
            "root_contract",
            "machine_registry_directory",
            "governed_subdomain_extension",
            "demoted_support_directory",
        ),
        "law_bearing_required": True,
        "expected_authority_mode": "navigational_only",
    },
    "constitution": {
        "derivation_mode": "constitutional_freeze",
        "allowed_upstream_classes": ("bottom_theory",),
        "law_bearing_required": True,
        "expected_authority_mode": "frozen_law_only",
    },
    "runtime_constitution": {
        "derivation_mode": "runtime_constitutional_freeze",
        "allowed_upstream_classes": ("bottom_theory", "constitution"),
        "law_bearing_required": True,
        "expected_authority_mode": "frozen_law_only",
    },
    "root_contract": {
        "derivation_mode": "domain_contract_freeze",
        "allowed_upstream_classes": ("bottom_theory", "constitution", "runtime_constitution"),
        "law_bearing_required": True,
        "expected_authority_mode": "frozen_law_only",
    },
    "machine_registry_directory": {
        "derivation_mode": "machine_registry_projection",
        "allowed_upstream_classes": ("bottom_theory", "constitution", "runtime_constitution", "root_contract"),
        "law_bearing_required": True,
        "expected_authority_mode": "machine_consumed_family",
    },
    "governed_subdomain_extension": {
        "derivation_mode": "governed_extension_freeze",
        "allowed_upstream_classes": (
            "bottom_theory",
            "constitution",
            "runtime_constitution",
            "root_contract",
            "machine_registry_directory",
        ),
        "law_bearing_required": True,
        "expected_authority_mode": "extension_family",
    },
    "demoted_support_directory": {
        "derivation_mode": "demoted_support_projection",
        "allowed_upstream_classes": (
            "bottom_theory",
            "constitution",
            "runtime_constitution",
            "root_contract",
            "machine_registry_directory",
            "governed_subdomain_extension",
        ),
        "law_bearing_required": False,
        "expected_authority_mode": "demoted_support_only",
    },
}
EXPECTED_CURRENT_TURN_ALLOWED_CLASS = "machine_registry_directory"
EXPECTED_DERIVATION_COMPLETENESS_ROWS = {
    "explicit_derivation_row_family": {
        "order": 1,
        "contract_phrase": "required derivation-class-profile rows must remain explicit as a separate machine-readable row family;",
    },
    "congruent_derivation_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_derivation_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for that family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_derivation_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize derivation legality while missing or unexpected corpus-class identities remain known only internally;",
    },
    "fail_close_preserves_derivation_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## One-way derivation discipline",
        "a later enforcement verdict may expose incompleteness, but it must not become the semantic parent of the earlier layer it tests.",
        "Explanatory or evidence surfaces may motivate strengthening, but they must re-enter root law only through governed refreezing at the proper layer.",
        "## Root derivation completeness discipline",
        "These derivation-completeness rules must remain bound to canonical derivation-completeness rows rather than drifting into soft summary prose.",
        "1. required derivation-class-profile rows must remain explicit as a separate machine-readable row family;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Derivation direction must stay one-way",
        "Later enforcement may reveal incompleteness; it never becomes the semantic author of the earlier law it tests.",
        "A motivating surface is not yet a law-bearing parent surface.",
        "### Derivation row-family completeness must stay explicit",
        "README root derivation completeness discipline must therefore stay congruent with admitted derivation-completeness rows rather than becoming a freehand completeness summary.",
        "The machine world must not finalize derivation legality while required corpus-class identity drift remains known only internally.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Constitutional derivation discipline",
        "Current stream, checker, or verdict state must not be reverse-projected into constitutional source law.",
        "Operational evidence may justify constitutional strengthening, but it becomes law only after governed refreezing at constitutional or contract layers.",
        "## Root derivation completeness boundary",
        "1. Derivation law must remain machine-readable as a separate derivation-class-profile row family.",
        "4. Protocol legality must not finalize derivation legality while missing or unexpected corpus-class identities remain known only inside validator logic.",
        "6. README root derivation completeness discipline rendered at protocol root must remain congruent with admitted derivation-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime derivation boundary",
        "Runtime execution may expose shared-law gaps, but it must not self-author protocol law by reverse projection from a current-turn verdict.",
        "Runtime evidence can trigger strengthening; it becomes shared law only after governed refreezing through the proper root-law surfaces.",
        "## Runtime derivation consumption boundary",
        "1. Runtime consumes derivation law as a separate derivation-class-profile row family rather than as undifferentiated derivation prose.",
        "4. Runtime must not finalize derivation legality while missing or unexpected corpus-class identities remain known only inside validator machinery.",
        "6. Runtime consumes README root derivation completeness discipline as a governed completeness projection bound to admitted derivation-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus one-way derivation topology.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    derivation_doc, derivation_entry_path, derivation_active_path, derivation_alias_error = load_root_corpus_derivation(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    question_routing_doc, question_routing_entry_path, question_routing_active_path, question_routing_alias_error = (
        load_root_corpus_question_routing(repo_root)
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    derivation_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if derivation_alias_error:
        stale_reasons.append(f"root_corpus_derivation_alias_error:{derivation_alias_error}")
        error_code = ERR_REGISTRY
    elif not derivation_doc:
        stale_reasons.append("root_corpus_derivation_empty_or_invalid")
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

    anchor_checks = derivation_anchor_checks_from_doc(derivation_doc) if derivation_doc else ()
    class_profiles = derivation_class_profiles_from_doc(derivation_doc) if derivation_doc else ()
    derivation_completeness_rows = derivation_completeness_rows_from_doc(derivation_doc) if derivation_doc else ()
    derivation_completeness_surface = readme_derivation_completeness_surface(repo_root)
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    source_rows = source_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_profiles = authority_class_profiles_from_doc(authority_doc) if authority_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(question_routing_doc) if question_routing_doc else adjudication_redirect_from_doc({})

    if not stale_reasons:
        if str(derivation_doc.get("derivation_family") or "").strip() != "protocol_root_corpus_derivation":
            stale_reasons.append("root_corpus_derivation_family_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("derivation_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_derivation_version_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_derivation_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_derivation_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_derivation_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("authority_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-authority.current.yaml":
            stale_reasons.append("root_corpus_derivation_authority_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("question_routing_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-question-routing.current.yaml":
            stale_reasons.append("root_corpus_derivation_question_routing_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_derivation.py":
            stale_reasons.append("root_corpus_derivation_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh":
            stale_reasons.append("root_corpus_derivation_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(derivation_doc.get("common_script") or "").strip() != "scripts/root_corpus_derivation_common.py":
            stale_reasons.append("root_corpus_derivation_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(derivation_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_derivation_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_derivation_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_derivation_class_profiles_missing")
            error_code = ERR_REGISTRY
        if not derivation_completeness_rows:
            stale_reasons.append("root_corpus_derivation_completeness_rows_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_derivation",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    class_profile_map = {row.corpus_class: row for row in class_profiles}
    authority_profile_map = {row.corpus_class: row for row in authority_profiles}
    source_rank_by_class = {row.corpus_class: row.order for row in source_rows}

    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "derivation_class_profiles",
                "member_id_key": "corpus_class",
                "actual_rows": class_profiles,
                "expected_rows": {corpus_class: {} for corpus_class in registry_classes},
                "id_attr": "corpus_class",
            },
            {
                "family_id": "derivation_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": derivation_completeness_rows,
                "expected_rows": {
                    completeness_id: {}
                    for completeness_id in EXPECTED_DERIVATION_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "derivation_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": derivation_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {}
                    for row in EXPECTED_DERIVATION_COMPLETENESS_ROWS.values()
                },
                "id_attr": "contract_phrase",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    row_family_projection_by_id = index_row_family_projection_rows(
        row_family_projection_rows
    )
    if not stale_reasons:
        append_root_doc_anchor_registry_structure_violations(
            structure_violations,
            anchor_checks,
            field_name="derivation_anchor_checks",
            registry_paths=registry_paths,
            registry_entry_kind_map=registry_entry_kind_map,
            registry_entry_law_bearing_map=registry_entry_law_bearing_map,
            require_file_entry=True,
            require_law_bearing=True,
        )

        append_membership_delta_violations(
            structure_violations,
            field_name="derivation_class_profiles",
            expected_ids=registry_classes,
            actual_ids=class_profile_map,
            payload_key="corpus_classes",
            missing_reason="missing_registry_classes",
            extra_reason="extra_unregistered_classes",
            duplicate_reason="duplicate_corpus_class",
            actual_total_count=len(class_profiles),
        )
        for reason in derivation_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "derivation_completeness_surface",
                    "reason": f"derivation_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": derivation_completeness_rows,
                    "expected_rows": EXPECTED_DERIVATION_COMPLETENESS_ROWS,
                    "field_name": "derivation_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "non_contiguous_reason": "derivation_completeness_row_order_non_contiguous",
                    "order_reason": "derivation_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": derivation_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_DERIVATION_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "derivation_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_derivation_completeness_surface_phrase",
                    "non_contiguous_reason": "derivation_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_derivation_completeness_surface_rows",
                    "extra_reason": "extra_derivation_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "derivation_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=derivation_violations,
        )

        expected_forbidden_root_classes = sorted(set(registry_classes) - {EXPECTED_CURRENT_TURN_ALLOWED_CLASS})
        actual_forbidden_root_classes = sorted(set(adjudication_redirect.forbidden_root_corpus_classes))
        if adjudication_redirect.question_class != "current_turn_legality":
            derivation_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "question_class_mismatch",
                    "expected": "current_turn_legality",
                    "actual": adjudication_redirect.question_class,
                }
            )
        if actual_forbidden_root_classes != expected_forbidden_root_classes:
            derivation_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "current_turn_forbidden_root_classes_mismatch",
                    "expected": expected_forbidden_root_classes,
                    "actual": actual_forbidden_root_classes,
                }
            )
        if EXPECTED_CURRENT_TURN_ALLOWED_CLASS in actual_forbidden_root_classes:
            derivation_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "machine_registry_directory_must_remain_current_turn_allowed",
                    "corpus_class": EXPECTED_CURRENT_TURN_ALLOWED_CLASS,
                }
            )

        for row in class_profiles:
            expected = EXPECTED_CLASS_RULES.get(row.corpus_class)
            if expected is None:
                continue
            if row.derivation_mode != expected["derivation_mode"]:
                derivation_violations.append(
                    {
                        "field": "derivation_class_profiles",
                        "reason": "derivation_mode_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["derivation_mode"],
                        "actual": row.derivation_mode,
                    }
                )
            if tuple(row.allowed_upstream_classes) != tuple(expected["allowed_upstream_classes"]):
                derivation_violations.append(
                    {
                        "field": "derivation_class_profiles",
                        "reason": "allowed_upstream_classes_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": list(expected["allowed_upstream_classes"]),
                        "actual": list(row.allowed_upstream_classes),
                    }
                )
            if bool(row.law_bearing_required) != bool(expected["law_bearing_required"]):
                derivation_violations.append(
                    {
                        "field": "derivation_class_profiles",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["law_bearing_required"]),
                        "actual": bool(row.law_bearing_required),
                    }
                )

            authority_profile = authority_profile_map.get(row.corpus_class)
            if authority_profile is None:
                derivation_violations.append(
                    {
                        "field": "derivation_class_profiles",
                        "reason": "authority_profile_missing",
                        "corpus_class": row.corpus_class,
                    }
                )
            else:
                if authority_profile.authority_mode != expected["expected_authority_mode"]:
                    derivation_violations.append(
                        {
                            "field": "derivation_class_profiles",
                            "reason": "authority_mode_incompatible_with_derivation",
                            "corpus_class": row.corpus_class,
                            "expected": expected["expected_authority_mode"],
                            "actual": authority_profile.authority_mode,
                        }
                    )
                if bool(authority_profile.law_bearing_required) != bool(row.law_bearing_required):
                    derivation_violations.append(
                        {
                            "field": "derivation_class_profiles",
                            "reason": "authority_law_bearing_mismatch",
                            "corpus_class": row.corpus_class,
                            "expected": bool(row.law_bearing_required),
                            "actual": bool(authority_profile.law_bearing_required),
                        }
                    )

            seen_upstreams: set[str] = set()
            for upstream_class in row.allowed_upstream_classes:
                if upstream_class in seen_upstreams:
                    derivation_violations.append(
                        {
                            "field": "derivation_class_profiles",
                            "reason": "duplicate_upstream_class",
                            "corpus_class": row.corpus_class,
                            "upstream_class": upstream_class,
                        }
                    )
                    continue
                seen_upstreams.add(upstream_class)
                if upstream_class == row.corpus_class:
                    derivation_violations.append(
                        {
                            "field": "derivation_class_profiles",
                            "reason": "self_upstream_forbidden",
                            "corpus_class": row.corpus_class,
                        }
                    )
                    continue
                if upstream_class not in registry_classes:
                    derivation_violations.append(
                        {
                            "field": "derivation_class_profiles",
                            "reason": "upstream_class_not_registered",
                            "corpus_class": row.corpus_class,
                            "upstream_class": upstream_class,
                        }
                    )
                    continue
                if row.corpus_class != "root_index":
                    if upstream_class == "root_index":
                        derivation_violations.append(
                            {
                                "field": "derivation_class_profiles",
                                "reason": "root_index_must_not_define_other_layers",
                                "corpus_class": row.corpus_class,
                            }
                        )
                    if row.corpus_class != "demoted_support_directory" and upstream_class == "demoted_support_directory":
                        derivation_violations.append(
                            {
                                "field": "derivation_class_profiles",
                                "reason": "law_bearing_class_must_not_derive_from_demoted_support",
                                "corpus_class": row.corpus_class,
                            }
                        )
                    upstream_rank = source_rank_by_class.get(upstream_class)
                    current_rank = source_rank_by_class.get(row.corpus_class)
                    if current_rank is None:
                        derivation_violations.append(
                            {
                                "field": "derivation_class_profiles",
                                "reason": "corpus_class_missing_from_source_order",
                                "corpus_class": row.corpus_class,
                            }
                        )
                    elif upstream_rank is None:
                        derivation_violations.append(
                            {
                                "field": "derivation_class_profiles",
                                "reason": "upstream_class_missing_from_source_order",
                                "corpus_class": row.corpus_class,
                                "upstream_class": upstream_class,
                            }
                        )
                    elif upstream_rank >= current_rank:
                        derivation_violations.append(
                            {
                                "field": "derivation_class_profiles",
                                "reason": "source_order_inversion",
                                "corpus_class": row.corpus_class,
                                "upstream_class": upstream_class,
                                "upstream_rank": upstream_rank,
                                "current_rank": current_rank,
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
    if not error_code and (derivation_violations or anchor_violations):
        error_code = ERR_DERIVATION

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"derivation_violation:{row['field']}:{row['reason']}" for row in derivation_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    sorted_profiles = sorted(class_profiles, key=lambda item: item.corpus_class)
    sorted_derivation_completeness_rows = sorted(derivation_completeness_rows, key=lambda item: item.order)
    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_DERIVATION),
        "derivation_entry_path": str(derivation_entry_path),
        "derivation_active_path": str(derivation_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "question_routing_entry_path": str(question_routing_entry_path),
        "question_routing_active_path": str(question_routing_active_path),
        "root_dir": str(derivation_doc.get("root_dir") or ""),
        "derivation_completeness_row_count": len(derivation_completeness_rows),
        **project_root_contract_support_projection(
            prefix="derivation",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        **project_named_row_family_statuses(
            row_family_projection_rows_by_id=row_family_projection_by_id,
            specs=(
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_class_profile_row_coverage_status",
                    family_id="derivation_class_profiles",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_class_profile_row_identity_projection_status",
                    family_id="derivation_class_profiles",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_completeness_row_coverage_status",
                    family_id="derivation_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_completeness_row_identity_projection_status",
                    family_id="derivation_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_completeness_surface_coverage_status",
                    family_id="derivation_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="derivation_completeness_surface_identity_projection_status",
                    family_id="derivation_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "permitted_current_turn_root_corpus_class": EXPECTED_CURRENT_TURN_ALLOWED_CLASS,
        "current_turn_forbidden_root_classes": sorted(set(adjudication_redirect.forbidden_root_corpus_classes)),
        "derivation_class_profiles": [
            {
                "corpus_class": row.corpus_class,
                "derivation_mode": row.derivation_mode,
                "allowed_upstream_classes": list(row.allowed_upstream_classes),
                "law_bearing_required": row.law_bearing_required,
            }
            for row in sorted_profiles
        ],
        "derivation_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted_derivation_completeness_rows
        ],
        "derivation_completeness_surface": {
            "rel_path": derivation_completeness_surface.rel_path,
            "entry_count": len(derivation_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in derivation_completeness_surface.rows
            ],
            "extraction_violations": list(derivation_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "derivation_violations": derivation_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
