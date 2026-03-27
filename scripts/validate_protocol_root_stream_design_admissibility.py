#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
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
from root_stream_design_admissibility_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    admissibility_limit_rows_from_doc,
    admissibility_proof_rows_from_doc,
    load_root_stream_design_admissibility,
    outcome_class_rows_from_doc,
    required_projection_surfaces_from_doc,
    required_question_rows_from_doc,
)

STATUS_KEY = "protocol_root_stream_design_admissibility_status"
ERR_REGISTRY = "IP-RSDA-001"
ERR_STRUCTURE = "IP-RSDA-002"
ERR_ADMISSIBILITY = "IP-RSDA-003"

EXPECTED_QUESTION_ROWS = {
    "ontology": {
        "order": 1,
        "contract_heading": "### 1. Ontology question",
        "normative_focus": "object_identity_and_non_collapse",
    },
    "truth_lifecycle": {
        "order": 2,
        "contract_heading": "### 2. Truth-lifecycle question",
        "normative_focus": "canonical_truth_discoverability_admissibility_binding_consumption",
    },
    "normative": {
        "order": 3,
        "contract_heading": "### 3. Normative question",
        "normative_focus": "allowed_actions_fail_close_success_path_and_forbidden_shortcuts",
    },
    "responsibility_split": {
        "order": 4,
        "contract_heading": "### 4. Responsibility-split question",
        "normative_focus": "protocol_instance_operator_boundary",
    },
    "answer_surface": {
        "order": 5,
        "contract_heading": "### 5. Answer-surface question",
        "normative_focus": "stable_operator_delivery_surface",
    },
}
EXPECTED_OUTCOME_CLASSES = (
    "local_technique_only",
    "instance_adaptation_only",
    "governed_extension_strengthening",
    "root_contract_strengthening",
    "constitutional_strengthening",
)
EXPECTED_ADMISSIBILITY_PROOF_ROWS = {
    "ontology_closure_proof": {
        "order": 1,
        "contract_heading": "### 1. Ontology-closure proof",
        "proof_role": "object_identity_non_collapse_proof",
    },
    "truth_lifecycle_closure_proof": {
        "order": 2,
        "contract_heading": "### 2. Truth-lifecycle-closure proof",
        "proof_role": "truth_lifecycle_closure_proof",
    },
    "normative_closure_proof": {
        "order": 3,
        "contract_heading": "### 3. Normative-closure proof",
        "proof_role": "normative_boundary_closure_proof",
    },
    "responsibility_split_closure_proof": {
        "order": 4,
        "contract_heading": "### 4. Responsibility-split-closure proof",
        "proof_role": "responsibility_split_closure_proof",
    },
    "answer_surface_closure_proof": {
        "order": 5,
        "contract_heading": "### 5. Answer-surface-closure proof",
        "proof_role": "operator_answer_surface_closure_proof",
    },
}
EXPECTED_ADMISSIBILITY_LIMIT_ROWS = {
    "ontology_not_truth_lifecycle": {
        "order": 1,
        "contract_phrase": "ontology-closure proof is not proof of truth-lifecycle closure;",
    },
    "truth_lifecycle_not_normative": {
        "order": 2,
        "contract_phrase": "truth-lifecycle-closure proof is not proof of normative closure;",
    },
    "normative_not_responsibility_split": {
        "order": 3,
        "contract_phrase": "normative-closure proof is not proof of responsibility-split closure;",
    },
    "responsibility_split_not_answer_surface": {
        "order": 4,
        "contract_phrase": "responsibility-split-closure proof is not proof of answer-surface closure;",
    },
    "proof_not_projection_substitute": {
        "order": 5,
        "contract_phrase": "no admissibility proof may substitute for mandatory projection into governed surfaces.",
    },
}
EXPECTED_PROJECTION_SURFACES = (
    "governed_governance_surface",
    "governed_review_surface",
    "root_contract_or_machine_registry_surface",
    "validator_and_probe_surface",
    "runtime_answer_surface_if_applicable",
)
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for stream-design admissibility",
    "## Admissibility law",
    "## Five required design questions",
    "## Admissibility-proof discipline",
    "## Admissibility-proof limits",
    "## Mandatory projection surfaces",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md`"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _entry_marker_missing(required_markers: tuple[str, ...], expected_markers: tuple[str, ...]) -> list[str]:
    marker_set = {str(item or "").strip() for item in required_markers if str(item or "").strip()}
    return [marker for marker in expected_markers if marker not in marker_set]


def _surface_rows(surface_ids: tuple[str, ...]) -> tuple[SimpleNamespace, ...]:
    return tuple(SimpleNamespace(surface_id=surface_id) for surface_id in surface_ids)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root stream-design admissibility law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    admissibility_doc, admissibility_entry_path, admissibility_active_path, admissibility_alias_error = load_root_stream_design_admissibility(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    admissibility_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if admissibility_alias_error:
        stale_reasons.append(f"root_stream_design_admissibility_alias_error:{admissibility_alias_error}")
        error_code = ERR_REGISTRY
    elif not admissibility_doc:
        stale_reasons.append("root_stream_design_admissibility_empty_or_invalid")
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

    question_rows = required_question_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    proof_rows = admissibility_proof_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    limit_rows = admissibility_limit_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    outcome_rows = outcome_class_rows_from_doc(admissibility_doc) if admissibility_doc else ()
    projection_surfaces = required_projection_surfaces_from_doc(admissibility_doc) if admissibility_doc else ()
    projection_surface_rows = _surface_rows(projection_surfaces)
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "admissibility_family": "protocol_root_stream_design_admissibility",
            "admissibility_version": "v1",
            "contract_file": "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_stream_design_admissibility.py",
            "probe_script": "scripts/ci/run_protocol_root_stream_design_admissibility_probes_ci.sh",
            "common_script": "scripts/root_stream_design_admissibility_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(admissibility_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_stream_design_admissibility_field_invalid:{field}")
                error_code = ERR_REGISTRY

        if not question_rows:
            stale_reasons.append("root_stream_design_admissibility_question_rows_missing")
            error_code = ERR_REGISTRY
        if not proof_rows:
            stale_reasons.append("root_stream_design_admissibility_proof_rows_missing")
            error_code = ERR_REGISTRY
        if not limit_rows:
            stale_reasons.append("root_stream_design_admissibility_limit_rows_missing")
            error_code = ERR_REGISTRY
        if not outcome_rows:
            stale_reasons.append("root_stream_design_admissibility_outcome_rows_missing")
            error_code = ERR_REGISTRY
        if not projection_surfaces:
            stale_reasons.append("root_stream_design_admissibility_projection_surfaces_missing")
            error_code = ERR_REGISTRY
        if not admissibility_doc.get("contract_required_markers"):
            stale_reasons.append("root_stream_design_admissibility_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(admissibility_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_stream_design_admissibility_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_question_rows",
                member_id_key="question_id",
                actual_rows=question_rows,
                expected_rows=EXPECTED_QUESTION_ROWS,
                id_attr="question_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_admissibility_proof_rows",
                member_id_key="proof_id",
                actual_rows=proof_rows,
                expected_rows=EXPECTED_ADMISSIBILITY_PROOF_ROWS,
                id_attr="proof_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_admissibility_limit_rows",
                member_id_key="limit_id",
                actual_rows=limit_rows,
                expected_rows=EXPECTED_ADMISSIBILITY_LIMIT_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="admissibility_outcome_rows",
                member_id_key="outcome_class",
                actual_rows=outcome_rows,
                expected_rows={outcome_class: {"order": idx} for idx, outcome_class in enumerate(EXPECTED_OUTCOME_CLASSES, start=1)},
                id_attr="outcome_class",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_projection_surfaces",
                member_id_key="surface_id",
                actual_rows=projection_surface_rows,
                expected_rows={surface_id: {"order": idx} for idx, surface_id in enumerate(EXPECTED_PROJECTION_SURFACES, start=1)},
                id_attr="surface_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
        ]
        question_orders = [row.order for row in question_rows]
        proof_orders = [row.order for row in proof_rows]
        limit_orders = [row.order for row in limit_rows]
        outcome_orders = [row.order for row in outcome_rows]
        question_map = {row.question_id: row for row in question_rows}
        proof_map = {row.proof_id: row for row in proof_rows}
        limit_map = {row.row_id: row for row in limit_rows}
        if len(question_map) != len(question_rows):
            structure_violations.append({"field": "required_question_rows", "reason": "duplicate_question_id"})
        if len(proof_map) != len(proof_rows):
            structure_violations.append({"field": "required_admissibility_proof_rows", "reason": "duplicate_proof_id"})
        if len(limit_map) != len(limit_rows):
            structure_violations.append({"field": "required_admissibility_limit_rows", "reason": "duplicate_limit_id"})
        if len(set(question_orders)) != len(question_orders) or not _contiguous_orders(sorted(question_orders)):
            structure_violations.append({"field": "required_question_rows", "reason": "question_order_non_contiguous"})
        if len(set(proof_orders)) != len(proof_orders) or not _contiguous_orders(sorted(proof_orders)):
            structure_violations.append({"field": "required_admissibility_proof_rows", "reason": "proof_order_non_contiguous"})
        if len(set(limit_orders)) != len(limit_orders) or not _contiguous_orders(sorted(limit_orders)):
            structure_violations.append({"field": "required_admissibility_limit_rows", "reason": "limit_order_non_contiguous"})
        missing_questions = sorted(set(EXPECTED_QUESTION_ROWS) - set(question_map))
        extra_questions = sorted(set(question_map) - set(EXPECTED_QUESTION_ROWS))
        missing_proofs = sorted(set(EXPECTED_ADMISSIBILITY_PROOF_ROWS) - set(proof_map))
        extra_proofs = sorted(set(proof_map) - set(EXPECTED_ADMISSIBILITY_PROOF_ROWS))
        missing_limits = sorted(set(EXPECTED_ADMISSIBILITY_LIMIT_ROWS) - set(limit_map))
        extra_limits = sorted(set(limit_map) - set(EXPECTED_ADMISSIBILITY_LIMIT_ROWS))
        if missing_questions:
            structure_violations.append(
                {"field": "required_question_rows", "reason": "missing_expected_questions", "question_ids": missing_questions}
            )
        if extra_questions:
            structure_violations.append(
                {"field": "required_question_rows", "reason": "extra_questions", "question_ids": extra_questions}
            )
        if missing_proofs:
            structure_violations.append(
                {"field": "required_admissibility_proof_rows", "reason": "missing_expected_rows", "proof_ids": missing_proofs}
            )
        if extra_proofs:
            structure_violations.append(
                {"field": "required_admissibility_proof_rows", "reason": "extra_rows", "proof_ids": extra_proofs}
            )
        if missing_limits:
            structure_violations.append(
                {"field": "required_admissibility_limit_rows", "reason": "missing_expected_rows", "limit_ids": missing_limits}
            )
        if extra_limits:
            structure_violations.append(
                {"field": "required_admissibility_limit_rows", "reason": "extra_rows", "limit_ids": extra_limits}
            )
        for row in question_rows:
            expected = EXPECTED_QUESTION_ROWS.get(row.question_id)
            if expected is None:
                continue
            if row.order != expected["order"]:
                admissibility_violations.append(
                    {
                        "field": "required_question_rows",
                        "question_id": row.question_id,
                        "reason": "question_order_mismatch",
                        "expected": expected["order"],
                        "actual": row.order,
                    }
                )
            if row.contract_heading != expected["contract_heading"]:
                admissibility_violations.append(
                    {
                        "field": "required_question_rows",
                        "question_id": row.question_id,
                        "reason": "contract_heading_mismatch",
                        "expected": expected["contract_heading"],
                        "actual": row.contract_heading,
                    }
                )
            if row.normative_focus != expected["normative_focus"]:
                admissibility_violations.append(
                    {
                        "field": "required_question_rows",
                        "question_id": row.question_id,
                        "reason": "normative_focus_mismatch",
                        "expected": expected["normative_focus"],
                        "actual": row.normative_focus,
                    }
                )

        for row in proof_rows:
            expected = EXPECTED_ADMISSIBILITY_PROOF_ROWS.get(row.proof_id)
            if expected is None:
                continue
            if row.order != expected["order"]:
                admissibility_violations.append(
                    {
                        "field": "required_admissibility_proof_rows",
                        "proof_id": row.proof_id,
                        "reason": "proof_order_mismatch",
                        "expected": expected["order"],
                        "actual": row.order,
                    }
                )
            if row.contract_heading != expected["contract_heading"]:
                admissibility_violations.append(
                    {
                        "field": "required_admissibility_proof_rows",
                        "proof_id": row.proof_id,
                        "reason": "contract_heading_mismatch",
                        "expected": expected["contract_heading"],
                        "actual": row.contract_heading,
                    }
                )
            if row.proof_role != expected["proof_role"]:
                admissibility_violations.append(
                    {
                        "field": "required_admissibility_proof_rows",
                        "proof_id": row.proof_id,
                        "reason": "proof_role_mismatch",
                        "expected": expected["proof_role"],
                        "actual": row.proof_role,
                    }
                )

        for row in limit_rows:
            expected = EXPECTED_ADMISSIBILITY_LIMIT_ROWS.get(row.row_id)
            if expected is None:
                continue
            if row.order != expected["order"]:
                admissibility_violations.append(
                    {
                        "field": "required_admissibility_limit_rows",
                        "limit_id": row.row_id,
                        "reason": "limit_order_mismatch",
                        "expected": expected["order"],
                        "actual": row.order,
                    }
                )
            if row.contract_phrase != expected["contract_phrase"]:
                admissibility_violations.append(
                    {
                        "field": "required_admissibility_limit_rows",
                        "limit_id": row.row_id,
                        "reason": "contract_phrase_mismatch",
                        "expected": expected["contract_phrase"],
                        "actual": row.contract_phrase,
                    }
                )

        if len(set(outcome_orders)) != len(outcome_orders) or not _contiguous_orders(sorted(outcome_orders)):
            structure_violations.append({"field": "admissibility_outcome_rows", "reason": "outcome_order_non_contiguous"})
        actual_outcomes = tuple(row.outcome_class for row in sorted(outcome_rows, key=lambda item: item.order))
        if actual_outcomes != EXPECTED_OUTCOME_CLASSES:
            admissibility_violations.append(
                {
                    "field": "admissibility_outcome_rows",
                    "reason": "outcome_classes_mismatch",
                    "expected": list(EXPECTED_OUTCOME_CLASSES),
                    "actual": list(actual_outcomes),
                }
            )

        if tuple(projection_surfaces) != EXPECTED_PROJECTION_SURFACES:
            admissibility_violations.append(
                {
                    "field": "required_projection_surfaces",
                    "reason": "projection_surfaces_mismatch",
                    "expected": list(EXPECTED_PROJECTION_SURFACES),
                    "actual": list(projection_surfaces),
                }
            )

        contract_file = str(admissibility_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            admissibility_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in admissibility_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"rel_path": contract_file, "reason": "required_marker_missing", "marker": marker})
            for row in question_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"rel_path": contract_file, "reason": "question_heading_missing", "marker": marker})
            for row in proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"rel_path": contract_file, "reason": "proof_heading_missing", "marker": marker})
            for row in limit_rows:
                for marker in find_missing_markers(contract_text, (row.contract_phrase,)):
                    contract_marker_violations.append({"rel_path": contract_file, "reason": "limit_phrase_missing", "marker": marker})

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
                integration_violations.append(
                    {"field": "root_corpus_registry", "reason": "registry_entry_must_be_law_bearing"}
                )
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
            for child in ("root-stream-design-admissibility.current.yaml", "root-stream-design-admissibility.v1.yaml"):
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
        missing_authority_markers = _entry_marker_missing(
            authority_anchor_map.get(contract_file, ()),
            EXPECTED_AUTHORITY_MARKERS,
        )
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
        missing_routing_markers = _entry_marker_missing(
            routing_anchor_map.get(contract_file, ()),
            EXPECTED_ROUTING_MARKERS,
        )
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
    if not error_code and (admissibility_violations or integration_violations or contract_marker_violations):
        error_code = ERR_ADMISSIBILITY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"admissibility_violation:{row.get('field', 'contract_markers')}:{row['reason']}"
        for row in admissibility_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    stream_design_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    stream_design_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
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
        "question_count": len(question_rows),
        "proof_count": len(proof_rows),
        "limit_count": len(limit_rows),
        "outcome_count": len(outcome_rows),
        "projection_surface_count": len(projection_surfaces),
        "stream_design_row_family_count": len(row_family_projection_rows),
        "stream_design_row_coverage_status": stream_design_row_coverage_status,
        "stream_design_row_identity_projection_status": stream_design_row_identity_projection_status,
        "row_family_projection_rows": row_family_projection_rows,
        "question_ids": [row.question_id for row in sorted(question_rows, key=lambda item: item.order)],
        "proof_ids": [row.proof_id for row in sorted(proof_rows, key=lambda item: item.order)],
        "limit_ids": [row.row_id for row in sorted(limit_rows, key=lambda item: item.order)],
        "outcome_classes": [row.outcome_class for row in sorted(outcome_rows, key=lambda item: item.order)],
        "projection_surfaces": list(projection_surfaces),
        "structure_violations": structure_violations,
        "admissibility_violations": admissibility_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
