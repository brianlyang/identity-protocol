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
from root_machine_world_ontology_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    load_root_machine_world_ontology,
    ontology_limit_rows_from_doc,
    ontology_proof_rows_from_doc,
    object_rows_from_doc,
    stratum_rows_from_doc,
)

STATUS_KEY = "protocol_root_machine_world_ontology_status"
ERR_REGISTRY = "IP-RMWO-001"
ERR_STRUCTURE = "IP-RMWO-002"
ERR_ONTOLOGY = "IP-RMWO-003"

EXPECTED_STRATA_ROWS = {
    "identity_resolution_objects": {
        "order": 1,
        "contract_heading": "### 1. Identity-resolution objects",
        "stratum_role": "identity_resolution_object_stratum",
    },
    "authority_execution_objects": {
        "order": 2,
        "contract_heading": "### 2. Authority and execution-boundary objects",
        "stratum_role": "authority_execution_object_stratum",
    },
    "continuity_retention_objects": {
        "order": 3,
        "contract_heading": "### 3. Continuity and retention objects",
        "stratum_role": "continuity_retention_object_stratum",
    },
    "feedback_gate_verdict_objects": {
        "order": 4,
        "contract_heading": "### 4. Feedback, gate, and verdict objects",
        "stratum_role": "feedback_gate_verdict_object_stratum",
    },
}
EXPECTED_OBJECT_ROWS = {
    "identity_id": {
        "order": 1,
        "contract_phrase": "`identity_id` is the stable identity-resolution key rather than a prompt nickname or narrative persona label.",
    },
    "scope": {
        "order": 2,
        "contract_phrase": "`scope` is the resolved operating scope rather than a free-form situational impression.",
    },
    "work_layer": {
        "order": 3,
        "contract_phrase": "`work_layer` is the active execution layer rather than a vague locality intuition.",
    },
    "source_layer": {
        "order": 4,
        "contract_phrase": "`source_layer` is the authority-bearing source layer rather than a convenience alias.",
    },
    "catalog_path": {
        "order": 5,
        "contract_phrase": "`catalog_path` is the canonical identity catalog source rather than a guessed filesystem memory.",
    },
    "pack_path": {
        "order": 6,
        "contract_phrase": "`pack_path` is the canonical resolved pack location rather than a repo fixture substitute.",
    },
    "actor_session_tuple": {
        "order": 7,
        "contract_phrase": "actor / session tuple is the machine-attested speaking/runtime tuple rather than a narrative self-claim.",
    },
    "launcher_surface": {
        "order": 8,
        "contract_phrase": "launcher surface is the governed execution-entry surface rather than filename discovery by habit.",
    },
    "current_turn_authoritative_truth": {
        "order": 9,
        "contract_phrase": "current-turn authoritative truth is the present-turn admissible authority rather than the latest visible artifact.",
    },
    "canonical_state": {
        "order": 10,
        "contract_phrase": "canonical state is the governed state object rather than an arbitrary local snapshot.",
    },
    "canonical_receipt": {
        "order": 11,
        "contract_phrase": "canonical receipt is the governed execution/admission receipt rather than any artifact that merely looks recent.",
    },
    "canonical_artifact_family": {
        "order": 12,
        "contract_phrase": "canonical artifact family is the governed output family rather than an undifferentiated memory bucket.",
    },
    "continuity_brief": {
        "order": 13,
        "contract_phrase": "continuity brief is the governed re-entry object rather than raw transcript persistence.",
    },
    "dialogue_retention_current_thread": {
        "order": 14,
        "contract_phrase": "dialogue-retention current-thread is the thread-scoped continuity object rather than global memory.",
    },
    "protocol_feedback_lane": {
        "order": 15,
        "contract_phrase": "protocol-feedback lane is the governed feedback object rather than free-form commentary.",
    },
    "required_gate_bundle": {
        "order": 16,
        "contract_phrase": "required gate bundle is the machine admission bundle rather than an informal checklist.",
    },
    "three_plane_verdict": {
        "order": 17,
        "contract_phrase": "three-plane verdict is the governed cross-plane verdict object rather than a prose summary.",
    },
}
EXPECTED_ONTOLOGY_PROOF_ROWS = {
    "canonical_object_definition_proof": {
        "order": 1,
        "contract_heading": "### 1. Canonical-object-definition proof",
        "proof_role": "canonical_object_definition_ontology_proof",
    },
    "stratum_boundary_preservation_proof": {
        "order": 2,
        "contract_heading": "### 2. Stratum-boundary preservation proof",
        "proof_role": "stratum_boundary_preservation_ontology_proof",
    },
    "authority_location_proof": {
        "order": 3,
        "contract_heading": "### 3. Authority-location proof",
        "proof_role": "authority_location_ontology_proof",
    },
    "lifecycle_position_proof": {
        "order": 4,
        "contract_heading": "### 4. Lifecycle-position proof",
        "proof_role": "lifecycle_position_ontology_proof",
    },
    "memory_family_non_collapse_proof": {
        "order": 5,
        "contract_heading": "### 5. Memory-family non-collapse proof",
        "proof_role": "memory_family_non_collapse_ontology_proof",
    },
}
EXPECTED_ONTOLOGY_LIMIT_ROWS = {
    "canonical_definition_not_stratum_boundary": {
        "order": 1,
        "contract_phrase": "canonical-object-definition proof is not proof of stratum-boundary preservation;",
    },
    "stratum_boundary_not_authority_location": {
        "order": 2,
        "contract_phrase": "stratum-boundary preservation proof is not proof of authority location;",
    },
    "authority_location_not_lifecycle_position": {
        "order": 3,
        "contract_phrase": "authority-location proof is not proof of lifecycle position;",
    },
    "lifecycle_position_not_memory_family_non_collapse": {
        "order": 4,
        "contract_phrase": "lifecycle-position proof is not proof of memory-family non-collapse;",
    },
    "memory_family_non_collapse_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "memory-family non-collapse proof is not proof that an object may bypass current-turn runtime adjudication.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "term_meaning_borrowing": {
        "order": 1,
        "contract_phrase": "terms borrow meaning from each other as if object boundaries were optional.",
    },
    "arbitrary_path_drift": {
        "order": 2,
        "contract_phrase": "paths drift arbitrarily and are treated as if path-bearing objects did not need canonical meaning.",
    },
    "latest_as_current": {
        "order": 3,
        "contract_phrase": "the latest visible artifact is treated as if it were automatically current-turn authority.",
    },
    "summary_as_truth": {
        "order": 4,
        "contract_phrase": "summary or projection is treated as if it were truth itself.",
    },
    "history_as_authority": {
        "order": 5,
        "contract_phrase": "history is treated as if it were present authority.",
    },
    "memory_as_vague_bucket": {
        "order": 6,
        "contract_phrase": "`memory` becomes a vague bucket that swallows multiple distinct object families and boundaries.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for machine-world ontology law",
    "## Machine-world ontology law",
    "## Four ontology strata",
    "## Required ontology objects",
    "## Machine-world ontology proof discipline",
    "## Machine-world ontology proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Machine-world ontology row-family completeness must stay explicit",
        "Required strata, object, ontology-proof, ontology-limit, and collapse families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize machine-world ontology legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root machine-world ontology completeness discipline",
        "Machine-world ontology law is not a soft prose bundle.",
        "1. required strata, object, ontology-proof, ontology-limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root machine-world ontology completeness boundary",
        "1. Machine-world ontology law must remain machine-readable as separate strata, object, ontology-proof, ontology-limit, and collapse row families.",
        "4. Protocol legality must not finalize machine-world ontology legality while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime machine-world ontology consumption boundary",
        "1. Runtime consumes machine-world ontology law as separate strata, object, ontology-proof, ontology-limit, and collapse row families rather than as undifferentiated naming prose.",
        "4. Runtime must not finalize machine-world ontology legality while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root machine-world ontology law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    ontology_doc, ontology_entry_path, ontology_active_path, ontology_alias_error = load_root_machine_world_ontology(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    ontology_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if ontology_alias_error:
        stale_reasons.append(f"root_machine_world_ontology_alias_error:{ontology_alias_error}")
        error_code = ERR_REGISTRY
    elif not ontology_doc:
        stale_reasons.append("root_machine_world_ontology_empty_or_invalid")
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

    stratum_rows = stratum_rows_from_doc(ontology_doc) if ontology_doc else ()
    object_rows = object_rows_from_doc(ontology_doc) if ontology_doc else ()
    ontology_proof_rows = ontology_proof_rows_from_doc(ontology_doc) if ontology_doc else ()
    ontology_limit_rows = ontology_limit_rows_from_doc(ontology_doc) if ontology_doc else ()
    collapse_rows = collapse_rows_from_doc(ontology_doc) if ontology_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(ontology_doc) if ontology_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "ontology_family": "protocol_root_machine_world_ontology",
            "ontology_version": "v1",
            "contract_file": "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_machine_world_ontology.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_world_ontology_probes_ci.sh",
            "common_script": "scripts/root_machine_world_ontology_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(ontology_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_world_ontology_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_strata_rows", stratum_rows),
            ("required_object_rows", object_rows),
            ("required_ontology_proof_rows", ontology_proof_rows),
            ("required_ontology_limit_rows", ontology_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_machine_world_ontology_{field}_missing")
                error_code = ERR_REGISTRY
        if not ontology_doc.get("contract_required_markers"):
            stale_reasons.append("root_machine_world_ontology_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_machine_world_ontology",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(ontology_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_machine_world_ontology_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_strata_rows",
                    "member_id_key": "stratum_id",
                    "actual_rows": stratum_rows,
                    "expected_rows": EXPECTED_STRATA_ROWS,
                    "id_attr": "stratum_id",
                },
                {
                    "family_id": "required_object_rows",
                    "member_id_key": "object_id",
                    "actual_rows": object_rows,
                    "expected_rows": EXPECTED_OBJECT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_ontology_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": ontology_proof_rows,
                    "expected_rows": EXPECTED_ONTOLOGY_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_ontology_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": ontology_limit_rows,
                    "expected_rows": EXPECTED_ONTOLOGY_LIMIT_ROWS,
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
                    "actual_rows": stratum_rows,
                    "expected_rows": EXPECTED_STRATA_ROWS,
                    "field_name": "required_strata_rows",
                    "id_attr": "stratum_id",
                    "compare_fields": ("contract_heading", "stratum_role"),
                },
                {
                    "actual_rows": object_rows,
                    "expected_rows": EXPECTED_OBJECT_ROWS,
                    "field_name": "required_object_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": ontology_proof_rows,
                    "expected_rows": EXPECTED_ONTOLOGY_PROOF_ROWS,
                    "field_name": "required_ontology_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": ontology_limit_rows,
                    "expected_rows": EXPECTED_ONTOLOGY_LIMIT_ROWS,
                    "field_name": "required_ontology_limit_rows",
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
            ontology_violations=ontology_violations,
        )

        contract_file = str(ontology_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            ontology_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(ontology_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            stratum_rows,
                            reason="stratum_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            ontology_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            object_rows + ontology_limit_rows + collapse_rows,
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
                mappings_required_children=('root-machine-world-ontology.current.yaml', 'root-machine-world-ontology.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = ontology_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_ONTOLOGY,
        support_reason_prefix="machine_world_ontology_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ONTOLOGY),
        "ontology_entry_path": str(ontology_entry_path),
        "ontology_active_path": str(ontology_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(ontology_doc.get("contract_file") or ""),
        "stratum_count": len(stratum_rows),
        "object_count": len(object_rows),
        "ontology_proof_count": len(ontology_proof_rows),
        "ontology_limit_count": len(ontology_limit_rows),
        "collapse_count": len(collapse_rows),
        **project_root_contract_support_projection(
            prefix="machine_world_ontology",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "stratum_ids": [row.stratum_id for row in sorted(stratum_rows, key=lambda item: item.order)],
        "object_ids": [row.row_id for row in sorted(object_rows, key=lambda item: item.order)],
        "ontology_proof_ids": [row.proof_id for row in sorted(ontology_proof_rows, key=lambda item: item.order)],
        "ontology_limit_ids": [row.row_id for row in sorted(ontology_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "ontology_violations": ontology_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
