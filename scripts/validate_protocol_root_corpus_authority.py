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
from root_corpus_authority_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    authority_anchor_checks_from_doc,
    authority_class_profiles_from_doc,
    authority_completeness_rows_from_doc,
    authority_layer_stages_from_doc,
    entry_authority_projections_from_doc,
    load_root_corpus_authority,
    readme_authority_completeness_surface,
    readme_authority_layer_surface,
)
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc

STATUS_KEY = "protocol_root_corpus_authority_status"
ERR_REGISTRY = "IP-RCA-001"
ERR_STRUCTURE = "IP-RCA-002"
ERR_AUTHORITY = "IP-RCA-003"

EXPECTED_CLASS_RULES = {
    "bottom_theory": {
        "authority_role": "interpretive_bottom_theory",
        "authority_mode": "interpretive_only",
        "philosophical_primacy": True,
        "law_bearing_required": True,
    },
    "root_index": {
        "authority_role": "navigational_root_index",
        "authority_mode": "navigational_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "constitution": {
        "authority_role": "constitutional_protocol_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "runtime_constitution": {
        "authority_role": "constitutional_runtime_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "root_contract": {
        "authority_role": "root_domain_contract_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "machine_registry_directory": {
        "authority_role": "machine_consumed_registry_family",
        "authority_mode": "machine_consumed_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "governed_subdomain_extension": {
        "authority_role": "governed_subdomain_extension_family",
        "authority_mode": "extension_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "demoted_support_directory": {
        "authority_role": "demoted_support_material",
        "authority_mode": "demoted_support_only",
        "philosophical_primacy": False,
        "law_bearing_required": False,
    },
}
ALLOWED_AUTHORITY_MODES = {
    "interpretive_only",
    "navigational_only",
    "frozen_law_only",
    "machine_consumed_family",
    "extension_family",
    "demoted_support_only",
}
EXPECTED_AUTHORITY_COMPLETENESS_ROWS = {
    "explicit_authority_row_families": {
        "order": 1,
        "contract_phrase": "required authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_authority_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_authority_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_authority_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize authority legality while missing or unexpected corpus-class, entry, or authority-layer-stage identities remain known only internally;",
    },
    "fail_close_preserves_authority_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Authority layering",
        "This authority layering must remain bound to canonical authority-layer stage rows rather than becoming a freehand alternate authority ladder.",
        "## Root authority completeness discipline",
        "These authority-completeness rules must remain bound to canonical authority-completeness rows rather than drifting into soft summary prose.",
        "1. required authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface rows must remain explicit as separate machine-readable row families;",
        "machine-consumed enforcement authority",
        "Philosophical primacy, however, is not the same as runtime-source primacy.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Authority row-family completeness must stay explicit",
        "philosophical primacy does not mean runtime-source primacy",
        "machine-consumed authority still lives in frozen contracts, mappings, validators, runtime state, and receipts",
        "README root authority completeness discipline must therefore stay congruent with admitted authority-completeness rows rather than becoming a freehand completeness summary.",
        "README authority layering must therefore stay congruent with admitted authority-layer-stage rows rather than becoming a freehand alternate authority ladder.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root authority completeness boundary",
        "1. Authority law must remain machine-readable as separate authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface row families.",
        "README root authority completeness discipline rendered at protocol root must remain congruent with admitted authority-completeness rows rather than silently authoring an alternate completeness summary.",
        "7. README authority layering stages rendered at protocol root must remain congruent with admitted authority-layer-stage rows rather than silently authoring an alternate authority ladder.",
        "README authority layering stages rendered at protocol root must remain congruent with admitted authority-layer-stage rows rather than silently authoring an alternate authority ladder.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime authority consumption boundary",
        "1. Runtime consumes authority law as separate authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface row families rather than as undifferentiated authority prose.",
        "Runtime consumes README root authority completeness discipline as a governed completeness projection bound to admitted authority-completeness rows rather than as a freehand completeness summary.",
        "7. Runtime consumes README authority layering as a governed stage projection bound to admitted authority-layer-stage rows rather than as a freehand alternate authority ladder.",
        "Runtime consumes README authority layering as a governed stage projection bound to admitted authority-layer-stage rows rather than as a freehand alternate authority ladder.",
    ),
    "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-law primacy legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn epistemic legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn decision-evidence legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn success-path state legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ERROR_TERMINALITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn error terminality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn artifact-family admissibility must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_DISCOVERY.md": (
        "## Runtime adjudication boundary",
        "Current-turn discovery legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn self-judgement legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/AGENT_HANDOFF_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn responsibility legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn truth lifecycle legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
}
EXPECTED_AUTHORITY_COMPLETENESS_ROWS = {
    "explicit_authority_row_families": {
        "order": 1,
        "contract_phrase": "required authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_authority_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_authority_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_authority_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize authority legality while missing or unexpected corpus-class, entry, or authority-layer-stage identities remain known only internally;",
    },
    "fail_close_preserves_authority_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_AUTHORITY_LAYER_STAGES = {
    "bottom-theory primacy": {
        "order": 1,
        "bound_corpus_classes": ("bottom_theory",),
        "bound_authority_roles": ("interpretive_bottom_theory",),
        "bound_machine_surfaces": (),
        "required_markers": (
            "`IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`",
            "explains *why* protocol law has the shape it has.",
        ),
    },
    "constitutional / contract authority": {
        "order": 2,
        "bound_corpus_classes": ("constitution", "runtime_constitution", "root_contract"),
        "bound_authority_roles": (
            "constitutional_protocol_law",
            "constitutional_runtime_law",
            "root_domain_contract_law",
        ),
        "bound_machine_surfaces": (),
        "required_markers": (
            "`IDENTITY_PROTOCOL.md`",
            "`IDENTITY_RUNTIME.md`",
            "root contract files such as machine-law primacy, machine-world ontology, current-truth epistemology, decision-evidence admissibility, success-path state admissibility, entry-surface legitimacy, error terminality, artifact-family admissibility, prompt bootstrap, discovery, handoff, instance self-judgement, protocol-instance responsibility, stream-design admissibility, truth-lifecycle, and operator answer-surface contracts",
            "these define *what law is concretely frozen*.",
        ),
    },
    "machine-consumed enforcement authority": {
        "order": 3,
        "bound_corpus_classes": ("machine_registry_directory",),
        "bound_authority_roles": ("machine_consumed_registry_family",),
        "bound_machine_surfaces": (
            "governance_review_docs",
            "mappings",
            "validators",
            "probes",
            "runtime_state",
            "receipts",
        ),
        "required_markers": (
            "governance/review docs",
            "mappings",
            "validators",
            "probes",
            "runtime state",
            "receipts",
            "these determine *current machine truth and pass/fail authority*.",
        ),
    },
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus authority layering and authority-role topology.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    authority_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
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

    anchor_checks = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    class_profiles = authority_class_profiles_from_doc(authority_doc) if authority_doc else ()
    entry_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    authority_layer_stages = authority_layer_stages_from_doc(authority_doc) if authority_doc else ()
    authority_completeness_rows = authority_completeness_rows_from_doc(authority_doc) if authority_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_completeness_surface = readme_authority_completeness_surface(repo_root)
    authority_layer_surface = readme_authority_layer_surface(repo_root)

    if not stale_reasons:
        if str(authority_doc.get("authority_family") or "").strip() != "protocol_root_corpus_authority":
            stale_reasons.append("root_corpus_authority_family_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("authority_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_authority_version_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_authority_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_authority_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_authority_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_authority.py":
            stale_reasons.append("root_corpus_authority_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh":
            stale_reasons.append("root_corpus_authority_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("common_script") or "").strip() != "scripts/root_corpus_authority_common.py":
            stale_reasons.append("root_corpus_authority_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(authority_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_authority_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_authority_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_authority_class_profiles_missing")
            error_code = ERR_REGISTRY
        if not entry_projections:
            stale_reasons.append("root_corpus_authority_entry_projection_missing")
            error_code = ERR_REGISTRY
        if not authority_layer_stages:
            stale_reasons.append("root_corpus_authority_layer_stages_missing")
            error_code = ERR_REGISTRY
        if not authority_completeness_rows:
            stale_reasons.append("root_corpus_authority_completeness_rows_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_authority",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_class_law_bearing = {entry.corpus_class: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    class_profile_map = {row.corpus_class: row for row in class_profiles}
    entry_projection_map = {row.rel_path: row for row in entry_projections}
    authority_layer_stage_map = {row.stage_label: row for row in authority_layer_stages}
    authority_layer_surface_map = {row.stage_label: row for row in authority_layer_surface.rows}
    ordering_reading_paths = [row.rel_path for row in sorted(reading_rows, key=lambda item: item.order)]
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip() if ordering_doc else ""

    if not stale_reasons:
        for reason in authority_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "authority_completeness_surface",
                    "reason": f"authority_completeness_surface_{reason}",
                }
            )
        append_root_doc_anchor_registry_structure_violations(
            structure_violations,
            anchor_checks,
            field_name="authority_anchor_checks",
            registry_paths=registry_paths,
            registry_entry_kind_map=registry_entry_kind_map,
            registry_entry_law_bearing_map=registry_entry_law_bearing_map,
            require_file_entry=True,
            require_law_bearing=True,
        )

        append_membership_delta_violations(
            structure_violations,
            field_name="authority_class_profiles",
            expected_ids=registry_classes,
            actual_ids=class_profile_map,
            payload_key="corpus_classes",
            missing_reason="missing_registry_classes",
            extra_reason="extra_unregistered_classes",
            duplicate_reason="duplicate_corpus_class",
            actual_total_count=len(class_profiles),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="entry_authority_projection",
            expected_ids=registry_paths,
            actual_ids=entry_projection_map,
            payload_key="rel_paths",
            missing_reason="missing_registered_entries",
            extra_reason="extra_unregistered_entries",
            duplicate_reason="duplicate_rel_path",
            actual_total_count=len(entry_projections),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="authority_layer_stages",
            expected_ids=EXPECTED_AUTHORITY_LAYER_STAGES,
            actual_ids=authority_layer_stage_map,
            payload_key="stage_labels",
            missing_reason="missing_authority_layer_stages",
            extra_reason="extra_authority_layer_stages",
            duplicate_reason="duplicate_authority_layer_stage",
            actual_total_count=len(authority_layer_stages),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="authority_layer_stage_surface",
            expected_ids=EXPECTED_AUTHORITY_LAYER_STAGES,
            actual_ids=authority_layer_surface_map,
            payload_key="stage_labels",
            missing_reason="missing_authority_layer_surface_stages",
            extra_reason="extra_authority_layer_surface_stages",
            duplicate_reason="duplicate_authority_layer_surface_stage",
            actual_total_count=len(authority_layer_surface.rows),
        )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": authority_completeness_rows,
                    "expected_rows": EXPECTED_AUTHORITY_COMPLETENESS_ROWS,
                    "field_name": "authority_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_authority_completeness_id",
                    "non_contiguous_reason": "authority_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_authority_completeness_rows",
                    "extra_reason": "extra_authority_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "authority_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": authority_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_AUTHORITY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "authority_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_authority_completeness_surface_phrase",
                    "non_contiguous_reason": "authority_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_authority_completeness_surface_rows",
                    "extra_reason": "extra_authority_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "authority_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=authority_violations,
        )
        expected_authority_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_AUTHORITY_COMPLETENESS_ROWS.values()
        ]
        actual_authority_completeness_phrases = [
            row.contract_phrase for row in authority_completeness_surface.rows
        ]
        expected_authority_completeness_orders = [
            int(row["order"]) for row in EXPECTED_AUTHORITY_COMPLETENESS_ROWS.values()
        ]
        actual_authority_completeness_orders = [
            row.order for row in authority_completeness_surface.rows
        ]
        if actual_authority_completeness_phrases and tuple(actual_authority_completeness_phrases) != tuple(
            expected_authority_completeness_phrases
        ):
            authority_violations.append(
                {
                    "field": "authority_completeness_surface",
                    "reason": "authority_completeness_surface_phrase_order_mismatch",
                    "expected": expected_authority_completeness_phrases,
                    "actual": actual_authority_completeness_phrases,
                }
            )
        if actual_authority_completeness_orders and tuple(actual_authority_completeness_orders) != tuple(
            expected_authority_completeness_orders
        ):
            authority_violations.append(
                {
                    "field": "authority_completeness_surface",
                    "reason": "authority_completeness_surface_order_mismatch",
                    "expected": expected_authority_completeness_orders,
                    "actual": actual_authority_completeness_orders,
                }
            )
        for row in class_profiles:
            if row.authority_mode not in ALLOWED_AUTHORITY_MODES:
                structure_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "invalid_authority_mode",
                        "corpus_class": row.corpus_class,
                        "authority_mode": row.authority_mode,
                    }
                )
            expected = EXPECTED_CLASS_RULES.get(row.corpus_class)
            if expected is None:
                continue
            if row.authority_role != expected["authority_role"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_role_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_role"],
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != expected["authority_mode"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_mode_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_mode"],
                        "actual": row.authority_mode,
                    }
                )
            if bool(row.philosophical_primacy) != bool(expected["philosophical_primacy"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "philosophical_primacy_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["philosophical_primacy"]),
                        "actual": bool(row.philosophical_primacy),
                    }
                )
            if bool(row.law_bearing_required) != bool(expected["law_bearing_required"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["law_bearing_required"]),
                        "actual": bool(row.law_bearing_required),
                    }
                )
            registry_law_bearing = registry_class_law_bearing.get(row.corpus_class)
            if registry_law_bearing is not None and bool(row.law_bearing_required) != bool(registry_law_bearing):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "registry_law_bearing_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(registry_law_bearing),
                        "actual": bool(row.law_bearing_required),
                    }
                )

        primacy_classes = sorted(row.corpus_class for row in class_profiles if row.philosophical_primacy)
        if primacy_classes != ["bottom_theory"]:
            authority_violations.append(
                {
                    "field": "authority_class_profiles",
                    "reason": "philosophical_primacy_not_exclusive_to_bottom_theory",
                    "corpus_classes": primacy_classes,
                }
            )

        for row in entry_projections:
            expected_class = registry_entry_class_map.get(row.rel_path)
            if expected_class and row.corpus_class != expected_class:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_corpus_class_mismatch",
                        "rel_path": row.rel_path,
                        "expected": expected_class,
                        "actual": row.corpus_class,
                    }
                )
            class_profile = class_profile_map.get(row.corpus_class)
            if class_profile is None:
                continue
            if row.authority_role != class_profile.authority_role:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_role_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_role,
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != class_profile.authority_mode:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_mode_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_mode,
                        "actual": row.authority_mode,
                    }
                )

        if root_index_entry:
            root_index_projection = entry_projection_map.get(root_index_entry)
            if root_index_projection is None:
                authority_violations.append(
                    {"field": "entry_authority_projection", "reason": "root_index_entry_missing_projection", "rel_path": root_index_entry}
                )
            else:
                if root_index_projection.corpus_class != "root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_class",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.corpus_class,
                        }
                    )
                if root_index_projection.authority_role != "navigational_root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_role",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_role,
                        }
                    )
                if root_index_projection.authority_mode != "navigational_only":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_mode",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_mode,
                        }
                    )

        expected_stage_labels = list(EXPECTED_AUTHORITY_LAYER_STAGES.keys())
        expected_stage_orders = [int(stage["order"]) for stage in EXPECTED_AUTHORITY_LAYER_STAGES.values()]
        actual_stage_orders = [row.order for row in authority_layer_stages]
        actual_surface_orders = [row.order for row in authority_layer_surface.rows]
        actual_surface_labels = [row.stage_label for row in authority_layer_surface.rows]
        if len(set(actual_stage_orders)) != len(actual_stage_orders):
            structure_violations.append(
                {"field": "authority_layer_stages", "reason": "duplicate_authority_layer_stage_order"}
            )
        if actual_stage_orders and sorted(actual_stage_orders) != list(range(1, len(actual_stage_orders) + 1)):
            structure_violations.append(
                {"field": "authority_layer_stages", "reason": "authority_layer_stage_order_non_contiguous"}
            )
        if len(set(actual_surface_orders)) != len(actual_surface_orders):
            structure_violations.append(
                {"field": "authority_layer_stage_surface", "reason": "duplicate_authority_layer_surface_order"}
            )
        if actual_surface_orders and sorted(actual_surface_orders) != list(range(1, len(actual_surface_orders) + 1)):
            structure_violations.append(
                {"field": "authority_layer_stage_surface", "reason": "authority_layer_surface_order_non_contiguous"}
            )
        if actual_surface_labels and tuple(actual_surface_labels) != tuple(expected_stage_labels):
            authority_violations.append(
                {
                    "field": "authority_layer_stage_surface",
                    "reason": "authority_layer_surface_label_order_mismatch",
                    "expected": expected_stage_labels,
                    "actual": actual_surface_labels,
                }
            )
        if actual_surface_orders and tuple(actual_surface_orders) != tuple(expected_stage_orders):
            authority_violations.append(
                {
                    "field": "authority_layer_stage_surface",
                    "reason": "authority_layer_surface_stage_order_mismatch",
                    "expected": expected_stage_orders,
                    "actual": actual_surface_orders,
                }
            )
        for stage_label, expected in EXPECTED_AUTHORITY_LAYER_STAGES.items():
            stage_row = authority_layer_stage_map.get(stage_label)
            if stage_row is not None:
                if stage_row.order != int(expected["order"]):
                    authority_violations.append(
                        {
                            "field": "authority_layer_stages",
                            "reason": "authority_layer_stage_order_mismatch",
                            "stage_label": stage_label,
                            "expected": int(expected["order"]),
                            "actual": stage_row.order,
                        }
                    )
                if tuple(stage_row.bound_corpus_classes) != tuple(expected["bound_corpus_classes"]):
                    authority_violations.append(
                        {
                            "field": "authority_layer_stages",
                            "reason": "bound_corpus_classes_mismatch",
                            "stage_label": stage_label,
                            "expected": list(expected["bound_corpus_classes"]),
                            "actual": list(stage_row.bound_corpus_classes),
                        }
                    )
                if tuple(stage_row.bound_authority_roles) != tuple(expected["bound_authority_roles"]):
                    authority_violations.append(
                        {
                            "field": "authority_layer_stages",
                            "reason": "bound_authority_roles_mismatch",
                            "stage_label": stage_label,
                            "expected": list(expected["bound_authority_roles"]),
                            "actual": list(stage_row.bound_authority_roles),
                        }
                    )
                if tuple(stage_row.bound_machine_surfaces) != tuple(expected["bound_machine_surfaces"]):
                    authority_violations.append(
                        {
                            "field": "authority_layer_stages",
                            "reason": "bound_machine_surfaces_mismatch",
                            "stage_label": stage_label,
                            "expected": list(expected["bound_machine_surfaces"]),
                            "actual": list(stage_row.bound_machine_surfaces),
                        }
                    )
                if tuple(stage_row.required_markers) != tuple(expected["required_markers"]):
                    authority_violations.append(
                        {
                            "field": "authority_layer_stages",
                            "reason": "required_markers_mismatch",
                            "stage_label": stage_label,
                            "expected": list(expected["required_markers"]),
                            "actual": list(stage_row.required_markers),
                        }
                    )
            surface_row = authority_layer_surface_map.get(stage_label)
            if surface_row is not None:
                surface_text = "\n".join(surface_row.body_lines)
                for marker in expected["required_markers"]:
                    if marker not in surface_text:
                        authority_violations.append(
                            {
                                "field": "authority_layer_stage_surface",
                                "reason": "required_marker_missing",
                                "stage_label": stage_label,
                                "marker": marker,
                            }
                        )

        for reason in authority_layer_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "authority_layer_stage_surface",
                    "reason": f"authority_layer_surface_{reason}",
                }
            )

        if ordering_reading_paths and ordering_reading_paths != registry_paths:
            # Registry paths are alphabetical, ordering paths are semantic. No violation here.
            pass

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name="authority_anchor_checks",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (authority_violations or anchor_violations):
        error_code = ERR_AUTHORITY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"authority_violation:{row['field']}:{row['reason']}" for row in authority_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "authority_class_profiles",
                "member_id_key": "corpus_class",
                "actual_rows": class_profiles,
                "expected_rows": {corpus_class: {} for corpus_class in registry_classes},
                "id_attr": "corpus_class",
            },
            {
                "family_id": "entry_authority_projection",
                "member_id_key": "rel_path",
                "actual_rows": entry_projections,
                "expected_rows": {rel_path: {} for rel_path in registry_paths},
                "id_attr": "rel_path",
            },
            {
                "family_id": "authority_layer_stages",
                "member_id_key": "stage_label",
                "actual_rows": authority_layer_stages,
                "expected_rows": EXPECTED_AUTHORITY_LAYER_STAGES,
                "id_attr": "stage_label",
            },
            {
                "family_id": "authority_layer_stage_surface",
                "member_id_key": "stage_label",
                "actual_rows": authority_layer_surface.rows,
                "expected_rows": EXPECTED_AUTHORITY_LAYER_STAGES,
                "id_attr": "stage_label",
            },
            {
                "family_id": "authority_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": authority_completeness_rows,
                "expected_rows": {row_id: {} for row_id in EXPECTED_AUTHORITY_COMPLETENESS_ROWS},
                "id_attr": "completeness_id",
            },
            {
                "family_id": "authority_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": authority_completeness_surface.rows,
                "expected_rows": {row["contract_phrase"]: {} for row in EXPECTED_AUTHORITY_COMPLETENESS_ROWS.values()},
                "id_attr": "contract_phrase",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    row_family_projection_by_id = index_row_family_projection_rows(
        row_family_projection_rows
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_AUTHORITY),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "root_dir": str(authority_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "authority_anchor_check_count": len(anchor_checks),
        "authority_class_profile_count": len(class_profiles),
        "entry_authority_projection_count": len(entry_projections),
        "authority_layer_stage_count": len(authority_layer_stages),
        "authority_completeness_row_count": len(authority_completeness_rows),
        **project_root_contract_support_projection(
            prefix="authority",
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
                    payload_key="authority_completeness_row_coverage_status",
                    family_id="authority_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="authority_completeness_row_identity_projection_status",
                    family_id="authority_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="authority_completeness_surface_coverage_status",
                    family_id="authority_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="authority_completeness_surface_identity_projection_status",
                    family_id="authority_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "authority_class_profiles": [
            {
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
                "philosophical_primacy": row.philosophical_primacy,
                "law_bearing_required": row.law_bearing_required,
            }
            for row in class_profiles
        ],
        "entry_authority_projection": [
            {
                "rel_path": row.rel_path,
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
            }
            for row in entry_projections
        ],
        "authority_layer_stages": [
            {
                "order": row.order,
                "stage_label": row.stage_label,
                "bound_corpus_classes": list(row.bound_corpus_classes),
                "bound_authority_roles": list(row.bound_authority_roles),
                "bound_machine_surfaces": list(row.bound_machine_surfaces),
                "required_markers": list(row.required_markers),
            }
            for row in sorted(authority_layer_stages, key=lambda item: item.order)
        ],
        "authority_layer_stage_surface": {
            "rel_path": authority_layer_surface.rel_path,
            "entry_count": len(authority_layer_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "stage_label": row.stage_label,
                    "body_lines": list(row.body_lines),
                }
                for row in authority_layer_surface.rows
            ],
            "extraction_violations": list(authority_layer_surface.extraction_violations),
        },
        "authority_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(authority_completeness_rows, key=lambda item: item.order)
        ],
        "authority_completeness_surface": {
            "rel_path": authority_completeness_surface.rel_path,
            "entry_count": len(authority_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in authority_completeness_surface.rows
            ],
            "extraction_violations": list(authority_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "authority_violations": authority_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
