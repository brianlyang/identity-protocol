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
from root_identity_instance_self_judgement_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_rows_from_doc,
    collapse_rows_from_doc,
    load_root_identity_instance_self_judgement,
    question_rows_from_doc,
    self_judgement_limit_rows_from_doc,
    self_judgement_proof_rows_from_doc,
)

STATUS_KEY = "protocol_root_identity_instance_self_judgement_status"
ERR_REGISTRY = "IP-RIISJ-001"
ERR_STRUCTURE = "IP-RIISJ-002"
ERR_JUDGEMENT = "IP-RIISJ-003"

EXPECTED_QUESTION_ROWS = {
    "who_i_am": {
        "order": 1,
        "contract_heading": "### 1. Who I am",
        "judgement_role": "machine_verifiable_identity",
    },
    "what_i_can_do": {
        "order": 2,
        "contract_heading": "### 2. What I can do",
        "judgement_role": "lawful_capability_boundary",
    },
    "how_i_do_it": {
        "order": 3,
        "contract_heading": "### 3. How I do it",
        "judgement_role": "canonical_execution_under_law",
    },
    "when_not_my_place": {
        "order": 4,
        "contract_heading": "### 4. When it is not my place to decide by myself",
        "judgement_role": "escalation_boundary_awareness",
    },
}
EXPECTED_ANCHOR_ROWS = {
    "resolved_identity_context": {
        "order": 1,
        "contract_phrase": "resolved identity context rather than narrative self-claim;",
    },
    "governed_routes_states_receipts_artifacts": {
        "order": 2,
        "contract_phrase": "governed routes, states, receipts, and artifact families rather than abstract capability inflation;",
    },
    "canonical_execution_paths": {
        "order": 3,
        "contract_phrase": "canonical execution paths rather than local convenience paths;",
    },
    "governed_escalation_criteria": {
        "order": 4,
        "contract_phrase": "governed escalation criteria rather than instance preference.",
    },
}
EXPECTED_SELF_JUDGEMENT_PROOF_ROWS = {
    "identity_resolution_self_judgement_proof": {
        "order": 1,
        "contract_heading": "### 1. Identity-resolution self-judgement proof",
        "proof_role": "identity_resolution_self_judgement_proof",
    },
    "capability_boundary_self_judgement_proof": {
        "order": 2,
        "contract_heading": "### 2. Capability-boundary self-judgement proof",
        "proof_role": "capability_boundary_self_judgement_proof",
    },
    "canonical_execution_self_judgement_proof": {
        "order": 3,
        "contract_heading": "### 3. Canonical-execution self-judgement proof",
        "proof_role": "canonical_execution_self_judgement_proof",
    },
    "escalation_boundary_self_judgement_proof": {
        "order": 4,
        "contract_heading": "### 4. Escalation-boundary self-judgement proof",
        "proof_role": "escalation_boundary_self_judgement_proof",
    },
    "non_self_authorization_self_judgement_proof": {
        "order": 5,
        "contract_heading": "### 5. Non-self-authorization proof",
        "proof_role": "non_self_authorization_self_judgement_proof",
    },
}
EXPECTED_SELF_JUDGEMENT_LIMIT_ROWS = {
    "identity_resolution_not_capability_boundary": {
        "order": 1,
        "contract_phrase": "identity-resolution self-judgement proof is not proof of capability boundary;",
    },
    "capability_boundary_not_canonical_execution": {
        "order": 2,
        "contract_phrase": "capability-boundary self-judgement proof is not proof of canonical execution;",
    },
    "canonical_execution_not_escalation_boundary": {
        "order": 3,
        "contract_phrase": "canonical-execution self-judgement proof is not proof of escalation boundary awareness;",
    },
    "escalation_boundary_not_non_self_authorization": {
        "order": 4,
        "contract_phrase": "escalation-boundary self-judgement proof is not proof of non-self-authorization;",
    },
    "non_self_authorization_not_runtime_bypass": {
        "order": 5,
        "contract_phrase": "non-self-authorization proof is not proof that the instance may bypass current-turn machine adjudication.",
    },
}
EXPECTED_COLLAPSE_ROWS = {
    "narrative_identity_substitution": {
        "order": 1,
        "contract_phrase": "narrative self-description is treated as if it were machine-verifiable identity truth.",
    },
    "capability_inflation_without_law": {
        "order": 2,
        "contract_phrase": "abstract model power is treated as if it were lawful identity capability.",
    },
    "local_path_improvisation_as_law": {
        "order": 3,
        "contract_phrase": "convenient local execution paths are treated as equivalent to canonical governed execution.",
    },
    "self_authorized_boundary_crossing": {
        "order": 4,
        "contract_phrase": "the instance decides it may cross a boundary merely because it believes it can.",
    },
    "escalation_avoidance_by_self_confidence": {
        "order": 5,
        "contract_phrase": "an issue requiring escalation is kept local purely because the instance feels confident.",
    },
}
EXPECTED_REGISTRY_MARKERS = (
    "this file remains the authoritative root-domain contract for identity-instance self-judgement law",
    "## Four self-judgement questions",
    "## Required self-judgement anchors",
    "## Self-judgement proof discipline",
    "## Self-judgement proof limits",
    "## Non-compliant self-judgement collapses",
)
EXPECTED_AUTHORITY_MARKERS = (
    "## Runtime adjudication boundary",
    "Current-turn self-judgement legality must still resolve from machine-consumed enforcement surfaces",
)
EXPECTED_ROUTING_MARKERS = EXPECTED_AUTHORITY_MARKERS
EXPECTED_README_MARKER = "`IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md`"


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
    judgement_violations: list[dict[str, Any]],
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
            judgement_violations.append(
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
                judgement_violations.append(
                    {
                        "field": field_name,
                        "row_id": row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate root identity-instance self-judgement law and root-corpus integration.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    self_doc, self_entry_path, self_active_path, self_alias_error = load_root_identity_instance_self_judgement(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    judgement_violations: list[dict[str, Any]] = []
    integration_violations: list[dict[str, Any]] = []
    contract_marker_violations: list[dict[str, Any]] = []
    error_code = ""

    if self_alias_error:
        stale_reasons.append(f"root_identity_instance_self_judgement_alias_error:{self_alias_error}")
        error_code = ERR_REGISTRY
    elif not self_doc:
        stale_reasons.append("root_identity_instance_self_judgement_empty_or_invalid")
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

    question_rows = question_rows_from_doc(self_doc) if self_doc else ()
    anchor_rows = anchor_rows_from_doc(self_doc) if self_doc else ()
    self_judgement_proof_rows = self_judgement_proof_rows_from_doc(self_doc) if self_doc else ()
    self_judgement_limit_rows = self_judgement_limit_rows_from_doc(self_doc) if self_doc else ()
    collapse_rows = collapse_rows_from_doc(self_doc) if self_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_anchors = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    authority_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    routing_anchors = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    routing_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "self_judgement_family": "protocol_root_identity_instance_self_judgement",
            "self_judgement_version": "v1",
            "contract_file": "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md",
            "philosophy_anchor_file": "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "validator_script": "scripts/validate_protocol_root_identity_instance_self_judgement.py",
            "probe_script": "scripts/ci/run_protocol_root_identity_instance_self_judgement_probes_ci.sh",
            "common_script": "scripts/root_identity_instance_self_judgement_common.py",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "ordering_current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
            "authority_current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
            "question_routing_current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(self_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_identity_instance_self_judgement_field_invalid:{field}")
                error_code = ERR_REGISTRY

        for field, rows in (
            ("required_question_rows", question_rows),
            ("required_anchor_rows", anchor_rows),
            ("required_self_judgement_proof_rows", self_judgement_proof_rows),
            ("required_self_judgement_limit_rows", self_judgement_limit_rows),
            ("required_collapse_rows", collapse_rows),
        ):
            if not rows:
                stale_reasons.append(f"root_identity_instance_self_judgement_{field}_missing")
                error_code = ERR_REGISTRY
        if not self_doc.get("contract_required_markers"):
            stale_reasons.append("root_identity_instance_self_judgement_contract_required_markers_missing")
            error_code = ERR_REGISTRY

        for field in ("contract_file", "philosophy_anchor_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(self_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_identity_instance_self_judgement_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    if not stale_reasons:
        _validate_rows(
            actual_rows=question_rows,
            expected_rows=EXPECTED_QUESTION_ROWS,
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
            field_name="required_question_rows",
            id_attr="question_id",
            compare_fields=("contract_heading", "judgement_role"),
        )
        _validate_rows(
            actual_rows=anchor_rows,
            expected_rows=EXPECTED_ANCHOR_ROWS,
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
            field_name="required_anchor_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=self_judgement_proof_rows,
            expected_rows=EXPECTED_SELF_JUDGEMENT_PROOF_ROWS,
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
            field_name="required_self_judgement_proof_rows",
            id_attr="proof_id",
            compare_fields=("contract_heading", "proof_role"),
        )
        _validate_rows(
            actual_rows=self_judgement_limit_rows,
            expected_rows=EXPECTED_SELF_JUDGEMENT_LIMIT_ROWS,
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
            field_name="required_self_judgement_limit_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )
        _validate_rows(
            actual_rows=collapse_rows,
            expected_rows=EXPECTED_COLLAPSE_ROWS,
            structure_violations=structure_violations,
            judgement_violations=judgement_violations,
            field_name="required_collapse_rows",
            id_attr="row_id",
            compare_fields=("contract_phrase",),
        )

        contract_file = str(self_doc.get("contract_file") or "").strip()
        contract_path = (repo_root / contract_file).resolve()
        if not contract_path.exists() or not contract_path.is_file():
            judgement_violations.append({"field": "contract_file", "reason": "contract_file_missing", "rel_path": contract_file})
        else:
            contract_text = contract_path.read_text(encoding="utf-8", errors="ignore")
            required_markers = tuple(
                str(item or "").strip() for item in self_doc.get("contract_required_markers") if str(item or "").strip()
            )
            for marker in find_missing_markers(contract_text, required_markers):
                contract_marker_violations.append({"field": "contract_file", "reason": "required_marker_missing", "marker": marker})
            for row in question_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading,)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "question_heading_missing", "marker": marker})
            for row in self_judgement_proof_rows:
                for marker in find_missing_markers(contract_text, (row.contract_heading, row.proof_role)):
                    contract_marker_violations.append({"field": "contract_file", "reason": "contract_phrase_missing", "marker": marker})
            for row in anchor_rows + self_judgement_limit_rows + collapse_rows:
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
            for child in ("root-identity-instance-self-judgement.current.yaml", "root-identity-instance-self-judgement.v1.yaml"):
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
    if not error_code and (judgement_violations or integration_violations or contract_marker_violations):
        error_code = ERR_JUDGEMENT

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(
        f"self_judgement_violation:{row.get('field', 'contract_file')}:{row['reason']}"
        for row in judgement_violations + integration_violations + contract_marker_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_JUDGEMENT),
        "self_entry_path": str(self_entry_path),
        "self_active_path": str(self_active_path),
        "registry_entry_path": str(registry_entry_path),
        "ordering_entry_path": str(ordering_entry_path),
        "authority_entry_path": str(authority_entry_path),
        "routing_entry_path": str(routing_entry_path),
        "contract_file": str(self_doc.get("contract_file") or ""),
        "question_count": len(question_rows),
        "anchor_count": len(anchor_rows),
        "self_judgement_proof_count": len(self_judgement_proof_rows),
        "self_judgement_limit_count": len(self_judgement_limit_rows),
        "collapse_count": len(collapse_rows),
        "question_ids": [row.question_id for row in sorted(question_rows, key=lambda item: item.order)],
        "anchor_ids": [row.row_id for row in sorted(anchor_rows, key=lambda item: item.order)],
        "self_judgement_proof_ids": [row.proof_id for row in sorted(self_judgement_proof_rows, key=lambda item: item.order)],
        "self_judgement_limit_ids": [row.row_id for row in sorted(self_judgement_limit_rows, key=lambda item: item.order)],
        "collapse_ids": [row.row_id for row in sorted(collapse_rows, key=lambda item: item.order)],
        "structure_violations": structure_violations,
        "judgement_violations": judgement_violations,
        "integration_violations": integration_violations,
        "contract_marker_violations": contract_marker_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
