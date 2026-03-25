#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_authority_common import entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_gateway_admissibility_common import gateway_effect_targets_from_doc, load_root_corpus_gateway_admissibility
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    adjudication_redirect_from_doc,
    entry_question_projections_from_doc,
    gateway_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_class_profiles_from_doc,
    question_routing_anchor_checks_from_doc,
)

STATUS_KEY = "protocol_root_corpus_question_routing_status"
ERR_REGISTRY = "IP-RCQR-001"
ERR_STRUCTURE = "IP-RCQR-002"
ERR_ROUTING = "IP-RCQR-003"

EXPECTED_QUESTION_RULES = {
    "generative_why": {
        "answer_mode": "interpretive_answer_only",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "interpretive_only",
        "corpus_class": "bottom_theory",
    },
    "root_entry_navigation": {
        "answer_mode": "navigational_answer_only",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "navigational_only",
        "corpus_class": "root_index",
    },
    "frozen_protocol_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "constitution",
    },
    "frozen_runtime_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "runtime_constitution",
    },
    "frozen_domain_contract_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "root_contract",
    },
    "registry_resolution": {
        "answer_mode": "machine_registry_answer",
        "current_turn_authority_allowed": True,
        "root_entry_required": True,
        "authority_mode": "machine_consumed_family",
        "corpus_class": "machine_registry_directory",
    },
    "governed_extension_law": {
        "answer_mode": "extension_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "extension_family",
        "corpus_class": "governed_subdomain_extension",
    },
    "support_material_lookup": {
        "answer_mode": "support_material_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "demoted_support_only",
        "corpus_class": "demoted_support_directory",
    },
    "current_turn_legality": {
        "answer_mode": "redirect_to_machine_enforcement",
        "current_turn_authority_allowed": True,
        "root_entry_required": False,
        "authority_mode": "",
        "corpus_class": "",
    },
}
ALLOWED_ANSWER_MODES = {
    "interpretive_answer_only",
    "navigational_answer_only",
    "frozen_law_answer",
    "machine_registry_answer",
    "extension_answer",
    "support_material_answer",
    "redirect_to_machine_enforcement",
}
EXPECTED_TERMINAL_MACHINE_SURFACES = (
    "mappings",
    "validators",
    "probes",
    "runtime_state",
    "receipts",
)
EXPECTED_FORBIDDEN_ROOT_CLASSES = (
    "bottom_theory",
    "root_index",
    "constitution",
    "runtime_constitution",
    "root_contract",
    "governed_subdomain_extension",
    "demoted_support_directory",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus question-routing and answer-surface discipline.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    gateway_doc, gateway_entry_path, gateway_active_path, gateway_alias_error = load_root_corpus_gateway_admissibility(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    routing_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    error_code = ""

    if routing_alias_error:
        stale_reasons.append(f"root_corpus_question_routing_alias_error:{routing_alias_error}")
        error_code = ERR_REGISTRY
    elif not routing_doc:
        stale_reasons.append("root_corpus_question_routing_empty_or_invalid")
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

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
        error_code = ERR_REGISTRY
    if gateway_alias_error:
        stale_reasons.append(f"root_corpus_gateway_admissibility_alias_error:{gateway_alias_error}")
        error_code = ERR_REGISTRY
    elif not gateway_doc:
        stale_reasons.append("root_corpus_gateway_admissibility_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    question_profiles = question_class_profiles_from_doc(routing_doc) if routing_doc else ()
    entry_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    gateway_question_projections = gateway_question_projections_from_doc(routing_doc) if routing_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(routing_doc) if routing_doc else adjudication_redirect_from_doc({})
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_entry_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    gateway_effect_targets = gateway_effect_targets_from_doc(gateway_doc) if gateway_doc else ()

    if not stale_reasons:
        if str(routing_doc.get("routing_family") or "").strip() != "protocol_root_corpus_question_routing":
            stale_reasons.append("root_corpus_question_routing_family_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("routing_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_question_routing_version_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_question_routing_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_question_routing_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_question_routing_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("authority_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-authority.current.yaml":
            stale_reasons.append("root_corpus_question_routing_authority_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("gateway_admissibility_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml":
            stale_reasons.append("root_corpus_question_routing_gateway_admissibility_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_question_routing.py":
            stale_reasons.append("root_corpus_question_routing_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh":
            stale_reasons.append("root_corpus_question_routing_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("common_script") or "").strip() != "scripts/root_corpus_question_routing_common.py":
            stale_reasons.append("root_corpus_question_routing_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(routing_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_question_routing_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_question_routing_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not question_profiles:
            stale_reasons.append("root_corpus_question_routing_profiles_missing")
            error_code = ERR_REGISTRY
        if not entry_projections:
            stale_reasons.append("root_corpus_question_routing_entry_projection_missing")
            error_code = ERR_REGISTRY
        if not gateway_question_projections:
            stale_reasons.append("root_corpus_question_routing_gateway_question_projection_missing")
            error_code = ERR_REGISTRY
        if not adjudication_redirect.question_class:
            stale_reasons.append("root_corpus_question_routing_adjudication_redirect_missing")
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    question_profile_map = {row.question_class: row for row in question_profiles}
    entry_projection_map = {row.rel_path: row for row in entry_projections}
    gateway_question_projection_map = {row.gateway_class: row for row in gateway_question_projections}
    gateway_effect_target_map = {row.gateway_class: row for row in gateway_effect_targets}
    authority_entry_map = {row.rel_path: row for row in authority_entry_projections}
    anchor_rel_paths = [row.rel_path for row in anchor_checks]
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip() if ordering_doc else ""
    reading_paths = [row.rel_path for row in sorted(reading_rows, key=lambda item: item.order)]

    if not stale_reasons:
        if len(question_profile_map) != len(question_profiles):
            structure_violations.append({"field": "question_class_profiles", "reason": "duplicate_question_class"})
        if len(entry_projection_map) != len(entry_projections):
            structure_violations.append({"field": "entry_question_projection", "reason": "duplicate_rel_path"})
        if len(gateway_question_projection_map) != len(gateway_question_projections):
            structure_violations.append({"field": "gateway_question_projection", "reason": "duplicate_gateway_class"})
        if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
            structure_violations.append({"field": "question_routing_anchor_checks", "reason": "duplicate_rel_path"})

        missing_question_profiles = sorted(set(EXPECTED_QUESTION_RULES) - set(question_profile_map))
        extra_question_profiles = sorted(set(question_profile_map) - set(EXPECTED_QUESTION_RULES))
        if missing_question_profiles:
            structure_violations.append(
                {"field": "question_class_profiles", "reason": "missing_expected_question_classes", "question_classes": missing_question_profiles}
            )
        if extra_question_profiles:
            structure_violations.append(
                {"field": "question_class_profiles", "reason": "extra_question_classes", "question_classes": extra_question_profiles}
            )

        missing_entry_projections = sorted(set(registry_paths) - set(entry_projection_map))
        extra_entry_projections = sorted(set(entry_projection_map) - set(registry_paths))
        if missing_entry_projections:
            structure_violations.append(
                {"field": "entry_question_projection", "reason": "missing_registered_entries", "rel_paths": missing_entry_projections}
            )
        if extra_entry_projections:
            structure_violations.append(
                {"field": "entry_question_projection", "reason": "extra_unregistered_entries", "rel_paths": extra_entry_projections}
            )
        missing_gateway_question_projections = sorted(set(gateway_effect_target_map) - set(gateway_question_projection_map))
        extra_gateway_question_projections = sorted(set(gateway_question_projection_map) - set(gateway_effect_target_map))
        if missing_gateway_question_projections:
            structure_violations.append(
                {
                    "field": "gateway_question_projection",
                    "reason": "missing_gateway_classes",
                    "gateway_classes": missing_gateway_question_projections,
                }
            )
        if extra_gateway_question_projections:
            structure_violations.append(
                {
                    "field": "gateway_question_projection",
                    "reason": "extra_gateway_classes",
                    "gateway_classes": extra_gateway_question_projections,
                }
            )

        missing_anchor_entries = sorted(set(anchor_rel_paths) - set(registry_paths))
        if missing_anchor_entries:
            structure_violations.append(
                {"field": "question_routing_anchor_checks", "reason": "unregistered_anchor_entries", "rel_paths": missing_anchor_entries}
            )
        for rel_path in anchor_rel_paths:
            entry_kind = registry_entry_kind_map.get(rel_path)
            if entry_kind is None:
                continue
            if entry_kind != "file":
                structure_violations.append(
                    {
                        "field": "question_routing_anchor_checks",
                        "reason": "anchor_must_target_file_entry",
                        "rel_path": rel_path,
                        "entry_kind": entry_kind,
                    }
                )
            if not bool(registry_entry_law_bearing_map.get(rel_path, False)):
                structure_violations.append(
                    {
                        "field": "question_routing_anchor_checks",
                        "reason": "anchor_must_target_law_bearing_entry",
                        "rel_path": rel_path,
                    }
                )

        for row in question_profiles:
            if row.answer_mode not in ALLOWED_ANSWER_MODES:
                structure_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "invalid_answer_mode",
                        "question_class": row.question_class,
                        "answer_mode": row.answer_mode,
                    }
                )
            expected = EXPECTED_QUESTION_RULES.get(row.question_class)
            if expected is None:
                continue
            if row.answer_mode != expected["answer_mode"]:
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "answer_mode_mismatch",
                        "question_class": row.question_class,
                        "expected": expected["answer_mode"],
                        "actual": row.answer_mode,
                    }
                )
            if bool(row.current_turn_authority_allowed) != bool(expected["current_turn_authority_allowed"]):
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "current_turn_authority_allowed_mismatch",
                        "question_class": row.question_class,
                        "expected": bool(expected["current_turn_authority_allowed"]),
                        "actual": bool(row.current_turn_authority_allowed),
                    }
                )
            if bool(row.root_entry_required) != bool(expected["root_entry_required"]):
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "root_entry_required_mismatch",
                        "question_class": row.question_class,
                        "expected": bool(expected["root_entry_required"]),
                        "actual": bool(row.root_entry_required),
                    }
                )

        for rel_path, row in entry_projection_map.items():
            expected_corpus_class = registry_entry_class_map.get(rel_path, "")
            expected_question_classes = sorted(
                question_class
                for question_class, expected in EXPECTED_QUESTION_RULES.items()
                if expected.get("corpus_class") == expected_corpus_class and expected.get("root_entry_required")
            )
            actual_question_classes = sorted(set(row.question_classes))
            if actual_question_classes != expected_question_classes:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "entry_question_classes_mismatch",
                        "rel_path": rel_path,
                        "expected": expected_question_classes,
                        "actual": actual_question_classes,
                    }
                )
            if "current_turn_legality" in actual_question_classes:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "current_turn_legality_must_not_bind_to_root_entry",
                        "rel_path": rel_path,
                    }
                )
            authority_row = authority_entry_map.get(rel_path)
            for question_class in actual_question_classes:
                expected = EXPECTED_QUESTION_RULES.get(question_class)
                if expected is None or authority_row is None:
                    continue
                expected_mode = str(expected.get("authority_mode") or "")
                if expected_mode and authority_row.authority_mode != expected_mode:
                    routing_violations.append(
                        {
                            "field": "entry_question_projection",
                            "reason": "entry_authority_mode_incompatible_with_question_class",
                            "rel_path": rel_path,
                            "question_class": question_class,
                            "expected": expected_mode,
                            "actual": authority_row.authority_mode,
                        }
                    )

        for gateway_class, row in gateway_question_projection_map.items():
            gateway_effect_target = gateway_effect_target_map.get(gateway_class)
            if gateway_effect_target is None:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "unbound_gateway_class",
                        "gateway_class": gateway_class,
                    }
                )
                continue
            if row.effect_target_class != gateway_effect_target.effect_target_class:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "effect_target_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_class,
                        "actual": row.effect_target_class,
                    }
                )
            if row.question_class != gateway_effect_target.effect_target_question_class:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_question_class,
                        "actual": row.question_class,
                    }
                )
            if row.answer_mode != gateway_effect_target.effect_target_answer_mode:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "answer_mode_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_answer_mode,
                        "actual": row.answer_mode,
                    }
                )
            question_profile = question_profile_map.get(row.question_class)
            if question_profile is None:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_profile_missing",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                    }
                )
                continue
            if row.answer_mode != question_profile.answer_mode:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_profile_answer_mode_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": question_profile.answer_mode,
                        "actual": row.answer_mode,
                    }
                )
            if bool(row.current_turn_authority_allowed) != bool(question_profile.current_turn_authority_allowed):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "current_turn_authority_allowed_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": bool(question_profile.current_turn_authority_allowed),
                        "actual": bool(row.current_turn_authority_allowed),
                    }
                )
            if bool(row.root_entry_required) != bool(question_profile.root_entry_required):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "root_entry_required_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": bool(question_profile.root_entry_required),
                        "actual": bool(row.root_entry_required),
                    }
                )
            expected_rule = EXPECTED_QUESTION_RULES.get(row.question_class)
            if expected_rule is not None and row.effect_target_class != str(expected_rule.get("corpus_class") or ""):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "effect_target_class_incompatible_with_question_class",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": str(expected_rule.get("corpus_class") or ""),
                        "actual": row.effect_target_class,
                    }
                )

        if root_index_entry:
            root_index_projection = entry_projection_map.get(root_index_entry)
            if root_index_projection is None:
                routing_violations.append(
                    {"field": "entry_question_projection", "reason": "root_index_entry_missing_projection", "rel_path": root_index_entry}
                )
            elif sorted(set(root_index_projection.question_classes)) != ["root_entry_navigation"]:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "root_index_entry_wrong_question_class",
                        "rel_path": root_index_entry,
                        "actual": sorted(set(root_index_projection.question_classes)),
                    }
                )

        if set(reading_paths) != set(registry_paths):
            structure_violations.append(
                {"field": "entry_question_projection", "reason": "reading_order_registry_mismatch"}
            )

        if adjudication_redirect.question_class != "current_turn_legality":
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "adjudication_redirect_wrong_question_class",
                    "actual": adjudication_redirect.question_class,
                }
            )
        if tuple(adjudication_redirect.terminal_machine_surfaces) != EXPECTED_TERMINAL_MACHINE_SURFACES:
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "terminal_machine_surfaces_mismatch",
                    "expected": list(EXPECTED_TERMINAL_MACHINE_SURFACES),
                    "actual": list(adjudication_redirect.terminal_machine_surfaces),
                }
            )
        if tuple(adjudication_redirect.forbidden_root_corpus_classes) != EXPECTED_FORBIDDEN_ROOT_CLASSES:
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "forbidden_root_corpus_classes_mismatch",
                    "expected": list(EXPECTED_FORBIDDEN_ROOT_CLASSES),
                    "actual": list(adjudication_redirect.forbidden_root_corpus_classes),
                }
            )
        if "machine_registry_directory" in set(adjudication_redirect.forbidden_root_corpus_classes):
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "machine_registry_directory_must_not_be_forbidden_for_current_turn_legality",
                }
            )

        for anchor in anchor_checks:
            path = (repo_root / anchor.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append(
                    {"field": "question_routing_anchor_checks", "reason": "anchor_file_missing", "rel_path": anchor.rel_path}
                )
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            missing_markers = find_missing_markers(text, anchor.required_markers)
            for marker in missing_markers:
                anchor_violations.append(
                    {
                        "field": "question_routing_anchor_checks",
                        "reason": "required_marker_missing",
                        "rel_path": anchor.rel_path,
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (routing_violations or anchor_violations):
        error_code = ERR_ROUTING

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"routing_violation:{row['field']}:{row['reason']}" for row in routing_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ROUTING),
        "routing_entry_path": str(routing_entry_path),
        "routing_active_path": str(routing_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "root_dir": str(routing_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "question_routing_anchor_check_count": len(anchor_checks),
        "question_class_profile_count": len(question_profiles),
        "entry_question_projection_count": len(entry_projections),
        "gateway_question_projection_count": len(gateway_question_projections),
        "question_class_profiles": [
            {
                "question_class": row.question_class,
                "answer_mode": row.answer_mode,
                "current_turn_authority_allowed": row.current_turn_authority_allowed,
                "root_entry_required": row.root_entry_required,
            }
            for row in question_profiles
        ],
        "entry_question_projection": [
            {
                "rel_path": row.rel_path,
                "question_classes": list(row.question_classes),
            }
            for row in entry_projections
        ],
        "gateway_question_projection": [
            {
                "gateway_class": row.gateway_class,
                "effect_target_class": row.effect_target_class,
                "question_class": row.question_class,
                "answer_mode": row.answer_mode,
                "current_turn_authority_allowed": row.current_turn_authority_allowed,
                "root_entry_required": row.root_entry_required,
            }
            for row in gateway_question_projections
        ],
        "adjudication_redirect": {
            "question_class": adjudication_redirect.question_class,
            "terminal_machine_surfaces": list(adjudication_redirect.terminal_machine_surfaces),
            "forbidden_root_corpus_classes": list(adjudication_redirect.forbidden_root_corpus_classes),
        },
        "structure_violations": structure_violations,
        "routing_violations": routing_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
