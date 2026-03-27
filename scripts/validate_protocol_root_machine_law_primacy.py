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
from root_machine_law_primacy_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    collapse_rows_from_doc,
    commitment_rows_from_doc,
    load_root_machine_law_primacy,
    primacy_limit_rows_from_doc,
    primacy_proof_rows_from_doc,
)

STATUS_KEY = "protocol_root_machine_law_primacy_status"
ERR_REGISTRY = "IP-RMLP-001"
ERR_STRUCTURE = "IP-RMLP-002"
ERR_PRIMACY = "IP-RMLP-003"

EXPECTED_COMMITMENT_ROWS = {
    "law_before_compatibility_shelter": {
        "order": 1,
        "contract_heading": "### 1. Law before compatibility shelter",
        "commitment_role": "machine_law_first",
    },
    "governed_success_path_before_convenience": {
        "order": 2,
        "contract_heading": "### 2. Governed success path before convenience permissiveness",
        "commitment_role": "success_path_admissibility_first",
    },
    "fail_close_before_silent_swallowing": {
        "order": 3,
        "contract_heading": "### 3. Fail-close exposure before silent swallowing",
        "commitment_role": "fail_close_before_shelter",
    },
    "governed_convergence_before_downgrade": {
        "order": 4,
        "contract_heading": "### 4. Governed convergence before downgrade laundering",
        "commitment_role": "governed_convergence_over_downgrade",
    },
}
EXPECTED_ANCHOR_ROWS = {
    "machine_law_first": {
        "order": 1,
        "contract_phrase": "machine law first rather than a compatibility shelter or historical backstop;",
    },
    "governed_success_path": {
        "order": 2,
        "contract_phrase": "governed current-turn success path rather than convenience-path permissiveness;",
    },
    "fail_close_over_projection": {
        "order": 3,
        "contract_phrase": "fail-close exposure of missing or ambiguous truth rather than silent swallowing through compatibility projection;",
    },
    "governed_convergence_over_downgrade": {
        "order": 4,
        "contract_phrase": "governed convergence and refreezing rather than residue laundering or protocol downgrade.",
    },
}
EXPECTED_PRIMACY_PROOF_ROWS = {
    "frozen_law_primacy_proof": {
        "order": 1,
        "contract_heading": "### 1. Frozen-law primacy proof",
        "proof_role": "frozen_law_primacy_proof",
    },
    "success_path_demotion_boundary_primacy_proof": {
        "order": 2,
        "contract_heading": "### 2. Success-path demotion-boundary proof",
        "proof_role": "success_path_demotion_boundary_primacy_proof",
    },
    "fail_close_exposure_primacy_proof": {
        "order": 3,
        "contract_heading": "### 3. Fail-close exposure proof",
        "proof_role": "fail_close_exposure_primacy_proof",
    },
    "governed_convergence_primacy_proof": {
        "order": 4,
        "contract_heading": "### 4. Governed-convergence proof",
        "proof_role": "governed_convergence_primacy_proof",
    },
    "runtime_adjudication_non_bypass_primacy_proof": {
        "order": 5,
        "contract_heading": "### 5. Runtime-adjudication non-bypass proof",
        "proof_role": "runtime_adjudication_non_bypass_primacy_proof",
    },
}
EXPECTED_PRIMACY_LIMIT_ROWS = {
    "frozen_law_not_success_path_demotion_boundary": {
        "order": 1,
        "contract_phrase": "frozen-law primacy proof is not proof of success-path demotion boundary;",
    },
    "success_path_demotion_not_fail_close_exposure": {
        "order": 2,
        "contract_phrase": "success-path demotion-boundary proof is not proof of fail-close exposure;",
    },
    "fail_close_not_governed_convergence": {
        "order": 3,
        "contract_phrase": "fail-close exposure proof is not proof of governed convergence;",
    },
    "governed_convergence_not_runtime_non_bypass": {
        "order": 4,
        "contract_phrase": "governed-convergence proof is not proof of runtime-adjudication non-bypass;",
    },
    "runtime_non_bypass_not_success_path_reentry": {
        "order": 5,
        "contract_phrase": "runtime-adjudication non-bypass proof is not proof that compatibility or recovery surfaces may re-enter active success-path legality.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "compatibility_shelter_substitution": {
        "order": 1,
        "contract_phrase": "the active protocol is treated as a shelter for lagging residue instead of as the upgrade target.",
    },
    "silent_truth_reconstruction": {
        "order": 2,
        "contract_phrase": "missing or ambiguous current-turn truth is rebuilt through compatibility projection, alias bridges, or local familiarity.",
    },
    "demoted_surface_reentry": {
        "order": 3,
        "contract_phrase": "migration, import, fixture, diagnostic, or fallback surfaces re-enter active defaults as if demotion did not exist.",
    },
    "protocol_downgrade_for_residue": {
        "order": 4,
        "contract_phrase": "shared law is weakened or reopened merely to keep local residue alive.",
    },
    "convenience_claims_legality": {
        "order": 5,
        "contract_phrase": "convenience, vividness, or historical familiarity is treated as if it proved active-path legality.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for machine-law primacy",
    "## Machine-law primacy law",
    "## Four primacy commitments",
    "## Required primacy anchors",
    "## Machine-law primacy proof discipline",
    "## Machine-law primacy proof limits",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn machine-law primacy legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`MACHINE_LAW_PRIMACY_CONTRACT.md`"


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
    primacy_violations: list[dict[str, Any]],
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
            primacy_violations.append(
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
                primacy_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root machine-law primacy and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    primacy_doc, primacy_entry_path, primacy_active_path, primacy_alias_error = load_root_machine_law_primacy(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    primacy_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if primacy_alias_error:
        stale_reasons.append(f"root_machine_law_primacy_alias_error:{primacy_alias_error}")
        error_code = ERR_REGISTRY
    elif not primacy_doc:
        stale_reasons.append("root_machine_law_primacy_empty_or_invalid")
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

    commitment_rows = commitment_rows_from_doc(primacy_doc) if primacy_doc else ()
    anchor_rows = anchor_rows_from_doc(primacy_doc) if primacy_doc else ()
    primacy_proof_rows = primacy_proof_rows_from_doc(primacy_doc) if primacy_doc else ()
    primacy_limit_rows = primacy_limit_rows_from_doc(primacy_doc) if primacy_doc else ()
    collapse_rows = collapse_rows_from_doc(primacy_doc) if primacy_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "machine_law_family": "protocol_root_machine_law_primacy",
            "machine_law_version": "v1",
            "contract_file": "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_machine_law_primacy.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_law_primacy_probes_ci.sh",
            "common_script": "scripts/root_machine_law_primacy_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(primacy_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_law_primacy_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_commitment_rows", commitment_rows),
            ("required_anchor_rows", anchor_rows),
            ("required_primacy_proof_rows", primacy_proof_rows),
            ("required_primacy_limit_rows", primacy_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_machine_law_primacy_{field}_missing")
                error_code = ERR_REGISTRY
        if not primacy_doc.get("contract_required_markers"):
            stale_reasons.append("root_machine_law_primacy_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(primacy_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_machine_law_primacy_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        row_family_projection_rows = [
            project_row_family(
                family_id="required_commitment_rows",
                member_id_key="commitment_id",
                actual_rows=commitment_rows,
                expected_rows=EXPECTED_COMMITMENT_ROWS,
                id_attr="commitment_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_anchor_rows",
                member_id_key="anchor_id",
                actual_rows=anchor_rows,
                expected_rows=EXPECTED_ANCHOR_ROWS,
                id_attr="row_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_primacy_proof_rows",
                member_id_key="proof_id",
                actual_rows=primacy_proof_rows,
                expected_rows=EXPECTED_PRIMACY_PROOF_ROWS,
                id_attr="proof_id",
                pass_status=STATUS_PASS_REQUIRED,
                fail_status=STATUS_FAIL_REQUIRED,
            ),
            project_row_family(
                family_id="required_primacy_limit_rows",
                member_id_key="limit_id",
                actual_rows=primacy_limit_rows,
                expected_rows=EXPECTED_PRIMACY_LIMIT_ROWS,
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
            actual_rows=commitment_rows,
            expected_rows=EXPECTED_COMMITMENT_ROWS,
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
            field_name="required_commitment_rows",
            id_attr="commitment_id",
            compare_fields=("contract_heading", "commitment_role"),
        )
        _validate_rows(
            actual_rows=anchor_rows,
            expected_rows=EXPECTED_ANCHOR_ROWS,
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
            field_name="required_anchor_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=primacy_proof_rows,
            expected_rows=EXPECTED_PRIMACY_PROOF_ROWS,
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
            field_name="required_primacy_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_rows(
            actual_rows=primacy_limit_rows,
            expected_rows=EXPECTED_PRIMACY_LIMIT_ROWS,
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
            field_name="required_primacy_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            primacy_violations=primacy_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(primacy_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            primacy_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in primacy_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in commitment_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "commitment_heading_missing", "marker": marker})
            for row in primacy_proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading, row.proof_role)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "contract_phrase_missing", "marker": marker})
            for row in anchor_rows + primacy_limit_rows + collapse_rows:
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
            for child in ("root-machine-law-primacy.current.yaml", "root-machine-law-primacy.v1.yaml"):
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
    if not error_code and (primacy_violations or integration_violations or contract_marker_violations):
        error_code = ERR_PRIMACY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"machine_law_primacy_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in primacy_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    machine_law_primacy_row_coverage_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="coverage_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    machine_law_primacy_row_identity_projection_status = aggregate_row_family_status(
        row_family_projection_rows,
        status_key="identity_projection_status",
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_PRIMACY),
        "primacy_entry_path": str(primacy_entry_path),
        "primacy_active_path": str(primacy_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(primacy_doc.get("contract_file") or ""),
        "commitment_count": len(commitment_rows),
        "anchor_count": len(anchor_rows),
        "primacy_proof_count": len(primacy_proof_rows),
        "primacy_limit_count": len(primacy_limit_rows),
        "collapse_count": len(collapse_rows),
        "machine_law_primacy_row_family_count": len(row_family_projection_rows),
        "machine_law_primacy_row_coverage_status": machine_law_primacy_row_coverage_status,
        "machine_law_primacy_row_identity_projection_status": machine_law_primacy_row_identity_projection_status,
        "row_family_projection_rows": row_family_projection_rows,
        "commitment_ids": [row.commitment_id for row in sorted(commitment_rows, key=lambda item: item.order)],
        "anchor_ids": [row.row_id for row in sorted(anchor_rows, key=lambda item: item.order)],
        "primacy_proof_ids": [row.proof_id for row in sorted(primacy_proof_rows, key=lambda item: item.order)],
        "primacy_limit_ids": [row.row_id for row in sorted(primacy_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "primacy_violations": primacy_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
