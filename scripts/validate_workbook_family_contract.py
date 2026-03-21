#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from workbook_control_plane_common import (
    MINOR_FAMILY_UNIQUENESS_EXACT_CANONICAL_PAIR_ONLY,
    PROJECTION_BOUNDARY_MARKER,
    PROJECTION_MODE_MIRROR_ONLY,
    WORKBOOK_CONTROL_PLANE_CONTRACT,
    WorkbookTemplateContract,
    load_active_workbook_registry,
    resolve_workbook_roots,
    unresolved_template_tokens,
    validate_minor_family_token,
    workbook_family_layout,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CONTRACT_DISCOVERY = "IP-WFVC-001"
ERR_FAMILY_LAYOUT = "IP-WFVC-002"
ERR_PROJECTION_STUB = "IP-WFVC-003"
ERR_ACTIVATION_BOUNDARY = "IP-WFVC-004"

def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"yaml root must be mapping: {path}")
    return doc


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _repo_rel(repo_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(repo_root))


def _validate_markdown_doc(
    *,
    repo_root: Path,
    path: Path,
    required_markers: list[str],
    violations: list[str],
    violation_prefix: str,
) -> None:
    if not path.exists():
        violations.append(f"{violation_prefix}_missing:{_repo_rel(repo_root, path)}")
        return
    text = path.read_text(encoding="utf-8")
    for marker in required_markers:
        if marker not in text:
            violations.append(f"{violation_prefix}_marker_missing:{_repo_rel(repo_root, path)}:{marker}")
    unresolved = unresolved_template_tokens(text)
    if unresolved:
        violations.append(
            f"{violation_prefix}_unresolved_placeholders:{_repo_rel(repo_root, path)}:{','.join(unresolved)}"
        )


def _validate_projection_stub(
    *,
    path: Path,
    authority_doc_rel: str,
    current_pointer_rel: str,
    family_registry_rel: str,
    repo_name: str,
    violations: list[str],
) -> None:
    if not path.exists():
        violations.append(f"projection_stub_missing:{path}")
        return
    text = path.read_text(encoding="utf-8")
    required_markers = [
        PROJECTION_MODE_MIRROR_ONLY,
        PROJECTION_BOUNDARY_MARKER,
        f"Projection source: `{repo_name}/{authority_doc_rel}`",
        f"Workbook registry source: `{repo_name}/{current_pointer_rel}`",
        f"Activation candidate registry: `{repo_name}/{family_registry_rel}`",
    ]
    for marker in required_markers:
        if marker not in text:
            violations.append(f"projection_stub_marker_missing:{path}:{marker}")
    unresolved = unresolved_template_tokens(text)
    if unresolved:
        violations.append(f"projection_stub_unresolved_placeholders:{path}:{','.join(unresolved)}")


