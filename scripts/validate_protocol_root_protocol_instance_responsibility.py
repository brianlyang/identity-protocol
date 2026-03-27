#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_marker_checks_common import (
    contract_required_markers_from_doc,
    contract_text_marker_checks_from_rows,
    evaluate_contract_text_marker_checks,
    merge_contract_text_marker_checks,
)
from root_corpus_authority_common import authority_anchor_checks_from_doc, entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_row_family
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
EXPECTED_README_MARKER = "`PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md`"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _entry_marker_missing(required_markers: tuple[str, ...], expected_markers: tuple[str, ...]) -> list[str]:
    marker_set = {str(item or "").strip() for item in required_markers if str(item or "").strip()}
    return [marker for marker in expected_markers if marker not in marker_set]


def _validate_exact_rows(
    *,
    actual_rows,
    expected_rows: dict[str, dict[str, Any]],
    structure_violations: list[dict[str, Any]],
    responsibility_violations: list[dict[str, Any]],
    field_name: str,
    id_attr: str,
    compare_fields: tuple[str, ...],
) -> None:
    actual_map = {getattr(row, id_attr): row for row in actual_rows}
    orders = [row.order for row in actual_rows]
    if len(actual_map) != len(actual_rows):
        structure_violations.append({"field": field_name, "reason": f"duplicate_{id_attr}"})
    if len(set(orders)) != len(orders) or not _contiguous_orders(sorted(orders)):
        structure_violations.append({"field": field_name, "reason": f"{field_name}_order_non_contiguous"})
    missing_ids = sorted(set(expected_rows) - set(actual_map))
    extra_ids = sorted(set(actual_map) - set(expected_rows))
    if missing_ids:
        structure_violations.append({"field": field_name, "reason": "missing_expected_rows", "row_ids": missing_ids})
    if extra_ids:
        structure_violations.append({"field": field_name, "reason": "extra_rows", "row_ids": extra_ids})
    for row_id, expected in expected_rows.items():
        row = actual_map.get(row_id)
        if row is None:
            continue
        if row.order != expected["order"]:
            responsibility_violations.append(
                {
                    "field": field_name,
                    "row_id": row_id,
                    "reason": "order_mismatch",
                    "expected": expected["order"],
                    "actual": row.order,
                }
            )
        for compare_field in compare_fields:
            actual_value = getattr(row, compare_field)
            expected_value = expected[compare_field]
            if actual_value != expected_value:
                responsibility_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


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

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(responsibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_protocol_instance_responsibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_layer_rows",
                member_id_key="layer_id",
                actual_rows=layer_rows,
                expected_rows=EXPECTED_LAYER_ROWS,
                id_attr="layer_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_responsibility_rows",
                member_id_key="owner_id",
                actual_rows=owner_rows,
                expected_rows=EXPECTED_RESPONSIBILITY_ROWS,
                id_attr="owner_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_escalation_rows",
                member_id_key="trigger_id",
                actual_rows=escalation_rows,
                expected_rows=EXPECTED_ESCALATION_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_escalation_proof_rows",
                member_id_key="proof_id",
                actual_rows=escalation_proof_rows,
                expected_rows=EXPECTED_ESCALATION_PROOF_ROWS,
                id_attr="proof_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_escalation_limit_rows",
                member_id_key="limit_id",
                actual_rows=escalation_limit_rows,
                expected_rows=EXPECTED_ESCALATION_LIMIT_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_boundary_collapse_rows",
                member_id_key="collapse_id",
                actual_rows=boundary_collapse_rows,
                expected_rows=EXPECTED_BOUNDARY_COLLAPSES,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
        ]
        _validate_exact_rows(
            actual_rows=layer_rows,
            expected_rows=EXPECTED_LAYER_ROWS,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_layer_rows",
            id_attr="layer_id",
            compare_fields=("contract_heading", "layer_role"),
        )
        _validate_exact_rows(
            actual_rows=owner_rows,
            expected_rows=EXPECTED_RESPONSIBILITY_ROWS,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_responsibility_rows",
            id_attr="owner_id",
            compare_fields=("contract_heading", "responsibility_role"),
        )
        _validate_exact_rows(
            actual_rows=escalation_rows,
            expected_rows=EXPECTED_ESCALATION_ROWS,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_escalation_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_exact_rows(
            actual_rows=escalation_proof_rows,
            expected_rows=EXPECTED_ESCALATION_PROOF_ROWS,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_escalation_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_exact_rows(
            actual_rows=escalation_limit_rows,
            expected_rows=EXPECTED_ESCALATION_LIMIT_ROWS,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_escalation_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_exact_rows(
            actual_rows=boundary_collapse_rows,
            expected_rows=EXPECTED_BOUNDARY_COLLAPSES,
            structure_violations=structure_violations,
            responsibility_violations=responsibility_violations,
            field_name="required_boundary_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
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

        readme_path = repo_root / "identity/protocol/README.md"
        if not readme_path.exists():
            integration_violations.append({"field": "README", "reason": "root_readme_missing"})
        else:
            readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")
            if EXPECTED_README_MARKER not in readme_text:
                integration_violations.append(
                    {
                        "field": "README",
                        "reason": "root_readme_missing_contract_reference",
                        "marker": EXPECTED_README_MARKER,
                    }
                )

        registry_entry_map = {entry.rel_path: entry for entry in registry_entries}
        registry_entry = registry_entry_map.get(contract_file)
        if registry_entry is None:
            integration_violations.append({"field": "root_corpus_registry", "reason": "contract_not_registered"})
        else:
            if registry_entry.entry_kind != "file":
                integration_violations.append(
                    {"field": "root_corpus_registry", "reason": "registry_entry_kind_mismatch", "actual": registry_entry.entry_kind}
                )
            if registry_entry.corpus_class != "root_contract":
                integration_violations.append(
                    {
                        "field": "root_corpus_registry",
                        "reason": "registry_corpus_class_mismatch",
                        "expected": "root_contract",
                        "actual": registry_entry.corpus_class,
                    }
                )
            if not bool(registry_entry.law_bearing):
                integration_violations.append({"field": "root_corpus_registry", "reason": "registry_entry_must_be_law_bearing"})
            missing_registry_markers = _entry_marker_missing(registry_entry.required_markers, EXPECTED_REGISTRY_MARKERS)
            if missing_registry_markers:
                integration_violations.append(
                    {
                        "field": "root_corpus_registry",
                        "reason": "registry_required_markers_missing",
                        "missing_markers": missing_registry_markers,
                    }
                )

        mappings_entry = registry_entry_map.get("identity/protocol/mappings")
        if mappings_entry is None:
            integration_violations.append({"field": "root_corpus_registry", "reason": "mappings_directory_not_registered"})
        else:
            required_children = set(mappings_entry.required_children)
            for child in ("root-protocol-instance-responsibility.current.yaml", "root-protocol-instance-responsibility.v1.yaml"):
                if child not in required_children:
                    integration_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "mappings_required_child_missing",
                            "child": child,
                        }
                    )

        ordering_map = {row.rel_path: row for row in reading_rows}
        ordering_row = ordering_map.get(contract_file)
        if ordering_row is None:
            integration_violations.append({"field": "root_corpus_ordering", "reason": "reading_order_entry_missing"})
        elif ordering_row.entry_role != "root_contract_entry":
            integration_violations.append(
                {
                    "field": "root_corpus_ordering",
                    "reason": "reading_order_entry_role_mismatch",
                    "expected": "root_contract_entry",
                    "actual": ordering_row.entry_role,
                }
            )

        authority_anchor_map = {row.rel_path: row.required_markers for row in authority_anchors}
        missing_authority_markers = _entry_marker_missing(authority_anchor_map.get(contract_file, ()), EXPECTED_AUTHORITY_MARKERS)
        if missing_authority_markers:
            integration_violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": "authority_anchor_missing_or_incomplete",
                    "missing_markers": missing_authority_markers,
                }
            )

        authority_projection_map = {row.rel_path: row for row in authority_projections}
        authority_projection = authority_projection_map.get(contract_file)
        if authority_projection is None:
            integration_violations.append({"field": "root_corpus_authority", "reason": "authority_projection_missing"})
        else:
            if authority_projection.corpus_class != "root_contract":
                integration_violations.append(
                    {
                        "field": "root_corpus_authority",
                        "reason": "authority_projection_corpus_class_mismatch",
                        "expected": "root_contract",
                        "actual": authority_projection.corpus_class,
                    }
                )
            if authority_projection.authority_role != "root_domain_contract_law":
                integration_violations.append(
                    {
                        "field": "root_corpus_authority",
                        "reason": "authority_role_mismatch",
                        "expected": "root_domain_contract_law",
                        "actual": authority_projection.authority_role,
                    }
                )
            if authority_projection.authority_mode != "frozen_law_only":
                integration_violations.append(
                    {
                        "field": "root_corpus_authority",
                        "reason": "authority_mode_mismatch",
                        "expected": "frozen_law_only",
                        "actual": authority_projection.authority_mode,
                    }
                )

        routing_anchor_map = {row.rel_path: row.required_markers for row in routing_anchors}
        missing_routing_markers = _entry_marker_missing(routing_anchor_map.get(contract_file, ()), EXPECTED_ROUTING_MARKERS)
        if missing_routing_markers:
            integration_violations.append(
                {
                    "field": "root_corpus_question_routing",
                    "reason": "routing_anchor_missing_or_incomplete",
                    "missing_markers": missing_routing_markers,
                }
            )

        routing_projection_map = {row.rel_path: row for row in routing_projections}
        routing_projection = routing_projection_map.get(contract_file)
        if routing_projection is None:
            integration_violations.append({"field": "root_corpus_question_routing", "reason": "routing_projection_missing"})
        else:
            actual_question_classes = tuple(routing_projection.question_classes)
            if actual_question_classes != ("frozen_domain_contract_law",):
                integration_violations.append(
                    {
                        "field": "root_corpus_question_routing",
                        "reason": "routing_projection_question_classes_mismatch",
                        "expected": ["frozen_domain_contract_law"],
                        "actual": list(actual_question_classes),
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (responsibility_violations or integration_violations or contract_marker_violations):
        error_code = ERR_RESPONSIBILITY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"responsibility_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in responsibility_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    protocol_instance_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    protocol_instance_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
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
        "protocol_instance_row_family_count": len(row_family_projection_rows),
        "protocol_instance_row_coverage_status": protocol_instance_row_coverage_status,
        "protocol_instance_row_identity_projection_status": protocol_instance_row_identity_projection_status,
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
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
