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
from root_prompt_bootstrap_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    binding_field_rows_from_doc,
    load_root_prompt_bootstrap,
    native_literal_rows_from_doc,
    output_field_rows_from_doc,
    prompt_bootstrap_completeness_rows_from_doc,
    prompt_bootstrap_limit_rows_from_doc,
    prompt_bootstrap_proof_rows_from_doc,
    readme_prompt_bootstrap_completeness_surface,
)

STATUS_KEY = "protocol_root_prompt_bootstrap_status"
ERR_REGISTRY = "IP-RPB-001"
ERR_STRUCTURE = "IP-RPB-002"
ERR_PROMPT = "IP-RPB-003"

EXPECTED_ANCHOR_ROWS = {
    "rq_014_prompt_bootstrap_capability_contract_v1": {
        "order": 1,
        "contract_heading": "### rq_014_prompt_bootstrap_capability_contract_v1",
    },
    "rq_015_prompt_capability_matrix_fail_closed_contract_v1": {
        "order": 2,
        "contract_heading": "### rq_015_prompt_capability_matrix_fail_closed_contract_v1",
    },
    "rq_027_derived_prompt_conformance_contract_v1": {
        "order": 3,
        "contract_heading": "### rq_027_derived_prompt_conformance_contract_v1",
    },
    "shared_prompt_current_run_driver_binding_projection_v1619": {
        "order": 4,
        "contract_heading": "### Shared prompt current-run driver binding projection (v1.6.19 additive)",
    },
    "rq_031_prompt_import_executable_coupling_contract_v1": {
        "order": 5,
        "contract_heading": "### rq_031_prompt_import_executable_coupling_contract_v1",
    },
    "rq_033_native_chat_headstamp_prompt_contract_v1": {
        "order": 6,
        "contract_heading": "### rq_033_native_chat_headstamp_prompt_contract_v1",
    },
}
EXPECTED_OUTPUT_FIELD_ROWS = {
    "capability_driver_required_total": {"order": 1, "contract_phrase": "`capability_driver_required_total`"},
    "capability_driver_present_total": {"order": 2, "contract_phrase": "`capability_driver_present_total`"},
    "capability_driver_coverage_rate": {"order": 3, "contract_phrase": "`capability_driver_coverage_rate`"},
    "missing_capability_drivers": {"order": 4, "contract_phrase": "`missing_capability_drivers`"},
    "prompt_bootstrap_contract_status": {"order": 5, "contract_phrase": "`prompt_bootstrap_contract_status`"},
    "error_code": {"order": 6, "contract_phrase": "`error_code`"},
}
EXPECTED_BINDING_FIELD_ROWS = {
    "driver_receipt_refs": {"order": 1, "contract_phrase": "`driver_receipt_refs`"},
    "driver_run_id": {"order": 2, "contract_phrase": "`driver_run_id`"},
    "driver_projection_digest": {"order": 3, "contract_phrase": "`driver_projection_digest`"},
    "current_run_driver_binding_status": {"order": 4, "contract_phrase": "`current_run_driver_binding_status`"},
    "requiredization_current_round_linked": {"order": 5, "contract_phrase": "`requiredization_current_round_linked`"},
}
EXPECTED_NATIVE_LITERAL_ROWS = {
    "native_chat_headstamp_hard_guard": {"order": 1, "contract_phrase": "`Native Chat Headstamp Hard Guard`"},
    "two_line_headstamp_before_body": {"order": 2, "contract_phrase": "every assistant-authored native-chat reply begins with a two-line headstamp before body text"},
    "headerless_reply_forbidden": {"order": 3, "contract_phrase": "headerless native-chat reply path is forbidden"},
    "failure_path_withheld_conflict": {"order": 4, "contract_phrase": "failure path still emits withheld/conflict `Identity-Context` + `Machine-Verification: verification_status=FAIL_REQUIRED ...`"},
    "native_chat_visible_order": {"order": 5, "contract_phrase": "native chat keeps `Identity-Context -> Machine-Verification -> body`"},
    "governed_visible_order": {"order": 6, "contract_phrase": "governed surfaces keep `Display-Headstamp -> Machine-Verification -> body`"},
    "default_native_chat_mini_profile": {"order": 7, "contract_phrase": "default native-chat `Machine-Verification` profile is `mini`"},
    "failure_line_requested_identity_only": {"order": 8, "contract_phrase": "failure line 1 may claim only `requested_identity_id`"},
    "compatibility_pointer_diagnostic_only": {"order": 9, "contract_phrase": "compatibility pointer diagnostics stay on `Machine-Verification` and remain diagnostic-only"},
}
EXPECTED_PROMPT_BOOTSTRAP_PROOF_ROWS = {
    "constitutional_inheritance_proof": {
        "order": 1,
        "contract_heading": "### 1. Constitutional-inheritance proof",
        "proof_role": "constitutional_inheritance_prompt_bootstrap_proof",
    },
    "capability_absorption_proof": {
        "order": 2,
        "contract_heading": "### 2. Capability-absorption proof",
        "proof_role": "capability_absorption_prompt_bootstrap_proof",
    },
    "current_run_driver_binding_proof": {
        "order": 3,
        "contract_heading": "### 3. Current-run-driver-binding proof",
        "proof_role": "current_run_driver_binding_prompt_bootstrap_proof",
    },
    "executable_coupling_proof": {
        "order": 4,
        "contract_heading": "### 4. Executable-coupling proof",
        "proof_role": "executable_coupling_prompt_bootstrap_proof",
    },
    "hard_guard_literal_preservation_proof": {
        "order": 5,
        "contract_heading": "### 5. Hard-guard-literal preservation proof",
        "proof_role": "hard_guard_literal_preservation_prompt_bootstrap_proof",
    },
}
EXPECTED_PROMPT_BOOTSTRAP_LIMIT_ROWS = {
    "constitutional_inheritance_not_capability_absorption": {
        "order": 1,
        "contract_phrase": "constitutional-inheritance proof is not proof of capability absorption;",
    },
    "capability_absorption_not_current_run_binding": {
        "order": 2,
        "contract_phrase": "capability-absorption proof is not proof of current-run-driver binding;",
    },
    "current_run_binding_not_executable_coupling": {
        "order": 3,
        "contract_phrase": "current-run-driver-binding proof is not proof of executable coupling;",
    },
    "executable_coupling_not_hard_guard_preservation": {
        "order": 4,
        "contract_phrase": "executable-coupling proof is not proof of hard-guard-literal preservation;",
    },
    "hard_guard_preservation_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "hard-guard-literal preservation proof is not proof that current-turn prompt legality may bypass runtime adjudication.",
    },
}
EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS = {
    "explicit_prompt_bootstrap_row_families": {
        "order": 1,
        "contract_phrase": "required anchor, output-field, binding-field, proof, limit, and native-literal rows must remain explicit as separate machine-readable families;",
    },
    "congruent_prompt_bootstrap_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_prompt_bootstrap_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_prompt_bootstrap_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize prompt-bootstrap truth while missing or unexpected row identities remain known only internally;",
    },
    "fail_close_preserves_prompt_bootstrap_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for prompt bootstrap behavior",
    "## Contract anchors",
    "## Base protocol capability absorption matrix (full set)",
    "## Prompt-bootstrap proof discipline",
    "## Prompt-bootstrap proof limits",
    "## Continuous iteration protocol (mandatory)",
    "## Four-track evidence binding (T1/T2/T3/T4)",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Prompt-bootstrap row-family completeness must stay explicit",
        "Required anchor, output-field, binding-field, proof, limit, and native-literal families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize prompt-bootstrap legality while required row identity drift remains known only internally.",
        "README root prompt-bootstrap completeness discipline must therefore stay\ncongruent with admitted prompt-bootstrap-completeness rows rather than\nbecoming a freehand completeness summary.",
    ),
    "identity/protocol/README.md": (
        "## Root prompt-bootstrap completeness discipline",
        "Prompt-bootstrap law is not a soft prose bundle.",
        "These prompt-bootstrap-completeness rules must remain bound to canonical prompt-bootstrap-completeness rows rather than drifting into soft summary prose.",
        "1. required anchor, output-field, binding-field, proof, limit, and native-literal rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root prompt-bootstrap completeness boundary",
        "1. Prompt-bootstrap law must remain machine-readable as separate anchor, output-field, binding-field, proof, limit, and native-literal row families.",
        "4. Protocol legality must not finalize prompt-bootstrap truth while missing or unexpected row identities remain known only inside validator logic.",
        "6. README root prompt-bootstrap completeness discipline rendered at protocol root must remain congruent with admitted prompt-bootstrap-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime prompt-bootstrap consumption boundary",
        "1. Runtime consumes prompt-bootstrap law as separate anchor, output-field, binding-field, proof, limit, and native-literal row families rather than as undifferentiated prompt prose.",
        "4. Runtime must not finalize prompt-bootstrap legality while missing or unexpected row identities remain known only inside validator machinery.",
        "6. Runtime consumes README root prompt-bootstrap completeness discipline as a governed completeness projection bound to admitted prompt-bootstrap-completeness rows rather than as a freehand completeness summary.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root prompt-bootstrap law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    prompt_doc, prompt_entry_path, prompt_active_path, prompt_alias_error = load_root_prompt_bootstrap(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    prompt_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if prompt_alias_error:
        stale_reasons.append(f"root_prompt_bootstrap_alias_error:{prompt_alias_error}")
        error_code = ERR_REGISTRY
    elif not prompt_doc:
        stale_reasons.append("root_prompt_bootstrap_empty_or_invalid")
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

    anchor_rows = anchor_rows_from_doc(prompt_doc) if prompt_doc else ()
    output_field_rows = output_field_rows_from_doc(prompt_doc) if prompt_doc else ()
    binding_field_rows = binding_field_rows_from_doc(prompt_doc) if prompt_doc else ()
    prompt_bootstrap_proof_rows = prompt_bootstrap_proof_rows_from_doc(prompt_doc) if prompt_doc else ()
    prompt_bootstrap_limit_rows = prompt_bootstrap_limit_rows_from_doc(prompt_doc) if prompt_doc else ()
    native_literal_rows = native_literal_rows_from_doc(prompt_doc) if prompt_doc else ()
    prompt_bootstrap_completeness_rows = prompt_bootstrap_completeness_rows_from_doc(prompt_doc) if prompt_doc else ()
    prompt_bootstrap_completeness_surface = readme_prompt_bootstrap_completeness_surface(repo_root)
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(prompt_doc) if prompt_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "prompt_bootstrap_family": "protocol_root_prompt_bootstrap",
            "prompt_bootstrap_version": "v1",
            "contract_file": "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_prompt_bootstrap.py",
            "probe_script": "scripts/ci/run_protocol_root_prompt_bootstrap_probes_ci.sh",
            "common_script": "scripts/root_prompt_bootstrap_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(prompt_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_prompt_bootstrap_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_anchor_rows", anchor_rows),
            ("required_output_field_rows", output_field_rows),
            ("required_binding_field_rows", binding_field_rows),
            ("required_prompt_bootstrap_proof_rows", prompt_bootstrap_proof_rows),
            ("required_prompt_bootstrap_limit_rows", prompt_bootstrap_limit_rows),
            ("required_native_literal_rows", native_literal_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_prompt_bootstrap_{field}_missing")
                error_code = ERR_REGISTRY
        if not prompt_bootstrap_completeness_rows:
            stale_reasons.append("root_prompt_bootstrap_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not prompt_doc.get("contract_required_markers"):
            stale_reasons.append("root_prompt_bootstrap_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_prompt_bootstrap",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(prompt_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_prompt_bootstrap_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = project_row_families(
            families=(
                {
                    "family_id": "required_anchor_rows",
                    "member_id_key": "anchor_id",
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "id_attr": "anchor_id",
                },
                {
                    "family_id": "required_output_field_rows",
                    "member_id_key": "output_field_id",
                    "actual_rows": output_field_rows,
                    "expected_rows": EXPECTED_OUTPUT_FIELD_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_binding_field_rows",
                    "member_id_key": "binding_field_id",
                    "actual_rows": binding_field_rows,
                    "expected_rows": EXPECTED_BINDING_FIELD_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_prompt_bootstrap_proof_rows",
                    "member_id_key": "proof_id",
                    "actual_rows": prompt_bootstrap_proof_rows,
                    "expected_rows": EXPECTED_PROMPT_BOOTSTRAP_PROOF_ROWS,
                    "id_attr": "proof_id",
                },
                {
                    "family_id": "required_prompt_bootstrap_limit_rows",
                    "member_id_key": "limit_id",
                    "actual_rows": prompt_bootstrap_limit_rows,
                    "expected_rows": EXPECTED_PROMPT_BOOTSTRAP_LIMIT_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "required_native_literal_rows",
                    "member_id_key": "native_literal_id",
                    "actual_rows": native_literal_rows,
                    "expected_rows": EXPECTED_NATIVE_LITERAL_ROWS,
                    "id_attr": "row_id",
                },
                {
                    "family_id": "prompt_bootstrap_completeness_rows",
                    "member_id_key": "completeness_id",
                    "actual_rows": prompt_bootstrap_completeness_rows,
                    "expected_rows": {
                        completeness_id: {} for completeness_id in EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS
                    },
                    "id_attr": "completeness_id",
                },
                {
                    "family_id": "prompt_bootstrap_completeness_surface",
                    "member_id_key": "contract_phrase",
                    "actual_rows": prompt_bootstrap_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {}
                        for row in EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values()
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
                    "actual_rows": anchor_rows,
                    "expected_rows": EXPECTED_ANCHOR_ROWS,
                    "field_name": "required_anchor_rows",
                    "id_attr": "anchor_id",
                    "compare_fields": ("contract_heading",),
                },
                {
                    "actual_rows": output_field_rows,
                    "expected_rows": EXPECTED_OUTPUT_FIELD_ROWS,
                    "field_name": "required_output_field_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": binding_field_rows,
                    "expected_rows": EXPECTED_BINDING_FIELD_ROWS,
                    "field_name": "required_binding_field_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": prompt_bootstrap_proof_rows,
                    "expected_rows": EXPECTED_PROMPT_BOOTSTRAP_PROOF_ROWS,
                    "field_name": "required_prompt_bootstrap_proof_rows",
                    "id_attr": "proof_id",
                    "compare_fields": ("contract_heading", "proof_role"),
                },
                {
                    "actual_rows": prompt_bootstrap_limit_rows,
                    "expected_rows": EXPECTED_PROMPT_BOOTSTRAP_LIMIT_ROWS,
                    "field_name": "required_prompt_bootstrap_limit_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": native_literal_rows,
                    "expected_rows": EXPECTED_NATIVE_LITERAL_ROWS,
                    "field_name": "required_native_literal_rows",
                    "id_attr": "row_id",
                    "compare_fields": ("contract_phrase",),
                },
                {
                    "actual_rows": prompt_bootstrap_completeness_rows,
                    "expected_rows": EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS,
                    "field_name": "prompt_bootstrap_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_prompt_bootstrap_completeness_id",
                    "non_contiguous_reason": "prompt_bootstrap_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_prompt_bootstrap_completeness_rows",
                    "extra_reason": "extra_prompt_bootstrap_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "prompt_bootstrap_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": prompt_bootstrap_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "prompt_bootstrap_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_prompt_bootstrap_completeness_surface_phrase",
                    "non_contiguous_reason": "prompt_bootstrap_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_prompt_bootstrap_completeness_surface_rows",
                    "extra_reason": "extra_prompt_bootstrap_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "prompt_bootstrap_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            prompt_violations=prompt_violations,
        )

        expected_prompt_bootstrap_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values()
        ]
        actual_prompt_bootstrap_completeness_phrases = [
            row.contract_phrase for row in prompt_bootstrap_completeness_surface.rows
        ]
        expected_prompt_bootstrap_completeness_orders = [
            int(row["order"]) for row in EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values()
        ]
        actual_prompt_bootstrap_completeness_orders = [
            row.order for row in prompt_bootstrap_completeness_surface.rows
        ]
        for reason in prompt_bootstrap_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "prompt_bootstrap_completeness_surface",
                    "reason": f"prompt_bootstrap_completeness_surface_{reason}",
                }
            )
        if actual_prompt_bootstrap_completeness_phrases and tuple(
            actual_prompt_bootstrap_completeness_phrases
        ) != tuple(expected_prompt_bootstrap_completeness_phrases):
            prompt_violations.append(
                {
                    "field": "prompt_bootstrap_completeness_surface",
                    "reason": "prompt_bootstrap_completeness_surface_phrase_order_mismatch",
                    "expected": expected_prompt_bootstrap_completeness_phrases,
                    "actual": actual_prompt_bootstrap_completeness_phrases,
                }
            )
        if actual_prompt_bootstrap_completeness_orders and tuple(
            actual_prompt_bootstrap_completeness_orders
        ) != tuple(expected_prompt_bootstrap_completeness_orders):
            prompt_violations.append(
                {
                    "field": "prompt_bootstrap_completeness_surface",
                    "reason": "prompt_bootstrap_completeness_surface_order_mismatch",
                    "expected": expected_prompt_bootstrap_completeness_orders,
                    "actual": actual_prompt_bootstrap_completeness_orders,
                }
            )

        contract_file = str(prompt_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            prompt_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(prompt_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(
                            anchor_rows,
                            reason="anchor_heading_missing",
                        ),
                        contract_text_marker_checks_from_rows(
                            prompt_bootstrap_proof_rows,
                            reason="contract_phrase_missing",
                            marker_attrs=("contract_heading", "proof_role"),
                        ),
                        contract_text_marker_checks_from_rows(
                            output_field_rows + binding_field_rows + prompt_bootstrap_limit_rows + native_literal_rows,
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
                mappings_required_children=("root-prompt-bootstrap.current.yaml", "root-prompt-bootstrap.v1.yaml"),
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
    support_violations = prompt_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_PROMPT,
        project_structure_reasons=False,
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
        "mapping_entry_path": str(prompt_entry_path),
        "mapping_active_path": str(prompt_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "routing_entry_path": str(routing_entry_path),
        "routing_active_path": str(routing_active_path),
        "anchor_count": len(anchor_rows),
        "output_field_count": len(output_field_rows),
        "binding_field_count": len(binding_field_rows),
        "prompt_bootstrap_proof_count": len(prompt_bootstrap_proof_rows),
        "prompt_bootstrap_limit_count": len(prompt_bootstrap_limit_rows),
        "native_literal_count": len(native_literal_rows),
        "prompt_bootstrap_completeness_row_count": len(prompt_bootstrap_completeness_rows),
        **project_root_contract_support_projection(
            prefix="prompt_bootstrap",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "anchor_ids": [row.anchor_id for row in anchor_rows],
        "output_field_ids": [row.row_id for row in output_field_rows],
        "binding_field_ids": [row.row_id for row in binding_field_rows],
        "prompt_bootstrap_proof_ids": [row.proof_id for row in prompt_bootstrap_proof_rows],
        "prompt_bootstrap_limit_ids": [row.row_id for row in prompt_bootstrap_limit_rows],
        "native_literal_ids": [row.row_id for row in native_literal_rows],
        "prompt_bootstrap_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(prompt_bootstrap_completeness_rows, key=lambda item: item.order)
        ],
        "prompt_bootstrap_completeness_surface": {
            "rel_path": prompt_bootstrap_completeness_surface.rel_path,
            "entry_count": len(prompt_bootstrap_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in prompt_bootstrap_completeness_surface.rows
            ],
            "extraction_violations": list(prompt_bootstrap_completeness_surface.extraction_violations),
        },
        "stale_reasons": stale_reasons,
        "structure_violations": structure_violations,
        "prompt_violations": prompt_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "summary_markers": summary_markers,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
