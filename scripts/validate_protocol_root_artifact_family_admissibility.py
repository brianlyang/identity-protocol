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
from root_artifact_family_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    artifact_family_admissibility_completeness_rows_from_doc,
    collapse_rows_from_doc,
    family_admission_class_rows_from_doc,
    family_admission_limit_rows_from_doc,
    family_admission_proof_rows_from_doc,
    differentiation_rows_from_doc,
    load_root_artifact_family_admissibility,
    readme_artifact_family_admissibility_completeness_surface,
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

STATUS_KEY = "protocol_root_artifact_family_admissibility_status"
ERR_REGISTRY = "IP-AFA-001"
ERR_STRUCTURE = "IP-AFA-002"
ERR_ADMISSIBILITY = "IP-AFA-003"

EXPECTED_FAMILY_ADMISSION_CLASS_ROWS = {
    "frozen_artifact_family_definition": {"order": 1, "contract_heading": "### 1. Frozen artifact-family definition", "admission_role": "frozen_artifact_family_definition"},
    "canonical_family_sink": {"order": 2, "contract_heading": "### 2. Canonical family sink", "admission_role": "canonical_family_sink"},
    "family_compatible_artifact": {"order": 3, "contract_heading": "### 3. Family-compatible artifact", "admission_role": "family_compatible_artifact"},
    "bound_family_admitted_artifact": {"order": 4, "contract_heading": "### 4. Bound family-admitted artifact", "admission_role": "bound_family_admitted_artifact"},
    "governed_recovery_or_redirect_sink": {"order": 5, "contract_heading": "### 5. Governed recovery or redirect sink", "admission_role": "governed_recovery_or_redirect_sink"},
    "demoted_support_or_quarantine_sink": {"order": 6, "contract_heading": "### 6. Demoted support or quarantine sink", "admission_role": "demoted_support_or_quarantine_sink"},
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "frozen_definition_vs_canonical_sink": {"order": 1, "contract_phrase": "frozen artifact-family definition is separated from canonical family sink;"},
    "canonical_sink_vs_compatible_artifact": {"order": 2, "contract_phrase": "canonical family sink is separated from family-compatible artifact;"},
    "compatible_artifact_vs_bound_admission": {"order": 3, "contract_phrase": "family-compatible artifact is separated from bound family-admitted artifact;"},
    "bound_admission_vs_redirect_sink": {"order": 4, "contract_phrase": "bound family-admitted artifact is separated from governed recovery or redirect sink;"},
    "redirect_sink_vs_demoted_sink": {"order": 5, "contract_phrase": "governed recovery or redirect sink is separated from demoted support or quarantine sink;"},
    "visible_presence_vs_family_admission": {"order": 6, "contract_phrase": "visible path, filename similarity, or artifact presence is separated from lawful family admission."},
}
EXPECTED_FAMILY_ADMISSION_PROOF_ROWS = {
    "frozen_definition_family_admission_proof": {"order": 1, "contract_heading": "### 1. Frozen-definition family-admission proof", "proof_role": "frozen_definition_family_admission_proof"},
    "canonical_sink_family_admission_proof": {"order": 2, "contract_heading": "### 2. Canonical-sink family-admission proof", "proof_role": "canonical_sink_family_admission_proof"},
    "compatibility_family_admission_proof": {"order": 3, "contract_heading": "### 3. Compatibility family-admission proof", "proof_role": "compatibility_family_admission_proof"},
    "bound_admission_family_admission_proof": {"order": 4, "contract_heading": "### 4. Bound-admission family-admission proof", "proof_role": "bound_admission_family_admission_proof"},
    "redirect_recovery_family_admission_proof": {"order": 5, "contract_heading": "### 5. Redirect-recovery family-admission proof", "proof_role": "redirect_recovery_family_admission_proof"},
    "demotion_quarantine_family_admission_proof": {"order": 6, "contract_heading": "### 6. Demotion-quarantine family-admission proof", "proof_role": "demotion_quarantine_family_admission_proof"},
}
EXPECTED_FAMILY_ADMISSION_LIMIT_ROWS = {
    "frozen_definition_not_canonical_sink": {"order": 1, "contract_phrase": "frozen-definition family-admission proof is not proof of canonical sink resolution;"},
    "canonical_sink_not_compatibility": {"order": 2, "contract_phrase": "canonical-sink family-admission proof is not proof of artifact compatibility;"},
    "compatibility_not_bound_admission": {"order": 3, "contract_phrase": "compatibility family-admission proof is not proof of bound family admission;"},
    "bound_admission_not_redirect_recovery": {"order": 4, "contract_phrase": "bound-admission family-admission proof is not proof of governed redirect or recovery classification;"},
    "redirect_recovery_not_demotion_quarantine": {"order": 5, "contract_phrase": "redirect-recovery family-admission proof is not proof of demotion or quarantine confinement;"},
    "demotion_quarantine_not_canonical_admission": {"order": 6, "contract_phrase": "demotion-quarantine family-admission proof is not proof of lawful canonical family admission."},
}
EXPECTED_COLLAPSE_ROWS = {
    "defined_family_as_live_sink": {"order": 1, "contract_phrase": "a law-defined artifact family is treated as if it were already a live canonical family sink."},
    "artifact_resemblance_as_family_compatibility": {"order": 2, "contract_phrase": "filename resemblance, path similarity, or local habit is treated as if it proved family compatibility."},
    "compatible_artifact_as_admitted_artifact": {"order": 3, "contract_phrase": "a merely compatible artifact is treated as if it were already canonically admitted."},
    "redirect_sink_as_canonical_admission": {"order": 4, "contract_phrase": "a governed recovery, replay, repair, or redirect sink is treated as if it were canonical family admission."},
    "demoted_sink_as_canonical_family_sink": {"order": 5, "contract_phrase": "sample, fixture, diagnostics, archive, compatibility, explanatory, or quarantine material is treated as if it were canonical family admission."},
    "path_presence_as_family_admissibility_proof": {"order": 6, "contract_phrase": "visible path presence, filename visibility, or artifact existence is treated as if it proved lawful family admission."},
}
EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS = {
    "explicit_artifact_family_admissibility_row_families": {"order": 1, "contract_phrase": "required family-admission-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;"},
    "congruent_artifact_family_admissibility_row_family_totals": {"order": 2, "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"},
    "explicit_artifact_family_admissibility_row_identity_sets": {"order": 3, "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;"},
    "hidden_artifact_family_admissibility_identity_drift_forbidden": {"order": 4, "contract_phrase": "runtime or validator code must not finalize artifact-family admissibility while missing or unexpected row identities remain known only internally;"},
    "fail_close_preserves_artifact_family_admissibility_identity_projection": {"order": 5, "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure."},
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for artifact-family admissibility law",
    "## Artifact-family admissibility law",
    "## Six family-admission classes",
    "## Required family-admission differentiations",
    "## Family-admission proof discipline",
    "## Family-admission proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn artifact-family admissibility must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Artifact-family admissibility row-family completeness must stay explicit",
        "Required family-admission-class, differentiation, proof, limit, and collapse families must remain explicit as separate machine-readable row families.",
        "README root artifact-family admissibility completeness discipline must therefore stay congruent with admitted artifact-family-admissibility-completeness rows rather than becoming a freehand completeness summary.",
        "The machine world must not finalize artifact-family admissibility while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root artifact-family admissibility completeness discipline",
        "Artifact-family admissibility law is not a soft prose bundle.",
        "These artifact-family-admissibility-completeness rules must remain bound to canonical artifact-family-admissibility-completeness rows rather than drifting into soft summary prose.",
        "1. required family-admission-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root artifact-family admissibility completeness boundary",
        "1. Artifact-family admissibility law must remain machine-readable as separate family-admission-class, differentiation, proof, limit, and collapse row families.",
        "4. Protocol legality must not finalize artifact-family admissibility while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root artifact-family admissibility completeness discipline rendered at protocol root must remain congruent with admitted artifact-family-admissibility-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime artifact-family admissibility consumption boundary",
        "1. Runtime consumes artifact-family admissibility law as separate family-admission-class, differentiation, proof, limit, and collapse row families rather than as undifferentiated admissibility prose.",
        "4. Runtime must not finalize artifact-family admissibility while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root artifact-family admissibility completeness discipline as a governed completeness projection bound to admitted artifact-family-admissibility-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root artifact-family admissibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = load_root_artifact_family_admissibility(repo_root)
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
    row_family_projection_by_id: dict[str, dict[str, Any]] = {}
    error_code = ""

    if admissibility_alias_error:
        stale_reasons.append(f"root_artifact_family_admissibility_alias_error:{admissibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not admissibility_doc:
        stale_reasons.append("root_artifact_family_admissibility_empty_or_invalid")
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

    family_admission_class_rows = family_admission_class_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    differentiation_rows = differentiation_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    family_admission_proof_rows = family_admission_proof_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    family_admission_limit_rows = family_admission_limit_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    collapse_rows = collapse_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    artifact_family_admissibility_completeness_rows = artifact_family_admissibility_completeness_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(admissibility_doc) if admissibility_doc else ()
    artifact_family_admissibility_completeness_surface = readme_artifact_family_admissibility_completeness_surface(repo_root)
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "artifact_family_admissibility_family": "protocol_root_artifact_family_admissibility",
            "artifact_family_admissibility_version": "v1",
            "contract_file": "identity/protocol/ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_artifact_family_admissibility.py",
            "probe_script": "scripts/ci/run_protocol_root_artifact_family_admissibility_probes_ci.sh",
            "common_script": "scripts/root_artifact_family_admissibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(admissibility_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_artifact_family_admissibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_family_admission_class_rows", family_admission_class_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_family_admission_proof_rows", family_admission_proof_rows),
            ("required_family_admission_limit_rows", family_admission_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_artifact_family_admissibility_{field}_missing")
                error_code = ERR_REGISTRY
        if not artifact_family_admissibility_completeness_rows:
            stale_reasons.append("root_artifact_family_admissibility_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not admissibility_doc.get("contract_required_markers"):
            stale_reasons.append("root_artifact_family_admissibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        if append_expected_root_doc_anchor_stale_reasons(
            stale_reasons,
            root_doc_anchor_checks,
            EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
            stale_reason_prefix="root_artifact_family_admissibility",
        ):
            error_code = ERR_REGISTRY
        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(admissibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_artifact_family_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {"family_id": "required_family_admission_class_rows", "member_id_key": "family_admission_class_id", "actual_rows": family_admission_class_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_CLASS_ROWS, "id_attr": "family_admission_class_id"},
                {"family_id": "required_differentiation_rows", "member_id_key": "differentiation_id", "actual_rows": differentiation_rows, "expected_rows": EXPECTED_DIFFERENTIATION_ROWS, "id_attr": "row_id"},
                {"family_id": "required_family_admission_proof_rows", "member_id_key": "proof_id", "actual_rows": family_admission_proof_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_PROOF_ROWS, "id_attr": "proof_id"},
                {"family_id": "required_family_admission_limit_rows", "member_id_key": "limit_id", "actual_rows": family_admission_limit_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_LIMIT_ROWS, "id_attr": "row_id"},
                {"family_id": "required_collapse_rows", "member_id_key": "collapse_id", "actual_rows": collapse_rows, "expected_rows": EXPECTED_COLLAPSE_ROWS, "id_attr": "row_id"},
                {"family_id": "artifact_family_admissibility_completeness_rows", "member_id_key": "completeness_id", "actual_rows": artifact_family_admissibility_completeness_rows, "expected_rows": {k: {} for k in EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS}, "id_attr": "completeness_id"},
                {"family_id": "artifact_family_admissibility_completeness_surface", "member_id_key": "contract_phrase", "actual_rows": artifact_family_admissibility_completeness_surface.rows, "expected_rows": {row["contract_phrase"]: {} for row in EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS.values()}, "id_attr": "contract_phrase"},
            ),
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        )
        row_family_projection_by_id = index_row_family_projection_rows(row_family_projection_rows)

        validate_contract_row_batches(
            batches=(
                {"actual_rows": family_admission_class_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_CLASS_ROWS, "field_name": "required_family_admission_class_rows", "id_attr": "family_admission_class_id", "compare_fields": ("contract_heading", "admission_role")},
                {"actual_rows": differentiation_rows, "expected_rows": EXPECTED_DIFFERENTIATION_ROWS, "field_name": "required_differentiation_rows", "id_attr": "row_id", "compare_fields": ("contract_phrase",)},
                {"actual_rows": family_admission_proof_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_PROOF_ROWS, "field_name": "required_family_admission_proof_rows", "id_attr": "proof_id", "compare_fields": ("contract_heading", "proof_role")},
                {"actual_rows": family_admission_limit_rows, "expected_rows": EXPECTED_FAMILY_ADMISSION_LIMIT_ROWS, "field_name": "required_family_admission_limit_rows", "id_attr": "row_id", "compare_fields": ("contract_phrase",)},
                {"actual_rows": collapse_rows, "expected_rows": EXPECTED_COLLAPSE_ROWS, "field_name": "required_collapse_rows", "id_attr": "row_id", "compare_fields": ("contract_phrase",)},
                {"actual_rows": artifact_family_admissibility_completeness_rows, "expected_rows": EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS, "field_name": "artifact_family_admissibility_completeness_rows", "id_attr": "completeness_id", "compare_fields": ("contract_phrase",), "duplicate_reason": "duplicate_artifact_family_admissibility_completeness_id", "non_contiguous_reason": "artifact_family_admissibility_completeness_row_order_non_contiguous", "missing_reason": "missing_artifact_family_admissibility_completeness_rows", "extra_reason": "extra_artifact_family_admissibility_completeness_rows", "missing_ids_key": "completeness_ids", "extra_ids_key": "completeness_ids", "violation_id_key": "completeness_id", "order_reason": "artifact_family_admissibility_completeness_row_order_mismatch"},
                {"actual_rows": artifact_family_admissibility_completeness_surface.rows, "expected_rows": {row["contract_phrase"]: {"order": int(row["order"])} for row in EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS.values()}, "field_name": "artifact_family_admissibility_completeness_surface", "id_attr": "contract_phrase", "compare_fields": (), "duplicate_reason": "duplicate_artifact_family_admissibility_completeness_surface_phrase", "non_contiguous_reason": "artifact_family_admissibility_completeness_surface_order_non_contiguous", "missing_reason": "missing_artifact_family_admissibility_completeness_surface_rows", "extra_reason": "extra_artifact_family_admissibility_completeness_surface_rows", "missing_ids_key": "contract_phrases", "extra_ids_key": "contract_phrases", "violation_id_key": "contract_phrase", "order_reason": "artifact_family_admissibility_completeness_surface_order_mismatch"},
            ),
            structure_violations=structure_violations,
            support_violations=admissibility_violations,
        )

        expected_phrases = [row["contract_phrase"] for row in EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS.values()]
        actual_phrases = [row.contract_phrase for row in artifact_family_admissibility_completeness_surface.rows]
        expected_orders = [int(row["order"]) for row in EXPECTED_ARTIFACT_FAMILY_ADMISSIBILITY_COMPLETENESS_ROWS.values()]
        actual_orders = [row.order for row in artifact_family_admissibility_completeness_surface.rows]
        for reason in artifact_family_admissibility_completeness_surface.extraction_violations:
            structure_violations.append({"field": "artifact_family_admissibility_completeness_surface", "reason": f"artifact_family_admissibility_completeness_surface_{reason}"})
        if actual_phrases and tuple(actual_phrases) != tuple(expected_phrases):
            admissibility_violations.append({"field": "artifact_family_admissibility_completeness_surface", "reason": "artifact_family_admissibility_completeness_surface_phrase_order_mismatch", "expected": expected_phrases, "actual": actual_phrases})
        if actual_orders and tuple(actual_orders) != tuple(expected_orders):
            admissibility_violations.append({"field": "artifact_family_admissibility_completeness_surface", "reason": "artifact_family_admissibility_completeness_surface_order_mismatch", "expected": expected_orders, "actual": actual_orders})

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
                        contract_text_marker_checks_from_rows(family_admission_class_rows, reason="family_admission_class_heading_missing"),
                        contract_text_marker_checks_from_rows(family_admission_proof_rows, reason="proof_heading_missing"),
                        contract_text_marker_checks_from_rows(differentiation_rows + family_admission_limit_rows + collapse_rows, reason="contract_phrase_missing", marker_attrs=("contract_phrase",)),
                    ),
                    payload_base={"field": "contract_file"},
                )
            )

        root_doc_anchor_violations.extend(evaluate_root_doc_anchor_checks(repo_root, root_doc_anchor_checks, field_name="root_doc_anchor_checks"))
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
                mappings_required_children=("root-artifact-family-admissibility.current.yaml", "root-artifact-family-admissibility.v1.yaml"),
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
        support_reason_prefix="artifact_family_admissibility_violation",
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
        "family_admission_class_count": len(family_admission_class_rows),
        "differentiation_count": len(differentiation_rows),
        "family_admission_proof_count": len(family_admission_proof_rows),
        "family_admission_limit_count": len(family_admission_limit_rows),
        "collapse_count": len(collapse_rows),
        "artifact_family_admissibility_completeness_row_count": len(artifact_family_admissibility_completeness_rows),
        **project_root_contract_support_projection(prefix="artifact_family", row_family_projection_rows=row_family_projection_rows, anchor_checks=root_doc_anchor_checks, anchor_violations=root_doc_anchor_violations, pass_status=STATUS_PASS_REQUIRED, fail_status=STATUS_FAIL_REQUIRED),
        **project_named_row_family_statuses(
            row_family_projection_rows_by_id=row_family_projection_by_id,
            specs=(
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="artifact_family_admissibility_completeness_row_coverage_status",
                    family_id="artifact_family_admissibility_completeness_rows",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="artifact_family_admissibility_completeness_row_identity_projection_status",
                    family_id="artifact_family_admissibility_completeness_rows",
                    status_key="identity_projection_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="artifact_family_admissibility_completeness_surface_coverage_status",
                    family_id="artifact_family_admissibility_completeness_surface",
                    status_key="coverage_status",
                ),
                NamedRowFamilyStatusProjectionSpec(
                    payload_key="artifact_family_admissibility_completeness_surface_identity_projection_status",
                    family_id="artifact_family_admissibility_completeness_surface",
                    status_key="identity_projection_status",
                ),
            ),
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "family_admission_class_ids": [row.family_admission_class_id for row in sorted(family_admission_class_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "family_admission_proof_ids": [row.proof_id for row in sorted(family_admission_proof_rows, key=lambda item: item.order)],
        "family_admission_limit_ids": [row.row_id for row in sorted(family_admission_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "artifact_family_admissibility_completeness_rows": [{"order": row.order, "completeness_id": row.completeness_id, "contract_phrase": row.contract_phrase} for row in sorted(artifact_family_admissibility_completeness_rows, key=lambda item: item.order)],
        "artifact_family_admissibility_completeness_surface": {
            "rel_path": artifact_family_admissibility_completeness_surface.rel_path,
            "entry_count": len(artifact_family_admissibility_completeness_surface.rows),
            "entries": [{"order": row.order, "contract_phrase": row.contract_phrase} for row in artifact_family_admissibility_completeness_surface.rows],
            "extraction_violations": list(artifact_family_admissibility_completeness_surface.extraction_violations),
        },
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
