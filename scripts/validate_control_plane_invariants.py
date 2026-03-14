#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import collect_requirement_rows, requirement_row_keys

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - runtime dependency guard
    Draft202012Validator = None  # type: ignore[assignment]

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_INVARIANT = "IP-CP-INV-001"
PLUGIN_DOC_CONTROL_DEFAULT_REL = "identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml"
PLUGIN_FAILCLOSE_GOVERNANCE_CURRENT_DEFAULT_REL = "identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml"
GITHUB_OFFLOAD_CURRENT_DEFAULT_REL = "identity/protocol/mappings/github-control-plane-offload.current.yaml"
LAYER_TARGETED_GATE_PROFILE_CURRENT_DEFAULT_REL = "identity/protocol/mappings/layer-targeted-gate-profile.current.yaml"
STREAM_DOC_REGISTRY_CURRENT_DEFAULT_REL = "identity/protocol/mappings/stream-doc-registry.current.yaml"
DOC_EVIDENCE_ALLOWLIST_CURRENT_DEFAULT_REL = "identity/protocol/mappings/doc-evidence-allowlist.current.yaml"
CONTRACT_BINDING_CURRENT_DEFAULT_REL = "identity/protocol/mappings/contract-binding.current.yaml"
CONTROL_PLANE_INVARIANTS_CURRENT_DEFAULT_REL = "identity/protocol/mappings/control-plane-invariants.current.yaml"
CONTROL_PLANE_BUDGET_CURRENT_DEFAULT_REL = "identity/protocol/mappings/control-plane-budget.current.yaml"
CONTROL_PLANE_STATUS_CURRENT_DEFAULT_REL = "identity/protocol/mappings/control-plane-status.current.yaml"
INTEGRATION_KIND_RULES = {
    "skill": {
        "protocol_contract_root": "identity/protocol/plugins/skill",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/skills",
    },
    "mcp": {
        "protocol_contract_root": "identity/protocol/plugins/mcp",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/mcp",
    },
    "api": {
        "protocol_contract_root": "identity/protocol/plugins",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/api",
    },
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _mapping_rows(mapping_doc: dict[str, Any]) -> list[str]:
    return requirement_row_keys(mapping_doc)


def _bundle_rows() -> list[str]:
    from required_gate_bundle_runner import BUNDLE_REQUIREMENT_ORDER  # local import for script stability

    return sorted(set(str(x).strip() for x in BUNDLE_REQUIREMENT_ORDER if str(x).strip()))


def _bundle_target_map() -> dict[str, str]:
    from required_gate_bundle_runner import TARGET_NAME_BY_REQUIREMENT  # local import for script stability

    return {
        str(k).strip(): str(v).strip()
        for k, v in TARGET_NAME_BY_REQUIREMENT.items()
        if str(k).strip() and str(v).strip()
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    return [str(x).strip() for x in _as_list(value) if str(x).strip()]


def _mapping_validator_scripts(row: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for raw in _as_str_list(row.get("validator_ids")):
        script = raw.split("::", 1)[0].strip()
        if script:
            out.add(script)
    return out


def _append_violation(violations: list[dict[str, Any]], *, field: str, reason: str, **extra: Any) -> None:
    row = {"field": field, "reason": reason}
    row.update(extra)
    violations.append(row)


def _path_within_root(path_value: str, root_value: str) -> bool:
    norm_path = str(path_value or "").strip().strip("/")
    norm_root = str(root_value or "").strip().strip("/")
    if not norm_path or not norm_root:
        return False
    return norm_path == norm_root or norm_path.startswith(f"{norm_root}/")


def _surface_token_present(repo_root: Path, rel_path: str, token: str) -> tuple[bool, str]:
    path = (repo_root / rel_path).resolve()
    if not path.exists():
        return False, "surface_missing"
    text = _read_text(path)
    return (token in text), ""


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    current_doc = _load_yaml(configured_path)
    if not current_doc:
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _scan_forbidden_versioned_refs(
    *,
    repo_root: Path,
    regex: str,
    surfaces: list[str],
    skip_files: set[Path] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    violations: list[dict[str, Any]] = []
    stale_reasons: list[str] = []
    skip = {p.resolve() for p in (skip_files or set())}
    try:
        pattern = re.compile(regex)
    except re.error:
        stale_reasons.append(f"forbid_versioned_reference_regex_invalid:{regex}")
        return violations, stale_reasons

    hit_files: list[str] = []
    for rel_surface in surfaces:
        surface_path = (repo_root / rel_surface).resolve()
        if not surface_path.exists():
            stale_reasons.append(f"forbid_versioned_reference_surface_missing:{rel_surface}")
            continue
        candidates: list[Path] = []
        if surface_path.is_file():
            candidates = [surface_path]
        elif surface_path.is_dir():
            candidates = [p for p in surface_path.rglob("*") if p.is_file()]
        for candidate in candidates:
            candidate_resolved = candidate.resolve()
            if candidate_resolved in skip:
                continue
            text = _read_text(candidate_resolved)
            if pattern.search(text):
                try:
                    rel_candidate = candidate_resolved.relative_to(repo_root).as_posix()
                except Exception:
                    rel_candidate = str(candidate_resolved)
                hit_files.append(rel_candidate)

    if hit_files:
        uniq_hits = sorted(set(hit_files))
        violations.append(
            {
                "reason": "direct_versioned_reference_detected_on_forbidden_surfaces",
                "regex": regex,
                "surfaces": surfaces,
                "hit_files": uniq_hits,
                "hit_count": len(uniq_hits),
            }
        )
    return violations, stale_reasons


def _validate_mapping_alias_contract(
    *,
    repo_root: Path,
    alias_field: str,
    alias_cfg: dict[str, Any],
    configured_current_file: str,
    expected_active_prefix: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    state = {
        "alias_enabled": False,
        "current_configured_file": configured_current_file,
        "current_path": (repo_root / configured_current_file).resolve(),
        "current_resolved_path": (repo_root / configured_current_file).resolve(),
        "active_file": "",
        "parse_ok": False,
    }
    violations: list[dict[str, Any]] = []
    violation_count = 0

    if not isinstance(alias_cfg, dict) or not alias_cfg:
        return state, violations, violation_count

    state["alias_enabled"] = True
    cfg_current_file = str(alias_cfg.get("current_file", "")).strip()
    if cfg_current_file:
        state["current_configured_file"] = cfg_current_file
    state["current_path"] = (repo_root / str(state["current_configured_file"])).resolve()
    state["current_resolved_path"] = state["current_path"]

    if not str(state["current_configured_file"]).endswith(".current.yaml"):
        violation_count += 1
        violations.append(
            {
                "field": alias_field,
                "reason": "current_file_non_canonical",
                "current_file": state["current_configured_file"],
            }
        )

    active_path, active_file, alias_error = _resolve_current_yaml_alias(
        repo_root, str(state["current_configured_file"])
    )
    state["active_file"] = active_file
    if alias_error:
        violation_count += 1
        violations.append(
            {
                "field": alias_field,
                "reason": alias_error,
                "current_file": state["current_configured_file"],
                "active_file": active_file,
            }
        )
    else:
        state["current_resolved_path"] = active_path
        if active_file and expected_active_prefix and not active_file.startswith(expected_active_prefix):
            violation_count += 1
            violations.append(
                {
                    "field": alias_field,
                    "reason": "active_file_non_canonical",
                    "active_file": active_file,
                }
            )
        if not active_path.exists() or not active_path.is_file():
            violation_count += 1
            violations.append(
                {
                    "field": alias_field,
                    "reason": "active_file_not_found",
                    "active_file": active_file,
                }
            )
        else:
            active_doc = _load_yaml(active_path)
            if not active_doc:
                violation_count += 1
                violations.append(
                    {
                        "field": alias_field,
                        "reason": "active_file_parse_failed",
                        "active_file": active_file,
                    }
                )
            else:
                state["parse_ok"] = True
                required_fields = _as_str_list(alias_cfg.get("required_fields"))
                for field_name in required_fields:
                    value = active_doc.get(field_name)
                    if value in (None, "", [], {}):
                        violation_count += 1
                        violations.append(
                            {
                                "field": alias_field,
                                "reason": "required_field_missing_or_empty",
                                "active_file": active_file,
                                "required_field": field_name,
                            }
                        )
                required_row_fields = _as_str_list(alias_cfg.get("required_row_fields"))
                if required_row_fields:
                    mapping_rows = list(collect_requirement_rows(active_doc).items())
                    if not mapping_rows:
                        violation_count += 1
                        violations.append(
                            {
                                "field": alias_field,
                                "reason": "required_row_fields_mapping_rows_missing",
                                "active_file": active_file,
                            }
                        )
                    else:
                        for requirement_key, row in mapping_rows:
                            for field_name in required_row_fields:
                                value = row.get(field_name)
                                if value in (None, "", [], {}):
                                    violation_count += 1
                                    violations.append(
                                        {
                                            "field": alias_field,
                                            "reason": "required_row_field_missing_or_empty",
                                            "active_file": active_file,
                                            "requirement_key": requirement_key,
                                            "required_row_field": field_name,
                                        }
                                    )

    forbid_cfg = alias_cfg.get("forbid_versioned_reference")
    if isinstance(forbid_cfg, dict):
        ref_regex = str(forbid_cfg.get("regex", "")).strip()
        ref_surfaces = _as_str_list(forbid_cfg.get("surfaces"))
        if not ref_regex:
            violation_count += 1
            violations.append(
                {
                    "field": alias_field,
                    "reason": "forbid_versioned_reference_regex_missing",
                }
            )
        elif not ref_surfaces:
            violation_count += 1
            violations.append(
                {
                    "field": alias_field,
                    "reason": "forbid_versioned_reference_surfaces_missing",
                }
            )
        else:
            skip_files: set[Path] = set()
            resolved_active = (
                (repo_root / str(state["active_file"])).resolve()
                if str(state["active_file"])
                else None
            )
            if resolved_active and resolved_active.exists():
                skip_files.add(resolved_active)
            ref_violations, ref_stale = _scan_forbidden_versioned_refs(
                repo_root=repo_root,
                regex=ref_regex,
                surfaces=ref_surfaces,
                skip_files=skip_files,
            )
            for reason in ref_stale:
                violation_count += 1
                violations.append(
                    {
                        "field": alias_field,
                        "reason": reason,
                        "regex": ref_regex,
                        "surfaces": ref_surfaces,
                    }
                )
            for row in ref_violations:
                hit_count = int(row.get("hit_count", 1))
                violation_count += hit_count
                violations.append(
                    {
                        "field": alias_field,
                        "reason": str(row.get("reason", "")),
                        "regex": ref_regex,
                        "surfaces": ref_surfaces,
                        "hit_files": row.get("hit_files", []),
                        "hit_count": row.get("hit_count", 0),
                    }
                )

    return state, violations, violation_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-plane invariants (bundle/mapping parity + fail-close plugin wiring).")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--invariants-file",
        default=CONTROL_PLANE_INVARIANTS_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--contract-mapping",
        default=CONTRACT_BINDING_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--plugin-governance-file",
        default=PLUGIN_FAILCLOSE_GOVERNANCE_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--plugin-doc-control-file",
        default=PLUGIN_DOC_CONTROL_DEFAULT_REL,
    )
    parser.add_argument(
        "--github-offload-current-file",
        default=GITHUB_OFFLOAD_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--layer-gate-profile-current-file",
        default=LAYER_TARGETED_GATE_PROFILE_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--stream-doc-registry-current-file",
        default=STREAM_DOC_REGISTRY_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--doc-evidence-allowlist-current-file",
        default=DOC_EVIDENCE_ALLOWLIST_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--control-plane-budget-current-file",
        default=CONTROL_PLANE_BUDGET_CURRENT_DEFAULT_REL,
    )
    parser.add_argument(
        "--control-plane-status-current-file",
        default=CONTROL_PLANE_STATUS_CURRENT_DEFAULT_REL,
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    invariants_configured_file = str(args.invariants_file)
    invariants_entry_path = (repo_root / invariants_configured_file).resolve()
    invariants_path, invariants_active_file, invariants_alias_error = _resolve_current_yaml_alias(
        repo_root,
        invariants_configured_file,
    )
    contract_mapping_configured_file = str(args.contract_mapping)
    contract_mapping_entry_path = (repo_root / contract_mapping_configured_file).resolve()
    mapping_path, contract_mapping_active_file, contract_mapping_alias_error = _resolve_current_yaml_alias(
        repo_root,
        contract_mapping_configured_file,
    )
    plugin_governance_configured_file = str(args.plugin_governance_file)
    plugin_governance_entry_path = (repo_root / plugin_governance_configured_file).resolve()
    plugin_governance_path, plugin_governance_active_file, plugin_governance_alias_error = _resolve_current_yaml_alias(
        repo_root,
        plugin_governance_configured_file,
    )
    plugin_doc_control_path = (repo_root / str(args.plugin_doc_control_file)).resolve()
    github_offload_current_path = (repo_root / str(args.github_offload_current_file)).resolve()
    plugin_governance_alias_enabled = plugin_governance_entry_path.name.endswith(".current.yaml")
    plugin_governance_violation_count = 0
    plugin_doc_control_resolved_path = plugin_doc_control_path
    plugin_doc_control_active_file = ""
    github_offload_current_configured_file = str(args.github_offload_current_file)
    github_offload_current_resolved_path = github_offload_current_path
    github_offload_active_file = ""
    github_offload_active_path: Path | None = None
    github_offload_alias_enabled = False
    github_offload_parse_ok = False
    github_offload_violation_count = 0
    layer_gate_profile_current_configured_file = str(args.layer_gate_profile_current_file)
    layer_gate_profile_current_path = (repo_root / layer_gate_profile_current_configured_file).resolve()
    layer_gate_profile_current_resolved_path = layer_gate_profile_current_path
    layer_gate_profile_active_file = ""
    layer_gate_profile_alias_enabled = False
    layer_gate_profile_parse_ok = False
    layer_gate_profile_violation_count = 0
    stream_doc_registry_current_configured_file = str(args.stream_doc_registry_current_file)
    stream_doc_registry_current_path = (repo_root / stream_doc_registry_current_configured_file).resolve()
    stream_doc_registry_current_resolved_path = stream_doc_registry_current_path
    stream_doc_registry_active_file = ""
    stream_doc_registry_alias_enabled = False
    stream_doc_registry_parse_ok = False
    stream_doc_registry_violation_count = 0
    doc_evidence_allowlist_current_configured_file = str(args.doc_evidence_allowlist_current_file)
    doc_evidence_allowlist_current_path = (repo_root / doc_evidence_allowlist_current_configured_file).resolve()
    doc_evidence_allowlist_current_resolved_path = doc_evidence_allowlist_current_path
    doc_evidence_allowlist_active_file = ""
    doc_evidence_allowlist_alias_enabled = False
    doc_evidence_allowlist_parse_ok = False
    doc_evidence_allowlist_violation_count = 0
    control_plane_budget_current_configured_file = str(args.control_plane_budget_current_file)
    control_plane_budget_current_path = (repo_root / control_plane_budget_current_configured_file).resolve()
    control_plane_budget_current_resolved_path = control_plane_budget_current_path
    control_plane_budget_active_file = ""
    control_plane_budget_alias_enabled = False
    control_plane_budget_parse_ok = False
    control_plane_budget_violation_count = 0
    control_plane_status_current_configured_file = str(args.control_plane_status_current_file)
    control_plane_status_current_path = (repo_root / control_plane_status_current_configured_file).resolve()
    control_plane_status_current_resolved_path = control_plane_status_current_path
    control_plane_status_active_file = ""
    control_plane_status_alias_enabled = False
    control_plane_status_parse_ok = False
    control_plane_status_violation_count = 0
    plugin_control_plane_alias_enabled = False
    plugin_control_plane_alias_parse_ok = False
    plugin_control_plane_alias_violation_count = 0
    plugin_control_plane_alias_current_files: dict[str, str] = {}
    plugin_control_plane_alias_active_files: dict[str, str] = {}

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []

    if not invariants_entry_path.exists():
        stale_reasons.append(f"invariants_entry_file_missing:{invariants_entry_path}")
    if invariants_alias_error:
        stale_reasons.append(f"invariants_alias_error:{invariants_alias_error}")
    if not invariants_path.exists():
        stale_reasons.append(f"invariants_file_missing:{invariants_path}")
    if not contract_mapping_entry_path.exists():
        stale_reasons.append(f"contract_mapping_entry_missing:{contract_mapping_entry_path}")
    if contract_mapping_alias_error:
        stale_reasons.append(f"contract_mapping_alias_error:{contract_mapping_alias_error}")
    if not mapping_path.exists():
        stale_reasons.append(f"contract_mapping_missing:{mapping_path}")
    if not plugin_governance_entry_path.exists():
        stale_reasons.append(f"plugin_governance_entry_file_missing:{plugin_governance_entry_path}")
    if plugin_governance_alias_error:
        stale_reasons.append(f"plugin_governance_alias_error:{plugin_governance_alias_error}")
        plugin_governance_violation_count += 1
        _append_violation(
            violations,
            field="plugin_governance_alias",
            reason=plugin_governance_alias_error,
            plugin_governance_file=plugin_governance_configured_file,
            active_file=plugin_governance_active_file,
        )
    if not plugin_governance_path.exists():
        stale_reasons.append(f"plugin_governance_file_missing:{plugin_governance_path}")
    if not plugin_doc_control_path.exists():
        stale_reasons.append(f"plugin_doc_control_file_missing:{plugin_doc_control_path}")

    missing_rows: list[str] = []
    extra_rows: list[str] = []
    mapping_doc: dict[str, Any] = {}
    contract_binding_meta_row_count = -1
    contract_binding_actual_row_count = 0
    contract_binding_row_count_match = False
    bundle_rows = _bundle_rows()
    bundle_target_map = _bundle_target_map()
    mode = ""
    baseline_missing_rows = -1
    reduction_plan_file = ""
    reduction_plan_status = "SKIPPED_NOT_REQUIRED"
    reduction_plan_target_zero = False
    reduction_plan_targets: list[int] = []
    contract_binding_alias_enabled = contract_mapping_entry_path.name.endswith(".current.yaml")
    contract_binding_current_configured_file = contract_mapping_configured_file
    contract_binding_current_path = contract_mapping_entry_path
    contract_binding_current_resolved_path = mapping_path
    contract_binding_active_file = contract_mapping_active_file
    contract_binding_parse_ok = False
    contract_binding_violation_count = 0

    if invariants_path.exists() and mapping_path.exists():
        inv_doc = _load_yaml(invariants_path)
        invariants = inv_doc.get("invariants") or {}
        parity_cfg = (invariants.get("bundle_mapping_parity") or {}) if isinstance(invariants, dict) else {}
        contract_binding_alias_cfg = (
            (invariants.get("contract_binding_alias") or {}) if isinstance(invariants, dict) else {}
        )
        contract_binding_state, contract_binding_violations, contract_binding_violation_count = _validate_mapping_alias_contract(
            repo_root=repo_root,
            alias_field="contract_binding_alias",
            alias_cfg=contract_binding_alias_cfg if isinstance(contract_binding_alias_cfg, dict) else {},
            configured_current_file=contract_binding_current_configured_file,
            expected_active_prefix="identity/protocol/mappings/contract-binding.v",
        )
        contract_binding_alias_enabled = bool(contract_binding_state.get("alias_enabled", False))
        contract_binding_current_configured_file = str(contract_binding_state.get("current_configured_file", ""))
        contract_binding_current_path = Path(contract_binding_state.get("current_path", contract_binding_current_path))
        contract_binding_current_resolved_path = Path(
            contract_binding_state.get("current_resolved_path", contract_binding_current_resolved_path)
        )
        contract_binding_active_file = str(contract_binding_state.get("active_file", contract_mapping_active_file))
        contract_binding_parse_ok = bool(contract_binding_state.get("parse_ok", False))
        contract_mapping_active_file = contract_binding_active_file
        mapping_path = contract_binding_current_resolved_path
        for row in contract_binding_violations:
            violations.append(row)

        github_offload_cfg = (
            (invariants.get("github_control_plane_offload_alias") or {}) if isinstance(invariants, dict) else {}
        )
        if isinstance(github_offload_cfg, dict) and github_offload_cfg:
            github_offload_alias_enabled = True
            configured_current_file = str(github_offload_cfg.get("current_file", "")).strip()
            if configured_current_file:
                github_offload_current_configured_file = configured_current_file
                github_offload_current_path = (repo_root / configured_current_file).resolve()
                github_offload_current_resolved_path = github_offload_current_path
            if not github_offload_current_configured_file.endswith(".current.yaml"):
                github_offload_violation_count += 1
                _append_violation(
                    violations,
                    field="github_control_plane_offload_alias",
                    reason="current_file_non_canonical",
                    current_file=github_offload_current_configured_file,
                )

            if not github_offload_current_path.exists() or not github_offload_current_path.is_file():
                github_offload_violation_count += 1
                _append_violation(
                    violations,
                    field="github_control_plane_offload_alias",
                    reason="current_file_missing",
                    current_file=github_offload_current_configured_file,
                )
            else:
                current_doc = _load_yaml(github_offload_current_path)
                if not current_doc:
                    github_offload_violation_count += 1
                    _append_violation(
                        violations,
                        field="github_control_plane_offload_alias",
                        reason="current_file_parse_failed",
                        current_file=github_offload_current_configured_file,
                    )
                else:
                    github_offload_active_file = str(current_doc.get("active_file", "")).strip()
                    if not github_offload_active_file:
                        github_offload_violation_count += 1
                        _append_violation(
                            violations,
                            field="github_control_plane_offload_alias",
                            reason="active_file_missing",
                            current_file=github_offload_current_configured_file,
                        )
                    else:
                        if not github_offload_active_file.startswith(
                            "identity/protocol/mappings/github-control-plane-offload.v"
                        ):
                            github_offload_violation_count += 1
                            _append_violation(
                                violations,
                                field="github_control_plane_offload_alias",
                                reason="active_file_non_canonical",
                                active_file=github_offload_active_file,
                            )
                        active_path = (repo_root / github_offload_active_file).resolve()
                        github_offload_active_path = active_path
                        github_offload_current_resolved_path = active_path
                        if not active_path.exists() or not active_path.is_file():
                            github_offload_violation_count += 1
                            _append_violation(
                                violations,
                                field="github_control_plane_offload_alias",
                                reason="active_file_not_found",
                                current_file=github_offload_current_configured_file,
                                active_file=github_offload_active_file,
                            )
                        else:
                            active_doc = _load_yaml(active_path)
                            if not active_doc:
                                github_offload_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="github_control_plane_offload_alias",
                                    reason="active_file_parse_failed",
                                    active_file=github_offload_active_file,
                                )
                            else:
                                github_offload_parse_ok = True
                                required_fields = _as_str_list(github_offload_cfg.get("required_fields"))
                                for field_name in required_fields:
                                    value = active_doc.get(field_name)
                                    if value in (None, "", [], {}):
                                        github_offload_violation_count += 1
                                        _append_violation(
                                            violations,
                                            field="github_control_plane_offload_alias",
                                            reason="required_field_missing_or_empty",
                                            active_file=github_offload_active_file,
                                            required_field=field_name,
                                        )

                                required_control_ids = set(
                                    _as_str_list(github_offload_cfg.get("required_control_ids"))
                                )
                                observed_control_ids = {
                                    str(row.get("control_id", "")).strip()
                                    for row in _as_list(active_doc.get("platform_offload_controls"))
                                    if isinstance(row, dict)
                                }
                                missing_control_ids = sorted(
                                    x for x in required_control_ids if x and x not in observed_control_ids
                                )
                                if missing_control_ids:
                                    github_offload_violation_count += len(missing_control_ids)
                                    _append_violation(
                                        violations,
                                        field="github_control_plane_offload_alias",
                                        reason="required_control_ids_missing",
                                        active_file=github_offload_active_file,
                                        missing_control_ids=missing_control_ids,
                                    )

                                required_requirement_keys = set(
                                    _as_str_list(github_offload_cfg.get("required_retained_requirement_keys"))
                                )
                                observed_requirement_keys = {
                                    str(row.get("requirement_key", "")).strip()
                                    for row in _as_list(active_doc.get("repo_retained_semantic_contracts"))
                                    if isinstance(row, dict)
                                }
                                missing_requirement_keys = sorted(
                                    x
                                    for x in required_requirement_keys
                                    if x and x not in observed_requirement_keys
                                )
                                if missing_requirement_keys:
                                    github_offload_violation_count += len(missing_requirement_keys)
                                    _append_violation(
                                        violations,
                                        field="github_control_plane_offload_alias",
                                        reason="required_retained_requirement_keys_missing",
                                        active_file=github_offload_active_file,
                                        missing_requirement_keys=missing_requirement_keys,
                                    )

            forbid_cfg = github_offload_cfg.get("forbid_versioned_reference")
            if isinstance(forbid_cfg, dict):
                ref_regex = str(forbid_cfg.get("regex", "")).strip()
                ref_surfaces = _as_str_list(forbid_cfg.get("surfaces"))
                if not ref_regex:
                    github_offload_violation_count += 1
                    _append_violation(
                        violations,
                        field="github_control_plane_offload_alias",
                        reason="forbid_versioned_reference_regex_missing",
                    )
                elif not ref_surfaces:
                    github_offload_violation_count += 1
                    _append_violation(
                        violations,
                        field="github_control_plane_offload_alias",
                        reason="forbid_versioned_reference_surfaces_missing",
                    )
                else:
                    try:
                        ref_pattern = re.compile(ref_regex)
                    except re.error:
                        github_offload_violation_count += 1
                        _append_violation(
                            violations,
                            field="github_control_plane_offload_alias",
                            reason="forbid_versioned_reference_regex_invalid",
                            regex=ref_regex,
                        )
                    else:
                        versioned_hits: list[str] = []
                        for rel_surface in ref_surfaces:
                            surface_path = (repo_root / rel_surface).resolve()
                            if not surface_path.exists():
                                github_offload_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="github_control_plane_offload_alias",
                                    reason="forbid_versioned_reference_surface_missing",
                                    surface=rel_surface,
                                )
                                continue
                            candidates: list[Path] = []
                            if surface_path.is_file():
                                candidates = [surface_path]
                            elif surface_path.is_dir():
                                candidates = [p for p in surface_path.rglob("*") if p.is_file()]
                            for candidate in candidates:
                                if github_offload_active_path and candidate.resolve() == github_offload_active_path.resolve():
                                    continue
                                text = _read_text(candidate)
                                if ref_pattern.search(text):
                                    try:
                                        rel_candidate = candidate.relative_to(repo_root).as_posix()
                                    except Exception:
                                        rel_candidate = str(candidate)
                                    versioned_hits.append(rel_candidate)
                        if versioned_hits:
                            uniq_hits = sorted(set(versioned_hits))
                            github_offload_violation_count += len(uniq_hits)
                            _append_violation(
                                violations,
                                field="github_control_plane_offload_alias",
                                reason="direct_versioned_reference_detected_on_forbidden_surfaces",
                                regex=ref_regex,
                                surfaces=ref_surfaces,
                                hit_files=uniq_hits,
                                hit_count=len(uniq_hits),
                            )

        layer_profile_alias_cfg = (
            (invariants.get("layer_targeted_gate_profile_alias") or {}) if isinstance(invariants, dict) else {}
        )
        if isinstance(layer_profile_alias_cfg, dict) and layer_profile_alias_cfg:
            layer_gate_profile_alias_enabled = True
            configured_current_file = str(layer_profile_alias_cfg.get("current_file", "")).strip()
            if configured_current_file:
                layer_gate_profile_current_configured_file = configured_current_file
                layer_gate_profile_current_path = (repo_root / configured_current_file).resolve()
                layer_gate_profile_current_resolved_path = layer_gate_profile_current_path
            if not layer_gate_profile_current_configured_file.endswith(".current.yaml"):
                layer_gate_profile_violation_count += 1
                _append_violation(
                    violations,
                    field="layer_targeted_gate_profile_alias",
                    reason="current_file_non_canonical",
                    current_file=layer_gate_profile_current_configured_file,
                )

            layer_profile_active_path, layer_profile_active_file, layer_profile_alias_error = _resolve_current_yaml_alias(
                repo_root,
                layer_gate_profile_current_configured_file,
            )
            layer_gate_profile_active_file = layer_profile_active_file
            if layer_profile_alias_error:
                layer_gate_profile_violation_count += 1
                _append_violation(
                    violations,
                    field="layer_targeted_gate_profile_alias",
                    reason=layer_profile_alias_error,
                    current_file=layer_gate_profile_current_configured_file,
                    active_file=layer_profile_active_file,
                )
            else:
                layer_gate_profile_current_resolved_path = layer_profile_active_path
                if layer_gate_profile_active_file and not layer_gate_profile_active_file.startswith(
                    "identity/protocol/mappings/layer-targeted-gate-profile.v"
                ):
                    layer_gate_profile_violation_count += 1
                    _append_violation(
                        violations,
                        field="layer_targeted_gate_profile_alias",
                        reason="active_file_non_canonical",
                        active_file=layer_gate_profile_active_file,
                    )
                if not layer_profile_active_path.exists() or not layer_profile_active_path.is_file():
                    layer_gate_profile_violation_count += 1
                    _append_violation(
                        violations,
                        field="layer_targeted_gate_profile_alias",
                        reason="active_file_not_found",
                        active_file=layer_gate_profile_active_file,
                    )
                else:
                    active_doc = _load_yaml(layer_profile_active_path)
                    if not active_doc:
                        layer_gate_profile_violation_count += 1
                        _append_violation(
                            violations,
                            field="layer_targeted_gate_profile_alias",
                            reason="active_file_parse_failed",
                            active_file=layer_gate_profile_active_file,
                        )
                    else:
                        layer_gate_profile_parse_ok = True
                        required_fields = _as_str_list(layer_profile_alias_cfg.get("required_fields"))
                        for field_name in required_fields:
                            value = active_doc.get(field_name)
                            if value in (None, "", [], {}):
                                layer_gate_profile_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="layer_targeted_gate_profile_alias",
                                    reason="required_field_missing_or_empty",
                                    active_file=layer_gate_profile_active_file,
                                    required_field=field_name,
                                )

            forbid_cfg = layer_profile_alias_cfg.get("forbid_versioned_reference")
            if isinstance(forbid_cfg, dict):
                ref_regex = str(forbid_cfg.get("regex", "")).strip()
                ref_surfaces = _as_str_list(forbid_cfg.get("surfaces"))
                if not ref_regex:
                    layer_gate_profile_violation_count += 1
                    _append_violation(
                        violations,
                        field="layer_targeted_gate_profile_alias",
                        reason="forbid_versioned_reference_regex_missing",
                    )
                elif not ref_surfaces:
                    layer_gate_profile_violation_count += 1
                    _append_violation(
                        violations,
                        field="layer_targeted_gate_profile_alias",
                        reason="forbid_versioned_reference_surfaces_missing",
                    )
                else:
                    skip_files: set[Path] = set()
                    resolved_active = (repo_root / layer_gate_profile_active_file).resolve() if layer_gate_profile_active_file else None
                    if resolved_active and resolved_active.exists():
                        skip_files.add(resolved_active)
                    ref_violations, ref_stale = _scan_forbidden_versioned_refs(
                        repo_root=repo_root,
                        regex=ref_regex,
                        surfaces=ref_surfaces,
                        skip_files=skip_files,
                    )
                    if ref_stale:
                        layer_gate_profile_violation_count += len(ref_stale)
                        for reason in ref_stale:
                            _append_violation(
                                violations,
                                field="layer_targeted_gate_profile_alias",
                                reason=reason,
                                regex=ref_regex,
                                surfaces=ref_surfaces,
                            )
                    if ref_violations:
                        for row in ref_violations:
                            layer_gate_profile_violation_count += int(row.get("hit_count", 1))
                            _append_violation(
                                violations,
                                field="layer_targeted_gate_profile_alias",
                                reason=str(row.get("reason", "")),
                                regex=ref_regex,
                                surfaces=ref_surfaces,
                                hit_files=row.get("hit_files", []),
                                hit_count=row.get("hit_count", 0),
                            )

        stream_doc_registry_alias_cfg = (
            (invariants.get("stream_doc_registry_alias") or {}) if isinstance(invariants, dict) else {}
        )
        stream_doc_state, stream_doc_violations, stream_doc_violation_count = _validate_mapping_alias_contract(
            repo_root=repo_root,
            alias_field="stream_doc_registry_alias",
            alias_cfg=stream_doc_registry_alias_cfg if isinstance(stream_doc_registry_alias_cfg, dict) else {},
            configured_current_file=stream_doc_registry_current_configured_file,
            expected_active_prefix="identity/protocol/mappings/stream-doc-registry.v",
        )
        stream_doc_registry_alias_enabled = bool(stream_doc_state.get("alias_enabled", False))
        stream_doc_registry_current_configured_file = str(stream_doc_state.get("current_configured_file", ""))
        stream_doc_registry_current_path = Path(stream_doc_state.get("current_path", stream_doc_registry_current_path))
        stream_doc_registry_current_resolved_path = Path(
            stream_doc_state.get("current_resolved_path", stream_doc_registry_current_resolved_path)
        )
        stream_doc_registry_active_file = str(stream_doc_state.get("active_file", ""))
        stream_doc_registry_parse_ok = bool(stream_doc_state.get("parse_ok", False))
        stream_doc_registry_violation_count = stream_doc_violation_count
        for row in stream_doc_violations:
            violations.append(row)

        doc_evidence_allowlist_alias_cfg = (
            (invariants.get("doc_evidence_allowlist_alias") or {}) if isinstance(invariants, dict) else {}
        )
        doc_allow_state, doc_allow_violations, doc_allow_violation_count = _validate_mapping_alias_contract(
            repo_root=repo_root,
            alias_field="doc_evidence_allowlist_alias",
            alias_cfg=doc_evidence_allowlist_alias_cfg if isinstance(doc_evidence_allowlist_alias_cfg, dict) else {},
            configured_current_file=doc_evidence_allowlist_current_configured_file,
            expected_active_prefix="identity/protocol/mappings/doc-evidence-allowlist.v",
        )
        doc_evidence_allowlist_alias_enabled = bool(doc_allow_state.get("alias_enabled", False))
        doc_evidence_allowlist_current_configured_file = str(doc_allow_state.get("current_configured_file", ""))
        doc_evidence_allowlist_current_path = Path(doc_allow_state.get("current_path", doc_evidence_allowlist_current_path))
        doc_evidence_allowlist_current_resolved_path = Path(
            doc_allow_state.get("current_resolved_path", doc_evidence_allowlist_current_resolved_path)
        )
        doc_evidence_allowlist_active_file = str(doc_allow_state.get("active_file", ""))
        doc_evidence_allowlist_parse_ok = bool(doc_allow_state.get("parse_ok", False))
        doc_evidence_allowlist_violation_count = doc_allow_violation_count
        for row in doc_allow_violations:
            violations.append(row)

        control_plane_budget_alias_cfg = (
            (invariants.get("control_plane_budget_alias") or {}) if isinstance(invariants, dict) else {}
        )
        budget_state, budget_violations, budget_violation_count = _validate_mapping_alias_contract(
            repo_root=repo_root,
            alias_field="control_plane_budget_alias",
            alias_cfg=control_plane_budget_alias_cfg if isinstance(control_plane_budget_alias_cfg, dict) else {},
            configured_current_file=control_plane_budget_current_configured_file,
            expected_active_prefix="identity/protocol/mappings/control-plane-budget.v",
        )
        control_plane_budget_alias_enabled = bool(budget_state.get("alias_enabled", False))
        control_plane_budget_current_configured_file = str(budget_state.get("current_configured_file", ""))
        control_plane_budget_current_path = Path(
            budget_state.get("current_path", control_plane_budget_current_path)
        )
        control_plane_budget_current_resolved_path = Path(
            budget_state.get("current_resolved_path", control_plane_budget_current_resolved_path)
        )
        control_plane_budget_active_file = str(budget_state.get("active_file", ""))
        control_plane_budget_parse_ok = bool(budget_state.get("parse_ok", False))
        control_plane_budget_violation_count = budget_violation_count
        for row in budget_violations:
            violations.append(row)

        control_plane_status_alias_cfg = (
            (invariants.get("control_plane_status_alias") or {}) if isinstance(invariants, dict) else {}
        )
        status_state, status_violations, status_violation_count = _validate_mapping_alias_contract(
            repo_root=repo_root,
            alias_field="control_plane_status_alias",
            alias_cfg=control_plane_status_alias_cfg if isinstance(control_plane_status_alias_cfg, dict) else {},
            configured_current_file=control_plane_status_current_configured_file,
            expected_active_prefix="identity/protocol/mappings/control-plane-status.v",
        )
        control_plane_status_alias_enabled = bool(status_state.get("alias_enabled", False))
        control_plane_status_current_configured_file = str(status_state.get("current_configured_file", ""))
        control_plane_status_current_path = Path(
            status_state.get("current_path", control_plane_status_current_path)
        )
        control_plane_status_current_resolved_path = Path(
            status_state.get("current_resolved_path", control_plane_status_current_resolved_path)
        )
        control_plane_status_active_file = str(status_state.get("active_file", ""))
        control_plane_status_parse_ok = bool(status_state.get("parse_ok", False))
        control_plane_status_violation_count = status_violation_count
        for row in status_violations:
            violations.append(row)

        plugin_alias_cfg = (invariants.get("plugin_control_plane_alias") or {}) if isinstance(invariants, dict) else {}
        if isinstance(plugin_alias_cfg, dict) and plugin_alias_cfg:
            plugin_control_plane_alias_enabled = True
            alias_rows = {
                "plugin_registry_current_file": (
                    str(plugin_alias_cfg.get("plugin_registry_current_file", "")).strip(),
                    "identity/protocol/plugins/PLUGIN_REGISTRY.v",
                ),
                "provider_profiles_current_file": (
                    str(plugin_alias_cfg.get("provider_profiles_current_file", "")).strip(),
                    "identity/protocol/plugins/PROVIDER_PROFILES.v",
                ),
                "failclose_governance_current_file": (
                    str(plugin_alias_cfg.get("failclose_governance_current_file", "")).strip(),
                    "identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v",
                ),
                "plugin_doc_control_current_file": (
                    str(plugin_alias_cfg.get("plugin_doc_control_current_file", "")).strip(),
                    "identity/protocol/plugins/PLUGIN_DOC_CONTROL.v",
                ),
            }
            alias_resolved_ok = True
            for alias_key, (current_file, active_prefix) in alias_rows.items():
                plugin_control_plane_alias_current_files[alias_key] = current_file
                if not current_file:
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="current_file_missing",
                        alias_key=alias_key,
                    )
                    continue
                if not current_file.endswith(".current.yaml"):
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="current_file_non_canonical",
                        alias_key=alias_key,
                        current_file=current_file,
                    )
                resolved_path, active_file, alias_error = _resolve_current_yaml_alias(repo_root, current_file)
                plugin_control_plane_alias_active_files[alias_key] = active_file
                if alias_error:
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason=alias_error,
                        alias_key=alias_key,
                        current_file=current_file,
                        active_file=active_file,
                    )
                    continue
                if active_file and not active_file.startswith(active_prefix):
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="active_file_non_canonical",
                        alias_key=alias_key,
                        active_file=active_file,
                    )
                if not resolved_path.exists() or not resolved_path.is_file():
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="active_file_not_found",
                        alias_key=alias_key,
                        active_file=active_file,
                    )

            forbid_cfg = plugin_alias_cfg.get("forbid_versioned_reference")
            if isinstance(forbid_cfg, dict):
                ref_regex = str(forbid_cfg.get("regex", "")).strip()
                ref_surfaces = _as_str_list(forbid_cfg.get("surfaces"))
                if not ref_regex:
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="forbid_versioned_reference_regex_missing",
                    )
                elif not ref_surfaces:
                    alias_resolved_ok = False
                    plugin_control_plane_alias_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_control_plane_alias",
                        reason="forbid_versioned_reference_surfaces_missing",
                    )
                else:
                    ref_violations, ref_stale = _scan_forbidden_versioned_refs(
                        repo_root=repo_root,
                        regex=ref_regex,
                        surfaces=ref_surfaces,
                    )
                    if ref_stale:
                        alias_resolved_ok = False
                        plugin_control_plane_alias_violation_count += len(ref_stale)
                        for reason in ref_stale:
                            _append_violation(
                                violations,
                                field="plugin_control_plane_alias",
                                reason=reason,
                                regex=ref_regex,
                                surfaces=ref_surfaces,
                            )
                    if ref_violations:
                        alias_resolved_ok = False
                        for row in ref_violations:
                            plugin_control_plane_alias_violation_count += int(row.get("hit_count", 1))
                            _append_violation(
                                violations,
                                field="plugin_control_plane_alias",
                                reason=str(row.get("reason", "")),
                                regex=ref_regex,
                                surfaces=ref_surfaces,
                                hit_files=row.get("hit_files", []),
                                hit_count=row.get("hit_count", 0),
                            )

            plugin_control_plane_alias_parse_ok = alias_resolved_ok and bool(alias_rows)

        mode = str(parity_cfg.get("mode", "")).strip().lower() or "freeze"
        baseline_missing_rows = int(parity_cfg.get("baseline_missing_rows", -1))
        reduction_plan_file = str(parity_cfg.get("reduction_plan_file", "")).strip()

        mapping_doc = _load_yaml(mapping_path)
        mapping_rows = _mapping_rows(mapping_doc)
        contract_binding_actual_row_count = len(mapping_rows)
        meta_doc = mapping_doc.get("_meta")
        if isinstance(meta_doc, dict):
            raw_meta_count = meta_doc.get("row_count")
            if raw_meta_count in (None, ""):
                contract_binding_violation_count += 1
                _append_violation(
                    violations,
                    field="contract_binding_row_count",
                    reason="meta_row_count_missing",
                    actual_row_count=contract_binding_actual_row_count,
                )
            else:
                try:
                    contract_binding_meta_row_count = int(raw_meta_count)
                except Exception:
                    contract_binding_violation_count += 1
                    _append_violation(
                        violations,
                        field="contract_binding_row_count",
                        reason="meta_row_count_not_integer",
                        meta_row_count=raw_meta_count,
                        actual_row_count=contract_binding_actual_row_count,
                    )
                else:
                    contract_binding_row_count_match = contract_binding_meta_row_count == contract_binding_actual_row_count
                    if not contract_binding_row_count_match:
                        contract_binding_violation_count += 1
                        _append_violation(
                            violations,
                            field="contract_binding_row_count",
                            reason="meta_row_count_mismatch",
                            meta_row_count=contract_binding_meta_row_count,
                            actual_row_count=contract_binding_actual_row_count,
                        )
        else:
            contract_binding_violation_count += 1
            _append_violation(
                violations,
                field="contract_binding_row_count",
                reason="meta_section_missing",
                actual_row_count=contract_binding_actual_row_count,
            )
        missing_rows = sorted(x for x in mapping_rows if x not in bundle_rows)
        extra_rows = sorted(x for x in bundle_rows if x not in mapping_rows)

        if extra_rows:
            _append_violation(
                violations,
                field="bundle_rows_not_in_mapping",
                reason="bundle_row_without_mapping",
                rows=extra_rows,
            )

        if mode == "strict":
            if missing_rows:
                _append_violation(
                    violations,
                    field="mapping_rows_missing_in_bundle",
                    reason="bundle_mapping_parity_strict_violation",
                    mode=mode,
                    missing_rows=missing_rows,
                    missing_count=len(missing_rows),
                )
        elif mode == "freeze":
            if baseline_missing_rows < 0:
                _append_violation(
                    violations,
                    field="bundle_mapping_parity_baseline",
                    reason="freeze_mode_baseline_missing",
                    mode=mode,
                )
            elif len(missing_rows) > baseline_missing_rows:
                _append_violation(
                    violations,
                    field="mapping_rows_missing_in_bundle",
                    reason="bundle_mapping_gap_growth_in_freeze_mode",
                    mode=mode,
                    missing_count=len(missing_rows),
                    baseline_missing_rows=baseline_missing_rows,
                    missing_rows=missing_rows,
                )
            if baseline_missing_rows > 0:
                if not reduction_plan_file:
                    _append_violation(
                        violations,
                        field="bundle_mapping_parity_reduction_plan",
                        reason="reduction_plan_file_missing_for_freeze_debt",
                        baseline_missing_rows=baseline_missing_rows,
                    )
                else:
                    plan_path = (repo_root / reduction_plan_file).resolve()
                    if not plan_path.exists():
                        _append_violation(
                            violations,
                            field="bundle_mapping_parity_reduction_plan",
                            reason="reduction_plan_file_not_found",
                            reduction_plan_file=reduction_plan_file,
                        )
                    else:
                        plan_doc = _load_yaml(plan_path)
                        plan_baseline = int(plan_doc.get("baseline_missing_rows", -1))
                        milestones = _as_list(plan_doc.get("milestones"))
                        reduction_plan_targets = []
                        for row in milestones:
                            if not isinstance(row, dict):
                                continue
                            try:
                                target = int(row.get("target_max_missing_rows", -1))
                            except Exception:
                                continue
                            if target >= 0:
                                reduction_plan_targets.append(target)
                        reduction_plan_target_zero = any(t == 0 for t in reduction_plan_targets)
                        if plan_baseline != baseline_missing_rows:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_baseline_mismatch",
                                baseline_missing_rows=baseline_missing_rows,
                                plan_baseline_missing_rows=plan_baseline,
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not reduction_plan_targets:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_targets_missing",
                                reduction_plan_file=reduction_plan_file,
                            )
                        if reduction_plan_targets and min(reduction_plan_targets) >= baseline_missing_rows:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_no_strict_reduction_target",
                                baseline_missing_rows=baseline_missing_rows,
                                reduction_plan_targets=sorted(reduction_plan_targets),
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not reduction_plan_target_zero:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_missing_zero_target",
                                reduction_plan_targets=sorted(reduction_plan_targets),
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not any(v.get("field") == "bundle_mapping_parity_reduction_plan" for v in violations):
                            reduction_plan_status = "PASS_REQUIRED"
                        else:
                            reduction_plan_status = STATUS_FAIL_REQUIRED
            else:
                reduction_plan_status = "SKIPPED_NOT_REQUIRED"
        else:
            _append_violation(
                violations,
                field="bundle_mapping_parity_mode",
                reason="invalid_mode",
                mode=mode,
            )

    plugin_profile_count = 0
    plugin_wiring_violation_count = 0
    unique_egress_violation_count = 0
    bundle_entry_violation_count = 0
    prompt_binding_violation_count = 0
    plugin_readability_violation_count = 0
    plugin_doc_control_parse_ok = False
    registry_fail_close_plugin_ids: set[str] = set()
    governance_plugin_ids: set[str] = set()
    duplicate_governance_plugin_ids: set[str] = set()
    registry_source_files: set[str] = set()
    plugin_doc_parse_ok = False

    if plugin_governance_path.exists() and not plugin_governance_alias_error:
        plugin_doc = _load_yaml(plugin_governance_path)
        plugin_doc_parse_ok = bool(plugin_doc)
        if not plugin_doc_parse_ok:
            _append_violation(
                violations,
                field="plugin_governance_file",
                reason="plugin_governance_parse_failed",
                plugin_governance_file=str(plugin_governance_path),
            )
        else:
            doc_control_doc: dict[str, Any] = {}
            docs_cfg: dict[str, Any] = {}
            plugin_doc_map: dict[str, dict[str, Any]] = {}
            playbook_link_token = ""
            if plugin_doc_control_path.exists() and plugin_doc_control_path.is_file():
                doc_control_doc = _load_yaml(plugin_doc_control_path)
                plugin_doc_control_parse_ok = bool(doc_control_doc)
                if not plugin_doc_control_parse_ok:
                    plugin_readability_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_doc_control",
                        reason="plugin_doc_control_parse_failed",
                        plugin_doc_control_file=str(plugin_doc_control_path),
                    )
                else:
                    plugin_doc_control_active_file = str(doc_control_doc.get("active_file", "")).strip()
                    if plugin_doc_control_active_file:
                        active_path = (repo_root / plugin_doc_control_active_file).resolve()
                        plugin_doc_control_resolved_path = active_path
                        if not active_path.exists() or not active_path.is_file():
                            plugin_readability_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_doc_control",
                                reason="active_file_missing",
                                plugin_doc_control_file=str(plugin_doc_control_path),
                                active_file=plugin_doc_control_active_file,
                            )
                            doc_control_doc = {}
                        else:
                            resolved_doc = _load_yaml(active_path)
                            if not resolved_doc:
                                plugin_readability_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="plugin_doc_control",
                                    reason="active_file_parse_failed",
                                    plugin_doc_control_file=str(plugin_doc_control_path),
                                    active_file=plugin_doc_control_active_file,
                                )
                                doc_control_doc = {}
                            else:
                                doc_control_doc = resolved_doc

                    docs_cfg_raw = doc_control_doc.get("docs")
                    docs_cfg = docs_cfg_raw if isinstance(docs_cfg_raw, dict) else {}
                    playbook_rel = str(docs_cfg.get("canonical_playbook", "")).strip()
                    playbook_link_token = str(
                        docs_cfg.get("playbook_link_token", "PLUGIN_WIRING_PLAYBOOK.current.md")
                    ).strip()
                    if not playbook_rel:
                        plugin_readability_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_doc_control",
                            reason="canonical_playbook_missing",
                            plugin_doc_control_file=str(plugin_doc_control_path),
                        )
                    else:
                        playbook_path = (repo_root / playbook_rel).resolve()
                        if not playbook_path.exists() or not playbook_path.is_file():
                            plugin_readability_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_wiring_playbook",
                                reason="playbook_missing",
                                playbook=playbook_rel,
                            )

                    root_readme_rel = str(docs_cfg.get("root_readme", "")).strip()
                    if not root_readme_rel:
                        plugin_readability_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_doc_control",
                            reason="root_readme_missing",
                            plugin_doc_control_file=str(plugin_doc_control_path),
                        )
                    else:
                        root_readme_path = (repo_root / root_readme_rel).resolve()
                        if not root_readme_path.exists() or not root_readme_path.is_file():
                            plugin_readability_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_readme",
                                reason="root_plugin_readme_missing",
                                readme=root_readme_rel,
                            )
                        else:
                            root_readme_text = _read_text(root_readme_path)
                            required_root_tokens = _as_str_list(docs_cfg.get("root_required_tokens"))
                            if playbook_link_token:
                                required_root_tokens.append(playbook_link_token)
                            for token in sorted(set(required_root_tokens)):
                                if token and token not in root_readme_text:
                                    plugin_readability_violation_count += 1
                                    _append_violation(
                                        violations,
                                        field="plugin_readme",
                                        reason="root_plugin_readme_missing_required_token",
                                        readme=root_readme_rel,
                                        missing_token=token,
                                    )

                    for row in _as_list(doc_control_doc.get("plugin_docs")):
                        if not isinstance(row, dict):
                            continue
                        plugin_id = str(row.get("plugin_id", "")).strip()
                        if plugin_id:
                            plugin_doc_map[plugin_id] = row

            # Unique egress invariants.
            unique_egress = plugin_doc.get("unique_egress")
            if isinstance(unique_egress, dict):
                egress_script = str(unique_egress.get("script", "")).strip()
                channel_id = str(unique_egress.get("channel_id", "")).strip()
                surfaces = _as_str_list(unique_egress.get("strict_surfaces"))
                for rel in surfaces:
                    ok_script, err_script = _surface_token_present(repo_root, rel, egress_script)
                    if err_script:
                        unique_egress_violation_count += 1
                        _append_violation(
                            violations,
                            field="unique_egress_surface",
                            reason=err_script,
                            surface=rel,
                            required_script=egress_script,
                        )
                        continue
                    if not ok_script:
                        unique_egress_violation_count += 1
                        _append_violation(
                            violations,
                            field="unique_egress_script",
                            reason="egress_script_missing_on_surface",
                            surface=rel,
                            required_script=egress_script,
                        )
                    if channel_id:
                        ok_channel, _ = _surface_token_present(repo_root, rel, channel_id)
                        if not ok_channel:
                            unique_egress_violation_count += 1
                            _append_violation(
                                violations,
                                field="unique_egress_channel",
                                reason="egress_channel_literal_missing_on_surface",
                                surface=rel,
                                required_channel_id=channel_id,
                            )
            else:
                _append_violation(
                    violations,
                    field="unique_egress",
                    reason="unique_egress_config_missing",
                )

            # Bundle entry invariants.
            bundle_entry = plugin_doc.get("bundle_entry")
            bundle_script = ""
            if isinstance(bundle_entry, dict):
                bundle_script = str(bundle_entry.get("script", "")).strip()
                surfaces = _as_str_list(bundle_entry.get("strict_surfaces"))
                for rel in surfaces:
                    ok_bundle, err_bundle = _surface_token_present(repo_root, rel, bundle_script)
                    if err_bundle:
                        bundle_entry_violation_count += 1
                        _append_violation(
                            violations,
                            field="bundle_entry_surface",
                            reason=err_bundle,
                            surface=rel,
                            required_script=bundle_script,
                        )
                        continue
                    if not ok_bundle:
                        bundle_entry_violation_count += 1
                        _append_violation(
                            violations,
                            field="bundle_entry_script",
                            reason="bundle_script_missing_on_surface",
                            surface=rel,
                            required_script=bundle_script,
                        )
            else:
                _append_violation(
                    violations,
                    field="bundle_entry",
                    reason="bundle_entry_config_missing",
                )

            # Plugin fail-close profile invariants.
            profiles = _as_list(plugin_doc.get("plugin_failclose_profiles"))
            registry_cache: dict[str, dict[str, Any]] = {}
            registry_source_files.update(_as_str_list(plugin_doc.get("plugin_registry_files")))
            if not registry_source_files:
                registry_source_files.add("identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml")
            registry_schema_path = (repo_root / "identity/protocol/plugins/schemas/plugin-registry.schema.json").resolve()
            registry_schema_validator = None
            if Draft202012Validator is None:
                plugin_wiring_violation_count += 1
                _append_violation(
                    violations,
                    field="plugin_registry_schema",
                    reason="jsonschema_dependency_missing",
                    schema_file=str(registry_schema_path),
                )
            elif not registry_schema_path.exists() or not registry_schema_path.is_file():
                plugin_wiring_violation_count += 1
                _append_violation(
                    violations,
                    field="plugin_registry_schema",
                    reason="schema_file_missing",
                    schema_file=str(registry_schema_path),
                )
            else:
                try:
                    registry_schema_validator = Draft202012Validator(_load_json(registry_schema_path))
                except Exception as exc:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry_schema",
                        reason="schema_parse_failed",
                        schema_file=str(registry_schema_path),
                        detail=str(exc),
                    )

            for profile in profiles:
                if not isinstance(profile, dict):
                    continue
                registry_file = str(profile.get("registry_file", "")).strip()
                if registry_file:
                    registry_source_files.add(registry_file)

            for registry_file in sorted(registry_source_files):
                registry_path, registry_active_file, registry_alias_error = _resolve_current_yaml_alias(
                    repo_root,
                    registry_file,
                )
                if registry_alias_error:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry",
                        reason=registry_alias_error,
                        registry_file=registry_file,
                        active_file=registry_active_file,
                    )
                    continue
                if not registry_path.exists() or not registry_path.is_file():
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry",
                        reason="registry_file_missing",
                        registry_file=registry_file,
                    )
                    continue
                cache_key = str(registry_path)
                if cache_key not in registry_cache:
                    registry_cache[cache_key] = _load_yaml(registry_path)
                registry_doc = registry_cache.get(cache_key) or {}
                if registry_schema_validator is not None:
                    schema_errors = list(registry_schema_validator.iter_errors(registry_doc))
                    if schema_errors:
                        plugin_wiring_violation_count += len(schema_errors)
                        for err in schema_errors:
                            error_path = ".".join(str(token) for token in list(getattr(err, "path", [])))
                            _append_violation(
                                violations,
                                field="plugin_registry_schema",
                                reason="registry_schema_validation_failed",
                                registry_file=registry_file,
                                schema_file=str(registry_schema_path),
                                error_path=error_path or "<root>",
                                detail=str(err.message),
                            )
                plugins = _as_list(registry_doc.get("plugins"))
                for row in plugins:
                    if not isinstance(row, dict):
                        continue
                    reg_plugin_id = str(row.get("plugin_id", "")).strip()
                    reg_gate_mode = str(row.get("gate_mode", "")).strip().lower()
                    if reg_plugin_id and reg_gate_mode == "fail_close_strict":
                        registry_fail_close_plugin_ids.add(reg_plugin_id)
                        missing_tuple_fields = [
                            field
                            for field in (
                                "requirement_key",
                                "bundle_target_name",
                                "ssot_mapping_ref",
                                "integration_kind",
                                "protocol_contract_root",
                                "instance_runtime_root",
                            )
                            if not str(row.get(field, "")).strip()
                        ]
                        if missing_tuple_fields:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="fail_close_tuple_fields_missing",
                                plugin_id=reg_plugin_id,
                                registry_file=registry_file,
                                missing_fields=missing_tuple_fields,
                            )

            for profile in profiles:
                if not isinstance(profile, dict):
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_failclose_profiles",
                        reason="profile_row_not_object",
                    )
                    continue
                plugin_profile_count += 1
                plugin_id = str(profile.get("plugin_id", "")).strip()
                requirement_key = str(profile.get("requirement_key", "")).strip()
                target_name = str(profile.get("target_name", "")).strip()
                registry_file = str(profile.get("registry_file", "")).strip()
                contract_file = str(profile.get("contract_file", "")).strip()
                validator_script = str(profile.get("validator_script", "")).strip()
                strict_surfaces = _as_str_list(profile.get("strict_surfaces"))
                required_gate_surfaces = set(_as_str_list(profile.get("required_gate_surfaces")))
                required_report_fields = set(_as_str_list(profile.get("required_report_fields")))
                if not plugin_id:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_failclose_profiles",
                        reason="plugin_id_missing",
                    )
                elif plugin_id in governance_plugin_ids:
                    duplicate_governance_plugin_ids.add(plugin_id)
                governance_plugin_ids.add(plugin_id)

                # Registry profile checks.
                if not registry_file:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry",
                        reason="registry_file_missing_on_profile",
                        plugin_id=plugin_id,
                    )
                else:
                    registry_path, registry_active_file, registry_alias_error = _resolve_current_yaml_alias(
                        repo_root,
                        registry_file,
                    )
                    cache_key = str(registry_path)
                    registry_doc = registry_cache.get(cache_key)
                    if registry_alias_error:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_registry",
                            reason=registry_alias_error,
                            plugin_id=plugin_id,
                            registry_file=registry_file,
                            active_file=registry_active_file,
                        )
                        registry_doc = {}
                    elif registry_doc is None:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_registry",
                            reason="registry_file_missing",
                            plugin_id=plugin_id,
                            registry_file=registry_file,
                        )
                        registry_doc = {}
                    plugins = _as_list(registry_doc.get("plugins"))
                    plugin_rows = [
                        row
                        for row in plugins
                        if isinstance(row, dict) and str(row.get("plugin_id", "")).strip() == plugin_id
                    ]
                    if not plugin_rows:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_registry",
                            reason="plugin_id_missing_in_registry",
                            plugin_id=plugin_id,
                            registry_file=registry_file,
                        )
                    else:
                        reg_row = plugin_rows[0]
                        registry_contract = str(reg_row.get("contract_file", "")).strip()
                        registry_validator = str(reg_row.get("validator_script", "")).strip()
                        registry_requirement = str(reg_row.get("requirement_key", "")).strip()
                        registry_target = str(reg_row.get("bundle_target_name", "")).strip()
                        registry_mode = str(reg_row.get("gate_mode", "")).strip().lower()
                        registry_status = str(reg_row.get("status", "")).strip().lower()
                        registry_integration_kind = str(reg_row.get("integration_kind", "")).strip().lower()
                        registry_protocol_root = str(reg_row.get("protocol_contract_root", "")).strip()
                        registry_runtime_root = str(reg_row.get("instance_runtime_root", "")).strip()
                        if contract_file and registry_contract != contract_file:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_contract_mismatch",
                                plugin_id=plugin_id,
                                expected_contract_file=contract_file,
                                observed_contract_file=registry_contract,
                            )
                        if validator_script and registry_validator != validator_script:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_validator_mismatch",
                                plugin_id=plugin_id,
                                expected_validator_script=validator_script,
                                observed_validator_script=registry_validator,
                            )
                        if not registry_requirement:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_requirement_key_missing",
                                plugin_id=plugin_id,
                                expected_requirement_key=requirement_key,
                            )
                        elif registry_requirement != requirement_key:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_requirement_key_mismatch",
                                plugin_id=plugin_id,
                                expected_requirement_key=requirement_key,
                                observed_requirement_key=registry_requirement,
                            )
                        if not registry_target:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_bundle_target_missing",
                                plugin_id=plugin_id,
                                expected_target_name=target_name,
                            )
                        elif registry_target != target_name:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_bundle_target_mismatch",
                                plugin_id=plugin_id,
                                expected_target_name=target_name,
                                observed_target_name=registry_target,
                            )
                        if not registry_mode:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_gate_mode_missing",
                                plugin_id=plugin_id,
                                expected_gate_mode="fail_close_strict",
                            )
                        elif registry_mode != "fail_close_strict":
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_gate_mode_not_fail_close_strict",
                                plugin_id=plugin_id,
                                expected_gate_mode="fail_close_strict",
                                observed_gate_mode=registry_mode,
                            )
                        if registry_mode == "fail_close_strict" and registry_status != "active":
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_fail_close_plugin_status_not_active",
                                plugin_id=plugin_id,
                                expected_status="active",
                                observed_status=registry_status or "MISSING",
                            )
                        if not registry_integration_kind:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_integration_kind_missing",
                                plugin_id=plugin_id,
                            )
                        else:
                            integration_rule = INTEGRATION_KIND_RULES.get(registry_integration_kind)
                            if integration_rule is None:
                                plugin_wiring_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="plugin_registry",
                                    reason="registry_integration_kind_invalid",
                                    plugin_id=plugin_id,
                                    integration_kind=registry_integration_kind,
                                    allowed=sorted(INTEGRATION_KIND_RULES.keys()),
                                )
                            else:
                                expected_protocol_root = integration_rule["protocol_contract_root"]
                                expected_runtime_root = integration_rule["instance_runtime_root"]
                                if registry_protocol_root != expected_protocol_root:
                                    plugin_wiring_violation_count += 1
                                    _append_violation(
                                        violations,
                                        field="plugin_registry",
                                        reason="registry_protocol_contract_root_mismatch",
                                        plugin_id=plugin_id,
                                        expected_protocol_contract_root=expected_protocol_root,
                                        observed_protocol_contract_root=registry_protocol_root,
                                    )
                                if registry_runtime_root != expected_runtime_root:
                                    plugin_wiring_violation_count += 1
                                    _append_violation(
                                        violations,
                                        field="plugin_registry",
                                        reason="registry_instance_runtime_root_mismatch",
                                        plugin_id=plugin_id,
                                        expected_instance_runtime_root=expected_runtime_root,
                                        observed_instance_runtime_root=registry_runtime_root,
                                    )
                                if registry_contract and registry_protocol_root and not _path_within_root(
                                    registry_contract, registry_protocol_root
                                ):
                                    plugin_wiring_violation_count += 1
                                    _append_violation(
                                        violations,
                                        field="plugin_registry",
                                        reason="registry_contract_file_out_of_protocol_root",
                                        plugin_id=plugin_id,
                                        contract_file=registry_contract,
                                        protocol_contract_root=registry_protocol_root,
                                    )

                # Contract file canonical path check.
                contract_path = (repo_root / contract_file).resolve() if contract_file else None
                if not contract_file or contract_path is None or not contract_path.exists():
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_contract_file",
                        reason="contract_file_missing",
                        plugin_id=plugin_id,
                        contract_file=contract_file,
                    )
                else:
                    doc_cfg = plugin_doc_map.get(plugin_id)
                    if not isinstance(doc_cfg, dict):
                        plugin_readability_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_doc_control",
                            reason="plugin_doc_entry_missing",
                            plugin_id=plugin_id,
                            plugin_doc_control_file=str(plugin_doc_control_path),
                        )
                        doc_cfg = {}
                    plugin_dir = Path(contract_file).parent
                    plugin_readme_rel = str(doc_cfg.get("readme", "")).strip() or (plugin_dir / "README.md").as_posix()
                    plugin_readme_path = (repo_root / plugin_readme_rel).resolve()
                    if not plugin_readme_path.exists() or not plugin_readme_path.is_file():
                        plugin_readability_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_readme",
                            reason="plugin_readme_missing",
                            plugin_id=plugin_id,
                            readme=plugin_readme_rel,
                        )
                    else:
                        plugin_readme_text = _read_text(plugin_readme_path)
                        required_tokens = set(_as_str_list(doc_cfg.get("required_tokens")))
                        if playbook_link_token:
                            required_tokens.add(playbook_link_token)
                        if requirement_key:
                            required_tokens.add(requirement_key)
                        if target_name:
                            required_tokens.add(target_name)
                        for token in sorted(required_tokens):
                            if token and token not in plugin_readme_text:
                                plugin_readability_violation_count += 1
                                _append_violation(
                                    violations,
                                    field="plugin_readme",
                                    reason="plugin_readme_missing_required_token",
                                    plugin_id=plugin_id,
                                    readme=plugin_readme_rel,
                                    missing_token=token,
                                )

                # Mapping row checks.
                mapping_row = mapping_doc.get(requirement_key) if isinstance(mapping_doc, dict) else None
                if not isinstance(mapping_row, dict):
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="mapping_row",
                        reason="mapping_row_missing_for_plugin_requirement",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                    )
                else:
                    mapping_validators = _mapping_validator_scripts(mapping_row)
                    if validator_script and validator_script not in mapping_validators:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_validator_missing",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            expected_validator_script=validator_script,
                            observed_validator_scripts=sorted(mapping_validators),
                        )

                    mapping_surfaces = set(_as_str_list(mapping_row.get("gate_surfaces")))
                    missing_surfaces = sorted(required_gate_surfaces - mapping_surfaces)
                    if missing_surfaces:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_gate_surfaces_incomplete",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            missing_gate_surfaces=missing_surfaces,
                        )

                    mapping_fields = set(_as_str_list(mapping_row.get("report_field_refs")))
                    missing_fields = sorted(required_report_fields - mapping_fields)
                    if missing_fields:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_report_field_refs_incomplete",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            missing_report_field_refs=missing_fields,
                        )

                # Bundle requirement/target checks.
                if requirement_key and requirement_key not in bundle_rows:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="bundle_runner",
                        reason="bundle_requirement_missing",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                    )
                observed_target = bundle_target_map.get(requirement_key, "")
                if requirement_key and target_name and observed_target != target_name:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="bundle_runner",
                        reason="bundle_target_mapping_mismatch",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        expected_target_name=target_name,
                        observed_target_name=observed_target,
                    )

                # Direct validator bypass checks on strict surfaces.
                for rel in strict_surfaces:
                    path = (repo_root / rel).resolve()
                    if not path.exists():
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="strict_surface_missing",
                            plugin_id=plugin_id,
                            surface=rel,
                        )
                        continue
                    text = _read_text(path)
                    if validator_script and validator_script in text:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="direct_validator_reference_detected",
                            plugin_id=plugin_id,
                            surface=rel,
                            validator_script=validator_script,
                        )
                    if bundle_script and bundle_script not in text:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="bundle_runner_reference_missing",
                            plugin_id=plugin_id,
                            surface=rel,
                            required_script=bundle_script,
                        )

            if duplicate_governance_plugin_ids:
                plugin_wiring_violation_count += len(duplicate_governance_plugin_ids)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="duplicate_plugin_profile_detected",
                    duplicate_plugin_ids=sorted(duplicate_governance_plugin_ids),
                )

            missing_governance_profiles = sorted(registry_fail_close_plugin_ids - governance_plugin_ids)
            if missing_governance_profiles:
                plugin_wiring_violation_count += len(missing_governance_profiles)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="registry_fail_close_plugin_missing_governance_profile",
                    missing_plugin_ids=missing_governance_profiles,
                    missing_count=len(missing_governance_profiles),
                )

            orphan_governance_profiles = sorted(governance_plugin_ids - registry_fail_close_plugin_ids)
            if orphan_governance_profiles:
                plugin_wiring_violation_count += len(orphan_governance_profiles)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="governance_profile_missing_registry_fail_close_plugin",
                    orphan_plugin_ids=orphan_governance_profiles,
                    orphan_count=len(orphan_governance_profiles),
                )

            # Prompt fail-close binding invariants.
            prompt_binding = plugin_doc.get("prompt_failclose_binding")
            if isinstance(prompt_binding, dict):
                script_rel = str(prompt_binding.get("enforcement_script", "")).strip()
                script_path = (repo_root / script_rel).resolve()
                if not script_rel or not script_path.exists():
                    prompt_binding_violation_count += 1
                    _append_violation(
                        violations,
                        field="prompt_failclose_binding",
                        reason="enforcement_script_missing",
                        enforcement_script=script_rel,
                    )
                else:
                    text = _read_text(script_path)
                    for token in _as_str_list(prompt_binding.get("required_contract_keys")):
                        if token not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="required_contract_key_not_wired",
                                enforcement_script=script_rel,
                                missing_contract_key=token,
                            )
                    for token in _as_str_list(prompt_binding.get("required_result_fields")):
                        if token not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="required_result_field_not_emitted",
                                enforcement_script=script_rel,
                                missing_result_field=token,
                            )
                    strict_guard = prompt_binding.get("strict_failure_guard")
                    if isinstance(strict_guard, dict):
                        status_field = str(strict_guard.get("status_field", "")).strip()
                        required_status = str(strict_guard.get("required_status", "")).strip()
                        if status_field and status_field not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="strict_failure_status_field_missing",
                                enforcement_script=script_rel,
                                status_field=status_field,
                            )
                        if required_status and required_status not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="strict_failure_required_status_missing",
                                enforcement_script=script_rel,
                                required_status=required_status,
                            )
            else:
                _append_violation(
                    violations,
                    field="prompt_failclose_binding",
                    reason="prompt_failclose_binding_config_missing",
                )

    plugin_governance_violation_count = sum(
        1
        for row in violations
        if str(row.get("field", "")).strip() in {"plugin_governance_alias", "plugin_governance_file"}
    )

    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_INVARIANT
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "control_plane_invariants_status": status,
        "error_code": error_code,
        "invariants_entry_file": str(invariants_entry_path),
        "invariants_configured_file": invariants_configured_file,
        "invariants_file": str(invariants_path),
        "invariants_active_file": invariants_active_file,
        "invariants_alias_error": invariants_alias_error,
        "contract_mapping_entry": str(contract_mapping_entry_path),
        "contract_mapping": str(mapping_path),
        "contract_mapping_active_file": contract_mapping_active_file,
        "contract_mapping_alias_error": contract_mapping_alias_error,
        "contract_binding_alias_enabled": contract_binding_alias_enabled,
        "contract_binding_current_file": str(contract_binding_current_path),
        "contract_binding_current_configured_file": contract_binding_current_configured_file,
        "contract_binding_current_resolved_file": str(contract_binding_current_resolved_path),
        "contract_binding_parse_ok": contract_binding_parse_ok,
        "contract_binding_violation_count": contract_binding_violation_count,
        "contract_binding_meta_row_count": contract_binding_meta_row_count,
        "contract_binding_actual_row_count": contract_binding_actual_row_count,
        "contract_binding_row_count_match": contract_binding_row_count_match,
        "plugin_governance_configured_file": plugin_governance_configured_file,
        "plugin_governance_entry_file": str(plugin_governance_entry_path),
        "plugin_governance_file": str(plugin_governance_path),
        "plugin_governance_active_file": plugin_governance_active_file,
        "plugin_governance_alias_enabled": plugin_governance_alias_enabled,
        "plugin_governance_alias_error": plugin_governance_alias_error,
        "plugin_governance_violation_count": plugin_governance_violation_count,
        "plugin_doc_control_file": str(plugin_doc_control_path),
        "plugin_doc_control_resolved_file": str(plugin_doc_control_resolved_path),
        "plugin_doc_control_active_file": plugin_doc_control_active_file,
        "github_offload_alias_enabled": github_offload_alias_enabled,
        "github_offload_current_file": str(github_offload_current_path),
        "github_offload_current_configured_file": github_offload_current_configured_file,
        "github_offload_current_resolved_file": str(github_offload_current_resolved_path),
        "github_offload_active_file": github_offload_active_file,
        "github_offload_parse_ok": github_offload_parse_ok,
        "github_offload_violation_count": github_offload_violation_count,
        "layer_gate_profile_alias_enabled": layer_gate_profile_alias_enabled,
        "layer_gate_profile_current_file": str(layer_gate_profile_current_path),
        "layer_gate_profile_current_configured_file": layer_gate_profile_current_configured_file,
        "layer_gate_profile_current_resolved_file": str(layer_gate_profile_current_resolved_path),
        "layer_gate_profile_active_file": layer_gate_profile_active_file,
        "layer_gate_profile_parse_ok": layer_gate_profile_parse_ok,
        "layer_gate_profile_violation_count": layer_gate_profile_violation_count,
        "stream_doc_registry_alias_enabled": stream_doc_registry_alias_enabled,
        "stream_doc_registry_current_file": str(stream_doc_registry_current_path),
        "stream_doc_registry_current_configured_file": stream_doc_registry_current_configured_file,
        "stream_doc_registry_current_resolved_file": str(stream_doc_registry_current_resolved_path),
        "stream_doc_registry_active_file": stream_doc_registry_active_file,
        "stream_doc_registry_parse_ok": stream_doc_registry_parse_ok,
        "stream_doc_registry_violation_count": stream_doc_registry_violation_count,
        "doc_evidence_allowlist_alias_enabled": doc_evidence_allowlist_alias_enabled,
        "doc_evidence_allowlist_current_file": str(doc_evidence_allowlist_current_path),
        "doc_evidence_allowlist_current_configured_file": doc_evidence_allowlist_current_configured_file,
        "doc_evidence_allowlist_current_resolved_file": str(doc_evidence_allowlist_current_resolved_path),
        "doc_evidence_allowlist_active_file": doc_evidence_allowlist_active_file,
        "doc_evidence_allowlist_parse_ok": doc_evidence_allowlist_parse_ok,
        "doc_evidence_allowlist_violation_count": doc_evidence_allowlist_violation_count,
        "control_plane_budget_alias_enabled": control_plane_budget_alias_enabled,
        "control_plane_budget_current_file": str(control_plane_budget_current_path),
        "control_plane_budget_current_configured_file": control_plane_budget_current_configured_file,
        "control_plane_budget_current_resolved_file": str(control_plane_budget_current_resolved_path),
        "control_plane_budget_active_file": control_plane_budget_active_file,
        "control_plane_budget_parse_ok": control_plane_budget_parse_ok,
        "control_plane_budget_violation_count": control_plane_budget_violation_count,
        "control_plane_status_alias_enabled": control_plane_status_alias_enabled,
        "control_plane_status_current_file": str(control_plane_status_current_path),
        "control_plane_status_current_configured_file": control_plane_status_current_configured_file,
        "control_plane_status_current_resolved_file": str(control_plane_status_current_resolved_path),
        "control_plane_status_active_file": control_plane_status_active_file,
        "control_plane_status_parse_ok": control_plane_status_parse_ok,
        "control_plane_status_violation_count": control_plane_status_violation_count,
        "plugin_control_plane_alias_enabled": plugin_control_plane_alias_enabled,
        "plugin_control_plane_alias_parse_ok": plugin_control_plane_alias_parse_ok,
        "plugin_control_plane_alias_violation_count": plugin_control_plane_alias_violation_count,
        "plugin_control_plane_alias_current_files": plugin_control_plane_alias_current_files,
        "plugin_control_plane_alias_active_files": plugin_control_plane_alias_active_files,
        "bundle_mapping_parity_mode": mode,
        "bundle_mapping_parity_baseline_missing_rows": baseline_missing_rows,
        "bundle_mapping_parity_reduction_plan_file": reduction_plan_file,
        "bundle_mapping_parity_reduction_plan_status": reduction_plan_status,
        "bundle_mapping_parity_reduction_plan_targets": sorted(reduction_plan_targets),
        "bundle_mapping_parity_reduction_plan_zero_target": reduction_plan_target_zero,
        "mapping_rows_missing_in_bundle_count": len(missing_rows),
        "mapping_rows_missing_in_bundle": missing_rows,
        "bundle_rows_not_in_mapping_count": len(extra_rows),
        "bundle_rows_not_in_mapping": extra_rows,
        "plugin_profile_count": plugin_profile_count,
        "plugin_wiring_violation_count": plugin_wiring_violation_count,
        "registry_fail_close_plugin_count": len(registry_fail_close_plugin_ids),
        "registry_fail_close_plugin_ids": sorted(registry_fail_close_plugin_ids),
        "governance_profile_plugin_count": len(governance_plugin_ids),
        "governance_profile_plugin_ids": sorted(governance_plugin_ids),
        "duplicate_governance_profile_count": len(duplicate_governance_plugin_ids),
        "duplicate_governance_plugin_ids": sorted(duplicate_governance_plugin_ids),
        "unique_egress_violation_count": unique_egress_violation_count,
        "bundle_entry_violation_count": bundle_entry_violation_count,
        "prompt_binding_violation_count": prompt_binding_violation_count,
        "plugin_readability_violation_count": plugin_readability_violation_count,
        "plugin_governance_parse_ok": plugin_doc_parse_ok,
        "plugin_doc_control_parse_ok": plugin_doc_control_parse_ok,
        "bundle_target_map_size": len(bundle_target_map),
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-INVARIANTS] status={status} "
            f"mode={mode or '-'} "
            f"mapping_missing={len(missing_rows)} "
            f"extra_bundle_rows={len(extra_rows)} "
            f"plugin_profiles={plugin_profile_count} "
            f"violations={len(violations)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
