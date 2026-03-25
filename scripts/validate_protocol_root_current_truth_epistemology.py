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
from root_current_truth_epistemology_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    commitment_rows_from_doc,
    differentiation_rows_from_doc,
    load_root_current_truth_epistemology,
)

STATUS_KEY = "protocol_root_current_truth_epistemology_status"
ERR_REGISTRY = "IP-CTE-001"
ERR_STRUCTURE = "IP-CTE-002"
ERR_EPISTEMOLOGY = "IP-CTE-003"

EXPECTED_COMMITMENT_ROWS = {
    "canonical_source_before_narration": {
        "order": 1,
        "contract_heading": "### 1. Canonical source before narration",
        "epistemic_role": "canonical_source_before_narration",
    },
    "governed_resolution_before_historical_familiarity": {
        "order": 2,
        "contract_heading": "### 2. Governed resolution before historical familiarity",
        "epistemic_role": "governed_resolution_before_historical_familiarity",
    },
    "present_turn_authority_before_visible_recency": {
        "order": 3,
        "contract_heading": "### 3. Present-turn authority before visible recency",
        "epistemic_role": "present_turn_authority_before_visible_recency",
    },
    "provenance_preserving_derivation_before_compressed_summary": {
        "order": 4,
        "contract_heading": "### 4. Provenance-preserving derivation before compressed summary",
        "epistemic_role": "provenance_preserving_derivation_before_compressed_summary",
    },
    "fail_close_justification_before_operational_assertion": {
        "order": 5,
        "contract_heading": "### 5. Fail-close justification before operational assertion",
        "epistemic_role": "fail_close_justification_before_operational_assertion",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "installed_vs_discoverability": {
        "order": 1,
        "contract_phrase": "installed and discoverability are separated;",
    },
    "latest_receipt_vs_current_thread_binding": {
        "order": 2,
        "contract_phrase": "latest receipt and current-thread binding are separated;",
    },
    "continuity_vs_authority": {
        "order": 3,
        "contract_phrase": "continuity and authority are separated;",
    },
    "durable_family_vs_runtime_family": {
        "order": 4,
        "contract_phrase": "pack durable families and runtime families are separated;",
    },
    "retention_governance_feedback_continuity_absorption": {
        "order": 5,
        "contract_phrase": "dialogue-retention, dialogue-governance, protocol-feedback, continuity, and memory-absorption are separated;",
    },
    "declaration_gate_vs_artifact_sink": {
        "order": 6,
        "contract_phrase": "declaration / gate surfaces and artifact sinks are separated.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "narration_as_current_truth": {
        "order": 1,
        "contract_phrase": "narrative recollection or self-claim is treated as if it were canonical present truth.",
    },
    "guesswork_as_authority": {
        "order": 2,
        "contract_phrase": "plausibility, intuition, or guesswork is treated as if it were admissible authority.",
    },
    "historical_accident_as_resolution": {
        "order": 3,
        "contract_phrase": "a path, state, or artifact is treated as authoritative merely because it happened to work in history.",
    },
    "implicit_habit_as_canonical_source": {
        "order": 4,
        "contract_phrase": "local habit or convenience memory is treated as if it resolved the canonical source.",
    },
    "compatibility_residue_as_truth": {
        "order": 5,
        "contract_phrase": "compatibility residue or leftover implementation drift is treated as if it justified present truth.",
    },
    "derived_projection_as_truth": {
        "order": 6,
        "contract_phrase": "a projection, inference, or compressed summary is treated as if it were the source truth itself.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for current-truth epistemology law",
    "## Current-truth epistemology law",
    "## Five epistemic commitments",
    "## Required epistemic differentiations",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn epistemic legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md`"


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
    epistemology_violations: list[dict[str, Any]],
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
            epistemology_violations.append(
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
                epistemology_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root current-truth epistemology law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    epistemology_doc, epistemology_entry_path, epistemology_active_path, epistemology_alias_error = load_root_current_truth_epistemology(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    epistemology_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    error_code = ""

    if epistemology_alias_error:
        stale_reasons.append(f"root_current_truth_epistemology_alias_error:{epistemology_alias_error}")
        error_code = ERR_REGISTRY
    elif not epistemology_doc:
        stale_reasons.append("root_current_truth_epistemology_empty_or_invalid")
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

    commitment_rows = commitment_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    differentiation_rows = differentiation_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    collapse_rows = collapse_rows_from_doc(epistemology_doc) if epistemology_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "epistemology_family": "protocol_root_current_truth_epistemology",
            "epistemology_version": "v1",
            "contract_file": "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_current_truth_epistemology.py",
            "probe_script": "scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
            "common_script": "scripts/root_current_truth_epistemology_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(epistemology_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_current_truth_epistemology_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_commitment_rows", commitment_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_current_truth_epistemology_{field}_missing")
                error_code = ERR_REGISTRY
        if not epistemology_doc.get("contract_required_markers"):
            stale_reasons.append("root_current_truth_epistemology_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(epistemology_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_current_truth_epistemology_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        _validate_rows(
            actual_rows=commitment_rows,
            expected_rows=EXPECTED_COMMITMENT_ROWS,
            structure_violations=structure_violations,
            epistemology_violations=epistemology_violations,
            field_name="required_commitment_rows",
            id_attr="commitment_id",
            compare_fields=("contract_heading", "epistemic_role"),
        )
        _validate_rows(
            actual_rows=differentiation_rows,
            expected_rows=EXPECTED_DIFFERENTIATION_ROWS,
            structure_violations=structure_violations,
            epistemology_violations=epistemology_violations,
            field_name="required_differentiation_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            epistemology_violations=epistemology_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(epistemology_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            epistemology_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in epistemology_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in commitment_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "commitment_heading_missing", "marker": marker})
            for row in differentiation_rows + collapse_rows:
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
            for child in ("root-current-truth-epistemology.current.yaml", "root-current-truth-epistemology.v1.yaml"):
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
    if not error_code and (epistemology_violations or integration_violations or contract_marker_violations):
        error_code = ERR_EPISTEMOLOGY

    stale_reasons.extend(f"structural_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"current_truth_epistemology_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in epistemology_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_EPISTEMOLOGY),
        "epistemology_entry_path": str(epistemology_entry_path),
        "epistemology_active_path": str(epistemology_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(epistemology_doc.get("contract_file") or ""),
        "commitment_count": len(commitment_rows),
        "differentiation_count": len(differentiation_rows),
        "collapse_count": len(collapse_rows),
        "commitment_ids": [row.commitment_id for row in sorted(commitment_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "epistemology_violations": epistemology_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
