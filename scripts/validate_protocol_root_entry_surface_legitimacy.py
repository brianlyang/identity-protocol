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
from root_entry_surface_legitimacy_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collapse_rows_from_doc,
    differentiation_rows_from_doc,
    entry_admission_limit_rows_from_doc,
    entry_admission_proof_rows_from_doc,
    entry_class_rows_from_doc,
    load_root_entry_surface_legitimacy,
)

STATUS_KEY = "protocol_root_entry_surface_legitimacy_status"
ERR_REGISTRY = "IP-ESL-001"
ERR_STRUCTURE = "IP-ESL-002"
ERR_ENTRY_LEGITIMACY = "IP-ESL-003"

EXPECTED_ENTRY_CLASS_ROWS = {
    "frozen_entry_definition": {
        "order": 1,
        "contract_heading": "### 1. Frozen entry definition",
        "entry_role": "frozen_entry_definition",
    },
    "natural_language_collaboration_entry_surface": {
        "order": 2,
        "contract_heading": "### 2. Natural-language collaboration entry surface",
        "entry_role": "natural_language_collaboration_entry_surface",
    },
    "governed_execution_entry_surface": {
        "order": 3,
        "contract_heading": "### 3. Governed execution entry surface",
        "entry_role": "governed_execution_entry_surface",
    },
    "governed_recovery_only_entry_surface": {
        "order": 4,
        "contract_heading": "### 4. Governed recovery-only entry surface",
        "entry_role": "governed_recovery_only_entry_surface",
    },
    "discoverability_helper_surface": {
        "order": 5,
        "contract_heading": "### 5. Discoverability-helper surface",
        "entry_role": "discoverability_helper_surface",
    },
    "demoted_support_or_non_entry_surface": {
        "order": 6,
        "contract_heading": "### 6. Demoted support or non-entry surface",
        "entry_role": "demoted_support_or_non_entry_surface",
    },
}
EXPECTED_DIFFERENTIATION_ROWS = {
    "frozen_vs_live_execution_entry": {
        "order": 1,
        "contract_phrase": "frozen law-defined entry is separated from live governed execution entry;",
    },
    "operator_vs_machine_execution_entry": {
        "order": 2,
        "contract_phrase": "natural-language collaboration entry is separated from machine execution entry;",
    },
    "execution_vs_recovery_entry": {
        "order": 3,
        "contract_phrase": "governed execution entry is separated from governed recovery-only entry;",
    },
    "helper_vs_canonical_execution_entry": {
        "order": 4,
        "contract_phrase": "discoverability-helper surface is separated from canonical execution entry;",
    },
    "support_vs_active_entry_surface": {
        "order": 5,
        "contract_phrase": "demoted support or non-entry surface is separated from any active entry surface;",
    },
    "visibility_vs_entry_admission": {
        "order": 6,
        "contract_phrase": "visible installation or discoverability is separated from lawful entry admission.",
    },
}
EXPECTED_ENTRY_ADMISSION_PROOF_ROWS = {
    "frozen_definition_entry_admission_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-definition entry-admission proof",
        "proof_role": "frozen_definition_entry_admission_proof",
    },
    "collaboration_boundary_entry_admission_proof": {
        "order": 2,
        "contract_heading": "### 2. Collaboration-boundary entry-admission proof",
        "proof_role": "collaboration_boundary_entry_admission_proof",
    },
    "governed_execution_entry_admission_proof": {
        "order": 3,
        "contract_heading": "### 3. Governed-execution entry-admission proof",
        "proof_role": "governed_execution_entry_admission_proof",
    },
    "recovery_confinement_entry_admission_proof": {
        "order": 4,
        "contract_heading": "### 4. Recovery-confinement entry-admission proof",
        "proof_role": "recovery_confinement_entry_admission_proof",
    },
    "helper_support_demotion_entry_admission_proof": {
        "order": 5,
        "contract_heading": "### 5. Helper/support-demotion entry-admission proof",
        "proof_role": "helper_support_demotion_entry_admission_proof",
    },
}
EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS = {
    "frozen_definition_not_collaboration_boundary": {
        "order": 1,
        "contract_phrase": "frozen-definition entry-admission proof is not proof of collaboration-boundary preservation;",
    },
    "collaboration_boundary_not_governed_execution": {
        "order": 2,
        "contract_phrase": "collaboration-boundary entry-admission proof is not proof of governed execution entry;",
    },
    "governed_execution_not_recovery_confinement": {
        "order": 3,
        "contract_phrase": "governed-execution entry-admission proof is not proof of recovery confinement;",
    },
    "recovery_confinement_not_helper_support_demotion": {
        "order": 4,
        "contract_phrase": "recovery-confinement entry-admission proof is not proof of helper or support demotion;",
    },
    "helper_support_demotion_not_lawful_active_execution_entry": {
        "order": 5,
        "contract_phrase": "helper/support-demotion entry-admission proof is not proof of lawful active execution entry.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "declared_entry_as_live_execution_entry": {
        "order": 1,
        "contract_phrase": "a law-defined or declared entry surface is treated as if it were already live governed execution entry.",
    },
    "operator_surface_as_machine_execution_entry": {
        "order": 2,
        "contract_phrase": "the operator collaboration surface is treated as if it were sufficient machine execution entry.",
    },
    "recovery_entry_as_primary_execution_entry": {
        "order": 3,
        "contract_phrase": "a recovery, replay, diagnostics, or repair entry surface is treated as if it were the canonical primary execution entry.",
    },
    "helper_surface_as_canonical_entry": {
        "order": 4,
        "contract_phrase": "a helper path, discoverability aid, or installation alias is treated as if it were canonical execution entry.",
    },
    "support_surface_as_active_entry": {
        "order": 5,
        "contract_phrase": "a demoted support or non-entry surface is treated as if it were active execution entry.",
    },
    "installation_visibility_as_entry_legality": {
        "order": 6,
        "contract_phrase": "visibility, installation presence, or easy discovery is treated as if it proved lawful entry admission.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for entry-surface legitimacy law",
    "## Entry-surface legitimacy law",
    "## Six entry classes",
    "## Required entry differentiations",
    "## Entry-admission proof discipline",
    "## Entry-admission proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`ENTRY_SURFACE_LEGITIMACY_CONTRACT.md`"


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
    legitimacy_violations: list[dict[str, Any]],
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
            legitimacy_violations.append(
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
                legitimacy_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root entry-surface legitimacy law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    entry_doc, entry_entry_path, entry_active_path, entry_alias_error = load_root_entry_surface_legitimacy(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    legitimacy_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if entry_alias_error:
        stale_reasons.append(f"root_entry_surface_legitimacy_alias_error:{entry_alias_error}")
        error_code = ERR_REGISTRY
    elif not entry_doc:
        stale_reasons.append("root_entry_surface_legitimacy_empty_or_invalid")
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

    entry_class_rows = entry_class_rows_from_doc(entry_doc) if entry_doc else ()
    differentiation_rows = differentiation_rows_from_doc(entry_doc) if entry_doc else ()
    entry_admission_proof_rows = entry_admission_proof_rows_from_doc(entry_doc) if entry_doc else ()
    entry_admission_limit_rows = entry_admission_limit_rows_from_doc(entry_doc) if entry_doc else ()
    collapse_rows = collapse_rows_from_doc(entry_doc) if entry_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "entry_family": "protocol_root_entry_surface_legitimacy",
            "entry_version": "v1",
            "contract_file": "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_entry_surface_legitimacy.py",
            "probe_script": "scripts/ci/run_protocol_root_entry_surface_legitimacy_probes_ci.sh",
            "common_script": "scripts/root_entry_surface_legitimacy_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(entry_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_entry_surface_legitimacy_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_entry_class_rows", entry_class_rows),
            ("required_differentiation_rows", differentiation_rows),
            ("required_entry_admission_proof_rows", entry_admission_proof_rows),
            ("required_entry_admission_limit_rows", entry_admission_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_entry_surface_legitimacy_{field}_missing")
                error_code = ERR_REGISTRY
        if not entry_doc.get("contract_required_markers"):
            stale_reasons.append("root_entry_surface_legitimacy_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(entry_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_entry_surface_legitimacy_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_entry_class_rows",
                member_id_key="entry_class_id",
                actual_rows=entry_class_rows,
                expected_rows=EXPECTED_ENTRY_CLASS_ROWS,
                id_attr="entry_class_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_differentiation_rows",
                member_id_key="differentiation_id",
                actual_rows=differentiation_rows,
                expected_rows=EXPECTED_DIFFERENTIATION_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_entry_admission_proof_rows",
                member_id_key="proof_id",
                actual_rows=entry_admission_proof_rows,
                expected_rows=EXPECTED_ENTRY_ADMISSION_PROOF_ROWS,
                id_attr="proof_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_entry_admission_limit_rows",
                member_id_key="limit_id",
                actual_rows=entry_admission_limit_rows,
                expected_rows=EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS,
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
            actual_rows=entry_class_rows,
            expected_rows=EXPECTED_ENTRY_CLASS_ROWS,
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
            field_name="required_entry_class_rows",
            id_attr="entry_class_id",
            compare_fields=("contract_heading", "entry_role"),
        )
        _validate_rows(
            actual_rows=differentiation_rows,
            expected_rows=EXPECTED_DIFFERENTIATION_ROWS,
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
            field_name="required_differentiation_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=entry_admission_proof_rows,
            expected_rows=EXPECTED_ENTRY_ADMISSION_PROOF_ROWS,
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
            field_name="required_entry_admission_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_rows(
            actual_rows=entry_admission_limit_rows,
            expected_rows=EXPECTED_ENTRY_ADMISSION_LIMIT_ROWS,
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
            field_name="required_entry_admission_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            legitimacy_violations=legitimacy_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(entry_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            legitimacy_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in entry_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in entry_class_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "entry_class_heading_missing", "marker": marker})
            for row in entry_admission_proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "proof_heading_missing", "marker": marker})
            for row in differentiation_rows + entry_admission_limit_rows + collapse_rows:
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
            for child in ("root-entry-surface-legitimacy.current.yaml", "root-entry-surface-legitimacy.v1.yaml"):
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
    if not error_code and (legitimacy_violations or integration_violations or contract_marker_violations):
        error_code = ERR_ENTRY_LEGITIMACY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"entry_surface_legitimacy_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in legitimacy_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    entry_surface_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    entry_surface_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ENTRY_LEGITIMACY),
        "entry_entry_path": str(entry_entry_path),
        "entry_active_path": str(entry_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(entry_doc.get("contract_file") or ""),
        "entry_class_count": len(entry_class_rows),
        "differentiation_count": len(differentiation_rows),
        "entry_admission_proof_count": len(entry_admission_proof_rows),
        "entry_admission_limit_count": len(entry_admission_limit_rows),
        "collapse_count": len(collapse_rows),
        "entry_surface_row_family_count": len(row_family_projection_rows),
        "entry_surface_row_coverage_status": entry_surface_row_coverage_status,
        "entry_surface_row_identity_projection_status": entry_surface_row_identity_projection_status,
        "row_family_projection_rows": row_family_projection_rows,
        "entry_class_ids": [row.entry_class_id for row in sorted(entry_class_rows, key=lambda item: item.order)],
        "differentiation_ids": [row.row_id for row in sorted(differentiation_rows, key=lambda item: item.order)],
        "entry_admission_proof_ids": [row.proof_id for row in sorted(entry_admission_proof_rows, key=lambda item: item.order)],
        "entry_admission_limit_ids": [row.row_id for row in sorted(entry_admission_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "legitimacy_violations": legitimacy_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
