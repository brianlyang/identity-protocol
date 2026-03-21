#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

WORKBOOK_REGISTRY_CURRENT = "identity/protocol/mappings/workbook-registry.current.yaml"
STREAM_DOC_REGISTRY_CURRENT = "identity/protocol/mappings/stream-doc-registry.current.yaml"
CONTROL_PLANE_STATUS_CURRENT = "identity/protocol/mappings/control-plane-status.current.yaml"
WORKBOOK_MINOR_RE = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)$")
TEMPLATE_PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")


@dataclass(frozen=True)
class WorkbookTemplateContract:
    contract_id: str
    template_dir_rel: str
    templates_readme_rel: str
    issue_register_template_rel: str
    deep_audit_template_rel: str
    scaffold_script_rel: str
    contract_validator_rel: str
    scaffold_projection_root_rel: str
    projection_policy: str
    projection_presence_policy: str
    projection_freshness_mode: str
    current_pointer_activation_mode: str
    current_pointer_activation_consent_token: str
    governance_doc_rel: str
    control_plane_status_ref: str
    stream_doc_registry_ref: str
    workbook_registry_current_ref: str


@dataclass(frozen=True)
class WorkbookFamilyLayout:
    minor: str
    patch_lane_token: str
    issue_register_doc_rel: str
    deep_audit_doc_rel: str
    registry_doc_rel: str
    issue_register_projection_rel: str
    deep_audit_projection_rel: str


@dataclass(frozen=True)
class WorkbookRegistryBundle:
    current_path: Path
    versioned_path: Path
    registry_doc: dict[str, Any]
    active_family_doc: dict[str, Any]
    template_contract: WorkbookTemplateContract


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"yaml root must be mapping: {path}")
    return doc


def _non_empty_text(value: Any) -> str:
    return str(value or "").strip()


def validate_minor_family_token(minor: str) -> str:
    token = _non_empty_text(minor)
    if not WORKBOOK_MINOR_RE.fullmatch(token):
        raise ValueError(f"invalid workbook minor token: {minor}")
    return token


def derive_patch_lane_token(minor: str) -> str:
    token = validate_minor_family_token(minor)
    return f"{token}.x"


def derive_probe_minor_from_active(active_minor: str) -> str:
    match = WORKBOOK_MINOR_RE.fullmatch(validate_minor_family_token(active_minor))
    if match is None:
        raise ValueError(f"invalid active workbook minor token: {active_minor}")
    major = int(match.group("major"))
    minor = int(match.group("minor")) + 1
    return f"v{major}.{minor}"


def workbook_family_layout(minor: str, *, template_contract: WorkbookTemplateContract) -> WorkbookFamilyLayout:
    token = validate_minor_family_token(minor)
    projection_root = Path(template_contract.scaffold_projection_root_rel) / token
    return WorkbookFamilyLayout(
        minor=token,
        patch_lane_token=derive_patch_lane_token(token),
        issue_register_doc_rel=f"docs/workbook/protocol-issue-register-{token}.md",
        deep_audit_doc_rel=f"docs/workbook/protocol-deep-audit-workbook-{token}.md",
        registry_doc_rel=f"identity/protocol/mappings/workbook-registry.{token}.yaml",
        issue_register_projection_rel=str(projection_root / f"protocol-issue-register-{token}.projection.md"),
        deep_audit_projection_rel=str(projection_root / f"protocol-deep-audit-workbook-{token}.projection.md"),
    )


