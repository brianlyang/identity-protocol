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
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_success_path_state_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    differentiation_rows_from_doc,
    load_root_success_path_state_admissibility,
    state_admission_limit_rows_from_doc,
    state_admission_proof_rows_from_doc,
    state_class_rows_from_doc,
    state_class_proof_alignment_rows_from_doc,
)

STATUS_KEY = "protocol_root_success_path_state_admissibility_status"
ERR_REGISTRY = "IP-SPSA-001"
ERR_STRUCTURE = "IP-SPSA-002"
ERR_STATE_ADMISSIBILITY = "IP-SPSA-003"

EXPECTED_STATE_CLASS_ROWS = {
    "frozen_state_definition": {
        "order": 1,
        "contract_heading": "### 1. Frozen state definition",
        "state_role": "frozen_state_definition",
    },
    "admissible_current_turn_state": {
        "order": 2,
        "contract_heading": "### 2. Admissible current-turn state",
        "state_role": "admissible_current_turn_state",
    },
    "bound_active_success_path_state": {
        "order": 3,
        "contract_heading": "### 3. Bound active success-path state",
        "state_role": "bound_active_success_path_state",
    },
    "optional_non_entry_state": {
        "order": 4,
        "contract_heading": "### 4. Optional non-entry state",
        "state_role": "optional_non_entry_state",
    },
    "governed_recovery_only_state": {
        "order": 5,
        "contract_heading": "### 5. Governed recovery-only state",
        "state_role": "governed_recovery_only_state",
    },
    "demoted_support_or_quarantine_state": {
        "order": 6,
        "contract_heading": "### 6. Demoted support or quarantine state",
        "state_role": "demoted_support_or_quarantine_state",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "frozen_vs_admissible_state": {
        "order": 1,
        "contract_phrase": "frozen law-defined state is separated from admissible current-turn state;",
    },
    "admissible_vs_bound_success_state": {
        "order": 2,
        "contract_phrase": "admissible current-turn state is separated from bound active success-path state;",
    },
    "optional_vs_recovery_state": {
        "order": 3,
        "contract_phrase": "optional non-entry state is separated from governed recovery-only state;",
    },
    "recovery_vs_support_quarantine_state": {
        "order": 4,
        "contract_phrase": "governed recovery-only state is separated from demoted support or quarantine state;",
    },
    "visible_projection_vs_state_admission_proof": {
        "order": 5,
        "contract_phrase": "visible status projection is separated from success-path state admission proof;",
    },
    "progress_feeling_vs_lawful_state_admission": {
        "order": 6,
        "contract_phrase": "local progress feeling or convenience is separated from lawful state admission.",
    },
}
EXPECTED_STATE_ADMISSION_PROOF_ROWS = {
    "frozen_definition_state_admission_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-definition state-admission proof",
        "proof_role": "frozen_definition_state_admission_proof",
    },
    "current_turn_admissibility_state_admission_proof": {
        "order": 2,
        "contract_heading": "### 2. Current-turn-admissibility state-admission proof",
        "proof_role": "current_turn_admissibility_state_admission_proof",
    },
    "active_binding_state_admission_proof": {
        "order": 3,
        "contract_heading": "### 3. Active-binding state-admission proof",
        "proof_role": "active_binding_state_admission_proof",
    },
    "non_entry_recovery_classification_state_admission_proof": {
        "order": 4,
        "contract_heading": "### 4. Non-entry/recovery-classification proof",
        "proof_role": "non_entry_recovery_classification_state_admission_proof",
    },
    "support_quarantine_confinement_state_admission_proof": {
        "order": 5,
        "contract_heading": "### 5. Support/quarantine-confinement proof",
        "proof_role": "support_quarantine_confinement_state_admission_proof",
    },
}
EXPECTED_STATE_CLASS_PROOF_ALIGNMENT_ROWS = {
    "frozen_state_definition": {
        "order": 1,
        "proof_id": "frozen_definition_state_admission_proof",
        "alignment_role": "frozen_state_definition_class_proof_alignment",
    },
    "admissible_current_turn_state": {
        "order": 2,
        "proof_id": "current_turn_admissibility_state_admission_proof",
        "alignment_role": "admissible_current_turn_state_class_proof_alignment",
    },
    "bound_active_success_path_state": {
        "order": 3,
        "proof_id": "active_binding_state_admission_proof",
        "alignment_role": "bound_active_success_path_state_class_proof_alignment",
    },
    "optional_non_entry_state": {
        "order": 4,
        "proof_id": "non_entry_recovery_classification_state_admission_proof",
        "alignment_role": "optional_non_entry_state_class_proof_alignment",
    },
    "governed_recovery_only_state": {
        "order": 5,
        "proof_id": "non_entry_recovery_classification_state_admission_proof",
        "alignment_role": "governed_recovery_only_state_class_proof_alignment",
    },
    "demoted_support_or_quarantine_state": {
        "order": 6,
        "proof_id": "support_quarantine_confinement_state_admission_proof",
        "alignment_role": "demoted_support_or_quarantine_state_class_proof_alignment",
    },
}
EXPECTED_STATE_ADMISSION_LIMIT_ROWS = {
    "frozen_definition_not_current_turn_admissibility": {
        "order": 1,
        "contract_phrase": "frozen-definition state-admission proof is not proof of current-turn admissibility;",
    },
    "current_turn_admissibility_not_active_binding": {
        "order": 2,
        "contract_phrase": "current-turn-admissibility state-admission proof is not proof of active binding;",
    },
    "active_binding_not_non_entry_recovery_classification": {
        "order": 3,
        "contract_phrase": "active-binding state-admission proof is not proof of lawful non-entry or recovery classification;",
    },
    "non_entry_recovery_not_support_quarantine_confinement": {
        "order": 4,
        "contract_phrase": "non-entry/recovery-classification proof is not proof of support or quarantine confinement;",
    },
    "support_quarantine_not_active_success_path_admission": {
        "order": 5,
        "contract_phrase": "support/quarantine-confinement proof is not proof of active success-path admission.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "defined_state_as_live_success_state": {
        "order": 1,
        "contract_phrase": "a law-defined or declared state is treated as if it were already live success-path admission.",
    },
    "admissible_unbound_state_as_active_path_state": {
        "order": 2,
        "contract_phrase": "an admissible but unbound state is treated as if it were already on the active success path.",
    },
    "optional_state_as_failure_or_failure_as_optional": {
        "order": 3,
        "contract_phrase": "optional non-entry state and governed recovery-only state are treated as if they were interchangeable.",
    },
    "recovery_state_as_success_state": {
        "order": 4,
        "contract_phrase": "a governed recovery, blocked, or redirected state is treated as if it were active success-path state.",
    },
    "support_quarantine_state_as_active_state": {
        "order": 5,
        "contract_phrase": "demoted support, migration, replay, diagnostics, archive, or quarantine state is treated as if it were active success-path state.",
    },
    "status_projection_as_state_admission_proof": {
        "order": 6,
        "contract_phrase": "a visible status label, projection, or dashboard summary is treated as if it proved lawful state admission.",
    },
    "state_class_proof_flattening": {
        "order": 7,
        "contract_phrase": "frozen-definition, admissible-current-turn, bound-active, optional-non-entry, governed-recovery, and demoted-support state classes are treated as if one state-admission proof stratum were sufficient for all of them.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for success-path state admissibility law",
    "## Success-path state admissibility law",
    "## Six state classes",
    "## Required state differentiations",
    "## State-class proof alignment",
    "## State-admission proof discipline",
    "## State-admission proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn success-path state legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Success-path state admissibility row-family completeness must stay explicit",
        "Required state-class, differentiation, proof, state-class-proof-alignment,\nlimit, and collapse families must remain explicit as separate machine-readable\nrow families.",
        "The machine world must not finalize success-path state admissibility while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root success-path state admissibility completeness discipline",
        "Success-path state admissibility law is not a soft prose bundle.",
        "1. required state-class, differentiation, proof, state-class-proof-alignment, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root success-path state admissibility completeness boundary",
        "1. Success-path state admissibility law must remain machine-readable as separate state-class, differentiation, proof, state-class-proof-alignment, limit, and collapse row families.",
        "4. Protocol legality must not finalize success-path state admissibility while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime success-path state admissibility consumption boundary",
        "1. Runtime consumes success-path state admissibility law as separate state-class, differentiation, proof, state-class-proof-alignment, limit, and collapse row families rather than as undifferentiated state-admission prose.",
        "4. Runtime must not finalize success-path state admissibility while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root success-path state admissibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    state_doc, state_entry_path, state_active_path, state_alias_error = load_root_success_path_state_admissibility(repo_root)
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

    if state_alias_error:
        stale_reasons.append(f"root_success_path_state_admissibility_alias_error:{state_alias_error}")
        error_code = ERR_REGISTRY
    elif not state_doc:
        stale_reasons.append("root_success_path_state_admissibility_empty_or_invalid")
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

    state_class_rows = state_class_rows_from_doc(state_doc) if state_doc else ()
    differentiation_rows = differentiation_rows_from_doc(state_doc) if state_doc else ()
    state_admission_proof_rows = state_admission_proof_rows_from_doc(state_doc) if state_doc else ()
    state_class_proof_alignment_rows = state_class_proof_alignment_rows_from_doc(state_doc) if state_doc else ()
    state_admission_limit_rows = state_admission_limit_rows_from_doc(state_doc) if state_doc else ()
    collapse_rows = collapse_rows_from_doc(state_doc) if state_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(state_doc) if state_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "state_family": "protocol_root_success_path_state_admissibility",
            "state_version": "v1",
            "contract_file": "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_success_path_state_admissibility.py",
            "probe_script": "scripts/ci/run_protocol_root_success_path_state_admissibility_probes_ci.sh",
            "common_script": "scripts/root_success_path_state_admissibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(state_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_success_path_state_admissibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_state_class_rows", state_class_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_state_admission_proof_rows", state_admission_proof_rows),
            ("required_state_class_proof_alignment_rows", state_class_proof_alignment_rows),
            ("required_state_admission_limit_rows", state_admission_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_success_path_state_admissibility_{field}_missing")
                error_code = ERR_REGISTRY
        if not state_doc.get("contract_required_markers"):
            stale_reasons.append("root_success_path_state_admissibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_success_path_state_admissibility",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(state_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_success_path_state_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_state_class_rows",
                    "member_id_key": "state_class_id",
                    "actual_rows": state_class_rows,
                    "expected_rows": EXPECTED_STATE_CLASS_ROWS,
                    "id_attr": "state_class_id",
                },
                {
                    "family_id": "required_differentiation_rows",
                    "member_id_key": "differentiation_id",
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_state_admission_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": state_admission_proof_rows,
                    "expected_rows": EXPECTED_STATE_ADMISSION_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_state_class_proof_alignment_rows",
                    "member_id_key": "state_class_id",
                    "actual_rows": state_class_proof_alignment_rows,
                    "expected_rows": EXPECTED_STATE_CLASS_PROOF_ALIGNMENT_ROWS,
                    "id_attr": "state_class_id",
                },
                {
                    "family_id": "required_state_admission_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": state_admission_limit_rows,
                    "expected_rows": EXPECTED_STATE_ADMISSION_LIMIT_ROWS,
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
                    "actual_rows": state_class_rows,
                    "expected_rows": EXPECTED_STATE_CLASS_ROWS,
                    "field_name": "required_state_class_rows",
                    "id_attr": "state_class_id",
                    "compare_fields": ("contract_heading", "state_role"),
                },
                {
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "field_name": "required_differentiation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": state_admission_proof_rows,
                    "expected_rows": EXPECTED_STATE_ADMISSION_PROOF_ROWS,
                    "field_name": "required_state_admission_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": state_class_proof_alignment_rows,
                    "expected_rows": EXPECTED_STATE_CLASS_PROOF_ALIGNMENT_ROWS,
                    "field_name": "required_state_class_proof_alignment_rows",
                    "id_attr": "state_class_id",
                    "compare_fields": ("proof_id", "alignment_role"),
                },
                {
                    "actual_rows": state_admission_limit_rows,
                    "expected_rows": EXPECTED_STATE_ADMISSION_LIMIT_ROWS,
                    "field_name": "required_state_admission_limit_rows",
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

        contract_file = str(state_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            admissibility_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(state_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            state_class_rows,
                            reason="state_class_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            state_admission_proof_rows,
                            reason="proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            differentiation_rows + state_admission_limit_rows + collapse_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_phrase",),
                        ),
                    ),
                    payload_base={"field": "contract_file"},
                )
            )

        state_class_order_map = {row.state_class_id: row.order for row in state_class_rows}
        proof_order_map = {row.proof_id: row.order for row in state_admission_proof_rows}
        previous_state_class_order = 0
        previous_proof_order = 0
        for row in sorted(state_class_proof_alignment_rows, key=lambda item: item.order):
            state_class_order = state_class_order_map.get(row.state_class_id)
            if state_class_order is None:
                integration_violations.append(
                    {
                        "field": "root_success_path_state_admissibility",
                        "reason": "state_class_proof_alignment_missing_state_class",
                        "state_class_id": row.state_class_id,
                    }
                )
            else:
                if state_class_order != row.order:
                    integration_violations.append(
                        {
                            "field": "root_success_path_state_admissibility",
                            "reason": "state_class_proof_alignment_state_order_mismatch",
                            "state_class_id": row.state_class_id,
                            "alignment_order": row.order,
                            "state_class_order": state_class_order,
                        }
                    )
                if state_class_order <= previous_state_class_order:
                    integration_violations.append(
                        {
                            "field": "root_success_path_state_admissibility",
                            "reason": "state_class_proof_alignment_state_order_not_increasing",
                            "state_class_id": row.state_class_id,
                            "state_class_order": state_class_order,
                            "previous_state_class_order": previous_state_class_order,
                        }
                    )
                previous_state_class_order = state_class_order

            proof_order = proof_order_map.get(row.proof_id)
            if proof_order is None:
                integration_violations.append(
                    {
                        "field": "root_success_path_state_admissibility",
                        "reason": "state_class_proof_alignment_missing_proof",
                        "state_class_id": row.state_class_id,
                        "proof_id": row.proof_id,
                    }
                )
            else:
                if proof_order < previous_proof_order:
                    integration_violations.append(
                        {
                            "field": "root_success_path_state_admissibility",
                            "reason": "state_class_proof_alignment_proof_order_regressed",
                            "state_class_id": row.state_class_id,
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
                mappings_required_children=('root-success-path-state-admissibility.current.yaml', 'root-success-path-state-admissibility.v1.yaml'),
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
        support_error_code=ERR_STATE_ADMISSIBILITY,
        support_reason_prefix="success_path_state_admissibility_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_STATE_ADMISSIBILITY),
        "state_entry_path": str(state_entry_path),
        "state_active_path": str(state_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(state_doc.get("contract_file") or ""),
        "state_class_count": len(state_class_rows),
        "differentiation_count": len(differentiation_rows),
        "state_admission_proof_count": len(state_admission_proof_rows),
        "state_class_proof_alignment_count": len(state_class_proof_alignment_rows),
        "state_admission_limit_count": len(state_admission_limit_rows),
        "collapse_count": len(collapse_rows),
        **project_root_contract_support_projection(
            prefix="success_path_state",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "state_class_ids": [row.state_class_id for row in sorted(state_class_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "state_admission_proof_ids": [row.proof_id for row in sorted(state_admission_proof_rows, key=lambda item: item.order)],
        "state_class_proof_alignment_ids": [
            row.state_class_id for row in sorted(state_class_proof_alignment_rows, key=lambda item: item.order)
        ],
        "state_admission_limit_ids": [row.row_id for row in sorted(state_admission_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "state_class_proof_alignment_rows": [
            {
                "order": row.order,
                "state_class_id": row.state_class_id,
                "proof_id": row.proof_id,
                "alignment_role": row.alignment_role,
            }
            for row in sorted(state_class_proof_alignment_rows, key=lambda item: item.order)
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
