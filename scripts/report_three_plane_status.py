#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _tracked_worktree_state() -> tuple[bool, list[str], str]:
    rc, out, err = _run(["git", "status", "--porcelain"])
    if rc != 0:
        return False, [], (err or out or "git_status_failed")
    rows = [ln for ln in out.splitlines() if ln.strip()]
    tracked_dirty = [ln for ln in rows if not ln.startswith("??")]
    return len(tracked_dirty) == 0, tracked_dirty[:20], ""


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_json(path: str) -> dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"json file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _latest_report(identity_id: str, identity_home: str = "", preferred_pack: str = "") -> Path | None:
    roots: list[Path] = []
    if preferred_pack.strip():
        pack = Path(preferred_pack).expanduser().resolve()
        roots.append(pack / "runtime" / "reports")
        roots.append(pack / "runtime")
    roots.extend(
        [
            Path("/tmp/identity-upgrade-reports"),
            Path("/tmp/identity-runtime"),
        ]
    )
    if identity_home.strip():
        roots.append(Path(identity_home).expanduser().resolve())
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(root.glob(f"**/identity-upgrade-exec-{identity_id}-*.json"))
    filtered = [p for p in candidates if not p.name.endswith("-patch-plan.json")]
    if not filtered:
        return None
    filtered.sort(key=lambda p: p.stat().st_mtime)
    return filtered[-1]


