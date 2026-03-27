#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_authority_common import authority_anchor_checks_from_doc, entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    entry_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_anchor_checks_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_row_family
from root_machine_world_ontology_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    load_root_machine_world_ontology,
    ontology_limit_rows_from_doc,
    ontology_proof_rows_from_doc,
    object_rows_from_doc,
    stratum_rows_from_doc,
)

STATUS_KEY = "protocol_root_machine_world_ontology_status"
ERR_REGISTRY = "IP-RMWO-001"
ERR_STRUCTURE = "IP-RMWO-002"
ERR_ONTOLOGY = "IP-RMWO-003"

EXPECTED_STRATA_ROWS = {
    "identity_resolution_objects": {
        "order": 1,
        "contract_heading": "### 1. Identity-resolution objects",
        "stratum_role": "identity_resolution_object_stratum",
    },
    "authority_execution_objects": {
        "order": 2,
        "contract_heading": "### 2. Authority and execution-boundary objects",
        "stratum_role": "authority_execution_object_stratum",
    },
    "continuity_retention_objects": {
        "order": 3,
        "contract_heading": "### 3. Continuity and retention objects",
        "stratum_role": "continuity_retention_object_stratum",
    },
    "feedback_gate_verdict_objects": {
        "order": 4,
        "contract_heading": "### 4. Feedback, gate, and verdict objects",
        "stratum_role": "feedback_gate_verdict_object_stratum",
    },
}
EXPECTED_OBJECT_ROWS = {
    "identity_id": {
        "order": 1,
        "contract_phrase": "`identity_id` is the stable identity-resolution key rather than a prompt nickname or narrative persona label.",
    },
    "scope": {
        "order": 2,
        "contract_phrase": "`scope` is the resolved operating scope rather than a free-form situational impression.",
    },
    "work_layer": {
        "order": 3,
        "contract_phrase": "`work_layer` is the active execution layer rather than a vague locality intuition.",
    },
    "source_layer": {
        "order": 4,
        "contract_phrase": "`source_layer` is the authority-bearing source layer rather than a convenience alias.",
    },
    "catalog_path": {
        "order": 5,
        "contract_phrase": "`catalog_path` is the canonical identity catalog source rather than a guessed filesystem memory.",
    },
    "pack_path": {
        "order": 6,
        "contract_phrase": "`pack_path` is the canonical resolved pack location rather than a repo fixture substitute.",
    },
    "actor_session_tuple": {
        "order": 7,
        "contract_phrase": "actor / session tuple is the machine-attested speaking/runtime tuple rather than a narrative self-claim.",
    },
    "launcher_surface": {
        "order": 8,
        "contract_phrase": "launcher surface is the governed execution-entry surface rather than filename discovery by habit.",
    },
    "current_turn_authoritative_truth": {
        "order": 9,
        "contract_phrase": "current-turn authoritative truth is the present-turn admissible authority rather than the latest visible artifact.",
    },
    "canonical_state": {
        "order": 10,
        "contract_phrase": "canonical state is the governed state object rather than an arbitrary local snapshot.",
    },
    "canonical_receipt": {
        "order": 11,
        "contract_phrase": "canonical receipt is the governed execution/admission receipt rather than any artifact that merely looks recent.",
    },
    "canonical_artifact_family": {
        "order": 12,
        "contract_phrase": "canonical artifact family is the governed output family rather than an undifferentiated memory bucket.",
    },
    "continuity_brief": {
        "order": 13,
        "contract_phrase": "continuity brief is the governed re-entry object rather than raw transcript persistence.",
    },
    "dialogue_retention_current_thread": {
        "order": 14,
        "contract_phrase": "dialogue-retention current-thread is the thread-scoped continuity object rather than global memory.",
    },
    "protocol_feedback_lane": {
        "order": 15,
        "contract_phrase": "protocol-feedback lane is the governed feedback object rather than free-form commentary.",
    },
    "required_gate_bundle": {
        "order": 16,
        "contract_phrase": "required gate bundle is the machine admission bundle rather than an informal checklist.",
    },
    "three_plane_verdict": {
        "order": 17,
        "contract_phrase": "three-plane verdict is the governed cross-plane verdict object rather than a prose summary.",
    },
}
EXPECTED_ONTOLOGY_PROOF_ROWS = {
    "canonical_object_definition_proof": {
        "order": 1,
        "contract_heading": "### 1. Canonical-object-definition proof",
        "proof_role": "canonical_object_definition_ontology_proof",
    },
    "stratum_boundary_preservation_proof": {
        "order": 2,
        "contract_heading": "### 2. Stratum-boundary preservation proof",
        "proof_role": "stratum_boundary_preservation_ontology_proof",
    },
    "authority_location_proof": {
        "order": 3,
        "contract_heading": "### 3. Authority-location proof",
        "proof_role": "authority_location_ontology_proof",
    },
    "lifecycle_position_proof": {
        "order": 4,
        "contract_heading": "### 4. Lifecycle-position proof",
        "proof_role": "lifecycle_position_ontology_proof",
    },
    "memory_family_non_collapse_proof": {
        "order": 5,
        "contract_heading": "### 5. Memory-family non-collapse proof",
        "proof_role": "memory_family_non_collapse_ontology_proof",
    },
}
EXPECTED_ONTOLOGY_LIMIT_ROWS = {
    "canonical_definition_not_stratum_boundary": {
        "order": 1,
        "contract_phrase": "canonical-object-definition proof is not proof of stratum-boundary preservation;",
    },
    "stratum_boundary_not_authority_location": {
        "order": 2,
        "contract_phrase": "stratum-boundary preservation proof is not proof of authority location;",
    },
    "authority_location_not_lifecycle_position": {
        "order": 3,
        "contract_phrase": "authority-location proof is not proof of lifecycle position;",
    },
    "lifecycle_position_not_memory_family_non_collapse": {
        "order": 4,
        "contract_phrase": "lifecycle-position proof is not proof of memory-family non-collapse;",
    },
    "memory_family_non_collapse_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "memory-family non-collapse proof is not proof that an object may bypass current-turn runtime adjudication.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "term_meaning_borrowing": {
        "order": 1,
        "contract_phrase": "terms borrow meaning from each other as if object boundaries were optional.",
    },
    "arbitrary_path_drift": {
        "order": 2,
        "contract_phrase": "paths drift arbitrarily and are treated as if path-bearing objects did not need canonical meaning.",
    },
    "latest_as_current": {
        "order": 3,
        "contract_phrase": "the latest visible artifact is treated as if it were automatically current-turn authority.",
    },
    "summary_as_truth": {
        "order": 4,
        "contract_phrase": "summary or projection is treated as if it were truth itself.",
    },
    "history_as_authority": {
        "order": 5,
        "contract_phrase": "history is treated as if it were present authority.",
    },
    "memory_as_vague_bucket": {
        "order": 6,
        "contract_phrase": "`memory` becomes a vague bucket that swallows multiple distinct object families and boundaries.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for machine-world ontology law",
    "## Machine-world ontology law",
    "## Four ontology strata",
    "## Required ontology objects",
    "## Machine-world ontology proof discipline",
    "## Machine-world ontology proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`MACHINE_WORLD_ONTOLOGY_CONTRACT.md`"


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
    ontology_violations: list[dict[str, Any]],
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
            ontology_violations.append(
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
                ontology_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root machine-world ontology law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    ontology_doc, ontology_entry_path, ontology_active_path, ontology_alias_error = load_root_machine_world_ontology(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    ontology_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if ontology_alias_error:
        stale_reasons.append(f"root_machine_world_ontology_alias_error:{ontology_alias_error}")
        error_code = ERR_REGISTRY
    elif not ontology_doc:
        stale_reasons.append("root_machine_world_ontology_empty_or_invalid")
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

    stratum_rows = stratum_rows_from_doc(ontology_doc) if ontology_doc else ()
    object_rows = object_rows_from_doc(ontology_doc) if ontology_doc else ()
    ontology_proof_rows = ontology_proof_rows_from_doc(ontology_doc) if ontology_doc else ()
    ontology_limit_rows = ontology_limit_rows_from_doc(ontology_doc) if ontology_doc else ()
    collapse_rows = collapse_rows_from_doc(ontology_doc) if ontology_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "ontology_family": "protocol_root_machine_world_ontology",
            "ontology_version": "v1",
            "contract_file": "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_machine_world_ontology.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_world_ontology_probes_ci.sh",
            "common_script": "scripts/root_machine_world_ontology_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(ontology_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_world_ontology_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_strata_rows", stratum_rows),
            ("required_object_rows", object_rows),
            ("required_ontology_proof_rows", ontology_proof_rows),
            ("required_ontology_limit_rows", ontology_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_machine_world_ontology_{field}_missing")
                error_code = ERR_REGISTRY
        if not ontology_doc.get("contract_required_markers"):
            stale_reasons.append("root_machine_world_ontology_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(ontology_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_machine_world_ontology_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_strata_rows",
                member_id_key="stratum_id",
                actual_rows=stratum_rows,
                expected_rows=EXPECTED_STRATA_ROWS,
                id_attr="stratum_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_object_rows",
                member_id_key="object_id",
                actual_rows=object_rows,
                expected_rows=EXPECTED_OBJECT_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_ontology_proof_rows",
                member_id_key="proof_id",
                actual_rows=ontology_proof_rows,
                expected_rows=EXPECTED_ONTOLOGY_PROOF_ROWS,
                id_attr="proof_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_ontology_limit_rows",
                member_id_key="limit_id",
                actual_rows=ontology_limit_rows,
                expected_rows=EXPECTED_ONTOLOGY_LIMIT_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_collapse_rows",
                member_id_key="collapse_id",
                actual_rows=collapse_rows,
                expected_rows=EXPECTED_COLLAPSE_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
        ]
        _validate_rows(
            actual_rows=stratum_rows,
            expected_rows=EXPECTED_STRATA_ROWS,
            structure_violations=structure_violations,
            ontology_violations=ontology_violations,
            field_name="required_strata_rows",
            id_attr="stratum_id",
            compare_fields=("contract_heading", "stratum_role"),
        )
        _validate_rows(
            actual_rows=object_rows,
            expected_rows=EXPECTED_OBJECT_ROWS,
            structure_violations=structure_violations,
            ontology_violations=ontology_violations,
            field_name="required_object_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=ontology_proof_rows,
            expected_rows=EXPECTED_ONTOLOGY_PROOF_ROWS,
            structure_violations=structure_violations,
            ontology_violations=ontology_violations,
            field_name="required_ontology_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_rows(
            actual_rows=ontology_limit_rows,
            expected_rows=EXPECTED_ONTOLOGY_LIMIT_ROWS,
            structure_violations=structure_violations,
            ontology_violations=ontology_violations,
            field_name="required_ontology_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            ontology_violations=ontology_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(ontology_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            ontology_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in ontology_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in stratum_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "stratum_heading_missing", "marker": marker})
            for row in ontology_proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading, row.proof_role)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "contract_phrase_missing", "marker": marker})
            for row in object_rows + ontology_limit_rows + collapse_rows:
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
            for child in ("root-machine-world-ontology.current.yaml", "root-machine-world-ontology.v1.yaml"):
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
    if not error_code and (ontology_violations or integration_violations or contract_marker_violations):
        error_code = ERR_ONTOLOGY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"machine_world_ontology_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in ontology_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    machine_world_ontology_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    machine_world_ontology_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ONTOLOGY),
        "ontology_entry_path": str(ontology_entry_path),
        "ontology_active_path": str(ontology_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(ontology_doc.get("contract_file") or ""),
        "stratum_count": len(stratum_rows),
        "object_count": len(object_rows),
        "ontology_proof_count": len(ontology_proof_rows),
        "ontology_limit_count": len(ontology_limit_rows),
        "collapse_count": len(collapse_rows),
        "machine_world_ontology_row_family_count": len(row_family_projection_rows),
        "machine_world_ontology_row_coverage_status": machine_world_ontology_row_coverage_status,
        "machine_world_ontology_row_identity_projection_status": machine_world_ontology_row_identity_projection_status,
        "row_family_projection_rows": row_family_projection_rows,
        "stratum_ids": [row.stratum_id for row in sorted(stratum_rows, key=lambda item: item.order)],
        "object_ids": [row.row_id for row in sorted(object_rows, key=lambda item: item.order)],
        "ontology_proof_ids": [row.proof_id for row in sorted(ontology_proof_rows, key=lambda item: item.order)],
        "ontology_limit_ids": [row.row_id for row in sorted(ontology_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "ontology_violations": ontology_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
