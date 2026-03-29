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
from root_entry_surface_legitimacy_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    differentiation_rows_from_doc,
    entry_surface_legitimacy_completeness_rows_from_doc,
    entry_admission_limit_rows_from_doc,
    entry_admission_proof_rows_from_doc,
    entry_class_rows_from_doc,
    load_root_entry_surface_legitimacy,
    readme_entry_surface_legitimacy_completeness_surface,
)

STATUS_KEY = "protocol_root_entry_surface_legitimacy_status"
ERR_REGISTRY = "IP-ESL-001"
ERR_STRUCTURE = "IP-ESL-002"
ERR_ENTRY_LEGITIMACY = "IP-ESL-003"

EXPECTED_ENTRY_CLASS_ROWS = {
    "frozen_entry_definition": {
        "order": 1,
        "contract_heading": "### 1. Frozen entry definition",
        "entry_role": "frozen_entry_definition",
    },
    "natural_language_collaboration_entry_surface": {
        "order": 2,
        "contract_heading": "### 2. Natural-language collaboration entry surface",
        "entry_role": "natural_language_collaboration_entry_surface",
    },
    "governed_execution_entry_surface": {
        "order": 3,
        "contract_heading": "### 3. Governed execution entry surface",
        "entry_role": "governed_execution_entry_surface",
    },
    "governed_recovery_only_entry_surface": {
        "order": 4,
        "contract_heading": "### 4. Governed recovery-only entry surface",
        "entry_role": "governed_recovery_only_entry_surface",
    },
    "discoverability_helper_surface": {
        "order": 5,
        "contract_heading": "### 5. Discoverability-helper surface",
        "entry_role": "discoverability_helper_surface",
    },
    "demoted_support_or_non_entry_surface": {
        "order": 6,
        "contract_heading": "### 6. Demoted support or non-entry surface",
        "entry_role": "demoted_support_or_non_entry_surface",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "frozen_vs_live_execution_entry": {
        "order": 1,
        "contract_phrase": "frozen law-defined entry is separated from live governed execution entry;",
    },
    "operator_vs_machine_execution_entry": {
        "order": 2,
        "contract_phrase": "natural-language collaboration entry is separated from machine execution entry;",
    },
    "execution_vs_recovery_entry": {
        "order": 3,
        "contract_phrase": "governed execution entry is separated from governed recovery-only entry;",
    },
    "helper_vs_canonical_execution_entry": {
        "order": 4,
        "contract_phrase": "discoverability-helper surface is separated from canonical execution entry;",
    },
    "support_vs_active_entry_surface": {
        "order": 5,
        "contract_phrase": "demoted support or non-entry surface is separated from any active entry surface;",
    },
    "visibility_vs_entry_admission": {
        "order": 6,
        "contract_phrase": "visible installation or discoverability is separated from lawful entry admission.",
    },
}
EXPECTED_ENTRY_ADMISSION_PROOF_ROWS = {
    "frozen_definition_entry_admission_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-definition entry-admission proof",
        "proof_role": "frozen_definition_entry_admission_proof",
    },
    "collaboration_boundary_entry_admission_proof": {
        "order": 2,
        "contract_heading": "### 2. Collaboration-boundary entry-admission proof",
        "proof_role": "collaboration_boundary_entry_admission_proof",
    },
    "governed_execution_entry_admission_proof": {
        "order": 3,
        "contract_heading": "### 3. Governed-execution entry-admission proof",
        "proof_role": "governed_execution_entry_admission_proof",
    },
    "recovery_confinement_entry_admission_proof": {
        "order": 4,
        "contract_heading": "### 4. Recovery-confinement entry-admission proof",
        "proof_role": "recovery_confinement_entry_admission_proof",
    },
    "helper_support_demotion_entry_admission_proof": {
        "order": 5,
        "contract_heading": "### 5. Helper/support-demotion entry-admission proof",
        "proof_role": "helper_support_demotion_entry_admission_proof",
    },
}
EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS = {
    "frozen_definition_not_collaboration_boundary": {
        "order": 1,
        "contract_phrase": "frozen-definition entry-admission proof is not proof of collaboration-boundary preservation;",
    },
    "collaboration_boundary_not_governed_execution": {
        "order": 2,
        "contract_phrase": "collaboration-boundary entry-admission proof is not proof of governed execution entry;",
    },
    "governed_execution_not_recovery_confinement": {
        "order": 3,
        "contract_phrase": "governed-execution entry-admission proof is not proof of recovery confinement;",
    },
    "recovery_confinement_not_helper_support_demotion": {
        "order": 4,
        "contract_phrase": "recovery-confinement entry-admission proof is not proof of helper or support demotion;",
    },
    "helper_support_demotion_not_lawful_active_execution_entry": {
        "order": 5,
        "contract_phrase": "helper/support-demotion entry-admission proof is not proof of lawful active execution entry.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "declared_entry_as_live_execution_entry": {
        "order": 1,
        "contract_phrase": "a law-defined or declared entry surface is treated as if it were already live governed execution entry.",
    },
    "operator_surface_as_machine_execution_entry": {
        "order": 2,
        "contract_phrase": "the operator collaboration surface is treated as if it were sufficient machine execution entry.",
    },
    "recovery_entry_as_primary_execution_entry": {
        "order": 3,
        "contract_phrase": "a recovery, replay, diagnostics, or repair entry surface is treated as if it were the canonical primary execution entry.",
    },
    "helper_surface_as_canonical_entry": {
        "order": 4,
        "contract_phrase": "a helper path, discoverability aid, or installation alias is treated as if it were canonical execution entry.",
    },
    "support_surface_as_active_entry": {
        "order": 5,
        "contract_phrase": "a demoted support or non-entry surface is treated as if it were active execution entry.",
    },
    "installation_visibility_as_entry_legality": {
        "order": 6,
        "contract_phrase": "visibility, installation presence, or easy discovery is treated as if it proved lawful entry admission.",
    },
}
EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS = {
    "explicit_entry_surface_legitimacy_row_families": {
        "order": 1,
        "contract_phrase": "required entry-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_entry_surface_legitimacy_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_entry_surface_legitimacy_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_entry_surface_legitimacy_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize entry-surface legitimacy truth while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_entry_surface_legitimacy_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for entry-surface legitimacy law",
    "## Entry-surface legitimacy law",
    "## Six entry classes",
    "## Required entry differentiations",
    "## Entry-admission proof discipline",
    "## Entry-admission proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Entry-surface legitimacy row-family completeness must stay explicit",
        "Required entry-class, differentiation, proof, limit, and collapse\nfamilies must remain explicit as separate machine-readable row families.",
        "README root entry-surface legitimacy completeness discipline must\ntherefore stay congruent with admitted\nentry-surface-legitimacy-completeness rows rather than becoming a freehand\ncompleteness summary.",
        "The machine world must not finalize entry-surface legitimacy while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root entry-surface legitimacy completeness discipline",
        "Entry-surface legitimacy law is not a soft prose bundle.",
        "These entry-surface-legitimacy-completeness rules must remain bound to canonical entry-surface-legitimacy-completeness rows rather than drifting into soft summary prose.",
        "1. required entry-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root entry-surface legitimacy completeness boundary",
        "1. Entry-surface legitimacy law must remain machine-readable as separate entry-class, differentiation, proof, limit, and collapse row families.",
        "4. Protocol legality must not finalize entry-surface legitimacy truth while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root entry-surface legitimacy completeness discipline rendered at protocol root must remain congruent with admitted entry-surface-legitimacy-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime entry-surface legitimacy consumption boundary",
        "1. Runtime consumes entry-surface legitimacy law as separate entry-class, differentiation, proof, limit, and collapse row families rather than as undifferentiated legitimacy prose.",
        "4. Runtime must not finalize entry-surface legitimacy while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root entry-surface legitimacy completeness discipline as a governed completeness projection bound to admitted entry-surface-legitimacy-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root entry-surface legitimacy law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    entry_doc, entry_entry_path, entry_active_path, entry_alias_error = load_root_entry_surface_legitimacy(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    legitimacy_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if entry_alias_error:
        stale_reasons.append(f"root_entry_surface_legitimacy_alias_error:{entry_alias_error}")
        error_code = ERR_REGISTRY
    elif not entry_doc:
        stale_reasons.append("root_entry_surface_legitimacy_empty_or_invalid")
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

    entry_class_rows = entry_class_rows_from_doc(entry_doc) if entry_doc else ()
    differentiation_rows = differentiation_rows_from_doc(entry_doc) if entry_doc else ()
    entry_admission_proof_rows = entry_admission_proof_rows_from_doc(entry_doc) if entry_doc else ()
    entry_admission_limit_rows = entry_admission_limit_rows_from_doc(entry_doc) if entry_doc else ()
    collapse_rows = collapse_rows_from_doc(entry_doc) if entry_doc else ()
    entry_surface_legitimacy_completeness_rows = (
        entry_surface_legitimacy_completeness_rows_from_doc(entry_doc) if entry_doc else ()
    )
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(entry_doc) if entry_doc else ()
    entry_surface_legitimacy_completeness_surface = readme_entry_surface_legitimacy_completeness_surface(repo_root)
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "entry_family": "protocol_root_entry_surface_legitimacy",
            "entry_version": "v1",
            "contract_file": "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_entry_surface_legitimacy.py",
            "probe_script": "scripts/ci/run_protocol_root_entry_surface_legitimacy_probes_ci.sh",
            "common_script": "scripts/root_entry_surface_legitimacy_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(entry_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_entry_surface_legitimacy_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_entry_class_rows", entry_class_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_entry_admission_proof_rows", entry_admission_proof_rows),
            ("required_entry_admission_limit_rows", entry_admission_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_entry_surface_legitimacy_{field}_missing")
                error_code = ERR_REGISTRY
        if not entry_surface_legitimacy_completeness_rows:
            stale_reasons.append("root_entry_surface_legitimacy_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not entry_doc.get("contract_required_markers"):
            stale_reasons.append("root_entry_surface_legitimacy_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_entry_surface_legitimacy",
        ):
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(entry_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_entry_surface_legitimacy_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_entry_class_rows",
                    "member_id_key": "entry_class_id",
                    "actual_rows": entry_class_rows,
                    "expected_rows": EXPECTED_ENTRY_CLASS_ROWS,
                    "id_attr": "entry_class_id",
                },
                {
                    "family_id": "required_differentiation_rows",
                    "member_id_key": "differentiation_id",
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_entry_admission_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": entry_admission_proof_rows,
                    "expected_rows": EXPECTED_ENTRY_ADMISSION_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_entry_admission_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": entry_admission_limit_rows,
                    "expected_rows": EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS,
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
                    "family_id": "entry_surface_legitimacy_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": entry_surface_legitimacy_completeness_rows,
                    "expected_rows": {
                        completeness_id: {}
                        for completeness_id in EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "entry_surface_legitimacy_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": entry_surface_legitimacy_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS.values()
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
                    "actual_rows": entry_class_rows,
                    "expected_rows": EXPECTED_ENTRY_CLASS_ROWS,
                    "field_name": "required_entry_class_rows",
                    "id_attr": "entry_class_id",
                    "compare_fields": ("contract_heading", "entry_role"),
                },
                {
                    "actual_rows": differentiation_rows,
                    "expected_rows": EXPECTED_DIFFERENTIATION_ROWS,
                    "field_name": "required_differentiation_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": entry_admission_proof_rows,
                    "expected_rows": EXPECTED_ENTRY_ADMISSION_PROOF_ROWS,
                    "field_name": "required_entry_admission_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": entry_admission_limit_rows,
                    "expected_rows": EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS,
                    "field_name": "required_entry_admission_limit_rows",
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
                    "actual_rows": entry_surface_legitimacy_completeness_rows,
                    "expected_rows": EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS,
                    "field_name": "entry_surface_legitimacy_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_entry_surface_legitimacy_completeness_id",
                    "non_contiguous_reason": "entry_surface_legitimacy_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_entry_surface_legitimacy_completeness_rows",
                    "extra_reason": "extra_entry_surface_legitimacy_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "entry_surface_legitimacy_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": entry_surface_legitimacy_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "entry_surface_legitimacy_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_entry_surface_legitimacy_completeness_surface_phrase",
                    "non_contiguous_reason": "entry_surface_legitimacy_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_entry_surface_legitimacy_completeness_surface_rows",
                    "extra_reason": "extra_entry_surface_legitimacy_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "entry_surface_legitimacy_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
        )

        expected_entry_surface_legitimacy_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS.values()
        ]
        actual_entry_surface_legitimacy_completeness_phrases = [
            row.contract_phrase for row in entry_surface_legitimacy_completeness_surface.rows
        ]
        expected_entry_surface_legitimacy_completeness_orders = [
            int(row["order"]) for row in EXPECTED_ENTRY_SURFACE_LEGITIMACY_COMPLETENESS_ROWS.values()
        ]
        actual_entry_surface_legitimacy_completeness_orders = [
            row.order for row in entry_surface_legitimacy_completeness_surface.rows
        ]
        for reason in entry_surface_legitimacy_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "entry_surface_legitimacy_completeness_surface",
                    "reason": f"entry_surface_legitimacy_completeness_surface_{reason}",
                }
            )
        if actual_entry_surface_legitimacy_completeness_phrases and tuple(
            actual_entry_surface_legitimacy_completeness_phrases
        ) != tuple(expected_entry_surface_legitimacy_completeness_phrases):
            legitimacy_violations.append(
                {
                    "field": "entry_surface_legitimacy_completeness_surface",
                    "reason": "entry_surface_legitimacy_completeness_surface_phrase_order_mismatch",
                    "expected": expected_entry_surface_legitimacy_completeness_phrases,
                    "actual": actual_entry_surface_legitimacy_completeness_phrases,
                }
            )
        if actual_entry_surface_legitimacy_completeness_orders and tuple(
            actual_entry_surface_legitimacy_completeness_orders
        ) != tuple(expected_entry_surface_legitimacy_completeness_orders):
            legitimacy_violations.append(
                {
                    "field": "entry_surface_legitimacy_completeness_surface",
                    "reason": "entry_surface_legitimacy_completeness_surface_order_mismatch",
                    "expected": expected_entry_surface_legitimacy_completeness_orders,
                    "actual": actual_entry_surface_legitimacy_completeness_orders,
                }
            )

        contract_file = str(entry_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            legitimacy_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(entry_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            entry_class_rows,
                            reason="entry_class_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            entry_admission_proof_rows,
                            reason="proof_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            differentiation_rows + entry_admission_limit_rows + collapse_rows,
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
                mappings_required_children=('root-entry-surface-legitimacy.current.yaml', 'root-entry-surface-legitimacy.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = legitimacy_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_ENTRY_LEGITIMACY,
        support_reason_prefix="entry_surface_legitimacy_violation",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ENTRY_LEGITIMACY),
        "entry_entry_path": str(entry_entry_path),
        "entry_active_path": str(entry_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(entry_doc.get("contract_file") or ""),
        "entry_class_count": len(entry_class_rows),
        "differentiation_count": len(differentiation_rows),
        "entry_admission_proof_count": len(entry_admission_proof_rows),
        "entry_admission_limit_count": len(entry_admission_limit_rows),
        "collapse_count": len(collapse_rows),
        "entry_surface_legitimacy_completeness_row_count": len(entry_surface_legitimacy_completeness_rows),
        **project_root_contract_support_projection(
            prefix="entry_surface",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "entry_class_ids": [row.entry_class_id for row in sorted(entry_class_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "entry_admission_proof_ids": [row.proof_id for row in sorted(entry_admission_proof_rows, key=lambda item: item.order)],
        "entry_admission_limit_ids": [row.row_id for row in sorted(entry_admission_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "entry_surface_legitimacy_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(entry_surface_legitimacy_completeness_rows, key=lambda item: item.order)
        ],
        "entry_surface_legitimacy_completeness_surface": {
            "rel_path": entry_surface_legitimacy_completeness_surface.rel_path,
            "entry_count": len(entry_surface_legitimacy_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in entry_surface_legitimacy_completeness_surface.rows
            ],
            "extraction_violations": list(entry_surface_legitimacy_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "legitimacy_violations": legitimacy_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