def _release_plane_status(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if args.checks_json:
        checks_doc = _load_json(args.checks_json)
        raw = checks_doc.get("required_checks_set", [])
        if isinstance(raw, list):
            checks = [x for x in raw if isinstance(x, dict)]

    if not args.required_gates_run_id:
        detail = {
            "conditions": {
                "target_branch_explicit": bool(args.target_branch),
                "release_head_sha_explicit": bool(args.release_head_sha),
                "required_gates_run_id_accessible": False,
                "run_head_matches_release_head": False,
                "required_checks_all_success": False,
                "workflow_file_sha_matches": False,
            },
            "required_checks_set": checks,
        }
        return "NOT_STARTED", detail

    cond = {
        "target_branch_explicit": bool(args.target_branch),
        "release_head_sha_explicit": bool(args.release_head_sha),
        "required_gates_run_id_accessible": bool(args.required_gates_run_id and args.run_url),
        "run_head_matches_release_head": args.run_head_sha == args.release_head_sha and bool(args.run_head_sha),
        "required_checks_all_success": bool(checks) and all(str(x.get("status", "")).lower() == "success" for x in checks),
        "workflow_file_sha_matches": args.run_workflow_file_sha == args.workflow_file_sha and bool(args.workflow_file_sha),
    }
    return ("CLOSED" if all(cond.values()) else "BLOCKED"), {"conditions": cond, "required_checks_set": checks}


def _repo_plane_status(args: argparse.Namespace, resolved: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    workspace_clean, workspace_dirty_entries, workspace_status_error = _tracked_worktree_state()
    checks: dict[str, Any] = {
        "catalog_explicit": bool(args.catalog and Path(args.catalog).exists()),
        "resolved_scope_known": str(resolved.get("resolved_scope", "")).upper() != "UNKNOWN",
        "conflict_detected": bool(resolved.get("conflict_detected", False)),
        "workspace_clean": workspace_clean,
        "workspace_dirty_entries": workspace_dirty_entries,
        "workspace_status_error": workspace_status_error,
    }
    if args.with_docs_contract:
        rc, out, err = _run(["python3", "scripts/docs_command_contract_check.py"])
        checks["docs_command_contract"] = {
            "rc": rc,
            "ok": rc == 0,
            "stdout_tail": out.splitlines()[-1] if out else "",
            "stderr_tail": err.splitlines()[-1] if err else "",
        }
    status = "CLOSED"
    if checks["conflict_detected"]:
        status = "BLOCKED"
    if not checks["catalog_explicit"] or not checks["resolved_scope_known"]:
        status = "BLOCKED"
    if not checks["workspace_clean"] or checks["workspace_status_error"]:
        status = "BLOCKED"
    if args.with_docs_contract and not checks["docs_command_contract"]["ok"]:
        status = "BLOCKED"
    return status, checks


def _instance_plane_status(args: argparse.Namespace, report_path: Path | None) -> tuple[str, dict[str, Any]]:
    if report_path is None:
        return "NOT_STARTED", {"reason": "execution_report_not_found"}

    data = _load_json(str(report_path))
    ew = data.get("experience_writeback") or {}
    mandatory = all(
        k in data
        for k in (
            "permission_state",
            "writeback_status",
            "next_action",
            "skills_used",
            "mcp_tools_used",
            "tool_calls_used",
            "capability_activation_status",
            "capability_activation_error_code",
        )
    ) and isinstance(ew, dict) and (
        "status" in ew and "error_code" in ew
    )
    wb = str(data.get("writeback_status", "")).strip()
    ps = str(data.get("permission_state", "")).strip()
    all_ok = _bool(data.get("all_ok", False))
    err_code = str((ew.get("error_code", "") or data.get("permission_error_code", ""))).strip()
    next_action = str(data.get("next_action", "")).strip()
    cap_status = str(data.get("capability_activation_status", "")).strip().upper()
    cap_error = str(data.get("capability_activation_error_code", "")).strip()
    hard_boundary = err_code.startswith("IP-PATH-") or err_code.startswith("IP-PERM-")

    validators: dict[str, Any] = {}
    # Always validate tuple and writeback linkage to keep evidence machine-checkable.
    rc_tuple, out_tuple, err_tuple = _run(
        ["python3", "scripts/validate_identity_binding_tuple.py", "--identity-id", args.identity_id, "--report", str(report_path)]
    )
    validators["binding_tuple"] = {"rc": rc_tuple, "ok": rc_tuple == 0, "out": out_tuple, "err": err_tuple}

    rc_wb, out_wb, err_wb = _run(
        [
            "python3",
            "scripts/validate_identity_experience_writeback.py",
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--local-catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
            "--execution-report",
            str(report_path),
        ]
    )
    validators["experience_writeback"] = {"rc": rc_wb, "ok": rc_wb == 0, "out": out_wb, "err": err_wb}

    perm_cmd = ["python3", "scripts/validate_identity_permission_state.py", "--identity-id", args.identity_id, "--report", str(report_path), "--ci"]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        perm_cmd.append("--require-written")
    rc_perm, out_perm, err_perm = _run(perm_cmd)
    validators["permission_state"] = {"rc": rc_perm, "ok": rc_perm == 0, "out": out_perm, "err": err_perm}

    rc_session, out_session, err_session = _run(
        [
            "python3",
            "scripts/validate_identity_session_pointer_consistency.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["session_pointer"] = {
        "rc": rc_session,
        "ok": rc_session == 0,
        "out": out_session,
        "err": err_session,
    }

    rc_home_align, out_home_align, err_home_align = _run(
        [
            "python3",
            "scripts/validate_identity_home_catalog_alignment.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-home",
            str(Path(args.catalog).expanduser().resolve().parent),
            "--json-only",
        ]
    )
    home_align_payload = _parse_json_payload(out_home_align) or {}
    validators["identity_home_catalog_alignment"] = {
        "rc": rc_home_align,
        "ok": rc_home_align == 0,
        "out": out_home_align,
        "err": err_home_align,
    }
    home_align_status = str(home_align_payload.get("path_governance_status", "")).strip().upper()
    if rc_home_align != 0 or home_align_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fixture_boundary, out_fixture_boundary, err_fixture_boundary = _run(
        [
            "python3",
            "scripts/validate_fixture_runtime_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fixture_boundary_payload = _parse_json_payload(out_fixture_boundary) or {}
    validators["fixture_runtime_boundary"] = {
        "rc": rc_fixture_boundary,
        "ok": rc_fixture_boundary == 0,
        "out": out_fixture_boundary,
        "err": err_fixture_boundary,
    }
    fixture_boundary_status = str(fixture_boundary_payload.get("path_governance_status", "")).strip().upper()
    if rc_fixture_boundary != 0 or fixture_boundary_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_actor_binding, out_actor_binding, err_actor_binding = _run(
        [
            "python3",
            "scripts/validate_actor_session_binding.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    actor_binding_payload = _parse_json_payload(out_actor_binding) or {}
    validators["actor_session_binding"] = {
        "rc": rc_actor_binding,
        "ok": rc_actor_binding == 0,
        "out": out_actor_binding,
        "err": err_actor_binding,
    }
    actor_binding_status = str(actor_binding_payload.get("actor_binding_status", "")).strip().upper()
    if rc_actor_binding != 0 or actor_binding_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_no_implicit, out_no_implicit, err_no_implicit = _run(
        [
            "python3",
            "scripts/validate_no_implicit_switch.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    no_implicit_payload = _parse_json_payload(out_no_implicit) or {}
    validators["no_implicit_switch"] = {
        "rc": rc_no_implicit,
        "ok": rc_no_implicit == 0,
        "out": out_no_implicit,
        "err": err_no_implicit,
    }
    no_implicit_status = str(no_implicit_payload.get("implicit_switch_status", "")).strip().upper()
    if rc_no_implicit != 0 or no_implicit_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_cross_actor, out_cross_actor, err_cross_actor = _run(
        [
            "python3",
            "scripts/validate_cross_actor_isolation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cross_actor_payload = _parse_json_payload(out_cross_actor) or {}
    validators["cross_actor_isolation"] = {
        "rc": rc_cross_actor,
        "ok": rc_cross_actor == 0,
        "out": out_cross_actor,
        "err": err_cross_actor,
    }
    cross_actor_status = str(cross_actor_payload.get("cross_actor_isolation_status", "")).strip().upper()
    if rc_cross_actor != 0 or cross_actor_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_refresh, out_refresh, err_refresh = _run(
        [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--baseline-policy",
            "warn",
            "--json-only",
        ]
    )
    refresh_payload = _parse_json_payload(out_refresh) or {}
    validators["session_refresh_status"] = {
        "rc": rc_refresh,
        "ok": rc_refresh == 0,
        "out": out_refresh,
        "err": err_refresh,
    }
    refresh_status = str(refresh_payload.get("session_refresh_status", "")).strip().upper()
    if rc_refresh != 0 or refresh_status == "FAIL_REQUIRED":
        hard_boundary = True

    stamp_artifact = f"/tmp/identity-response-stamp-three-plane-{args.identity_id}.json"
    stamp_blocker_receipt = f"/tmp/identity-stamp-blocker-receipt-three-plane-{args.identity_id}.json"

    rc_stamp_render, out_stamp_render, err_stamp_render = _run(
        [
            "python3",
            "scripts/render_identity_response_stamp.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--view",
            "external",
            "--out",
            stamp_artifact,
            "--json-only",
        ]
    )
    stamp_render_payload = _parse_json_payload(out_stamp_render) or {}
    validators["response_stamp_render"] = {
        "rc": rc_stamp_render,
        "ok": rc_stamp_render == 0,
        "out": out_stamp_render,
        "err": err_stamp_render,
    }

    rc_stamp, out_stamp, err_stamp = _run(
        [
            "python3",
            "scripts/validate_identity_response_stamp.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-user-visible-gate",
            "--blocker-receipt-out",
            stamp_blocker_receipt,
            "--json-only",
        ]
    )
    stamp_payload = _parse_json_payload(out_stamp) or {}
    validators["response_stamp_validation"] = {
        "rc": rc_stamp,
        "ok": rc_stamp == 0,
        "out": out_stamp,
        "err": err_stamp,
    }

    rc_receipt, out_receipt, err_receipt = _run(
        [
            "python3",
            "scripts/validate_identity_response_stamp_blocker_receipt.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--force-check",
            "--receipt",
            stamp_blocker_receipt,
            "--json-only",
        ]
    )
    receipt_payload = _parse_json_payload(out_receipt) or {}
    validators["response_stamp_blocker_receipt"] = {
        "rc": rc_receipt,
        "ok": rc_receipt == 0,
        "out": out_receipt,
        "err": err_receipt,
    }

    rc_prompt, out_prompt, err_prompt = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_activation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_activation"] = {"rc": rc_prompt, "ok": rc_prompt == 0, "out": out_prompt, "err": err_prompt}

    rc_prompt_lc, out_prompt_lc, err_prompt_lc = _run(
        [
            "python3",
            "scripts/validate_identity_prompt_lifecycle.py",
            "--identity-id",
            args.identity_id,
            "--report",
            str(report_path),
        ]
    )
    validators["prompt_lifecycle"] = {
        "rc": rc_prompt_lc,
        "ok": rc_prompt_lc == 0,
        "out": out_prompt_lc,
        "err": err_prompt_lc,
    }

    cap_cmd = [
        "python3",
        "scripts/validate_identity_capability_activation.py",
        "--identity-id",
        args.identity_id,
        "--report",
        str(report_path),
    ]
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN":
        cap_cmd.append("--require-activated")
    rc_cap, out_cap, err_cap = _run(cap_cmd)
    validators["capability_activation"] = {
        "rc": rc_cap,
        "ok": rc_cap == 0,
        "out": out_cap,
        "err": err_cap,
    }

    rc_dc, out_dc, err_dc = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_content.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_content"] = {"rc": rc_dc, "ok": rc_dc == 0, "out": out_dc, "err": err_dc}

    rc_dcv, out_dcv, err_dcv = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_cross_validation.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_cross_validation"] = {
        "rc": rc_dcv,
        "ok": rc_dcv == 0,
        "out": out_dcv,
        "err": err_dcv,
    }

    rc_drs, out_drs, err_drs = _run(
        [
            "python3",
            "scripts/validate_identity_dialogue_result_support.py",
            "--catalog",
            args.catalog,
            "--identity-id",
            args.identity_id,
        ]
    )
    validators["dialogue_result_support"] = {"rc": rc_drs, "ok": rc_drs == 0, "out": out_drs, "err": err_drs}

    rc_cov, out_cov, err_cov = _run(
        [
            "python3",
            "scripts/validate_required_contract_coverage.py",
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--identity-id",
            args.identity_id,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    coverage_payload = _parse_json_payload(out_cov) or {}
    validators["required_contract_coverage"] = {
        "rc": rc_cov,
        "ok": rc_cov == 0,
        "out": out_cov,
        "err": err_cov,
    }

    rc_semantic, out_semantic, err_semantic = _run(
        [
            "python3",
            "scripts/validate_semantic_routing_guard.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    semantic_payload = _parse_json_payload(out_semantic) or {}
    validators["semantic_routing_guard"] = {
        "rc": rc_semantic,
        "ok": rc_semantic == 0,
        "out": out_semantic,
        "err": err_semantic,
    }
    semantic_status = str(semantic_payload.get("semantic_routing_status", "")).strip().upper()
    if rc_semantic != 0 or semantic_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_semantic_iso, out_semantic_iso, err_semantic_iso = _run(
        [
            "python3",
            "scripts/validate_protocol_vendor_semantic_isolation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    semantic_iso_payload = _parse_json_payload(out_semantic_iso) or {}
    validators["protocol_vendor_semantic_isolation"] = {
        "rc": rc_semantic_iso,
        "ok": rc_semantic_iso == 0,
        "out": out_semantic_iso,
        "err": err_semantic_iso,
    }
    semantic_iso_status = str(semantic_iso_payload.get("protocol_vendor_semantic_isolation_status", "")).strip().upper()
    if rc_semantic_iso != 0 or semantic_iso_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_namespace, out_namespace, err_namespace = _run(
        [
            "python3",
            "scripts/validate_vendor_namespace_separation.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    namespace_payload = _parse_json_payload(out_namespace) or {}
    validators["vendor_namespace_separation"] = {
        "rc": rc_namespace,
        "ok": rc_namespace == 0,
        "out": out_namespace,
        "err": err_namespace,
    }
    namespace_status = str(namespace_payload.get("vendor_namespace_status", "")).strip().upper()
    if rc_namespace != 0 or namespace_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_writeback, out_writeback, err_writeback = _run(
        [
            "python3",
            "scripts/validate_writeback_continuity.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    writeback_payload = _parse_json_payload(out_writeback) or {}
    validators["writeback_continuity"] = {
        "rc": rc_writeback,
        "ok": rc_writeback == 0,
        "out": out_writeback,
        "err": err_writeback,
    }
    writeback_status = str(writeback_payload.get("writeback_continuity_status", "")).strip().upper()
    if rc_writeback != 0 or writeback_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_post_exec, out_post_exec, err_post_exec = _run(
        [
            "python3",
            "scripts/validate_post_execution_mandatory.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    post_exec_payload = _parse_json_payload(out_post_exec) or {}
    validators["post_execution_mandatory"] = {
        "rc": rc_post_exec,
        "ok": rc_post_exec == 0,
        "out": out_post_exec,
        "err": err_post_exec,
    }
    post_exec_status = str(post_exec_payload.get("post_execution_mandatory_status", "")).strip().upper()
    if rc_post_exec != 0 or post_exec_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_sidecar, out_sidecar, err_sidecar = _run(
        [
            "python3",
            "scripts/validate_protocol_feedback_sidecar_contract.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    sidecar_payload = _parse_json_payload(out_sidecar) or {}
    validators["protocol_feedback_sidecar"] = {
        "rc": rc_sidecar,
        "ok": rc_sidecar == 0,
        "out": out_sidecar,
        "err": err_sidecar,
    }
    sidecar_status = str(sidecar_payload.get("sidecar_contract_status", "")).strip().upper()
    if rc_sidecar != 0 or sidecar_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_base_boundary, out_base_boundary, err_base_boundary = _run(
        [
            "python3",
            "scripts/validate_instance_base_repo_write_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    base_boundary_payload = _parse_json_payload(out_base_boundary) or {}
    validators["instance_base_repo_write_boundary"] = {
        "rc": rc_base_boundary,
        "ok": rc_base_boundary == 0,
        "out": out_base_boundary,
        "err": err_base_boundary,
    }
    base_boundary_status = str(base_boundary_payload.get("base_repo_write_boundary_status", "")).strip().upper()
    if rc_base_boundary != 0 or base_boundary_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_archival, out_archival, err_archival = _run(
        [
            "python3",
            "scripts/validate_protocol_feedback_ssot_archival.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    archival_payload = _parse_json_payload(out_archival) or {}
    validators["protocol_feedback_ssot_archival"] = {
        "rc": rc_archival,
        "ok": rc_archival == 0,
        "out": out_archival,
        "err": err_archival,
    }
    archival_status = str(archival_payload.get("feedback_ssot_archival_status", "")).strip().upper()
    if rc_archival != 0 or archival_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fresh, out_fresh, err_fresh = _run(
        [
            "python3",
            "scripts/validate_execution_report_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--report",
            str(report_path),
            "--execution-report-policy",
            "strict",
            "--json-only",
        ]
    )
    freshness_payload = _parse_json_payload(out_fresh) or {}
    validators["execution_report_freshness"] = {
        "rc": rc_fresh,
        "ok": rc_fresh == 0,
        "out": out_fresh,
        "err": err_fresh,
    }

    rc_baseline, out_baseline, err_baseline = _run(
        [
            "python3",
            "scripts/validate_identity_protocol_baseline_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--execution-report",
            str(report_path),
            "--baseline-policy",
            "warn",
            "--json-only",
        ]
    )
    baseline_payload = _parse_json_payload(out_baseline) or {}
    validators["protocol_baseline_freshness"] = {
        "rc": rc_baseline,
        "ok": rc_baseline == 0,
        "out": out_baseline,
        "err": err_baseline,
    }

    detail = {
        "report_path": str(report_path),
        "all_ok": all_ok,
        "writeback_status": wb,
        "permission_state": ps,
        "capability_activation_status": cap_status,
        "capability_activation_error_code": cap_error,
        "next_action": next_action,
        "error_code": err_code,
        "mandatory_fields_complete": bool(mandatory),
        "hard_boundary": hard_boundary,
        "required_contract_coverage": {
            "required_contract_total": coverage_payload.get("required_contract_total"),
            "required_contract_passed": coverage_payload.get("required_contract_passed"),
            "required_contract_coverage_rate": coverage_payload.get("required_contract_coverage_rate"),
            "skipped_contract_count": coverage_payload.get("skipped_contract_count"),
            "failed_required_contract_count": coverage_payload.get("failed_required_contract_count"),
            "failed_optional_contract_count": coverage_payload.get("failed_optional_contract_count"),
        },
        "semantic_routing_guard": {
            "semantic_routing_status": semantic_payload.get("semantic_routing_status"),
            "error_code": semantic_payload.get("error_code", ""),
            "required_contract": semantic_payload.get("required_contract"),
            "auto_required_signal": semantic_payload.get("auto_required_signal"),
            "feedback_batch_path": semantic_payload.get("feedback_batch_path"),
            "intent_domain": semantic_payload.get("intent_domain"),
            "intent_confidence": semantic_payload.get("intent_confidence"),
            "classifier_reason": semantic_payload.get("classifier_reason", ""),
            "legacy_namespace_refs": semantic_payload.get("legacy_namespace_refs", []),
            "stale_reasons": semantic_payload.get("stale_reasons", []),
        },
        "protocol_vendor_semantic_isolation": {
            "protocol_vendor_semantic_isolation_status": semantic_iso_payload.get("protocol_vendor_semantic_isolation_status"),
            "error_code": semantic_iso_payload.get("error_code", ""),
            "required_contract": semantic_iso_payload.get("required_contract"),
            "auto_required_signal": semantic_iso_payload.get("auto_required_signal"),
            "feedback_batch_path": semantic_iso_payload.get("feedback_batch_path"),
            "intent_domain": semantic_iso_payload.get("intent_domain"),
            "intent_confidence": semantic_iso_payload.get("intent_confidence"),
            "intent_domain_before": semantic_iso_payload.get("intent_domain_before"),
            "intent_domain_after": semantic_iso_payload.get("intent_domain_after"),
            "switch_receipt_required": semantic_iso_payload.get("switch_receipt_required"),
            "switch_receipt_present": semantic_iso_payload.get("switch_receipt_present"),
            "switch_receipt_fields": semantic_iso_payload.get("switch_receipt_fields", {}),
            "protocol_vendor_refs": semantic_iso_payload.get("protocol_vendor_refs", []),
            "business_partner_refs": semantic_iso_payload.get("business_partner_refs", []),
            "stale_reasons": semantic_iso_payload.get("stale_reasons", []),
        },
        "vendor_namespace_separation": {
            "vendor_namespace_status": namespace_payload.get("vendor_namespace_status"),
            "error_code": namespace_payload.get("error_code", ""),
            "required_contract": namespace_payload.get("required_contract"),
            "auto_required_signal": namespace_payload.get("auto_required_signal"),
            "feedback_root": namespace_payload.get("feedback_root"),
            "protocol_vendor_file_count": namespace_payload.get("protocol_vendor_file_count"),
            "business_partner_file_count": namespace_payload.get("business_partner_file_count"),
            "legacy_vendor_file_count": namespace_payload.get("legacy_vendor_file_count"),
            "legacy_namespace_refs": namespace_payload.get("legacy_namespace_refs", []),
            "stale_reasons": namespace_payload.get("stale_reasons", []),
        },
        "writeback_continuity": {
            "writeback_continuity_status": writeback_payload.get("writeback_continuity_status"),
            "error_code": writeback_payload.get("error_code", ""),
            "required_contract": writeback_payload.get("required_contract"),
            "report_selected_path": writeback_payload.get("report_selected_path"),
            "writeback_mode": writeback_payload.get("writeback_mode"),
            "writeback_status": writeback_payload.get("writeback_status"),
            "upgrade_required": writeback_payload.get("upgrade_required"),
            "all_ok": writeback_payload.get("all_ok"),
            "degrade_reason": writeback_payload.get("degrade_reason", ""),
            "risk_level": writeback_payload.get("risk_level", ""),
            "next_recovery_action": writeback_payload.get("next_recovery_action", ""),
            "stale_reasons": writeback_payload.get("stale_reasons", []),
        },
        "post_execution_mandatory": {
            "post_execution_mandatory_status": post_exec_payload.get("post_execution_mandatory_status"),
            "error_code": post_exec_payload.get("error_code", ""),
            "required_contract": post_exec_payload.get("required_contract"),
            "report_selected_path": post_exec_payload.get("report_selected_path"),
            "missing_fields": post_exec_payload.get("missing_fields", []),
            "writeback_mode": post_exec_payload.get("writeback_mode", ""),
            "writeback_status": post_exec_payload.get("writeback_status", ""),
            "next_action": post_exec_payload.get("next_action", ""),
            "next_recovery_action": post_exec_payload.get("next_recovery_action", ""),
            "stale_reasons": post_exec_payload.get("stale_reasons", []),
        },
        "protocol_feedback_sidecar": {
            "sidecar_contract_status": sidecar_payload.get("sidecar_contract_status"),
            "sidecar_error_code": sidecar_payload.get("sidecar_error_code", ""),
            "required_contract": sidecar_payload.get("required_contract"),
            "auto_required_signal": sidecar_payload.get("auto_required_signal"),
            "enforce_blocking": sidecar_payload.get("enforce_blocking"),
            "escalation_required": sidecar_payload.get("escalation_required"),
            "escalation_decision": sidecar_payload.get("escalation_decision"),
            "blocking_error_codes": sidecar_payload.get("blocking_error_codes", []),
            "p0_violations": sidecar_payload.get("p0_violations", []),
            "track_a": sidecar_payload.get("track_a", {}),
            "track_b": sidecar_payload.get("track_b", {}),
            "stale_reasons": sidecar_payload.get("stale_reasons", []),
        },
        "instance_base_repo_write_boundary": {
            "base_repo_write_boundary_status": base_boundary_payload.get("base_repo_write_boundary_status"),
            "error_code": base_boundary_payload.get("error_code", ""),
            "required_contract": base_boundary_payload.get("required_contract"),
            "auto_required_signal": base_boundary_payload.get("auto_required_signal"),
            "report_selected_path": base_boundary_payload.get("report_selected_path", ""),
            "source_mode": base_boundary_payload.get("source_mode", ""),
            "allowlist_prefixes": base_boundary_payload.get("allowlist_prefixes", []),
            "denylist_prefixes": base_boundary_payload.get("denylist_prefixes", []),
            "repo_relative_candidates": base_boundary_payload.get("repo_relative_candidates", []),
            "allowed_paths": base_boundary_payload.get("allowed_paths", []),
            "blocked_paths": base_boundary_payload.get("blocked_paths", []),
            "explicit_deny_hits": base_boundary_payload.get("explicit_deny_hits", []),
            "override_receipt_path": base_boundary_payload.get("override_receipt_path", ""),
            "override_applied": base_boundary_payload.get("override_applied"),
            "stale_reasons": base_boundary_payload.get("stale_reasons", []),
        },
        "protocol_feedback_ssot_archival": {
            "feedback_ssot_archival_status": archival_payload.get("feedback_ssot_archival_status"),
            "error_code": archival_payload.get("error_code", ""),
            "required_contract": archival_payload.get("required_contract"),
            "auto_required_signal": archival_payload.get("auto_required_signal"),
            "feedback_root": archival_payload.get("feedback_root", ""),
            "outbox_dir": archival_payload.get("outbox_dir", ""),
            "evidence_index_path": archival_payload.get("evidence_index_path", ""),
            "batch_file_count": archival_payload.get("batch_file_count"),
            "batch_files": archival_payload.get("batch_files", []),
            "index_linked_batches": archival_payload.get("index_linked_batches", []),
            "index_unlinked_batches": archival_payload.get("index_unlinked_batches", []),
            "mirror_candidate_refs": archival_payload.get("mirror_candidate_refs", []),
            "stale_reasons": archival_payload.get("stale_reasons", []),
        },
        "identity_home_catalog_alignment": {
            "path_governance_status": home_align_payload.get("path_governance_status"),
            "path_error_codes": home_align_payload.get("path_error_codes", []),
            "identity_home": home_align_payload.get("identity_home"),
            "identity_home_expected": home_align_payload.get("identity_home_expected"),
            "identity_home_source": home_align_payload.get("identity_home_source"),
            "stale_reasons": home_align_payload.get("stale_reasons", []),
        },
        "fixture_runtime_boundary": {
            "path_governance_status": fixture_boundary_payload.get("path_governance_status"),
            "path_error_codes": fixture_boundary_payload.get("path_error_codes", []),
            "operation": fixture_boundary_payload.get("operation"),
            "allow_fixture_runtime": fixture_boundary_payload.get("allow_fixture_runtime"),
            "fixture_audit_receipt": fixture_boundary_payload.get("fixture_audit_receipt"),
            "stale_reasons": fixture_boundary_payload.get("stale_reasons", []),
        },
        "actor_session_binding": {
            "actor_binding_status": actor_binding_payload.get("actor_binding_status"),
            "error_code": actor_binding_payload.get("error_code", ""),
            "actor_id": actor_binding_payload.get("actor_id", ""),
            "actor_session_path": actor_binding_payload.get("actor_session_path", ""),
            "bound_identity_id": actor_binding_payload.get("bound_identity_id", ""),
            "catalog_identity_status": actor_binding_payload.get("catalog_identity_status", ""),
            "stale_reasons": actor_binding_payload.get("stale_reasons", []),
        },
        "no_implicit_switch": {
            "implicit_switch_status": no_implicit_payload.get("implicit_switch_status"),
            "error_code": no_implicit_payload.get("error_code", ""),
            "switch_report_path": no_implicit_payload.get("switch_report_path", ""),
            "switch_id": no_implicit_payload.get("switch_id", ""),
            "actor_id": no_implicit_payload.get("actor_id", ""),
            "run_id": no_implicit_payload.get("run_id", ""),
            "cross_actor_demotion_detected": no_implicit_payload.get("cross_actor_demotion_detected"),
            "stale_reasons": no_implicit_payload.get("stale_reasons", []),
        },
        "cross_actor_isolation": {
            "cross_actor_isolation_status": cross_actor_payload.get("cross_actor_isolation_status"),
            "error_code": cross_actor_payload.get("error_code", ""),
            "actor_binding_count": cross_actor_payload.get("actor_binding_count"),
            "active_identities": cross_actor_payload.get("active_identities", []),
            "stale_reasons": cross_actor_payload.get("stale_reasons", []),
        },
        "session_refresh_status": {
            "session_refresh_status": refresh_payload.get("session_refresh_status"),
            "error_code": refresh_payload.get("error_code", ""),
            "actor_id": refresh_payload.get("actor_id", ""),
            "lease_status": refresh_payload.get("lease_status", ""),
            "pointer_consistency": refresh_payload.get("pointer_consistency", ""),
            "risk_flags": refresh_payload.get("risk_flags", []),
            "next_action": refresh_payload.get("next_action", ""),
            "baseline_status": refresh_payload.get("baseline_status", ""),
            "baseline_error_code": refresh_payload.get("baseline_error_code", ""),
            "report_protocol_commit_sha": refresh_payload.get("report_protocol_commit_sha", ""),
            "current_protocol_head_sha": refresh_payload.get("current_protocol_head_sha", ""),
            "lag_commits": refresh_payload.get("lag_commits"),
            "report_selected_path": refresh_payload.get("report_selected_path", ""),
            "stale_reasons": refresh_payload.get("stale_reasons", []),
        },
        "response_identity_stamp": {
            "render_status": "PASS" if rc_stamp_render == 0 else "FAIL",
            "stamp_status": stamp_payload.get("stamp_status"),
            "stamp_error_code": stamp_payload.get("error_code"),
            "blocker_receipt_status": receipt_payload.get("receipt_status"),
            "blocker_receipt_path": stamp_payload.get("blocker_receipt_path", ""),
            "reply_sample_count": stamp_payload.get("reply_sample_count", 0),
            "reply_stamp_missing_count": stamp_payload.get("reply_stamp_missing_count", 0),
            "reply_stamp_missing_refs": stamp_payload.get("reply_stamp_missing_refs", []),
            "external_stamp": stamp_render_payload.get("external_stamp"),
            "stale_reasons": stamp_payload.get("stale_reasons", []),
        },
        "execution_report_freshness": {
            "freshness_status": freshness_payload.get("freshness_status"),
            "freshness_error_code": freshness_payload.get("freshness_error_code"),
            "report_selected_path": freshness_payload.get("report_selected_path"),
            "stale_reasons": freshness_payload.get("stale_reasons", []),
            "checks": freshness_payload.get("checks", {}),
        },
        "protocol_baseline_freshness": {
            "baseline_status": baseline_payload.get("baseline_status"),
            "baseline_error_code": baseline_payload.get("baseline_error_code"),
            "report_selected_path": baseline_payload.get("report_selected_path"),
            "report_protocol_root": baseline_payload.get("report_protocol_root"),
            "report_protocol_commit_sha": baseline_payload.get("report_protocol_commit_sha"),
            "current_protocol_head_sha": baseline_payload.get("current_protocol_head_sha"),
            "lag_commits": baseline_payload.get("lag_commits"),
            "stale_reasons": baseline_payload.get("stale_reasons", []),
        },
        "validators": validators,
    }

    validators_all_ok = all(v.get("ok", False) for v in validators.values())
    capability_strict_ok = cap_status in {"ACTIVATED", "NOT_REQUIRED"}
    if all_ok and wb == "WRITTEN" and ps == "WRITEBACK_WRITTEN" and mandatory and validators_all_ok and capability_strict_ok:
        return "CLOSED", detail
    if hard_boundary:
        return "BLOCKED", detail
    if mandatory and next_action and validators_all_ok:
        return "IN_PROGRESS", detail
    return "BLOCKED", detail


def _git_current_branch() -> str:
    rc, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def _git_head_sha() -> str:
    rc, out, _ = _run(["git", "rev-parse", "HEAD"])
    if rc == 0:
        return out.strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit unified three-plane status for identity governance.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=os.environ.get("IDENTITY_CATALOG", ""))
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="", help="optional explicit scope arbitration: REPO/USER/ADMIN/SYSTEM")
    ap.add_argument("--execution-report", default="")
    ap.add_argument("--with-docs-contract", action="store_true", help="run repo-plane docs contract checker")
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--workflow-file-sha", default="")
    ap.add_argument("--run-head-sha", default="")
    ap.add_argument("--run-workflow-file-sha", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not args.catalog:
        print("[FAIL] --catalog is required (or export IDENTITY_CATALOG first).")
        return 2
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            preferred_scope=str(args.scope or ""),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve identity context: {exc}")
        return 2

    if not args.target_branch:
        args.target_branch = _git_current_branch()
    if not args.release_head_sha:
        args.release_head_sha = _git_head_sha()

    preferred_pack = str(resolved.get("resolved_pack_path") or resolved.get("pack_path") or "")
    report_path = Path(args.execution_report).expanduser().resolve() if args.execution_report else _latest_report(
        args.identity_id,
        os.environ.get("IDENTITY_HOME", ""),
        preferred_pack,
    )
    instance_status, instance_detail = _instance_plane_status(args, report_path)
    repo_status, repo_detail = _repo_plane_status(args, resolved)
    release_status, release_detail = _release_plane_status(args)

    payload = {
        "target_branch": args.target_branch,
        "release_head_sha": args.release_head_sha,
        "required_gates_run_id": args.required_gates_run_id,
        "run_url": args.run_url,
        "workflow_file_sha": args.workflow_file_sha,
        "required_checks_set": release_detail.get("required_checks_set", []),
        "instance_plane_status": instance_status,
        "repo_plane_status": repo_status,
        "release_plane_status": release_status,
        "identity_context": {
            "identity_id": args.identity_id,
            "source_layer": resolved.get("source_layer"),
            "catalog_path": resolved.get("catalog_path"),
            "pack_path": resolved.get("pack_path"),
            "resolved_scope": resolved.get("resolved_scope"),
            "resolved_pack_path": resolved.get("resolved_pack_path"),
            "conflict_detected": resolved.get("conflict_detected"),
        },
        "instance_plane_detail": instance_detail,
        "repo_plane_detail": repo_detail,
        "release_plane_detail": release_detail,
    }

    overall = "Conditional Go"
    if instance_status == "CLOSED" and repo_status == "CLOSED" and release_status == "CLOSED":
        overall = "Full Go"
    payload["overall_release_decision"] = overall
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"overall_release_decision={overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
