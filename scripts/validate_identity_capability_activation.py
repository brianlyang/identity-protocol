#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml

from instance_script_orchestration_common import (
    STATUS_FAIL_REQUIRED as ORCHESTRATION_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED as ORCHESTRATION_PASS_REQUIRED,
    build_route_execution_lane_matrix,
    build_route_orchestration_matrix,
    clean_string_list,
    execution_lane_required as instance_script_execution_lane_required,
    load_manifest_doc,
    manifest_required as instance_script_manifest_required,
    normalize_source_layer,
    orchestration_required as instance_script_orchestration_required,
    route_uses_instance_scripts,
    route_uses_execution_lanes,
    validate_manifest_doc,
)
from resolve_identity_context import resolve_identity


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    catalog = _load_yaml(catalog_path)
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack = Path(str(row.get("pack_path", "")).strip()).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def _skill_candidates(skill: str, cwd: Path) -> list[Path]:
    names = [skill]
    # weak aliasing for system skill naming conventions.
    if skill.startswith("identity-"):
        names.append(skill.replace("identity-", "skill-", 1))
    roots = [
        cwd / "skills",
        cwd / ".codex" / "skills",
        cwd / ".." / "skills",
        cwd / ".." / ".codex" / "skills",
        cwd / "identity-protocol-local" / "skills",
        Path.home() / ".codex" / "skills",
        Path.home() / ".codex" / "skills" / ".system",
    ]
    out: list[Path] = []
    for root in roots:
        for n in names:
            if root.name == ".system":
                out.append((root / n / "SKILL.md").resolve())
            else:
                out.append((root / n / "SKILL.md").resolve())
                out.append((root / ".system" / n / "SKILL.md").resolve())
    # de-dup preserve order
    seen: set[str] = set()
    dedup: list[Path] = []
    for p in out:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        dedup.append(p)
    return dedup


def _find_skill(skill: str, cwd: Path) -> str:
    for p in _skill_candidates(skill, cwd):
        if p.exists():
            return str(p)
    return ""


def _load_mcp_servers(cwd: Path) -> dict[str, str]:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
    cfg_paths = [
        cwd / ".codex" / "config.toml",
        cwd / ".." / ".codex" / "config.toml",
        codex_home / "config.toml",
    ]
    servers: dict[str, str] = {}
    for cfg in cfg_paths:
        if not cfg.exists():
            continue
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            continue
        raw = data.get("mcp_servers") or {}
        if not isinstance(raw, dict):
            continue
        for name in raw.keys():
            servers[str(name)] = str(cfg)
    return servers


