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
from root_machine_law_primacy_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    collapse_rows_from_doc,
    commitment_rows_from_doc,
    load_root_machine_law_primacy,
    machine_law_primacy_completeness_rows_from_doc,
    primacy_limit_rows_from_doc,
    primacy_proof_rows_from_doc,
    readme_machine_law_primacy_completeness_surface,
)

STATUS_KEY = "protocol_root_machine_law_primacy_status"
ERR_REGISTRY = "IP-RMLP-001"
ERR_STRUCTURE = "IP-RMLP-002"
ERR_PRIMACY = "IP-RMLP-003"

EXPECTED_COMMITMENT_ROWS = {
    "law_before_compatibility_shelter": {
        "order": 1,
        "contract_heading": "### 1. Law before compatibility shelter",
        "commitment_role": "machine_law_first",
    },
    "governed_success_path_before_convenience": {
        "order": 2,
        "contract_heading": "### 2. Governed success path before convenience permissiveness",
        "commitment_role": "success_path_admissibility_first",
    },
    "fail_close_before_silent_swallowing": {
        "order": 3,
        "contract_heading": "### 3. Fail-close exposure before silent swallowing",
        "commitment_role": "fail_close_before_shelter",
    },
    "governed_convergence_before_downgrade": {
        "order": 4,
        "contract_heading": "### 4. Governed convergence before downgrade laundering",
        "commitment_role": "governed_convergence_over_downgrade",
    },
}
EXPECTED_ANCHOR_ROWS = {
    "machine_law_first": {
        "order": 1,
        "contract_phrase": "machine law first rather than a compatibility shelter or historical backstop;",
    },
    "governed_success_path": {
        "order": 2,
        "contract_phrase": "governed current-turn success path rather than convenience-path permissiveness;",
    },
    "fail_close_over_projection": {
        "order": 3,
        "contract_phrase": "fail-close exposure of missing or ambiguous truth rather than silent swallowing through compatibility projection;",
    },
    "governed_convergence_over_downgrade": {
        "order": 4,
        "contract_phrase": "governed convergence and refreezing rather than residue laundering or protocol downgrade.",
    },
}
EXPECTED_PRIMACY_PROOF_ROWS = {
    "frozen_law_primacy_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-law primacy proof",
        "proof_role": "frozen_law_primacy_proof",
    },
    "success_path_demotion_boundary_primacy_proof": {
        "order": 2,
        "contract_heading": "### 2. Success-path demotion-boundary proof",
        "proof_role": "success_path_demotion_boundary_primacy_proof",
    },
    "fail_close_exposure_primacy_proof": {
        "order": 3,
        "contract_heading": "### 3. Fail-close exposure proof",
        "proof_role": "fail_close_exposure_primacy_proof",
    },
    "governed_convergence_primacy_proof": {
        "order": 4,
        "contract_heading": "### 4. Governed-convergence proof",
        "proof_role": "governed_convergence_primacy_proof",
    },
    "runtime_adjudication_non_bypass_primacy_proof": {
        "order": 5,
        "contract_heading": "### 5. Runtime-adjudication non-bypass proof",
        "proof_role": "runtime_adjudication_non_bypass_primacy_proof",
    },
}
EXPECTED_PRIMACY_LIMIT_ROWS = {
    "frozen_law_not_success_path_demotion_boundary": {
        "order": 1,
        "contract_phrase": "frozen-law primacy proof is not proof of success-path demotion boundary;",
    },
    "success_path_demotion_not_fail_close_exposure": {
        "order": 2,
        "contract_phrase": "success-path demotion-boundary proof is not proof of fail-close exposure;",
    },
    "fail_close_not_governed_convergence": {
        "order": 3,
        "contract_phrase": "fail-close exposure proof is not proof of governed convergence;",
    },
    "governed_convergence_not_runtime_non_bypass": {
        "order": 4,
        "contract_phrase": "governed-convergence proof is not proof of runtime-adjudication non-bypass;",
    },
    "runtime_non_bypass_not_success_path_reentry": {
        "order": 5,
        "contract_phrase": "runtime-adjudication non-bypass proof is not proof that compatibility or recovery surfaces may re-enter active success-path legality.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "compatibility_shelter_substitution": {
        "order": 1,
        "contract_phrase": "the active protocol is treated as a shelter for lagging residue instead of as the upgrade target.",
    },
    "silent_truth_reconstruction": {
        "order": 2,
        "contract_phrase": "missing or ambiguous current-turn truth is rebuilt through compatibility projection, alias bridges, or local familiarity.",
    },
    "demoted_surface_reentry": {
        "order": 3,
        "contract_phrase": "migration, import, fixture, diagnostic, or fallback surfaces re-enter active defaults as if demotion did not exist.",
    },
    "protocol_downgrade_for_residue": {
        "order": 4,
        "contract_phrase": "shared law is weakened or reopened merely to keep local residue alive.",
    },
    "convenience_claims_legality": {
        "order": 5,
        "contract_phrase": "convenience, vividness, or historical familiarity is treated as if it proved active-path legality.",
    },
}
EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS = {
    "explicit_machine_law_primacy_row_families": {
        "order": 1,
        "contract_phrase": "required commitment, anchor, primacy-proof, primacy-limit, and collapse rows must remain explicit as separate machine-readable families;",
    },
    "congruent_machine_law_primacy_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_machine_law_primacy_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_machine_law_primacy_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize machine-law primacy legality while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_machine_law_primacy_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for machine-law primacy",
    "## Machine-law primacy law",
    "## Four primacy commitments",
    "## Required primacy anchors",
    "## Machine-law primacy proof discipline",
    "## Machine-law primacy proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn machine-law primacy legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Machine-law primacy row-family completeness must stay explicit",
        "Required commitment, anchor, primacy-proof, primacy-limit, and collapse families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize machine-law primacy legality while required row identity drift remains known only internally.",
        "README root machine-law primacy completeness discipline must therefore stay congruent with admitted machine-law-primacy-completeness rows rather than becoming a freehand completeness summary.",
    ),
    "identity/protocol/README.md": (
        "## Root machine-law primacy completeness discipline",
        "Machine-law primacy law is not a soft prose bundle.",
        "These machine-law-primacy-completeness rules must remain bound to canonical machine-law-primacy-completeness rows rather than drifting into soft summary prose.",
        "1. required commitment, anchor, primacy-proof, primacy-limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root machine-law primacy completeness boundary",
        "1. Machine-law primacy law must remain machine-readable as separate commitment, anchor, primacy-proof, primacy-limit, and collapse row families.",
        "4. Protocol legality must not finalize machine-law primacy legality while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root machine-law primacy completeness discipline rendered at protocol root must remain congruent with admitted machine-law-primacy-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime machine-law primacy consumption boundary",
        "1. Runtime consumes machine-law primacy law as separate commitment, anchor, primacy-proof, primacy-limit, and collapse row families rather than as undifferentiated anti-compatibility prose.",
        "4. Runtime must not finalize machine-law primacy legality while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root machine-law primacy completeness discipline as a governed completeness projection bound to admitted machine-law-primacy-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root machine-law primacy and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    primacy_doc, primacy_entry_path, primacy_active_path, primacy_alias_error = load_root_machine_law_primacy(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    primacy_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if primacy_alias_error:
        stale_reasons.append(f"root_machine_law_primacy_alias_error:{primacy_alias_error}")
        error_code = ERR_REGISTRY
    elif not primacy_doc:
        stale_reasons.append("root_machine_law_primacy_empty_or_invalid")
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

    commitment_rows = commitment_rows_from_doc(primacy_doc) if primacy_doc else ()
    anchor_rows = anchor_rows_from_doc(primacy_doc) if primacy_doc else ()
    primacy_proof_rows = primacy_proof_rows_from_doc(primacy_doc) if primacy_doc else ()
    primacy_limit_rows = primacy_limit_rows_from_doc(primacy_doc) if primacy_doc else ()
    collapse_rows = collapse_rows_from_doc(primacy_doc) if primacy_doc else ()
    machine_law_primacy_completeness_rows = (
        machine_law_primacy_completeness_rows_from_doc(primacy_doc) if primacy_doc else ()
    )
    machine_law_primacy_completeness_surface = readme_machine_law_primacy_completeness_surface(repo_root)
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(primacy_doc) if primacy_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "machine_law_family": "protocol_root_machine_law_primacy",
            "machine_law_version": "v1",
            "contract_file": "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_machine_law_primacy.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_law_primacy_probes_ci.sh",
            "common_script": "scripts/root_machine_law_primacy_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(primacy_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_law_primacy_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_commitment_rows", commitment_rows),
            ("required_anchor_rows", anchor_rows),
            ("required_primacy_proof_rows", primacy_proof_rows),
            ("required_primacy_limit_rows", primacy_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_machine_law_primacy_{field}_missing")
                error_code = ERR_REGISTRY
        if not machine_law_primacy_completeness_rows:
            stale_reasons.append("root_machine_law_primacy_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not primacy_doc.get("contract_required_markers"):
            stale_reasons.append("root_machine_law_primacy_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_machine_law_primacy",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(primacy_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_machine_law_primacy_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_commitment_rows",
                    "member_id_key": "commitment_id",
                    "actual_rows": commitment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_ROWS,
                    "id_attr": "commitment_id",
                },
                {
                    "family_id": "required_anchor_rows",
                    "member_id_key": "anchor_id",
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_primacy_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": primacy_proof_rows,
                    "expected_rows": EXPECTED_PRIMACY_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_primacy_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": primacy_limit_rows,
                    "expected_rows": EXPECTED_PRIMACY_LIMIT_ROWS,
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
                    "family_id": "machine_law_primacy_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": machine_law_primacy_completeness_rows,
                    "expected_rows": {
                        completeness_id: {} for completeness_id in EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "machine_law_primacy_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": machine_law_primacy_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {} for row in EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS.values()
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
                    "actual_rows": commitment_rows,
                    "expected_rows": EXPECTED_COMMITMENT_ROWS,
                    "field_name": "required_commitment_rows",
                    "id_attr": "commitment_id",
                    "compare_fields": ("contract_heading", "commitment_role"),
                },
                {
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "field_name": "required_anchor_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": primacy_proof_rows,
                    "expected_rows": EXPECTED_PRIMACY_PROOF_ROWS,
                    "field_name": "required_primacy_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": primacy_limit_rows,
                    "expected_rows": EXPECTED_PRIMACY_LIMIT_ROWS,
                    "field_name": "required_primacy_limit_rows",
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
                    "actual_rows": machine_law_primacy_completeness_rows,
                    "expected_rows": EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS,
                    "field_name": "machine_law_primacy_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_machine_law_primacy_completeness_id",
                    "non_contiguous_reason": "machine_law_primacy_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_machine_law_primacy_completeness_rows",
                    "extra_reason": "extra_machine_law_primacy_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "machine_law_primacy_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": machine_law_primacy_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "machine_law_primacy_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_machine_law_primacy_completeness_surface_phrase",
                    "non_contiguous_reason": "machine_law_primacy_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_machine_law_primacy_completeness_surface_rows",
                    "extra_reason": "extra_machine_law_primacy_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "machine_law_primacy_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
        )

        expected_machine_law_primacy_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS.values()
        ]
        actual_machine_law_primacy_completeness_phrases = [
            row.contract_phrase for row in machine_law_primacy_completeness_surface.rows
        ]
        expected_machine_law_primacy_completeness_orders = [
            int(row["order"]) for row in EXPECTED_MACHINE_LAW_PRIMACY_COMPLETENESS_ROWS.values()
        ]
        actual_machine_law_primacy_completeness_orders = [
            row.order for row in machine_law_primacy_completeness_surface.rows
        ]
        for reason in machine_law_primacy_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "machine_law_primacy_completeness_surface",
                    "reason": f"machine_law_primacy_completeness_surface_{reason}",
                }
            )
        if actual_machine_law_primacy_completeness_phrases and tuple(
            actual_machine_law_primacy_completeness_phrases
        ) != tuple(expected_machine_law_primacy_completeness_phrases):
            primacy_violations.append(
                {
                    "field": "machine_law_primacy_completeness_surface",
                    "reason": "machine_law_primacy_completeness_surface_phrase_order_mismatch",
                    "expected": expected_machine_law_primacy_completeness_phrases,
                    "actual": actual_machine_law_primacy_completeness_phrases,
                }
            )
        if actual_machine_law_primacy_completeness_orders and tuple(
            actual_machine_law_primacy_completeness_orders
        ) != tuple(expected_machine_law_primacy_completeness_orders):
            primacy_violations.append(
                {
                    "field": "machine_law_primacy_completeness_surface",
                    "reason": "machine_law_primacy_completeness_surface_order_mismatch",
                    "expected": expected_machine_law_primacy_completeness_orders,
                    "actual": actual_machine_law_primacy_completeness_orders,
                }
            )

        contract_file = str(primacy_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            primacy_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(primacy_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            commitment_rows,
                            reason="commitment_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            primacy_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            anchor_rows + primacy_limit_rows + collapse_rows,
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
                mappings_required_children=('root-machine-law-primacy.current.yaml', 'root-machine-law-primacy.v1.yaml'),
                expected_authority_markers=EXPECTED_AUTHORITY_MARKERS,
                expected_routing_markers=EXPECTED_ROUTING_MARKERS,
            )
        )

    support_violations = primacy_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_PRIMACY,
        support_reason_prefix="machine_law_primacy_violation",
        anchor_violations=root_doc_anchor_violations,
        anchor_reason_prefix="root_doc_anchor_violation",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    error_code = str(verdict["error_code"])
    status = str(verdict["status"])
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_PRIMACY),
        "primacy_entry_path": str(primacy_entry_path),
        "primacy_active_path": str(primacy_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(primacy_doc.get("contract_file") or ""),
        "commitment_count": len(commitment_rows),
        "anchor_count": len(anchor_rows),
        "primacy_proof_count": len(primacy_proof_rows),
        "primacy_limit_count": len(primacy_limit_rows),
        "collapse_count": len(collapse_rows),
        "machine_law_primacy_completeness_row_count": len(machine_law_primacy_completeness_rows),
        **project_root_contract_support_projection(
            prefix="machine_law_primacy",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "commitment_ids": [row.commitment_id for row in sorted(commitment_rows, key=lambda item: item.order)],
        "anchor_ids": [row.row_id for row in sorted(anchor_rows, key=lambda item: item.order)],
        "primacy_proof_ids": [row.proof_id for row in sorted(primacy_proof_rows, key=lambda item: item.order)],
        "primacy_limit_ids": [row.row_id for row in sorted(primacy_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "machine_law_primacy_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(machine_law_primacy_completeness_rows, key=lambda item: item.order)
        ],
        "machine_law_primacy_completeness_surface": {
            "rel_path": machine_law_primacy_completeness_surface.rel_path,
            "entry_count": len(machine_law_primacy_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in machine_law_primacy_completeness_surface.rows
            ],
            "extraction_violations": list(machine_law_primacy_completeness_surface.extraction_violations),
        },
        "structure_violations": structure_violations,
        "primacy_violations": primacy_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
