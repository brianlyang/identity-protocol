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
from root_contract_row_validation_common import validate_contract_row_batches
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
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_protocol_instance_responsibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    boundary_collapse_rows_from_doc,
    escalation_limit_rows_from_doc,
    escalation_proof_rows_from_doc,
    escalation_rows_from_doc,
    layer_rows_from_doc,
    load_root_protocol_instance_responsibility,
    responsibility_rows_from_doc,
)

STATUS_KEY = "protocol_root_protocol_instance_responsibility_status"
ERR_REGISTRY = "IP-RPIR-001"
ERR_STRUCTURE = "IP-RPIR-002"
ERR_RESPONSIBILITY = "IP-RPIR-003"

EXPECTED_LAYER_ROWS = {
    "standard_codex": {
        "order": 1,
        "contract_heading": "### 1. Standard Codex layer",
        "layer_role": "general_execution_substrate",
    },
    "identity_protocol": {
        "order": 2,
        "contract_heading": "### 2. Identity protocol layer",
        "layer_role": "machine_governance_law_layer",
    },
    "identity_instance": {
        "order": 3,
        "contract_heading": "### 3. Identity instance layer",
        "layer_role": "embodied_role_runtime",
    },
    "operator": {
        "order": 4,
        "contract_heading": "### 4. Operator layer",
        "layer_role": "natural_language_collaboration_entry",
    },
}
EXPECTED_RESPONSIBILITY_ROWS = {
    "protocol_layer": {
        "order": 1,
        "contract_heading": "### 1. Protocol-layer obligations",
        "responsibility_role": "defines_the_law_of_the_world",
    },
    "instance_layer": {
        "order": 2,
        "contract_heading": "### 2. Instance-layer obligations",
        "responsibility_role": "continuous_convergence_under_law",
    },
    "operator_surface": {
        "order": 3,
        "contract_heading": "### 3. Operator-surface compression boundary",
        "responsibility_role": "stable_answer_surface_without_memory_burden",
    },
}
EXPECTED_ESCALATION_ROWS = {
    "protocol_semantics_not_unambiguous": {
        "order": 1,
        "contract_phrase": "protocol semantics themselves are not unambiguous.",
    },
    "shared_implementation_contradicts_shared_law": {
        "order": 2,
        "contract_phrase": "shared implementation contradicts shared documentation or shared law.",
    },
    "multi_instance_structural_gap": {
        "order": 3,
        "contract_phrase": "multiple instances will reliably hit the same structural gap.",
    },
    "machine_truth_incomplete": {
        "order": 4,
        "contract_phrase": "machine truth itself is incomplete, so no amount of instance self-repair can achieve alignment.",
    },
}
EXPECTED_ESCALATION_PROOF_ROWS = {
    "semantic_ambiguity_proof": {
        "order": 1,
        "contract_heading": "### 1. Semantic-ambiguity proof",
        "proof_role": "shared_law_semantic_ambiguity_proof",
    },
    "shared_law_contradiction_proof": {
        "order": 2,
        "contract_heading": "### 2. Shared-law contradiction proof",
        "proof_role": "shared_law_implementation_contradiction_proof",
    },
    "multi_instance_structural_gap_proof": {
        "order": 3,
        "contract_heading": "### 3. Multi-instance structural-gap proof",
        "proof_role": "cross_instance_structural_gap_proof",
    },
    "machine_truth_incompleteness_proof": {
        "order": 4,
        "contract_heading": "### 4. Machine-truth incompleteness proof",
        "proof_role": "machine_truth_incompleteness_proof",
    },
}
EXPECTED_ESCALATION_LIMIT_ROWS = {
    "semantic_ambiguity_not_shared_contradiction": {
        "order": 1,
        "contract_phrase": "semantic-ambiguity proof is not proof of shared implementation contradiction;",
    },
    "shared_contradiction_not_multi_instance_gap": {
        "order": 2,
        "contract_phrase": "shared-law contradiction proof is not proof of multi-instance structural gap;",
    },
    "multi_instance_gap_not_machine_truth_incomplete": {
        "order": 3,
        "contract_phrase": "multi-instance structural-gap proof is not proof of machine-truth incompleteness;",
    },
    "machine_truth_incomplete_not_instance_amnesty": {
        "order": 4,
        "contract_phrase": "machine-truth incompleteness proof is not proof that instance convergence duty disappears;",
    },
    "escalation_proof_not_protocol_debt_laundering": {
        "order": 5,
        "contract_phrase": "no escalation proof may launder unproved local residue into protocol debt.",
    },
}
EXPECTED_BOUNDARY_COLLAPSES = {
    "instance_residue_laundering": {
        "order": 1,
        "contract_phrase": "instance residue is relabeled as protocol debt without responsibility proof.",
    },
    "protocol_backstop_laundering": {
        "order": 2,
        "contract_phrase": "the protocol is treated as a shelter for unresolved instance convergence debt.",
    },
    "operator_memory_dumping": {
        "order": 3,
        "contract_phrase": "low-level protocol burden is pushed directly onto the operator instead of being compressed by the governed instance surface.",
    },
    "runtime_authorship_inversion": {
        "order": 4,
        "contract_phrase": "runtime evidence or current vividness is treated as if it authored the upstream law that interprets it.",
    },
    "local_vividness_promotion": {
        "order": 5,
        "contract_phrase": "one local pressure point is treated as sufficient proof of shared-law promotion.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for protocol-vs-instance responsibility law",
    "## Four-layer relation",
    "## Responsibility law",
    "## Escalation admission law",
    "## Escalation-proof discipline",
    "## Escalation-proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn responsibility legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Protocol-instance responsibility row-family completeness must stay explicit",
        "Required layer, responsibility, escalation-trigger, escalation-proof,\nescalation-limit, and boundary-collapse families must remain explicit as\nseparate machine-readable row families.",
        "The machine world must not finalize protocol-instance responsibility legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root protocol-instance responsibility completeness discipline",
        "Protocol-instance responsibility law is not a soft prose bundle.",
        "1. required layer, responsibility, escalation-trigger, escalation-proof, escalation-limit, and boundary-collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root protocol-instance responsibility completeness boundary",
        "1. Protocol-instance responsibility law must remain machine-readable as separate layer, responsibility, escalation-trigger, escalation-proof, escalation-limit, and boundary-collapse row families.",
        "4. Protocol legality must not finalize protocol-instance responsibility legality while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime protocol-instance responsibility consumption boundary",
        "1. Runtime consumes protocol-instance responsibility law as separate layer, responsibility, escalation-trigger, escalation-proof, escalation-limit, and boundary-collapse row families rather than as undifferentiated ownership prose.",
        "4. Runtime must not finalize protocol-instance responsibility legality while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root protocol-instance responsibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    responsibility_doc, responsibility_entry_path, responsibility_active_path, responsibility_alias_error = load_root_protocol_instance_responsibility(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    responsibility_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if responsibility_alias_error:
        stale_reasons.append(f"root_protocol_instance_responsibility_alias_error:{responsibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not responsibility_doc:
        stale_reasons.append("root_protocol_instance_responsibility_empty_or_invalid")
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

    layer_rows = layer_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    owner_rows = responsibility_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    escalation_rows = escalation_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    escalation_proof_rows = escalation_proof_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    escalation_limit_rows = escalation_limit_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    boundary_collapse_rows = boundary_collapse_rows_from_doc(responsibility_doc) if responsibility_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(responsibility_doc) if responsibility_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "responsibility_family": "protocol_root_protocol_instance_responsibility",
            "responsibility_version": "v1",
            "contract_file": "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_protocol_instance_responsibility.py",
            "probe_script": "scripts/ci/run_protocol_root_protocol_instance_responsibility_probes_ci.sh",
            "common_script": "scripts/root_protocol_instance_responsibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(responsibility_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_protocol_instance_responsibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_layer_rows", layer_rows),
            ("required_responsibility_rows", owner_rows),
            ("required_escalation_rows", escalation_rows),
            ("required_escalation_proof_rows", escalation_proof_rows),
            ("required_escalation_limit_rows", escalation_limit_rows),
            ("required_boundary_collapse_rows", boundary_collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_protocol_instance_responsibility_{field}_missing")
                error_code = ERR_REGISTRY
        if not responsibility_doc.get("contract_required_markers"):
            stale_reasons.append("root_protocol_instance_responsibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_protocol_instance_responsibility",
        ):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(responsibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_protocol_instance_responsibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_layer_rows",
                    "member_id_key": "layer_id",
                    "actual_rows": layer_rows,
                    "expected_rows": EXPECTED_LAYER_ROWS,
                    "id_attr": "layer_id",
                },
                {
                    "family_id": "required_responsibility_rows",
                    "member_id_key": "owner_id",
                    "actual_rows": owner_rows,
                    "expected_rows": EXPECTED_RESPONSIBILITY_ROWS,
                    "id_attr": "owner_id",
                },
                {
                    "family_id": "required_escalation_rows",
                    "member_id_key": "trigger_id",
                    "actual_rows": escalation_rows,
                    "expected_rows": EXPECTED_ESCALATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_escalation_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": escalation_proof_rows,
                    "expected_rows": EXPECTED_ESCALATION_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_escalation_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": escalation_limit_rows,
                    "expected_rows": EXPECTED_ESCALATION_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_boundary_collapse_rows",
                    "member_id_key": "collapse_id",
                    "actual_rows": boundary_collapse_rows,
                    "expected_rows": EXPECTED_BOUNDARY_COLLAPSES,
                    "id_attr": "row_id",
                },
            ),
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": layer_rows,
                    "expected_rows": EXPECTED_LAYER_ROWS,
                    "field_name": "required_layer_rows",
                    "id_attr": "layer_id",
                    "compare_fields": ("contract_heading", "layer_role"),
                },
                {
                    "actual_rows": owner_rows,
                    "expected_rows": EXPECTED_RESPONSIBILITY_ROWS,
                    "field_name": "required_responsibility_rows",
                    "id_attr": "owner_id",
                    "compare_fields": ("contract_heading", "responsibility_role"),
                },
                {
                    "actual_rows": escalation_rows,
                    "expected_rows": EXPECTED_ESCALATION_ROWS,
                    "field_name": "required_escalation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": escalation_proof_rows,
                    "expected_rows": EXPECTED_ESCALATION_PROOF_ROWS,
                    "field_name": "required_escalation_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": escalation_limit_rows,
                    "expected_rows": EXPECTED_ESCALATION_LIMIT_ROWS,
                    "field_name": "required_escalation_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": boundary_collapse_rows,
                    "expected_rows": EXPECTED_BOUNDARY_COLLAPSES,
                    "field_name": "required_boundary_collapse_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
            ),
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
        )

        contract_file = str(responsibility_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            responsibility_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(responsibility_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            layer_rows,
                            reason="layer_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            owner_rows,
                            reason="responsibility_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            escalation_proof_rows,
                            reason="escalation_proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            escalation_rows + escalation_limit_rows + boundary_collapse_rows,
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
                mappings_required_children=('root-protocol-instance-responsibility.current.yaml', 'root-protocol-instance-responsibility.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = responsibility_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_RESPONSIBILITY,
        support_reason_prefix="responsibility_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_RESPONSIBILITY),
        "responsibility_entry_path": str(responsibility_entry_path),
        "responsibility_active_path": str(responsibility_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(responsibility_doc.get("contract_file") or ""),
        "layer_count": len(layer_rows),
        "responsibility_count": len(owner_rows),
        "escalation_trigger_count": len(escalation_rows),
        "escalation_proof_count": len(escalation_proof_rows),
        "escalation_limit_count": len(escalation_limit_rows),
        "boundary_collapse_count": len(boundary_collapse_rows),
        **project_root_contract_support_projection(
            prefix="protocol_instance",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "layer_ids": [row.layer_id for row in sorted(layer_rows, key=lambda item: item.order)],
        "owner_ids": [row.owner_id for row in sorted(owner_rows, key=lambda item: item.order)],
        "escalation_trigger_ids": [row.row_id for row in sorted(escalation_rows, key=lambda item: item.order)],
        "escalation_proof_ids": [row.proof_id for row in sorted(escalation_proof_rows, key=lambda item: item.order)],
        "escalation_limit_ids": [row.row_id for row in sorted(escalation_limit_rows, key=lambda item: item.order)],
        "boundary_collapse_ids": [row.row_id for row in sorted(boundary_collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "responsibility_violations": responsibility_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
