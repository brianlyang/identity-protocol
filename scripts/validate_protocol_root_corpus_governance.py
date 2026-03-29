#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_contract_row_validation_common import contiguous_orders, validate_contract_row_batches
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_corpus_governance_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collect_protocol_root_top_level_entries,
    corpus_class_profiles_from_registry,
    forbidden_classes_from_registry,
    find_missing_markers,
    load_root_corpus_registry,
    merge_forbidden_content_classes,
    merge_required_markers,
    readme_root_maintenance_guardrail_surface,
    readme_root_index_class_projection_surface,
    root_index_class_projections_from_registry,
    root_maintenance_guardrails_from_registry,
    root_corpus_entries_from_registry,
    scan_forbidden_content,
)

STATUS_KEY = "protocol_root_corpus_governance_status"
ERR_REGISTRY = "IP-RCG-001"
ERR_STRUCTURE = "IP-RCG-002"
ERR_CONTENT = "IP-RCG-003"
ALLOWED_ENTRY_KINDS = {"file", "directory"}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Governance row-family completeness must stay explicit",
        "Required registered-top-level-entry, corpus-class-profile, root-index-class-projection, root-maintenance-guardrail, and forbidden-content-class families must remain explicit as separate machine-readable row families.",
        "README maintenance guardrails about how protocol root is authored and kept law-bearing must therefore stay bound to canonical guardrail rows rather than remaining reviewer-memory advice.",
        "The machine world must not finalize governance legality while required rel-path, corpus-class, root-index-class-projection, root-maintenance-guardrail, or forbidden-content-class identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root governance completeness discipline",
        "Governance law is not a soft prose bundle.",
        "1. required registered-top-level-entry, corpus-class-profile, root-index-class-projection, root-maintenance-guardrail, and forbidden-content-class rows must remain explicit as separate machine-readable row families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root governance completeness boundary",
        "1. Governance law must remain machine-readable as separate registered-top-level-entry, corpus-class-profile, root-index-class-projection, root-maintenance-guardrail, and forbidden-content-class row families.",
        "4. Protocol legality must not finalize governance legality while missing or unexpected rel-path, corpus-class, root-index-class-projection, root-maintenance-guardrail, or forbidden-content-class identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime governance consumption boundary",
        "1. Runtime consumes governance law as separate registered-top-level-entry, corpus-class-profile, root-index-class-projection, root-maintenance-guardrail, and forbidden-content-class row families rather than as undifferentiated governance prose.",
        "4. Runtime must not finalize governance legality while missing or unexpected rel-path, corpus-class, root-index-class-projection, root-maintenance-guardrail, or forbidden-content-class identities remain known only inside validator machinery.",
    ),
}

