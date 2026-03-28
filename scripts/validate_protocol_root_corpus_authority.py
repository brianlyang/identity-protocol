#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_root_doc_anchor_registry_structure_violations,
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families
from root_corpus_authority_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    authority_anchor_checks_from_doc,
    authority_class_profiles_from_doc,
    entry_authority_projections_from_doc,
    load_root_corpus_authority,
)
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc

STATUS_KEY = "protocol_root_corpus_authority_status"
ERR_REGISTRY = "IP-RCA-001"
ERR_STRUCTURE = "IP-RCA-002"
ERR_AUTHORITY = "IP-RCA-003"

EXPECTED_CLASS_RULES = {
    "bottom_theory": {
        "authority_role": "interpretive_bottom_theory",
        "authority_mode": "interpretive_only",
        "philosophical_primacy": True,
        "law_bearing_required": True,
    },
    "root_index": {
        "authority_role": "navigational_root_index",
        "authority_mode": "navigational_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "constitution": {
        "authority_role": "constitutional_protocol_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "runtime_constitution": {
        "authority_role": "constitutional_runtime_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "root_contract": {
        "authority_role": "root_domain_contract_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "machine_registry_directory": {
        "authority_role": "machine_consumed_registry_family",
        "authority_mode": "machine_consumed_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "governed_subdomain_extension": {
        "authority_role": "governed_subdomain_extension_family",
        "authority_mode": "extension_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "demoted_support_directory": {
        "authority_role": "demoted_support_material",
        "authority_mode": "demoted_support_only",
        "philosophical_primacy": False,
        "law_bearing_required": False,
    },
}
ALLOWED_AUTHORITY_MODES = {
    "interpretive_only",
    "navigational_only",
    "frozen_law_only",
    "machine_consumed_family",
    "extension_family",
    "demoted_support_only",
}
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Authority layering",
        "machine-consumed enforcement authority",
        "Philosophical primacy, however, is not the same as runtime-source primacy.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "philosophical primacy does not mean runtime-source primacy",
        "machine-consumed authority still lives in frozen contracts, mappings, validators, runtime state, and receipts",
    ),
    "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-law primacy legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn epistemic legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn decision-evidence legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn success-path state legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ERROR_TERMINALITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn error terminality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn artifact-family admissibility must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_DISCOVERY.md": (
        "## Runtime adjudication boundary",
        "Current-turn discovery legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn self-judgement legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/AGENT_HANDOFF_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn responsibility legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn truth lifecycle legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus authority layering and authority-role topology.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    authority_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    class_profiles = authority_class_profiles_from_doc(authority_doc) if authority_doc else ()
    entry_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()

    if not stale_reasons:
        if str(authority_doc.get("authority_family") or "").strip() != "protocol_root_corpus_authority":
            stale_reasons.append("root_corpus_authority_family_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("authority_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_authority_version_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_authority_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_authority_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_authority_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_authority.py":
            stale_reasons.append("root_corpus_authority_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh":
            stale_reasons.append("root_corpus_authority_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("common_script") or "").strip() != "scripts/root_corpus_authority_common.py":
            stale_reasons.append("root_corpus_authority_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(authority_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_authority_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_authority_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_authority_class_profiles_missing")
            error_code = ERR_REGISTRY
        if not entry_projections:
            stale_reasons.append("root_corpus_authority_entry_projection_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_authority",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_class_law_bearing = {entry.corpus_class: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    class_profile_map = {row.corpus_class: row for row in class_profiles}
    entry_projection_map = {row.rel_path: row for row in entry_projections}
    ordering_reading_paths = [row.rel_path for row in sorted(reading_rows, key=lambda item: item.order)]
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip() if ordering_doc else ""

    if not stale_reasons:
        append_root_doc_anchor_registry_structure_violations(
            structure_violations,
            anchor_checks,
            field_name="authority_anchor_checks",
            registry_paths=registry_paths,
            registry_entry_kind_map=registry_entry_kind_map,
            registry_entry_law_bearing_map=registry_entry_law_bearing_map,
            require_file_entry=True,
            require_law_bearing=True,
        )

        append_membership_delta_violations(
            structure_violations,
            field_name="authority_class_profiles",
            expected_ids=registry_classes,
            actual_ids=class_profile_map,
            payload_key="corpus_classes",
            missing_reason="missing_registry_classes",
            extra_reason="extra_unregistered_classes",
            duplicate_reason="duplicate_corpus_class",
            actual_total_count=len(class_profiles),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="entry_authority_projection",
            expected_ids=registry_paths,
            actual_ids=entry_projection_map,
            payload_key="rel_paths",
            missing_reason="missing_registered_entries",
            extra_reason="extra_unregistered_entries",
            duplicate_reason="duplicate_rel_path",
            actual_total_count=len(entry_projections),
        )
        for row in class_profiles:
            if row.authority_mode not in ALLOWED_AUTHORITY_MODES:
                structure_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "invalid_authority_mode",
                        "corpus_class": row.corpus_class,
                        "authority_mode": row.authority_mode,
                    }
                )
            expected = EXPECTED_CLASS_RULES.get(row.corpus_class)
            if expected is None:
                continue
            if row.authority_role != expected["authority_role"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_role_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_role"],
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != expected["authority_mode"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_mode_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_mode"],
                        "actual": row.authority_mode,
                    }
                )
            if bool(row.philosophical_primacy) != bool(expected["philosophical_primacy"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "philosophical_primacy_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["philosophical_primacy"]),
                        "actual": bool(row.philosophical_primacy),
                    }
                )
            if bool(row.law_bearing_required) != bool(expected["law_bearing_required"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["law_bearing_required"]),
                        "actual": bool(row.law_bearing_required),
                    }
                )
            registry_law_bearing = registry_class_law_bearing.get(row.corpus_class)
            if registry_law_bearing is not None and bool(row.law_bearing_required) != bool(registry_law_bearing):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "registry_law_bearing_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(registry_law_bearing),
                        "actual": bool(row.law_bearing_required),
                    }
                )

        primacy_classes = sorted(row.corpus_class for row in class_profiles if row.philosophical_primacy)
        if primacy_classes != ["bottom_theory"]:
            authority_violations.append(
                {
                    "field": "authority_class_profiles",
                    "reason": "philosophical_primacy_not_exclusive_to_bottom_theory",
                    "corpus_classes": primacy_classes,
                }
            )

        for row in entry_projections:
            expected_class = registry_entry_class_map.get(row.rel_path)
            if expected_class and row.corpus_class != expected_class:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_corpus_class_mismatch",
                        "rel_path": row.rel_path,
                        "expected": expected_class,
                        "actual": row.corpus_class,
                    }
                )
            class_profile = class_profile_map.get(row.corpus_class)
            if class_profile is None:
                continue
            if row.authority_role != class_profile.authority_role:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_role_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_role,
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != class_profile.authority_mode:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_mode_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_mode,
                        "actual": row.authority_mode,
                    }
                )

        if root_index_entry:
            root_index_projection = entry_projection_map.get(root_index_entry)
            if root_index_projection is None:
                authority_violations.append(
                    {"field": "entry_authority_projection", "reason": "root_index_entry_missing_projection", "rel_path": root_index_entry}
                )
            else:
                if root_index_projection.corpus_class != "root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_class",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.corpus_class,
                        }
                    )
                if root_index_projection.authority_role != "navigational_root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_role",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_role,
                        }
                    )
                if root_index_projection.authority_mode != "navigational_only":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_mode",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_mode,
                        }
                    )

        if ordering_reading_paths and ordering_reading_paths != registry_paths:
            # Registry paths are alphabetical, ordering paths are semantic. No violation here.
            pass

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name="authority_anchor_checks",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (authority_violations or anchor_violations):
        error_code = ERR_AUTHORITY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"authority_violation:{row['field']}:{row['reason']}" for row in authority_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "authority_class_profiles",
                "member_id_key": "corpus_class",
                "actual_rows": class_profiles,
                "expected_rows": {corpus_class: {} for corpus_class in registry_classes},
                "id_attr": "corpus_class",
            },
            {
                "family_id": "entry_authority_projection",
                "member_id_key": "rel_path",
                "actual_rows": entry_projections,
                "expected_rows": {rel_path: {} for rel_path in registry_paths},
                "id_attr": "rel_path",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_AUTHORITY),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "root_dir": str(authority_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "authority_anchor_check_count": len(anchor_checks),
        "authority_class_profile_count": len(class_profiles),
        "entry_authority_projection_count": len(entry_projections),
        **project_root_contract_support_projection(
            prefix="authority",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "authority_class_profiles": [
            {
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
                "philosophical_primacy": row.philosophical_primacy,
                "law_bearing_required": row.law_bearing_required,
            }
            for row in class_profiles
        ],
        "entry_authority_projection": [
            {
                "rel_path": row.rel_path,
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
            }
            for row in entry_projections
        ],
        "structure_violations": structure_violations,
        "authority_violations": authority_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
