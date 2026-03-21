#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from workbook_control_plane_common import (
    WorkbookFamilyLayout,
    WorkbookTemplateContract,
    load_active_workbook_registry,
    render_template_text,
    resolve_workbook_roots,
    validate_minor_family_token,
    workbook_family_layout,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_SCAFFOLD_CONTRACT = "IP-WFSC-001"
ERR_OUTPUT_EXISTS = "IP-WFSC-002"
ERR_ACTIVATION_CONSENT = "IP-WFSC-003"


def _load_template_text(repo_root: Path, rel_path: str) -> str:
    return (repo_root / rel_path).read_text(encoding="utf-8")


def _projection_stub_text(
    *,
    projection_source_rel: str,
    registry_current_rel: str,
    family_registry_rel: str,
    minor: str,
) -> str:
    repo_name = "identity-protocol-local"
    return (
        f"# Identity Protocol {minor} Workbook Projection Stub\n\n"
        "Projection mode: mirror-only\n"
        "Authority boundary: this file is projection-only\n"
        f"Projection source: `{repo_name}/{projection_source_rel}`\n"
        f"Workbook registry source: `{repo_name}/{registry_current_rel}`\n"
        f"Activation candidate registry: `{repo_name}/{family_registry_rel}`\n\n"
        "## Scaffold state\n\n"
        "1. This projection stub exists only to reserve the outer export path for the workbook family scaffold.\n"
        "2. It does not participate in status authority before workbook-family activation and projection backfill.\n"
        "3. Refresh live counts only after the family becomes active.\n"
    )


def _render_markdown_templates(
    *,
    repo_root: Path,
    template_contract: WorkbookTemplateContract,
    layout: WorkbookFamilyLayout,
) -> tuple[str, str]:
    replacements = {
        "WORKBOOK_MINOR": layout.minor,
        "WORKBOOK_PATCH_LANE": layout.patch_lane_token,
        "WORKBOOK_REGISTRY_CURRENT_REF": template_contract.workbook_registry_current_ref,
        "STREAM_DOC_REGISTRY_CURRENT_REF": template_contract.stream_doc_registry_ref,
        "CONTROL_PLANE_STATUS_CURRENT_REF": template_contract.control_plane_status_ref,
        "FAMILY_REGISTRY_DOC": layout.registry_doc_rel,
        "GOVERNANCE_DOC": template_contract.governance_doc_rel,
        "SCAFFOLD_SCRIPT": template_contract.scaffold_script_rel,
        "ISSUE_REGISTER_DOC": layout.issue_register_doc_rel,
        "DEEP_AUDIT_DOC": layout.deep_audit_doc_rel,
    }
    issue_register_text = render_template_text(
        _load_template_text(repo_root, template_contract.issue_register_template_rel),
        replacements,
    )
    deep_audit_text = render_template_text(
        _load_template_text(repo_root, template_contract.deep_audit_template_rel),
        replacements,
    )
    return issue_register_text, deep_audit_text


def _registry_doc(
    *,
    template_contract: WorkbookTemplateContract,
    layout: WorkbookFamilyLayout,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "version": layout.minor,
        "control_plane_contract": "minor_family_workbook_control_plane",
        "description": "Canonical workbook registry for cross-stream issue governance inside identity-protocol-local.",
        "template_contract": {
            "contract_id": template_contract.contract_id,
            "template_dir": template_contract.template_dir_rel,
            "templates_readme": template_contract.templates_readme_rel,
            "issue_register_template": template_contract.issue_register_template_rel,
            "deep_audit_template": template_contract.deep_audit_template_rel,
            "scaffold_script": template_contract.scaffold_script_rel,
            "contract_validator": template_contract.contract_validator_rel,
            "scaffold_projection_root": template_contract.scaffold_projection_root_rel,
            "projection_policy": template_contract.projection_policy,
            "projection_presence_policy": template_contract.projection_presence_policy,
            "projection_freshness_mode": template_contract.projection_freshness_mode,
            "current_pointer_activation_mode": template_contract.current_pointer_activation_mode,
            "current_pointer_activation_consent_token": template_contract.current_pointer_activation_consent_token,
            "governance_doc": template_contract.governance_doc_rel,
            "workbook_registry_current_ref": template_contract.workbook_registry_current_ref,
            "stream_doc_registry_ref": template_contract.stream_doc_registry_ref,
            "control_plane_status_ref": template_contract.control_plane_status_ref,
        },
        "active_workbook_family": {
            "workbook_family": layout.minor,
            "minor_family_uniqueness_mode": "exact_canonical_pair_only",
            "authority_surfaces": {
                "issue_register_doc": layout.issue_register_doc_rel,
                "deep_audit_workbook_doc": layout.deep_audit_doc_rel,
            },
            "issue_register_doc": layout.issue_register_doc_rel,
            "deep_audit_workbook_doc": layout.deep_audit_doc_rel,
            "governance_doc": template_contract.governance_doc_rel,
            "projection_policy": template_contract.projection_policy,
            "projection_exports": [
                {
                    "projection_role": "issue_register_projection",
                    "path": layout.issue_register_projection_rel,
                    "authority_doc": layout.issue_register_doc_rel,
                    "presence_policy": template_contract.projection_presence_policy,
                    "freshness_mode": template_contract.projection_freshness_mode,
                },
                {
                    "projection_role": "deep_audit_projection",
                    "path": layout.deep_audit_projection_rel,
                    "authority_doc": layout.deep_audit_doc_rel,
                    "presence_policy": template_contract.projection_presence_policy,
                    "freshness_mode": template_contract.projection_freshness_mode,
                },
            ],
            "authority_model": "minor_family_issue_register_authoritative_with_optional_workspace_projections",
            "stream_version_mode": "workbook_minor_governs_stream_patch_lanes",
        },
    }


