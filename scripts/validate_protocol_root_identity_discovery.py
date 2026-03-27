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
from root_contract_row_validation_common import validate_contract_rows
from root_corpus_authority_common import authority_anchor_checks_from_doc, entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family
from root_identity_discovery_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    activation_rows_from_doc,
    collapse_rows_from_doc,
    discovery_limit_rows_from_doc,
    discovery_proof_rows_from_doc,
    error_field_rows_from_doc,
    implementation_rows_from_doc,
    load_root_identity_discovery,
    precedence_rows_from_doc,
    request_field_rows_from_doc,
    response_field_rows_from_doc,
    section_rows_from_doc,
)

STATUS_KEY = "protocol_root_identity_discovery_status"
ERR_REGISTRY = "IP-RID-001"
ERR_STRUCTURE = "IP-RID-002"
ERR_DISCOVERY = "IP-RID-003"

EXPECTED_SECTION_ROWS = {
    "method_identity_list": {"order": 1, "contract_heading": "## Method: `identity/list`"},
    "discovery_precedence": {"order": 2, "contract_heading": "## Discovery precedence"},
    "activation_policy_contract": {"order": 3, "contract_heading": "## Activation policy contract"},
    "required_error_reporting": {"order": 4, "contract_heading": "## Required error reporting"},
    "minimal_local_implementation_requirements": {
        "order": 5,
        "contract_heading": "## Minimal local implementation requirements",
    },
    "non_compliant_discovery_collapses": {
        "order": 6,
        "contract_heading": "## Non-compliant discovery collapses",
    },
}
EXPECTED_REQUEST_FIELD_ROWS = {
    "method": {"order": 1, "contract_phrase": "`method`"},
    "id": {"order": 2, "contract_phrase": "`id`"},
    "cwds": {"order": 3, "contract_phrase": "`cwds`"},
    "extraRoots": {"order": 4, "contract_phrase": "`extraRoots`"},
    "forceReload": {"order": 5, "contract_phrase": "`forceReload`"},
}
EXPECTED_RESPONSE_FIELD_ROWS = {
    "defaultIdentity": {"order": 1, "contract_phrase": "`defaultIdentity`"},
    "identities": {"order": 2, "contract_phrase": "`identities`"},
    "errors": {"order": 3, "contract_phrase": "`errors`"},
    "packPath": {"order": 4, "contract_phrase": "`packPath`"},
    "allowImplicitActivation": {"order": 5, "contract_phrase": "`allowImplicitActivation`"},
    "activationPriority": {"order": 6, "contract_phrase": "`activationPriority`"},
    "conflictResolution": {"order": 7, "contract_phrase": "`conflictResolution`"},
}
EXPECTED_PRECEDENCE_ROWS = {
    "explicit_project_root": {"order": 1, "contract_phrase": "Explicit project root (`cwd`)"},
    "parent_repository_roots": {
        "order": 2,
        "contract_phrase": "Parent repository roots (if configured)",
    },
    "extra_roots": {"order": 3, "contract_phrase": "`extraRoots`"},
}
EXPECTED_ACTIVATION_ROWS = {
    "explicit_identity_selection": {"order": 1, "contract_phrase": "explicit identity selection"},
    "runtime_pin": {
        "order": 2,
        "contract_phrase": "runtime pin (`identity/PROTOCOL_PIN.yaml` and project defaults)",
    },
    "implicit_policy_match": {
        "order": 3,
        "contract_phrase": "implicit policy match (`allow_implicit_activation=true` + objective similarity)",
    },
}
EXPECTED_ERROR_FIELD_ROWS = {
    "code": {"order": 1, "contract_phrase": "`code`"},
    "path": {"order": 2, "contract_phrase": "`path`"},
    "message": {"order": 3, "contract_phrase": "`message`"},
    "severity": {"order": 4, "contract_phrase": "`severity`"},
}
EXPECTED_IMPLEMENTATION_ROWS = {
    "resolve_identity_catalog": {
        "order": 1,
        "contract_phrase": "Resolve `identity/catalog/identities.yaml`",
    },
    "resolve_default_identity": {"order": 2, "contract_phrase": "Resolve `default_identity`"},
    "verify_pack_path_exists": {"order": 3, "contract_phrase": "Verify each `pack_path` exists"},
    "return_normalized_metadata_and_errors": {
        "order": 4,
        "contract_phrase": "Return normalized metadata + errors",
    },
}
EXPECTED_DISCOVERY_PROOF_ROWS = {
    "request_shape_proof": {
        "order": 1,
        "contract_heading": "### 1. Request-shape proof",
        "proof_role": "request_shape_governed_discovery_proof",
    },
    "response_shape_proof": {
        "order": 2,
        "contract_heading": "### 2. Response-shape proof",
        "proof_role": "response_shape_governed_discovery_proof",
    },
    "precedence_resolution_proof": {
        "order": 3,
        "contract_heading": "### 3. Precedence-resolution proof",
        "proof_role": "precedence_resolution_governed_discovery_proof",
    },
    "activation_resolution_proof": {
        "order": 4,
        "contract_heading": "### 4. Activation-resolution proof",
        "proof_role": "activation_resolution_governed_discovery_proof",
    },
    "error_reporting_proof": {
        "order": 5,
        "contract_heading": "### 5. Error-reporting proof",
        "proof_role": "error_reporting_governed_discovery_proof",
    },
    "implementation_compliance_proof": {
        "order": 6,
        "contract_heading": "### 6. Implementation-compliance proof",
        "proof_role": "implementation_compliance_governed_discovery_proof",
    },
}
EXPECTED_DISCOVERY_LIMIT_ROWS = {
    "request_not_response_shape": {
        "order": 1,
        "contract_phrase": "request-shape proof is not proof of response-shape compliance;",
    },
    "response_shape_not_precedence": {
        "order": 2,
        "contract_phrase": "response-shape proof is not proof of governed precedence resolution;",
    },
    "precedence_not_activation": {
        "order": 3,
        "contract_phrase": "precedence-resolution proof is not proof of governed activation resolution;",
    },
    "activation_not_error_reporting": {
        "order": 4,
        "contract_phrase": "activation-resolution proof is not proof of required error reporting;",
    },
    "error_reporting_not_implementation": {
        "order": 5,
        "contract_phrase": "error-reporting proof is not proof of implementation compliance;",
    },
    "implementation_not_current_turn_legality": {
        "order": 6,
        "contract_phrase": "implementation-compliance proof is not proof of current-turn resolver legality.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "cached_catalogue_as_current_turn_truth": {
        "order": 1,
        "contract_phrase": "a cached catalogue snapshot is treated as current-turn governed discovery truth.",
    },
    "path_presence_as_discovery_legality": {
        "order": 2,
        "contract_phrase": "visible path presence or a nearby folder is treated as sufficient discovery legality.",
    },
    "local_convenience_as_conflict_resolution": {
        "order": 3,
        "contract_phrase": "same-id conflicts are resolved by local convenience rather than governed precedence and explicit pinning.",
    },
    "missing_error_fields_as_valid_discovery": {
        "order": 4,
        "contract_phrase": "discovery output is treated as valid even though required `errors[]` fields are missing.",
    },
    "operator_note_as_resolver_truth": {
        "order": 5,
        "contract_phrase": "an operator-facing note or summary is treated as if it were the governed resolver output.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "This file remains the authoritative root-domain contract for deterministic identity discovery law.",
    "## Deterministic identity discovery law",
    "## Method: `identity/list`",
    "## Discovery precedence",
    "## Activation policy contract",
    "## Required error reporting",
    "## Minimal local implementation requirements",
    "## Discovery-proof discipline",
    "## Discovery-proof limits",
    "## Non-compliant discovery collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn discovery legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Identity-discovery row-family completeness must stay explicit",
        "Required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize identity-discovery legality while required row identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root identity-discovery completeness discipline",
        "Identity-discovery law is not a soft prose bundle.",
        "1. required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root identity-discovery completeness boundary",
        "1. Identity-discovery law must remain machine-readable as separate section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse row families.",
        "4. Protocol legality must not finalize identity-discovery truth while missing or unexpected row identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime identity-discovery consumption boundary",
        "1. Runtime consumes identity-discovery law as separate section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse row families rather than as undifferentiated discovery prose.",
        "4. Runtime must not finalize identity-discovery legality while missing or unexpected row identities remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))




def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root identity-discovery law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    discovery_doc, discovery_entry_path, discovery_active_path, discovery_alias_error = load_root_identity_discovery(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    discovery_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if discovery_alias_error:
        stale_reasons.append(f"root_identity_discovery_alias_error:{discovery_alias_error}")
        error_code = ERR_REGISTRY
    elif not discovery_doc:
        stale_reasons.append("root_identity_discovery_empty_or_invalid")
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

    section_rows = section_rows_from_doc(discovery_doc) if discovery_doc else ()
    request_field_rows = request_field_rows_from_doc(discovery_doc) if discovery_doc else ()
    response_field_rows = response_field_rows_from_doc(discovery_doc) if discovery_doc else ()
    precedence_rows = precedence_rows_from_doc(discovery_doc) if discovery_doc else ()
    activation_rows = activation_rows_from_doc(discovery_doc) if discovery_doc else ()
    error_field_rows = error_field_rows_from_doc(discovery_doc) if discovery_doc else ()
    implementation_rows = implementation_rows_from_doc(discovery_doc) if discovery_doc else ()
    discovery_proof_rows = discovery_proof_rows_from_doc(discovery_doc) if discovery_doc else ()
    discovery_limit_rows = discovery_limit_rows_from_doc(discovery_doc) if discovery_doc else ()
    collapse_rows = collapse_rows_from_doc(discovery_doc) if discovery_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(discovery_doc) if discovery_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "identity_discovery_family": "protocol_root_identity_discovery",
            "identity_discovery_version": "v1",
            "contract_file": "identity/protocol/IDENTITY_DISCOVERY.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_identity_discovery.py",
            "probe_script": "scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh",
            "common_script": "scripts/root_identity_discovery_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(discovery_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_identity_discovery_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_section_rows", section_rows),
            ("required_request_field_rows", request_field_rows),
            ("required_response_field_rows", response_field_rows),
            ("required_precedence_rows", precedence_rows),
            ("required_activation_rows", activation_rows),
            ("required_error_field_rows", error_field_rows),
            ("required_implementation_rows", implementation_rows),
            ("required_discovery_proof_rows", discovery_proof_rows),
            ("required_discovery_limit_rows", discovery_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_identity_discovery_{field}_missing")
                error_code = ERR_REGISTRY
        if not discovery_doc.get("contract_required_markers"):
            stale_reasons.append("root_identity_discovery_contract_required_markers_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_identity_discovery",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(discovery_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_identity_discovery_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_section_rows",
                member_id_key="section_id",
                actual_rows=section_rows,
                expected_rows=EXPECTED_SECTION_ROWS,
                id_attr="section_id",
            ),
            project_row_family(
                family_id="required_request_field_rows",
                member_id_key="request_field_id",
                actual_rows=request_field_rows,
                expected_rows=EXPECTED_REQUEST_FIELD_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_response_field_rows",
                member_id_key="response_field_id",
                actual_rows=response_field_rows,
                expected_rows=EXPECTED_RESPONSE_FIELD_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_precedence_rows",
                member_id_key="precedence_id",
                actual_rows=precedence_rows,
                expected_rows=EXPECTED_PRECEDENCE_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_activation_rows",
                member_id_key="activation_id",
                actual_rows=activation_rows,
                expected_rows=EXPECTED_ACTIVATION_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_error_field_rows",
                member_id_key="error_field_id",
                actual_rows=error_field_rows,
                expected_rows=EXPECTED_ERROR_FIELD_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_implementation_rows",
                member_id_key="implementation_id",
                actual_rows=implementation_rows,
                expected_rows=EXPECTED_IMPLEMENTATION_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_discovery_proof_rows",
                member_id_key="proof_id",
                actual_rows=discovery_proof_rows,
                expected_rows=EXPECTED_DISCOVERY_PROOF_ROWS,
                id_attr="proof_id",
            ),
            project_row_family(
                family_id="required_discovery_limit_rows",
                member_id_key="limit_id",
                actual_rows=discovery_limit_rows,
                expected_rows=EXPECTED_DISCOVERY_LIMIT_ROWS,
                id_attr="row_id",
            ),
            project_row_family(
                family_id="required_collapse_rows",
                member_id_key="collapse_id",
                actual_rows=collapse_rows,
                expected_rows=EXPECTED_COLLAPSE_ROWS,
                id_attr="row_id",
            ),
        ]

        validate_contract_rows(
            actual_rows=section_rows,
            expected_rows=EXPECTED_SECTION_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_section_rows",
            id_attr="section_id",
            compare_fields=("contract_heading",),
        )
        validate_contract_rows(
            actual_rows=request_field_rows,
            expected_rows=EXPECTED_REQUEST_FIELD_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_request_field_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=response_field_rows,
            expected_rows=EXPECTED_RESPONSE_FIELD_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_response_field_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=precedence_rows,
            expected_rows=EXPECTED_PRECEDENCE_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_precedence_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=activation_rows,
            expected_rows=EXPECTED_ACTIVATION_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_activation_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=error_field_rows,
            expected_rows=EXPECTED_ERROR_FIELD_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_error_field_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=implementation_rows,
            expected_rows=EXPECTED_IMPLEMENTATION_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_implementation_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=discovery_proof_rows,
            expected_rows=EXPECTED_DISCOVERY_PROOF_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_discovery_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        validate_contract_rows(
            actual_rows=discovery_limit_rows,
            expected_rows=EXPECTED_DISCOVERY_LIMIT_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_discovery_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        validate_contract_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            discovery_violations=discovery_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(discovery_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            discovery_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            contract_marker_violations.extend(
                evaluate_contract_text_marker_checks(
                    contract_text,
                    required_markers=contract_required_markers_from_doc(discovery_doc),
                    row_checks=merge_contract_text_marker_checks(
                        contract_text_marker_checks_from_rows(section_rows, reason="section_heading_missing"),
                        contract_text_marker_checks_from_rows(discovery_proof_rows, reason="proof_heading_missing"),
                        contract_text_marker_checks_from_rows(
                            request_field_rows
                            + response_field_rows
                            + precedence_rows
                            + activation_rows
                            + error_field_rows
                            + implementation_rows
                            + discovery_limit_rows
                            + collapse_rows,
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
                mappings_required_children=("root-identity-discovery.current.yaml", "root-identity-discovery.v1.yaml"),
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
    support_violations = discovery_violations + integration_violations + contract_marker_violations + root_doc_anchor_violations
    verdict = project_root_contract_support_verdict(
        stale_reasons=stale_reasons,
        error_code=error_code,
        structure_violations=structure_violations,
        support_violations=support_violations,
        structure_error_code=ERR_STRUCTURE,
        support_error_code=ERR_DISCOVERY,
        project_structure_reasons=False,
        project_support_reasons=False,
        include_summary_markers=True,
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
        "mapping_entry_path": str(discovery_entry_path),
        "mapping_active_path": str(discovery_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "routing_entry_path": str(routing_entry_path),
        "routing_active_path": str(routing_active_path),
        "section_count": len(section_rows),
        "request_field_count": len(request_field_rows),
        "response_field_count": len(response_field_rows),
        "precedence_count": len(precedence_rows),
        "activation_count": len(activation_rows),
        "error_field_count": len(error_field_rows),
        "implementation_count": len(implementation_rows),
        "discovery_proof_count": len(discovery_proof_rows),
        "discovery_limit_count": len(discovery_limit_rows),
        "collapse_count": len(collapse_rows),
        **project_root_contract_support_projection(
            prefix="identity_discovery",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "section_ids": [row.section_id for row in sorted(section_rows, key=lambda item: item.order)],
        "request_field_ids": [row.row_id for row in sorted(request_field_rows, key=lambda item: item.order)],
        "response_field_ids": [row.row_id for row in sorted(response_field_rows, key=lambda item: item.order)],
        "precedence_ids": [row.row_id for row in sorted(precedence_rows, key=lambda item: item.order)],
        "activation_ids": [row.row_id for row in sorted(activation_rows, key=lambda item: item.order)],
        "error_field_ids": [row.row_id for row in sorted(error_field_rows, key=lambda item: item.order)],
        "implementation_ids": [row.row_id for row in sorted(implementation_rows, key=lambda item: item.order)],
        "discovery_proof_ids": [row.proof_id for row in sorted(discovery_proof_rows, key=lambda item: item.order)],
        "discovery_limit_ids": [row.row_id for row in sorted(discovery_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "stale_reasons": stale_reasons,
        "structure_violations": structure_violations,
        "discovery_violations": discovery_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "summary_markers": summary_markers,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
