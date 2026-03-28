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
from root_corpus_ordering_common import (
    adjudication_surface_profiles_from_doc,
    load_root_corpus_ordering,
    reading_order_rows_from_doc,
)
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_decision_evidence_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    adjudication_phase_alignment_rows_from_doc,
    collapse_rows_from_doc,
    decision_evidence_limit_rows_from_doc,
    decision_evidence_proof_rows_from_doc,
    differentiation_rows_from_doc,
    evidence_class_proof_alignment_rows_from_doc,
    evidence_class_rows_from_doc,
    evaluate_ordering_adjudication_phase_alignment,
    load_root_decision_evidence_admissibility,
)

STATUS_KEY = "protocol_root_decision_evidence_admissibility_status"
ERR_REGISTRY = "IP-DEA-001"
ERR_STRUCTURE = "IP-DEA-002"
ERR_ADMISSIBILITY = "IP-DEA-003"

EXPECTED_EVIDENCE_CLASS_ROWS = {
    "frozen_law_evidence": {
        "order": 1,
        "contract_heading": "### 1. Frozen-law evidence",
        "evidence_role": "frozen_law_evidence",
    },
    "machine_registry_evidence": {
        "order": 2,
        "contract_heading": "### 2. Machine-registry evidence",
        "evidence_role": "machine_registry_evidence",
    },
    "validator_probe_verdict_evidence": {
        "order": 3,
        "contract_heading": "### 3. Validator-and-probe verdict evidence",
        "evidence_role": "validator_probe_verdict_evidence",
    },
    "bound_runtime_evidence": {
        "order": 4,
        "contract_heading": "### 4. Bound runtime evidence",
        "evidence_role": "bound_runtime_evidence",
    },
    "adjudicated_verdict_closure_evidence": {
        "order": 5,
        "contract_heading": "### 5. Adjudicated verdict closure evidence",
        "evidence_role": "adjudicated_verdict_closure_evidence",
    },
    "demoted_support_evidence": {
        "order": 6,
        "contract_heading": "### 6. Demoted support evidence",
        "evidence_role": "demoted_support_evidence",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "motivation_vs_terminal_evidence": {
        "order": 1,
        "contract_phrase": "motivating evidence is separated from terminal decision evidence;",
    },
    "latest_visible_vs_bound_receipt": {
        "order": 2,
        "contract_phrase": "latest visible receipt is separated from bound admissible receipt;",
    },
    "runtime_vs_shared_law_evidence": {
        "order": 3,
        "contract_phrase": "runtime evidence is separated from shared-law evidence;",
    },
    "summary_projection_vs_source_evidence": {
        "order": 4,
        "contract_phrase": "summary, projection, or commentary is separated from source evidence;",
    },
    "support_material_vs_active_success_path_evidence": {
        "order": 5,
        "contract_phrase": "sample, fixture, diagnostics, migration, and replay evidence are separated from active success-path evidence;",
    },
    "bound_runtime_vs_adjudicated_verdict_closure_evidence": {
        "order": 6,
        "contract_phrase": "bound runtime evidence is separated from adjudicated verdict closure evidence;",
    },
    "prose_payload_vs_machine_decision_evidence": {
        "order": 7,
        "contract_phrase": "handoff payload or operator-facing prose is separated from machine decision evidence.",
    },
}
EXPECTED_ADJUDICATION_PHASE_ALIGNMENT_ROWS = {
    "runtime_state": {
        "order": 1,
        "evidence_class_id": "bound_runtime_evidence",
        "proof_id": "bound_runtime_decision_evidence_proof",
        "surface_role": "live_state_truth_binding",
    },
    "receipts": {
        "order": 2,
        "evidence_class_id": "adjudicated_verdict_closure_evidence",
        "proof_id": "adjudicated_verdict_closure_decision_evidence_proof",
        "surface_role": "adjudicated_verdict_closure",
    },
}
EXPECTED_DECISION_EVIDENCE_PROOF_ROWS = {
    "frozen_law_decision_evidence_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-law decision-evidence proof",
        "proof_role": "frozen_law_decision_evidence_proof",
    },
    "registry_resolution_decision_evidence_proof": {
        "order": 2,
        "contract_heading": "### 2. Registry-resolution decision-evidence proof",
        "proof_role": "registry_resolution_decision_evidence_proof",
    },
    "validator_verdict_decision_evidence_proof": {
        "order": 3,
        "contract_heading": "### 3. Validator-verdict decision-evidence proof",
        "proof_role": "validator_verdict_decision_evidence_proof",
    },
    "bound_runtime_decision_evidence_proof": {
        "order": 4,
        "contract_heading": "### 4. Bound-runtime decision-evidence proof",
        "proof_role": "bound_runtime_decision_evidence_proof",
    },
    "adjudicated_verdict_closure_decision_evidence_proof": {
        "order": 5,
        "contract_heading": "### 5. Adjudicated-verdict-closure decision-evidence proof",
        "proof_role": "adjudicated_verdict_closure_decision_evidence_proof",
    },
    "demotion_confinement_decision_evidence_proof": {
        "order": 6,
        "contract_heading": "### 6. Demotion-confinement decision-evidence proof",
        "proof_role": "demotion_confinement_decision_evidence_proof",
    },
}
EXPECTED_EVIDENCE_CLASS_PROOF_ALIGNMENT_ROWS = {
    "frozen_law_evidence": {
        "order": 1,
        "proof_id": "frozen_law_decision_evidence_proof",
        "alignment_role": "frozen_law_evidence_class_proof_alignment",
    },
    "machine_registry_evidence": {
        "order": 2,
        "proof_id": "registry_resolution_decision_evidence_proof",
        "alignment_role": "machine_registry_evidence_class_proof_alignment",
    },
    "validator_probe_verdict_evidence": {
        "order": 3,
        "proof_id": "validator_verdict_decision_evidence_proof",
        "alignment_role": "validator_probe_verdict_evidence_class_proof_alignment",
    },
    "bound_runtime_evidence": {
        "order": 4,
        "proof_id": "bound_runtime_decision_evidence_proof",
        "alignment_role": "bound_runtime_evidence_class_proof_alignment",
    },
    "adjudicated_verdict_closure_evidence": {
        "order": 5,
        "proof_id": "adjudicated_verdict_closure_decision_evidence_proof",
        "alignment_role": "adjudicated_verdict_closure_evidence_class_proof_alignment",
    },
    "demoted_support_evidence": {
        "order": 6,
        "proof_id": "demotion_confinement_decision_evidence_proof",
        "alignment_role": "demoted_support_evidence_class_proof_alignment",
    },
}
EXPECTED_DECISION_EVIDENCE_LIMIT_ROWS = {
    "frozen_law_not_registry_resolution": {
        "order": 1,
        "contract_phrase": "frozen-law decision-evidence proof is not proof of registry resolution;",
    },
    "registry_resolution_not_validator_verdict": {
        "order": 2,
        "contract_phrase": "registry-resolution decision-evidence proof is not proof of validator-and-probe verdict passage;",
    },
    "validator_verdict_not_bound_runtime": {
        "order": 3,
        "contract_phrase": "validator-verdict decision-evidence proof is not proof of bound runtime evidence;",
    },
    "bound_runtime_not_verdict_closure": {
        "order": 4,
        "contract_phrase": "bound-runtime decision-evidence proof is not proof of adjudicated verdict closure;",
    },
    "adjudicated_verdict_closure_not_upstream_legality_authorship": {
        "order": 5,
        "contract_phrase": "adjudicated-verdict-closure decision-evidence proof is not proof of upstream legality authorship or earlier-phase substitution;",
    },
    "adjudicated_verdict_closure_not_support_terminality": {
        "order": 6,
        "contract_phrase": "adjudicated-verdict-closure decision-evidence proof is not proof that demoted support evidence may terminate the decision;",
    },
    "demotion_confinement_not_active_terminal_scope": {
        "order": 7,
        "contract_phrase": "demotion-confinement decision-evidence proof is not proof that support material may enter active success-path terminal scope.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "motivation_surface_as_terminal_evidence": {
        "order": 1,
        "contract_phrase": "motivating or contextual material is treated as if it were terminal decision evidence.",
    },
    "latest_visible_receipt_as_admissible_evidence": {
        "order": 2,
        "contract_phrase": "the latest visible receipt is treated as if it were automatically bound admissible evidence.",
    },
    "runtime_residue_as_shared_law_evidence": {
        "order": 3,
        "contract_phrase": "runtime residue is treated as if it rewrote shared law or constitutional authority.",
    },
    "summary_projection_as_source_evidence": {
        "order": 4,
        "contract_phrase": "summary, projection, or commentary is treated as if it were source evidence.",
    },
    "sample_fixture_diagnostic_as_live_decision_evidence": {
        "order": 5,
        "contract_phrase": "sample, fixture, diagnostics, migration, or replay material is treated as if it were active success-path evidence.",
    },
    "receipt_closure_as_upstream_legality_evidence": {
        "order": 6,
        "contract_phrase": "receipt closure is treated as if it authored or replaced earlier legality phases.",
    },
    "prose_payload_as_machine_decision_evidence": {
        "order": 7,
        "contract_phrase": "handoff prose or operator-facing narration is treated as if it were machine decision evidence.",
    },
    "decision_evidence_class_proof_flattening": {
        "order": 8,
        "contract_phrase": "frozen-law, registry, validator-verdict, bound-runtime, adjudicated-closure, and demoted-support evidence classes are treated as if one decision-evidence proof stratum were sufficient for all of them.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for decision-evidence admissibility law",
    "## Decision-evidence admissibility law",
    "## Six decision-evidence classes",
    "## Required decision-evidence differentiations",
    "## Evidence-class proof alignment",
    "## Adjudication-phase evidence alignment",
    "## Decision-evidence proof discipline",
    "## Decision-evidence proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn decision-evidence legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Decision-evidence admissibility row-family completeness must stay explicit",
        "Required evidence-class, differentiation, adjudication-phase-alignment,\ndecision-evidence-proof, evidence-class-proof-alignment, limit, and collapse\nfamilies must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize decision-evidence admissibility while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root decision-evidence admissibility completeness discipline",
        "Decision-evidence admissibility law is not a soft prose bundle.",
        "1. required evidence-class, differentiation, adjudication-phase-alignment, decision-evidence-proof, evidence-class-proof-alignment, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root decision-evidence admissibility completeness boundary",
        "1. Decision-evidence admissibility law must remain machine-readable as separate evidence-class, differentiation, adjudication-phase-alignment, decision-evidence-proof, evidence-class-proof-alignment, limit, and collapse row families.",
        "4. Protocol legality must not finalize decision-evidence admissibility while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime decision-evidence admissibility consumption boundary",
        "1. Runtime consumes decision-evidence admissibility law as separate evidence-class, differentiation, adjudication-phase-alignment, decision-evidence-proof, evidence-class-proof-alignment, limit, and collapse row families rather than as undifferentiated decision-evidence prose.",
        "4. Runtime must not finalize decision-evidence admissibility while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root decision-evidence admissibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = load_root_decision_evidence_admissibility(repo_root)
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
        stale_reasons.append(f"root_decision_evidence_admissibility_alias_error:{admissibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not admissibility_doc:
        stale_reasons.append("root_decision_evidence_admissibility_empty_or_invalid")
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

    evidence_class_rows = evidence_class_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    differentiation_rows = differentiation_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    adjudication_phase_alignment_rows = adjudication_phase_alignment_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    decision_evidence_proof_rows = decision_evidence_proof_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    evidence_class_proof_alignment_rows = evidence_class_proof_alignment_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    decision_evidence_limit_rows = decision_evidence_limit_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    collapse_rows = collapse_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(admissibility_doc) if admissibility_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    adjudication_surface_profiles = adjudication_surface_profiles_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "evidence_family": "protocol_root_decision_evidence_admissibility",
            "evidence_version": "v1",
            "contract_file": "identity/protocol/DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_decision_evidence_admissibility.py",
            "probe_script": "scripts/ci/run_protocol_root_decision_evidence_admissibility_probes_ci.sh",
            "common_script": "scripts/root_decision_evidence_admissibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(admissibility_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_decision_evidence_admissibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_evidence_class_rows", evidence_class_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_adjudication_phase_alignment_rows", adjudication_phase_alignment_rows),
            ("required_decision_evidence_proof_rows", decision_evidence_proof_rows),
            ("required_evidence_class_proof_alignment_rows", evidence_class_proof_alignment_rows),
            ("required_decision_evidence_limit_rows", decision_evidence_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_decision_evidence_admissibility_{field}_missing")
                error_code = ERR_REGISTRY
        if not admissibility_doc.get("contract_required_markers"):
            stale_reasons.append("root_decision_evidence_admissibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_decision_evidence_admissibility",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(admissibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_decision_evidence_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_evidence_class_rows",
                    "member_id_key": "evidence_class_id",
                    "actual_rows": evidence_class_rows,
                    "expected_rows": EXPECTED_EVIDENCE_CLASS_ROWS,
                    "id_attr": "evidence_class_id",
                },
                {
                    "family_id": "required_differentiation_rows",
                    "member_id_key": "differentiation_id",
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_adjudication_phase_alignment_rows",
                    "member_id_key": "machine_surface",
                    "actual_rows": adjudication_phase_alignment_rows,
                    "expected_rows": EXPECTED_ADJUDICATION_PHASE_ALIGNMENT_ROWS,
                    "id_attr": "machine_surface",
                },
                {
                    "family_id": "required_decision_evidence_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": decision_evidence_proof_rows,
                    "expected_rows": EXPECTED_DECISION_EVIDENCE_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_evidence_class_proof_alignment_rows",
                    "member_id_key": "evidence_class_id",
                    "actual_rows": evidence_class_proof_alignment_rows,
                    "expected_rows": EXPECTED_EVIDENCE_CLASS_PROOF_ALIGNMENT_ROWS,
                    "id_attr": "evidence_class_id",
                },
                {
                    "family_id": "required_decision_evidence_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": decision_evidence_limit_rows,
                    "expected_rows": EXPECTED_DECISION_EVIDENCE_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_collapse_rows",
                    "member_id_key": "collapse_id",
                    "actual_rows": collapse_rows,
                    "expected_rows": EXPECTED_COLLAPSE_ROWS,
                    "id_attr": "row_id",
                },
            ),
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        )

        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": evidence_class_rows,
                    "expected_rows": EXPECTED_EVIDENCE_CLASS_ROWS,
                    "field_name": "required_evidence_class_rows",
                    "id_attr": "evidence_class_id",
                    "compare_fields": ("contract_heading", "evidence_role"),
                },
                {
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "field_name": "required_differentiation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": adjudication_phase_alignment_rows,
                    "expected_rows": EXPECTED_ADJUDICATION_PHASE_ALIGNMENT_ROWS,
                    "field_name": "required_adjudication_phase_alignment_rows",
                    "id_attr": "machine_surface",
                    "compare_fields": ("evidence_class_id", "proof_id", "surface_role"),
                },
                {
                    "actual_rows": decision_evidence_proof_rows,
                    "expected_rows": EXPECTED_DECISION_EVIDENCE_PROOF_ROWS,
                    "field_name": "required_decision_evidence_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": evidence_class_proof_alignment_rows,
                    "expected_rows": EXPECTED_EVIDENCE_CLASS_PROOF_ALIGNMENT_ROWS,
                    "field_name": "required_evidence_class_proof_alignment_rows",
                    "id_attr": "evidence_class_id",
                    "compare_fields": ("proof_id", "alignment_role"),
                },
                {
                    "actual_rows": decision_evidence_limit_rows,
                    "expected_rows": EXPECTED_DECISION_EVIDENCE_LIMIT_ROWS,
                    "field_name": "required_decision_evidence_limit_rows",
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
            ),
            structure_violations=structure_violations,
            admissibility_violations=admissibility_violations,
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
                            evidence_class_rows,
                            reason="evidence_class_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            decision_evidence_proof_rows,
                            reason="proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            differentiation_rows + decision_evidence_limit_rows + collapse_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_phrase",),
                        ),
                    ),
                    payload_base={"field": "contract_file"},
                )
            )

        evidence_class_order_map = {row.evidence_class_id: row.order for row in evidence_class_rows}
        proof_order_map = {row.proof_id: row.order for row in decision_evidence_proof_rows}
        alignment_map = {row.evidence_class_id: row for row in evidence_class_proof_alignment_rows}
        previous_evidence_class_order = 0
        previous_proof_order = 0
        for row in sorted(evidence_class_proof_alignment_rows, key=lambda item: item.order):
            evidence_class_order = evidence_class_order_map.get(row.evidence_class_id)
            if evidence_class_order is None:
                integration_violations.append(
                    {
                        "field": "root_decision_evidence_admissibility",
                        "reason": "evidence_class_proof_alignment_missing_evidence_class",
                        "evidence_class_id": row.evidence_class_id,
                    }
                )
            else:
                if evidence_class_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_decision_evidence_admissibility",
                            "reason": "evidence_class_proof_alignment_evidence_order_mismatch",
                            "evidence_class_id": row.evidence_class_id,
                            "alignment_order": row.order,
                            "evidence_class_order": evidence_class_order,
                        }
                    )
                if evidence_class_order <= previous_evidence_class_order:
                    integration_violations.append(
                        {
                            "field": "root_decision_evidence_admissibility",
                            "reason": "evidence_class_proof_alignment_evidence_order_not_increasing",
                            "evidence_class_id": row.evidence_class_id,
                            "evidence_class_order": evidence_class_order,
                            "previous_evidence_class_order": previous_evidence_class_order,
                        }
                    )
                previous_evidence_class_order = evidence_class_order

            proof_order = proof_order_map.get(row.proof_id)
            if proof_order is None:
                integration_violations.append(
                    {
                        "field": "root_decision_evidence_admissibility",
                        "reason": "evidence_class_proof_alignment_missing_proof",
                        "evidence_class_id": row.evidence_class_id,
                        "proof_id": row.proof_id,
                    }
                )
            else:
                if proof_order <= previous_proof_order:
                    integration_violations.append(
                        {
                            "field": "root_decision_evidence_admissibility",
                            "reason": "evidence_class_proof_alignment_proof_order_not_increasing",
                            "evidence_class_id": row.evidence_class_id,
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
            evaluate_ordering_adjudication_phase_alignment(
                ordering_surface_profiles=adjudication_surface_profiles,
                required_alignment_rows=adjudication_phase_alignment_rows,
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
                mappings_required_children=('root-decision-evidence-admissibility.current.yaml', 'root-decision-evidence-admissibility.v1.yaml'),
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
        support_reason_prefix="decision_evidence_admissibility_violation",
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
        "evidence_class_count": len(evidence_class_rows),
        "differentiation_count": len(differentiation_rows),
        "adjudication_phase_alignment_count": len(adjudication_phase_alignment_rows),
        "decision_evidence_proof_count": len(decision_evidence_proof_rows),
        "evidence_class_proof_alignment_count": len(evidence_class_proof_alignment_rows),
        "decision_evidence_limit_count": len(decision_evidence_limit_rows),
        "collapse_count": len(collapse_rows),
        **project_root_contract_support_projection(
            prefix="decision_evidence",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "evidence_class_ids": [row.evidence_class_id for row in sorted(evidence_class_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "adjudication_phase_alignment_surfaces": [row.machine_surface for row in sorted(adjudication_phase_alignment_rows, key=lambda item: item.order)],
        "decision_evidence_proof_ids": [row.proof_id for row in sorted(decision_evidence_proof_rows, key=lambda item: item.order)],
        "evidence_class_proof_alignment_ids": [
            row.evidence_class_id for row in sorted(evidence_class_proof_alignment_rows, key=lambda item: item.order)
        ],
        "decision_evidence_limit_ids": [row.row_id for row in sorted(decision_evidence_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "adjudication_phase_alignment_rows": [
            {
                "order": row.order,
                "machine_surface": row.machine_surface,
                "evidence_class_id": row.evidence_class_id,
                "proof_id": row.proof_id,
                "surface_role": row.surface_role,
            }
            for row in sorted(adjudication_phase_alignment_rows, key=lambda item: item.order)
        ],
        "evidence_class_proof_alignment_rows": [
            {
                "order": row.order,
                "evidence_class_id": row.evidence_class_id,
                "proof_id": row.proof_id,
                "alignment_role": row.alignment_role,
            }
            for row in sorted(evidence_class_proof_alignment_rows, key=lambda item: item.order)
        ],
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
