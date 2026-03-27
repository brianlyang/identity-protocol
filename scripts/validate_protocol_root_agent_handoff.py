#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_agent_handoff_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    collapse_rows_from_doc,
    handoff_limit_rows_from_doc,
    handoff_proof_rows_from_doc,
    load_root_agent_handoff,
    payload_rows_from_doc,
    role_rows_from_doc,
)
from root_corpus_authority_common import authority_anchor_checks_from_doc, entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_row_family

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
EXPECTED_README_MARKER = "`AGENT_HANDOFF_CONTRACT.md`"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _entry_marker_missing(required_markers: tuple[str, ...], expected_markers: tuple[str, ...]) -> list[str]:
    marker_set = {str(item or "").strip() for item in required_markers if str(item or "").strip()}
    return [marker for marker in expected_markers if marker not in marker_set]


def _validate_rows(
    *,
    actual_rows,
    expected_rows: dict[str, dict[str, Any]],
    structure_violations: list[dict[str, Any]],
    handoff_violations: list[dict[str, Any]],
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
            handoff_violations.append(
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
                handoff_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


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
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    row_family_projection_rows = [
        project_row_family(
            family_id="role_rows",
            member_id_key="role_id",
            actual_rows=role_rows,
            expected_rows=EXPECTED_ROLE_ROWS,
            id_attr="role_id",
        ),
        project_row_family(
            family_id="payload_rows",
            member_id_key="payload_field_id",
            actual_rows=payload_rows,
            expected_rows=EXPECTED_PAYLOAD_ROWS,
            id_attr="row_id",
        ),
        project_row_family(
            family_id="anchor_rows",
            member_id_key="anchor_id",
            actual_rows=anchor_rows,
            expected_rows=EXPECTED_ANCHOR_ROWS,
            id_attr="row_id",
        ),
        project_row_family(
            family_id="handoff_proof_rows",
            member_id_key="proof_id",
            actual_rows=handoff_proof_rows,
            expected_rows=EXPECTED_HANDOFF_PROOF_ROWS,
            id_attr="proof_id",
        ),
        project_row_family(
            family_id="handoff_limit_rows",
            member_id_key="limit_id",
            actual_rows=handoff_limit_rows,
            expected_rows=EXPECTED_HANDOFF_LIMIT_ROWS,
            id_attr="row_id",
        ),
        project_row_family(
            family_id="collapse_rows",
            member_id_key="collapse_id",
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            id_attr="row_id",
        ),
    ]
    agent_handoff_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
    )
    agent_handoff_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
    )
    row_family_projection_by_id = {row["family_id"]: row for row in row_family_projection_rows}

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
        if not handoff_doc.get("contract_required_markers"):
            stale_reasons.append("root_agent_handoff_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(handoff_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_agent_handoff_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        _validate_rows(
            actual_rows=role_rows,
            expected_rows=EXPECTED_ROLE_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_role_rows",
            id_attr="role_id",
            compare_fields=("contract_heading", "handoff_role"),
        )
        _validate_rows(
            actual_rows=payload_rows,
            expected_rows=EXPECTED_PAYLOAD_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_payload_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=anchor_rows,
            expected_rows=EXPECTED_ANCHOR_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_anchor_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=handoff_proof_rows,
            expected_rows=EXPECTED_HANDOFF_PROOF_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_handoff_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_rows(
            actual_rows=handoff_limit_rows,
            expected_rows=EXPECTED_HANDOFF_LIMIT_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_handoff_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            handoff_violations=handoff_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(handoff_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            handoff_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in handoff_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in role_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "role_heading_missing", "marker": marker})
            for row in handoff_proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "proof_heading_missing", "marker": marker})
            for row in payload_rows + anchor_rows + handoff_limit_rows + collapse_rows:
                for marker in find_missing_markers(contract_text, (row.contract_phrase,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "contract_phrase_missing", "marker": marker})

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
            for child in ("root-agent-handoff.current.yaml", "root-agent-handoff.v1.yaml"):
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

        authority_anchor_map = {row.rel_path: row for row in authority_anchors}
        authority_anchor = authority_anchor_map.get(contract_file)
        if authority_anchor is None:
            integration_violations.append({"field": "root_corpus_authority", "reason": "authority_anchor_missing"})
        else:
            missing_authority_markers = _entry_marker_missing(authority_anchor.required_markers, EXPECTED_AUTHORITY_MARKERS)
            if missing_authority_markers:
                integration_violations.append(
                    {
                        "field": "root_corpus_authority",
                        "reason": "authority_required_markers_missing",
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
                        "reason": "authority_projection_role_mismatch",
                        "expected": "root_domain_contract_law",
                        "actual": authority_projection.authority_role,
                    }
                )
            if authority_projection.authority_mode != "frozen_law_only":
                integration_violations.append(
                    {
                        "field": "root_corpus_authority",
                        "reason": "authority_projection_mode_mismatch",
                        "expected": "frozen_law_only",
                        "actual": authority_projection.authority_mode,
                    }
                )

        routing_anchor_map = {row.rel_path: row for row in routing_anchors}
        routing_anchor = routing_anchor_map.get(contract_file)
        if routing_anchor is None:
            integration_violations.append({"field": "root_corpus_question_routing", "reason": "routing_anchor_missing"})
        else:
            missing_routing_markers = _entry_marker_missing(routing_anchor.required_markers, EXPECTED_ROUTING_MARKERS)
            if missing_routing_markers:
                integration_violations.append(
                    {
                        "field": "root_corpus_question_routing",
                        "reason": "routing_required_markers_missing",
                        "missing_markers": missing_routing_markers,
                    }
                )

        routing_projection_map = {row.rel_path: row for row in routing_projections}
        routing_projection = routing_projection_map.get(contract_file)
        if routing_projection is None:
            integration_violations.append({"field": "root_corpus_question_routing", "reason": "routing_projection_missing"})
        else:
            actual_question_classes = tuple(routing_projection.question_classes)
            expected_question_classes = ("frozen_domain_contract_law",)
            if actual_question_classes != expected_question_classes:
                integration_violations.append(
                    {
                        "field": "root_corpus_question_routing",
                        "reason": "routing_projection_question_classes_mismatch",
                        "expected": list(expected_question_classes),
                        "actual": list(actual_question_classes),
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (handoff_violations or integration_violations or contract_marker_violations):
        error_code = ERR_HANDOFF

    status = (
        STATUS_PASS_REQUIRED
        if not any((stale_reasons, structure_violations, handoff_violations, integration_violations, contract_marker_violations))
        else STATUS_FAIL_REQUIRED
    )
    rc = 0 if status == STATUS_PASS_REQUIRED else 1
    summary_markers = sorted(
        {
            row.get("marker", "")
            for row in handoff_violations + integration_violations + contract_marker_violations
            if row.get("marker")
        }
    )

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
        "agent_handoff_row_family_count": len(row_family_projection_rows),
        "agent_handoff_row_coverage_status": agent_handoff_row_coverage_status,
        "agent_handoff_row_identity_projection_status": agent_handoff_row_identity_projection_status,
        "role_row_coverage_status": row_family_projection_by_id["role_rows"]["coverage_status"],
        "role_row_identity_projection_status": row_family_projection_by_id["role_rows"]["identity_projection_status"],
        "payload_row_coverage_status": row_family_projection_by_id["payload_rows"]["coverage_status"],
        "payload_row_identity_projection_status": row_family_projection_by_id["payload_rows"][
            "identity_projection_status"
        ],
        "anchor_row_coverage_status": row_family_projection_by_id["anchor_rows"]["coverage_status"],
        "anchor_row_identity_projection_status": row_family_projection_by_id["anchor_rows"][
            "identity_projection_status"
        ],
        "handoff_proof_row_coverage_status": row_family_projection_by_id["handoff_proof_rows"][
            "coverage_status"
        ],
        "handoff_proof_row_identity_projection_status": row_family_projection_by_id["handoff_proof_rows"][
            "identity_projection_status"
        ],
        "handoff_limit_row_coverage_status": row_family_projection_by_id["handoff_limit_rows"][
            "coverage_status"
        ],
        "handoff_limit_row_identity_projection_status": row_family_projection_by_id["handoff_limit_rows"][
            "identity_projection_status"
        ],
        "collapse_row_coverage_status": row_family_projection_by_id["collapse_rows"]["coverage_status"],
        "collapse_row_identity_projection_status": row_family_projection_by_id["collapse_rows"][
            "identity_projection_status"
        ],
        "handoff_proof_ids": [row.proof_id for row in sorted(handoff_proof_rows, key=lambda item: item.order)],
        "handoff_limit_ids": [row.row_id for row in sorted(handoff_limit_rows, key=lambda item: item.order)],
        "row_family_projection_rows": row_family_projection_rows,
        "stale_reasons": stale_reasons,
        "structure_violations": structure_violations,
        "handoff_violations": handoff_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "summary_markers": summary_markers,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