def _load_template_contract(template_doc: dict[str, Any]) -> WorkbookTemplateContract:
    template_dir_rel = _non_empty_text(template_doc.get("template_dir"))
    templates_readme_rel = _non_empty_text(template_doc.get("templates_readme"))
    issue_register_template_rel = _non_empty_text(template_doc.get("issue_register_template"))
    deep_audit_template_rel = _non_empty_text(template_doc.get("deep_audit_template"))
    scaffold_script_rel = _non_empty_text(template_doc.get("scaffold_script"))
    contract_validator_rel = _non_empty_text(template_doc.get("contract_validator"))
    scaffold_projection_root_rel = _non_empty_text(template_doc.get("scaffold_projection_root"))
    governance_doc_rel = _non_empty_text(template_doc.get("governance_doc"))
    current_pointer_activation_consent_token = _non_empty_text(
        template_doc.get("current_pointer_activation_consent_token")
    )
    required = {
        "template_dir": template_dir_rel,
        "templates_readme": templates_readme_rel,
        "issue_register_template": issue_register_template_rel,
        "deep_audit_template": deep_audit_template_rel,
        "scaffold_script": scaffold_script_rel,
        "contract_validator": contract_validator_rel,
        "scaffold_projection_root": scaffold_projection_root_rel,
        "governance_doc": governance_doc_rel,
        "current_pointer_activation_consent_token": current_pointer_activation_consent_token,
    }
    missing = sorted(key for key, value in required.items() if not value)
    if missing:
        raise ValueError(f"template_contract missing fields: {','.join(missing)}")
    return WorkbookTemplateContract(
        contract_id=_non_empty_text(template_doc.get("contract_id")) or "minor_family_workbook_template_v1",
        template_dir_rel=template_dir_rel,
        templates_readme_rel=templates_readme_rel,
        issue_register_template_rel=issue_register_template_rel,
        deep_audit_template_rel=deep_audit_template_rel,
        scaffold_script_rel=scaffold_script_rel,
        contract_validator_rel=contract_validator_rel,
        scaffold_projection_root_rel=scaffold_projection_root_rel,
        projection_policy=_non_empty_text(template_doc.get("projection_policy"))
        or "optional_workspace_projection_exports",
        projection_presence_policy=_non_empty_text(template_doc.get("projection_presence_policy"))
        or "optional_projection",
        projection_freshness_mode=_non_empty_text(template_doc.get("projection_freshness_mode"))
        or "activation_required_before_freshness",
        current_pointer_activation_mode=_non_empty_text(template_doc.get("current_pointer_activation_mode"))
        or "explicit_current_pointer_switch_only",
        current_pointer_activation_consent_token=current_pointer_activation_consent_token,
        governance_doc_rel=governance_doc_rel,
        control_plane_status_ref=_non_empty_text(template_doc.get("control_plane_status_ref"))
        or CONTROL_PLANE_STATUS_CURRENT,
        stream_doc_registry_ref=_non_empty_text(template_doc.get("stream_doc_registry_ref"))
        or STREAM_DOC_REGISTRY_CURRENT,
        workbook_registry_current_ref=_non_empty_text(template_doc.get("workbook_registry_current_ref"))
        or WORKBOOK_REGISTRY_CURRENT,
    )


def load_active_workbook_registry(repo_root: Path) -> WorkbookRegistryBundle:
    current_path = (repo_root / WORKBOOK_REGISTRY_CURRENT).resolve()
    current_doc = _load_yaml(current_path)
    active_file = _non_empty_text(current_doc.get("active_file"))
    if not active_file:
        raise ValueError(f"active_file missing in workbook registry current pointer: {current_path}")
    versioned_path = (repo_root / active_file).resolve()
    registry_doc = _load_yaml(versioned_path)
    active_family_doc = registry_doc.get("active_workbook_family")
    if not isinstance(active_family_doc, dict):
        raise ValueError(f"active_workbook_family missing: {versioned_path}")
    template_contract_doc = registry_doc.get("template_contract")
    if not isinstance(template_contract_doc, dict):
        raise ValueError(f"template_contract missing: {versioned_path}")
    return WorkbookRegistryBundle(
        current_path=current_path,
        versioned_path=versioned_path,
        registry_doc=registry_doc,
        active_family_doc=active_family_doc,
        template_contract=_load_template_contract(template_contract_doc),
    )


def resolve_workbook_roots(repo_root_arg: str, workspace_root_arg: str, *, start: str | Path) -> tuple[Path, Path]:
    repo_root = resolve_protocol_repo_root(repo_root_arg, start=start)
    workspace_root = resolve_workspace_root(workspace_root_arg, start=start)
    return repo_root, workspace_root


def render_template_text(template_text: str, replacements: dict[str, str]) -> str:
    rendered = template_text
    for key, value in replacements.items():
        rendered = rendered.replace(f"__{key}__", value)
    return rendered


def unresolved_template_tokens(text: str) -> list[str]:
    return sorted(set(TEMPLATE_PLACEHOLDER_RE.findall(text)))
