#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_expected_root_doc_anchor_stale_reasons,
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
)
from root_contract_marker_checks_common import (
    contract_required_markers_from_doc,
    contract_text_marker_checks_from_rows,
    evaluate_contract_text_marker_checks,
    merge_contract_text_marker_checks,
)
from root_contract_integration_checks_common import evaluate_root_contract_integration
from root_contract_integration_checks_common import append_membership_delta_violations
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
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_current_truth_epistemology_common import (
    epistemic_proof_rows_from_doc,
    load_root_current_truth_epistemology,
)
from root_decision_evidence_admissibility_common import (
    decision_evidence_proof_rows_from_doc,
    load_root_decision_evidence_admissibility,
)
from root_operator_answer_surface_common import (
    answer_surface_limit_rows_from_doc,
    answer_surface_stage_rows_from_doc,
    answer_claim_alignment_rows_from_doc,
    answer_claim_epistemic_alignment_rows_from_doc,
    answer_surface_proof_rows_from_doc,
    operator_answer_surface_completeness_rows_from_doc,
    readme_answer_surface_stage_surface,
    readme_operator_answer_surface_completeness_surface,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    boundary_rows_from_doc,
    collapse_rows_from_doc,
    load_root_operator_answer_surface,
    support_limit_rows_from_doc,
    support_memory_rows_from_doc,
    surface_rows_from_doc,
)

STATUS_KEY = "protocol_root_operator_answer_surface_status"
ERR_REGISTRY = "IP-ROAS-001"
ERR_STRUCTURE = "IP-ROAS-002"
ERR_ANSWER = "IP-ROAS-003"

