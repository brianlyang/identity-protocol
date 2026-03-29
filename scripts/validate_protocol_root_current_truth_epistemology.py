#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_marker_checks_common import (
    contract_required_markers_from_doc,
    contract_text_marker_checks_from_rows,
    evaluate_contract_text_marker_checks,
    merge_contract_text_marker_checks,
)
from root_contract_integration_checks_common import evaluate_root_contract_integration
from root_contract_verdict_common import project_root_contract_support_verdict
from root_contract_row_validation_common import validate_contract_row_batches
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
    index_row_family_projection_rows,
    project_named_row_family_statuses,
    project_root_contract_support_projection,
    project_row_families,
)
from root_current_truth_epistemology_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    commitment_proof_alignment_rows_from_doc,
    commitment_rows_from_doc,
    current_truth_epistemology_completeness_rows_from_doc,
    differentiation_rows_from_doc,
    epistemic_limit_rows_from_doc,
    epistemic_proof_rows_from_doc,
    load_root_current_truth_epistemology,
    readme_current_truth_epistemology_completeness_surface,
)

STATUS_KEY = "protocol_root_current_truth_epistemology_status"
ERR_REGISTRY = "IP-CTE-001"
ERR_STRUCTURE = "IP-CTE-002"
ERR_EPISTEMOLOGY = "IP-CTE-003"