def _collect_contract(
    pack: Path,
    task_path: Path,
    *,
    identity_id: str,
    work_layer: str,
    source_layer: str,
) -> dict[str, Any]:
    task = _load_json(task_path)
    c = (task.get("capability_orchestration_contract") or {}) if isinstance(task, dict) else {}
    routes = c.get("task_type_routes") or {}
    required_skills: set[str] = set()
    required_mcp: set[str] = set()
    tool_routes: list[dict[str, Any]] = []
    for route_name, route in routes.items():
        if not isinstance(route, dict):
            continue
        route_skills: set[str] = set()
        route_mcp: set[str] = set()
        for s in route.get("primary_skills") or []:
            if str(s).strip():
                token = str(s).strip()
                required_skills.add(token)
                route_skills.add(token)
        for s in route.get("fallback_skills") or []:
            if str(s).strip():
                token = str(s).strip()
                required_skills.add(token)
                route_skills.add(token)
        for m in route.get("required_mcp") or []:
            if str(m).strip():
                token = str(m).strip()
                required_mcp.add(token)
                route_mcp.add(token)
        primary_instance_scripts = clean_string_list(route.get("primary_instance_scripts"))
        fallback_instance_scripts = clean_string_list(route.get("fallback_instance_scripts"))
        tool_routes.append(
            {
                "route": str(route_name),
                "pipeline": route.get("pipeline") or [],
                "max_tool_calls": route.get("max_tool_calls"),
                "max_runtime_minutes": route.get("max_runtime_minutes"),
                "required_skills": sorted(route_skills),
                "required_mcp": sorted(route_mcp),
                "uses_instance_scripts": route_uses_instance_scripts(route),
                "primary_instance_scripts": primary_instance_scripts,
                "fallback_instance_scripts": fallback_instance_scripts,
                "script_receipt_pattern": str(route.get("script_receipt_pattern", "")).strip(),
                "uses_execution_lanes": route_uses_execution_lanes(route),
                "allowed_execution_lanes": list(route.get("allowed_execution_lanes") or []),
                "lane_admission_policy": dict(route.get("lane_admission_policy") or {}),
                "lane_receipt_pattern": str(route.get("lane_receipt_pattern", "")).strip(),
                "lane_block_on_fallback": bool(route.get("lane_block_on_fallback")),
            }
        )
    manifest_path, manifest_doc = load_manifest_doc(pack)
    manifest_required = instance_script_manifest_required(task, pack)
    orchestration_required = instance_script_orchestration_required(task)
    execution_lane_required = instance_script_execution_lane_required(task)
    manifest_status = "SKIPPED_NOT_REQUIRED"
    orchestration_status = "SKIPPED_NOT_REQUIRED"
    execution_lane_status = "SKIPPED_NOT_REQUIRED"
    manifest_stale_reasons: list[str] = []
    orchestration_stale_reasons: list[str] = []
    execution_lane_stale_reasons: list[str] = []
    route_script_rows: list[dict[str, Any]] = []
    route_execution_lane_rows: list[dict[str, Any]] = []
    if manifest_required:
        if manifest_doc is None:
            manifest_status = ORCHESTRATION_FAIL_REQUIRED
            manifest_stale_reasons = ["manifest_missing"]
            if orchestration_required:
                orchestration_status = ORCHESTRATION_FAIL_REQUIRED
                orchestration_stale_reasons = ["manifest_missing_for_adopted_routes"]
            if execution_lane_required:
                execution_lane_status = ORCHESTRATION_FAIL_REQUIRED
                execution_lane_stale_reasons = ["manifest_missing_for_execution_lane_routes"]
        else:
            manifest_validation = validate_manifest_doc(
                manifest_doc=manifest_doc,
                manifest_path=manifest_path,
                pack_root=pack,
                identity_id=identity_id,
            )
            manifest_status = str(manifest_validation.get("status", "")).strip() or ORCHESTRATION_FAIL_REQUIRED
            manifest_stale_reasons = list(manifest_validation.get("stale_reasons") or [])
            if orchestration_required:
                if manifest_status == ORCHESTRATION_PASS_REQUIRED:
                    route_validation = build_route_orchestration_matrix(
                        task_doc=task,
                        manifest_validation=manifest_validation,
                        identity_id=identity_id,
                        work_layer=work_layer,
                        source_layer=source_layer,
                    )
                    orchestration_status = (
                        str(route_validation.get("status", "")).strip() or ORCHESTRATION_FAIL_REQUIRED
                    )
                    orchestration_stale_reasons = list(route_validation.get("stale_reasons") or [])
                    route_script_rows = list(route_validation.get("route_rows") or [])
                    if execution_lane_required:
                        lane_validation = build_route_execution_lane_matrix(
                            pack_root=pack,
                            task_doc=task,
                            manifest_validation=manifest_validation,
                            route_validation=route_validation,
                            identity_id=identity_id,
                            require_observed=False,
                        )
                        execution_lane_status = (
                            str(lane_validation.get("status", "")).strip() or ORCHESTRATION_FAIL_REQUIRED
                        )
                        execution_lane_stale_reasons = list(lane_validation.get("stale_reasons") or [])
                        route_execution_lane_rows = list(lane_validation.get("route_rows") or [])
                else:
                    orchestration_status = ORCHESTRATION_FAIL_REQUIRED
                    orchestration_stale_reasons = ["manifest_invalid_for_adopted_routes"]
                    if execution_lane_required:
                        execution_lane_status = ORCHESTRATION_FAIL_REQUIRED
                        execution_lane_stale_reasons = ["manifest_invalid_for_execution_lane_routes"]
    return {
        "required": bool(c.get("required", False)),
        "required_skills": sorted(required_skills),
        "required_mcp": sorted(required_mcp),
        "preflight_requirements": [str(x) for x in (c.get("preflight_requirements") or []) if str(x).strip()],
        "tool_routes": tool_routes,
        "pack_path": str(pack),
        "task_path": str(task_path),
        "instance_script_manifest_required": manifest_required,
        "instance_script_manifest_status": manifest_status,
        "instance_script_manifest_stale_reasons": manifest_stale_reasons,
        "instance_script_orchestration_required": orchestration_required,
        "instance_script_orchestration_status": orchestration_status,
        "instance_script_orchestration_stale_reasons": orchestration_stale_reasons,
        "route_script_rows": route_script_rows,
        "instance_script_execution_lane_required": execution_lane_required,
        "instance_script_execution_lane_status": execution_lane_status,
        "instance_script_execution_lane_stale_reasons": execution_lane_stale_reasons,
        "route_execution_lane_rows": route_execution_lane_rows,
        "manifest_path": str(manifest_path),
    }


