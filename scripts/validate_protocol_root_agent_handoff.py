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
from root_agent_handoff_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    agent_handoff_completeness_rows_from_doc,
    anchor_rows_from_doc,
    readme_agent_handoff_completeness_surface,
    collapse_rows_from_doc,
    handoff_limit_rows_from_doc,
    handoff_proof_rows_from_doc,
    load_root_agent_handoff,
    payload_rows_from_doc,
    role_rows_from_doc,
)
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

STATUS_KEY = "protocol_root_agent_handoff_status"
ERR_REGISTRY = "IP-RAH-001"
ERR_STRUCTURE = "IP-RAH-002"
ERR_HANDOFF = "IP-RAH-003"

EXPECTED_ROLE_ROWS = {
    "master_orchestrator": {
        "order": 1,
        "contract_heading": "### 1. Master orchestration role",
        "handoff_role": "master_orchestrator",
    },
    "delegated_sub_agent_execution": {
        "order": 2,
        "contract_heading": "### 2. Delegated sub-agent execution role",
        "handoff_role": "delegated_sub_agent_execution",
    },
}
EXPECTED_PAYLOAD_ROWS = {
    "handoff_id": {"order": 1, "contract_phrase": "`handoff_id`"},
    "task_id": {"order": 2, "contract_phrase": "`task_id`"},
    "from_agent": {"order": 3, "contract_phrase": "`from_agent`"},
    "to_agent": {"order": 4, "contract_phrase": "`to_agent`"},
    "input_scope": {"order": 5, "contract_phrase": "`input_scope`"},
    "actions_taken": {"order": 6, "contract_phrase": "`actions_taken`"},
    "artifacts": {"order": 7, "contract_phrase": "`artifacts`"},
    "result": {"order": 8, "contract_phrase": "`result`"},
    "next_action": {"order": 9, "contract_phrase": "`next_action`"},
    "rulebook_update": {"order": 10, "contract_phrase": "`rulebook_update`"},
}
EXPECTED_ANCHOR_ROWS = {
    "artifact_path_kind": {
        "order": 1,
        "contract_phrase": "each artifact item includes `path` and `kind`;",
    },
    "rulebook_update_run_binding": {
        "order": 2,
        "contract_phrase": "`rulebook_update.evidence_run_id` is required when `rulebook_update.applied=true`;",
    },
    "next_action_triplet": {
        "order": 3,
        "contract_phrase": "`next_action` includes `owner`, `action`, and `input`;",
    },
    "production_identity_task_freshness": {
        "order": 4,
        "contract_phrase": "production handoff evidence remains freshness-bounded and identity/task scoped when current-turn legality is claimed;",
    },
    "production_sample_track_separation": {
        "order": 5,
        "contract_phrase": "production and sample validation tracks remain separated so sample proof never stands in for current-run runtime proof.",
    },
}
EXPECTED_HANDOFF_PROOF_ROWS = {
    "role_boundary_proof": {
        "order": 1,
        "contract_heading": "### 1. Role-boundary proof",
        "proof_role": "role_boundary_governed_handoff_proof",
    },
    "payload_completeness_proof": {
        "order": 2,
        "contract_heading": "### 2. Payload-completeness proof",
        "proof_role": "payload_completeness_governed_handoff_proof",
    },
    "evidence_binding_proof": {
        "order": 3,
        "contract_heading": "### 3. Evidence-binding proof",
        "proof_role": "evidence_binding_governed_handoff_proof",
    },
    "next_step_executability_proof": {
        "order": 4,
        "contract_heading": "### 4. Next-step-executability proof",
        "proof_role": "next_step_executability_governed_handoff_proof",
    },
    "validation_track_separation_proof": {
        "order": 5,
        "contract_heading": "### 5. Validation-track-separation proof",
        "proof_role": "validation_track_separation_governed_handoff_proof",
    },
}
EXPECTED_HANDOFF_LIMIT_ROWS = {
    "role_boundary_not_payload_completeness": {
        "order": 1,
        "contract_phrase": "role-boundary proof is not proof of payload completeness;",
    },
    "payload_completeness_not_evidence_binding": {
        "order": 2,
        "contract_phrase": "payload-completeness proof is not proof of evidence binding;",
    },
    "evidence_binding_not_next_step_executability": {
        "order": 3,
        "contract_phrase": "evidence-binding proof is not proof of next-step executability;",
    },
    "next_step_executability_not_validation_track_separation": {
        "order": 4,
        "contract_phrase": "next-step-executability proof is not proof of validation-track separation;",
    },
    "validation_track_separation_not_current_turn_legality": {
        "order": 5,
        "contract_phrase": "validation-track-separation proof is not proof of current-turn production handoff legality by itself.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "delegated_scope_as_global_contract_authority": {
        "order": 1,
        "contract_phrase": "a delegated sub-agent mutates top-level identity or protocol contract surfaces as if delegated execution granted global law authorship.",
    },
    "completion_without_evidence_artifacts": {
        "order": 2,
        "contract_phrase": "a handoff claims completion without evidence artifacts that support the claimed result.",
    },
    "missing_executable_next_action_as_valid_delivery": {
        "order": 3,
        "contract_phrase": "a handoff omits an executable next action but is treated as a valid delivery.",
    },
    "contradictory_evidence_as_successful_handoff": {
        "order": 4,
        "contract_phrase": "a handoff result is treated as valid even when it contradicts the provided evidence.",
    },
    "sample_track_as_production_runtime_proof": {
        "order": 5,
        "contract_phrase": "sample or self-test validation is treated as if it proved present-turn production handoff legality.",
    },
}
EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS = {
    "explicit_agent_handoff_row_families": {
        "order": 1,
        "contract_phrase": "required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_agent_handoff_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_agent_handoff_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_agent_handoff_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize agent-handoff legality while missing or unexpected handoff row identities remain known only internally;",
    },
    "fail_close_preserves_agent_handoff_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected role, payload, anchor, proof, limit, and collapse row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "This file remains the authoritative root-domain contract for governed agent-handoff law.",
    "## Governed handoff law",
    "## Two governed handoff roles",
    "## Mandatory handoff payload fields",
    "## Required handoff evidence and next-step anchors",
    "## Handoff-proof discipline",
    "## Handoff-proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Agent-handoff row-family completeness must stay explicit",
        "Required role, payload, anchor, handoff-proof, handoff-limit, and collapse families must remain explicit as separate machine-readable row families.",
        "README root agent-handoff completeness discipline must therefore stay congruent with admitted agent-handoff-completeness rows rather than becoming a freehand completeness summary.",
        "The machine world must not finalize handoff legality while required role, payload, anchor, proof, limit, or collapse identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root agent-handoff completeness discipline",
        "`AGENT_HANDOFF_CONTRACT.md` freezes governed handoff law as root-domain contract law rather than informal collaboration guidance.",
        "These agent-handoff-completeness rules must remain bound to canonical agent-handoff-completeness rows rather than drifting into soft summary prose.",
        "1. required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root agent-handoff completeness boundary",
        "1. Agent-handoff law must remain machine-readable as separate role, payload, anchor, handoff-proof, handoff-limit, and collapse row families.",
        "4. Protocol legality must not finalize agent-handoff legality while missing or unexpected handoff row identities remain known only inside validator logic.",
        "6. README root agent-handoff completeness discipline rendered at protocol root must remain congruent with admitted agent-handoff-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime agent-handoff consumption boundary",
        "1. Runtime consumes agent-handoff law as separate role, payload, anchor, handoff-proof, handoff-limit, and collapse row families rather than as undifferentiated collaboration prose.",
        "4. Runtime must not finalize agent-handoff legality while missing or unexpected handoff row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root agent-handoff completeness discipline as a governed completeness projection bound to admitted agent-handoff-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root agent-handoff law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    handoff_doc, handoff_entry_path, handoff_active_path, handoff_alias_error = load_root_agent_handoff(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    handoff_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    error_code = ""

    if handoff_alias_error:
        stale_reasons.append(f"root_agent_handoff_alias_error:{handoff_alias_error}")
        error_code = ERR_REGISTRY
    elif not handoff_doc:
        stale_reasons.append("root_agent_handoff_empty_or_invalid")
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

    role_rows = role_rows_from_doc(handoff_doc) if handoff_doc else ()
    payload_rows = payload_rows_from_doc(handoff_doc) if handoff_doc else ()
    anchor_rows = anchor_rows_from_doc(handoff_doc) if handoff_doc else ()
    handoff_proof_rows = handoff_proof_rows_from_doc(handoff_doc) if handoff_doc else ()
    handoff_limit_rows = handoff_limit_rows_from_doc(handoff_doc) if handoff_doc else ()
    collapse_rows = collapse_rows_from_doc(handoff_doc) if handoff_doc else ()
    agent_handoff_completeness_rows = (
        agent_handoff_completeness_rows_from_doc(handoff_doc) if handoff_doc else ()
    )
    agent_handoff_completeness_surface = readme_agent_handoff_completeness_surface(repo_root)
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(handoff_doc) if handoff_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "role_rows",
                "member_id_key": "role_id",
                "actual_rows": role_rows,
                "expected_rows": EXPECTED_ROLE_ROWS,
                "id_attr": "role_id",
            },
            {
                "family_id": "payload_rows",
                "member_id_key": "payload_field_id",
                "actual_rows": payload_rows,
                "expected_rows": EXPECTED_PAYLOAD_ROWS,
                "id_attr": "row_id",
            },
            {
                "family_id": "anchor_rows",
                "member_id_key": "anchor_id",
                "actual_rows": anchor_rows,
                "expected_rows": EXPECTED_ANCHOR_ROWS,
                "id_attr": "row_id",
            },
            {
                "family_id": "handoff_proof_rows",
                "member_id_key": "proof_id",
                "actual_rows": handoff_proof_rows,
                "expected_rows": EXPECTED_HANDOFF_PROOF_ROWS,
                "id_attr": "proof_id",
            },
            {
                "family_id": "handoff_limit_rows",
                "member_id_key": "limit_id",
                "actual_rows": handoff_limit_rows,
                "expected_rows": EXPECTED_HANDOFF_LIMIT_ROWS,
                "id_attr": "row_id",
            },
            {
                "family_id": "collapse_rows",
                "member_id_key": "collapse_id",
                "actual_rows": collapse_rows,
                "expected_rows": EXPECTED_COLLAPSE_ROWS,
                "id_attr": "row_id",
            },
            {
                "family_id": "agent_handoff_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": agent_handoff_completeness_rows,
                "expected_rows": {
                    completeness_id: {}
                    for completeness_id in EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "agent_handoff_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": agent_handoff_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {}
                    for row in EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS.values()
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
        expected_scalar_fields = {
            "agent_handoff_family": "protocol_root_agent_handoff",
            "agent_handoff_version": "v1",
            "contract_file": "identity/protocol/AGENT_HANDOFF_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_agent_handoff.py",
            "probe_script": "scripts/ci/run_protocol_root_agent_handoff_probes_ci.sh",
            "common_script": "scripts/root_agent_handoff_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(handoff_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_agent_handoff_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_role_rows", role_rows),
            ("required_payload_rows", payload_rows),
            ("required_anchor_rows", anchor_rows),
            ("required_handoff_proof_rows", handoff_proof_rows),
            ("required_handoff_limit_rows", handoff_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_agent_handoff_{field}_missing")
                error_code = ERR_REGISTRY
        if not agent_handoff_completeness_rows:
            stale_reasons.append("root_agent_handoff_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not handoff_doc.get("contract_required_markers"):
            stale_reasons.append("root_agent_handoff_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_agent_handoff",
            )
        )
        if any(reason.startswith("root_agent_handoff_anchor_") for reason in stale_reasons):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(handoff_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_agent_handoff_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        for reason in agent_handoff_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "agent_handoff_completeness_surface",
                    "reason": f"agent_handoff_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": role_rows,
                    "expected_rows": EXPECTED_ROLE_ROWS,
                    "field_name": "required_role_rows",
                    "id_attr": "role_id",
                    "compare_fields": ("contract_heading", "handoff_role"),
                },
                {
                    "actual_rows": payload_rows,
                    "expected_rows": EXPECTED_PAYLOAD_ROWS,
                    "field_name": "required_payload_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "field_name": "required_anchor_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": handoff_proof_rows,
                    "expected_rows": EXPECTED_HANDOFF_PROOF_ROWS,
                    "field_name": "required_handoff_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": handoff_limit_rows,
                    "expected_rows": EXPECTED_HANDOFF_LIMIT_ROWS,
                    "field_name": "required_handoff_limit_rows",
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
                    "actual_rows": agent_handoff_completeness_rows,
                    "expected_rows": EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS,
                    "field_name": "agent_handoff_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "non_contiguous_reason": "agent_handoff_completeness_row_order_non_contiguous",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "agent_handoff_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": agent_handoff_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "agent_handoff_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_agent_handoff_completeness_surface_phrase",
                    "non_contiguous_reason": "agent_handoff_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_agent_handoff_completeness_surface_rows",
                    "extra_reason": "extra_agent_handoff_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "agent_handoff_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
        )

        contract_file = str(handoff_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            handoff_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(handoff_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(role_rows, reason="role_heading_missing"),
                        contract_text_marker_checks_from_rows(handoff_proof_rows, reason="proof_heading_missing"),
                        contract_text_marker_checks_from_rows(
                            payload_rows + anchor_rows + handoff_limit_rows + collapse_rows,
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
                mappings_required_children=("root-agent-handoff.current.yaml", "root-agent-handoff.v1.yaml"),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
                authority_missing_anchor_reason="authority_anchor_missing",
                authority_missing_markers_reason="authority_required_markers_missing",
                authority_projection_role_reason="authority_projection_role_mismatch",
                authority_projection_mode_reason="authority_projection_mode_mismatch",
                routing_missing_anchor_reason="routing_anchor_missing",
                routing_missing_markers_reason="routing_required_markers_missing",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    support_violations = handoff_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_HANDOFF,
        project_structure_reasons=True,
        project_support_reasons=False,
        include_summary_markers=True,
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    rc = int(verdict["rc"])
    summary_markers = list(verdict["summary_markers"])

    payload = {
        STATUS_KEY: status,
        "error_code": error_code,
        "repo_root": str(repo_root),
        "mapping_entry_path": str(handoff_entry_path),
        "mapping_active_path": str(handoff_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "routing_entry_path": str(routing_entry_path),
        "routing_active_path": str(routing_active_path),
        "role_count": len(role_rows),
        "payload_field_count": len(payload_rows),
        "anchor_count": len(anchor_rows),
        "handoff_proof_count": len(handoff_proof_rows),
        "handoff_limit_count": len(handoff_limit_rows),
        "collapse_count": len(collapse_rows),
        "agent_handoff_completeness_row_count": len(agent_handoff_completeness_rows),
        **project_root_contract_support_projection(
            prefix="agent_handoff",
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
                    payload_key="agent_handoff_completeness_row_coverage_status",
                    family_id="agent_handoff_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="agent_handoff_completeness_row_identity_projection_status",
                    family_id="agent_handoff_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="agent_handoff_completeness_surface_coverage_status",
                    family_id="agent_handoff_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="agent_handoff_completeness_surface_identity_projection_status",
                    family_id="agent_handoff_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        **project_named_row_family_statuses(
            row_family_projection_rows_by_id=row_family_projection_by_id,
            specs=(
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="role_row_coverage_status",
                    family_id="role_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="role_row_identity_projection_status",
                    family_id="role_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="payload_row_coverage_status",
                    family_id="payload_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="payload_row_identity_projection_status",
                    family_id="payload_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="anchor_row_coverage_status",
                    family_id="anchor_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="anchor_row_identity_projection_status",
                    family_id="anchor_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="handoff_proof_row_coverage_status",
                    family_id="handoff_proof_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="handoff_proof_row_identity_projection_status",
                    family_id="handoff_proof_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="handoff_limit_row_coverage_status",
                    family_id="handoff_limit_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="handoff_limit_row_identity_projection_status",
                    family_id="handoff_limit_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="collapse_row_coverage_status",
                    family_id="collapse_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="collapse_row_identity_projection_status",
                    family_id="collapse_rows",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "agent_handoff_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(agent_handoff_completeness_rows, key=lambda item: item.order)
        ],
        "agent_handoff_completeness_surface": {
            "rel_path": agent_handoff_completeness_surface.rel_path,
            "entry_count": len(agent_handoff_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in agent_handoff_completeness_surface.rows
            ],
            "extraction_violations": list(agent_handoff_completeness_surface.extraction_violations),
        },
        "handoff_proof_ids": [row.proof_id for row in sorted(handoff_proof_rows, key=lambda item: item.order)],
        "handoff_limit_ids": [row.row_id for row in sorted(handoff_limit_rows, key=lambda item: item.order)],
        "row_family_projection_rows": row_family_projection_rows,
        "stale_reasons": stale_reasons,
        "structure_violations": structure_violations,
        "handoff_violations": handoff_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "summary_markers": summary_markers,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