def _compare_template_contract(
    *,
    expected: WorkbookTemplateContract,
    actual: dict[str, Any],
    violations: list[str],
) -> None:
    comparable = {
        "contract_id": expected.contract_id,
        "template_dir": expected.template_dir_rel,
        "templates_readme": expected.templates_readme_rel,
        "issue_register_template": expected.issue_register_template_rel,
        "deep_audit_template": expected.deep_audit_template_rel,
        "scaffold_script": expected.scaffold_script_rel,
        "contract_validator": expected.contract_validator_rel,
        "scaffold_projection_root": expected.scaffold_projection_root_rel,
        "projection_policy": expected.projection_policy,
        "projection_presence_policy": expected.projection_presence_policy,
        "projection_freshness_mode": expected.projection_freshness_mode,
        "current_pointer_activation_mode": expected.current_pointer_activation_mode,
        "current_pointer_activation_consent_token": expected.current_pointer_activation_consent_token,
        "governance_doc": expected.governance_doc_rel,
        "workbook_registry_current_ref": expected.workbook_registry_current_ref,
        "stream_doc_registry_ref": expected.stream_doc_registry_ref,
        "control_plane_status_ref": expected.control_plane_status_ref,
    }
    for key, expected_value in comparable.items():
        if _norm(actual.get(key)) != expected_value:
            violations.append(f"template_contract_mismatch:{key}:expected={expected_value}:recorded={_norm(actual.get(key))}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scaffolded workbook family contract.")
    parser.add_argument("--minor", required=True)
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--workspace-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "minor": "",
        "repo_root": "",
        "workspace_root": "",
        "active_family": "",
        "layout": {},
        "violations": [],
    }

    try:
        repo_root, workspace_root = resolve_workbook_roots(args.repo_root, args.workspace_root, start=__file__)
        minor = validate_minor_family_token(args.minor)
        registry_bundle = load_active_workbook_registry(repo_root)
        layout = workbook_family_layout(minor, template_contract=registry_bundle.template_contract)
        target_registry_path = (repo_root / layout.registry_doc_rel).resolve()
        target_registry_doc = _load_yaml(target_registry_path)
        active_family = _norm(registry_bundle.active_family_doc.get("workbook_family"))
    except Exception as exc:
        payload["error_code"] = ERR_CONTRACT_DISCOVERY
        payload["violations"] = [f"contract_discovery:{type(exc).__name__}:{exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["minor"] = minor
    payload["repo_root"] = str(repo_root)
    payload["workspace_root"] = str(workspace_root)
    payload["active_family"] = active_family
    payload["layout"] = {
        "issue_register_doc": layout.issue_register_doc_rel,
        "deep_audit_doc": layout.deep_audit_doc_rel,
        "registry_doc": layout.registry_doc_rel,
        "issue_register_projection": layout.issue_register_projection_rel,
        "deep_audit_projection": layout.deep_audit_projection_rel,
    }

    violations: list[str] = []
    if _norm(target_registry_doc.get("version")) != minor:
        violations.append(f"registry_version_mismatch:expected={minor}:recorded={_norm(target_registry_doc.get('version'))}")
    if _norm(target_registry_doc.get("control_plane_contract")) != WORKBOOK_CONTROL_PLANE_CONTRACT:
        violations.append("registry_control_plane_contract_mismatch")

    template_contract_doc = target_registry_doc.get("template_contract")
    if not isinstance(template_contract_doc, dict):
        violations.append("template_contract_missing")
    else:
        _compare_template_contract(
            expected=registry_bundle.template_contract,
            actual=template_contract_doc,
            violations=violations,
        )

    active_family_doc = target_registry_doc.get("active_workbook_family")
    if not isinstance(active_family_doc, dict):
        violations.append("active_workbook_family_missing")
    else:
        if _norm(active_family_doc.get("workbook_family")) != minor:
            violations.append(
                f"active_family_mismatch:expected={minor}:recorded={_norm(active_family_doc.get('workbook_family'))}"
            )
        authority_surfaces = active_family_doc.get("authority_surfaces")
        if not isinstance(authority_surfaces, dict):
            violations.append("authority_surfaces_missing")
        else:
            if _norm(authority_surfaces.get("issue_register_doc")) != layout.issue_register_doc_rel:
                violations.append("authority_surfaces_issue_register_doc_path_mismatch")
            if _norm(authority_surfaces.get("deep_audit_workbook_doc")) != layout.deep_audit_doc_rel:
                violations.append("authority_surfaces_deep_audit_doc_path_mismatch")
        if _norm(active_family_doc.get("issue_register_doc")) != layout.issue_register_doc_rel:
            violations.append("issue_register_doc_path_mismatch")
        if _norm(active_family_doc.get("deep_audit_workbook_doc")) != layout.deep_audit_doc_rel:
            violations.append("deep_audit_doc_path_mismatch")
        if _norm(active_family_doc.get("governance_doc")) != registry_bundle.template_contract.governance_doc_rel:
            violations.append("governance_doc_path_mismatch")
        if _norm(active_family_doc.get("minor_family_uniqueness_mode")) != MINOR_FAMILY_UNIQUENESS_EXACT_CANONICAL_PAIR_ONLY:
            violations.append("minor_family_uniqueness_mode_mismatch")
        if _norm(active_family_doc.get("projection_policy")) != registry_bundle.template_contract.projection_policy:
            violations.append("projection_policy_mismatch")
        projections = active_family_doc.get("projection_exports") or []
        if not isinstance(projections, list) or len(projections) != 2:
            violations.append("projection_exports_shape_mismatch")
        else:
            expected_rows = {
                "issue_register_projection": (
                    layout.issue_register_projection_rel,
                    layout.issue_register_doc_rel,
                ),
                "deep_audit_projection": (
                    layout.deep_audit_projection_rel,
                    layout.deep_audit_doc_rel,
                ),
            }
            for row in projections:
                if not isinstance(row, dict):
                    violations.append("projection_export_row_invalid")
                    continue
                role = _norm(row.get("projection_role"))
                expected = expected_rows.get(role)
                if expected is None:
                    violations.append(f"projection_export_unknown_role:{role}")
                    continue
                if _norm(row.get("path")) != expected[0]:
                    violations.append(f"projection_export_path_mismatch:{role}")
                if _norm(row.get("authority_doc")) != expected[1]:
                    violations.append(f"projection_export_authority_doc_mismatch:{role}")
                if _norm(row.get("presence_policy")) != registry_bundle.template_contract.projection_presence_policy:
                    violations.append(f"projection_export_presence_policy_mismatch:{role}")
                if _norm(row.get("freshness_mode")) != registry_bundle.template_contract.projection_freshness_mode:
                    violations.append(f"projection_export_freshness_mode_mismatch:{role}")

    issue_register_doc = (repo_root / layout.issue_register_doc_rel).resolve()
    deep_audit_doc = (repo_root / layout.deep_audit_doc_rel).resolve()
    _validate_markdown_doc(
        repo_root=repo_root,
        path=issue_register_doc,
        required_markers=[
            f"Identity Protocol {minor} Issue Register",
            f"`{registry_bundle.template_contract.workbook_registry_current_ref}`",
            f"`{registry_bundle.template_contract.stream_doc_registry_ref}`",
            f"`{registry_bundle.template_contract.control_plane_status_ref}`",
            "| Issue | Status | Primary owner lane | Current closure anchor | Freeze rule |",
        ],
        violations=violations,
        violation_prefix="issue_register_doc",
    )
    _validate_markdown_doc(
        repo_root=repo_root,
        path=deep_audit_doc,
        required_markers=[
            f"Identity Protocol {minor} Deep Audit Workbook",
            f"`{registry_bundle.template_contract.workbook_registry_current_ref}`",
            f"`{registry_bundle.template_contract.stream_doc_registry_ref}`",
            f"`{registry_bundle.template_contract.control_plane_status_ref}`",
            "### RC-01 Pending intake cluster",
        ],
        violations=violations,
        violation_prefix="deep_audit_doc",
    )

    _validate_projection_stub(
        path=(workspace_root / layout.issue_register_projection_rel).resolve(),
        authority_doc_rel=layout.issue_register_doc_rel,
        current_pointer_rel=registry_bundle.template_contract.workbook_registry_current_ref,
        family_registry_rel=layout.registry_doc_rel,
        repo_name=repo_root.name,
        violations=violations,
    )
    _validate_projection_stub(
        path=(workspace_root / layout.deep_audit_projection_rel).resolve(),
        authority_doc_rel=layout.deep_audit_doc_rel,
        current_pointer_rel=registry_bundle.template_contract.workbook_registry_current_ref,
        family_registry_rel=layout.registry_doc_rel,
        repo_name=repo_root.name,
        violations=violations,
    )

    current_pointer_doc = _load_yaml(registry_bundle.current_path)
    current_active_file = _norm(current_pointer_doc.get("active_file"))
    current_active_family = _norm(current_pointer_doc.get("active_family"))
    if minor != active_family:
        if current_active_family == minor or current_active_file == layout.registry_doc_rel:
            violations.append("current_pointer_changed_without_activation")

    payload["violations"] = violations
    if violations:
        payload["error_code"] = (
            ERR_ACTIVATION_BOUNDARY
            if any("current_pointer" in item for item in violations)
            else ERR_PROJECTION_STUB
            if any(item.startswith("projection_") for item in violations)
            else ERR_FAMILY_LAYOUT
        )
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["status"] = STATUS_PASS_REQUIRED
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
