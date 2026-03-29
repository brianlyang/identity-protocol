#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from types import SimpleNamespace
from typing import Any

from registry_alias_control_plane_common import resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_row_validation_common import validate_contract_row_batches
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_machine_registry_completeness_common import (
    default_surface_stem_from_family_id,
    extract_validator_error_codes,
    extract_repo_rel_path_surface_stem,
    family_surface_stem_binding_policy_from_doc,
    family_surface_stem_overrides_from_doc,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_checks_from_doc,
    extract_validator_status_key,
    load_mapping_descriptor,
    load_root_machine_registry_completeness,
    machine_registry_completeness_rows_from_doc,
    repo_rel_path_escape_policy_from_doc,
    repo_rel_path_pattern_matches,
    repo_rel_path_role_typing_policy_from_doc,
    repo_rel_path_surface_stem_policy_from_doc,
    readme_machine_registry_completeness_surface,
    repo_rel_path_scope_policy_from_doc,
    resolve_repo_relative_surface,
    required_probe_surface_contract_fields_from_doc,
    required_probe_surface_contract_values_from_doc,
    required_repo_rel_path_patterns_from_doc,
    required_descriptor_field_modes_from_doc,
    required_descriptor_fields_from_doc,
    required_validator_surface_contract_fields_from_doc,
    required_validator_surface_contract_values_from_doc,
    require_self_describing_families,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families

STATUS_KEY = "protocol_root_machine_registry_completeness_status"
ERR_REGISTRY = "IP-RMRC-001"
ERR_STRUCTURE = "IP-RMRC-002"
ERR_COMPLETENESS = "IP-RMRC-003"
REQUIRED_VALIDATOR_SURFACE_CONTRACT_FIELDS = (
    "validator_root_doc_anchor_contract",
    "validator_row_projection_contract",
)
REQUIRED_VALIDATOR_SURFACE_CONTRACT_VALUES = {
    "validator_root_doc_anchor_contract": (
        "root_doc_anchor_status_pass_required_with_positive_anchor_check_count"
    ),
    "validator_row_projection_contract": (
        "nonempty_row_family_projection_rows_with_pass_required_coverage_and_identity_statuses"
    ),
}
REQUIRED_PROBE_SURFACE_CONTRACT_FIELDS = ("probe_shadow_bootstrap_contract",)
REQUIRED_PROBE_SURFACE_CONTRACT_VALUES = {
    "probe_shadow_bootstrap_contract": (
        "probe_shadow_common_contract_rows_pass_required_with_bootstrap_and_mirror_bindings"
    ),
}
EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS = {
    "explicit_machine_registry_row_families": {
        "order": 1,
        "contract_phrase": "required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_machine_registry_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_machine_registry_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_machine_registry_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize machine-registry completeness truth while missing or unexpected family or contract-row identities remain known only internally;",
    },
    "fail_close_preserves_machine_registry_violation_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve violation-reason projection and row-identity drift rather than hiding registry completeness drift behind shorthand counts or generic structure failure.",
    },
}

EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Machine-registry completeness must stay explicit",
        "Registered-complete root-mapping-family total and family-status-row total must therefore stay congruent under machine-readable coverage",
        "Machine-registry law does not become canonical merely because a mapping file",
        "A governed root mapping family must be admitted into the registry directory",
        "registry-completeness failure rather than a",
        "Admission without discoverable enforcement still leaves the machine",
        "A lawful root mapping family must therefore disclose the validator, probe,",
        "shared-common, emitted status-key, and emitted error-code surfaces that govern it.",
        "validator root-doc-anchor and row-projection contract surfaces",
        "probe shadow-bootstrap contract surfaces as machine-readable surface rows rather than hidden probe shell folklore.",
        "machine-readable surface rows rather than hidden validator folklore.",
        "Those repo-relative path surfaces must remain repo-root relative and",
        "Absolute-path capture or parent-escape capture would let local filesystem accident impersonate governed protocol law.",
        "descriptor paths that bypass repo-root-relative discipline.",
        "Repo-relative descriptor surfaces must also remain role-typed.",
        "role-swapped descriptor paths inside repo root.",
        "Those role-typed surfaces must also remain cross-role coherent.",
        "descriptor surface sets whose role-typed paths are cross-family incoherent.",
        "Those cross-role coherent descriptor surfaces must also remain family-congruent.",
        "explicit registry-declared surface-stem binding when a family borrows another admitted family's enforcement surfaces.",
        "descriptor surface sets that impersonate a different admitted family without explicit registry declaration.",
    ),
    "identity/protocol/README.md": (
        "## Root machine-registry completeness discipline",
        "Registered-complete root-mapping-family total and family-status-row total must also remain congruent under machine-readable coverage completeness",
        "a law-bearing root mapping family does not gain canonical status from on-disk presence alone;",
        "a governed root mapping family must appear in the admitted machine-registry child set, normally as a current file plus its active versioned file;",
        "if a root mapping family exists on disk but is absent from that admitted child set, registry completeness has failed and current-turn consumption must fail-close.",
        "4. an admitted root mapping family must disclose its validator, probe, shared-common, emitted status-key, and emitted error-code enforcement surfaces to the machine world;",
        "5. an admitted root mapping family must also disclose its validator root-doc-anchor and row-projection contract surfaces as machine-readable surface rows;",
        "5a. an admitted root mapping family must also disclose its probe shadow-bootstrap contract surfaces as machine-readable surface rows;",
        "Hidden enforcement knowledge does not satisfy registry completeness.",
        "These machine-registry-completeness rules must remain bound to canonical machine-registry-completeness rows rather than drifting into soft summary prose.",
        "1. required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;",
        "Repo-relative descriptor surfaces must also stay repo-root relative and",
        "if they exist locally.",
        "Repo-relative descriptor surfaces must also remain role-typed; validator, probe, and shared-common paths are not interchangeable repo files.",
        "Those role-typed surfaces must also remain cross-role coherent; validator, probe, and shared-common paths for one admitted family may not silently point at different root surface stems.",
        "Those cross-role coherent descriptor surfaces must also remain family-congruent; if an admitted family borrows another family's coherent descriptor stem, that binding must be explicitly declared in registry completeness law.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root machine-registry completeness boundary",
        "Machine-registry completeness must also keep admitted family and emitted status disclosure explicit as separate row families",
        "Law-bearing root mapping families under `identity/protocol/mappings/` become canonical only when admitted by the machine-registry directory child set.",
        "On-disk presence without registry admission does not authorize current-turn consumption, legal ingress, or bundle membership.",
        "Registry-completeness drift is a root-law failure, not a convenience-layer warning.",
        "5. Registry admission without discoverable validator/probe/common/status-key/error-code surfaces is still incomplete.",
        "5a. Registry admission without discoverable validator root-doc-anchor and row-projection contract surfaces is still incomplete.",
        "5b. Registry admission without discoverable probe shadow-bootstrap contract surfaces is still incomplete.",
        "6. Repo-relative descriptor surfaces disclosed by an admitted family must remain repo-root relative and repo-contained; absolute-path or parent-escape capture is non-compliant.",
        "7. Repo-relative descriptor surfaces disclosed by an admitted family must also stay role-typed; validator, probe, and shared-common path classes are not interchangeable.",
        "8. Role-typed repo-relative descriptor surfaces disclosed by an admitted family must also stay cross-role coherent; validator/probe/common may not silently bind to different root surface stems.",
        "9. Cross-role coherent descriptor surfaces disclosed by an admitted family must also stay family-congruent; borrowing another family's descriptor stem requires explicit registry-completeness declaration rather than silent impersonation.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime registry-completeness boundary",
        "Runtime must also keep admitted family and emitted status disclosure explicit during machine-registry validation",
        "Runtime may consume only root mapping families admitted by governed machine-registry completeness law.",
        "A root mapping file present on disk but absent from the admitted child set is non-canonical for runtime legality.",
        "Runtime must fail-close on registry-completeness drift rather than loading the most convenient on-disk mapping.",
        "5. Runtime must discover validator/probe/common/status-key/error-code surfaces from admitted mapping-family descriptors rather than hidden local knowledge.",
        "5a. Runtime must also discover validator root-doc-anchor and row-projection contract surfaces from admitted mapping-family descriptors rather than hidden local knowledge.",
        "5b. Runtime must also discover probe shadow-bootstrap contract surfaces from admitted mapping-family descriptors rather than hidden local probe convention.",
        "6. Runtime must reject descriptor paths that are absolute or escape repo root; repo-relative descriptor surfaces must stay repo-root relative and repo-contained.",
        "7. Runtime must also reject role-swapped descriptor paths; validator, probe, and shared-common surfaces must stay role-typed rather than merely repo-local.",
        "8. Runtime must also reject cross-role incoherent descriptor sets; validator/probe/common surfaces for one admitted family must converge on one root surface stem.",
        "9. Runtime must also reject undeclared family-incongruent descriptor sets; even a coherent validator/probe/common set is non-canonical unless any cross-family stem binding is explicitly declared by registry completeness law.",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate protocol-root machine-registry completeness for governed root mapping families."
    )
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    completeness_doc, completeness_entry_path, completeness_active_path, completeness_alias_error = (
        load_root_machine_registry_completeness(repo_root)
    )
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    completeness_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    family_status_rows: list[dict[str, Any]] = []
    expected_family_status_row_count = 0
    family_status_row_coverage_incomplete = False
    discovered_family_ids: list[str] = []
    family_status_row_ids: list[str] = []
    missing_family_status_row_ids: list[str] = []
    unexpected_family_status_row_ids: list[str] = []
    family_status_row_identity_projection_incomplete = False
    validator_surface_contract_row_ids: list[str] = []
    missing_validator_surface_contract_row_ids: list[str] = []
    unexpected_validator_surface_contract_row_ids: list[str] = []
    validator_surface_contract_row_coverage_incomplete = False
    validator_surface_contract_row_identity_projection_incomplete = False
    probe_surface_contract_row_ids: list[str] = []
    missing_probe_surface_contract_row_ids: list[str] = []
    unexpected_probe_surface_contract_row_ids: list[str] = []
    probe_surface_contract_row_coverage_incomplete = False
    probe_surface_contract_row_identity_projection_incomplete = False
    registered_complete_family_ids: list[str] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    for prefix, doc, alias_error, empty_reason in (
        (
            "root_machine_registry_completeness",
            completeness_doc,
            completeness_alias_error,
            "root_machine_registry_completeness_empty_or_invalid",
        ),
        ("root_corpus_registry", registry_doc, registry_alias_error, "root_corpus_registry_empty_or_invalid"),
    ):
        if alias_error:
            stale_reasons.append(f"{prefix}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(empty_reason)
            error_code = ERR_REGISTRY

    anchor_checks = anchor_checks_from_doc(completeness_doc) if completeness_doc else ()
    machine_registry_completeness_rows = (
        machine_registry_completeness_rows_from_doc(completeness_doc)
        if completeness_doc
        else ()
    )
    machine_registry_completeness_surface = (
        readme_machine_registry_completeness_surface(repo_root)
    )
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    self_describing_required = require_self_describing_families(completeness_doc) if completeness_doc else False
    required_descriptor_fields = required_descriptor_fields_from_doc(completeness_doc) if completeness_doc else ()
    required_descriptor_field_modes = required_descriptor_field_modes_from_doc(completeness_doc) if completeness_doc else {}
    required_validator_surface_contract_fields = (
        required_validator_surface_contract_fields_from_doc(completeness_doc)
        if completeness_doc
        else ()
    )
    required_validator_surface_contract_values = (
        required_validator_surface_contract_values_from_doc(completeness_doc)
        if completeness_doc
        else {}
    )
    required_probe_surface_contract_fields = (
        required_probe_surface_contract_fields_from_doc(completeness_doc)
        if completeness_doc
        else ()
    )
    required_probe_surface_contract_values = (
        required_probe_surface_contract_values_from_doc(completeness_doc)
        if completeness_doc
        else {}
    )
    repo_rel_path_scope_policy = repo_rel_path_scope_policy_from_doc(completeness_doc) if completeness_doc else ""
    repo_rel_path_escape_policy = repo_rel_path_escape_policy_from_doc(completeness_doc) if completeness_doc else ""
    repo_rel_path_role_typing_policy = repo_rel_path_role_typing_policy_from_doc(completeness_doc) if completeness_doc else ""
    repo_rel_path_surface_stem_policy = repo_rel_path_surface_stem_policy_from_doc(completeness_doc) if completeness_doc else ""
    family_surface_stem_binding_policy = family_surface_stem_binding_policy_from_doc(completeness_doc) if completeness_doc else ""
    family_surface_stem_overrides = family_surface_stem_overrides_from_doc(completeness_doc) if completeness_doc else {}
    required_repo_rel_path_patterns = required_repo_rel_path_patterns_from_doc(completeness_doc) if completeness_doc else {}

    if not stale_reasons:
        expected_scalar_fields = {
            "completeness_family": "protocol_root_machine_registry_completeness",
            "completeness_version": "v1",
            "registry_directory_rel_path": "identity/protocol/mappings",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "validator_script": "scripts/validate_protocol_root_machine_registry_completeness.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh",
            "common_script": "scripts/root_machine_registry_completeness_common.py",
            "status_key": STATUS_KEY,
            "root_family_prefix": "root-",
            "current_suffix": ".current.yaml",
            "version_regex": r"^root-[a-z0-9-]+\.v[0-9]+\.yaml$",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(completeness_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_registry_completeness_field_invalid:{field}")
                error_code = ERR_REGISTRY

        if completeness_doc.get("require_current_version_pairs") is not True:
            stale_reasons.append("root_machine_registry_completeness_pairing_rule_invalid")
            error_code = ERR_REGISTRY
        if self_describing_required and not required_descriptor_fields:
            stale_reasons.append("root_machine_registry_completeness_descriptor_fields_missing")
            error_code = ERR_REGISTRY
        if repo_rel_path_scope_policy != "repo_root_relative_only":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_scope_policy_invalid")
            error_code = ERR_REGISTRY
        if repo_rel_path_escape_policy != "fail_closed":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_escape_policy_invalid")
            error_code = ERR_REGISTRY
        if repo_rel_path_role_typing_policy != "root_protocol_surface_patterns_required":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_role_typing_policy_invalid")
            error_code = ERR_REGISTRY
        if repo_rel_path_surface_stem_policy != "cross_role_stem_coherent":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_surface_stem_policy_invalid")
            error_code = ERR_REGISTRY
        if family_surface_stem_binding_policy != "family_id_surface_stem_congruent_or_explicit_override":
            stale_reasons.append("root_machine_registry_completeness_family_surface_stem_binding_policy_invalid")
            error_code = ERR_REGISTRY
        if family_surface_stem_overrides != {"root-corpus-registry": "root_corpus_governance"}:
            stale_reasons.append("root_machine_registry_completeness_family_surface_stem_overrides_invalid")
            error_code = ERR_REGISTRY
        if tuple(required_descriptor_fields) != ("validator_script", "probe_script", "common_script", "status_key", "error_codes"):
            stale_reasons.append("root_machine_registry_completeness_descriptor_fields_invalid")
            error_code = ERR_REGISTRY
        if required_descriptor_field_modes != {
            "validator_script": "repo_rel_path",
            "probe_script": "repo_rel_path",
            "common_script": "repo_rel_path",
            "status_key": "validator_status_key",
            "error_codes": "validator_error_code_list",
        }:
            stale_reasons.append("root_machine_registry_completeness_descriptor_field_modes_invalid")
            error_code = ERR_REGISTRY
        if required_validator_surface_contract_fields != REQUIRED_VALIDATOR_SURFACE_CONTRACT_FIELDS:
            stale_reasons.append(
                "root_machine_registry_completeness_required_validator_surface_contract_fields_invalid"
            )
            error_code = ERR_REGISTRY
        if required_validator_surface_contract_values != REQUIRED_VALIDATOR_SURFACE_CONTRACT_VALUES:
            stale_reasons.append(
                "root_machine_registry_completeness_required_validator_surface_contract_values_invalid"
            )
            error_code = ERR_REGISTRY
        if required_probe_surface_contract_fields != REQUIRED_PROBE_SURFACE_CONTRACT_FIELDS:
            stale_reasons.append(
                "root_machine_registry_completeness_required_probe_surface_contract_fields_invalid"
            )
            error_code = ERR_REGISTRY
        if required_probe_surface_contract_values != REQUIRED_PROBE_SURFACE_CONTRACT_VALUES:
            stale_reasons.append(
                "root_machine_registry_completeness_required_probe_surface_contract_values_invalid"
            )
            error_code = ERR_REGISTRY
        if required_repo_rel_path_patterns != {
            "validator_script": r"^scripts/validate_protocol_(?P<surface_stem>root_[a-z0-9_]+)\.py$",
            "probe_script": r"^scripts/ci/run_protocol_(?P<surface_stem>root_[a-z0-9_]+)_probes_ci\.sh$",
            "common_script": r"^scripts/(?P<surface_stem>root_[a-z0-9_]+)_common\.py$",
        }:
            stale_reasons.append("root_machine_registry_completeness_required_repo_rel_path_patterns_invalid")
            error_code = ERR_REGISTRY

        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_machine_registry_completeness",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

        if not anchor_checks:
            stale_reasons.append("root_machine_registry_completeness_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not machine_registry_completeness_rows:
            stale_reasons.append("root_machine_registry_completeness_rows_missing")
            error_code = ERR_REGISTRY

        for field in ("registry_current_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(completeness_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_machine_registry_completeness_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    version_re = None
    if not stale_reasons:
        try:
            version_re = re.compile(str(completeness_doc.get("version_regex") or "").strip())
        except re.error:
            structure_violations.append({"field": "version_regex", "reason": "regex_invalid"})
        if structure_violations:
            error_code = ERR_STRUCTURE

    if not stale_reasons and not structure_violations:
        registry_directory_rel = str(completeness_doc.get("registry_directory_rel_path") or "").strip()
        registry_dir = (repo_root / registry_directory_rel).resolve()
        if not registry_dir.exists() or not registry_dir.is_dir():
            completeness_violations.append(
                {
                    "field": "registry_directory",
                    "reason": "registry_directory_missing",
                    "rel_path": registry_directory_rel,
                }
            )
        registry_map = {row.rel_path: row for row in registry_entries}
        mappings_entry = registry_map.get("identity/protocol/mappings")
        if mappings_entry is None:
            completeness_violations.append(
                {
                    "field": "root_corpus_registry",
                    "reason": "mappings_directory_not_registered",
                }
            )
            registered_children: set[str] = set()
        else:
            registered_children = set(mappings_entry.required_children)
            prefix = str(completeness_doc.get("root_family_prefix") or "")
            current_suffix = str(completeness_doc.get("current_suffix") or "")
            registered_current_family_ids: set[str] = set()
            registered_version_family_ids: set[str] = set()
            for child in sorted(
                child for child in registered_children if child.startswith(prefix) and child.endswith(".yaml")
            ):
                if current_suffix and child.endswith(current_suffix):
                    registered_current_family_ids.add(child[: -len(current_suffix)])
                elif version_re and version_re.fullmatch(child):
                    registered_version_family_ids.add(child.split(".v", 1)[0])
            registered_complete_family_ids = sorted(
                registered_current_family_ids & registered_version_family_ids
            )

        if registry_dir.exists() and registry_dir.is_dir():
            prefix = str(completeness_doc.get("root_family_prefix") or "")
            current_suffix = str(completeness_doc.get("current_suffix") or "")
            root_yaml_files = sorted(
                path.name
                for path in registry_dir.iterdir()
                if path.is_file() and path.name.startswith(prefix) and path.name.endswith(".yaml")
            )
            actual_root_yaml_set = set(root_yaml_files)

            families: dict[str, dict[str, Any]] = {}
            for name in root_yaml_files:
                if current_suffix and name.endswith(current_suffix):
                    family_id = name[: -len(current_suffix)]
                    row = families.setdefault(family_id, {"current_file": "", "version_files": []})
                    if row["current_file"]:
                        structure_violations.append(
                            {"field": "root_mapping_family", "reason": "duplicate_current_file", "family_id": family_id}
                        )
                    row["current_file"] = name
                elif version_re and version_re.fullmatch(name):
                    family_id = name.split(".v", 1)[0]
                    row = families.setdefault(family_id, {"current_file": "", "version_files": []})
                    row["version_files"].append(name)
                else:
                    structure_violations.append(
                        {"field": "root_mapping_family", "reason": "unclassifiable_root_yaml", "filename": name}
                    )
            discovered_family_ids = sorted(families)
            expected_family_status_row_count = len(discovered_family_ids)

            for child in sorted(child for child in registered_children if child.startswith(prefix) and child.endswith(".yaml")):
                if child not in actual_root_yaml_set:
                    completeness_violations.append(
                        {"field": "registered_child", "reason": "registered_child_missing_on_disk", "child": child}
                    )

            for family_id in sorted(families):
                row = families[family_id]
                current_file = str(row.get("current_file") or "")
                version_files = sorted(set(str(item) for item in row.get("version_files") or [] if str(item)))
                family_violations: list[str] = []
                active_file = ""
                alias_error = ""
                descriptor_field_rows: list[dict[str, Any]] = []
                validator_surface_contract_rows: list[dict[str, Any]] = []
                probe_surface_contract_rows: list[dict[str, Any]] = []
                descriptor_surface_stems: dict[str, str] = {}
                default_family_surface_stem, expected_family_surface_stem_error = default_surface_stem_from_family_id(
                    family_id
                )
                expected_family_surface_stem = family_surface_stem_overrides.get(
                    family_id, default_family_surface_stem
                )
                expected_family_surface_stem_source = (
                    "explicit_override" if family_id in family_surface_stem_overrides else "family_id_default"
                )

                if not current_file:
                    family_violations.append("current_file_missing")
                    completeness_violations.append(
                        {"field": "root_mapping_family", "reason": "current_file_missing", "family_id": family_id}
                    )
                elif current_file not in registered_children:
                    family_violations.append("current_file_not_registered")
                    completeness_violations.append(
                        {
                            "field": "root_mapping_family",
                            "reason": "current_file_not_registered",
                            "family_id": family_id,
                            "child": current_file,
                        }
                    )

                if completeness_doc.get("require_current_version_pairs") and not version_files:
                    family_violations.append("version_file_missing")
                    completeness_violations.append(
                        {"field": "root_mapping_family", "reason": "version_file_missing", "family_id": family_id}
                    )

                for version_file in version_files:
                    if version_file not in registered_children:
                        family_violations.append("version_file_not_registered")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "version_file_not_registered",
                                "family_id": family_id,
                                "child": version_file,
                            }
                        )

                if current_file:
                    current_rel = f"{registry_directory_rel}/{current_file}"
                    active_path, active_ref, alias_error = resolve_current_yaml_alias(repo_root, current_rel)
                    active_file = active_path.name if active_path else ""
                    if alias_error:
                        family_violations.append("current_alias_error")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "current_alias_error",
                                "family_id": family_id,
                                "alias_error": alias_error,
                            }
                        )
                    else:
                        if active_file not in version_files:
                            family_violations.append("active_file_not_in_family_versions")
                            completeness_violations.append(
                                {
                                    "field": "root_mapping_family",
                                    "reason": "active_file_not_in_family_versions",
                                    "family_id": family_id,
                                    "active_file": active_ref,
                                }
                            )
                        if active_file not in registered_children:
                            family_violations.append("active_file_not_registered")
                            completeness_violations.append(
                                {
                                    "field": "root_mapping_family",
                                    "reason": "active_file_not_registered",
                                    "family_id": family_id,
                                    "child": active_file,
                                }
                            )
                        elif self_describing_required:
                            active_doc = load_mapping_descriptor(active_path)
                            if not active_doc:
                                family_violations.append("active_mapping_doc_invalid")
                                completeness_violations.append(
                                    {
                                        "field": "root_mapping_family",
                                        "reason": "active_mapping_doc_invalid",
                                        "family_id": family_id,
                                        "active_file": active_file,
                                    }
                                )
                            else:
                                for descriptor_field in required_descriptor_fields:
                                    descriptor_mode = required_descriptor_field_modes.get(descriptor_field, "")
                                    row_status = STATUS_FAIL_REQUIRED
                                    row_payload: dict[str, Any] = {
                                        "field": descriptor_field,
                                        "mode": descriptor_mode,
                                    }
                                    if descriptor_mode == "validator_error_code_list":
                                        raw_codes = active_doc.get(descriptor_field)
                                        descriptor_codes = tuple(
                                            str(item or "").strip()
                                            for item in raw_codes
                                            if str(item or "").strip()
                                        ) if isinstance(raw_codes, list) else ()
                                        expected_codes, error_codes_error = extract_validator_error_codes(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        row_payload["values"] = list(descriptor_codes)
                                        row_payload["expected_values"] = list(expected_codes)
                                        row_payload["support_error"] = error_codes_error
                                        row_status = (
                                            STATUS_PASS_REQUIRED
                                            if descriptor_codes and not error_codes_error and descriptor_codes == expected_codes
                                            else STATUS_FAIL_REQUIRED
                                        )
                                        descriptor_field_rows.append({**row_payload, "status": row_status})
                                        if not descriptor_codes:
                                            family_violations.append("descriptor_field_missing")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_field_missing",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                }
                                            )
                                        elif error_codes_error:
                                            family_violations.append("descriptor_supporting_surface_invalid")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_supporting_surface_invalid",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "support_error": error_codes_error,
                                                }
                                            )
                                        elif descriptor_codes != expected_codes:
                                            family_violations.append("descriptor_value_mismatch")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_value_mismatch",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "actual_values": list(descriptor_codes),
                                                    "expected_values": list(expected_codes),
                                                }
                                            )
                                        continue

                                    descriptor_value = str(active_doc.get(descriptor_field) or "").strip()
                                    row_payload["value"] = descriptor_value
                                    if descriptor_mode == "repo_rel_path":
                                        _rel_path, repo_rel_error, resolved_path = resolve_repo_relative_surface(
                                            repo_root, descriptor_value
                                        )
                                        expected_pattern = required_repo_rel_path_patterns.get(descriptor_field, "")
                                        pattern_match = repo_rel_path_pattern_matches(descriptor_value, expected_pattern)
                                        surface_stem, surface_stem_error = extract_repo_rel_path_surface_stem(
                                            descriptor_value, expected_pattern
                                        )
                                        row_payload["resolved_path"] = resolved_path
                                        row_payload["support_error"] = repo_rel_error
                                        row_payload["expected_pattern"] = expected_pattern
                                        row_payload["pattern_match"] = pattern_match
                                        row_payload["surface_stem"] = surface_stem
                                        row_payload["surface_stem_error"] = surface_stem_error
                                        row_status = (
                                            STATUS_PASS_REQUIRED
                                            if descriptor_value and not repo_rel_error and pattern_match and not surface_stem_error
                                            else STATUS_FAIL_REQUIRED
                                        )
                                    elif descriptor_mode == "validator_status_key":
                                        expected_status_key, status_key_error = extract_validator_status_key(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        row_payload["expected_value"] = expected_status_key
                                        row_payload["support_error"] = status_key_error
                                        row_status = (
                                            STATUS_PASS_REQUIRED
                                            if descriptor_value and not status_key_error and descriptor_value == expected_status_key
                                            else STATUS_FAIL_REQUIRED
                                        )
                                    descriptor_field_rows.append(
                                        {
                                            **row_payload,
                                            "status": row_status,
                                        }
                                    )
                                    if not descriptor_value:
                                        family_violations.append("descriptor_field_missing")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "descriptor_field_missing",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                }
                                            )
                                    elif descriptor_mode == "repo_rel_path":
                                        _rel_path, repo_rel_error, resolved_path = resolve_repo_relative_surface(
                                            repo_root, descriptor_value
                                        )
                                        expected_pattern = required_repo_rel_path_patterns.get(descriptor_field, "")
                                        pattern_match = repo_rel_path_pattern_matches(descriptor_value, expected_pattern)
                                        surface_stem, surface_stem_error = extract_repo_rel_path_surface_stem(
                                            descriptor_value, expected_pattern
                                        )
                                        if not pattern_match:
                                            family_violations.append("descriptor_path_role_pattern_mismatch")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_role_pattern_mismatch",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "expected_pattern": expected_pattern,
                                                }
                                            )
                                        elif surface_stem_error:
                                            family_violations.append("descriptor_surface_stem_unresolved")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_surface_stem_unresolved",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "expected_pattern": expected_pattern,
                                                    "surface_stem_error": surface_stem_error,
                                                }
                                            )
                                        else:
                                            descriptor_surface_stems[descriptor_field] = surface_stem
                                        if repo_rel_error == "absolute_path_forbidden":
                                            family_violations.append("descriptor_path_not_repo_relative")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_not_repo_relative",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                        if repo_rel_error == "repo_root_escape_forbidden":
                                            family_violations.append("descriptor_path_escapes_repo_root")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_escapes_repo_root",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                        if repo_rel_error == "path_missing":
                                            family_violations.append("descriptor_path_missing")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_missing",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                    elif descriptor_mode == "validator_status_key":
                                        expected_status_key, status_key_error = extract_validator_status_key(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        if status_key_error:
                                            family_violations.append("descriptor_supporting_surface_invalid")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_supporting_surface_invalid",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "support_error": status_key_error,
                                                }
                                            )
                                        elif descriptor_value != expected_status_key:
                                            family_violations.append("descriptor_value_mismatch")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_value_mismatch",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "actual_value": descriptor_value,
                                                    "expected_value": expected_status_key,
                                                }
                                            )

                                for contract_field in required_validator_surface_contract_fields:
                                    expected_contract_value = required_validator_surface_contract_values.get(
                                        contract_field, ""
                                    )
                                    actual_contract_value = str(active_doc.get(contract_field) or "").strip()
                                    contract_row_id = f"{family_id}:{contract_field}"
                                    contract_row_status = (
                                        STATUS_PASS_REQUIRED
                                        if actual_contract_value
                                        and actual_contract_value == expected_contract_value
                                        else STATUS_FAIL_REQUIRED
                                    )
                                    validator_surface_contract_rows.append(
                                        {
                                            "contract_row_id": contract_row_id,
                                            "contract_field": contract_field,
                                            "value": actual_contract_value,
                                            "expected_value": expected_contract_value,
                                            "status": contract_row_status,
                                        }
                                    )
                                    validator_surface_contract_row_ids.append(contract_row_id)
                                    if not actual_contract_value:
                                        family_violations.append("validator_surface_contract_field_missing")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "validator_surface_contract_field_missing",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                "contract_field": contract_field,
                                                "expected_value": expected_contract_value,
                                            }
                                        )
                                    elif actual_contract_value != expected_contract_value:
                                        family_violations.append("validator_surface_contract_value_mismatch")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "validator_surface_contract_value_mismatch",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                "contract_field": contract_field,
                                                "actual_value": actual_contract_value,
                                                "expected_value": expected_contract_value,
                                            }
                                        )

                                for contract_field in required_probe_surface_contract_fields:
                                    expected_contract_value = required_probe_surface_contract_values.get(
                                        contract_field, ""
                                    )
                                    actual_contract_value = str(active_doc.get(contract_field) or "").strip()
                                    contract_row_id = f"{family_id}:{contract_field}"
                                    contract_row_status = (
                                        STATUS_PASS_REQUIRED
                                        if actual_contract_value
                                        and actual_contract_value == expected_contract_value
                                        else STATUS_FAIL_REQUIRED
                                    )
                                    probe_surface_contract_rows.append(
                                        {
                                            "contract_row_id": contract_row_id,
                                            "contract_field": contract_field,
                                            "value": actual_contract_value,
                                            "expected_value": expected_contract_value,
                                            "status": contract_row_status,
                                        }
                                    )
                                    probe_surface_contract_row_ids.append(contract_row_id)
                                    if not actual_contract_value:
                                        family_violations.append("probe_surface_contract_field_missing")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "probe_surface_contract_field_missing",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                "contract_field": contract_field,
                                                "expected_value": expected_contract_value,
                                            }
                                        )
                                    elif actual_contract_value != expected_contract_value:
                                        family_violations.append("probe_surface_contract_value_mismatch")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "probe_surface_contract_value_mismatch",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                "contract_field": contract_field,
                                                "actual_value": actual_contract_value,
                                                "expected_value": expected_contract_value,
                                            }
                                        )

                unique_surface_stems = sorted(set(descriptor_surface_stems.values()))
                if len(unique_surface_stems) > 1:
                    family_violations.append("descriptor_surface_stem_mismatch")
                    completeness_violations.append(
                        {
                            "field": "root_mapping_family",
                            "reason": "descriptor_surface_stem_mismatch",
                            "family_id": family_id,
                            "active_file": active_file,
                            "descriptor_surface_stems": dict(descriptor_surface_stems),
                        }
                    )
                elif unique_surface_stems:
                    actual_family_surface_stem = unique_surface_stems[0]
                    if expected_family_surface_stem_error:
                        family_violations.append("family_surface_stem_unresolved")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "family_surface_stem_unresolved",
                                "family_id": family_id,
                                "active_file": active_file,
                                "family_surface_stem_error": expected_family_surface_stem_error,
                            }
                        )
                    elif actual_family_surface_stem != expected_family_surface_stem:
                        family_violations.append("descriptor_surface_family_mismatch")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "descriptor_surface_family_mismatch",
                                "family_id": family_id,
                                "active_file": active_file,
                                "expected_family_surface_stem": expected_family_surface_stem,
                                "actual_family_surface_stem": actual_family_surface_stem,
                                "descriptor_surface_stems": dict(descriptor_surface_stems),
                            }
                        )

                family_status_rows.append(
                    {
                        "family_id": family_id,
                        "current_file": current_file,
                        "version_files": version_files,
                        "active_file": active_file,
                        "alias_error": alias_error,
                        "expected_family_surface_stem": expected_family_surface_stem,
                        "expected_family_surface_stem_error": expected_family_surface_stem_error,
                        "expected_family_surface_stem_source": expected_family_surface_stem_source,
                        "self_describing_required": self_describing_required,
                        "required_descriptor_fields": list(required_descriptor_fields),
                        "required_descriptor_field_modes": dict(required_descriptor_field_modes),
                        "required_validator_surface_contract_fields": list(
                            required_validator_surface_contract_fields
                        ),
                        "required_validator_surface_contract_values": dict(
                            required_validator_surface_contract_values
                        ),
                        "required_probe_surface_contract_fields": list(
                            required_probe_surface_contract_fields
                        ),
                        "required_probe_surface_contract_values": dict(
                            required_probe_surface_contract_values
                        ),
                        "descriptor_field_rows": descriptor_field_rows,
                        "validator_surface_contract_rows": validator_surface_contract_rows,
                        "probe_surface_contract_rows": probe_surface_contract_rows,
                        "family_status": STATUS_PASS_REQUIRED if not family_violations else STATUS_FAIL_REQUIRED,
                        "family_violations": family_violations,
                    }
                )

            family_status_row_coverage_incomplete = (
                len(family_status_rows) != expected_family_status_row_count
            )
            if family_status_row_coverage_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_status_row_coverage_incomplete",
                        "expected_count": expected_family_status_row_count,
                        "actual_count": len(family_status_rows),
                    }
                )
            family_status_row_ids = [row["family_id"] for row in family_status_rows]
            missing_family_status_row_ids = sorted(
                set(discovered_family_ids) - set(family_status_row_ids)
            )
            unexpected_family_status_row_ids = sorted(
                set(family_status_row_ids) - set(discovered_family_ids)
            )
            family_status_row_identity_projection_incomplete = bool(
                missing_family_status_row_ids or unexpected_family_status_row_ids
            )
            if family_status_row_identity_projection_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_status_row_identity_projection_incomplete",
                        "missing_family_ids": missing_family_status_row_ids,
                        "unexpected_family_ids": unexpected_family_status_row_ids,
                    }
                )
            expected_family_validator_surface_contract_row_count = (
                len(discovered_family_ids) * len(required_validator_surface_contract_fields)
            )
            validator_surface_contract_row_coverage_incomplete = (
                len(validator_surface_contract_row_ids)
                != expected_family_validator_surface_contract_row_count
            )
            if validator_surface_contract_row_coverage_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_validator_surface_contract_row_coverage_incomplete",
                        "expected_count": expected_family_validator_surface_contract_row_count,
                        "actual_count": len(validator_surface_contract_row_ids),
                    }
                )
            expected_validator_surface_contract_row_ids = sorted(
                f"{family_id}:{contract_field}"
                for family_id in discovered_family_ids
                for contract_field in required_validator_surface_contract_fields
            )
            missing_validator_surface_contract_row_ids = sorted(
                set(expected_validator_surface_contract_row_ids)
                - set(validator_surface_contract_row_ids)
            )
            unexpected_validator_surface_contract_row_ids = sorted(
                set(validator_surface_contract_row_ids)
                - set(expected_validator_surface_contract_row_ids)
            )
            validator_surface_contract_row_identity_projection_incomplete = bool(
                missing_validator_surface_contract_row_ids
                or unexpected_validator_surface_contract_row_ids
            )
            if validator_surface_contract_row_identity_projection_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_validator_surface_contract_row_identity_projection_incomplete",
                        "missing_contract_row_ids": missing_validator_surface_contract_row_ids,
                        "unexpected_contract_row_ids": unexpected_validator_surface_contract_row_ids,
                    }
                )
            expected_family_probe_surface_contract_row_count = (
                len(discovered_family_ids) * len(required_probe_surface_contract_fields)
            )
            probe_surface_contract_row_coverage_incomplete = (
                len(probe_surface_contract_row_ids)
                != expected_family_probe_surface_contract_row_count
            )
            if probe_surface_contract_row_coverage_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_probe_surface_contract_row_coverage_incomplete",
                        "expected_count": expected_family_probe_surface_contract_row_count,
                        "actual_count": len(probe_surface_contract_row_ids),
                    }
                )
            expected_probe_surface_contract_row_ids = sorted(
                f"{family_id}:{contract_field}"
                for family_id in discovered_family_ids
                for contract_field in required_probe_surface_contract_fields
            )
            missing_probe_surface_contract_row_ids = sorted(
                set(expected_probe_surface_contract_row_ids)
                - set(probe_surface_contract_row_ids)
            )
            unexpected_probe_surface_contract_row_ids = sorted(
                set(probe_surface_contract_row_ids)
                - set(expected_probe_surface_contract_row_ids)
            )
            probe_surface_contract_row_identity_projection_incomplete = bool(
                missing_probe_surface_contract_row_ids
                or unexpected_probe_surface_contract_row_ids
            )
            if probe_surface_contract_row_identity_projection_incomplete:
                completeness_violations.append(
                    {
                        "field": "root_mapping_family",
                        "reason": "family_probe_surface_contract_row_identity_projection_incomplete",
                        "missing_contract_row_ids": missing_probe_surface_contract_row_ids,
                        "unexpected_contract_row_ids": unexpected_probe_surface_contract_row_ids,
                    }
                )

        for reason in machine_registry_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "machine_registry_completeness_surface",
                    "reason": f"machine_registry_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": machine_registry_completeness_rows,
                    "expected_rows": EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS,
                    "field_name": "machine_registry_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_machine_registry_completeness_id",
                    "non_contiguous_reason": "machine_registry_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_machine_registry_completeness_rows",
                    "extra_reason": "extra_machine_registry_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "machine_registry_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": machine_registry_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "machine_registry_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_machine_registry_completeness_surface_phrase",
                    "non_contiguous_reason": "machine_registry_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_machine_registry_completeness_surface_rows",
                    "extra_reason": "extra_machine_registry_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "machine_registry_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=completeness_violations,
        )
        expected_machine_registry_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS.values()
        ]
        actual_machine_registry_completeness_phrases = [
            row.contract_phrase for row in machine_registry_completeness_surface.rows
        ]
        expected_machine_registry_completeness_orders = [
            int(row["order"]) for row in EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS.values()
        ]
        actual_machine_registry_completeness_orders = [
            row.order for row in machine_registry_completeness_surface.rows
        ]
        if actual_machine_registry_completeness_phrases and tuple(
            actual_machine_registry_completeness_phrases
        ) != tuple(expected_machine_registry_completeness_phrases):
            completeness_violations.append(
                {
                    "field": "machine_registry_completeness_surface",
                    "reason": "machine_registry_completeness_surface_phrase_order_mismatch",
                    "expected": expected_machine_registry_completeness_phrases,
                    "actual": actual_machine_registry_completeness_phrases,
                }
            )
        if actual_machine_registry_completeness_orders and tuple(
            actual_machine_registry_completeness_orders
        ) != tuple(expected_machine_registry_completeness_orders):
            completeness_violations.append(
                {
                    "field": "machine_registry_completeness_surface",
                    "reason": "machine_registry_completeness_surface_order_mismatch",
                    "expected": expected_machine_registry_completeness_orders,
                    "actual": actual_machine_registry_completeness_orders,
                }
            )

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (completeness_violations or anchor_violations):
        error_code = ERR_COMPLETENESS

    projected_violation_reason_count = (
        len(structure_violations) + len(completeness_violations) + len(anchor_violations)
    )
    expected_projected_violation_reason_count = (
        len(structure_violations) + len(completeness_violations) + len(anchor_violations)
    )
    violation_projection_incomplete = (
        projected_violation_reason_count != expected_projected_violation_reason_count
    )
    violation_projection_status = (
        STATUS_FAIL_REQUIRED if violation_projection_incomplete else STATUS_PASS_REQUIRED
    )

    stale_reasons.extend(
        f"structure_violation:{row['field']}:{row['reason']}:{row.get('family_id', row.get('filename', ''))}".rstrip(":")
        for row in structure_violations
    )
    stale_reasons.extend(
        f"completeness_violation:{row['field']}:{row['reason']}:{row.get('family_id', row.get('child', ''))}".rstrip(":")
        for row in completeness_violations
    )
    stale_reasons.extend(
        f"anchor_violation:{row['rel_path']}:{row['reason']}:{row.get('marker', '')}".rstrip(":")
        for row in anchor_violations
    )
    if violation_projection_incomplete:
        stale_reasons.append("root_machine_registry_completeness_violation_projection_incomplete")
        if not error_code:
            error_code = ERR_COMPLETENESS

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    family_status_row_coverage_status = (
        STATUS_FAIL_REQUIRED if family_status_row_coverage_incomplete else STATUS_PASS_REQUIRED
    )
    family_status_row_identity_projection_status = (
        STATUS_FAIL_REQUIRED
        if family_status_row_identity_projection_incomplete
        else STATUS_PASS_REQUIRED
    )
    validator_surface_contract_row_coverage_status = (
        STATUS_FAIL_REQUIRED
        if validator_surface_contract_row_coverage_incomplete
        else STATUS_PASS_REQUIRED
    )
    validator_surface_contract_row_identity_projection_status = (
        STATUS_FAIL_REQUIRED
        if validator_surface_contract_row_identity_projection_incomplete
        else STATUS_PASS_REQUIRED
    )
    probe_surface_contract_row_coverage_status = (
        STATUS_FAIL_REQUIRED
        if probe_surface_contract_row_coverage_incomplete
        else STATUS_PASS_REQUIRED
    )
    probe_surface_contract_row_identity_projection_status = (
        STATUS_FAIL_REQUIRED
        if probe_surface_contract_row_identity_projection_incomplete
        else STATUS_PASS_REQUIRED
    )
    root_doc_anchor_status = (
        STATUS_FAIL_REQUIRED if anchor_violations else STATUS_PASS_REQUIRED
    )
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "registered_complete_root_mapping_families",
                "member_id_key": "family_id",
                "actual_rows": [
                    SimpleNamespace(family_id=family_id)
                    for family_id in discovered_family_ids
                ],
                "expected_rows": {
                    family_id: {} for family_id in registered_complete_family_ids
                },
                "id_attr": "family_id",
            },
            {
                "family_id": "family_status_rows",
                "member_id_key": "family_id",
                "actual_rows": [
                    SimpleNamespace(family_id=family_id)
                    for family_id in family_status_row_ids
                ],
                "expected_rows": {
                    family_id: {} for family_id in discovered_family_ids
                },
                "id_attr": "family_id",
            },
            {
                "family_id": "family_validator_surface_contract_rows",
                "member_id_key": "contract_row_id",
                "actual_rows": [
                    SimpleNamespace(contract_row_id=contract_row_id)
                    for contract_row_id in validator_surface_contract_row_ids
                ],
                "expected_rows": {
                    f"{family_id}:{contract_field}": {}
                    for family_id in discovered_family_ids
                    for contract_field in required_validator_surface_contract_fields
                },
                "id_attr": "contract_row_id",
            },
            {
                "family_id": "family_probe_surface_contract_rows",
                "member_id_key": "contract_row_id",
                "actual_rows": [
                    SimpleNamespace(contract_row_id=contract_row_id)
                    for contract_row_id in probe_surface_contract_row_ids
                ],
                "expected_rows": {
                    f"{family_id}:{contract_field}": {}
                    for family_id in discovered_family_ids
                    for contract_field in required_probe_surface_contract_fields
                },
                "id_attr": "contract_row_id",
            },
            {
                "family_id": "machine_registry_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": machine_registry_completeness_rows,
                "expected_rows": {
                    completeness_id: {}
                    for completeness_id in EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "machine_registry_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": machine_registry_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {}
                    for row in EXPECTED_MACHINE_REGISTRY_COMPLETENESS_ROWS.values()
                },
                "id_attr": "contract_phrase",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    row_family_projection_by_id = {
        row["family_id"]: row for row in row_family_projection_rows
    }
    payload = {
        STATUS_KEY: status,
        "completeness_family": str(completeness_doc.get("completeness_family") or ""),
        "completeness_version": str(completeness_doc.get("completeness_version") or ""),
        "mapping_entry_file": str(completeness_entry_path.relative_to(repo_root)),
        "mapping_active_file": str(completeness_active_path.relative_to(repo_root)),
        "registry_entry_file": str(registry_entry_path.relative_to(repo_root)),
        "registry_active_file": str(registry_active_path.relative_to(repo_root)),
        "required_descriptor_fields": list(required_descriptor_fields),
        "required_descriptor_field_modes": dict(required_descriptor_field_modes),
        "required_validator_surface_contract_fields": list(
            required_validator_surface_contract_fields
        ),
        "required_validator_surface_contract_values": dict(
            required_validator_surface_contract_values
        ),
        "required_probe_surface_contract_fields": list(
            required_probe_surface_contract_fields
        ),
        "required_probe_surface_contract_values": dict(
            required_probe_surface_contract_values
        ),
        "repo_rel_path_scope_policy": repo_rel_path_scope_policy,
        "repo_rel_path_escape_policy": repo_rel_path_escape_policy,
        "repo_rel_path_role_typing_policy": repo_rel_path_role_typing_policy,
        "repo_rel_path_surface_stem_policy": repo_rel_path_surface_stem_policy,
        "family_surface_stem_binding_policy": family_surface_stem_binding_policy,
        "family_surface_stem_overrides": dict(family_surface_stem_overrides),
        "required_repo_rel_path_patterns": dict(required_repo_rel_path_patterns),
        "family_count": len(family_status_rows),
        "registered_complete_family_count": len(registered_complete_family_ids),
        "registered_complete_family_ids": registered_complete_family_ids,
        "family_status_row_count": len(family_status_rows),
        "expected_family_status_row_count": expected_family_status_row_count,
        "family_status_row_coverage_status": family_status_row_coverage_status,
        "discovered_family_count": len(discovered_family_ids),
        "discovered_family_ids": discovered_family_ids,
        "family_status_row_ids": family_status_row_ids,
        "missing_family_status_row_ids": missing_family_status_row_ids,
        "unexpected_family_status_row_ids": unexpected_family_status_row_ids,
        "family_status_row_identity_projection_status": (
            family_status_row_identity_projection_status
        ),
        "validator_surface_contract_row_count": len(validator_surface_contract_row_ids),
        "expected_family_validator_surface_contract_row_count": (
            len(discovered_family_ids) * len(required_validator_surface_contract_fields)
        ),
        "validator_surface_contract_row_ids": validator_surface_contract_row_ids,
        "missing_validator_surface_contract_row_ids": (
            missing_validator_surface_contract_row_ids
        ),
        "unexpected_validator_surface_contract_row_ids": (
            unexpected_validator_surface_contract_row_ids
        ),
        "validator_surface_contract_row_coverage_status": (
            validator_surface_contract_row_coverage_status
        ),
        "validator_surface_contract_row_identity_projection_status": (
            validator_surface_contract_row_identity_projection_status
        ),
        "probe_surface_contract_row_count": len(probe_surface_contract_row_ids),
        "expected_family_probe_surface_contract_row_count": (
            len(discovered_family_ids) * len(required_probe_surface_contract_fields)
        ),
        "probe_surface_contract_row_ids": probe_surface_contract_row_ids,
        "missing_probe_surface_contract_row_ids": (
            missing_probe_surface_contract_row_ids
        ),
        "unexpected_probe_surface_contract_row_ids": (
            unexpected_probe_surface_contract_row_ids
        ),
        "probe_surface_contract_row_coverage_status": (
            probe_surface_contract_row_coverage_status
        ),
        "probe_surface_contract_row_identity_projection_status": (
            probe_surface_contract_row_identity_projection_status
        ),
        "machine_registry_completeness_row_count": len(machine_registry_completeness_rows),
        **project_root_contract_support_projection(
            prefix="machine_registry_completeness",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "machine_registry_completeness_canonical_row_coverage_status": row_family_projection_by_id[
            "machine_registry_completeness_rows"
        ]["coverage_status"],
        "machine_registry_completeness_canonical_row_identity_projection_status": row_family_projection_by_id[
            "machine_registry_completeness_rows"
        ]["identity_projection_status"],
        "machine_registry_completeness_surface_coverage_status": row_family_projection_by_id[
            "machine_registry_completeness_surface"
        ]["coverage_status"],
        "machine_registry_completeness_surface_identity_projection_status": row_family_projection_by_id[
            "machine_registry_completeness_surface"
        ]["identity_projection_status"],
        "structure_violation_count": len(structure_violations),
        "completeness_violation_count": len(completeness_violations),
        "anchor_violation_count": len(anchor_violations),
        "projected_violation_reason_count": projected_violation_reason_count,
        "expected_projected_violation_reason_count": (
            expected_projected_violation_reason_count
        ),
        "violation_projection_status": violation_projection_status,
        "family_ids": [row["family_id"] for row in family_status_rows],
        "row_family_projection_rows": row_family_projection_rows,
        "machine_registry_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted(machine_registry_completeness_rows, key=lambda item: item.order)
        ],
        "machine_registry_completeness_surface": {
            "rel_path": machine_registry_completeness_surface.rel_path,
            "entry_count": len(machine_registry_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in machine_registry_completeness_surface.rows
            ],
            "extraction_violations": list(
                machine_registry_completeness_surface.extraction_violations
            ),
        },
        "family_status_rows": family_status_rows,
        "structure_violations": structure_violations,
        "completeness_violations": completeness_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
        "error_code": error_code,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
