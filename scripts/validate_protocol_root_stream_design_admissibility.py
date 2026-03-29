#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_expected_root_doc_anchor_stale_reasons,
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
)
from root_contract_row_validation_common import contiguous_orders, validate_contract_row_batches
from root_contract_marker_checks_common import (
    contract_required_markers_from_doc,
    contract_text_marker_checks_from_rows,
    evaluate_contract_text_marker_checks,
    merge_contract_text_marker_checks,
)
from root_contract_integration_checks_common import evaluate_root_contract_integration
from root_contract_verdict_common import project_root_contract_support_verdict
from root_corpus_authority_common import authority_anchor_checks_from_doc, entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import (
    NamedRowFamilyStatusProjectionSpec,
    aggregate_row_family_status,
    index_row_family_projection_rows,
    project_named_row_family_statuses,
    project_root_contract_support_projection,
    project_row_families,
)
from root_stream_design_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    admissibility_limit_rows_from_doc,
    admissibility_proof_rows_from_doc,
    load_root_stream_design_admissibility,
    outcome_class_rows_from_doc,
    required_projection_surfaces_from_doc,
    required_question_rows_from_doc,
    readme_stream_design_admissibility_completeness_surface,
    stream_design_admissibility_completeness_rows_from_doc,
)

STATUS_KEY = "protocol_root_stream_design_admissibility_status"
ERR_REGISTRY = "IP-RSDA-001"
ERR_STRUCTURE = "IP-RSDA-002"
ERR_ADMISSIBILITY = "IP-RSDA-003"

