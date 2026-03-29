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
from root_identity_instance_self_judgement_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    collapse_rows_from_doc,
    identity_instance_self_judgement_completeness_rows_from_doc,
    load_root_identity_instance_self_judgement,
    question_rows_from_doc,
    readme_identity_instance_self_judgement_completeness_surface,
    self_judgement_limit_rows_from_doc,
    self_judgement_proof_rows_from_doc,
)

STATUS_KEY = "protocol_root_identity_instance_self_judgement_status"
ERR_REGISTRY = "IP-RIISJ-001"
ERR_STRUCTURE = "IP-RIISJ-002"
ERR_JUDGEMENT = "IP-RIISJ-003"

EXPECTED_QUESTION_ROWS = {
    "who_i_am": {
        "order": 1,
        "contract_heading": "### 1. Who I am",
        "judgement_role": "machine_verifiable_identity",
    },
    "what_i_can_do": {
        "order": 2,
        "contract_heading": "### 2. What I can do",
        "judgement_role": "lawful_capability_boundary",
    },
    "how_i_do_it": {
        "order": 3,
        "contract_heading": "### 3. How I do it",
        "judgement_role": "canonical_execution_under_law",
    },
    "when_not_my_place": {
        "order": 4,
        "contract_heading": "### 4. When it is not my place to decide by myself",
        "judgement_role": "escalation_boundary_awareness",
    },
}
EXPECTED_ANCHOR_ROWS = {
    "resolved_identity_context": {
        "order": 1,
        "contract_phrase": "resolved identity context rather than narrative self-claim;",
    },
    "governed_routes_states_receipts_artifacts": {
        "order": 2,
        "contract_phrase": "governed routes, states, receipts, and artifact families rather than abstract capability inflation;",
    },
    "canonical_execution_paths": {
        "order": 3,
        "contract_phrase": "canonical execution paths rather than local convenience paths;",
    },
    "governed_escalation_criteria": {
        "order": 4,
        "contract_phrase": "governed escalation criteria rather than instance preference.",
    },
}
EXPECTED_SELF_JUDGEMENT_PROOF_ROWS = {
    "identity_resolution_self_judgement_proof": {
        "order": 1,
        "contract_heading": "### 1. Identity-resolution self-judgement proof",
        "proof_role": "identity_resolution_self_judgement_proof",
    },
    "capability_boundary_self_judgement_proof": {
        "order": 2,
        "contract_heading": "### 2. Capability-boundary self-judgement proof",
        "proof_role": "capability_boundary_self_judgement_proof",
    },
    "canonical_execution_self_judgement_proof": {
        "order": 3,
        "contract_heading": "### 3. Canonical-execution self-judgement proof",
        "proof_role": "canonical_execution_self_judgement_proof",
    },
    "escalation_boundary_self_judgement_proof": {
        "order": 4,
        "contract_heading": "### 4. Escalation-boundary self-judgement proof",
        "proof_role": "escalation_boundary_self_judgement_proof",
    },
    "non_self_authorization_self_judgement_proof": {
        "order": 5,
        "contract_heading": "### 5. Non-self-authorization proof",
        "proof_role": "non_self_authorization_self_judgement_proof",
    },
}
EXPECTED_SELF_JUDGEMENT_LIMIT_ROWS = {
    "identity_resolution_not_capability_boundary": {
        "order": 1,
        "contract_phrase": "identity-resolution self-judgement proof is not proof of capability boundary;",
    },
    "capability_boundary_not_canonical_execution": {
        "order": 2,
        "contract_phrase": "capability-boundary self-judgement proof is not proof of canonical execution;",
    },
    "canonical_execution_not_escalation_boundary": {
        "order": 3,
        "contract_phrase": "canonical-execution self-judgement proof is not proof of escalation boundary awareness;",
    },
    "escalation_boundary_not_non_self_authorization": {
        "order": 4,
        "contract_phrase": "escalation-boundary self-judgement proof is not proof of non-self-authorization;",
    },
    "non_self_authorization_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "non-self-authorization proof is not proof that the instance may bypass current-turn machine adjudication.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "narrative_identity_substitution": {
        "order": 1,
        "contract_phrase": "narrative self-description is treated as if it were machine-verifiable identity truth.",
    },
    "capability_inflation_without_law": {
        "order": 2,
        "contract_phrase": "abstract model power is treated as if it were lawful identity capability.",
    },
    "local_path_improvisation_as_law": {
        "order": 3,
        "contract_phrase": "convenient local execution paths are treated as equivalent to canonical governed execution.",
    },
    "self_authorized_boundary_crossing": {
        "order": 4,
        "contract_phrase": "the instance decides it may cross a boundary merely because it believes it can.",
    },
    "escalation_avoidance_by_self_confidence": {
        "order": 5,
        "contract_phrase": "an issue requiring escalation is kept local purely because the instance feels confident.",
    },
}
EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS = {
    "explicit_identity_instance_self_judgement_row_families": {
        "order": 1,
        "contract_phrase": "required question, anchor, self-judgement-proof, self-judgement-limit, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_identity_instance_self_judgement_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_identity_instance_self_judgement_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_identity_instance_self_judgement_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_identity_instance_self_judgement_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for identity-instance self-judgement law",
    "## Four self-judgement questions",
    "## Required self-judgement anchors",
    "## Self-judgement proof discipline",
    "## Self-judgement proof limits",
    "## Non-compliant self-judgement collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn self-judgement legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Identity-instance self-judgement row-family completeness must stay explicit",
        "Required question, anchor, self-judgement-proof, self-judgement-limit, and\ncollapse families must remain explicit as separate machine-readable row\nfamilies.",
        "README root identity-instance self-judgement completeness discipline must\ntherefore stay congruent with admitted\nidentity-instance-self-judgement-completeness rows rather than becoming a\nfreehand completeness summary.",
        "The machine world must not finalize identity-instance self-judgement legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root identity-instance self-judgement completeness discipline",
        "Identity-instance self-judgement law is not a soft prose bundle.",
        "These identity-instance-self-judgement-completeness rules must remain bound to canonical identity-instance-self-judgement-completeness rows rather than drifting into soft summary prose.",
        "1. required question, anchor, self-judgement-proof, self-judgement-limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root identity-instance self-judgement completeness boundary",
        "1. Identity-instance self-judgement law must remain machine-readable as separate question, anchor, self-judgement-proof, self-judgement-limit, and collapse row families.",
        "4. Protocol legality must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root identity-instance self-judgement completeness discipline rendered at protocol root must remain congruent with admitted identity-instance-self-judgement-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime identity-instance self-judgement consumption boundary",
        "1. Runtime consumes identity-instance self-judgement law as separate question, anchor, self-judgement-proof, self-judgement-limit, and collapse row families rather than as undifferentiated self-description prose.",
        "4. Runtime must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root identity-instance self-judgement completeness discipline as a governed completeness projection bound to admitted identity-instance-self-judgement-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root identity-instance self-judgement law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    self_doc, self_entry_path, self_active_path, self_alias_error = load_root_identity_instance_self_judgement(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    judgement_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if self_alias_error:
        stale_reasons.append(f"root_identity_instance_self_judgement_alias_error:{self_alias_error}")
        error_code = ERR_REGISTRY
    elif not self_doc:
        stale_reasons.append("root_identity_instance_self_judgement_empty_or_invalid")
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

    question_rows = question_rows_from_doc(self_doc) if self_doc else ()
    anchor_rows = anchor_rows_from_doc(self_doc) if self_doc else ()
    self_judgement_proof_rows = self_judgement_proof_rows_from_doc(self_doc) if self_doc else ()
    self_judgement_limit_rows = self_judgement_limit_rows_from_doc(self_doc) if self_doc else ()
    collapse_rows = collapse_rows_from_doc(self_doc) if self_doc else ()
    identity_instance_self_judgement_completeness_rows = (
        identity_instance_self_judgement_completeness_rows_from_doc(self_doc) if self_doc else ()
    )
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(self_doc) if self_doc else ()
    identity_instance_self_judgement_completeness_surface = (
        readme_identity_instance_self_judgement_completeness_surface(repo_root)
    )
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "self_judgement_family": "protocol_root_identity_instance_self_judgement",
            "self_judgement_version": "v1",
            "contract_file": "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_identity_instance_self_judgement.py",
            "probe_script": "scripts/ci/run_protocol_root_identity_instance_self_judgement_probes_ci.sh",
            "common_script": "scripts/root_identity_instance_self_judgement_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(self_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_identity_instance_self_judgement_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_question_rows", question_rows),
            ("required_anchor_rows", anchor_rows),
            ("required_self_judgement_proof_rows", self_judgement_proof_rows),
            ("required_self_judgement_limit_rows", self_judgement_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_identity_instance_self_judgement_{field}_missing")
                error_code = ERR_REGISTRY
        if not identity_instance_self_judgement_completeness_rows:
            stale_reasons.append("root_identity_instance_self_judgement_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not self_doc.get("contract_required_markers"):
            stale_reasons.append("root_identity_instance_self_judgement_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_identity_instance_self_judgement",
        ):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(self_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_identity_instance_self_judgement_surface_missing:{field}:{rel_path}")
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
                    "family_id": "required_anchor_rows",
                    "member_id_key": "anchor_id",
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_self_judgement_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": self_judgement_proof_rows,
                    "expected_rows": EXPECTED_SELF_JUDGEMENT_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_self_judgement_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": self_judgement_limit_rows,
                    "expected_rows": EXPECTED_SELF_JUDGEMENT_LIMIT_ROWS,
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
                    "family_id": "identity_instance_self_judgement_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": identity_instance_self_judgement_completeness_rows,
                    "expected_rows": {
                        completeness_id: {}
                        for completeness_id in EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "identity_instance_self_judgement_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": identity_instance_self_judgement_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS.values()
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
                    "actual_rows": question_rows,
                    "expected_rows": EXPECTED_QUESTION_ROWS,
                    "field_name": "required_question_rows",
                    "id_attr": "question_id",
                    "compare_fields": ("contract_heading", "judgement_role"),
                },
                {
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "field_name": "required_anchor_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": self_judgement_proof_rows,
                    "expected_rows": EXPECTED_SELF_JUDGEMENT_PROOF_ROWS,
                    "field_name": "required_self_judgement_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": self_judgement_limit_rows,
                    "expected_rows": EXPECTED_SELF_JUDGEMENT_LIMIT_ROWS,
                    "field_name": "required_self_judgement_limit_rows",
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
                    "actual_rows": identity_instance_self_judgement_completeness_rows,
                    "expected_rows": EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS,
                    "field_name": "identity_instance_self_judgement_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_identity_instance_self_judgement_completeness_id",
                    "non_contiguous_reason": "identity_instance_self_judgement_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_identity_instance_self_judgement_completeness_rows",
                    "extra_reason": "extra_identity_instance_self_judgement_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "identity_instance_self_judgement_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": identity_instance_self_judgement_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "identity_instance_self_judgement_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_identity_instance_self_judgement_completeness_surface_phrase",
                    "non_contiguous_reason": "identity_instance_self_judgement_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_identity_instance_self_judgement_completeness_surface_rows",
                    "extra_reason": "extra_identity_instance_self_judgement_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "identity_instance_self_judgement_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
        )

        expected_identity_instance_self_judgement_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS.values()
        ]
        actual_identity_instance_self_judgement_completeness_phrases = [
            row.contract_phrase for row in identity_instance_self_judgement_completeness_surface.rows
        ]
        expected_identity_instance_self_judgement_completeness_orders = [
            int(row["order"]) for row in EXPECTED_IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_ROWS.values()
        ]
        actual_identity_instance_self_judgement_completeness_orders = [
            row.order for row in identity_instance_self_judgement_completeness_surface.rows
        ]
        for reason in identity_instance_self_judgement_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "identity_instance_self_judgement_completeness_surface",
                    "reason": f"identity_instance_self_judgement_completeness_surface_{reason}",
                }
            )
        if actual_identity_instance_self_judgement_completeness_phrases and tuple(
            actual_identity_instance_self_judgement_completeness_phrases
        ) != tuple(expected_identity_instance_self_judgement_completeness_phrases):
            judgement_violations.append(
                {
                    "field": "identity_instance_self_judgement_completeness_surface",
                    "reason": "identity_instance_self_judgement_completeness_surface_phrase_order_mismatch",
                    "expected": expected_identity_instance_self_judgement_completeness_phrases,
                    "actual": actual_identity_instance_self_judgement_completeness_phrases,
                }
            )
        if actual_identity_instance_self_judgement_completeness_orders and tuple(
            actual_identity_instance_self_judgement_completeness_orders
        ) != tuple(expected_identity_instance_self_judgement_completeness_orders):
            judgement_violations.append(
                {
                    "field": "identity_instance_self_judgement_completeness_surface",
                    "reason": "identity_instance_self_judgement_completeness_surface_order_mismatch",
                    "expected": expected_identity_instance_self_judgement_completeness_orders,
                    "actual": actual_identity_instance_self_judgement_completeness_orders,
                }
            )

        contract_file = str(self_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            judgement_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(self_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            question_rows,
                            reason="question_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            self_judgement_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            anchor_rows + self_judgement_limit_rows + collapse_rows,
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
                mappings_required_children=('root-identity-instance-self-judgement.current.yaml', 'root-identity-instance-self-judgement.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = judgement_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_JUDGEMENT,
        support_reason_prefix="self_judgement_violation",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_JUDGEMENT),
        "self_entry_path": str(self_entry_path),
        "self_active_path": str(self_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(self_doc.get("contract_file") or ""),
        "question_count": len(question_rows),
        "anchor_count": len(anchor_rows),
        "self_judgement_proof_count": len(self_judgement_proof_rows),
        "self_judgement_limit_count": len(self_judgement_limit_rows),
        "collapse_count": len(collapse_rows),
        "identity_instance_self_judgement_completeness_row_count": len(
            identity_instance_self_judgement_completeness_rows
        ),
        **project_root_contract_support_projection(
            prefix="self_judgement",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "question_ids": [row.question_id for row in sorted(question_rows, key=lambda item: item.order)],
        "anchor_ids": [row.row_id for row in sorted(anchor_rows, key=lambda item: item.order)],
        "self_judgement_proof_ids": [row.proof_id for row in sorted(self_judgement_proof_rows, key=lambda item: item.order)],
        "self_judgement_limit_ids": [row.row_id for row in sorted(self_judgement_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "identity_instance_self_judgement_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(identity_instance_self_judgement_completeness_rows, key=lambda item: item.order)
        ],
        "identity_instance_self_judgement_completeness_surface": {
            "rel_path": identity_instance_self_judgement_completeness_surface.rel_path,
            "entry_count": len(identity_instance_self_judgement_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in identity_instance_self_judgement_completeness_surface.rows
            ],
            "extraction_violations": list(identity_instance_self_judgement_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "judgement_violations": judgement_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