def _check_gh_cli() -> bool:
    return shutil.which("gh") is not None


def _check_gh_auth_status() -> tuple[bool, str]:
    """
    Returns:
      (auth_ready, detail_reason)
    """
    if not _check_gh_cli():
        return False, "gh_cli_missing"
    cmds = [
        ["gh", "auth", "status", "-h", "github.com"],
        ["gh", "auth", "status"],
    ]
    for cmd in cmds:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            return False, "gh_cli_missing"
        msg = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip().lower()
        if "failed to log in" in msg:
            return False, "gh_auth_invalid"
        if "invalid" in msg:
            return False, "gh_auth_invalid"
        if "not logged into any hosts" in msg or "run: gh auth login" in msg:
            return False, "gh_auth_missing"
        if proc.returncode == 0:
            return True, "gh_auth_ready"
    return False, "gh_auth_not_ready"


def _derive_activation_mode(catalog: Path) -> str:
    p = str(catalog)
    if "/.codex/.identity/" in p:
        return "global"
    if "/.identity/" in p:
        return "project"
    if "/.agents/identity/" in p:
        return "legacy_project"
    # Legacy forbidden root kept for migration detection.
    if "/.codex/identity/" in p:
        return "legacy_global"
    return "unknown"


def _aggregate_lane_rows(route_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not route_rows:
        return {
            "execution_lane_contract_status": "SKIPPED_NOT_REQUIRED",
            "execution_lane_receipt_status": "SKIPPED_NOT_REQUIRED",
            "execution_lane_diagnostic_label": "",
            "execution_lane_diagnostic_labels": [],
            "execution_lane_stale_reasons": [],
            "execution_lane_scripts": [],
            "execution_lane_ready": True,
        }

    contract_statuses = [
        str(row.get("lane_contract_status", "")).strip() or "SKIPPED_NOT_REQUIRED"
        for row in route_rows
    ]
    receipt_statuses = [
        str(row.get("lane_receipt_validation_status", "")).strip() or "SKIPPED_NOT_REQUIRED"
        for row in route_rows
    ]
    diagnostic_labels = [
        str(row.get("diagnostic_label", "")).strip()
        for row in route_rows
        if str(row.get("diagnostic_label", "")).strip()
    ]
    stale_reasons: list[str] = []
    for row in route_rows:
        for reason in (row.get("stale_reasons") or []):
            token = str(reason).strip()
            if token:
                stale_reasons.append(token)

    def _merge_status(statuses: list[str]) -> str:
        if any(status == ORCHESTRATION_FAIL_REQUIRED for status in statuses):
            return ORCHESTRATION_FAIL_REQUIRED
        if any(status == ORCHESTRATION_PASS_REQUIRED for status in statuses):
            return ORCHESTRATION_PASS_REQUIRED
        return "SKIPPED_NOT_REQUIRED"

    merged_contract_status = _merge_status(contract_statuses)
    merged_receipt_status = _merge_status(receipt_statuses)
    route_ready = (
        merged_contract_status != ORCHESTRATION_FAIL_REQUIRED
        and merged_receipt_status != ORCHESTRATION_FAIL_REQUIRED
    )
    preferred_label = ""
    if not route_ready:
        preferred_label = next(
            (
                str(row.get("diagnostic_label", "")).strip()
                for row in route_rows
                if str(row.get("lane_receipt_validation_status", "")).strip() == ORCHESTRATION_FAIL_REQUIRED
                and str(row.get("diagnostic_label", "")).strip()
            ),
            diagnostic_labels[0] if diagnostic_labels else "",
        )
    elif any(label == "ready" for label in diagnostic_labels):
        preferred_label = "ready"
    elif diagnostic_labels:
        preferred_label = diagnostic_labels[0]

    return {
        "execution_lane_contract_status": merged_contract_status,
        "execution_lane_receipt_status": merged_receipt_status,
        "execution_lane_diagnostic_label": preferred_label,
        "execution_lane_diagnostic_labels": diagnostic_labels,
        "execution_lane_stale_reasons": sorted(set(stale_reasons)),
        "execution_lane_scripts": [
            str(row.get("script_id", "")).strip()
            for row in route_rows
            if str(row.get("script_id", "")).strip()
        ],
        "execution_lane_ready": route_ready,
    }


def _build_runtime_payload(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    work_layer: str,
    source_layer: str,
    activation_policy: str = "strict-union",
) -> dict[str, Any]:
    pack, task_path = _resolve_current_task(catalog_path, identity_id)
    resolved_source_layer = str(source_layer or "").strip().lower() or normalize_source_layer(catalog_path)
    contract = _collect_contract(
        pack,
        task_path,
        identity_id=identity_id,
        work_layer=str(work_layer or "instance").strip().lower() or "instance",
        source_layer=resolved_source_layer,
    )
    cwd = Path.cwd().resolve()
    skill_rows: list[dict[str, Any]] = []
    active_skills: list[str] = []
    missing_skills: list[str] = []
    for skill in contract["required_skills"]:
        found = _find_skill(skill, cwd)
        row = {"skill": skill, "available": bool(found), "path": found}
        skill_rows.append(row)
        if found:
            active_skills.append(skill)
        else:
            missing_skills.append(skill)

    mcp_servers = _load_mcp_servers(cwd)
    gh_cli_present = _check_gh_cli()
    gh_auth_ready, gh_auth_reason = _check_gh_auth_status()
    mcp_rows: list[dict[str, Any]] = []
    mcp_tools_used: list[str] = []
    missing_mcp: list[str] = []
    missing_mcp_auth: list[str] = []
    mcp_ok_map: dict[str, bool] = {}
    for name in contract["required_mcp"]:
        ok = False
        reason = ""
        source = ""
        if name == "github":
            source = mcp_servers.get(name, "gh_cli" if gh_cli_present else "")
            if gh_auth_ready:
                ok = True
                reason = "github_auth_ready"
            else:
                ok = False
                reason = f"github_auth_not_ready:{gh_auth_reason}"
                missing_mcp_auth.append(name)
        elif name in mcp_servers:
            ok = True
            source = mcp_servers[name]
            reason = "configured_in_codex_config"
        else:
            reason = "not_configured"
        row = {"mcp": name, "available": ok, "source": source, "reason": reason}
        mcp_rows.append(row)
        mcp_ok_map[name] = ok
        if ok:
            mcp_tools_used.append(name)
        else:
            missing_mcp.append(name)

    skill_ok_map = {row["skill"]: bool(row["available"]) for row in skill_rows}
    route_activation_matrix: list[dict[str, Any]] = []
    route_ready_count = 0
    route_script_rows = {
        str(row.get("route", "")).strip(): row
        for row in (contract.get("route_script_rows") or [])
        if str(row.get("route", "")).strip()
    }
    route_execution_lane_rows: dict[str, list[dict[str, Any]]] = {}
    for row in (contract.get("route_execution_lane_rows") or []):
        route_name = str(row.get("route", "")).strip()
        if not route_name:
            continue
        route_execution_lane_rows.setdefault(route_name, []).append(dict(row))
    for route in contract["tool_routes"]:
        route_name = str(route.get("route", "")).strip()
        route_skills = [str(x).strip() for x in (route.get("required_skills") or []) if str(x).strip()]
        route_mcp = [str(x).strip() for x in (route.get("required_mcp") or []) if str(x).strip()]
        route_missing_skills = [s for s in route_skills if not skill_ok_map.get(s, False)]
        route_missing_mcp = [m for m in route_mcp if not mcp_ok_map.get(m, False)]
        route_script_row = route_script_rows.get(route_name, {})
        route_execution_lane_rowset = route_execution_lane_rows.get(route_name, [])
        lane_summary = _aggregate_lane_rows(route_execution_lane_rowset)
        route_uses_instance_scripts = bool(route.get("uses_instance_scripts"))
        route_uses_execution_lanes = bool(route.get("uses_execution_lanes"))
        route_missing_script_ids = [
            str(x).strip()
            for x in (route_script_row.get("missing_script_ids") or [])
            if str(x).strip()
        ]
        script_preconditions_status = str(route_script_row.get("script_preconditions_status", "")).strip()
        route_script_ready = (
            not route_uses_instance_scripts
            or str(route_script_row.get("route_ready", "")).strip().lower() == "true"
            or route_script_row.get("route_ready") is True
        )
        route_ready = (
            not route_missing_skills
            and not route_missing_mcp
            and route_script_ready
            and (not route_uses_execution_lanes or bool(lane_summary.get("execution_lane_ready")))
        )
        if route_ready:
            route_ready_count += 1
        route_activation_matrix.append(
            {
                "route": route_name,
                "required_skills": route_skills,
                "required_mcp": route_mcp,
                "missing_skills": route_missing_skills,
                "missing_mcp": route_missing_mcp,
                "uses_instance_scripts": route_uses_instance_scripts,
                "primary_instance_scripts": list(route.get("primary_instance_scripts") or []),
                "fallback_instance_scripts": list(route.get("fallback_instance_scripts") or []),
                "missing_script_ids": route_missing_script_ids,
                "script_receipt_pattern": str(route.get("script_receipt_pattern", "")).strip(),
                "uses_execution_lanes": route_uses_execution_lanes,
                "allowed_execution_lanes": list(route.get("allowed_execution_lanes") or []),
                "lane_admission_policy": dict(route.get("lane_admission_policy") or {}),
                "lane_receipt_pattern": str(route.get("lane_receipt_pattern", "")).strip(),
                "lane_block_on_fallback": bool(route.get("lane_block_on_fallback")),
                "execution_lane_rows": route_execution_lane_rowset,
                "execution_lane_scripts": list(lane_summary.get("execution_lane_scripts") or []),
                "script_preconditions_status": script_preconditions_status or "SKIPPED_NOT_REQUIRED",
                "script_route_contract_status": str(
                    route_script_row.get("route_contract_status", "SKIPPED_NOT_REQUIRED")
                ).strip(),
                "script_manifest_binding_status": str(
                    route_script_row.get("manifest_binding_status", "SKIPPED_NOT_REQUIRED")
                ).strip(),
                "execution_lane_contract_status": str(
                    lane_summary.get("execution_lane_contract_status", "SKIPPED_NOT_REQUIRED")
                ).strip(),
                "execution_lane_receipt_status": str(
                    lane_summary.get("execution_lane_receipt_status", "SKIPPED_NOT_REQUIRED")
                ).strip(),
                "execution_lane_diagnostic_label": str(
                    lane_summary.get("execution_lane_diagnostic_label", "")
                ).strip(),
                "execution_lane_diagnostic_labels": list(
                    lane_summary.get("execution_lane_diagnostic_labels") or []
                ),
                "execution_lane_stale_reasons": list(lane_summary.get("execution_lane_stale_reasons") or []),
                "script_diagnostic_label": str(route_script_row.get("diagnostic_label", "")).strip(),
                "script_stale_reasons": list(route_script_row.get("stale_reasons") or []),
                "ready": route_ready,
            }
        )

    status = "ACTIVATED"
    error_code = ""
    notes: list[str] = []
    policy = str(activation_policy or "strict-union").strip().lower()
    if policy == "route-any-ready" and route_activation_matrix:
        if route_ready_count == 0:
            status = "BLOCKED"
            error_code = "IP-CAP-004"
            notes.append("no_route_ready")
            if missing_skills:
                error_code = "IP-CAP-001"
                notes.append(f"missing_skills={missing_skills}")
            if missing_mcp:
                error_code = "IP-CAP-002"
                notes.append(f"missing_mcp={missing_mcp}")
            if missing_mcp_auth:
                error_code = "IP-CAP-003"
                notes.append(f"mcp_auth_not_ready={missing_mcp_auth}")
        elif route_ready_count < len(route_activation_matrix):
            notes.append(f"route_partial_ready={route_ready_count}/{len(route_activation_matrix)}")
            if missing_mcp_auth:
                notes.append(f"mcp_auth_not_ready_for_non_primary_routes={missing_mcp_auth}")
    else:
        if missing_skills:
            status = "BLOCKED"
            error_code = "IP-CAP-001"
            notes.append(f"missing_skills={missing_skills}")
        if missing_mcp:
            status = "BLOCKED"
            error_code = "IP-CAP-002"
            notes.append(f"missing_mcp={missing_mcp}")
        if missing_mcp_auth:
            status = "BLOCKED"
            error_code = "IP-CAP-003"
            notes.append(f"mcp_auth_not_ready={missing_mcp_auth}")
    if bool(contract.get("instance_script_orchestration_required")) and str(
        contract.get("instance_script_orchestration_status", "")
    ).strip() != ORCHESTRATION_PASS_REQUIRED:
        status = "BLOCKED"
        error_code = "IP-CAP-005"
        notes.append(
            "instance_script_orchestration_not_ready="
            + ",".join(str(x).strip() for x in (contract.get("instance_script_orchestration_stale_reasons") or []) if str(x).strip())
        )
    if bool(contract.get("instance_script_execution_lane_required")) and str(
        contract.get("instance_script_execution_lane_status", "")
    ).strip() != ORCHESTRATION_PASS_REQUIRED:
        status = "BLOCKED"
        error_code = "IP-CAP-006"
        notes.append(
            "instance_script_execution_lane_not_ready="
            + ",".join(
                str(x).strip()
                for x in (contract.get("instance_script_execution_lane_stale_reasons") or [])
                if str(x).strip()
            )
        )
    if not contract["required"]:
        status = "NOT_REQUIRED"
        error_code = ""
    ctx = resolve_identity(
        identity_id,
        repo_catalog_path.expanduser().resolve(),
        catalog_path.expanduser().resolve(),
        allow_conflict=True,
    )
    return {
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack),
        "task_path": str(task_path),
        "resolved_scope": str(ctx.get("resolved_scope", "")),
        "resolved_pack_path": str(ctx.get("resolved_pack_path", "")),
        "activation_mode": _derive_activation_mode(catalog_path),
        "preflight_requirements_checked": contract["preflight_requirements"],
        "required_skills": contract["required_skills"],
        "required_mcp": contract["required_mcp"],
        "github_cli_present": gh_cli_present,
        "github_auth_ready": gh_auth_ready,
        "github_auth_status_detail": gh_auth_reason,
        "skills_checked": skill_rows,
        "active_skills": active_skills,
        "mcp_servers_checked": mcp_rows,
        "mcp_servers": sorted(mcp_servers.keys()),
        "skills_used": active_skills,
        "mcp_tools_used": mcp_tools_used,
        "tool_calls_used": ["validate_identity_capability_activation"],
        "tool_routes": contract["tool_routes"],
        "route_script_rows": list(contract.get("route_script_rows") or []),
        "route_execution_lane_rows": list(contract.get("route_execution_lane_rows") or []),
        "route_activation_strategy": policy,
        "route_activation_matrix": route_activation_matrix,
        "route_ready_count": route_ready_count,
        "route_total_count": len(route_activation_matrix),
        "instance_script_manifest_required": bool(contract.get("instance_script_manifest_required")),
        "instance_script_manifest_status": str(contract.get("instance_script_manifest_status", "")).strip(),
        "instance_script_manifest_stale_reasons": list(
            contract.get("instance_script_manifest_stale_reasons") or []
        ),
        "instance_script_orchestration_required": bool(
            contract.get("instance_script_orchestration_required")
        ),
        "instance_script_orchestration_status": str(
            contract.get("instance_script_orchestration_status", "")
        ).strip(),
        "instance_script_orchestration_stale_reasons": list(
            contract.get("instance_script_orchestration_stale_reasons") or []
        ),
        "instance_script_execution_lane_required": bool(
            contract.get("instance_script_execution_lane_required")
        ),
        "instance_script_execution_lane_status": str(
            contract.get("instance_script_execution_lane_status", "")
        ).strip(),
        "instance_script_execution_lane_stale_reasons": list(
            contract.get("instance_script_execution_lane_stale_reasons") or []
        ),
        "instance_script_manifest_path": str(contract.get("manifest_path", "")).strip(),
        "capability_contract_required": bool(contract.get("required", False)),
        "capability_activation_status": status,
        "capability_activation_error_code": error_code,
        "capability_activation_notes": notes,
    }