EXPECTED_COMMITMENT_ROWS = {
    "canonical_source_before_narration": {
        "order": 1,
        "contract_heading": "### 1. Canonical source before narration",
        "epistemic_role": "canonical_source_before_narration",
    },
    "governed_resolution_before_historical_familiarity": {
        "order": 2,
        "contract_heading": "### 2. Governed resolution before historical familiarity",
        "epistemic_role": "governed_resolution_before_historical_familiarity",
    },
    "present_turn_authority_before_visible_recency": {
        "order": 3,
        "contract_heading": "### 3. Present-turn authority before visible recency",
        "epistemic_role": "present_turn_authority_before_visible_recency",
    },
    "provenance_preserving_derivation_before_compressed_summary": {
        "order": 4,
        "contract_heading": "### 4. Provenance-preserving derivation before compressed summary",
        "epistemic_role": "provenance_preserving_derivation_before_compressed_summary",
    },
    "fail_close_justification_before_operational_assertion": {
        "order": 5,
        "contract_heading": "### 5. Fail-close justification before operational assertion",
        "epistemic_role": "fail_close_justification_before_operational_assertion",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "installed_vs_discoverability": {
        "order": 1,
        "contract_phrase": "installed and discoverability are separated;",
    },
    "latest_receipt_vs_current_thread_binding": {
        "order": 2,
        "contract_phrase": "latest receipt and current-thread binding are separated;",
    },
    "continuity_vs_authority": {
        "order": 3,
        "contract_phrase": "continuity and authority are separated;",
    },
    "durable_family_vs_runtime_family": {
        "order": 4,
        "contract_phrase": "pack durable families and runtime families are separated;",
    },
    "retention_governance_feedback_continuity_absorption": {
        "order": 5,
        "contract_phrase": "dialogue-retention, dialogue-governance, protocol-feedback, continuity, and memory-absorption are separated;",
    },
    "declaration_gate_vs_artifact_sink": {
        "order": 6,
        "contract_phrase": "declaration / gate surfaces and artifact sinks are separated.",
    },
}
EXPECTED_EPISTEMIC_PROOF_ROWS = {
    "canonical_source_proof": {
        "order": 1,
        "contract_heading": "### 1. Canonical-source proof",
        "proof_role": "canonical_source_current_truth_proof",
    },
    "governed_resolution_proof": {
        "order": 2,
        "contract_heading": "### 2. Governed-resolution proof",
        "proof_role": "governed_resolution_current_truth_proof",
    },
    "present_turn_authority_proof": {
        "order": 3,
        "contract_heading": "### 3. Present-turn-authority proof",
        "proof_role": "present_turn_authority_current_truth_proof",
    },
    "provenance_preserving_derivation_proof": {
        "order": 4,
        "contract_heading": "### 4. Provenance-preserving-derivation proof",
        "proof_role": "provenance_preserving_derivation_current_truth_proof",
    },
    "fail_close_justification_proof": {
        "order": 5,
        "contract_heading": "### 5. Fail-close-justification proof",
        "proof_role": "fail_close_justification_current_truth_proof",
    },
}
EXPECTED_COMMITMENT_PROOF_ALIGNMENT_ROWS = {
    "canonical_source_before_narration": {
        "order": 1,
        "proof_id": "canonical_source_proof",
        "alignment_role": "canonical_source_commitment_proof_alignment",
    },
    "governed_resolution_before_historical_familiarity": {
        "order": 2,
        "proof_id": "governed_resolution_proof",
        "alignment_role": "governed_resolution_commitment_proof_alignment",
    },
    "present_turn_authority_before_visible_recency": {
        "order": 3,
        "proof_id": "present_turn_authority_proof",
        "alignment_role": "present_turn_authority_commitment_proof_alignment",
    },
    "provenance_preserving_derivation_before_compressed_summary": {
        "order": 4,
        "proof_id": "provenance_preserving_derivation_proof",
        "alignment_role": "provenance_preserving_derivation_commitment_proof_alignment",
    },
    "fail_close_justification_before_operational_assertion": {
        "order": 5,
        "proof_id": "fail_close_justification_proof",
        "alignment_role": "fail_close_justification_commitment_proof_alignment",
    },
}
EXPECTED_EPISTEMIC_LIMIT_ROWS = {
    "canonical_source_not_resolution": {
        "order": 1,
        "contract_phrase": "canonical-source proof is not proof of governed resolution;",
    },
    "resolution_not_present_turn_authority": {
        "order": 2,
        "contract_phrase": "governed-resolution proof is not proof of present-turn authority;",
    },
    "authority_not_provenance_preserving_derivation": {
        "order": 3,
        "contract_phrase": "present-turn-authority proof is not proof of provenance-preserving derivation;",
    },
    "provenance_not_fail_close_justification": {
        "order": 4,
        "contract_phrase": "provenance-preserving-derivation proof is not proof of fail-close justification;",
    },
    "fail_close_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "fail-close-justification proof is not proof that the resulting claim may bypass current-turn machine adjudication.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "narration_as_current_truth": {
        "order": 1,
        "contract_phrase": "narrative recollection or self-claim is treated as if it were canonical present truth.",
    },
    "guesswork_as_authority": {
        "order": 2,
        "contract_phrase": "plausibility, intuition, or guesswork is treated as if it were admissible authority.",
    },
    "historical_accident_as_resolution": {
        "order": 3,
        "contract_phrase": "a path, state, or artifact is treated as authoritative merely because it happened to work in history.",
    },
    "implicit_habit_as_canonical_source": {
        "order": 4,
        "contract_phrase": "local habit or convenience memory is treated as if it resolved the canonical source.",
    },
    "compatibility_residue_as_truth": {
        "order": 5,
        "contract_phrase": "compatibility residue or leftover implementation drift is treated as if it justified present truth.",
    },
    "derived_projection_as_truth": {
        "order": 6,
        "contract_phrase": "a projection, inference, or compressed summary is treated as if it were the source truth itself.",
    },
    "epistemic_commitment_proof_flattening": {
        "order": 7,
        "contract_phrase": "canonical-source, governed-resolution, present-turn-authority, provenance-preserving-derivation, and fail-close commitments are treated as if one proof stratum were sufficient for all of them.",
    },
}
EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS = {
    "explicit_current_truth_epistemology_row_families": {
        "order": 1,
        "contract_phrase": "required commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_current_truth_epistemology_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_current_truth_epistemology_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_current_truth_epistemology_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize current-truth epistemology while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_current_truth_epistemology_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for current-truth epistemology law",
    "## Current-truth epistemology law",
    "## Five epistemic commitments",
    "## Required epistemic differentiations",
    "## Epistemic commitment-proof alignment",
    "## Epistemic-proof discipline",
    "## Epistemic-proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn epistemic legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Current-truth epistemology row-family completeness must stay explicit",
        "Required commitment, differentiation, epistemic-proof, commitment-proof-\nalignment, epistemic-limit, and collapse families must remain explicit as\nseparate machine-readable row families.",
        "The machine world must not finalize current-truth epistemology while required row identity drift remains known only internally.",
        "README root current-truth epistemology completeness discipline must therefore\nstay congruent with admitted current-truth-epistemology-completeness rows\nrather than becoming a freehand completeness summary.",
    ),
    "identity/protocol/README.md": (
        "## Root current-truth epistemology completeness discipline",
        "Current-truth epistemology law is not a soft prose bundle.",
        "These current-truth-epistemology-completeness rules must remain bound to canonical current-truth-epistemology-completeness rows rather than drifting into soft summary prose.",
        "1. required commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root current-truth epistemology completeness boundary",
        "1. Current-truth epistemology law must remain machine-readable as separate commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse row families.",
        "4. Protocol legality must not finalize current-truth epistemology while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root current-truth epistemology completeness discipline rendered at protocol root must remain congruent with admitted current-truth-epistemology-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime current-truth epistemology consumption boundary",
        "1. Runtime consumes current-truth epistemology law as separate commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse row families rather than as undifferentiated epistemic prose.",
        "4. Runtime must not finalize current-truth epistemology while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root current-truth epistemology completeness discipline as a governed completeness projection bound to admitted current-truth-epistemology-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root current-truth epistemology law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    epistemology_doc, epistemology_entry_path, epistemology_active_path, epistemology_alias_error = load_root_current_truth_epistemology(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    epistemology_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if epistemology_alias_error:
        stale_reasons.append(f"root_current_truth_epistemology_alias_error:{epistemology_alias_error}")
        error_code = ERR_REGISTRY
    elif not epistemology_doc:
        stale_reasons.append("root_current_truth_epistemology_empty_or_invalid")
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

    commitment_rows = commitment_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    differentiation_rows = differentiation_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    epistemic_proof_rows = epistemic_proof_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    commitment_proof_alignment_rows = commitment_proof_alignment_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    epistemic_limit_rows = epistemic_limit_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    collapse_rows = collapse_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    current_truth_epistemology_completeness_rows = (
        current_truth_epistemology_completeness_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    )
    current_truth_epistemology_completeness_surface = readme_current_truth_epistemology_completeness_surface(repo_root)
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(epistemology_doc) if epistemology_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "epistemology_family": "protocol_root_current_truth_epistemology",
            "epistemology_version": "v1",
            "contract_file": "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_current_truth_epistemology.py",
            "probe_script": "scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
            "common_script": "scripts/root_current_truth_epistemology_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(epistemology_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_current_truth_epistemology_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_commitment_rows", commitment_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_epistemic_proof_rows", epistemic_proof_rows),
            ("required_commitment_proof_alignment_rows", commitment_proof_alignment_rows),
            ("required_epistemic_limit_rows", epistemic_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_current_truth_epistemology_{field}_missing")
                error_code = ERR_REGISTRY
        if not current_truth_epistemology_completeness_rows:
            stale_reasons.append("root_current_truth_epistemology_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not epistemology_doc.get("contract_required_markers"):
            stale_reasons.append("root_current_truth_epistemology_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_current_truth_epistemology",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(epistemology_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_current_truth_epistemology_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_commitment_rows",
                    "member_id_key": "commitment_id",
                    "actual_rows": commitment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_ROWS,
                    "id_attr": "commitment_id",
                },
                {
                    "family_id": "required_differentiation_rows",
                    "member_id_key": "differentiation_id",
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_epistemic_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": epistemic_proof_rows,
                    "expected_rows": EXPECTED_EPISTEMIC_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_commitment_proof_alignment_rows",
                    "member_id_key": "commitment_id",
                    "actual_rows": commitment_proof_alignment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_PROOF_ALIGNMENT_ROWS,
                    "id_attr": "commitment_id",
                },
                {
                    "family_id": "required_epistemic_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": epistemic_limit_rows,
                    "expected_rows": EXPECTED_EPISTEMIC_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_collapse_rows",
                    "member_id_key": "collapse_id",
                    "actual_rows": collapse_rows,
                    "expected_rows": EXPECTED_COLLAPSE_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "current_truth_epistemology_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": current_truth_epistemology_completeness_rows,
                    "expected_rows": {
                        completeness_id: {} for completeness_id in EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "current_truth_epistemology_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": current_truth_epistemology_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS.values()
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

        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": commitment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_ROWS,
                    "field_name": "required_commitment_rows",
                    "id_attr": "commitment_id",
                    "compare_fields": ("contract_heading", "epistemic_role"),
                },
                {
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "field_name": "required_differentiation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": epistemic_proof_rows,
                    "expected_rows": EXPECTED_EPISTEMIC_PROOF_ROWS,
                    "field_name": "required_epistemic_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": commitment_proof_alignment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_PROOF_ALIGNMENT_ROWS,
                    "field_name": "required_commitment_proof_alignment_rows",
                    "id_attr": "commitment_id",
                    "compare_fields": ("proof_id", "alignment_role"),
                },
                {
                    "actual_rows": epistemic_limit_rows,
                    "expected_rows": EXPECTED_EPISTEMIC_LIMIT_ROWS,
                    "field_name": "required_epistemic_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": collapse_rows,
                    "expected_rows": EXPECTED_COLLAPSE_ROWS,
                    "field_name": "required_collapse_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": current_truth_epistemology_completeness_rows,
                    "expected_rows": EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS,
                    "field_name": "current_truth_epistemology_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_current_truth_epistemology_completeness_id",
                    "non_contiguous_reason": "current_truth_epistemology_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_current_truth_epistemology_completeness_rows",
                    "extra_reason": "extra_current_truth_epistemology_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "current_truth_epistemology_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": current_truth_epistemology_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "current_truth_epistemology_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_current_truth_epistemology_completeness_surface_phrase",
                    "non_contiguous_reason": "current_truth_epistemology_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_current_truth_epistemology_completeness_surface_rows",
                    "extra_reason": "extra_current_truth_epistemology_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "current_truth_epistemology_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            epistemology_violations=epistemology_violations,
        )

        expected_current_truth_epistemology_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS.values()
        ]
        actual_current_truth_epistemology_completeness_phrases = [
            row.contract_phrase for row in current_truth_epistemology_completeness_surface.rows
        ]
        expected_current_truth_epistemology_completeness_orders = [
            int(row["order"]) for row in EXPECTED_CURRENT_TRUTH_EPISTEMOLOGY_COMPLETENESS_ROWS.values()
        ]
        actual_current_truth_epistemology_completeness_orders = [
            row.order for row in current_truth_epistemology_completeness_surface.rows
        ]
        for reason in current_truth_epistemology_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "current_truth_epistemology_completeness_surface",
                    "reason": f"current_truth_epistemology_completeness_surface_{reason}",
                }
            )
        if actual_current_truth_epistemology_completeness_phrases and tuple(
            actual_current_truth_epistemology_completeness_phrases
        ) != tuple(expected_current_truth_epistemology_completeness_phrases):
            epistemology_violations.append(
                {
                    "field": "current_truth_epistemology_completeness_surface",
                    "reason": "current_truth_epistemology_completeness_surface_phrase_order_mismatch",
                    "expected": expected_current_truth_epistemology_completeness_phrases,
                    "actual": actual_current_truth_epistemology_completeness_phrases,
                }
            )
        if actual_current_truth_epistemology_completeness_orders and tuple(
            actual_current_truth_epistemology_completeness_orders
        ) != tuple(expected_current_truth_epistemology_completeness_orders):
            epistemology_violations.append(
                {
                    "field": "current_truth_epistemology_completeness_surface",
                    "reason": "current_truth_epistemology_completeness_surface_order_mismatch",
                    "expected": expected_current_truth_epistemology_completeness_orders,
                    "actual": actual_current_truth_epistemology_completeness_orders,
                }
            )

        contract_file = str(epistemology_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            epistemology_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(epistemology_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            commitment_rows,
                            reason="commitment_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            epistemic_proof_rows,
                            reason="proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            differentiation_rows + epistemic_limit_rows + collapse_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_phrase",),
                        ),
                    ),
                    payload_base={"field": "contract_file"},
                )
            )

        commitment_order_map = {row.commitment_id: row.order for row in commitment_rows}
        proof_order_map = {row.proof_id: row.order for row in epistemic_proof_rows}
        previous_commitment_order = 0
        previous_proof_order = 0
        for row in sorted(commitment_proof_alignment_rows, key=lambda item: item.order):
            commitment_order = commitment_order_map.get(row.commitment_id)
            if commitment_order is None:
                integration_violations.append(
                    {
                        "field": "root_current_truth_epistemology",
                        "reason": "commitment_proof_alignment_missing_commitment",
                        "commitment_id": row.commitment_id,
                    }
                )
            else:
                if commitment_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_current_truth_epistemology",
                            "reason": "commitment_proof_alignment_commitment_order_mismatch",
                            "commitment_id": row.commitment_id,
                            "alignment_order": row.order,
                            "commitment_order": commitment_order,
                        }
                    )
                if commitment_order <= previous_commitment_order:
                    integration_violations.append(
                        {
                            "field": "root_current_truth_epistemology",
                            "reason": "commitment_proof_alignment_commitment_order_not_increasing",
                            "commitment_id": row.commitment_id,
                            "commitment_order": commitment_order,
                            "previous_commitment_order": previous_commitment_order,
                        }
                    )
                previous_commitment_order = commitment_order

            proof_order = proof_order_map.get(row.proof_id)
            if proof_order is None:
                integration_violations.append(
                    {
                        "field": "root_current_truth_epistemology",
                        "reason": "commitment_proof_alignment_missing_epistemic_proof",
                        "commitment_id": row.commitment_id,
                        "proof_id": row.proof_id,
                    }
                )
            else:
                if proof_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_current_truth_epistemology",
                            "reason": "commitment_proof_alignment_proof_order_mismatch",
                            "commitment_id": row.commitment_id,
                            "proof_id": row.proof_id,
                            "alignment_order": row.order,
                            "proof_order": proof_order,
                        }
                    )
                if proof_order <= previous_proof_order:
                    integration_violations.append(
                        {
                            "field": "root_current_truth_epistemology",
                            "reason": "commitment_proof_alignment_proof_order_not_increasing",
                            "commitment_id": row.commitment_id,
                            "proof_id": row.proof_id,
                            "proof_order": proof_order,
                            "previous_proof_order": previous_proof_order,
                        }
                    )
                previous_proof_order = proof_order

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
                mappings_required_children=('root-current-truth-epistemology.current.yaml', 'root-current-truth-epistemology.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = epistemology_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_EPISTEMOLOGY,
        structure_reason_prefix="structural_violation",
        support_reason_prefix="current_truth_epistemology_violation",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_EPISTEMOLOGY),
        "epistemology_entry_path": str(epistemology_entry_path),
        "epistemology_active_path": str(epistemology_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(epistemology_doc.get("contract_file") or ""),
        "commitment_count": len(commitment_rows),
        "differentiation_count": len(differentiation_rows),
        "epistemic_proof_count": len(epistemic_proof_rows),
        "commitment_proof_alignment_count": len(commitment_proof_alignment_rows),
        "epistemic_limit_count": len(epistemic_limit_rows),
        "collapse_count": len(collapse_rows),
        "current_truth_epistemology_completeness_row_count": len(current_truth_epistemology_completeness_rows),
        **project_root_contract_support_projection(
            prefix="current_truth",
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
                    payload_key="current_truth_epistemology_completeness_row_coverage_status",
                    family_id="current_truth_epistemology_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="current_truth_epistemology_completeness_row_identity_projection_status",
                    family_id="current_truth_epistemology_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="current_truth_epistemology_completeness_surface_coverage_status",
                    family_id="current_truth_epistemology_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="current_truth_epistemology_completeness_surface_identity_projection_status",
                    family_id="current_truth_epistemology_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "commitment_ids": [row.commitment_id for row in sorted(commitment_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "epistemic_proof_ids": [row.proof_id for row in sorted(epistemic_proof_rows, key=lambda item: item.order)],
        "commitment_proof_alignment_ids": [
            row.commitment_id for row in sorted(commitment_proof_alignment_rows, key=lambda item: item.order)
        ],
        "epistemic_limit_ids": [row.row_id for row in sorted(epistemic_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "commitment_proof_alignment_rows": [
            {
                "order": row.order,
                "commitment_id": row.commitment_id,
                "proof_id": row.proof_id,
                "alignment_role": row.alignment_role,
            }
            for row in sorted(commitment_proof_alignment_rows, key=lambda item: item.order)
        ],
        "current_truth_epistemology_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(current_truth_epistemology_completeness_rows, key=lambda item: item.order)
        ],
        "current_truth_epistemology_completeness_surface": {
            "rel_path": current_truth_epistemology_completeness_surface.rel_path,
            "entry_count": len(current_truth_epistemology_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in current_truth_epistemology_completeness_surface.rows
            ],
            "extraction_violations": list(current_truth_epistemology_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "epistemology_violations": epistemology_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