EXPECTED_ROOT_MAINTENANCE_GUARDRAILS = {
    "stream/version is manifestation, not origin": {
        "order": 1,
        "required_markers": (
            "stream or release labels mark governed freeze history;",
            "they do not become the philosophical source of protocol existence;",
            "no root contract should be written as if a stream label were prior to bottom theory.",
        ),
    },
    "machine verdict is adjudication, not philosophy source": {
        "order": 2,
        "required_markers": (
            "validators, probes, mappings, runtime state, and receipts determine current machine verdict;",
            "they do not retroactively define the meaning of design philosophy;",
            "philosophy explains why law has the shape it has, while machine-consumed surfaces decide current-turn legality.",
        ),
    },
    "root contracts must preserve layer clarity": {
        "order": 3,
        "required_markers": (
            "each root contract should state what bottom-theory commitments it inherits;",
            "each root contract should also state which concrete law it freezes;",
            "no root contract should blur philosophical grounding, contract freezing, and runtime-source authority into one layer.",
        ),
    },
    "root corpus admission must stay law-bearing": {
        "order": 4,
        "required_markers": (
            "the root directory should accept only bottom theory, constitutions, root contracts, machine-consumed registries/mappings, governed subdomain protocol packs, and clearly demoted support material;",
            "stream-local commentary, workbook material, business strategy, or workspace residue must not be promoted into protocol-root law-bearing position.",
        ),
    },
    "root-corpus admission must be machine-governed": {
        "order": 5,
        "required_markers": (
            "law-bearing admission, classification, and exclusion at `identity/protocol/` should be mirrored in protocol-owned registry / validator / probe surfaces rather than left to reviewer taste or oral memory;",
            "if root purity depends only on human recollection, the root corpus has already started to drift away from machine law.",
        ),
    },
    "protocol repo authority is exclusive": {
        "order": 6,
        "required_markers": (
            "protocol cleanliness, audit, commit admission, and release readiness for identity law must resolve only from the `identity-protocol-local` repository root;",
            "an enclosing workspace repo, instance repo, or other host container may physically contain the protocol checkout, but it remains non-authoritative for protocol-law verdicts;",
            "outer git dirty/clean state, top-level resolution, or history must not be projected as protocol repo truth.",
        ),
    },
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus governance and admission boundaries.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    registry_doc, registry_entry_path, registry_active_path, alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    file_violations: list[dict[str, Any]] = []
    directory_violations: list[dict[str, Any]] = []
    forbidden_hits: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    root_dir_rel = str(registry_doc.get("root_dir") or "identity/protocol").strip() if registry_doc else "identity/protocol"
    entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    content_classes = forbidden_classes_from_registry(registry_doc) if registry_doc else {}
    class_profiles = corpus_class_profiles_from_registry(registry_doc) if registry_doc else {}
    root_index_class_projections = root_index_class_projections_from_registry(registry_doc) if registry_doc else ()
    root_maintenance_guardrails = root_maintenance_guardrails_from_registry(registry_doc) if registry_doc else ()
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(registry_doc) if registry_doc else ()
    root_index_class_projection_surface = readme_root_index_class_projection_surface(repo_root)
    root_maintenance_guardrail_surface = readme_root_maintenance_guardrail_surface(repo_root)
    raw_forbidden_rows = registry_doc.get("forbidden_content_classes") if registry_doc else []
    raw_profile_rows = registry_doc.get("corpus_class_profiles") if registry_doc else []
    raw_root_index_projection_rows = registry_doc.get("root_index_class_projections") if registry_doc else []
    raw_root_maintenance_guardrail_rows = registry_doc.get("root_maintenance_guardrails") if registry_doc else []
    raw_forbidden_ids = [
        str(row.get("class_id") or "").strip()
        for row in raw_forbidden_rows
        if isinstance(row, dict) and str(row.get("class_id") or "").strip()
    ]
    raw_profile_ids = [
        str(row.get("corpus_class") or "").strip()
        for row in raw_profile_rows
        if isinstance(row, dict) and str(row.get("corpus_class") or "").strip()
    ]
    raw_root_index_projection_labels = [
        str(row.get("projection_label") or "").strip()
        for row in raw_root_index_projection_rows
        if isinstance(row, dict) and str(row.get("projection_label") or "").strip()
    ]
    raw_root_maintenance_guardrail_labels = [
        str(row.get("guardrail_label") or "").strip()
        for row in raw_root_maintenance_guardrail_rows
        if isinstance(row, dict) and str(row.get("guardrail_label") or "").strip()
    ]
    expected_profile_ids = sorted({entry.corpus_class for entry in entries if entry.law_bearing and entry.entry_kind == "file"})
    expected_root_index_bound_corpus_classes = sorted({entry.corpus_class for entry in entries if entry.corpus_class != "root_index"})
    expected_forbidden_ids = sorted(
        {class_id for entry in entries for class_id in entry.forbidden_content_classes}
        | {class_id for profile in class_profiles.values() for class_id in profile.forbidden_content_classes}
    )

    if not stale_reasons:
        if str(registry_doc.get("registry_family") or "").strip() != "protocol_root_corpus":
            stale_reasons.append("root_corpus_registry_family_invalid")
            error_code = ERR_REGISTRY
        if str(registry_doc.get("registry_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_registry_version_invalid")
            error_code = ERR_REGISTRY
        if not entries:
            stale_reasons.append("root_corpus_entries_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_class_profiles_missing")
            error_code = ERR_REGISTRY
        if not root_index_class_projections:
            stale_reasons.append("root_index_class_projections_missing")
            error_code = ERR_REGISTRY
        if not root_maintenance_guardrails:
            stale_reasons.append("root_maintenance_guardrails_missing")
            error_code = ERR_REGISTRY
        for key in ("validator_script", "probe_script", "common_script"):
            rel_path = str(registry_doc.get(key) or "").strip()
            if not rel_path:
                stale_reasons.append(f"root_corpus_registry_missing_field:{key}")
                error_code = ERR_REGISTRY
                continue
            if not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_corpus_registry_control_surface_missing:{key}:{rel_path}")
                error_code = ERR_REGISTRY
        for class_id, content_class in content_classes.items():
            if not content_class.patterns:
                stale_reasons.append(f"root_corpus_forbidden_class_missing_patterns:{class_id}")
                error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_governance",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    root_dir = (repo_root / root_dir_rel).resolve()
    if not stale_reasons and (not root_dir.exists() or not root_dir.is_dir()):
        stale_reasons.append(f"root_corpus_root_dir_missing:{root_dir_rel}")
        error_code = ERR_STRUCTURE

    registered_paths = sorted({entry.rel_path for entry in entries})
    actual_paths = collect_protocol_root_top_level_entries(repo_root, root_dir_rel) if root_dir.exists() else []

    if not stale_reasons:
        projection_orders = [row.order for row in root_index_class_projections]
        projection_labels = [row.projection_label for row in root_index_class_projections]
        bound_projection_corpus_classes = [
            corpus_class
            for row in root_index_class_projections
            for corpus_class in row.bound_corpus_classes
        ]
        surface_orders = [row.order for row in root_index_class_projection_surface.rows]
        surface_labels = [row.projection_label for row in root_index_class_projection_surface.rows]
        guardrail_orders = [row.order for row in root_maintenance_guardrails]
        guardrail_labels = [row.guardrail_label for row in root_maintenance_guardrails]
        guardrail_surface_orders = [row.order for row in root_maintenance_guardrail_surface.rows]
        guardrail_surface_labels = [row.guardrail_label for row in root_maintenance_guardrail_surface.rows]
        if len(set(projection_orders)) != len(projection_orders) or not contiguous_orders(sorted(projection_orders)):
            structure_violations.append(
                {"field": "root_index_class_projections", "reason": "projection_order_non_contiguous"}
            )
        if len(set(projection_labels)) != len(projection_labels):
            structure_violations.append(
                {"field": "root_index_class_projections", "reason": "duplicate_projection_label"}
            )
        for row in root_index_class_projections:
            if not row.bound_corpus_classes:
                structure_violations.append(
                    {
                        "field": "root_index_class_projections",
                        "reason": "bound_corpus_classes_missing",
                        "projection_label": row.projection_label,
                    }
                )
            if not row.required_markers:
                structure_violations.append(
                    {
                        "field": "root_index_class_projections",
                        "reason": "required_markers_missing",
                        "projection_label": row.projection_label,
                    }
                )
        if surface_orders and (
            len(set(surface_orders)) != len(surface_orders)
            or not contiguous_orders(sorted(surface_orders))
        ):
            structure_violations.append(
                {"field": "root_index_class_projection_surface", "reason": "projection_order_non_contiguous"}
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": root_maintenance_guardrails,
                    "expected_rows": EXPECTED_ROOT_MAINTENANCE_GUARDRAILS,
                    "field_name": "root_maintenance_guardrails",
                    "id_attr": "guardrail_label",
                    "compare_fields": ("required_markers",),
                    "duplicate_reason": "duplicate_guardrail_label",
                    "non_contiguous_reason": "guardrail_order_non_contiguous",
                    "missing_reason": "missing_root_maintenance_guardrails",
                    "extra_reason": "extra_root_maintenance_guardrails",
                    "missing_ids_key": "guardrail_labels",
                    "extra_ids_key": "guardrail_labels",
                    "violation_id_key": "guardrail_label",
                },
            ),
            structure_violations=structure_violations,
            support_violations=structure_violations,
        )
        if guardrail_surface_orders and (
            len(set(guardrail_surface_orders)) != len(guardrail_surface_orders)
            or not contiguous_orders(sorted(guardrail_surface_orders))
        ):
            structure_violations.append(
                {"field": "root_maintenance_guardrail_surface", "reason": "guardrail_order_non_contiguous"}
            )
        append_membership_delta_violations(
            structure_violations,
            field_name="registered_top_level_entries",
            expected_ids=registered_paths,
            actual_ids=actual_paths,
            payload_key="rel_paths",
            missing_reason="missing_root_entries",
            extra_reason="extra_root_entries",
            duplicate_reason="duplicate_rel_path",
            actual_total_count=len(actual_paths),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="corpus_class_profiles",
            expected_ids=expected_profile_ids,
            actual_ids=class_profiles,
            payload_key="corpus_classes",
            missing_reason="missing_expected_corpus_classes",
            extra_reason="extra_unreferenced_corpus_classes",
            duplicate_reason="duplicate_corpus_class",
            actual_total_count=len(raw_profile_ids),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="root_index_class_projections",
            expected_ids=expected_root_index_bound_corpus_classes,
            actual_ids=bound_projection_corpus_classes,
            payload_key="corpus_classes",
            missing_reason="missing_expected_bound_corpus_classes",
            extra_reason="extra_unexpected_bound_corpus_classes",
            duplicate_reason="duplicate_bound_corpus_class",
            actual_total_count=len(bound_projection_corpus_classes),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="root_index_class_projection_surface",
            expected_ids=projection_labels,
            actual_ids=surface_labels,
            payload_key="projection_labels",
            missing_reason="missing_root_index_projection_labels",
            extra_reason="extra_root_index_projection_labels",
            duplicate_reason="duplicate_root_index_projection_label",
            actual_total_count=len(surface_labels),
        )
        if surface_labels and tuple(surface_labels) != tuple(projection_labels):
            structure_violations.append(
                {
                    "field": "root_index_class_projection_surface",
                    "reason": "projection_label_order_mismatch",
                    "expected": projection_labels,
                    "actual": surface_labels,
                }
            )
        if surface_orders and tuple(surface_orders) != tuple(projection_orders):
            structure_violations.append(
                {
                    "field": "root_index_class_projection_surface",
                    "reason": "projection_order_mismatch",
                    "expected": projection_orders,
                    "actual": surface_orders,
                }
            )
        append_membership_delta_violations(
            structure_violations,
            field_name="root_maintenance_guardrail_surface",
            expected_ids=EXPECTED_ROOT_MAINTENANCE_GUARDRAILS.keys(),
            actual_ids=guardrail_surface_labels,
            payload_key="guardrail_labels",
            missing_reason="missing_root_maintenance_guardrail_labels",
            extra_reason="extra_root_maintenance_guardrail_labels",
            duplicate_reason="duplicate_root_maintenance_guardrail_label",
            actual_total_count=len(guardrail_surface_labels),
        )
        if guardrail_surface_labels and tuple(guardrail_surface_labels) != tuple(guardrail_labels):
            structure_violations.append(
                {
                    "field": "root_maintenance_guardrail_surface",
                    "reason": "guardrail_label_order_mismatch",
                    "expected": guardrail_labels,
                    "actual": guardrail_surface_labels,
                }
            )
        if guardrail_surface_orders and tuple(guardrail_surface_orders) != tuple(guardrail_orders):
            structure_violations.append(
                {
                    "field": "root_maintenance_guardrail_surface",
                    "reason": "guardrail_order_mismatch",
                    "expected": guardrail_orders,
                    "actual": guardrail_surface_orders,
                }
            )
        append_membership_delta_violations(
            structure_violations,
            field_name="forbidden_content_classes",
            expected_ids=expected_forbidden_ids,
            actual_ids=content_classes,
            payload_key="class_ids",
            missing_reason="missing_expected_class_ids",
            extra_reason="extra_unreferenced_class_ids",
            duplicate_reason="duplicate_class_id",
            actual_total_count=len(raw_forbidden_ids),
        )

    if not stale_reasons:
        for entry in entries:
            if entry.entry_kind not in ALLOWED_ENTRY_KINDS:
                stale_reasons.append(f"root_corpus_entry_kind_invalid:{entry.rel_path}:{entry.entry_kind}")
                error_code = ERR_REGISTRY
                continue
            path = (repo_root / entry.rel_path).resolve()
            if entry.entry_kind == "file":
                if not path.exists() or not path.is_file():
                    file_violations.append({"rel_path": entry.rel_path, "reason": "file_missing"})
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                missing_markers = find_missing_markers(
                    text,
                    merge_required_markers(entry, class_profiles=class_profiles),
                )
                for marker in missing_markers:
                    file_violations.append(
                        {"rel_path": entry.rel_path, "reason": "required_marker_missing", "marker": marker}
                    )
                for hit in scan_forbidden_content(
                    text,
                    content_classes=content_classes,
                    class_ids=merge_forbidden_content_classes(entry, class_profiles=class_profiles),
                ):
                    forbidden_hits.append(
                        {
                            "rel_path": entry.rel_path,
                            "class_id": hit.class_id,
                            "pattern": hit.pattern,
                            "line_no": hit.line_no,
                            "line_excerpt": hit.line_excerpt,
                        }
                    )
            else:
                if not path.exists() or not path.is_dir():
                    directory_violations.append({"rel_path": entry.rel_path, "reason": "directory_missing"})
                    continue
                for child in entry.required_children:
                    child_path = (path / child).resolve()
                    if not child_path.exists():
                        directory_violations.append(
                            {
                                "rel_path": entry.rel_path,
                                "reason": "required_child_missing",
                                "child": child,
                            }
                        )

        for reason in root_index_class_projection_surface.extraction_violations:
            file_violations.append(
                {
                    "rel_path": root_index_class_projection_surface.rel_path,
                    "reason": f"root_index_class_projection_surface_{reason}",
                }
            )
        surface_row_map = {
            row.projection_label: row for row in root_index_class_projection_surface.rows
        }
        for row in root_index_class_projections:
            surface_row = surface_row_map.get(row.projection_label)
            if surface_row is None:
                continue
            surface_text = "\n".join(surface_row.body_lines)
            for marker in find_missing_markers(surface_text, row.required_markers):
                file_violations.append(
                    {
                        "rel_path": root_index_class_projection_surface.rel_path,
                        "reason": "root_index_class_projection_marker_missing",
                        "projection_label": row.projection_label,
                        "marker": marker,
                    }
                )
        for reason in root_maintenance_guardrail_surface.extraction_violations:
            file_violations.append(
                {
                    "rel_path": root_maintenance_guardrail_surface.rel_path,
                    "reason": f"root_maintenance_guardrail_surface_{reason}",
                }
            )
        guardrail_surface_row_map = {
            row.guardrail_label: row for row in root_maintenance_guardrail_surface.rows
        }
        for row in root_maintenance_guardrails:
            surface_row = guardrail_surface_row_map.get(row.guardrail_label)
            if surface_row is None:
                continue
            surface_text = "\n".join(surface_row.body_lines)
            for marker in find_missing_markers(surface_text, row.required_markers):
                file_violations.append(
                    {
                        "rel_path": root_maintenance_guardrail_surface.rel_path,
                        "reason": "root_maintenance_guardrail_marker_missing",
                        "guardrail_label": row.guardrail_label,
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

    if not error_code and (structure_violations or file_violations or directory_violations or root_doc_anchor_violations):
        error_code = ERR_STRUCTURE
    if not error_code and forbidden_hits:
        error_code = ERR_CONTENT

    stale_reasons.extend(
        f"structure_violation:{item['field']}:{item['reason']}"
        for item in structure_violations
    )
    stale_reasons.extend(
        ":".join(
            token
            for token in (
                "file_violation",
                item["rel_path"],
                item["reason"],
                item.get("projection_label", ""),
                item.get("guardrail_label", ""),
                item.get("marker", ""),
            )
            if token
        )
        for item in file_violations
    )
    stale_reasons.extend(
        f"directory_violation:{item['rel_path']}:{item['reason']}:{item.get('child', '')}".rstrip(":")
        for item in directory_violations
    )
    stale_reasons.extend(
        f"forbidden_content:{item['rel_path']}:{item['class_id']}:{item['line_no']}" for item in forbidden_hits
    )
    stale_reasons.extend(
        ":".join(
            token
            for token in (
                "root_doc_anchor_violation",
                item["rel_path"],
                item["reason"],
                item.get("marker", ""),
            )
            if token
        )
        for item in root_doc_anchor_violations
    )

    status = (
        STATUS_PASS_REQUIRED
        if not (stale_reasons or root_doc_anchor_violations)
        else STATUS_FAIL_REQUIRED
    )
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "registered_top_level_entries",
                "member_id_key": "rel_path",
                "actual_rows": [SimpleNamespace(rel_path=rel_path) for rel_path in actual_paths],
                "expected_rows": {rel_path: {} for rel_path in registered_paths},
                "id_attr": "rel_path",
            },
            {
                "family_id": "corpus_class_profiles",
                "member_id_key": "corpus_class",
                "actual_rows": [SimpleNamespace(corpus_class=corpus_class) for corpus_class in sorted(class_profiles.keys())],
                "expected_rows": {corpus_class: {} for corpus_class in expected_profile_ids},
                "id_attr": "corpus_class",
            },
            {
                "family_id": "root_index_class_projections",
                "member_id_key": "projection_label",
                "actual_rows": [SimpleNamespace(projection_label=row.projection_label) for row in root_index_class_projections],
                "expected_rows": {row.projection_label: {} for row in root_index_class_projections},
                "id_attr": "projection_label",
            },
            {
                "family_id": "root_index_class_projection_surface",
                "member_id_key": "projection_label",
                "actual_rows": [SimpleNamespace(projection_label=row.projection_label) for row in root_index_class_projection_surface.rows],
                "expected_rows": {row.projection_label: {} for row in root_index_class_projections},
                "id_attr": "projection_label",
            },
            {
                "family_id": "root_maintenance_guardrails",
                "member_id_key": "guardrail_label",
                "actual_rows": [SimpleNamespace(guardrail_label=row.guardrail_label) for row in root_maintenance_guardrails],
                "expected_rows": {label: {} for label in EXPECTED_ROOT_MAINTENANCE_GUARDRAILS},
                "id_attr": "guardrail_label",
            },
            {
                "family_id": "root_maintenance_guardrail_surface",
                "member_id_key": "guardrail_label",
                "actual_rows": [SimpleNamespace(guardrail_label=row.guardrail_label) for row in root_maintenance_guardrail_surface.rows],
                "expected_rows": {label: {} for label in EXPECTED_ROOT_MAINTENANCE_GUARDRAILS},
                "id_attr": "guardrail_label",
            },
            {
                "family_id": "forbidden_content_classes",
                "member_id_key": "class_id",
                "actual_rows": [SimpleNamespace(class_id=class_id) for class_id in sorted(content_classes.keys())],
                "expected_rows": {class_id: {} for class_id in expected_forbidden_ids},
                "id_attr": "class_id",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_CONTENT),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "root_dir": root_dir_rel,
        "registered_top_level_entries": registered_paths,
        "actual_top_level_entries": actual_paths,
        "registered_top_level_count": len(registered_paths),
        "actual_top_level_count": len(actual_paths),
        "law_bearing_entry_count": sum(1 for entry in entries if entry.law_bearing),
        "validated_file_count": sum(1 for entry in entries if entry.entry_kind == "file"),
        "validated_directory_count": sum(1 for entry in entries if entry.entry_kind == "directory"),
        **project_root_contract_support_projection(
            prefix="governance",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "corpus_class_profile_ids": sorted(class_profiles.keys()),
        "corpus_class_profile_count": len(class_profiles),
        "root_index_class_projections": [
            {
                "order": row.order,
                "projection_label": row.projection_label,
                "bound_corpus_classes": list(row.bound_corpus_classes),
                "required_markers": list(row.required_markers),
            }
            for row in sorted(root_index_class_projections, key=lambda item: item.order)
        ],
        "root_index_class_projection_count": len(root_index_class_projections),
        "root_index_class_projection_surface": {
            "rel_path": root_index_class_projection_surface.rel_path,
            "entry_count": len(root_index_class_projection_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "projection_label": row.projection_label,
                    "body_lines": list(row.body_lines),
                }
                for row in root_index_class_projection_surface.rows
            ],
            "extraction_violations": list(root_index_class_projection_surface.extraction_violations),
        },
        "root_maintenance_guardrails": [
            {
                "order": row.order,
                "guardrail_label": row.guardrail_label,
                "required_markers": list(row.required_markers),
            }
            for row in sorted(root_maintenance_guardrails, key=lambda item: item.order)
        ],
        "root_maintenance_guardrail_count": len(root_maintenance_guardrails),
        "root_maintenance_guardrail_surface": {
            "rel_path": root_maintenance_guardrail_surface.rel_path,
            "entry_count": len(root_maintenance_guardrail_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "guardrail_label": row.guardrail_label,
                    "body_lines": list(row.body_lines),
                }
                for row in root_maintenance_guardrail_surface.rows
            ],
            "extraction_violations": list(root_maintenance_guardrail_surface.extraction_violations),
        },
        "forbidden_content_class_ids": sorted(content_classes.keys()),
        "structure_violations": structure_violations,
        "file_violations": file_violations,
        "directory_violations": directory_violations,
        "forbidden_content_hits": forbidden_hits,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