EXPECTED_SURFACE_ROWS = {
    "operator_entry": {
        "order": 1,
        "contract_heading": "### 1. Operator entry surface",
        "surface_role": "natural_language_collaboration_entry",
    },
    "stable_instance_answer": {
        "order": 2,
        "contract_heading": "### 2. Stable instance answer surface",
        "surface_role": "law_compressed_operator_answer",
    },
    "supporting_machine_truth": {
        "order": 3,
        "contract_heading": "### 3. Supporting machine-truth surface",
        "surface_role": "supporting_machine_truth_surface",
    },
    "terminal_machine_enforcement": {
        "order": 4,
        "contract_heading": "### 4. Terminal machine-enforcement surface",
        "surface_role": "current_turn_legality_terminal",
    },
}
EXPECTED_ANSWER_SURFACE_STAGE_ROWS = {
    "operator entry surface": {
        "order": 1,
        "bound_surface_ids": ("operator_entry",),
        "required_markers": (
            "`natural_language_collaboration_entry`",
            "natural-language collaboration entry.",
        ),
    },
    "stable instance answer surface": {
        "order": 2,
        "bound_surface_ids": ("stable_instance_answer",),
        "required_markers": (
            "`law_compressed_operator_answer`",
            "law-compressed operator answer.",
        ),
    },
    "supporting machine-truth surface": {
        "order": 3,
        "bound_surface_ids": ("supporting_machine_truth",),
        "required_markers": (
            "`supporting_machine_truth_surface`",
            "supporting machine-truth surface that may back the answer without replacing it.",
        ),
    },
    "terminal machine-enforcement surface": {
        "order": 4,
        "bound_surface_ids": ("terminal_machine_enforcement",),
        "required_markers": (
            "`current_turn_legality_terminal`",
            "current-turn legality terminal that constrains the answer without becoming answer prose itself.",
        ),
    },
}
EXPECTED_SUPPORT_MEMORY_ROWS = {
    "law_memory_support": {
        "order": 1,
        "contract_heading": "### 1. Law-memory support",
        "support_role": "law_grounding_support",
    },
    "discovery_memory_support": {
        "order": 2,
        "contract_heading": "### 2. Discovery-memory support",
        "support_role": "discovery_grounding_support",
    },
    "admissibility_memory_support": {
        "order": 3,
        "contract_heading": "### 3. Admissibility-memory support",
        "support_role": "admissibility_grounding_support",
    },
    "run_binding_memory_support": {
        "order": 4,
        "contract_heading": "### 4. Run-binding-memory support",
        "support_role": "run_binding_grounding_support",
    },
    "consumption_memory_support": {
        "order": 5,
        "contract_heading": "### 5. Consumption-memory support",
        "support_role": "consumption_grounding_support",
    },
}
EXPECTED_SUPPORT_LIMIT_ROWS = {
    "law_memory_not_legality": {
        "order": 1,
        "contract_phrase": "law-memory support is not proof of current-turn legality;",
    },
    "discovery_memory_not_admissibility": {
        "order": 2,
        "contract_phrase": "discovery-memory support is not proof of admissibility;",
    },
    "admissibility_memory_not_run_binding": {
        "order": 3,
        "contract_phrase": "admissibility-memory support is not proof of run binding;",
    },
    "run_binding_memory_not_consumption": {
        "order": 4,
        "contract_phrase": "run-binding-memory support is not proof of next-hop consumption;",
    },
    "consumption_memory_realized_effect_only": {
        "order": 5,
        "contract_phrase": "only consumption-memory support may back claims of realized operational effect.",
    },
}
EXPECTED_ANSWER_CLAIM_ALIGNMENT_ROWS = {
    "law_grounded_answer_claim": {
        "order": 1,
        "support_id": "law_memory_support",
        "decision_evidence_proof_id": "frozen_law_decision_evidence_proof",
        "answer_claim_role": "law_grounded_operator_answer_claim",
    },
    "canonical_source_answer_claim": {
        "order": 2,
        "support_id": "discovery_memory_support",
        "decision_evidence_proof_id": "registry_resolution_decision_evidence_proof",
        "answer_claim_role": "canonical_source_operator_answer_claim",
    },
    "admissibility_answer_claim": {
        "order": 3,
        "support_id": "admissibility_memory_support",
        "decision_evidence_proof_id": "validator_verdict_decision_evidence_proof",
        "answer_claim_role": "admissibility_operator_answer_claim",
    },
    "live_bound_status_answer_claim": {
        "order": 4,
        "support_id": "run_binding_memory_support",
        "decision_evidence_proof_id": "bound_runtime_decision_evidence_proof",
        "answer_claim_role": "live_bound_status_operator_answer_claim",
    },
    "realized_effect_answer_claim": {
        "order": 5,
        "support_id": "consumption_memory_support",
        "decision_evidence_proof_id": "adjudicated_verdict_closure_decision_evidence_proof",
        "answer_claim_role": "realized_effect_operator_answer_claim",
    },
}
EXPECTED_ANSWER_CLAIM_EPISTEMIC_ALIGNMENT_ROWS = {
    "law_grounded_answer_claim": {
        "order": 1,
        "current_truth_proof_id": "canonical_source_proof",
        "claim_epistemic_role": "law_grounded_answer_claim_epistemic_alignment",
    },
    "canonical_source_answer_claim": {
        "order": 2,
        "current_truth_proof_id": "governed_resolution_proof",
        "claim_epistemic_role": "canonical_source_answer_claim_epistemic_alignment",
    },
    "admissibility_answer_claim": {
        "order": 3,
        "current_truth_proof_id": "fail_close_justification_proof",
        "claim_epistemic_role": "admissibility_answer_claim_epistemic_alignment",
    },
    "live_bound_status_answer_claim": {
        "order": 4,
        "current_truth_proof_id": "present_turn_authority_proof",
        "claim_epistemic_role": "live_bound_status_answer_claim_epistemic_alignment",
    },
    "realized_effect_answer_claim": {
        "order": 5,
        "current_truth_proof_id": "provenance_preserving_derivation_proof",
        "claim_epistemic_role": "realized_effect_answer_claim_epistemic_alignment",
    },
}
EXPECTED_ANSWER_SURFACE_PROOF_ROWS = {
    "operator_entry_boundary_proof": {
        "order": 1,
        "contract_heading": "### 1. Operator-entry boundary proof",
        "proof_role": "operator_entry_boundary_answer_surface_proof",
    },
    "law_preserving_compression_proof": {
        "order": 2,
        "contract_heading": "### 2. Law-preserving compression proof",
        "proof_role": "law_preserving_compression_answer_surface_proof",
    },
    "support_surface_confinement_proof": {
        "order": 3,
        "contract_heading": "### 3. Support-surface confinement proof",
        "proof_role": "support_surface_confinement_answer_surface_proof",
    },
    "legality_terminal_preservation_proof": {
        "order": 4,
        "contract_heading": "### 4. Legality-terminal preservation proof",
        "proof_role": "legality_terminal_preservation_answer_surface_proof",
    },
    "realized_effect_answer_backing_proof": {
        "order": 5,
        "contract_heading": "### 5. Realized-effect answer-backing proof",
        "proof_role": "realized_effect_answer_backing_proof",
    },
}
EXPECTED_ANSWER_SURFACE_LIMIT_ROWS = {
    "entry_boundary_not_law_preserving_compression": {
        "order": 1,
        "contract_phrase": "operator-entry boundary proof is not proof of law-preserving compression;",
    },
    "law_preserving_compression_not_support_confinement": {
        "order": 2,
        "contract_phrase": "law-preserving compression proof is not proof of support-surface confinement;",
    },
    "support_confinement_not_legality_terminal_preservation": {
        "order": 3,
        "contract_phrase": "support-surface confinement proof is not proof of legality-terminal preservation;",
    },
    "legality_terminal_not_realized_effect_backing": {
        "order": 4,
        "contract_phrase": "legality-terminal preservation proof is not proof of realized-effect answer backing;",
    },
    "realized_effect_backing_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "realized-effect answer-backing proof is not proof that answer prose may bypass current-turn machine adjudication.",
    },
    "realized_effect_backing_not_live_bound_status_backing": {
        "order": 6,
        "contract_phrase": "realized-effect answer-backing proof is not proof of live-bound status backing.",
    },
}
EXPECTED_BOUNDARY_ROWS = {
    "operator_memory_burden": {
        "order": 1,
        "contract_phrase": "the operator should not bear the memory burden of low-level protocol law;",
    },
    "support_not_answer": {
        "order": 2,
        "contract_phrase": "lower-layer proof may support the answer without replacing the answer surface itself;",
    },
    "compression_without_bypass": {
        "order": 3,
        "contract_phrase": "operator simplicity must be achieved by law-preserving compression rather than by bypassing machine-law boundaries;",
    },
    "terminality_not_answer_prose": {
        "order": 4,
        "contract_phrase": "current-turn legality must still terminate in machine-consumed enforcement surfaces rather than in answer prose alone.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "support_proof_equals_answer": {
        "order": 1,
        "contract_phrase": "supporting proof is treated as the operator answer itself.",
    },
    "raw_internal_artifact_dumping": {
        "order": 2,
        "contract_phrase": "internal artifacts or raw protocol burden are dumped directly onto the operator as if dumping were an answer surface.",
    },
    "convenience_overrides_law_compression": {
        "order": 3,
        "contract_phrase": "operator comfort or local convenience is used to bypass law-preserving compression and enforcement boundaries.",
    },
    "answer_surface_seized_by_terminality": {
        "order": 4,
        "contract_phrase": "a machine terminal or receipt blob is treated as if it were the operator collaboration surface.",
    },
    "prose_without_machine_truth": {
        "order": 5,
        "contract_phrase": "fluent answer prose is treated as sufficient despite missing machine-truth backing when such backing is required.",
    },
    "realized_effect_claim_backed_by_earlier_strata": {
        "order": 6,
        "contract_phrase": "a realized-effect answer claim is treated as sufficiently backed by law-memory, discovery-memory, admissibility-memory, or run-binding-memory support alone.",
    },
    "answer_claim_epistemic_flattening": {
        "order": 7,
        "contract_phrase": "law-grounded, canonical-source, admissibility, live-bound, and realized-effect answer claims are treated as if one current-truth proof stratum were sufficient for all of them.",
    },
}
EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS = {
    "explicit_operator_answer_surface_row_families": {
        "order": 1,
        "contract_phrase": "required surface, answer-surface-stage, answer-surface-stage-surface, support-memory, support-limit, answer-claim-alignment, answer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit, boundary, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_operator_answer_surface_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_operator_answer_surface_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_operator_answer_surface_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize operator answer-surface legality while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_operator_answer_surface_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for operator answer-surface law",
    "## Operator answer-surface law",
    "## Four answer-surface strata",
    "## Lifecycle-aware support-memory discipline",
    "## Support-memory limits",
    "## Answer-claim backing alignment",
    "## Answer-claim epistemic alignment",
    "## Answer-surface proof discipline",
    "## Answer-surface proof limits",
    "## Compression boundary",
    "## Non-compliant answer-surface collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Operator answer-surface row-family completeness must stay explicit",
        "Required surface, support-memory, support-limit, answer-claim-alignment,\nanswer-surface-stage, answer-surface-stage-surface,\nanswer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit,\nboundary, and collapse families must remain explicit as separate\nmachine-readable row families.",
        "README root operator answer-surface discipline must therefore stay congruent with admitted answer-surface-stage rows rather than becoming a freehand delivery ladder.",
        "README root operator answer-surface completeness discipline must therefore stay\ncongruent with admitted operator-answer-surface-completeness rows rather than\nbecoming a freehand completeness summary.",
        "The machine world must not finalize operator answer-surface legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root operator answer-surface discipline",
        "This root operator answer-surface discipline must remain bound to canonical answer-surface-stage rows rather than becoming a freehand delivery ladder.",
        "`natural_language_collaboration_entry`",
        "`current_turn_legality_terminal`",
        "## Root operator answer-surface completeness discipline",
        "Operator answer-surface law is not a soft prose bundle.",
        "These operator-answer-surface-completeness rules must remain bound to canonical operator-answer-surface-completeness rows rather than drifting into soft summary prose.",
        "1. required surface, answer-surface-stage, answer-surface-stage-surface, support-memory, support-limit, answer-claim-alignment, answer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit, boundary, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root operator answer-surface completeness boundary",
        "1. Operator answer-surface law must remain machine-readable as separate surface, answer-surface-stage, answer-surface-stage-surface, support-memory, support-limit, answer-claim-alignment, answer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit, boundary, and collapse row families.",
        "4. Protocol legality must not finalize operator answer-surface legality while missing or unexpected row identities remain known only inside validator logic.",
        "README root operator answer-surface discipline rendered at protocol root must remain congruent with admitted answer-surface-stage rows rather than silently authoring an alternate delivery ladder.",
        "7. README root operator answer-surface completeness discipline rendered at protocol root must remain congruent with admitted operator-answer-surface-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime operator answer-surface consumption boundary",
        "1. Runtime consumes operator answer-surface law as separate surface, answer-surface-stage, answer-surface-stage-surface, support-memory, support-limit, answer-claim-alignment, answer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit, boundary, and collapse row families rather than as undifferentiated answer prose.",
        "4. Runtime must not finalize operator answer-surface legality while missing or unexpected row identities remain known only inside validator machinery.",
        "Runtime consumes README root operator answer-surface discipline as a governed stage projection bound to admitted answer-surface-stage rows rather than as a freehand delivery ladder.",
        "7. Runtime consumes README root operator answer-surface completeness discipline as a governed completeness projection bound to admitted operator-answer-surface-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root operator answer-surface law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    answer_doc, answer_entry_path, answer_active_path, answer_alias_error = load_root_operator_answer_surface(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)
    current_truth_doc, current_truth_entry_path, current_truth_active_path, current_truth_alias_error = (
        load_root_current_truth_epistemology(repo_root)
    )
    decision_evidence_doc, decision_evidence_entry_path, decision_evidence_active_path, decision_evidence_alias_error = (
        load_root_decision_evidence_admissibility(repo_root)
    )

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    answer_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if answer_alias_error:
        stale_reasons.append(f"root_operator_answer_surface_alias_error:{answer_alias_error}")
        error_code = ERR_REGISTRY
    elif not answer_doc:
        stale_reasons.append("root_operator_answer_surface_empty_or_invalid")
        error_code = ERR_REGISTRY

    for label, doc, alias_error in (
        ("root_corpus_registry", registry_doc, registry_alias_error),
        ("root_corpus_ordering", ordering_doc, ordering_alias_error),
        ("root_corpus_authority", authority_doc, authority_alias_error),
        ("root_corpus_question_routing", routing_doc, routing_alias_error),
        ("root_current_truth_epistemology", current_truth_doc, current_truth_alias_error),
        ("root_decision_evidence_admissibility", decision_evidence_doc, decision_evidence_alias_error),
    ):
        if alias_error:
            stale_reasons.append(f"{label}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(f"{label}_empty_or_invalid")
            error_code = ERR_REGISTRY

    surface_rows = surface_rows_from_doc(answer_doc) if answer_doc else ()
    answer_surface_stage_rows = answer_surface_stage_rows_from_doc(answer_doc) if answer_doc else ()
    support_memory_rows = support_memory_rows_from_doc(answer_doc) if answer_doc else ()
    support_limit_rows = support_limit_rows_from_doc(answer_doc) if answer_doc else ()
    answer_claim_alignment_rows = answer_claim_alignment_rows_from_doc(answer_doc) if answer_doc else ()
    answer_claim_epistemic_alignment_rows = answer_claim_epistemic_alignment_rows_from_doc(answer_doc) if answer_doc else ()
    answer_surface_proof_rows = answer_surface_proof_rows_from_doc(answer_doc) if answer_doc else ()
    answer_surface_limit_rows = answer_surface_limit_rows_from_doc(answer_doc) if answer_doc else ()
    boundary_rows = boundary_rows_from_doc(answer_doc) if answer_doc else ()
    collapse_rows = collapse_rows_from_doc(answer_doc) if answer_doc else ()
    operator_answer_surface_completeness_rows = (
        operator_answer_surface_completeness_rows_from_doc(answer_doc) if answer_doc else ()
    )
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(answer_doc) if answer_doc else ()
    current_truth_epistemic_proof_rows = epistemic_proof_rows_from_doc(current_truth_doc) if current_truth_doc else ()
    decision_evidence_proof_rows = decision_evidence_proof_rows_from_doc(decision_evidence_doc) if decision_evidence_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    answer_surface_stage_surface = readme_answer_surface_stage_surface(repo_root)
    operator_answer_surface_completeness_surface = readme_operator_answer_surface_completeness_surface(repo_root)

    if not stale_reasons:
        expected_scalar_fields = {
            "answer_surface_family": "protocol_root_operator_answer_surface",
            "answer_surface_version": "v1",
            "contract_file": "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_operator_answer_surface.py",
            "probe_script": "scripts/ci/run_protocol_root_operator_answer_surface_probes_ci.sh",
            "common_script": "scripts/root_operator_answer_surface_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
            "current_truth_current_file": "identity/protocol/mappings/root-current-truth-epistemology.current.yaml",
            "decision_evidence_current_file": "identity/protocol/mappings/root-decision-evidence-admissibility.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(answer_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_operator_answer_surface_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_surface_rows", surface_rows),
            ("answer_surface_stage_rows", answer_surface_stage_rows),
            ("required_support_memory_rows", support_memory_rows),
            ("required_support_limit_rows", support_limit_rows),
            ("required_answer_claim_alignment_rows", answer_claim_alignment_rows),
            ("required_answer_claim_epistemic_alignment_rows", answer_claim_epistemic_alignment_rows),
            ("required_answer_surface_proof_rows", answer_surface_proof_rows),
            ("required_answer_surface_limit_rows", answer_surface_limit_rows),
            ("required_boundary_rows", boundary_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_operator_answer_surface_{field}_missing")
                error_code = ERR_REGISTRY
        if not operator_answer_surface_completeness_rows:
            stale_reasons.append("root_operator_answer_surface_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not current_truth_epistemic_proof_rows:
            stale_reasons.append("root_operator_answer_surface_dependency_current_truth_epistemic_proof_rows_missing")
            error_code = ERR_REGISTRY
        if not decision_evidence_proof_rows:
            stale_reasons.append("root_operator_answer_surface_dependency_decision_evidence_proof_rows_missing")
            error_code = ERR_REGISTRY
        if not answer_doc.get("contract_required_markers"):
            stale_reasons.append("root_operator_answer_surface_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_operator_answer_surface",
        ):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(answer_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_operator_answer_surface_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_surface_rows",
                    "member_id_key": "surface_id",
                    "actual_rows": surface_rows,
                    "expected_rows": EXPECTED_SURFACE_ROWS,
                    "id_attr": "surface_id",
                },
                {
                    "family_id": "answer_surface_stage_rows",
                    "member_id_key": "stage_label",
                    "actual_rows": answer_surface_stage_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_STAGE_ROWS,
                    "id_attr": "stage_label",
                },
                {
                    "family_id": "answer_surface_stage_surface",
                    "member_id_key": "stage_label",
                    "actual_rows": answer_surface_stage_surface.rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_STAGE_ROWS,
                    "id_attr": "stage_label",
                },
                {
                    "family_id": "required_support_memory_rows",
                    "member_id_key": "support_id",
                    "actual_rows": support_memory_rows,
                    "expected_rows": EXPECTED_SUPPORT_MEMORY_ROWS,
                    "id_attr": "support_id",
                },
                {
                    "family_id": "required_support_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": support_limit_rows,
                    "expected_rows": EXPECTED_SUPPORT_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_answer_claim_alignment_rows",
                    "member_id_key": "claim_id",
                    "actual_rows": answer_claim_alignment_rows,
                    "expected_rows": EXPECTED_ANSWER_CLAIM_ALIGNMENT_ROWS,
                    "id_attr": "claim_id",
                },
                {
                    "family_id": "required_answer_claim_epistemic_alignment_rows",
                    "member_id_key": "claim_id",
                    "actual_rows": answer_claim_epistemic_alignment_rows,
                    "expected_rows": EXPECTED_ANSWER_CLAIM_EPISTEMIC_ALIGNMENT_ROWS,
                    "id_attr": "claim_id",
                },
                {
                    "family_id": "required_answer_surface_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": answer_surface_proof_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_answer_surface_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": answer_surface_limit_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_boundary_rows",
                    "member_id_key": "boundary_id",
                    "actual_rows": boundary_rows,
                    "expected_rows": EXPECTED_BOUNDARY_ROWS,
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
                    "family_id": "operator_answer_surface_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": operator_answer_surface_completeness_rows,
                    "expected_rows": {
                        completeness_id: {}
                        for completeness_id in EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "operator_answer_surface_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": operator_answer_surface_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS.values()
                    },
                    "id_attr": "contract_phrase",
                },
            ),
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        )

        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": surface_rows,
                    "expected_rows": EXPECTED_SURFACE_ROWS,
                    "field_name": "required_surface_rows",
                    "id_attr": "surface_id",
                    "compare_fields": ("contract_heading", "surface_role"),
                },
                {
                    "actual_rows": answer_surface_stage_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_STAGE_ROWS,
                    "field_name": "answer_surface_stage_rows",
                    "id_attr": "stage_label",
                    "compare_fields": ("bound_surface_ids", "required_markers"),
                },
                {
                    "actual_rows": support_memory_rows,
                    "expected_rows": EXPECTED_SUPPORT_MEMORY_ROWS,
                    "field_name": "required_support_memory_rows",
                    "id_attr": "support_id",
                    "compare_fields": ("contract_heading", "support_role"),
                },
                {
                    "actual_rows": support_limit_rows,
                    "expected_rows": EXPECTED_SUPPORT_LIMIT_ROWS,
                    "field_name": "required_support_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": answer_claim_alignment_rows,
                    "expected_rows": EXPECTED_ANSWER_CLAIM_ALIGNMENT_ROWS,
                    "field_name": "required_answer_claim_alignment_rows",
                    "id_attr": "claim_id",
                    "compare_fields": ("support_id", "decision_evidence_proof_id", "answer_claim_role"),
                },
                {
                    "actual_rows": answer_claim_epistemic_alignment_rows,
                    "expected_rows": EXPECTED_ANSWER_CLAIM_EPISTEMIC_ALIGNMENT_ROWS,
                    "field_name": "required_answer_claim_epistemic_alignment_rows",
                    "id_attr": "claim_id",
                    "compare_fields": ("current_truth_proof_id", "claim_epistemic_role"),
                },
                {
                    "actual_rows": answer_surface_proof_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_PROOF_ROWS,
                    "field_name": "required_answer_surface_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": answer_surface_limit_rows,
                    "expected_rows": EXPECTED_ANSWER_SURFACE_LIMIT_ROWS,
                    "field_name": "required_answer_surface_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": boundary_rows,
                    "expected_rows": EXPECTED_BOUNDARY_ROWS,
                    "field_name": "required_boundary_rows",
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
                    "actual_rows": operator_answer_surface_completeness_rows,
                    "expected_rows": EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS,
                    "field_name": "operator_answer_surface_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_operator_answer_surface_completeness_id",
                    "non_contiguous_reason": "operator_answer_surface_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_operator_answer_surface_completeness_rows",
                    "extra_reason": "extra_operator_answer_surface_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "operator_answer_surface_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": operator_answer_surface_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "operator_answer_surface_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_operator_answer_surface_completeness_surface_phrase",
                    "non_contiguous_reason": "operator_answer_surface_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_operator_answer_surface_completeness_surface_rows",
                    "extra_reason": "extra_operator_answer_surface_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "operator_answer_surface_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            answer_violations=answer_violations,
        )

        surface_row_map = {row.surface_id: row for row in surface_rows}
        answer_surface_stage_map = {row.stage_label: row for row in answer_surface_stage_rows}
        answer_surface_stage_surface_map = {row.stage_label: row for row in answer_surface_stage_surface.rows}

        append_membership_delta_violations(
            structure_violations,
            field_name="answer_surface_stage_rows",
            expected_ids=EXPECTED_ANSWER_SURFACE_STAGE_ROWS,
            actual_ids=answer_surface_stage_map,
            payload_key="stage_labels",
            missing_reason="missing_answer_surface_stage_rows",
            extra_reason="extra_answer_surface_stage_rows",
            duplicate_reason="duplicate_answer_surface_stage_row",
            actual_total_count=len(answer_surface_stage_rows),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="answer_surface_stage_surface",
            expected_ids=EXPECTED_ANSWER_SURFACE_STAGE_ROWS,
            actual_ids=answer_surface_stage_surface_map,
            payload_key="stage_labels",
            missing_reason="missing_answer_surface_stage_surface_rows",
            extra_reason="extra_answer_surface_stage_surface_rows",
            duplicate_reason="duplicate_answer_surface_stage_surface_row",
            actual_total_count=len(answer_surface_stage_surface.rows),
        )

        stage_orders = [row.order for row in answer_surface_stage_rows]
        stage_labels = [row.stage_label for row in answer_surface_stage_rows]
        stage_surface_orders = [row.order for row in answer_surface_stage_surface.rows]
        stage_surface_labels = [row.stage_label for row in answer_surface_stage_surface.rows]
        expected_stage_labels = list(EXPECTED_ANSWER_SURFACE_STAGE_ROWS.keys())
        expected_stage_orders = [
            int(stage["order"]) for stage in EXPECTED_ANSWER_SURFACE_STAGE_ROWS.values()
        ]
        if len(set(stage_orders)) != len(stage_orders) or sorted(stage_orders) != list(range(1, len(stage_orders) + 1)):
            structure_violations.append({"field": "answer_surface_stage_rows", "reason": "stage_order_non_contiguous"})
        if len(set(stage_labels)) != len(stage_labels):
            structure_violations.append({"field": "answer_surface_stage_rows", "reason": "duplicate_stage_label"})
        if stage_surface_orders and (
            len(set(stage_surface_orders)) != len(stage_surface_orders)
            or sorted(stage_surface_orders) != list(range(1, len(stage_surface_orders) + 1))
        ):
            structure_violations.append(
                {"field": "answer_surface_stage_surface", "reason": "stage_order_non_contiguous"}
            )
        if stage_surface_labels and tuple(stage_surface_labels) != tuple(expected_stage_labels):
            answer_violations.append(
                {
                    "field": "answer_surface_stage_surface",
                    "reason": "answer_surface_stage_surface_order_mismatch",
                    "expected": expected_stage_labels,
                    "actual": stage_surface_labels,
                }
            )
        if stage_surface_orders and tuple(stage_surface_orders) != tuple(expected_stage_orders):
            answer_violations.append(
                {
                    "field": "answer_surface_stage_surface",
                    "reason": "answer_surface_stage_surface_stage_order_mismatch",
                    "expected": expected_stage_orders,
                    "actual": stage_surface_orders,
                }
            )

        for stage_label, expected in EXPECTED_ANSWER_SURFACE_STAGE_ROWS.items():
            stage_row = answer_surface_stage_map.get(stage_label)
            if stage_row is None:
                continue
            if stage_row.order != int(expected["order"]):
                answer_violations.append(
                    {
                        "field": "answer_surface_stage_rows",
                        "reason": "stage_order_mismatch",
                        "stage_label": stage_label,
                        "expected": int(expected["order"]),
                        "actual": stage_row.order,
                    }
                )
            if tuple(stage_row.bound_surface_ids) != tuple(expected["bound_surface_ids"]):
                answer_violations.append(
                    {
                        "field": "answer_surface_stage_rows",
                        "reason": "bound_surface_ids_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["bound_surface_ids"]),
                        "actual": list(stage_row.bound_surface_ids),
                    }
                )
            if tuple(stage_row.required_markers) != tuple(expected["required_markers"]):
                answer_violations.append(
                    {
                        "field": "answer_surface_stage_rows",
                        "reason": "required_markers_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["required_markers"]),
                        "actual": list(stage_row.required_markers),
                    }
                )
            derived_surface_orders = sorted(
                surface_row_map[surface_id].order
                for surface_id in stage_row.bound_surface_ids
                if surface_id in surface_row_map
            )
            missing_surface_ids = sorted(
                surface_id for surface_id in stage_row.bound_surface_ids if surface_id not in surface_row_map
            )
            if missing_surface_ids:
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "answer_surface_stage_missing_surface_rows",
                        "stage_label": stage_label,
                        "surface_ids": missing_surface_ids,
                    }
                )
            if derived_surface_orders and derived_surface_orders != [stage_row.order]:
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "answer_surface_stage_order_not_aligned_with_surface_rows",
                        "stage_label": stage_label,
                        "stage_order": stage_row.order,
                        "surface_orders": derived_surface_orders,
                    }
                )

        for reason in answer_surface_stage_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "answer_surface_stage_surface",
                    "reason": f"answer_surface_stage_surface_{reason}",
                }
            )
        for stage_label, expected in EXPECTED_ANSWER_SURFACE_STAGE_ROWS.items():
            surface_row = answer_surface_stage_surface_map.get(stage_label)
            if surface_row is None:
                continue
            surface_text = "\n".join(surface_row.body_lines)
            for marker in expected["required_markers"]:
                if marker not in surface_text:
                    answer_violations.append(
                        {
                            "field": "answer_surface_stage_surface",
                            "reason": "required_marker_missing",
                            "stage_label": stage_label,
                            "marker": marker,
                        }
                    )

        expected_operator_answer_surface_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS.values()
        ]
        actual_operator_answer_surface_completeness_phrases = [
            row.contract_phrase for row in operator_answer_surface_completeness_surface.rows
        ]
        expected_operator_answer_surface_completeness_orders = [
            int(row["order"]) for row in EXPECTED_OPERATOR_ANSWER_SURFACE_COMPLETENESS_ROWS.values()
        ]
        actual_operator_answer_surface_completeness_orders = [
            row.order for row in operator_answer_surface_completeness_surface.rows
        ]
        for reason in operator_answer_surface_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "operator_answer_surface_completeness_surface",
                    "reason": f"operator_answer_surface_completeness_surface_{reason}",
                }
            )
        if actual_operator_answer_surface_completeness_phrases and tuple(
            actual_operator_answer_surface_completeness_phrases
        ) != tuple(expected_operator_answer_surface_completeness_phrases):
            answer_violations.append(
                {
                    "field": "operator_answer_surface_completeness_surface",
                    "reason": "operator_answer_surface_completeness_surface_phrase_order_mismatch",
                    "expected": expected_operator_answer_surface_completeness_phrases,
                    "actual": actual_operator_answer_surface_completeness_phrases,
                }
            )
        if actual_operator_answer_surface_completeness_orders and tuple(
            actual_operator_answer_surface_completeness_orders
        ) != tuple(expected_operator_answer_surface_completeness_orders):
            answer_violations.append(
                {
                    "field": "operator_answer_surface_completeness_surface",
                    "reason": "operator_answer_surface_completeness_surface_order_mismatch",
                    "expected": expected_operator_answer_surface_completeness_orders,
                    "actual": actual_operator_answer_surface_completeness_orders,
                }
            )

        contract_file = str(answer_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            answer_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(answer_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            surface_rows,
                            reason="surface_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            support_memory_rows,
                            reason="support_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            answer_surface_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            support_limit_rows + answer_surface_limit_rows + boundary_rows + collapse_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_phrase",),
                        ),
                    ),
                    payload_base={"field": "contract_file"},
                )
            )

        root_doc_anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                root_doc_anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

        support_memory_order_map = {row.support_id: row.order for row in support_memory_rows}
        answer_claim_alignment_map = {row.claim_id: row for row in answer_claim_alignment_rows}
        current_truth_epistemic_proof_order_map = {row.proof_id: row.order for row in current_truth_epistemic_proof_rows}
        decision_evidence_proof_order_map = {row.proof_id: row.order for row in decision_evidence_proof_rows}
        previous_support_order = 0
        previous_decision_evidence_proof_order = 0
        for row in sorted(answer_claim_alignment_rows, key=lambda item: item.order):
            support_order = support_memory_order_map.get(row.support_id)
            if support_order is None:
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "answer_claim_alignment_missing_support_memory",
                        "claim_id": row.claim_id,
                        "support_id": row.support_id,
                    }
                )
            else:
                if support_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_operator_answer_surface",
                            "reason": "answer_claim_alignment_support_order_mismatch",
                            "claim_id": row.claim_id,
                            "support_id": row.support_id,
                            "claim_order": row.order,
                            "support_order": support_order,
                        }
                    )
                if support_order <= previous_support_order:
                    integration_violations.append(
                        {
                            "field": "root_operator_answer_surface",
                            "reason": "answer_claim_alignment_support_order_not_increasing",
                            "claim_id": row.claim_id,
                            "support_id": row.support_id,
                            "support_order": support_order,
                            "previous_support_order": previous_support_order,
                        }
                    )
                previous_support_order = support_order

            decision_evidence_proof_order = decision_evidence_proof_order_map.get(row.decision_evidence_proof_id)
            if decision_evidence_proof_order is None:
                integration_violations.append(
                    {
                        "field": "root_decision_evidence_admissibility",
                        "reason": "answer_claim_alignment_missing_decision_evidence_proof",
                        "claim_id": row.claim_id,
                        "decision_evidence_proof_id": row.decision_evidence_proof_id,
                    }
                )
            else:
                if decision_evidence_proof_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_decision_evidence_admissibility",
                            "reason": "answer_claim_alignment_decision_evidence_proof_order_mismatch",
                            "claim_id": row.claim_id,
                            "decision_evidence_proof_id": row.decision_evidence_proof_id,
                            "claim_order": row.order,
                            "decision_evidence_proof_order": decision_evidence_proof_order,
                        }
                    )
                if decision_evidence_proof_order <= previous_decision_evidence_proof_order:
                    integration_violations.append(
                        {
                            "field": "root_decision_evidence_admissibility",
                            "reason": "answer_claim_alignment_decision_evidence_proof_order_not_increasing",
                            "claim_id": row.claim_id,
                            "decision_evidence_proof_id": row.decision_evidence_proof_id,
                            "decision_evidence_proof_order": decision_evidence_proof_order,
                            "previous_decision_evidence_proof_order": previous_decision_evidence_proof_order,
                        }
                    )
                previous_decision_evidence_proof_order = decision_evidence_proof_order

            if (
                row.claim_id == "realized_effect_answer_claim"
                and row.decision_evidence_proof_id != "adjudicated_verdict_closure_decision_evidence_proof"
            ):
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "realized_effect_claim_not_closure_backed",
                        "claim_id": row.claim_id,
                        "decision_evidence_proof_id": row.decision_evidence_proof_id,
                    }
                )

        for row in sorted(answer_claim_epistemic_alignment_rows, key=lambda item: item.order):
            backing_row = answer_claim_alignment_map.get(row.claim_id)
            if backing_row is None:
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "answer_claim_epistemic_alignment_missing_backing_alignment",
                        "claim_id": row.claim_id,
                    }
                )
            elif backing_row.order != row.order:
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "answer_claim_epistemic_alignment_order_mismatch",
                        "claim_id": row.claim_id,
                        "backing_order": backing_row.order,
                        "epistemic_order": row.order,
                    }
                )

            current_truth_proof_order = current_truth_epistemic_proof_order_map.get(row.current_truth_proof_id)
            if current_truth_proof_order is None:
                integration_violations.append(
                    {
                        "field": "root_current_truth_epistemology",
                        "reason": "answer_claim_epistemic_alignment_missing_current_truth_proof",
                        "claim_id": row.claim_id,
                        "current_truth_proof_id": row.current_truth_proof_id,
                    }
                )

            if row.claim_id == "realized_effect_answer_claim" and row.current_truth_proof_id != "provenance_preserving_derivation_proof":
                integration_violations.append(
                    {
                        "field": "root_operator_answer_surface",
                        "reason": "realized_effect_claim_not_provenance_grounded",
                        "claim_id": row.claim_id,
                        "current_truth_proof_id": row.current_truth_proof_id,
                    }
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
                mappings_required_children=('root-operator-answer-surface.current.yaml', 'root-operator-answer-surface.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = answer_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_ANSWER,
        support_reason_prefix="answer_surface_violation",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ANSWER),
        "answer_entry_path": str(answer_entry_path),
        "answer_active_path": str(answer_active_path),
        "current_truth_entry_path": str(current_truth_entry_path),
        "current_truth_active_path": str(current_truth_active_path),
        "decision_evidence_entry_path": str(decision_evidence_entry_path),
        "decision_evidence_active_path": str(decision_evidence_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(answer_doc.get("contract_file") or ""),
        "surface_count": len(surface_rows),
        "answer_surface_stage_count": len(answer_surface_stage_rows),
        "support_memory_count": len(support_memory_rows),
        "support_limit_count": len(support_limit_rows),
        "answer_claim_alignment_count": len(answer_claim_alignment_rows),
        "answer_claim_epistemic_alignment_count": len(answer_claim_epistemic_alignment_rows),
        "answer_surface_proof_count": len(answer_surface_proof_rows),
        "answer_surface_limit_count": len(answer_surface_limit_rows),
        "boundary_count": len(boundary_rows),
        "collapse_count": len(collapse_rows),
        "operator_answer_surface_completeness_row_count": len(operator_answer_surface_completeness_rows),
        **project_root_contract_support_projection(
            prefix="operator_answer",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "surface_ids": [row.surface_id for row in sorted(surface_rows, key=lambda item: item.order)],
        "answer_surface_stage_labels": [row.stage_label for row in sorted(answer_surface_stage_rows, key=lambda item: item.order)],
        "support_memory_ids": [row.support_id for row in sorted(support_memory_rows, key=lambda item: item.order)],
        "support_limit_ids": [row.row_id for row in sorted(support_limit_rows, key=lambda item: item.order)],
        "answer_claim_alignment_ids": [row.claim_id for row in sorted(answer_claim_alignment_rows, key=lambda item: item.order)],
        "answer_claim_epistemic_alignment_ids": [
            row.claim_id for row in sorted(answer_claim_epistemic_alignment_rows, key=lambda item: item.order)
        ],
        "answer_surface_proof_ids": [row.proof_id for row in sorted(answer_surface_proof_rows, key=lambda item: item.order)],
        "answer_surface_limit_ids": [row.row_id for row in sorted(answer_surface_limit_rows, key=lambda item: item.order)],
        "boundary_ids": [row.row_id for row in sorted(boundary_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "operator_answer_surface_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(operator_answer_surface_completeness_rows, key=lambda item: item.order)
        ],
        "answer_claim_alignment_rows": [
            {
                "order": row.order,
                "claim_id": row.claim_id,
                "support_id": row.support_id,
                "decision_evidence_proof_id": row.decision_evidence_proof_id,
                "answer_claim_role": row.answer_claim_role,
            }
            for row in sorted(answer_claim_alignment_rows, key=lambda item: item.order)
        ],
        "answer_surface_stage_rows": [
            {
                "order": row.order,
                "stage_label": row.stage_label,
                "bound_surface_ids": list(row.bound_surface_ids),
                "required_markers": list(row.required_markers),
            }
            for row in sorted(answer_surface_stage_rows, key=lambda item: item.order)
        ],
        "answer_surface_stage_surface": {
            "rel_path": answer_surface_stage_surface.rel_path,
            "entry_count": len(answer_surface_stage_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "stage_label": row.stage_label,
                    "body_lines": list(row.body_lines),
                }
                for row in answer_surface_stage_surface.rows
            ],
            "extraction_violations": list(answer_surface_stage_surface.extraction_violations),
        },
        "operator_answer_surface_completeness_surface": {
            "rel_path": operator_answer_surface_completeness_surface.rel_path,
            "entry_count": len(operator_answer_surface_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in operator_answer_surface_completeness_surface.rows
            ],
            "extraction_violations": list(operator_answer_surface_completeness_surface.extraction_violations),
        },
        "answer_claim_epistemic_alignment_rows": [
            {
                "order": row.order,
                "claim_id": row.claim_id,
                "current_truth_proof_id": row.current_truth_proof_id,
                "claim_epistemic_role": row.claim_epistemic_role,
            }
            for row in sorted(answer_claim_epistemic_alignment_rows, key=lambda item: item.order)
        ],
        "structure_violations": structure_violations,
        "answer_violations": answer_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