def _validate_report(path: Path, require_activated: bool) -> tuple[bool, str]:
    data = _load_json(path)
    required = [
        "skills_used",
        "mcp_tools_used",
        "tool_calls_used",
        "active_skills",
        "mcp_servers_checked",
        "tool_routes",
        "capability_activation_status",
        "capability_activation_error_code",
        "capability_contract_required",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"report_missing_fields:{missing}"
    status = str(data.get("capability_activation_status", "")).strip().upper()
    if require_activated and status != "ACTIVATED":
        return False, f"capability_activation_status_not_activated:{status}"
    if not isinstance(data.get("skills_used"), list):
        return False, "skills_used_must_be_list"
    if not isinstance(data.get("mcp_tools_used"), list):
        return False, "mcp_tools_used_must_be_list"
    if not isinstance(data.get("tool_calls_used"), list):
        return False, "tool_calls_used_must_be_list"
    if not isinstance(data.get("active_skills"), list):
        return False, "active_skills_must_be_list"
    if not isinstance(data.get("mcp_servers_checked"), list):
        return False, "mcp_servers_checked_must_be_list"
    if not isinstance(data.get("tool_routes"), list):
        return False, "tool_routes_must_be_list"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity capability activation (skill/mcp/tool attachment preflight).")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument("--require-activated", action="store_true")
    ap.add_argument(
        "--activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
        help="strict-union blocks when any required capability is unavailable; route-any-ready allows activation when at least one route is ready.",
    )
    ap.add_argument("--work-layer", default="instance")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.report.strip():
        report_path = Path(args.report).expanduser().resolve()
        if not report_path.exists():
            print(f"[FAIL] report not found: {report_path}")
            return 1
        ok, reason = _validate_report(report_path, require_activated=bool(args.require_activated))
        if not ok:
            print(f"[FAIL] {reason}")
            return 1
        print(f"[OK] capability activation report validated: {report_path}")
        return 0

    if not args.catalog.strip():
        print("[FAIL] --catalog is required when validating live capability activation (non-report mode)")
        return 1
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()

    try:
        payload = _build_runtime_payload(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            work_layer=args.work_layer,
            source_layer=args.source_layer,
            activation_policy=args.activation_policy,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if args.out.strip():
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = str(payload.get("capability_activation_status", "BLOCKED"))
    if args.require_activated and status != "ACTIVATED":
        print(f"[FAIL] capability activation not ready: status={status} error={payload.get('capability_activation_error_code')}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if status in {"BLOCKED", "ERROR"}:
        print(f"[WARN] capability activation not fully ready: status={status} error={payload.get('capability_activation_error_code')}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"[OK] capability activation validated: identity={args.identity_id} status={status}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
