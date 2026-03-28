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
from root_truth_lifecycle_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    differentiation_rows_from_doc,
    lifecycle_rows_from_doc,
    load_root_truth_lifecycle,
    memory_strata_rows_from_doc,
    truth_lifecycle_limit_rows_from_doc,
    truth_lifecycle_proof_rows_from_doc,
)

STATUS_KEY = "protocol_root_truth_lifecycle_status"
ERR_REGISTRY = "IP-RTLC-001"
ERR_STRUCTURE = "IP-RTLC-002"
ERR_TRUTH = "IP-RTLC-003"

EXPECTED_LIFECYCLE_ROWS = {
    "truth_exists": {
        "order": 1,
        "contract_heading": "### 1. Truth exists in protocol law",
        "lifecycle_role": "truth_exists",
    },
    "truth_discoverable": {
        "order": 2,
        "contract_heading": "### 2. Truth is discoverable by instance",
        "lifecycle_role": "truth_discoverable",
    },
    "truth_admissible": {
        "order": 3,
        "contract_heading": "### 3. Truth is admissible as current-turn authority",
        "lifecycle_role": "truth_admissible",
    },
    "truth_bound": {
        "order": 4,
        "contract_heading": "### 4. Truth is bound to current run / current thread",
        "lifecycle_role": "truth_bound",
    },
    "truth_consumed": {
        "order": 5,
        "contract_heading": "### 5. Truth is consumed by the next operational step",
        "lifecycle_role": "truth_consumed",
    },
}
EXPECTED_MEMORY_STRATA_ROWS = {
    "law_memory": {
        "order": 1,
        "contract_heading": "### 1. Law memory",
        "memory_role": "law_memory",
    },
    "discovery_memory": {
        "order": 2,
        "contract_heading": "### 2. Discovery memory",
        "memory_role": "discovery_memory",
    },
    "admissibility_memory": {
        "order": 3,
        "contract_heading": "### 3. Admissibility memory",
        "memory_role": "admissibility_memory",
    },
    "run_binding_memory": {
        "order": 4,
        "contract_heading": "### 4. Run-binding memory",
        "memory_role": "run_binding_memory",
    },
    "consumption_memory": {
        "order": 5,
        "contract_heading": "### 5. Consumption memory",
        "memory_role": "consumption_memory",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "existence_vs_discovery": {
        "order": 1,
        "contract_phrase": "truth exists in protocol law ≠ the instance has actually discovered it;",
    },
    "discovery_vs_admissibility": {
        "order": 2,
        "contract_phrase": "the instance discovered it ≠ it is admissible as current-turn authority;",
    },
    "admissibility_vs_binding": {
        "order": 3,
        "contract_phrase": "it is admissible as current-turn authority ≠ it is bound to the current run / current thread;",
    },
    "binding_vs_consumption": {
        "order": 4,
        "contract_phrase": "it is bound to the current run / current thread ≠ the next operational step has actually consumed it;",
    },
    "artifact_vs_operational_closure": {
        "order": 5,
        "contract_phrase": "some artifact or declaration exists ≠ full operational closure has been achieved.",
    },
}
EXPECTED_TRUTH_LIFECYCLE_PROOF_ROWS = {
    "law_existence_proof": {
        "order": 1,
        "contract_heading": "### 1. Law-existence proof",
        "proof_role": "law_existence_truth_lifecycle_proof",
    },
    "canonical_discovery_proof": {
        "order": 2,
        "contract_heading": "### 2. Canonical-discovery proof",
        "proof_role": "canonical_discovery_truth_lifecycle_proof",
    },
    "current_turn_admissibility_proof": {
        "order": 3,
        "contract_heading": "### 3. Current-turn-admissibility proof",
        "proof_role": "current_turn_admissibility_truth_lifecycle_proof",
    },
    "run_thread_binding_proof": {
        "order": 4,
        "contract_heading": "### 4. Run-thread-binding proof",
        "proof_role": "run_thread_binding_truth_lifecycle_proof",
    },
    "next_hop_consumption_proof": {
        "order": 5,
        "contract_heading": "### 5. Next-hop-consumption proof",
        "proof_role": "next_hop_consumption_truth_lifecycle_proof",
    },
}
EXPECTED_TRUTH_LIFECYCLE_LIMIT_ROWS = {
    "law_existence_not_canonical_discovery": {
        "order": 1,
        "contract_phrase": "law-existence proof is not proof of canonical discovery;",
    },
    "canonical_discovery_not_current_turn_admissibility": {
        "order": 2,
        "contract_phrase": "canonical-discovery proof is not proof of current-turn admissibility;",
    },
    "current_turn_admissibility_not_run_thread_binding": {
        "order": 3,
        "contract_phrase": "current-turn-admissibility proof is not proof of run/thread binding;",
    },
    "run_thread_binding_not_next_hop_consumption": {
        "order": 4,
        "contract_phrase": "run-thread-binding proof is not proof of next-hop consumption;",
    },
    "next_hop_consumption_not_lifecycle_bypass": {
        "order": 5,
        "contract_phrase": "next-hop-consumption proof is not proof that lifecycle closure may be claimed when earlier stages were missing or bypassed.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "existence_equals_discovery": {
        "order": 1,
        "contract_phrase": "shared-law existence is treated as if the instance has already discovered the truth.",
    },
    "discovery_equals_admissibility": {
        "order": 2,
        "contract_phrase": "discovery alone is treated as if current-turn authority has already been granted.",
    },
    "admissibility_equals_binding": {
        "order": 3,
        "contract_phrase": "admissibility is treated as if current-run or current-thread binding has already happened.",
    },
    "binding_equals_consumption": {
        "order": 4,
        "contract_phrase": "bound truth is treated as if the next hop has already consumed it.",
    },
    "artifact_presence_equals_operational_closure": {
        "order": 5,
        "contract_phrase": "the existence of an artifact or declaration is treated as full operational closure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for truth-lifecycle law",
    "## Truth-lifecycle law",
    "## Five lifecycle stages",
    "## Memory-bearing lifecycle strata",
    "## Required lifecycle differentiations",
    "## Truth-lifecycle proof discipline",
    "## Truth-lifecycle proof limits",
    "## Non-compliant lifecycle collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn truth lifecycle legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Truth-lifecycle row-family completeness must stay explicit",
        "Required lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize truth-lifecycle legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root truth-lifecycle completeness discipline",
        "Truth-lifecycle law is not a soft prose bundle.",
        "1. required lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root truth-lifecycle completeness boundary",
        "1. Truth-lifecycle law must remain machine-readable as separate lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse row families.",
        "4. Protocol legality must not finalize truth-lifecycle legality while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime truth-lifecycle consumption boundary",
        "1. Runtime consumes truth-lifecycle law as separate lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse row families rather than as undifferentiated lifecycle prose.",
        "4. Runtime must not finalize truth-lifecycle legality while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root truth-lifecycle law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    truth_doc, truth_entry_path, truth_active_path, truth_alias_error = load_root_truth_lifecycle(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    truth_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if truth_alias_error:
        stale_reasons.append(f"root_truth_lifecycle_alias_error:{truth_alias_error}")
        error_code = ERR_REGISTRY
    elif not truth_doc:
        stale_reasons.append("root_truth_lifecycle_empty_or_invalid")
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

    lifecycle_rows = lifecycle_rows_from_doc(truth_doc) if truth_doc else ()
    memory_strata_rows = memory_strata_rows_from_doc(truth_doc) if truth_doc else ()
    differentiation_rows = differentiation_rows_from_doc(truth_doc) if truth_doc else ()
    truth_lifecycle_proof_rows = truth_lifecycle_proof_rows_from_doc(truth_doc) if truth_doc else ()
    truth_lifecycle_limit_rows = truth_lifecycle_limit_rows_from_doc(truth_doc) if truth_doc else ()
    collapse_rows = collapse_rows_from_doc(truth_doc) if truth_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(truth_doc) if truth_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "truth_lifecycle_family": "protocol_root_truth_lifecycle",
            "truth_lifecycle_version": "v1",
            "contract_file": "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_truth_lifecycle.py",
            "probe_script": "scripts/ci/run_protocol_root_truth_lifecycle_probes_ci.sh",
            "common_script": "scripts/root_truth_lifecycle_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(truth_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_truth_lifecycle_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_lifecycle_rows", lifecycle_rows),
            ("required_memory_strata_rows", memory_strata_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_truth_lifecycle_proof_rows", truth_lifecycle_proof_rows),
            ("required_truth_lifecycle_limit_rows", truth_lifecycle_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_truth_lifecycle_{field}_missing")
                error_code = ERR_REGISTRY
        if not truth_doc.get("contract_required_markers"):
            stale_reasons.append("root_truth_lifecycle_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_truth_lifecycle",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(truth_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_truth_lifecycle_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_lifecycle_rows",
                    "member_id_key": "lifecycle_id",
                    "actual_rows": lifecycle_rows,
                    "expected_rows": EXPECTED_LIFECYCLE_ROWS,
                    "id_attr": "lifecycle_id",
                },
                {
                    "family_id": "required_memory_strata_rows",
                    "member_id_key": "memory_id",
                    "actual_rows": memory_strata_rows,
                    "expected_rows": EXPECTED_MEMORY_STRATA_ROWS,
                    "id_attr": "memory_id",
                },
                {
                    "family_id": "required_differentiation_rows",
                    "member_id_key": "differentiation_id",
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_truth_lifecycle_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": truth_lifecycle_proof_rows,
                    "expected_rows": EXPECTED_TRUTH_LIFECYCLE_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_truth_lifecycle_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": truth_lifecycle_limit_rows,
                    "expected_rows": EXPECTED_TRUTH_LIFECYCLE_LIMIT_ROWS,
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
                    "actual_rows": lifecycle_rows,
                    "expected_rows": EXPECTED_LIFECYCLE_ROWS,
                    "field_name": "required_lifecycle_rows",
                    "id_attr": "lifecycle_id",
                    "compare_fields": ("contract_heading", "lifecycle_role"),
                },
                {
                    "actual_rows": memory_strata_rows,
                    "expected_rows": EXPECTED_MEMORY_STRATA_ROWS,
                    "field_name": "required_memory_strata_rows",
                    "id_attr": "memory_id",
                    "compare_fields": ("contract_heading", "memory_role"),
                },
                {
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "field_name": "required_differentiation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": truth_lifecycle_proof_rows,
                    "expected_rows": EXPECTED_TRUTH_LIFECYCLE_PROOF_ROWS,
                    "field_name": "required_truth_lifecycle_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": truth_lifecycle_limit_rows,
                    "expected_rows": EXPECTED_TRUTH_LIFECYCLE_LIMIT_ROWS,
                    "field_name": "required_truth_lifecycle_limit_rows",
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
            truth_violations=truth_violations,
        )

        contract_file = str(truth_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            truth_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(truth_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            lifecycle_rows,
                            reason="lifecycle_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            memory_strata_rows,
                            reason="memory_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            truth_lifecycle_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            differentiation_rows + truth_lifecycle_limit_rows + collapse_rows,
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
                mappings_required_children=('root-truth-lifecycle.current.yaml', 'root-truth-lifecycle.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = truth_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_TRUTH,
        support_reason_prefix="truth_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_TRUTH),
        "truth_entry_path": str(truth_entry_path),
        "truth_active_path": str(truth_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(truth_doc.get("contract_file") or ""),
        "lifecycle_count": len(lifecycle_rows),
        "memory_strata_count": len(memory_strata_rows),
        "differentiation_count": len(differentiation_rows),
        "truth_lifecycle_proof_count": len(truth_lifecycle_proof_rows),
        "truth_lifecycle_limit_count": len(truth_lifecycle_limit_rows),
        "collapse_count": len(collapse_rows),
        **project_root_contract_support_projection(
            prefix="truth_lifecycle",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "lifecycle_ids": [row.lifecycle_id for row in sorted(lifecycle_rows, key=lambda item: item.order)],
        "memory_strata_ids": [row.memory_id for row in sorted(memory_strata_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "truth_lifecycle_proof_ids": [row.proof_id for row in sorted(truth_lifecycle_proof_rows, key=lambda item: item.order)],
        "truth_lifecycle_limit_ids": [row.row_id for row in sorted(truth_lifecycle_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "truth_violations": truth_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
