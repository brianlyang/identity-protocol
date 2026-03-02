#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent
from resolve_identity_context import resolve_identity

PROTOCOL_ROOT = Path(__file__).resolve().parent.parent

def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    run_cwd = cwd.resolve() if isinstance(cwd, Path) else PROTOCOL_ROOT
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(run_cwd))
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


def _resolve_applied_gate_set(*, layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> str:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="global",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    if work_layer == "protocol":
        return "protocol_required_checks"
    if work_layer == "instance":
        return "instance_required_checks"
    return "dual_unroutable"


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
    layer_intent_text = str(getattr(args, "layer_intent_text", "") or "").strip()
    expected_work_layer = str(getattr(args, "expected_work_layer", "") or "").strip().lower()
    expected_source_layer = str(getattr(args, "expected_source_layer", "") or "").strip().lower()
    lane_applied_gate_set = _resolve_applied_gate_set(
        layer_intent_text=layer_intent_text,
        expected_work_layer=expected_work_layer,
        expected_source_layer=expected_source_layer,
    )
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

    rc_actor_mb, out_actor_mb, err_actor_mb = _run(
        [
            "python3",
            "scripts/validate_actor_session_multibinding_concurrency.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    actor_mb_payload = _parse_json_payload(out_actor_mb) or {}
    validators["actor_session_multibinding_concurrency"] = {
        "rc": rc_actor_mb,
        "ok": rc_actor_mb == 0,
        "out": out_actor_mb,
        "err": err_actor_mb,
    }
    actor_mb_status = str(actor_mb_payload.get("actor_session_multibinding_status", "")).strip().upper()
    if rc_actor_mb != 0 or actor_mb_status == "FAIL_REQUIRED":
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
    reply_first_line_blocker_receipt = (
        f"/tmp/identity-reply-first-line-blocker-receipt-three-plane-{args.identity_id}.json"
    )
    send_time_reply_gate_blocker_receipt = (
        f"/tmp/identity-send-time-reply-gate-blocker-receipt-three-plane-{args.identity_id}.json"
    )
    execution_reply_coherence_blocker_receipt = (
        f"/tmp/identity-execution-reply-coherence-blocker-receipt-three-plane-{args.identity_id}.json"
    )

    render_cmd = [
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
        "--disclosure-level",
        "standard",
        "--out",
        stamp_artifact,
        "--json-only",
    ]
    if layer_intent_text:
        render_cmd.extend(["--layer-intent-text", layer_intent_text])
    rc_stamp_render, out_stamp_render, err_stamp_render = _run(render_cmd)
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
            "--operation",
            "three-plane",
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
    if rc_stamp != 0 or rc_receipt != 0:
        hard_boundary = True

    reply_first_line_cmd = [
        "python3",
        "scripts/validate_reply_identity_context_first_line.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-first-line-gate",
        "--operation",
        "three-plane",
        "--blocker-receipt-out",
        reply_first_line_blocker_receipt,
        "--json-only",
    ]
    if layer_intent_text:
        reply_first_line_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        reply_first_line_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        reply_first_line_cmd.extend(["--expected-source-layer", expected_source_layer])
    rc_reply_first_line, out_reply_first_line, err_reply_first_line = _run(reply_first_line_cmd)
    reply_first_line_payload = _parse_json_payload(out_reply_first_line) or {}
    validators["reply_identity_context_first_line"] = {
        "rc": rc_reply_first_line,
        "ok": rc_reply_first_line == 0,
        "out": out_reply_first_line,
        "err": err_reply_first_line,
    }
    reply_first_line_status = str(reply_first_line_payload.get("reply_first_line_status", "")).strip().upper()
    if rc_reply_first_line != 0 or reply_first_line_status == "FAIL_REQUIRED":
        hard_boundary = True

    layer_intent_cmd = [
        "python3",
        "scripts/validate_layer_intent_resolution.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-layer-intent-gate",
        "--operation",
        "three-plane",
        "--json-only",
    ]
    if layer_intent_text:
        layer_intent_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        layer_intent_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        layer_intent_cmd.extend(["--expected-source-layer", expected_source_layer])
    rc_layer_intent, out_layer_intent, err_layer_intent = _run(layer_intent_cmd)
    layer_intent_payload = _parse_json_payload(out_layer_intent) or {}
    validators["layer_intent_resolution"] = {
        "rc": rc_layer_intent,
        "ok": rc_layer_intent == 0,
        "out": out_layer_intent,
        "err": err_layer_intent,
    }
    layer_intent_status = str(layer_intent_payload.get("layer_intent_resolution_status", "")).strip().upper()
    if rc_layer_intent != 0 or layer_intent_status == "FAIL_REQUIRED":
        hard_boundary = True

    send_time_cmd = [
        "python3",
        "scripts/validate_send_time_reply_gate.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-send-time-gate",
        "--operation",
        "three-plane",
        "--blocker-receipt-out",
        send_time_reply_gate_blocker_receipt,
        "--json-only",
    ]
    if layer_intent_text:
        send_time_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        send_time_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        send_time_cmd.extend(["--expected-source-layer", expected_source_layer])
    rc_send_time_gate, out_send_time_gate, err_send_time_gate = _run(send_time_cmd)
    send_time_gate_payload = _parse_json_payload(out_send_time_gate) or {}
    validators["send_time_reply_gate"] = {
        "rc": rc_send_time_gate,
        "ok": rc_send_time_gate == 0,
        "out": out_send_time_gate,
        "err": err_send_time_gate,
    }
    send_time_gate_status = str(send_time_gate_payload.get("send_time_gate_status", "")).strip().upper()
    if rc_send_time_gate != 0 or send_time_gate_status == "FAIL_REQUIRED":
        hard_boundary = True

    reply_coherence_cmd = [
        "python3",
        "scripts/validate_execution_reply_identity_coherence.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--stamp-json",
        stamp_artifact,
        "--force-check",
        "--enforce-coherence-gate",
        "--operation",
        "three-plane",
        "--blocker-receipt-out",
        execution_reply_coherence_blocker_receipt,
        "--json-only",
    ]
    if layer_intent_text:
        reply_coherence_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        reply_coherence_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        reply_coherence_cmd.extend(["--expected-source-layer", expected_source_layer])
    rc_reply_coherence, out_reply_coherence, err_reply_coherence = _run(reply_coherence_cmd)
    reply_coherence_payload = _parse_json_payload(out_reply_coherence) or {}
    validators["execution_reply_identity_coherence"] = {
        "rc": rc_reply_coherence,
        "ok": rc_reply_coherence == 0,
        "out": out_reply_coherence,
        "err": err_reply_coherence,
    }
    reply_coherence_status = str(reply_coherence_payload.get("coherence_status", "")).strip().upper()
    if rc_reply_coherence != 0 or reply_coherence_status == "FAIL_REQUIRED":
        hard_boundary = True

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

    rc_herm, out_herm, err_herm = _run(
        [
            "python3",
            "scripts/validate_e2e_hermetic_runtime_import.py",
            "--operation",
            "three-plane",
            "--pythonpath-bootstrap-mode",
            "internal_bootstrap",
            "--json-only",
        ]
    )
    herm_payload = _parse_json_payload(out_herm) or {}
    validators["e2e_hermetic_runtime_import"] = {
        "rc": rc_herm,
        "ok": rc_herm == 0,
        "out": out_herm,
        "err": err_herm,
    }
    herm_status = str(herm_payload.get("e2e_hermetic_runtime_status", "")).strip().upper()
    if rc_herm != 0 or herm_status == "FAIL_REQUIRED":
        hard_boundary = True

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

    rc_split, out_split, err_split = _run(
        [
            "python3",
            "scripts/validate_instance_protocol_split_receipt.py",
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
    split_payload = _parse_json_payload(out_split) or {}
    validators["instance_protocol_split_receipt"] = {
        "rc": rc_split,
        "ok": rc_split == 0,
        "out": out_split,
        "err": err_split,
    }
    split_status = str(split_payload.get("instance_protocol_split_status", "")).strip().upper()
    if rc_split != 0 or split_status == "FAIL_REQUIRED":
        hard_boundary = True

    lane_cmd = [
        "python3",
        "scripts/validate_work_layer_gate_set_routing.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--applied-gate-set",
        lane_applied_gate_set,
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        lane_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        lane_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        lane_cmd.extend(["--source-layer", expected_source_layer])
    rc_lane, out_lane, err_lane = _run(lane_cmd)
    lane_payload = _parse_json_payload(out_lane) or {}
    validators["work_layer_gate_set_routing"] = {
        "rc": rc_lane,
        "ok": rc_lane == 0,
        "out": out_lane,
        "err": err_lane,
    }
    lane_status = str(lane_payload.get("work_layer_gate_set_routing_status", "")).strip().upper()
    if rc_lane != 0 or lane_status == "FAIL_REQUIRED":
        hard_boundary = True

    reply_channel_cmd = [
        "python3",
        "scripts/validate_protocol_feedback_reply_channel.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    rc_reply_channel, out_reply_channel, err_reply_channel = _run(reply_channel_cmd)
    reply_channel_payload = _parse_json_payload(out_reply_channel) or {}
    validators["protocol_feedback_reply_channel"] = {
        "rc": rc_reply_channel,
        "ok": rc_reply_channel == 0,
        "out": out_reply_channel,
        "err": err_reply_channel,
    }
    reply_channel_status = str(reply_channel_payload.get("protocol_feedback_reply_channel_status", "")).strip().upper()
    if rc_reply_channel != 0 or reply_channel_status == "FAIL_REQUIRED":
        hard_boundary = True

    bootstrap_cmd = [
        "python3",
        "scripts/validate_protocol_feedback_bootstrap_ready.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        bootstrap_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        bootstrap_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        bootstrap_cmd.extend(["--source-layer", expected_source_layer])
    rc_bootstrap, out_bootstrap, err_bootstrap = _run(bootstrap_cmd)
    bootstrap_payload = _parse_json_payload(out_bootstrap) or {}
    validators["protocol_feedback_bootstrap_ready"] = {
        "rc": rc_bootstrap,
        "ok": rc_bootstrap == 0,
        "out": out_bootstrap,
        "err": err_bootstrap,
    }
    bootstrap_status = str(bootstrap_payload.get("protocol_feedback_bootstrap_status", "")).strip().upper()
    if rc_bootstrap != 0 or bootstrap_status == "FAIL_REQUIRED":
        hard_boundary = True

    candidate_cmd = [
        "python3",
        "scripts/validate_protocol_entry_candidate_bridge.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        candidate_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        candidate_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        candidate_cmd.extend(["--source-layer", expected_source_layer])
    rc_candidate, out_candidate, err_candidate = _run(candidate_cmd)
    candidate_payload = _parse_json_payload(out_candidate) or {}
    validators["protocol_entry_candidate_bridge"] = {
        "rc": rc_candidate,
        "ok": rc_candidate == 0,
        "out": out_candidate,
        "err": err_candidate,
    }
    candidate_status = str(candidate_payload.get("protocol_entry_candidate_status", "")).strip().upper()
    if rc_candidate != 0 or candidate_status == "FAIL_REQUIRED":
        hard_boundary = True

    inquiry_cmd = [
        "python3",
        "scripts/validate_protocol_inquiry_followup_chain.py",
        "--identity-id",
        args.identity_id,
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--operation",
        "three-plane",
        "--force-check",
        "--json-only",
    ]
    if layer_intent_text:
        inquiry_cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        inquiry_cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        inquiry_cmd.extend(["--source-layer", expected_source_layer])
    rc_inquiry, out_inquiry, err_inquiry = _run(inquiry_cmd)
    inquiry_payload = _parse_json_payload(out_inquiry) or {}
    validators["protocol_inquiry_followup_chain"] = {
        "rc": rc_inquiry,
        "ok": rc_inquiry == 0,
        "out": out_inquiry,
        "err": err_inquiry,
    }
    inquiry_status = str(inquiry_payload.get("protocol_inquiry_followup_chain_status", "")).strip().upper()
    if rc_inquiry != 0 or inquiry_status == "FAIL_REQUIRED":
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

    rc_source_trust, out_source_trust, err_source_trust = _run(
        [
            "python3",
            "scripts/validate_external_source_trust_chain.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    source_trust_payload = _parse_json_payload(out_source_trust) or {}
    validators["external_source_trust_chain"] = {
        "rc": rc_source_trust,
        "ok": rc_source_trust == 0,
        "out": out_source_trust,
        "err": err_source_trust,
    }
    source_trust_status = str(source_trust_payload.get("external_source_trust_chain_status", "")).strip().upper()
    if rc_source_trust != 0 or source_trust_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_sanitization, out_sanitization, err_sanitization = _run(
        [
            "python3",
            "scripts/validate_protocol_data_sanitization_boundary.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    sanitization_payload = _parse_json_payload(out_sanitization) or {}
    validators["protocol_data_sanitization_boundary"] = {
        "rc": rc_sanitization,
        "ok": rc_sanitization == 0,
        "out": out_sanitization,
        "err": err_sanitization,
    }
    sanitization_status = (
        str(sanitization_payload.get("protocol_data_sanitization_boundary_status", "")).strip().upper()
    )
    if rc_sanitization != 0 or sanitization_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_opt_trigger, out_opt_trigger, err_opt_trigger = _run(
        [
            "python3",
            "scripts/trigger_platform_optimization_discovery.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    opt_trigger_payload = _parse_json_payload(out_opt_trigger) or {}
    validators["platform_optimization_discovery_trigger"] = {
        "rc": rc_opt_trigger,
        "ok": rc_opt_trigger == 0,
        "out": out_opt_trigger,
        "err": err_opt_trigger,
    }

    rc_dreq, out_dreq, err_dreq = _run(
        [
            "python3",
            "scripts/validate_discovery_requiredization.py",
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
    dreq_payload = _parse_json_payload(out_dreq) or {}
    validators["discovery_requiredization"] = {
        "rc": rc_dreq,
        "ok": rc_dreq == 0,
        "out": out_dreq,
        "err": err_dreq,
    }
    dreq_status = str(dreq_payload.get("discovery_requiredization_status", "")).strip().upper()
    if rc_dreq != 0 or dreq_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_vibe_pack, out_vibe_pack, err_vibe_pack = _run(
        [
            "python3",
            "scripts/build_vibe_coding_feeding_pack.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--out-root",
            "/tmp/vibe-coding-feeding-packs",
            "--json-only",
        ]
    )
    vibe_pack_payload = _parse_json_payload(out_vibe_pack) or {}
    validators["vibe_coding_feeding_pack"] = {
        "rc": rc_vibe_pack,
        "ok": rc_vibe_pack == 0,
        "out": out_vibe_pack,
        "err": err_vibe_pack,
    }

    rc_cap_fit, out_cap_fit, err_cap_fit = _run(
        [
            "python3",
            "scripts/validate_identity_capability_fit_optimization.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    cap_fit_payload = _parse_json_payload(out_cap_fit) or {}
    validators["capability_fit_optimization"] = {
        "rc": rc_cap_fit,
        "ok": rc_cap_fit == 0,
        "out": out_cap_fit,
        "err": err_cap_fit,
    }
    cap_fit_status = str(cap_fit_payload.get("capability_fit_optimization_status", "")).strip().upper()
    if rc_cap_fit != 0 or cap_fit_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_compose, out_compose, err_compose = _run(
        [
            "python3",
            "scripts/validate_capability_composition_before_discovery.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    compose_payload = _parse_json_payload(out_compose) or {}
    validators["capability_composition_before_discovery"] = {
        "rc": rc_compose,
        "ok": rc_compose == 0,
        "out": out_compose,
        "err": err_compose,
    }
    compose_status = str(compose_payload.get("compose_before_discovery_status", "")).strip().upper()
    if rc_compose != 0 or compose_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_fresh, out_fit_fresh, err_fit_fresh = _run(
        [
            "python3",
            "scripts/validate_capability_fit_review_freshness.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_fresh_payload = _parse_json_payload(out_fit_fresh) or {}
    validators["capability_fit_review_freshness"] = {
        "rc": rc_fit_fresh,
        "ok": rc_fit_fresh == 0,
        "out": out_fit_fresh,
        "err": err_fit_fresh,
    }
    fit_fresh_status = str(fit_fresh_payload.get("capability_fit_review_freshness_status", "")).strip().upper()
    if rc_fit_fresh != 0 or fit_fresh_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_roundtable, out_fit_roundtable, err_fit_roundtable = _run(
        [
            "python3",
            "scripts/validate_capability_fit_roundtable_evidence.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_roundtable_payload = _parse_json_payload(out_fit_roundtable) or {}
    validators["capability_fit_roundtable_evidence"] = {
        "rc": rc_fit_roundtable,
        "ok": rc_fit_roundtable == 0,
        "out": out_fit_roundtable,
        "err": err_fit_roundtable,
    }
    fit_roundtable_status = str(fit_roundtable_payload.get("capability_fit_roundtable_status", "")).strip().upper()
    if rc_fit_roundtable != 0 or fit_roundtable_status == "FAIL_REQUIRED":
        hard_boundary = True

    rc_fit_trigger, out_fit_trigger, err_fit_trigger = _run(
        [
            "python3",
            "scripts/trigger_capability_fit_review.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--json-only",
        ]
    )
    fit_trigger_payload = _parse_json_payload(out_fit_trigger) or {}
    validators["capability_fit_review_trigger"] = {
        "rc": rc_fit_trigger,
        "ok": rc_fit_trigger == 0,
        "out": out_fit_trigger,
        "err": err_fit_trigger,
    }

    rc_fit_builder, out_fit_builder, err_fit_builder = _run(
        [
            "python3",
            "scripts/build_capability_fit_matrix.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--operation",
            "three-plane",
            "--out-root",
            "/tmp/capability-fit-matrices",
            "--json-only",
        ]
    )
    fit_builder_payload = _parse_json_payload(out_fit_builder) or {}
    validators["capability_fit_matrix_builder"] = {
        "rc": rc_fit_builder,
        "ok": rc_fit_builder == 0,
        "out": out_fit_builder,
        "err": err_fit_builder,
    }

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

    rc_align, out_align, err_align = _run(
        [
            "python3",
            "scripts/validate_identity_protocol_version_alignment.py",
            "--identity-id",
            args.identity_id,
            "--catalog",
            args.catalog,
            "--repo-catalog",
            args.repo_catalog,
            "--execution-report",
            str(report_path),
            "--operation",
            "three-plane",
            "--alignment-policy",
            "warn",
            "--json-only",
        ]
    )
    align_payload = _parse_json_payload(out_align) or {}
    validators["protocol_version_alignment"] = {
        "rc": rc_align,
        "ok": rc_align == 0,
        "out": out_align,
        "err": err_align,
    }
    align_status = str(align_payload.get("protocol_version_alignment_status", "")).strip().upper()
    if rc_align != 0 or align_status == "FAIL_REQUIRED":
        hard_boundary = True

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
        "prompt_runtime_state_externalization": {
            "prompt_policy_hash": data.get("prompt_policy_hash", ""),
            "runtime_state_artifact_path": data.get("runtime_state_artifact_path", ""),
            "runtime_state_artifact_hash": data.get("runtime_state_artifact_hash", ""),
            "prompt_runtime_state_binding_status": data.get("prompt_runtime_state_binding_status", ""),
            "prompt_runtime_state_externalization_status": data.get("prompt_runtime_state_externalization_status", ""),
            "prompt_runtime_state_externalization_error_code": data.get("prompt_runtime_state_externalization_error_code", ""),
        },
        "required_contract_coverage": {
            "required_contract_total": coverage_payload.get("required_contract_total"),
            "required_contract_passed": coverage_payload.get("required_contract_passed"),
            "required_contract_coverage_rate": coverage_payload.get("required_contract_coverage_rate"),
            "discovery_required_total": coverage_payload.get("discovery_required_total"),
            "discovery_required_passed": coverage_payload.get("discovery_required_passed"),
            "discovery_required_coverage_rate": coverage_payload.get("discovery_required_coverage_rate"),
            "discovery_required_gate_failed": coverage_payload.get("discovery_required_gate_failed"),
            "skipped_contract_count": coverage_payload.get("skipped_contract_count"),
            "failed_required_contract_count": coverage_payload.get("failed_required_contract_count"),
            "failed_optional_contract_count": coverage_payload.get("failed_optional_contract_count"),
        },
        "e2e_hermetic_runtime_import": {
            "e2e_hermetic_runtime_status": herm_payload.get("e2e_hermetic_runtime_status"),
            "pythonpath_bootstrap_mode": herm_payload.get("pythonpath_bootstrap_mode", ""),
            "import_preflight_status": herm_payload.get("import_preflight_status", ""),
            "import_preflight_error_code": herm_payload.get("import_preflight_error_code", ""),
            "missing_modules": herm_payload.get("missing_modules", []),
            "stale_reasons": herm_payload.get("stale_reasons", []),
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
        "instance_protocol_split_receipt": {
            "instance_protocol_split_status": split_payload.get("instance_protocol_split_status"),
            "error_code": split_payload.get("error_code", ""),
            "required_contract": split_payload.get("required_contract"),
            "auto_required_signal": split_payload.get("auto_required_signal"),
            "receipt_path": split_payload.get("receipt_path", ""),
            "split_notice": split_payload.get("split_notice", ""),
            "feedback_triggered": split_payload.get("feedback_triggered"),
            "trigger_conditions": split_payload.get("trigger_conditions", {}),
            "instance_actions_ref": split_payload.get("instance_actions_ref", ""),
            "protocol_actions_ref": split_payload.get("protocol_actions_ref", ""),
            "evidence_index_ref": split_payload.get("evidence_index_ref", ""),
            "stale_reasons": split_payload.get("stale_reasons", []),
        },
        "work_layer_gate_set_routing": {
            "work_layer_gate_set_routing_status": lane_payload.get("work_layer_gate_set_routing_status"),
            "error_code": lane_payload.get("error_code", ""),
            "work_layer": lane_payload.get("work_layer", ""),
            "source_layer": lane_payload.get("source_layer", ""),
            "applied_gate_set": lane_payload.get("applied_gate_set", ""),
            "protocol_context_detected": lane_payload.get("protocol_context_detected"),
            "protocol_context_reasons": lane_payload.get("protocol_context_reasons", []),
            "session_lane_lock": lane_payload.get("session_lane_lock", ""),
            "session_lane_lock_source": lane_payload.get("session_lane_lock_source", ""),
            "session_lane_lock_receipt": lane_payload.get("session_lane_lock_receipt", ""),
            "lane_resolution_decision": lane_payload.get("lane_resolution_decision", ""),
            "lane_resolution_blocked": lane_payload.get("lane_resolution_blocked"),
            "lane_resolution_error_code": lane_payload.get("lane_resolution_error_code", ""),
            "lane_transition_reason": lane_payload.get("lane_transition_reason", ""),
            "protocol_feedback_triggered": lane_payload.get("protocol_feedback_triggered"),
            "protocol_feedback_paths": lane_payload.get("protocol_feedback_paths", []),
            "pending_receipt_path": lane_payload.get("pending_receipt_path", ""),
            "lane_lock_receipt_path": lane_payload.get("lane_lock_receipt_path", ""),
            "protocol_relevant_diff_detected": lane_payload.get("protocol_relevant_diff_detected"),
            "protocol_relevant_files": lane_payload.get("protocol_relevant_files", []),
            "stale_reasons": lane_payload.get("stale_reasons", []),
        },
        "protocol_feedback_reply_channel": {
            "protocol_feedback_reply_channel_status": reply_channel_payload.get("protocol_feedback_reply_channel_status"),
            "error_code": reply_channel_payload.get("error_code", ""),
            "required_contract": reply_channel_payload.get("required_contract"),
            "auto_required_signal": reply_channel_payload.get("auto_required_signal"),
            "primary_channel_root": reply_channel_payload.get("primary_channel_root", ""),
            "protocol_feedback_activity_detected": reply_channel_payload.get("protocol_feedback_activity_detected"),
            "protocol_feedback_activity_refs": reply_channel_payload.get("protocol_feedback_activity_refs", []),
            "non_standard_primary_refs": reply_channel_payload.get("non_standard_primary_refs", []),
            "mirror_reference_refs": reply_channel_payload.get("mirror_reference_refs", []),
            "split_receipt_requiredized": reply_channel_payload.get("split_receipt_requiredized"),
            "split_receipt_status": reply_channel_payload.get("split_receipt_status", ""),
            "split_receipt_error_code": reply_channel_payload.get("split_receipt_error_code", ""),
            "stale_reasons": reply_channel_payload.get("stale_reasons", []),
        },
        "protocol_feedback_bootstrap_ready": {
            "protocol_feedback_bootstrap_status": bootstrap_payload.get("protocol_feedback_bootstrap_status"),
            "protocol_feedback_bootstrap_mode": bootstrap_payload.get("protocol_feedback_bootstrap_mode", ""),
            "error_code": bootstrap_payload.get("error_code", ""),
            "required_contract": bootstrap_payload.get("required_contract"),
            "auto_required_signal": bootstrap_payload.get("auto_required_signal"),
            "resolved_work_layer": bootstrap_payload.get("resolved_work_layer", ""),
            "protocol_triggered": bootstrap_payload.get("protocol_triggered"),
            "protocol_lane_selected": bootstrap_payload.get("protocol_lane_selected"),
            "bootstrap_created_paths": bootstrap_payload.get("bootstrap_created_paths", []),
            "bootstrap_receipt_path": bootstrap_payload.get("bootstrap_receipt_path", ""),
            "feedback_root": bootstrap_payload.get("feedback_root", ""),
            "missing_required_dirs": bootstrap_payload.get("missing_required_dirs", []),
            "stale_reasons": bootstrap_payload.get("stale_reasons", []),
        },
        "protocol_entry_candidate_bridge": {
            "protocol_entry_candidate_status": candidate_payload.get("protocol_entry_candidate_status"),
            "protocol_entry_decision": candidate_payload.get("protocol_entry_decision", ""),
            "candidate_reason": candidate_payload.get("candidate_reason", ""),
            "candidate_confidence": candidate_payload.get("candidate_confidence"),
            "clarification_required": candidate_payload.get("clarification_required"),
            "clarification_questions": candidate_payload.get("clarification_questions", []),
            "candidate_seed_outbox_ref": candidate_payload.get("candidate_seed_outbox_ref", ""),
            "candidate_seed_index_ref": candidate_payload.get("candidate_seed_index_ref", ""),
            "candidate_receipt_path": candidate_payload.get("candidate_receipt_path", ""),
            "candidate_seed_path": candidate_payload.get("candidate_seed_path", ""),
            "candidate_promotion_status": candidate_payload.get("candidate_promotion_status", ""),
            "error_code": candidate_payload.get("error_code", ""),
            "stale_reasons": candidate_payload.get("stale_reasons", []),
        },
        "protocol_inquiry_followup_chain": {
            "protocol_inquiry_followup_chain_status": inquiry_payload.get("protocol_inquiry_followup_chain_status"),
            "candidate_decision": inquiry_payload.get("candidate_decision", ""),
            "candidate_status": inquiry_payload.get("candidate_status", ""),
            "inquiry_state": inquiry_payload.get("inquiry_state", ""),
            "followup_question_set": inquiry_payload.get("followup_question_set", []),
            "signal_origin": inquiry_payload.get("signal_origin", ""),
            "sanitization_paraphrase_ref": inquiry_payload.get("sanitization_paraphrase_ref", ""),
            "protocol_feedback_seed_ref": inquiry_payload.get("protocol_feedback_seed_ref", ""),
            "protocol_feedback_index_ref": inquiry_payload.get("protocol_feedback_index_ref", ""),
            "followup_round_count": inquiry_payload.get("followup_round_count"),
            "max_followup_rounds": inquiry_payload.get("max_followup_rounds"),
            "latest_evidence_age_hours": inquiry_payload.get("latest_evidence_age_hours"),
            "evidence_ttl_hours": inquiry_payload.get("evidence_ttl_hours"),
            "inquiry_requiredization_triggered": inquiry_payload.get("inquiry_requiredization_triggered"),
            "inquiry_requiredization_receipt_path": inquiry_payload.get("inquiry_requiredization_receipt_path", ""),
            "error_code": inquiry_payload.get("error_code", ""),
            "stale_reasons": inquiry_payload.get("stale_reasons", []),
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
        "external_source_trust_chain": {
            "external_source_trust_chain_status": source_trust_payload.get("external_source_trust_chain_status"),
            "error_code": source_trust_payload.get("error_code", ""),
            "required_contract": source_trust_payload.get("required_contract"),
            "auto_required_signal": source_trust_payload.get("auto_required_signal"),
            "feedback_batch_path": source_trust_payload.get("feedback_batch_path"),
            "allowed_trust_tiers": source_trust_payload.get("allowed_trust_tiers", []),
            "conclusion_required_tiers": source_trust_payload.get("conclusion_required_tiers", []),
            "source_row_count": source_trust_payload.get("source_row_count"),
            "conclusion_source_count": source_trust_payload.get("conclusion_source_count"),
            "candidate_source_count": source_trust_payload.get("candidate_source_count"),
            "unknown_in_conclusion_refs": source_trust_payload.get("unknown_in_conclusion_refs", []),
            "missing_tier_refs": source_trust_payload.get("missing_tier_refs", []),
            "missing_trace_refs": source_trust_payload.get("missing_trace_refs", []),
            "unknown_candidate_without_downgrade": source_trust_payload.get("unknown_candidate_without_downgrade", []),
            "stale_reasons": source_trust_payload.get("stale_reasons", []),
        },
        "protocol_data_sanitization_boundary": {
            "protocol_data_sanitization_boundary_status": sanitization_payload.get(
                "protocol_data_sanitization_boundary_status"
            ),
            "error_code": sanitization_payload.get("error_code", ""),
            "required_contract": sanitization_payload.get("required_contract"),
            "auto_required_signal": sanitization_payload.get("auto_required_signal"),
            "feedback_batch_path": sanitization_payload.get("feedback_batch_path"),
            "forbidden_key_hits": sanitization_payload.get("forbidden_key_hits", []),
            "sensitive_pattern_hits": sanitization_payload.get("sensitive_pattern_hits", []),
            "violation_count": sanitization_payload.get("violation_count"),
            "stale_reasons": sanitization_payload.get("stale_reasons", []),
        },
        "platform_optimization_discovery_trigger": {
            "platform_optimization_discovery_status": opt_trigger_payload.get("platform_optimization_discovery_status"),
            "error_code": opt_trigger_payload.get("error_code", ""),
            "required_contract": opt_trigger_payload.get("required_contract"),
            "auto_required_signal": opt_trigger_payload.get("auto_required_signal"),
            "triggered": opt_trigger_payload.get("triggered", False),
            "trigger_reason": opt_trigger_payload.get("trigger_reason", ""),
            "discovery_scope": opt_trigger_payload.get("discovery_scope", ""),
            "official_doc_retrieval_set": opt_trigger_payload.get("official_doc_retrieval_set", []),
            "cross_validation_summary": opt_trigger_payload.get("cross_validation_summary", {}),
            "upgrade_proposal_ref": opt_trigger_payload.get("upgrade_proposal_ref", ""),
            "feedback_batches": opt_trigger_payload.get("feedback_batches", []),
            "stale_reasons": opt_trigger_payload.get("stale_reasons", []),
        },
        "discovery_requiredization": {
            "discovery_requiredization_status": dreq_payload.get("discovery_requiredization_status"),
            "error_code": dreq_payload.get("error_code", ""),
            "required_contract": dreq_payload.get("required_contract"),
            "required_contract_declared": dreq_payload.get("required_contract_declared"),
            "auto_required_signal": dreq_payload.get("auto_required_signal"),
            "requiredization_triggered": dreq_payload.get("requiredization_triggered"),
            "trigger_classes": dreq_payload.get("trigger_classes", []),
            "window_rounds": dreq_payload.get("window_rounds"),
            "feedback_batches": dreq_payload.get("feedback_batches", []),
            "trigger_condition_flags": dreq_payload.get("trigger_condition_flags", {}),
            "discovery_contract_required_state": dreq_payload.get("discovery_contract_required_state", {}),
            "requiredized_all_discovery_contracts": dreq_payload.get("requiredized_all_discovery_contracts"),
            "requiredization_receipt_path": dreq_payload.get("requiredization_receipt_path", ""),
            "requiredization_receipt_linked": dreq_payload.get("requiredization_receipt_linked"),
            "evidence_index_path": dreq_payload.get("evidence_index_path", ""),
            "ci_required_validators_missing": dreq_payload.get("ci_required_validators_missing", []),
            "discovery_required_total": dreq_payload.get("discovery_required_total"),
            "discovery_required_passed": dreq_payload.get("discovery_required_passed"),
            "discovery_required_coverage_rate": dreq_payload.get("discovery_required_coverage_rate"),
            "stale_reasons": dreq_payload.get("stale_reasons", []),
        },
        "vibe_coding_feeding_pack": {
            "vibe_coding_feeding_pack_status": vibe_pack_payload.get("vibe_coding_feeding_pack_status"),
            "error_code": vibe_pack_payload.get("error_code", ""),
            "required_contract": vibe_pack_payload.get("required_contract"),
            "auto_required_signal": vibe_pack_payload.get("auto_required_signal"),
            "pack_root": vibe_pack_payload.get("pack_root", ""),
            "pack_id": vibe_pack_payload.get("pack_id", ""),
            "pack_files": vibe_pack_payload.get("pack_files", []),
            "feedback_batch_path": vibe_pack_payload.get("feedback_batch_path", ""),
            "feedback_batch_sha256": vibe_pack_payload.get("feedback_batch_sha256", ""),
            "evidence_index_path": vibe_pack_payload.get("evidence_index_path", ""),
            "evidence_index_linked": vibe_pack_payload.get("evidence_index_linked", False),
            "deterministic_manifest_sha256": vibe_pack_payload.get("deterministic_manifest_sha256", ""),
            "sanitization_check_passed": vibe_pack_payload.get("sanitization_check_passed", True),
            "stale_reasons": vibe_pack_payload.get("stale_reasons", []),
        },
        "capability_fit_optimization": {
            "capability_fit_optimization_status": cap_fit_payload.get("capability_fit_optimization_status"),
            "error_code": cap_fit_payload.get("error_code", ""),
            "required_contract": cap_fit_payload.get("required_contract"),
            "fit_matrix_path": cap_fit_payload.get("fit_matrix_path", ""),
            "matrix_candidate_count": cap_fit_payload.get("matrix_candidate_count"),
            "selected_candidate_count": cap_fit_payload.get("selected_candidate_count"),
            "selected_candidate_ids": cap_fit_payload.get("selected_candidate_ids", []),
            "missing_required_fields": cap_fit_payload.get("missing_required_fields", []),
            "selected_missing_fields": cap_fit_payload.get("selected_missing_fields", []),
            "next_review_at": cap_fit_payload.get("next_review_at", ""),
            "review_interval_days": cap_fit_payload.get("review_interval_days"),
            "review_freshness_status": cap_fit_payload.get("review_freshness_status", ""),
            "stale_reasons": cap_fit_payload.get("stale_reasons", []),
        },
        "capability_composition_before_discovery": {
            "compose_before_discovery_status": compose_payload.get("compose_before_discovery_status"),
            "error_code": compose_payload.get("error_code", ""),
            "required_contract": compose_payload.get("required_contract"),
            "fit_matrix_path": compose_payload.get("fit_matrix_path", ""),
            "existing_composition_candidate_count": compose_payload.get("existing_composition_candidate_count"),
            "selected_candidate_type": compose_payload.get("selected_candidate_type", ""),
            "decision_basis": compose_payload.get("decision_basis", ""),
            "stale_reasons": compose_payload.get("stale_reasons", []),
        },
        "capability_fit_review_freshness": {
            "capability_fit_review_freshness_status": fit_fresh_payload.get("capability_fit_review_freshness_status"),
            "error_code": fit_fresh_payload.get("error_code", ""),
            "required_contract": fit_fresh_payload.get("required_contract"),
            "fit_matrix_path": fit_fresh_payload.get("fit_matrix_path", ""),
            "selected_candidate_id": fit_fresh_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_fresh_payload.get("selected_candidate_type", ""),
            "next_review_at": fit_fresh_payload.get("next_review_at", ""),
            "review_interval_days": fit_fresh_payload.get("review_interval_days"),
            "review_freshness_status": fit_fresh_payload.get("review_freshness_status", ""),
            "overdue_by_days": fit_fresh_payload.get("overdue_by_days"),
            "stale_reasons": fit_fresh_payload.get("stale_reasons", []),
        },
        "capability_fit_roundtable_evidence": {
            "capability_fit_roundtable_status": fit_roundtable_payload.get("capability_fit_roundtable_status"),
            "error_code": fit_roundtable_payload.get("error_code", ""),
            "required_contract": fit_roundtable_payload.get("required_contract"),
            "fit_matrix_path": fit_roundtable_payload.get("fit_matrix_path", ""),
            "roundtable_evidence_path": fit_roundtable_payload.get("roundtable_evidence_path", ""),
            "selected_candidate_id": fit_roundtable_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_roundtable_payload.get("selected_candidate_type", ""),
            "roundtable_required": fit_roundtable_payload.get("roundtable_required", False),
            "facts_count": fit_roundtable_payload.get("facts_count"),
            "inferences_count": fit_roundtable_payload.get("inferences_count"),
            "selected_fact_refs": fit_roundtable_payload.get("selected_fact_refs", []),
            "stale_reasons": fit_roundtable_payload.get("stale_reasons", []),
        },
        "capability_fit_review_trigger": {
            "capability_fit_review_trigger_status": fit_trigger_payload.get("capability_fit_review_trigger_status"),
            "error_code": fit_trigger_payload.get("error_code", ""),
            "required_contract": fit_trigger_payload.get("required_contract"),
            "triggered": fit_trigger_payload.get("triggered", False),
            "trigger_reason": fit_trigger_payload.get("trigger_reason", ""),
            "fit_matrix_path": fit_trigger_payload.get("fit_matrix_path", ""),
            "selected_candidate_id": fit_trigger_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_trigger_payload.get("selected_candidate_type", ""),
            "review_freshness_status": fit_trigger_payload.get("review_freshness_status", ""),
            "roundtable_required": fit_trigger_payload.get("roundtable_required", False),
            "roundtable_evidence_path": fit_trigger_payload.get("roundtable_evidence_path", ""),
            "stale_reasons": fit_trigger_payload.get("stale_reasons", []),
        },
        "capability_fit_matrix_builder": {
            "capability_fit_matrix_builder_status": fit_builder_payload.get("capability_fit_matrix_builder_status"),
            "error_code": fit_builder_payload.get("error_code", ""),
            "required_contract": fit_builder_payload.get("required_contract"),
            "matrix_path": fit_builder_payload.get("matrix_path", ""),
            "matrix_candidate_count": fit_builder_payload.get("matrix_candidate_count"),
            "selected_candidate_count": fit_builder_payload.get("selected_candidate_count"),
            "selected_candidate_id": fit_builder_payload.get("selected_candidate_id", ""),
            "selected_candidate_type": fit_builder_payload.get("selected_candidate_type", ""),
            "inventory_snapshot_path": fit_builder_payload.get("inventory_snapshot_path", ""),
            "external_candidate_source_path": fit_builder_payload.get("external_candidate_source_path", ""),
            "stale_reasons": fit_builder_payload.get("stale_reasons", []),
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
        "actor_session_multibinding_concurrency": {
            "actor_session_multibinding_status": actor_mb_payload.get("actor_session_multibinding_status"),
            "error_code": actor_mb_payload.get("error_code", ""),
            "binding_key_mode": actor_mb_payload.get("binding_key_mode", ""),
            "session_entry_count": actor_mb_payload.get("session_entry_count"),
            "cas_checked": actor_mb_payload.get("cas_checked"),
            "cas_conflict_detected": actor_mb_payload.get("cas_conflict_detected"),
            "non_activation_mutation_detected": actor_mb_payload.get("non_activation_mutation_detected"),
            "rebind_receipt_status": actor_mb_payload.get("rebind_receipt_status", ""),
            "dropped_peer_session_count": actor_mb_payload.get("dropped_peer_session_count"),
            "stale_reasons": actor_mb_payload.get("stale_reasons", []),
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
            "protocol_head_sha_at_run_start": refresh_payload.get("protocol_head_sha_at_run_start", ""),
            "baseline_reference_mode": refresh_payload.get("baseline_reference_mode", ""),
            "current_protocol_head_sha": refresh_payload.get("current_protocol_head_sha", ""),
            "head_drift_detected": refresh_payload.get("head_drift_detected", False),
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
            "reply_first_line_status": reply_first_line_payload.get("reply_first_line_status"),
            "reply_first_line_error_code": reply_first_line_payload.get("error_code", ""),
            "reply_first_line_missing_count": reply_first_line_payload.get("reply_first_line_missing_count", 0),
            "reply_first_line_missing_refs": reply_first_line_payload.get("reply_first_line_missing_refs", []),
            "reply_first_line_blocker_receipt_path": reply_first_line_payload.get("blocker_receipt_path", ""),
            "layer_intent_resolution_status": layer_intent_payload.get("layer_intent_resolution_status", ""),
            "layer_intent_error_code": layer_intent_payload.get("error_code", ""),
            "resolved_work_layer": layer_intent_payload.get("resolved_work_layer", ""),
            "resolved_source_layer": layer_intent_payload.get("resolved_source_layer", ""),
            "layer_intent_confidence": layer_intent_payload.get("intent_confidence"),
            "layer_intent_source": layer_intent_payload.get("intent_source", ""),
            "layer_intent_fallback_reason": layer_intent_payload.get("fallback_reason", ""),
            "send_time_gate_status": send_time_gate_payload.get("send_time_gate_status"),
            "send_time_gate_error_code": send_time_gate_payload.get("error_code", ""),
            "send_time_reply_evidence_mode": send_time_gate_payload.get("reply_evidence_mode", ""),
            "send_time_reply_evidence_ref": send_time_gate_payload.get("reply_evidence_ref", ""),
            "send_time_reply_sample_count": send_time_gate_payload.get("reply_sample_count", 0),
            "send_time_reply_missing_count": send_time_gate_payload.get("reply_first_line_missing_count", 0),
            "send_time_reply_missing_refs": send_time_gate_payload.get("reply_first_line_missing_refs", []),
            "send_time_blocker_receipt_path": send_time_gate_payload.get("blocker_receipt_path", ""),
            "reply_coherence_status": reply_coherence_payload.get("coherence_status"),
            "reply_coherence_error_code": reply_coherence_payload.get("error_code", ""),
            "reply_coherence_decision": reply_coherence_payload.get("coherence_decision", ""),
            "reply_coherence_mismatch_fields": reply_coherence_payload.get("mismatch_fields", []),
            "reply_coherence_command_catalog_ref": reply_coherence_payload.get("command_catalog_ref", ""),
            "reply_coherence_resolved_catalog_ref": reply_coherence_payload.get("resolved_catalog_ref", ""),
            "reply_coherence_catalog_ref": reply_coherence_payload.get("reply_catalog_ref", ""),
            "reply_coherence_blocker_receipt_path": reply_coherence_payload.get("blocker_receipt_path", ""),
            "external_stamp": stamp_render_payload.get("external_stamp"),
            "stale_reasons": stamp_payload.get("stale_reasons", []),
            "first_line_stale_reasons": reply_first_line_payload.get("stale_reasons", []),
            "layer_intent_stale_reasons": layer_intent_payload.get("stale_reasons", []),
            "send_time_stale_reasons": send_time_gate_payload.get("stale_reasons", []),
            "coherence_stale_reasons": reply_coherence_payload.get("stale_reasons", []),
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
            "protocol_head_sha_at_run_start": baseline_payload.get("protocol_head_sha_at_run_start"),
            "baseline_reference_mode": baseline_payload.get("baseline_reference_mode"),
            "current_protocol_head_sha": baseline_payload.get("current_protocol_head_sha"),
            "head_drift_detected": baseline_payload.get("head_drift_detected", False),
            "lag_commits": baseline_payload.get("lag_commits"),
            "stale_reasons": baseline_payload.get("stale_reasons", []),
        },
        "protocol_version_alignment": {
            "protocol_version_alignment_status": align_payload.get("protocol_version_alignment_status"),
            "error_code": align_payload.get("error_code", ""),
            "operation": align_payload.get("operation"),
            "alignment_policy": align_payload.get("alignment_policy"),
            "report_selected_path": align_payload.get("report_selected_path"),
            "tuple_checks": align_payload.get("tuple_checks", {}),
            "stale_reasons": align_payload.get("stale_reasons", []),
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
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent passed to stamp render/reply gates")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not args.catalog:
        print("[FAIL] --catalog is required (or export IDENTITY_CATALOG first).")
        return 2
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_arg = Path(args.repo_catalog).expanduser()
    if repo_catalog_arg.is_absolute():
        repo_catalog_path = repo_catalog_arg.resolve()
    else:
        repo_catalog_path = (PROTOCOL_ROOT / repo_catalog_arg).resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(
            "[FAIL] IP-CWD-004 repo catalog not found under protocol-root deterministic resolution: "
            f"{repo_catalog_path} (hint: pass explicit --repo-catalog <absolute-path>)"
        )
        return 2
    args.repo_catalog = str(repo_catalog_path)

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