EXPECTED_QUESTION_ROWS = {
    "ontology": {
        "order": 1,
        "contract_heading": "### 1. Ontology question",
        "normative_focus": "object_identity_and_non_collapse",
    },
    "truth_lifecycle": {
        "order": 2,
        "contract_heading": "### 2. Truth-lifecycle question",
        "normative_focus": "canonical_truth_discoverability_admissibility_binding_consumption",
    },
    "normative": {
        "order": 3,
        "contract_heading": "### 3. Normative question",
        "normative_focus": "allowed_actions_fail_close_success_path_and_forbidden_shortcuts",
    },
    "responsibility_split": {
        "order": 4,
        "contract_heading": "### 4. Responsibility-split question",
        "normative_focus": "protocol_instance_operator_boundary",
    },
    "answer_surface": {
        "order": 5,
        "contract_heading": "### 5. Answer-surface question",
        "normative_focus": "stable_operator_delivery_surface",
    },
}
EXPECTED_OUTCOME_CLASSES = (
    "local_technique_only",
    "instance_adaptation_only",
    "governed_extension_strengthening",
    "root_contract_strengthening",
    "constitutional_strengthening",
)
EXPECTED_ADMISSIBILITY_PROOF_ROWS = {
    "ontology_closure_proof": {
        "order": 1,
        "contract_heading": "### 1. Ontology-closure proof",
        "proof_role": "object_identity_non_collapse_proof",
    },
    "truth_lifecycle_closure_proof": {
        "order": 2,
        "contract_heading": "### 2. Truth-lifecycle-closure proof",
        "proof_role": "truth_lifecycle_closure_proof",
    },
    "normative_closure_proof": {
        "order": 3,
        "contract_heading": "### 3. Normative-closure proof",
        "proof_role": "normative_boundary_closure_proof",
    },
    "responsibility_split_closure_proof": {
        "order": 4,
        "contract_heading": "### 4. Responsibility-split-closure proof",
        "proof_role": "responsibility_split_closure_proof",
    },
    "answer_surface_closure_proof": {
        "order": 5,
        "contract_heading": "### 5. Answer-surface-closure proof",
        "proof_role": "operator_answer_surface_closure_proof",
    },
}
EXPECTED_ADMISSIBILITY_LIMIT_ROWS = {
    "ontology_not_truth_lifecycle": {
        "order": 1,
        "contract_phrase": "ontology-closure proof is not proof of truth-lifecycle closure;",
    },
    "truth_lifecycle_not_normative": {
        "order": 2,
        "contract_phrase": "truth-lifecycle-closure proof is not proof of normative closure;",
    },
    "normative_not_responsibility_split": {
        "order": 3,
        "contract_phrase": "normative-closure proof is not proof of responsibility-split closure;",
    },
    "responsibility_split_not_answer_surface": {
        "order": 4,
        "contract_phrase": "responsibility-split-closure proof is not proof of answer-surface closure;",
    },
    "proof_not_projection_substitute": {
        "order": 5,
        "contract_phrase": "no admissibility proof may substitute for mandatory projection into governed surfaces.",
    },
}
EXPECTED_PROJECTION_SURFACES = (
    "governed_governance_surface",
    "governed_review_surface",
    "root_contract_or_machine_registry_surface",
    "validator_and_probe_surface",
    "runtime_answer_surface_if_applicable",
)
EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS = {
    "explicit_stream_design_admissibility_row_families": {
        "order": 1,
        "contract_phrase": "required question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface rows must remain explicit as separate machine-readable families;",
    },
    "congruent_stream_design_admissibility_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_stream_design_admissibility_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_stream_design_admissibility_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_stream_design_admissibility_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for stream-design admissibility",
    "## Admissibility law",
    "## Five required design questions",
    "## Admissibility-proof discipline",
    "## Admissibility-proof limits",
    "## Mandatory projection surfaces",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Stream-design admissibility row-family completeness must stay explicit",
        "Required question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize stream-design admissibility legality while required row identity drift remains known only internally.",
        "README root stream-design admissibility completeness discipline must therefore\nstay congruent with admitted stream-design-admissibility-completeness rows\nrather than becoming a freehand completeness summary.",
    ),
    "identity/protocol/README.md": (
        "## Root stream-design admissibility completeness discipline",
        "Stream-design admissibility law is not a soft prose bundle.",
        "These stream-design-admissibility-completeness rules must remain bound to canonical stream-design-admissibility-completeness rows rather than drifting into soft summary prose.",
        "1. required question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root stream-design admissibility completeness boundary",
        "1. Stream-design admissibility law must remain machine-readable as separate question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface row families.",
        "4. Protocol legality must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root stream-design admissibility completeness discipline rendered at protocol root must remain congruent with admitted stream-design-admissibility-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime stream-design admissibility consumption boundary",
        "1. Runtime consumes stream-design admissibility law as separate question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface row families rather than as undifferentiated design prose.",
        "4. Runtime must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root stream-design admissibility completeness discipline as a governed completeness projection bound to admitted stream-design-admissibility-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def _surface_rows(surface_ids: tuple[str, ...]) -> tuple[SimpleNamespace, ...]:
    return tuple(SimpleNamespace(surface_id=surface_id) for surface_id in surface_ids)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root stream-design admissibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = load_root_stream_design_admissibility(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    admissibility_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if admissibility_alias_error:
        stale_reasons.append(f"root_stream_design_admissibility_alias_error:{admissibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not admissibility_doc:
        stale_reasons.append("root_stream_design_admissibility_empty_or_invalid")
        error_code = ERR_REGISTRY

    for label, doc, alias_error in (
        ("root_corpus_registry", registry_doc, registry_alias_error),
        ("root_corpus_ordering", ordering_doc, ordering_alias_error),
        ("root_corpus_authority", authority_doc, authority_alias_error),
        ("root_corpus_question_routing", routing_doc, routing_alias_error),
    ):
        if alias_error:
            stale_reasons.append(f"{label}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(f"{label}_empty_or_invalid")
            error_code = ERR_REGISTRY

    question_rows = required_question_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    proof_rows = admissibility_proof_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    limit_rows = admissibility_limit_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    outcome_rows = outcome_class_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    projection_surfaces = required_projection_surfaces_from_doc(admissibility_doc) if admissibility_doc else ()
    projection_surface_rows = _surface_rows(projection_surfaces)
    stream_design_admissibility_completeness_rows = (
        stream_design_admissibility_completeness_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    )
    stream_design_admissibility_completeness_surface = readme_stream_design_admissibility_completeness_surface(repo_root)
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(admissibility_doc) if admissibility_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "admissibility_family": "protocol_root_stream_design_admissibility",
            "admissibility_version": "v1",
            "contract_file": "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_stream_design_admissibility.py",
            "probe_script": "scripts/ci/run_protocol_root_stream_design_admissibility_probes_ci.sh",
            "common_script": "scripts/root_stream_design_admissibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(admissibility_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_stream_design_admissibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        if not question_rows:
            stale_reasons.append("root_stream_design_admissibility_question_rows_missing")
            error_code = ERR_REGISTRY
        if not proof_rows:
            stale_reasons.append("root_stream_design_admissibility_proof_rows_missing")
            error_code = ERR_REGISTRY
        if not limit_rows:
            stale_reasons.append("root_stream_design_admissibility_limit_rows_missing")
            error_code = ERR_REGISTRY
        if not outcome_rows:
            stale_reasons.append("root_stream_design_admissibility_outcome_rows_missing")
            error_code = ERR_REGISTRY
        if not projection_surfaces:
            stale_reasons.append("root_stream_design_admissibility_projection_surfaces_missing")
            error_code = ERR_REGISTRY
        if not stream_design_admissibility_completeness_rows:
            stale_reasons.append("root_stream_design_admissibility_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not admissibility_doc.get("contract_required_markers"):
            stale_reasons.append("root_stream_design_admissibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_stream_design_admissibility",
        ):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(admissibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_stream_design_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_question_rows",
                    "member_id_key": "question_id",
                    "actual_rows": question_rows,
                    "expected_rows": EXPECTED_QUESTION_ROWS,
                    "id_attr": "question_id",
                },
                {
                    "family_id": "required_admissibility_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": proof_rows,
                    "expected_rows": EXPECTED_ADMISSIBILITY_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_admissibility_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": limit_rows,
                    "expected_rows": EXPECTED_ADMISSIBILITY_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "admissibility_outcome_rows",
                    "member_id_key": "outcome_class",
                    "actual_rows": outcome_rows,
                    "expected_rows": {outcome_class: {"order": idx} for idx, outcome_class in enumerate(EXPECTED_OUTCOME_CLASSES, start=1)},
                    "id_attr": "outcome_class",
                },
                {
                    "family_id": "required_projection_surfaces",
                    "member_id_key": "surface_id",
                    "actual_rows": projection_surface_rows,
                    "expected_rows": {surface_id: {"order": idx} for idx, surface_id in enumerate(EXPECTED_PROJECTION_SURFACES, start=1)},
                    "id_attr": "surface_id",
                },
                {
                    "family_id": "stream_design_admissibility_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": stream_design_admissibility_completeness_rows,
                    "expected_rows": {
                        completeness_id: {}
                        for completeness_id in EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "stream_design_admissibility_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": stream_design_admissibility_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS.values()
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
        outcome_orders = [row.order for row in outcome_rows]
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": question_rows,
                    "expected_rows": EXPECTED_QUESTION_ROWS,
                    "field_name": "required_question_rows",
                    "id_attr": "question_id",
                    "compare_fields": ("contract_heading", "normative_focus"),
                    "non_contiguous_reason": "question_order_non_contiguous",
                    "missing_reason": "missing_expected_questions",
                    "extra_reason": "extra_questions",
                    "missing_ids_key": "question_ids",
                    "extra_ids_key": "question_ids",
                    "violation_id_key": "question_id",
                    "order_reason": "question_order_mismatch",
                },
                {
                    "actual_rows": proof_rows,
                    "expected_rows": EXPECTED_ADMISSIBILITY_PROOF_ROWS,
                    "field_name": "required_admissibility_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                    "non_contiguous_reason": "proof_order_non_contiguous",
                    "missing_ids_key": "proof_ids",
                    "extra_ids_key": "proof_ids",
                    "violation_id_key": "proof_id",
                    "order_reason": "proof_order_mismatch",
                },
                {
                    "actual_rows": limit_rows,
                    "expected_rows": EXPECTED_ADMISSIBILITY_LIMIT_ROWS,
                    "field_name": "required_admissibility_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_limit_id",
                    "non_contiguous_reason": "limit_order_non_contiguous",
                    "missing_ids_key": "limit_ids",
                    "extra_ids_key": "limit_ids",
                    "violation_id_key": "limit_id",
                    "order_reason": "limit_order_mismatch",
                },
                {
                    "actual_rows": stream_design_admissibility_completeness_rows,
                    "expected_rows": EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS,
                    "field_name": "stream_design_admissibility_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_stream_design_admissibility_completeness_id",
                    "non_contiguous_reason": "stream_design_admissibility_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_stream_design_admissibility_completeness_rows",
                    "extra_reason": "extra_stream_design_admissibility_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "stream_design_admissibility_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": stream_design_admissibility_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "stream_design_admissibility_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_stream_design_admissibility_completeness_surface_phrase",
                    "non_contiguous_reason": "stream_design_admissibility_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_stream_design_admissibility_completeness_surface_rows",
                    "extra_reason": "extra_stream_design_admissibility_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "stream_design_admissibility_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            admissibility_violations=admissibility_violations,
        )

        if len(set(outcome_orders)) != len(outcome_orders) or not contiguous_orders(sorted(outcome_orders)):
            structure_violations.append({"field": "admissibility_outcome_rows", "reason": "outcome_order_non_contiguous"})
        actual_outcomes = tuple(row.outcome_class for row in sorted(outcome_rows, key=lambda item: item.order))
        if actual_outcomes != EXPECTED_OUTCOME_CLASSES:
            admissibility_violations.append(
                {
                    "field": "admissibility_outcome_rows",
                    "reason": "outcome_classes_mismatch",
                    "expected": list(EXPECTED_OUTCOME_CLASSES),
                    "actual": list(actual_outcomes),
                }
            )

        if tuple(projection_surfaces) != EXPECTED_PROJECTION_SURFACES:
            admissibility_violations.append(
                {
                    "field": "required_projection_surfaces",
                    "reason": "projection_surfaces_mismatch",
                    "expected": list(EXPECTED_PROJECTION_SURFACES),
                    "actual": list(projection_surfaces),
                }
            )

        expected_stream_design_admissibility_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS.values()
        ]
        actual_stream_design_admissibility_completeness_phrases = [
            row.contract_phrase for row in stream_design_admissibility_completeness_surface.rows
        ]
        expected_stream_design_admissibility_completeness_orders = [
            int(row["order"]) for row in EXPECTED_STREAM_DESIGN_ADMISSIBILITY_COMPLETENESS_ROWS.values()
        ]
        actual_stream_design_admissibility_completeness_orders = [
            row.order for row in stream_design_admissibility_completeness_surface.rows
        ]
        for reason in stream_design_admissibility_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "stream_design_admissibility_completeness_surface",
                    "reason": f"stream_design_admissibility_completeness_surface_{reason}",
                }
            )
        if actual_stream_design_admissibility_completeness_phrases and tuple(
            actual_stream_design_admissibility_completeness_phrases
        ) != tuple(expected_stream_design_admissibility_completeness_phrases):
            admissibility_violations.append(
                {
                    "field": "stream_design_admissibility_completeness_surface",
                    "reason": "stream_design_admissibility_completeness_surface_phrase_order_mismatch",
                    "expected": expected_stream_design_admissibility_completeness_phrases,
                    "actual": actual_stream_design_admissibility_completeness_phrases,
                }
            )
        if actual_stream_design_admissibility_completeness_orders and tuple(
            actual_stream_design_admissibility_completeness_orders
        ) != tuple(expected_stream_design_admissibility_completeness_orders):
            admissibility_violations.append(
                {
                    "field": "stream_design_admissibility_completeness_surface",
                    "reason": "stream_design_admissibility_completeness_surface_order_mismatch",
                    "expected": expected_stream_design_admissibility_completeness_orders,
                    "actual": actual_stream_design_admissibility_completeness_orders,
                }
            )

        contract_file = str(admissibility_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            admissibility_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(admissibility_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            question_rows,
                            reason="question_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            proof_rows,
                            reason="proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            limit_rows,
                            reason="limit_phrase_missing",
                            marker_attrs=("contract_phrase",),
                        ),
                    ),
                    payload_base={"rel_path": contract_file},
                )
            )

        root_doc_anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                root_doc_anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

        integration_violations.extend(
            evaluate_root_contract_integration(
                contract_file=contract_file,
                registry_entries=registry_entries,
                reading_rows=reading_rows,
                authority_anchors=authority_anchors,
                authority_projections=authority_projections,
                routing_anchors=routing_anchors,
                routing_projections=routing_projections,
                expected_registry_markers=EXPECTED_REGISTRY_MARKERS,
                mappings_required_children=('root-stream-design-admissibility.current.yaml', 'root-stream-design-admissibility.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = admissibility_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_ADMISSIBILITY,
        support_reason_prefix="admissibility_violation",
        support_fallback_field="contract_markers",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ADMISSIBILITY),
        "admissibility_entry_path": str(admissibility_entry_path),
        "admissibility_active_path": str(admissibility_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(admissibility_doc.get("contract_file") or ""),
        "question_count": len(question_rows),
        "proof_count": len(proof_rows),
        "limit_count": len(limit_rows),
        "outcome_count": len(outcome_rows),
        "projection_surface_count": len(projection_surfaces),
        "stream_design_admissibility_completeness_row_count": len(stream_design_admissibility_completeness_rows),
        **project_root_contract_support_projection(
            prefix="stream_design",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        **project_named_row_family_statuses(
            row_family_projection_rows_by_id=row_family_projection_by_id,
            specs=(
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="stream_design_admissibility_completeness_row_coverage_status",
                    family_id="stream_design_admissibility_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="stream_design_admissibility_completeness_row_identity_projection_status",
                    family_id="stream_design_admissibility_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="stream_design_admissibility_completeness_surface_coverage_status",
                    family_id="stream_design_admissibility_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="stream_design_admissibility_completeness_surface_identity_projection_status",
                    family_id="stream_design_admissibility_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "question_ids": [row.question_id for row in sorted(question_rows, key=lambda item: item.order)],
        "proof_ids": [row.proof_id for row in sorted(proof_rows, key=lambda item: item.order)],
        "limit_ids": [row.row_id for row in sorted(limit_rows, key=lambda item: item.order)],
        "outcome_classes": [row.outcome_class for row in sorted(outcome_rows, key=lambda item: item.order)],
        "projection_surfaces": list(projection_surfaces),
        "stream_design_admissibility_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(stream_design_admissibility_completeness_rows, key=lambda item: item.order)
        ],
        "stream_design_admissibility_completeness_surface": {
            "rel_path": stream_design_admissibility_completeness_surface.rel_path,
            "entry_count": len(stream_design_admissibility_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in stream_design_admissibility_completeness_surface.rows
            ],
            "extraction_violations": list(stream_design_admissibility_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "admissibility_violations": admissibility_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
