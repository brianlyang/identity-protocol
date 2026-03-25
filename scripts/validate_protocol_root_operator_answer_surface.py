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
from root_operator_answer_surface_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    boundary_rows_from_doc,
    collapse_rows_from_doc,
    load_root_operator_answer_surface,
    support_limit_rows_from_doc,
    support_memory_rows_from_doc,
    surface_rows_from_doc,
)

STATUS_KEY = "protocol_root_operator_answer_surface_status"
ERR_REGISTRY = "IP-ROAS-001"
ERR_STRUCTURE = "IP-ROAS-002"
ERR_ANSWER = "IP-ROAS-003"

EXPECTED_SURFACE_ROWS = {
    "operator_entry": {
        "order": 1,
        "contract_heading": "### 1. Operator entry surface",
        "surface_role": "natural_language_collaboration_entry",
    },
    "stable_instance_answer": {
        "order": 2,
        "contract_heading": "### 2. Stable instance answer surface",
        "surface_role": "law_compressed_operator_answer",
    },
    "supporting_machine_truth": {
        "order": 3,
        "contract_heading": "### 3. Supporting machine-truth surface",
        "surface_role": "supporting_machine_truth_surface",
    },
    "terminal_machine_enforcement": {
        "order": 4,
        "contract_heading": "### 4. Terminal machine-enforcement surface",
        "surface_role": "current_turn_legality_terminal",
    },
}
EXPECTED_SUPPORT_MEMORY_ROWS = {
    "law_memory_support": {
        "order": 1,
        "contract_heading": "### 1. Law-memory support",
        "support_role": "law_grounding_support",
    },
    "discovery_memory_support": {
        "order": 2,
        "contract_heading": "### 2. Discovery-memory support",
        "support_role": "discovery_grounding_support",
    },
    "admissibility_memory_support": {
        "order": 3,
        "contract_heading": "### 3. Admissibility-memory support",
        "support_role": "admissibility_grounding_support",
    },
    "run_binding_memory_support": {
        "order": 4,
        "contract_heading": "### 4. Run-binding-memory support",
        "support_role": "run_binding_grounding_support",
    },
    "consumption_memory_support": {
        "order": 5,
        "contract_heading": "### 5. Consumption-memory support",
        "support_role": "consumption_grounding_support",
    },
}
EXPECTED_SUPPORT_LIMIT_ROWS = {
    "law_memory_not_legality": {
        "order": 1,
        "contract_phrase": "law-memory support is not proof of current-turn legality;",
    },
    "discovery_memory_not_admissibility": {
        "order": 2,
        "contract_phrase": "discovery-memory support is not proof of admissibility;",
    },
    "admissibility_memory_not_run_binding": {
        "order": 3,
        "contract_phrase": "admissibility-memory support is not proof of run binding;",
    },
    "run_binding_memory_not_consumption": {
        "order": 4,
        "contract_phrase": "run-binding-memory support is not proof of next-hop consumption;",
    },
    "consumption_memory_realized_effect_only": {
        "order": 5,
        "contract_phrase": "only consumption-memory support may back claims of realized operational effect.",
    },
}
EXPECTED_BOUNDARY_ROWS = {
    "operator_memory_burden": {
        "order": 1,
        "contract_phrase": "the operator should not bear the memory burden of low-level protocol law;",
    },
    "support_not_answer": {
        "order": 2,
        "contract_phrase": "lower-layer proof may support the answer without replacing the answer surface itself;",
    },
    "compression_without_bypass": {
        "order": 3,
        "contract_phrase": "operator simplicity must be achieved by law-preserving compression rather than by bypassing machine-law boundaries;",
    },
    "terminality_not_answer_prose": {
        "order": 4,
        "contract_phrase": "current-turn legality must still terminate in machine-consumed enforcement surfaces rather than in answer prose alone.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "support_proof_equals_answer": {
        "order": 1,
        "contract_phrase": "supporting proof is treated as the operator answer itself.",
    },
    "raw_internal_artifact_dumping": {
        "order": 2,
        "contract_phrase": "internal artifacts or raw protocol burden are dumped directly onto the operator as if dumping were an answer surface.",
    },
    "convenience_overrides_law_compression": {
        "order": 3,
        "contract_phrase": "operator comfort or local convenience is used to bypass law-preserving compression and enforcement boundaries.",
    },
    "answer_surface_seized_by_terminality": {
        "order": 4,
        "contract_phrase": "a machine terminal or receipt blob is treated as if it were the operator collaboration surface.",
    },
    "prose_without_machine_truth": {
        "order": 5,
        "contract_phrase": "fluent answer prose is treated as sufficient despite missing machine-truth backing when such backing is required.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for operator answer-surface law",
    "## Operator answer-surface law",
    "## Four answer-surface strata",
    "## Lifecycle-aware support-memory discipline",
    "## Support-memory limits",
    "## Compression boundary",
    "## Non-compliant answer-surface collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`OPERATOR_ANSWER_SURFACE_CONTRACT.md`"


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
    answer_violations: list[dict[str, Any]],
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
            answer_violations.append(
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
                answer_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root operator answer-surface law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    answer_doc, answer_entry_path, answer_active_path, answer_alias_error = load_root_operator_answer_surface(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    answer_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    error_code = ""

    if answer_alias_error:
        stale_reasons.append(f"root_operator_answer_surface_alias_error:{answer_alias_error}")
        error_code = ERR_REGISTRY
    elif not answer_doc:
        stale_reasons.append("root_operator_answer_surface_empty_or_invalid")
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

    surface_rows = surface_rows_from_doc(answer_doc) if answer_doc else ()
    support_memory_rows = support_memory_rows_from_doc(answer_doc) if answer_doc else ()
    support_limit_rows = support_limit_rows_from_doc(answer_doc) if answer_doc else ()
    boundary_rows = boundary_rows_from_doc(answer_doc) if answer_doc else ()
    collapse_rows = collapse_rows_from_doc(answer_doc) if answer_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "answer_surface_family": "protocol_root_operator_answer_surface",
            "answer_surface_version": "v1",
            "contract_file": "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_operator_answer_surface.py",
            "probe_script": "scripts/ci/run_protocol_root_operator_answer_surface_probes_ci.sh",
            "common_script": "scripts/root_operator_answer_surface_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(answer_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_operator_answer_surface_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_surface_rows", surface_rows),
            ("required_support_memory_rows", support_memory_rows),
            ("required_support_limit_rows", support_limit_rows),
            ("required_boundary_rows", boundary_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_operator_answer_surface_{field}_missing")
                error_code = ERR_REGISTRY
        if not answer_doc.get("contract_required_markers"):
            stale_reasons.append("root_operator_answer_surface_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(answer_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_operator_answer_surface_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        _validate_rows(
            actual_rows=surface_rows,
            expected_rows=EXPECTED_SURFACE_ROWS,
            structure_violations=structure_violations,
            answer_violations=answer_violations,
            field_name="required_surface_rows",
            id_attr="surface_id",
            compare_fields=("contract_heading", "surface_role"),
        )
        _validate_rows(
            actual_rows=support_memory_rows,
            expected_rows=EXPECTED_SUPPORT_MEMORY_ROWS,
            structure_violations=structure_violations,
            answer_violations=answer_violations,
            field_name="required_support_memory_rows",
            id_attr="support_id",
            compare_fields=("contract_heading", "support_role"),
        )
        _validate_rows(
            actual_rows=support_limit_rows,
            expected_rows=EXPECTED_SUPPORT_LIMIT_ROWS,
            structure_violations=structure_violations,
            answer_violations=answer_violations,
            field_name="required_support_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=boundary_rows,
            expected_rows=EXPECTED_BOUNDARY_ROWS,
            structure_violations=structure_violations,
            answer_violations=answer_violations,
            field_name="required_boundary_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            answer_violations=answer_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(answer_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            answer_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in answer_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in surface_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "surface_heading_missing", "marker": marker})
            for row in support_memory_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "support_heading_missing", "marker": marker})
            for row in support_limit_rows + boundary_rows + collapse_rows:
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
            for child in ("root-operator-answer-surface.current.yaml", "root-operator-answer-surface.v1.yaml"):
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
    if not error_code and (answer_violations or integration_violations or contract_marker_violations):
        error_code = ERR_ANSWER

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"answer_surface_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in answer_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ANSWER),
        "answer_entry_path": str(answer_entry_path),
        "answer_active_path": str(answer_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(answer_doc.get("contract_file") or ""),
        "surface_count": len(surface_rows),
        "support_memory_count": len(support_memory_rows),
        "support_limit_count": len(support_limit_rows),
        "boundary_count": len(boundary_rows),
        "collapse_count": len(collapse_rows),
        "surface_ids": [row.surface_id for row in sorted(surface_rows, key=lambda item: item.order)],
        "support_memory_ids": [row.support_id for row in sorted(support_memory_rows, key=lambda item: item.order)],
        "support_limit_ids": [row.row_id for row in sorted(support_limit_rows, key=lambda item: item.order)],
        "boundary_ids": [row.row_id for row in sorted(boundary_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "answer_violations": answer_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