def _write_text(path: Path, text: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_yaml(path: Path, doc: dict[str, Any], *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new minor-family workbook control-plane bundle.")
    parser.add_argument("--minor", required=True)
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--workspace-root", default="")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--activate-current", action="store_true")
    parser.add_argument("--activation-consent-token", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "minor": "",
        "repo_root": "",
        "workspace_root": "",
        "generated_paths": {},
        "current_pointer_updated": False,
        "active_family_before": "",
        "active_family_after": "",
        "violations": [],
    }

    try:
        repo_root, workspace_root = resolve_workbook_roots(args.repo_root, args.workspace_root, start=__file__)
        minor = validate_minor_family_token(args.minor)
        registry_bundle = load_active_workbook_registry(repo_root)
        template_contract = registry_bundle.template_contract
        layout = workbook_family_layout(minor, template_contract=template_contract)
        active_family_before = str(registry_bundle.active_family_doc.get("workbook_family", "")).strip()
        issue_register_text, deep_audit_text = _render_markdown_templates(
            repo_root=repo_root,
            template_contract=template_contract,
            layout=layout,
        )
        registry_doc = _registry_doc(template_contract=template_contract, layout=layout)
        issue_projection_text = _projection_stub_text(
            projection_source_rel=layout.issue_register_doc_rel,
            registry_current_rel=template_contract.workbook_registry_current_ref,
            family_registry_rel=layout.registry_doc_rel,
            minor=layout.minor,
        )
        deep_projection_text = _projection_stub_text(
            projection_source_rel=layout.deep_audit_doc_rel,
            registry_current_rel=template_contract.workbook_registry_current_ref,
            family_registry_rel=layout.registry_doc_rel,
            minor=layout.minor,
        )
    except Exception as exc:
        payload["error_code"] = ERR_SCAFFOLD_CONTRACT
        payload["violations"] = [f"scaffold_contract:{type(exc).__name__}:{exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["minor"] = minor
    payload["repo_root"] = str(repo_root)
    payload["workspace_root"] = str(workspace_root)
    payload["active_family_before"] = active_family_before
    generated_paths = {
        "issue_register_doc": str((repo_root / layout.issue_register_doc_rel).resolve()),
        "deep_audit_workbook_doc": str((repo_root / layout.deep_audit_doc_rel).resolve()),
        "registry_doc": str((repo_root / layout.registry_doc_rel).resolve()),
        "issue_register_projection": str((workspace_root / layout.issue_register_projection_rel).resolve()),
        "deep_audit_projection": str((workspace_root / layout.deep_audit_projection_rel).resolve()),
    }
    payload["generated_paths"] = generated_paths

    try:
        _write_text(repo_root / layout.issue_register_doc_rel, issue_register_text, overwrite=args.overwrite)
        _write_text(repo_root / layout.deep_audit_doc_rel, deep_audit_text, overwrite=args.overwrite)
        _write_yaml(repo_root / layout.registry_doc_rel, registry_doc, overwrite=args.overwrite)
        _write_text(
            workspace_root / layout.issue_register_projection_rel,
            issue_projection_text,
            overwrite=args.overwrite,
        )
        _write_text(
            workspace_root / layout.deep_audit_projection_rel,
            deep_projection_text,
            overwrite=args.overwrite,
        )
        active_family_after = active_family_before
        if args.activate_current:
            if args.activation_consent_token != template_contract.current_pointer_activation_consent_token:
                raise PermissionError("activation consent token mismatch")
            current_doc = _load_current_pointer(registry_bundle.current_path)
            current_doc["active_family"] = minor
            current_doc["active_file"] = layout.registry_doc_rel
            _write_yaml(registry_bundle.current_path, current_doc, overwrite=True)
            active_family_after = minor
            payload["current_pointer_updated"] = True
        payload["active_family_after"] = active_family_after
    except FileExistsError as exc:
        payload["error_code"] = ERR_OUTPUT_EXISTS
        payload["violations"] = [f"output_exists:{exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1
    except PermissionError as exc:
        payload["error_code"] = ERR_ACTIVATION_CONSENT
        payload["violations"] = [f"activation_consent:{exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["status"] = STATUS_PASS_REQUIRED
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0


def _load_current_pointer(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"yaml root must be mapping: {path}")
    return doc


if __name__ == "__main__":
    raise SystemExit(main())
