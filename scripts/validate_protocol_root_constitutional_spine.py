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
from root_contract_row_validation_common import contiguous_orders
from root_constitutional_spine_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    bridge_rows_from_doc,
    constitutional_entry_rows_from_doc,
    load_root_constitutional_spine,
)
from root_corpus_authority_common import entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import entry_question_projections_from_doc, load_root_corpus_question_routing
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family

STATUS_KEY = "protocol_root_constitutional_spine_status"
ERR_REGISTRY = "IP-RCS-001"
ERR_STRUCTURE = "IP-RCS-002"
ERR_SPINE = "IP-RCS-003"

EXPECTED_ENTRY_ROWS = {
    "identity/protocol/README.md": {
        "order": 1,
        "corpus_class": "root_index",
        "reading_order": 1,
        "entry_role": "root_index_entry_surface",
        "authority_role": "navigational_root_index",
        "authority_mode": "navigational_only",
        "question_classes": ("root_entry_navigation",),
        "required_markers": (
            "## Purpose",
            "## Root reading order",
            "## Root constitutional-spine discipline",
            "## Authority layering",
            "## Source-order, reading-order, and adjudication-order",
            "Constitutional-entry rows and spine-bridge rows must remain explicit as separate machine-governed families.",
        ),
    },
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": {
        "order": 2,
        "corpus_class": "bottom_theory",
        "reading_order": 2,
        "entry_role": "bottom_theory_entry",
        "authority_role": "interpretive_bottom_theory",
        "authority_mode": "interpretive_only",
        "question_classes": ("generative_why",),
        "required_markers": (
            "## Document Positioning",
            "## One-line motherline",
            "### Machine-world reading rule",
            "### Constitutional derivation order",
            "### Constitutional spine row-family completeness must stay explicit",
            "### Three orders must never be collapsed",
            "### Question class and answer surface must stay paired",
            "Constitutional-entry rows and spine-bridge rows must remain explicit as",
        ),
    },
    "identity/protocol/IDENTITY_PROTOCOL.md": {
        "order": 3,
        "corpus_class": "constitution",
        "reading_order": 3,
        "entry_role": "protocol_constitution_entry",
        "authority_role": "constitutional_protocol_law",
        "authority_mode": "frozen_law_only",
        "question_classes": ("frozen_protocol_law",),
        "required_markers": (
            "## Normative source map (current governed execution)",
            "## Foundational design philosophy boundary",
            "## Constitutional derivation discipline",
            "## Root constitutional-spine boundary",
            "## Root-law promotion and re-entry boundary",
            "## Root-law bundle boundary",
            "The root constitutional spine is governed as separate constitutional-entry and spine-bridge row families rather than as one narrative claim.",
        ),
    },
    "identity/protocol/IDENTITY_RUNTIME.md": {
        "order": 4,
        "corpus_class": "runtime_constitution",
        "reading_order": 4,
        "entry_role": "runtime_constitution_entry",
        "authority_role": "constitutional_runtime_law",
        "authority_mode": "frozen_law_only",
        "question_classes": ("frozen_runtime_law",),
        "required_markers": (
            "## Integration objective",
            "## Foundational design philosophy anchor",
            "## Runtime derivation boundary",
            "## Runtime constitutional-spine consumption boundary",
            "## Runtime-to-root promotion boundary",
            "## Runtime consumption of the root-law bundle",
            "Runtime consumes constitutional spine law as separate constitutional-entry and spine-bridge row families rather than as undifferentiated narrative context.",
        ),
    },
}
EXPECTED_BRIDGE_ROWS = {
    "philosophy_to_protocol_constitution": {
        "order": 1,
        "source_rel_path": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "source_markers": (
            "In other words, `IDENTITY_PROTOCOL.md` explains protocol objects and boundaries",
        ),
        "target_rel_path": "identity/protocol/IDENTITY_PROTOCOL.md",
        "target_markers": (
            "This file is therefore a protocol-law constitution derived from that bottom theory",
        ),
    },
    "philosophy_to_runtime_constitution": {
        "order": 2,
        "source_rel_path": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "source_markers": (
            "`IDENTITY_RUNTIME.md` explains runtime and integration behavior",
        ),
        "target_rel_path": "identity/protocol/IDENTITY_RUNTIME.md",
        "target_markers": (
            "runtime is an operational embodiment of protocol bottom theory",
        ),
    },
    "philosophy_to_protocol_machine_authority_split": {
        "order": 3,
        "source_rel_path": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "source_markers": ("philosophical primacy does not mean runtime-source primacy",),
        "target_rel_path": "identity/protocol/IDENTITY_PROTOCOL.md",
        "target_markers": (
            "Machine-consumed truth remains frozen in governance/review docs, mappings, validators, probes, runtime state, and receipts",
        ),
    },
    "philosophy_to_runtime_machine_authority_split": {
        "order": 4,
        "source_rel_path": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "source_markers": (
            "machine-consumed authority still lives in frozen contracts, mappings, validators, runtime state, and receipts",
        ),
        "target_rel_path": "identity/protocol/IDENTITY_RUNTIME.md",
        "target_markers": (
            "Current-turn runtime legality remains machine-consumed registry and enforcement truth, not raw runtime motivation records.",
        ),
    },
    "protocol_to_runtime_root_bundle_consumption": {
        "order": 5,
        "source_rel_path": "identity/protocol/IDENTITY_PROTOCOL.md",
        "source_markers": (
            "The protocol constitution depends on a governed root-law bundle across:",
        ),
        "target_rel_path": "identity/protocol/IDENTITY_RUNTIME.md",
        "target_markers": (
            "Runtime does not consume root law as isolated slogans.",
            "Runtime must consume the governed root-law bundle together:",
        ),
    },
}
EXPECTED_MAPPINGS_CHILDREN = (
    "root-constitutional-spine.current.yaml",
    "root-constitutional-spine.v1.yaml",
)
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Constitutional spine row-family completeness must stay explicit",
        "Constitutional-entry rows and spine-bridge rows must remain explicit as separate machine-law families.",
        "The machine world must not finalize constitutional-spine truth while missing or unexpected entry rel-paths or bridge ids remain known only inside validator logic.",
    ),
    "identity/protocol/README.md": (
        "## Root constitutional-spine discipline",
        "Constitutional-entry rows and spine-bridge rows must remain explicit as separate machine-governed families.",
        "Validator or runtime code must not finalize constitutional-spine truth while missing or unexpected entry rel-paths or bridge ids remain known only inside local machinery.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root constitutional-spine boundary",
        "1. The root constitutional spine is governed as separate constitutional-entry and spine-bridge row families rather than as one narrative claim.",
        "6. Protocol legality must not finalize constitutional-spine truth while missing or unexpected entry rel-paths or bridge ids remain known only inside validator machinery.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime constitutional-spine consumption boundary",
        "1. Runtime consumes constitutional spine law as separate constitutional-entry and spine-bridge row families rather than as undifferentiated narrative context.",
        "4. Runtime must not finalize constitutional-spine legality while missing or unexpected entry rel-paths or bridge ids remain known only inside validator machinery.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))



def _validate_entry_rows(entry_rows, structure_violations: list[dict[str, Any]]) -> None:
    entry_map = {row.rel_path: row for row in entry_rows}
    orders = [row.order for row in entry_rows]
    if len(entry_map) != len(entry_rows):
        structure_violations.append({"field": "required_constitutional_entry_rows", "reason": "duplicate_rel_path"})
    if len(set(orders)) != len(orders) or not contiguous_orders(sorted(orders)):
        structure_violations.append({"field": "required_constitutional_entry_rows", "reason": "entry_order_non_contiguous"})

    missing = sorted(set(EXPECTED_ENTRY_ROWS) - set(entry_map))
    extra = sorted(set(entry_map) - set(EXPECTED_ENTRY_ROWS))
    if missing:
        structure_violations.append(
            {"field": "required_constitutional_entry_rows", "reason": "missing_expected_rows", "row_ids": missing}
        )
    if extra:
        structure_violations.append(
            {"field": "required_constitutional_entry_rows", "reason": "unexpected_rows", "row_ids": extra}
        )

    for rel_path, expected in EXPECTED_ENTRY_ROWS.items():
        row = entry_map.get(rel_path)
        if row is None:
            continue
        for field in ("order", "corpus_class", "reading_order", "entry_role", "authority_role", "authority_mode"):
            if getattr(row, field) != expected[field]:
                structure_violations.append(
                    {
                        "field": "required_constitutional_entry_rows",
                        "reason": f"{field}_mismatch",
                        "row_id": rel_path,
                        "expected": expected[field],
                        "actual": getattr(row, field),
                    }
                )
        if tuple(row.question_classes) != expected["question_classes"]:
            structure_violations.append(
                {
                    "field": "required_constitutional_entry_rows",
                    "reason": "question_classes_mismatch",
                    "row_id": rel_path,
                    "expected": list(expected["question_classes"]),
                    "actual": list(row.question_classes),
                }
            )
        if tuple(row.required_markers) != expected["required_markers"]:
            structure_violations.append(
                {
                    "field": "required_constitutional_entry_rows",
                    "reason": "required_markers_mismatch",
                    "row_id": rel_path,
                }
            )


def _validate_bridge_rows(bridge_rows, structure_violations: list[dict[str, Any]]) -> None:
    bridge_map = {row.bridge_id: row for row in bridge_rows}
    orders = [row.order for row in bridge_rows]
    if len(bridge_map) != len(bridge_rows):
        structure_violations.append({"field": "required_spine_bridge_rows", "reason": "duplicate_bridge_id"})
    if len(set(orders)) != len(orders) or not contiguous_orders(sorted(orders)):
        structure_violations.append({"field": "required_spine_bridge_rows", "reason": "bridge_order_non_contiguous"})

    missing = sorted(set(EXPECTED_BRIDGE_ROWS) - set(bridge_map))
    extra = sorted(set(bridge_map) - set(EXPECTED_BRIDGE_ROWS))
    if missing:
        structure_violations.append(
            {"field": "required_spine_bridge_rows", "reason": "missing_expected_rows", "row_ids": missing}
        )
    if extra:
        structure_violations.append(
            {"field": "required_spine_bridge_rows", "reason": "unexpected_rows", "row_ids": extra}
        )

    for bridge_id, expected in EXPECTED_BRIDGE_ROWS.items():
        row = bridge_map.get(bridge_id)
        if row is None:
            continue
        for field in ("order", "source_rel_path", "target_rel_path"):
            if getattr(row, field) != expected[field]:
                structure_violations.append(
                    {
                        "field": "required_spine_bridge_rows",
                        "reason": f"{field}_mismatch",
                        "row_id": bridge_id,
                        "expected": expected[field],
                        "actual": getattr(row, field),
                    }
                )
        if tuple(row.source_markers) != expected["source_markers"]:
            structure_violations.append(
                {
                    "field": "required_spine_bridge_rows",
                    "reason": "source_markers_mismatch",
                    "row_id": bridge_id,
                }
            )
        if tuple(row.target_markers) != expected["target_markers"]:
            structure_violations.append(
                {
                    "field": "required_spine_bridge_rows",
                    "reason": "target_markers_mismatch",
                    "row_id": bridge_id,
                }
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the protocol-root constitutional spine.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    spine_doc, spine_entry_path, spine_active_path, spine_alias_error = load_root_constitutional_spine(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    projection_violations: list[dict[str, Any]] = []
    bridge_violations: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    error_code = ""

    for prefix, alias_error, empty_reason in (
        ("root_constitutional_spine", spine_alias_error, "root_constitutional_spine_empty_or_invalid"),
        ("root_corpus_registry", registry_alias_error, "root_corpus_registry_empty_or_invalid"),
        ("root_corpus_ordering", ordering_alias_error, "root_corpus_ordering_empty_or_invalid"),
        ("root_corpus_authority", authority_alias_error, "root_corpus_authority_empty_or_invalid"),
        ("root_corpus_question_routing", routing_alias_error, "root_corpus_question_routing_empty_or_invalid"),
    ):
        doc = {
            "root_constitutional_spine": spine_doc,
            "root_corpus_registry": registry_doc,
            "root_corpus_ordering": ordering_doc,
            "root_corpus_authority": authority_doc,
            "root_corpus_question_routing": routing_doc,
        }[prefix]
        if alias_error:
            stale_reasons.append(f"{prefix}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(empty_reason)
            error_code = ERR_REGISTRY

    entry_rows = constitutional_entry_rows_from_doc(spine_doc) if spine_doc else ()
    bridge_rows = bridge_rows_from_doc(spine_doc) if spine_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(spine_doc) if spine_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_rows = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    question_rows = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    row_family_projection_rows = [
        project_row_family(
            family_id="constitutional_entry_rows",
            member_id_key="rel_path",
            actual_rows=entry_rows,
            expected_rows=EXPECTED_ENTRY_ROWS,
            id_attr="rel_path",
        ),
        project_row_family(
            family_id="spine_bridge_rows",
            member_id_key="bridge_id",
            actual_rows=bridge_rows,
            expected_rows=EXPECTED_BRIDGE_ROWS,
            id_attr="bridge_id",
        ),
    ]
    row_family_projection_by_id = {row["family_id"]: row for row in row_family_projection_rows}

    if not stale_reasons:
        expected_fields = {
            "spine_family": "protocol_root_constitutional_spine",
            "spine_version": "v1",
            "root_dir": "identity/protocol",
            "validator_script": "scripts/validate_protocol_root_constitutional_spine.py",
            "probe_script": "scripts/ci/run_protocol_root_constitutional_spine_probes_ci.sh",
            "common_script": "scripts/root_constitutional_spine_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_fields.items():
            if str(spine_doc.get(field) or "").strip() != expected:
                stale_reasons.append(f"root_constitutional_spine_field_invalid:{field}")
                error_code = ERR_REGISTRY
        for field in (
            "validator_script",
            "probe_script",
            "common_script",
            "registry_current_file",
            "ordering_current_file",
            "authority_current_file",
            "question_routing_current_file",
        ):
            rel_path = str(spine_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_constitutional_spine_dependency_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not entry_rows:
            stale_reasons.append("root_constitutional_spine_entry_rows_missing")
            error_code = ERR_REGISTRY
        if not bridge_rows:
            stale_reasons.append("root_constitutional_spine_bridge_rows_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_constitutional_spine",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    if not stale_reasons:
        _validate_entry_rows(entry_rows, structure_violations)
        _validate_bridge_rows(bridge_rows, structure_violations)
        if structure_violations:
            error_code = ERR_STRUCTURE

    if not stale_reasons and not structure_violations:
        registry_map = {row.rel_path: row for row in registry_entries}
        reading_map = {row.rel_path: row for row in reading_rows}
        authority_map = {row.rel_path: row for row in authority_rows}
        question_map = {row.rel_path: row for row in question_rows}
        entry_map = {row.rel_path: row for row in entry_rows}

        mappings_entry = registry_map.get("identity/protocol/mappings")
        if mappings_entry is None:
            projection_violations.append(
                {"field": "root_corpus_registry", "reason": "mappings_directory_not_registered"}
            )
        else:
            for child in EXPECTED_MAPPINGS_CHILDREN:
                if child not in mappings_entry.required_children:
                    projection_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "mappings_required_child_missing",
                            "child": child,
                        }
                    )

        for row in entry_rows:
            rel_path = row.rel_path
            file_path = (repo_root / rel_path).resolve()
            if not file_path.exists():
                projection_violations.append(
                    {"field": "root_files", "reason": "entry_file_missing", "rel_path": rel_path}
                )
                continue
            text = file_path.read_text(encoding="utf-8")
            for marker in find_missing_markers(text, tuple(row.required_markers)):
                projection_violations.append(
                    {
                        "field": "entry_files",
                        "reason": "required_marker_missing",
                        "rel_path": rel_path,
                        "marker": marker,
                    }
                )

            registry_entry = registry_map.get(rel_path)
            if registry_entry is None:
                projection_violations.append(
                    {"field": "root_corpus_registry", "reason": "entry_not_registered", "rel_path": rel_path}
                )
            else:
                if registry_entry.entry_kind != "file":
                    projection_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "entry_kind_mismatch",
                            "rel_path": rel_path,
                            "expected": "file",
                            "actual": registry_entry.entry_kind,
                        }
                    )
                if registry_entry.corpus_class != row.corpus_class:
                    projection_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "corpus_class_mismatch",
                            "rel_path": rel_path,
                            "expected": row.corpus_class,
                            "actual": registry_entry.corpus_class,
                        }
                    )
                if not registry_entry.law_bearing:
                    projection_violations.append(
                        {
                            "field": "root_corpus_registry",
                            "reason": "law_bearing_false",
                            "rel_path": rel_path,
                        }
                    )

            reading_row = reading_map.get(rel_path)
            if reading_row is None:
                projection_violations.append(
                    {"field": "root_corpus_ordering", "reason": "reading_projection_missing", "rel_path": rel_path}
                )
            else:
                if reading_row.order != row.reading_order:
                    projection_violations.append(
                        {
                            "field": "root_corpus_ordering",
                            "reason": "reading_order_mismatch",
                            "rel_path": rel_path,
                            "expected": row.reading_order,
                            "actual": reading_row.order,
                        }
                    )
                if reading_row.entry_role != row.entry_role:
                    projection_violations.append(
                        {
                            "field": "root_corpus_ordering",
                            "reason": "entry_role_mismatch",
                            "rel_path": rel_path,
                            "expected": row.entry_role,
                            "actual": reading_row.entry_role,
                        }
                    )

            authority_row = authority_map.get(rel_path)
            if authority_row is None:
                projection_violations.append(
                    {"field": "root_corpus_authority", "reason": "authority_projection_missing", "rel_path": rel_path}
                )
            else:
                if authority_row.corpus_class != row.corpus_class:
                    projection_violations.append(
                        {
                            "field": "root_corpus_authority",
                            "reason": "authority_corpus_class_mismatch",
                            "rel_path": rel_path,
                            "expected": row.corpus_class,
                            "actual": authority_row.corpus_class,
                        }
                    )
                if authority_row.authority_role != row.authority_role:
                    projection_violations.append(
                        {
                            "field": "root_corpus_authority",
                            "reason": "authority_role_mismatch",
                            "rel_path": rel_path,
                            "expected": row.authority_role,
                            "actual": authority_row.authority_role,
                        }
                    )
                if authority_row.authority_mode != row.authority_mode:
                    projection_violations.append(
                        {
                            "field": "root_corpus_authority",
                            "reason": "authority_mode_mismatch",
                            "rel_path": rel_path,
                            "expected": row.authority_mode,
                            "actual": authority_row.authority_mode,
                        }
                    )

            question_row = question_map.get(rel_path)
            if question_row is None:
                projection_violations.append(
                    {"field": "root_corpus_question_routing", "reason": "question_projection_missing", "rel_path": rel_path}
                )
            else:
                if tuple(question_row.question_classes) != tuple(row.question_classes):
                    projection_violations.append(
                        {
                            "field": "root_corpus_question_routing",
                            "reason": "question_classes_mismatch",
                            "rel_path": rel_path,
                            "expected": list(row.question_classes),
                            "actual": list(question_row.question_classes),
                        }
                    )

        for bridge in bridge_rows:
            if bridge.source_rel_path not in entry_map:
                bridge_violations.append(
                    {
                        "field": "required_spine_bridge_rows",
                        "reason": "source_rel_path_not_in_entry_rows",
                        "bridge_id": bridge.bridge_id,
                        "rel_path": bridge.source_rel_path,
                    }
                )
                continue
            if bridge.target_rel_path not in entry_map:
                bridge_violations.append(
                    {
                        "field": "required_spine_bridge_rows",
                        "reason": "target_rel_path_not_in_entry_rows",
                        "bridge_id": bridge.bridge_id,
                        "rel_path": bridge.target_rel_path,
                    }
                )
                continue
            source_text = (repo_root / bridge.source_rel_path).read_text(encoding="utf-8")
            target_text = (repo_root / bridge.target_rel_path).read_text(encoding="utf-8")
            for marker in find_missing_markers(source_text, tuple(bridge.source_markers)):
                bridge_violations.append(
                    {
                        "field": "bridge_source",
                        "reason": "marker_missing",
                        "bridge_id": bridge.bridge_id,
                        "rel_path": bridge.source_rel_path,
                        "marker": marker,
                    }
                )
            for marker in find_missing_markers(target_text, tuple(bridge.target_markers)):
                bridge_violations.append(
                    {
                        "field": "bridge_target",
                        "reason": "marker_missing",
                        "bridge_id": bridge.bridge_id,
                        "rel_path": bridge.target_rel_path,
                        "marker": marker,
                    }
                )

        root_doc_anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                root_doc_anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

        if projection_violations or bridge_violations or root_doc_anchor_violations:
            error_code = ERR_SPINE

    status = STATUS_PASS_REQUIRED
    if stale_reasons or structure_violations or projection_violations or bridge_violations or root_doc_anchor_violations:
        status = STATUS_FAIL_REQUIRED

    payload = {
        STATUS_KEY: status,
        "spine_family": str(spine_doc.get("spine_family") or ""),
        "spine_version": str(spine_doc.get("spine_version") or ""),
        "mapping_entry_file": str(spine_entry_path.relative_to(repo_root)),
        "mapping_active_file": str(spine_active_path.relative_to(repo_root)),
        "spine_entry_count": len(entry_rows),
        "spine_bridge_count": len(bridge_rows),
        **project_root_contract_support_projection(
            prefix="constitutional_spine",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "constitutional_entry_row_coverage_status": row_family_projection_by_id["constitutional_entry_rows"][
            "coverage_status"
        ],
        "constitutional_entry_row_identity_projection_status": row_family_projection_by_id[
            "constitutional_entry_rows"
        ]["identity_projection_status"],
        "spine_bridge_row_coverage_status": row_family_projection_by_id["spine_bridge_rows"]["coverage_status"],
        "spine_bridge_row_identity_projection_status": row_family_projection_by_id["spine_bridge_rows"][
            "identity_projection_status"
        ],
        "spine_rel_paths": [row.rel_path for row in sorted(entry_rows, key=lambda item: item.order)],
        "spine_bridge_ids": [row.bridge_id for row in sorted(bridge_rows, key=lambda item: item.order)],
        "row_family_projection_rows": row_family_projection_rows,
        "structure_violations": structure_violations,
        "projection_violations": projection_violations,
        "bridge_violations": bridge_violations,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
        "error_code": error_code,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
