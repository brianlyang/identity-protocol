#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import time
from typing import Any

import yaml

from response_stamp_common import DEFAULT_WORK_LAYER, resolve_layer_intent
from resolve_identity_context import collect_protocol_evidence, default_identity_home, resolve_identity

PROTOCOL_PUBLISH_CHECKS = {
    "scripts/validate_changelog_updated.py",
    "scripts/validate_protocol_handoff_coupling.py",
    "scripts/validate_release_metadata_sync.py",
    "scripts/validate_release_freeze_boundary.py",
}


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _lane_context(layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> dict[str, Any]:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="global",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    source_layer = str(resolved.get("resolved_source_layer", "global")).strip().lower() or "global"
    if work_layer == "instance":
        applied_gate_set = "instance_required_checks"
    elif work_layer == "protocol":
        applied_gate_set = "protocol_required_checks"
    else:
        applied_gate_set = "dual_unroutable"
    lane_transition_reason = (
        "explicit_work_layer_override"
        if str(resolved.get("intent_source", "")).strip() == "explicit_arg"
        else str(resolved.get("fallback_reason", "")).strip()
        or ("protocol_trigger_detected" if bool(resolved.get("protocol_triggered", False)) else "instance_default_fallback")
    )
    return {
        "work_layer": work_layer,
        "source_layer": source_layer,
        "applied_gate_set": applied_gate_set,
        "lane_transition_reason": lane_transition_reason,
    }


def _filter_required_checks_for_lane(required_checks: list[str], work_layer: str) -> tuple[list[str], list[str]]:
    if work_layer != "instance":
        return list(required_checks), []
    filtered: list[str] = []
    skipped: list[str] = []
    for chk in required_checks:
        token = str(chk or "").strip()
        if token in PROTOCOL_PUBLISH_CHECKS:
            skipped.append(token)
            continue
        filtered.append(token)
    return filtered, skipped


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_pack(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path)
        if p.exists():
            return p
    legacy = Path("identity") / identity_id
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"identity pack not found: {identity_id}")


def _resolve_prompt_contract(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    resolved_scope: str,
    resolved_pack_path: str,
) -> dict[str, Any]:
    source_layer = "local"
    scope = str(resolved_scope or "").strip()
    pack = Path(str(resolved_pack_path or "")).expanduser().resolve() if str(resolved_pack_path or "").strip() else None
    if pack is None:
        ctx = resolve_identity(
            identity_id,
            repo_catalog_path.expanduser().resolve(),
            catalog_path.expanduser().resolve(),
            preferred_scope=scope,
            allow_conflict=True,
        )
        source_layer = str(ctx.get("source_layer", "local"))
        scope = str(ctx.get("resolved_scope", "")).strip()
        pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    prompt_path = pack / "IDENTITY_PROMPT.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    runtime_state_path = (pack / "runtime" / "state" / "prompt_contract.json").resolve()
    runtime_state_doc: dict[str, Any] = {}
    runtime_state_hash = ""
    runtime_state_binding_status = "MISSING"
    runtime_state_externalization_status = "MISSING"
    runtime_state_error_code = ""
    contract = {
        "identity_prompt_path": str(prompt_path),
        "identity_prompt_sha256": "",
        "identity_prompt_bytes": 0,
        "identity_prompt_activated_at": now,
        "identity_prompt_source_layer": source_layer,
        "identity_prompt_scope": scope,
        "identity_prompt_status": "MISSING",
        "runtime_state_artifact_path": str(runtime_state_path),
        "runtime_state_artifact_hash": "",
        "prompt_runtime_state_binding_status": runtime_state_binding_status,
        "prompt_runtime_state_externalization_status": runtime_state_externalization_status,
        "prompt_runtime_state_externalization_error_code": runtime_state_error_code,
    }
    if prompt_path.exists():
        try:
            contract["identity_prompt_sha256"] = _sha256_file(prompt_path)
            contract["identity_prompt_bytes"] = int(prompt_path.stat().st_size)
            contract["identity_prompt_status"] = "ACTIVATED"
            prompt_text = prompt_path.read_text(encoding="utf-8", errors="ignore")
            if "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:BEGIN -->" in prompt_text:
                runtime_state_externalization_status = "FAIL_REQUIRED"
                runtime_state_error_code = "IP-PROMPT-STATE-001"
            else:
                runtime_state_externalization_status = "PASS_REQUIRED"
        except Exception:
            contract["identity_prompt_status"] = "ERROR"
            runtime_state_externalization_status = "FAIL_REQUIRED"
            runtime_state_error_code = "IP-PROMPT-STATE-001"
    if runtime_state_path.exists():
        try:
            runtime_state_doc = _load_json(runtime_state_path)
            runtime_state_hash = _sha256_file(runtime_state_path)
        except Exception:
            runtime_state_doc = {}
            runtime_state_hash = ""
    if runtime_state_doc:
        bound_hash = str(runtime_state_doc.get("prompt_policy_hash", "")).strip()
        if bound_hash and bound_hash == str(contract.get("identity_prompt_sha256", "")).strip():
            runtime_state_binding_status = "PASS_REQUIRED"
        else:
            runtime_state_binding_status = "FAIL_REQUIRED"
    contract["runtime_state_artifact_hash"] = runtime_state_hash
    contract["prompt_runtime_state_binding_status"] = runtime_state_binding_status
    contract["prompt_runtime_state_externalization_status"] = runtime_state_externalization_status
    contract["prompt_runtime_state_externalization_error_code"] = runtime_state_error_code
    return contract


def _apply_prompt_contract_update(
    *,
    prompt_path: Path,
    run_id: str,
    mode: str,
    trigger_reasons: list[str],
) -> tuple[bool, str, str, str, str, str]:
    """
    Write deterministic runtime-contract metadata to runtime/state artifact.
    Returns: (applied, note, hash_before, hash_after, runtime_state_path, runtime_state_hash)
    """
    if not prompt_path.exists():
        raise FileNotFoundError(f"identity prompt missing: {prompt_path}")
    hash_before = _sha256_file(prompt_path)
    hash_after = hash_before
    legacy_removed = False
    text = prompt_path.read_text(encoding="utf-8", errors="ignore")
    begin = "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:BEGIN -->"
    end = "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:END -->"
    if begin in text and end in text:
        s = text.index(begin)
        e = text.index(end) + len(end)
        prefix = text[:s].rstrip()
        suffix = text[e:].lstrip("\n")
        merged = "\n\n".join([x for x in [prefix, suffix] if x]).rstrip() + "\n"
        if merged != text:
            prompt_path.write_text(merged, encoding="utf-8")
            legacy_removed = True
            hash_after = _sha256_file(prompt_path)
    else:
        hash_after = hash_before
    runtime_state_path = (prompt_path.parent / "runtime" / "state" / "prompt_contract.json").resolve()
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "schema": "prompt_runtime_state_v1",
        "identity_prompt_path": str(prompt_path),
        "prompt_policy_hash": hash_after,
        "last_upgrade_run_id": run_id,
        "last_upgrade_mode": mode,
        "last_upgrade_at": now,
        "last_trigger_reasons": trigger_reasons or [],
    }
    _write_json(runtime_state_path, payload)
    runtime_state_hash = _sha256_file(runtime_state_path)
    note = "runtime_state_artifact_updated"
    if legacy_removed:
        note = "runtime_state_artifact_updated;legacy_runtime_block_removed"
    return True, note, hash_before, hash_after, str(runtime_state_path), runtime_state_hash


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], log_dir: Path, run_id: str, idx: int) -> dict[str, Any]:
    start = datetime.now(timezone.utc)
    t0 = time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    end = datetime.now(timezone.utc)
    elapsed_ms = int((time() - t0) * 1000)
    log_path = log_dir / f"{run_id}-check-{idx:02d}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_content = (
        f"$ {' '.join(cmd)}\n"
        f"[exit_code] {p.returncode}\n"
        f"[started_at] {start.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"[ended_at] {end.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"[stdout]\n{p.stdout}\n"
        f"[stderr]\n{p.stderr}\n"
    )
    log_path.write_text(log_content, encoding="utf-8")
    log_sha256 = _sha256_file(log_path)
    return {
        "command": " ".join(cmd),
        "cmd": " ".join(cmd),
        "code": p.returncode,
        "ok": p.returncode == 0,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
        "started_at": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_ms": elapsed_ms,
        "exit_code": p.returncode,
        "log_path": str(log_path),
        "sha256": log_sha256,
    }


def _extract_baseline_signal(
    checks: list[dict[str, Any]],
    *,
    protocol_head_sha_at_run_start: str,
) -> dict[str, Any]:
    default = {
        "protocol_head_sha_at_run_start": str(protocol_head_sha_at_run_start or "").strip(),
        "baseline_reference_mode": "run_pinned",
        "current_protocol_head_sha": "",
        "head_drift_detected": False,
        "baseline_status": "UNKNOWN",
        "baseline_error_code": "",
    }
    for row in checks:
        cmd = str(row.get("cmd", "")).strip()
        if "validate_identity_protocol_baseline_freshness.py" not in cmd:
            continue
        payload = _parse_json_payload(str(row.get("stdout", "")).strip()) or {}
        if not isinstance(payload, dict):
            return default
        out = dict(default)
        for key in (
            "protocol_head_sha_at_run_start",
            "baseline_reference_mode",
            "current_protocol_head_sha",
            "head_drift_detected",
            "baseline_status",
            "baseline_error_code",
        ):
            if key in payload:
                out[key] = payload.get(key)
        if not str(out.get("protocol_head_sha_at_run_start", "")).strip():
            out["protocol_head_sha_at_run_start"] = str(protocol_head_sha_at_run_start or "").strip()
        return out
    return default


def _build_skipped_check_results(
    *,
    check_cmds: list[list[str]],
    log_dir: Path,
    run_id: str,
    reason: str,
    exit_code: int = 97,
) -> list[dict[str, Any]]:
    """
    Build synthetic check/check_results rows for recoverable preflight-blocked flows.
    Keeps report contract machine-auditable while preserving fail-operational semantics.
    """
    start = datetime.now(timezone.utc)
    started = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict[str, Any]] = []
    log_dir.mkdir(parents=True, exist_ok=True)
    for i, cmd in enumerate(check_cmds, start=1):
        ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_path = log_dir / f"{run_id}-check-{i:02d}.log"
        log_content = (
            f"$ {' '.join(cmd)}\n"
            f"[exit_code] {exit_code}\n"
            f"[started_at] {started}\n"
            f"[ended_at] {ended}\n\n"
            f"[stdout]\n\n"
            f"[stderr]\n"
            f"skipped_preflight_blocked: {reason}\n"
        )
        log_path.write_text(log_content, encoding="utf-8")
        log_sha256 = _sha256_file(log_path)
        rows.append(
            {
                "command": " ".join(cmd),
                "cmd": " ".join(cmd),
                "code": exit_code,
                "ok": False,
                "stdout": "",
                "stderr": f"skipped_preflight_blocked:{reason}",
                "started_at": started,
                "ended_at": ended,
                "duration_ms": 0,
                "exit_code": exit_code,
                "log_path": str(log_path),
                "sha256": log_sha256,
            }
        )
    return rows


def _resolve_git_range() -> tuple[str, str]:
    def _git(cmd: list[str]) -> str:
        p = subprocess.run(["git", *cmd], capture_output=True, text=True)
        return (p.stdout or "").strip() if p.returncode == 0 else ""

    base = os.environ.get("PR_BASE_SHA") or os.environ.get("GITHUB_BASE_SHA") or os.environ.get("PUSH_BEFORE_SHA") or os.environ.get("GITHUB_EVENT_BEFORE") or ""
    head = os.environ.get("PR_HEAD_SHA") or os.environ.get("GITHUB_SHA") or ""
    if not head:
        head = _git(["rev-parse", "HEAD"])
    if not base:
        base = _git(["rev-parse", "HEAD~1"])
    return base or "HEAD~1", head or "HEAD"


def _build_validator_cmd(check: str, identity_id: str, catalog_path: str) -> list[str]:
    if not check.startswith("scripts/"):
        return ["python3", check]
    cmd = ["python3", check]
    if check.endswith("validate_changelog_updated.py"):
        base, head = _resolve_git_range()
        return ["python3", check, "--base", base, "--head", head]
    if check.endswith("validate_identity_self_upgrade_enforcement.py"):
        base, head = _resolve_git_range()
        return ["python3", check, "--identity-id", identity_id, "--base", base, "--head", head]
    if check.endswith("validate_identity_manifest.py") or check.endswith("compile_identity_runtime.py"):
        return cmd
    # most validators are identity scoped
    if "--identity-id" not in check:
        cmd += ["--identity-id", identity_id]
    if check.startswith("scripts/validate_") and "--catalog" not in check:
        cmd += ["--catalog", catalog_path]
    if check.endswith("validate_identity_collab_trigger.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_agent_handoff_contract.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_identity_knowledge_contract.py"):
        cmd += ["--self-test"]
    if check.endswith("validate_identity_experience_feedback.py"):
        cmd += ["--self-test"]
    return cmd


def _needs_upgrade(metrics: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    misroute = float(metrics.get("misroute_rate", 0))
    replay_fail = max(0.0, 100.0 - float(metrics.get("replay_success_rate", 100.0)))
    first_pass = float(metrics.get("first_pass_success_rate", 100.0))

    if misroute >= float(thresholds.get("misroute_rate_percent", 999)):
        reasons.append(f"misroute_rate {misroute} >= threshold {thresholds.get('misroute_rate_percent')}")
    if replay_fail >= float(thresholds.get("replay_failure_rate_percent", 999)):
        reasons.append(f"replay_failure_rate {replay_fail} >= threshold {thresholds.get('replay_failure_rate_percent')}")
    if (100.0 - first_pass) >= float(thresholds.get("first_pass_success_drop_percent", 999)):
        reasons.append(
            f"first_pass_success_drop {100.0-first_pass} >= threshold {thresholds.get('first_pass_success_drop_percent')}"
        )
    return (len(reasons) > 0), reasons


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _path_allowed(path: str, allowlist: list[str], denylist: list[str]) -> tuple[bool, str]:
    for pat in denylist:
        if fnmatch.fnmatch(path, pat):
            return False, f"denied by pattern: {pat}"
    for pat in allowlist:
        if fnmatch.fnmatch(path, pat):
            return True, f"allowed by pattern: {pat}"
    return False, "not matched by allowlist"


def _append_task_history(history_path: Path, line: str) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(f"\n- {line}\n")


def _writable_precheck(path: Path) -> tuple[bool, str]:
    parent = path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return False, f"parent_mkdir_failed:{exc}"
    if path.exists() and not os.access(path, os.W_OK):
        return False, "path_not_writable"
    if not os.access(parent, os.W_OK):
        return False, "parent_not_writable"
    return True, "ok"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _resolve_runtime_output_root(effective_pack: Path, identity_id: str, protocol_root: Path) -> Path:
    env = os.environ.get("IDENTITY_RUNTIME_OUTPUT_ROOT", "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env).expanduser().resolve())
    candidates.append(effective_pack / "runtime")

    skipped: list[str] = []
    for c in candidates:
        if _is_within(c, protocol_root):
            skipped.append(f"{c} (inside protocol_root={protocol_root})")
            continue
        # P0 hard constraint: runtime output root must align to resolved pack domain.
        # Allow only "<resolved_pack_path>/runtime" (or a subpath under it).
        allowed_root = (effective_pack / "runtime").resolve()
        if not _is_within(c, allowed_root):
            skipped.append(
                f"{c} (runtime_output_root not aligned with resolved_pack_path runtime={allowed_root})"
            )
            continue
        try:
            c.mkdir(parents=True, exist_ok=True)
            return c
        except Exception:
            continue
    hint = (
        "set IDENTITY_RUNTIME_OUTPUT_ROOT to a writable non-protocol path, "
        "or migrate identity pack via identity_installer adopt+lock."
    )
    raise PermissionError(
        "IP-PATH-001 unable to resolve runtime output root outside protocol root; "
        f"identity={identity_id}; resolved_pack_path={effective_pack}; skipped={skipped}; hint={hint}"
    )


def _base_report(
    *,
    run_id: str,
    identity_id: str,
    now: str,
    mode: str,
    protocol: dict[str, str],
    catalog_path: str,
    resolved_scope: str,
    resolved_pack_path: str,
    runtime_output_root: str,
    metrics_path: str,
    prompt_contract: dict[str, Any],
    capability_contract: dict[str, Any] | None = None,
    required_checks: list[str] | None = None,
    required_checks_raw: list[str] | None = None,
    skipped_protocol_publish_checks: list[str] | None = None,
    work_layer: str = "",
    source_layer: str = "",
    applied_gate_set: str = "",
    lane_transition_reason: str = "",
    protocol_feedback_triggered: bool = False,
    protocol_feedback_paths: list[str] | None = None,
    lane_routing_status: str = "",
    lane_routing_error_code: str = "",
    phase_a_refresh_applied: bool = False,
    phase_b_strict_revalidate_status: str = "NOT_APPLICABLE",
    phase_transition_reason: str = "",
    phase_transition_error_code: str = "",
) -> dict[str, Any]:
    """
    Build a report skeleton with mandatory closure fields always present.
    This keeps failed/blocked/safe-auto reports machine-auditable.
    """
    capability_contract = capability_contract or {}
    required_checks = required_checks or []
    required_checks_raw = required_checks_raw or []
    skipped_protocol_publish_checks = skipped_protocol_publish_checks or []
    protocol_feedback_paths = protocol_feedback_paths or []
    return {
        "run_id": run_id,
        "identity_id": identity_id,
        "generated_at": now,
        "mode": mode,
        "creator_invocation": {
            "tool": "identity-creator",
            "mode": "update",
            "entrypoint": "scripts/execute_identity_upgrade.py",
            "base_contract": "identity_update_lifecycle_contract",
            "run_id": run_id,
        },
        "execution_context": {
            "generated_by": "ci" if os.environ.get("CI") else "local",
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_sha": os.environ.get("GITHUB_SHA", ""),
        },
        "required_checks": list(required_checks),
        "required_checks_raw": list(required_checks_raw),
        "skipped_protocol_publish_checks": list(skipped_protocol_publish_checks),
        "work_layer": str(work_layer or ""),
        "source_layer": str(source_layer or ""),
        "applied_gate_set": str(applied_gate_set or ""),
        "lane_transition_reason": str(lane_transition_reason or ""),
        "protocol_feedback_triggered": bool(protocol_feedback_triggered),
        "protocol_feedback_paths": list(protocol_feedback_paths),
        "lane_routing_status": str(lane_routing_status or ""),
        "lane_routing_error_code": str(lane_routing_error_code or ""),
        "phase_a_refresh_applied": bool(phase_a_refresh_applied),
        "phase_b_strict_revalidate_status": str(phase_b_strict_revalidate_status or "NOT_APPLICABLE"),
        "phase_transition_reason": str(phase_transition_reason or ""),
        "phase_transition_error_code": str(phase_transition_error_code or ""),
        "actions_taken": [],
        "checks": [],
        "check_results": [],
        "artifacts": [],
        "experience_writeback": {
            "required": False,
            "status": "MISSING",
            "error_code": "",
            "mode": mode,
            "rulebook_path": "",
            "task_history_path": "",
            "rule_entry_id": "",
            "history_contains_run_id": False,
            "notes": "",
        },
        "writeback_paths": [],
        "writeback_status": "MISSING",
        "writeback_rule_id": "",
        "writeback_mode": "STRICT_WRITEBACK",
        "degrade_reason": "",
        "risk_level": "",
        "next_recovery_action": "",
        "all_ok": False,
        "permission_state": "PRECHECK",
        "permission_error_code": "",
        "escalation_required": False,
        "escalation_recommendation": "",
        "writeback_precheck": {"all_writable": False, "reason": "unknown"},
        "runtime_output_root": runtime_output_root,
        "metrics_path": metrics_path,
        "skills_used": list(capability_contract.get("skills_used") or []),
        "mcp_tools_used": list(capability_contract.get("mcp_tools_used") or []),
        "tool_calls_used": list(capability_contract.get("tool_calls_used") or []),
        "active_skills": list(capability_contract.get("active_skills") or []),
        "mcp_servers_checked": list(capability_contract.get("mcp_servers_checked") or []),
        "tool_routes": list(capability_contract.get("tool_routes") or []),
        "capability_activation_status": str(capability_contract.get("capability_activation_status", "UNKNOWN")),
        "capability_activation_error_code": str(capability_contract.get("capability_activation_error_code", "")),
        "capability_activation_notes": list(capability_contract.get("capability_activation_notes") or []),
        "capability_contract_required": bool(capability_contract.get("capability_contract_required", True)),
        "next_action": "",
        "failure_reason": "",
        "protocol_mode": protocol["protocol_mode"],
        "protocol_root": protocol["protocol_root"],
        "protocol_commit_sha": protocol["protocol_commit_sha"],
        "protocol_head_sha_at_run_start": str(
            protocol.get("protocol_head_sha_at_run_start") or protocol.get("protocol_commit_sha") or ""
        ),
        "baseline_reference_mode": str(protocol.get("baseline_reference_mode") or "run_pinned"),
        "current_protocol_head_sha": "",
        "head_drift_detected": False,
        "baseline_status": "UNKNOWN",
        "baseline_error_code": "",
        "protocol_ref": protocol["protocol_ref"],
        "identity_home": str(default_identity_home()),
        "catalog_path": str(Path(catalog_path).expanduser().resolve()),
        "resolved_scope": str(resolved_scope or ""),
        "resolved_pack_path": str(resolved_pack_path or ""),
        "prompt_change_required": False,
        "prompt_change_applied": False,
        "identity_prompt_hash_before": str(prompt_contract.get("identity_prompt_sha256", "")),
        "identity_prompt_hash_after": str(prompt_contract.get("identity_prompt_sha256", "")),
        "identity_prompt_change_note": "",
        "prompt_policy_hash": str(prompt_contract.get("identity_prompt_sha256", "")),
        **prompt_contract,
    }


def _derive_writeback_continuity_fields(
    *,
    upgrade_required: bool,
    all_ok: bool,
    writeback_status: str,
    writeback_error_code: str,
    permission_error_code: str,
    next_action: str,
) -> dict[str, str]:
    ws = str(writeback_status or "").strip().upper()
    wb_err = str(writeback_error_code or "").strip().upper()
    perm_err = str(permission_error_code or "").strip().upper()
    na = str(next_action or "").strip()

    if not upgrade_required:
        return {
            "writeback_mode": "STRICT_WRITEBACK",
            "degrade_reason": "",
            "risk_level": "",
            "next_recovery_action": "",
        }

    if all_ok and ws == "WRITTEN":
        return {
            "writeback_mode": "STRICT_WRITEBACK",
            "degrade_reason": "",
            "risk_level": "",
            "next_recovery_action": "",
        }

    # Degraded mode for non-closure or recoverable execution paths.
    degrade_reason = "validator_failure_before_writeback"
    risk_level = "medium"
    recovery = na or "fix_failing_validators_and_rerun_update"

    if ws == "DEFERRED_PERMISSION_BLOCKED" or wb_err.startswith("IP-PERM-") or perm_err.startswith("IP-PERM-"):
        degrade_reason = "permission_blocked_writeback"
        risk_level = "high"
        recovery = na or "restore_write_permission_or_escalate_then_rerun_update"
    elif ws == "DEFERRED_POLICY_BLOCKED" or wb_err.startswith("IP-SAFEAUTO-") or perm_err.startswith("IP-UPG-001"):
        degrade_reason = "policy_blocked_writeback"
        risk_level = "high"
        recovery = na or "adjust_safe_auto_policy_or_switch_mode_then_rerun_update"
    elif ws == "DEFERRED_VALIDATION_FAILED" or wb_err.startswith("IP-UPG-"):
        degrade_reason = "validator_failure_before_writeback"
        risk_level = "medium"
        recovery = na or "resolve_validation_failures_then_rerun_update"
    elif ws in {"MISSING", "NOT_EXECUTED"}:
        degrade_reason = "writeback_not_executed"
        risk_level = "high"
        recovery = na or "produce_valid_execution_report_with_degraded_or_strict_writeback"

    return {
        "writeback_mode": "DEGRADED_WRITEBACK",
        "degrade_reason": degrade_reason,
        "risk_level": risk_level,
        "next_recovery_action": recovery,
    }


def _default_capability_contract_payload(
    *,
    identity_id: str,
    catalog_path: Path,
) -> dict[str, Any]:
    return {
        "identity_id": identity_id,
        "catalog_path": str(catalog_path.expanduser().resolve()),
        "skills_used": [],
        "mcp_tools_used": [],
        "tool_calls_used": [],
        "active_skills": [],
        "mcp_servers_checked": [],
        "tool_routes": [],
        "capability_activation_status": "ERROR",
        "capability_activation_error_code": "IP-CAP-000",
        "capability_activation_notes": ["validator_execution_failed"],
        "capability_contract_required": True,
    }


def _resolve_capability_contract(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    runtime_output_root: Path,
    run_id: str,
    activation_policy: str = "strict-union",
) -> dict[str, Any]:
    payload = _default_capability_contract_payload(identity_id=identity_id, catalog_path=catalog_path)
    out_path: Path | None = None
    out_candidates = [
        runtime_output_root / "logs" / "capability" / f"{identity_id}-{run_id}.json",
        Path("/tmp/identity-runtime") / identity_id / "logs" / "capability" / f"{identity_id}-{run_id}.json",
    ]
    for candidate in out_candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            out_path = candidate
            break
        except Exception:
            continue
    cmd = [
        "python3",
        "scripts/validate_identity_capability_activation.py",
        "--catalog",
        str(catalog_path.expanduser().resolve()),
        "--repo-catalog",
        str(repo_catalog_path.expanduser().resolve()),
        "--identity-id",
        identity_id,
        "--activation-policy",
        str(activation_policy or "strict-union"),
    ]
    if out_path is not None:
        cmd.extend(["--out", str(out_path)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if out_path is not None and out_path.exists():
        try:
            raw = _load_json(out_path)
            if isinstance(raw, dict):
                payload.update(raw)
        except Exception:
            pass
    payload["capability_activation_validator_rc"] = proc.returncode
    payload["capability_activation_validator_stdout_tail"] = (
        (proc.stdout or "").strip().splitlines()[-1] if (proc.stdout or "").strip() else ""
    )
    payload["capability_activation_validator_stderr_tail"] = (
        (proc.stderr or "").strip().splitlines()[-1] if (proc.stderr or "").strip() else ""
    )
    payload["capability_activation_report_path"] = str(out_path) if out_path is not None else ""
    if out_path is None:
        notes = list(payload.get("capability_activation_notes") or [])
        notes.append("capability_report_path_unwritable")
        payload["capability_activation_notes"] = notes
    return payload


def _capability_next_action(cap: dict[str, Any]) -> str:
    code = str(cap.get("capability_activation_error_code", "")).strip()
    if code == "IP-CAP-001":
        return "install_required_skills_then_rerun_update"
    if code == "IP-CAP-002":
        return "configure_required_mcp_then_rerun_update"
    return "resolve_capability_activation_then_rerun_update"


def _enforce_protocol_runtime_separation(
    pack: Path,
    resolved_pack_path: str,
    protocol_root: Path,
    *,
    allow_protocol_root_pack: bool,
    identity_id: str,
) -> Path:
    effective_pack = Path(resolved_pack_path).expanduser().resolve() if str(resolved_pack_path).strip() else pack.resolve()
    if _is_within(effective_pack, protocol_root):
        if allow_protocol_root_pack:
            return effective_pack
        raise PermissionError(
            "IP-PATH-001 pack_path is inside protocol_root; "
            f"identity={identity_id} pack_path={effective_pack} protocol_root={protocol_root}. "
            "Run identity_installer adopt+lock to move runtime identity outside protocol repo "
            "or pass --allow-protocol-root-pack for fixture/debug only."
        )
    return effective_pack


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Execute identity upgrade cycle using metrics + arbitration thresholds (safe-auto/review-required)."
    )
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--mode", choices=["review-required", "safe-auto"], default="review-required")
    ap.add_argument("--metrics-path", default="", help="optional route metrics artifact path override")
    ap.add_argument("--out-dir", default="/tmp/identity-upgrade-reports")
    ap.add_argument("--protocol-root", default="")
    ap.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--resolved-scope", default="")
    ap.add_argument("--resolved-pack-path", default="")
    ap.add_argument(
        "--capability-activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
        help=(
            "capability preflight policy used to evaluate skill/mcp route readiness before upgrade execution; "
            "strict-union requires all declared route capabilities, route-any-ready allows execution when at least one route is ready."
        ),
    )
    ap.add_argument(
        "--allow-protocol-root-pack",
        action="store_true",
        help="allow executing upgrade for identities whose pack_path is inside protocol root (fixture/debug only)",
    )
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent passthrough")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override")
    ap.add_argument("--phase-a-refresh-applied", action="store_true")
    ap.add_argument("--phase-b-strict-revalidate-status", default="NOT_APPLICABLE")
    ap.add_argument("--phase-transition-reason", default="")
    ap.add_argument("--phase-transition-error-code", default="")
    args = ap.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"identity-upgrade-exec-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"

    protocol = collect_protocol_evidence(args.protocol_root, args.protocol_mode)
    protocol_root = Path(protocol["protocol_root"]).expanduser().resolve()

    pack = _resolve_pack(Path(args.catalog), args.identity_id)
    effective_pack = _enforce_protocol_runtime_separation(
        pack,
        str(args.resolved_pack_path or ""),
        protocol_root,
        allow_protocol_root_pack=bool(args.allow_protocol_root_pack),
        identity_id=args.identity_id,
    )
    report_pack_path = str(effective_pack.resolve())
    runtime_output_root = _resolve_runtime_output_root(effective_pack, args.identity_id, protocol_root)
    prompt_contract = _resolve_prompt_contract(
        identity_id=args.identity_id,
        catalog_path=Path(args.catalog),
        repo_catalog_path=Path(args.repo_catalog),
        resolved_scope=str(args.resolved_scope or ""),
        resolved_pack_path=report_pack_path,
    )
    prompt_path = Path(str(prompt_contract.get("identity_prompt_path", ""))).expanduser().resolve()
    runtime_state_target = (prompt_path.parent / "runtime" / "state" / "prompt_contract.json").resolve()
    out_dir = Path(args.out_dir)
    if str(out_dir).strip() in {"identity/runtime/reports", "/tmp/identity-upgrade-reports"}:
        out_dir = runtime_output_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    current_task_path = pack / "CURRENT_TASK.json"
    task = _load_json(current_task_path)
    required_checks_raw = (
        task.get("identity_update_lifecycle_contract", {})
        .get("validation_contract", {})
        .get("required_checks", [])
    )
    if not isinstance(required_checks_raw, list) or not required_checks_raw:
        required_checks_raw = [
            "scripts/validate_identity_upgrade_prereq.py",
            "scripts/validate_identity_runtime_contract.py",
            "scripts/validate_identity_update_lifecycle.py",
            "scripts/validate_identity_capability_arbitration.py",
        ]
    lane_ctx = _lane_context(args.layer_intent_text, args.expected_work_layer, args.expected_source_layer)
    work_layer = str(lane_ctx.get("work_layer", DEFAULT_WORK_LAYER))
    source_layer = str(lane_ctx.get("source_layer", "global"))
    applied_gate_set = str(lane_ctx.get("applied_gate_set", "instance_required_checks"))
    lane_transition_reason = str(lane_ctx.get("lane_transition_reason", "instance_default_fallback"))

    required_checks, skipped_protocol_publish_checks = _filter_required_checks_for_lane(required_checks_raw, work_layer)
    check_cmds = [_build_validator_cmd(chk, args.identity_id, args.catalog) for chk in required_checks]
    log_dir = runtime_output_root / "logs" / "upgrade" / args.identity_id

    base_sha, head_sha = _resolve_git_range()
    lane_routing_cmd = [
        "python3",
        "scripts/validate_work_layer_gate_set_routing.py",
        "--catalog",
        args.catalog,
        "--repo-catalog",
        args.repo_catalog,
        "--identity-id",
        args.identity_id,
        "--operation",
        "update",
        "--base",
        base_sha,
        "--head",
        head_sha,
        "--applied-gate-set",
        applied_gate_set,
        "--force-check",
        "--json-only",
    ]
    if args.layer_intent_text.strip():
        lane_routing_cmd.extend(["--layer-intent-text", args.layer_intent_text.strip()])
    if args.expected_work_layer.strip():
        lane_routing_cmd.extend(["--expected-work-layer", args.expected_work_layer.strip()])
    if args.expected_source_layer.strip():
        lane_routing_cmd.extend(["--source-layer", args.expected_source_layer.strip()])
    lane_routing_proc = subprocess.run(lane_routing_cmd, capture_output=True, text=True)
    lane_routing_payload = _parse_json_payload(lane_routing_proc.stdout) or {}
    if lane_routing_proc.returncode != 0:
        reason = "lane_gate_set_routing_failed"
        checks = _build_skipped_check_results(check_cmds=check_cmds, log_dir=log_dir, run_id=run_id, reason=reason, exit_code=97)
        protocol["check_results"] = checks
        now_fail = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        artifacts = {
            "patch_plan": "",
            "pr": "",
            "report_path": "",
            "failed_at": now_fail,
            "lane_routing_stdout_tail": (lane_routing_proc.stdout or "").strip().splitlines()[-1]
            if (lane_routing_proc.stdout or "").strip()
            else "",
            "lane_routing_stderr_tail": (lane_routing_proc.stderr or "").strip().splitlines()[-1]
            if (lane_routing_proc.stderr or "").strip()
            else "",
        }
        fallback_metrics_path = (
            str(Path(args.metrics_path).expanduser().resolve())
            if str(args.metrics_path or "").strip()
            else str((runtime_output_root / "metrics" / f"{args.identity_id}-route-quality.json").resolve())
        )
        report = _base_report(
            run_id=run_id,
            identity_id=args.identity_id,
            now=now,
            mode=args.mode,
            protocol=protocol,
            catalog_path=args.catalog,
            resolved_scope=str(args.resolved_scope or ""),
            resolved_pack_path=report_pack_path,
            runtime_output_root=str(runtime_output_root),
            metrics_path=fallback_metrics_path,
            prompt_contract=prompt_contract,
            capability_contract={
                "capability_activation_status": "NOT_EVALUATED",
                "capability_activation_error_code": "",
                "capability_activation_notes": ["lane_routing_failed_before_capability_preflight"],
                "capability_contract_required": True,
            },
            required_checks=required_checks,
            required_checks_raw=required_checks_raw,
            skipped_protocol_publish_checks=skipped_protocol_publish_checks,
            work_layer=work_layer,
            source_layer=source_layer,
            applied_gate_set=applied_gate_set,
            lane_transition_reason=lane_transition_reason,
            protocol_feedback_triggered=bool(lane_routing_payload.get("protocol_feedback_triggered", False)),
            protocol_feedback_paths=list(lane_routing_payload.get("protocol_feedback_paths") or []),
            lane_routing_status=str(lane_routing_payload.get("work_layer_gate_set_routing_status", "FAIL_REQUIRED")),
            lane_routing_error_code=str(lane_routing_payload.get("error_code", "IP-LAYER-GATE-001")),
            phase_a_refresh_applied=bool(args.phase_a_refresh_applied),
            phase_b_strict_revalidate_status=str(args.phase_b_strict_revalidate_status or "NOT_APPLICABLE"),
            phase_transition_reason=str(args.phase_transition_reason or ""),
            phase_transition_error_code=str(args.phase_transition_error_code or ""),
        )
        report.update(
            {
                "checks": checks,
                "check_results": checks,
                "all_ok": False,
                "next_action": "rerun_with_deterministic_lane_instance_or_protocol",
                "failure_reason": reason,
                "upgrade_required": False,
                "writeback_mode": "DEGRADED_WRITEBACK",
                "writeback_status": "DEFERRED_VALIDATION_FAILED",
                "degrade_reason": "validator_failure_before_writeback",
                "risk_level": "medium",
                "next_recovery_action": "rerun_with_deterministic_lane_instance_or_protocol",
                "artifacts": artifacts,
            }
        )
        report_path = out_dir / f"{run_id}.json"
        _write_json(report_path, report)
        print(f"report={report_path}")
        print("upgrade_required=False")
        print("all_ok=False")
        print("next_action=rerun_with_deterministic_lane_instance_or_protocol")
        return 1

    capability_contract = _resolve_capability_contract(
        identity_id=args.identity_id,
        catalog_path=Path(args.catalog),
        repo_catalog_path=Path(args.repo_catalog),
        runtime_output_root=runtime_output_root,
        run_id=run_id,
        activation_policy=args.capability_activation_policy,
    )
    capability_status = str(capability_contract.get("capability_activation_status", "ERROR")).strip().upper()
    capability_error_code = str(capability_contract.get("capability_activation_error_code", "")).strip()

    arb = task.get("capability_arbitration_contract") or {}
    thresholds = (arb.get("trigger_thresholds") or {}) if isinstance(arb, dict) else {}
    contract_metrics_path = Path(
        (task.get("route_quality_contract") or {}).get(
            "metrics_output_path", f"identity/runtime/metrics/{args.identity_id}-route-quality.json"
        )
    )
    default_metrics_path = runtime_output_root / "metrics" / f"{args.identity_id}-route-quality.json"
    if args.metrics_path:
        metrics_path = Path(args.metrics_path)
    elif default_metrics_path.exists():
        metrics_path = default_metrics_path
    else:
        metrics_path = contract_metrics_path
    if capability_status in {"BLOCKED", "ERROR"} and bool(capability_contract.get("capability_contract_required", True)):
        plan_path = out_dir / f"{run_id}-patch-plan.json"
        _write_json(
            plan_path,
            {
                "run_id": run_id,
                "identity_id": args.identity_id,
                "generated_at": now,
                "mode": args.mode,
                "upgrade_required": False,
                "trigger_reasons": [f"capability_activation_blocked:{capability_error_code or 'IP-CAP-000'}"],
                "patch_surface": [],
                "planned_actions": ["resolve capability activation and rerun update"],
                "required_checks": required_checks,
                "protocol_mode": protocol["protocol_mode"],
                "protocol_root": protocol["protocol_root"],
                "protocol_commit_sha": protocol["protocol_commit_sha"],
                "protocol_ref": protocol["protocol_ref"],
                "catalog_path": str(Path(args.catalog).expanduser().resolve()),
                "resolved_scope": str(args.resolved_scope or ""),
                "resolved_pack_path": report_pack_path,
                "capability_activation_status": capability_status,
                "capability_activation_error_code": capability_error_code,
            },
        )
        skipped_checks = _build_skipped_check_results(
            check_cmds=check_cmds,
            log_dir=log_dir,
            run_id=run_id,
            reason=f"capability_activation_blocked:{capability_error_code or 'IP-CAP-000'}",
        )
        report = _base_report(
            run_id=run_id,
            identity_id=args.identity_id,
            now=now,
            mode=args.mode,
            protocol=protocol,
            catalog_path=args.catalog,
            resolved_scope=str(args.resolved_scope or ""),
            resolved_pack_path=report_pack_path,
            runtime_output_root=str(runtime_output_root),
            metrics_path=str(metrics_path),
            prompt_contract=prompt_contract,
            capability_contract=capability_contract,
            required_checks=required_checks,
            required_checks_raw=required_checks_raw,
            skipped_protocol_publish_checks=skipped_protocol_publish_checks,
            work_layer=work_layer,
            source_layer=source_layer,
            applied_gate_set=applied_gate_set,
            lane_transition_reason=lane_transition_reason,
            protocol_feedback_triggered=bool(lane_routing_payload.get("protocol_feedback_triggered", False)),
            protocol_feedback_paths=list(lane_routing_payload.get("protocol_feedback_paths") or []),
            lane_routing_status=str(lane_routing_payload.get("work_layer_gate_set_routing_status", "")),
            lane_routing_error_code=str(lane_routing_payload.get("error_code", "")),
        )
        report.update(
            {
                "upgrade_required": False,
                "trigger_reasons": [f"capability_activation_blocked:{capability_error_code or 'IP-CAP-000'}"],
                "required_checks": required_checks,
                "checks": skipped_checks,
                "check_results": skipped_checks,
                "actions_taken": [
                    f"patch_plan_written:{plan_path}",
                    "validator_execution_skipped_preflight_blocked",
                ],
                "artifacts": [
                    str(plan_path),
                    str(capability_contract.get("capability_activation_report_path", "")),
                ],
                "permission_state": "PRECHECK",
                "permission_error_code": "",
                "escalation_recommendation": "activate required skill/mcp attachments before retry",
                "writeback_precheck": {"all_writable": False, "reason": "capability_activation_blocked"},
                "next_action": _capability_next_action(capability_contract),
                "failure_reason": "capability activation blocked before upgrade execution",
            }
        )
        report["experience_writeback"].update(
            {
                "required": False,
                "status": "NOT_REQUIRED",
                "error_code": capability_error_code or "IP-CAP-000",
                "notes": "capability activation preflight blocked execution",
            }
        )
        report["writeback_status"] = str(report["experience_writeback"]["status"])
        report.update(
            _derive_writeback_continuity_fields(
                upgrade_required=bool(report.get("upgrade_required", False)),
                all_ok=bool(report.get("all_ok", False)),
                writeback_status=str(report.get("writeback_status", "")),
                writeback_error_code=str((report.get("experience_writeback") or {}).get("error_code", "")),
                permission_error_code=str(report.get("permission_error_code", "")),
                next_action=str(report.get("next_action", "")),
            )
        )
        report_path = out_dir / f"{run_id}.json"
        _write_json(report_path, report)
        print(f"report={report_path}")
        print("upgrade_required=False")
        print("all_ok=False")
        print(f"next_action={report.get('next_action','')}")
        return 2
    if not metrics_path.exists():
        plan_path = out_dir / f"{run_id}-patch-plan.json"
        _write_json(
            plan_path,
            {
                "run_id": run_id,
                "identity_id": args.identity_id,
                "generated_at": now,
                "mode": args.mode,
                "upgrade_required": False,
                "trigger_reasons": [f"metrics_artifact_missing:{metrics_path}"],
                "patch_surface": [],
                "planned_actions": ["generate route metrics and rerun update"],
                "required_checks": required_checks,
                "protocol_mode": protocol["protocol_mode"],
                "protocol_root": protocol["protocol_root"],
                "protocol_commit_sha": protocol["protocol_commit_sha"],
                "protocol_ref": protocol["protocol_ref"],
                "catalog_path": str(Path(args.catalog).expanduser().resolve()),
                "resolved_scope": str(args.resolved_scope or ""),
                "resolved_pack_path": report_pack_path,
                "capability_activation_status": capability_status,
                "capability_activation_error_code": capability_error_code,
            },
        )
        skipped_checks = _build_skipped_check_results(
            check_cmds=check_cmds,
            log_dir=log_dir,
            run_id=run_id,
            reason=f"metrics_artifact_missing:{metrics_path}",
        )
        report = _base_report(
            run_id=run_id,
            identity_id=args.identity_id,
            now=now,
            mode=args.mode,
            protocol=protocol,
            catalog_path=args.catalog,
            resolved_scope=str(args.resolved_scope or ""),
            resolved_pack_path=report_pack_path,
            runtime_output_root=str(runtime_output_root),
            metrics_path=str(metrics_path),
            prompt_contract=prompt_contract,
            capability_contract=capability_contract,
            required_checks=required_checks,
            required_checks_raw=required_checks_raw,
            skipped_protocol_publish_checks=skipped_protocol_publish_checks,
            work_layer=work_layer,
            source_layer=source_layer,
            applied_gate_set=applied_gate_set,
            lane_transition_reason=lane_transition_reason,
            protocol_feedback_triggered=bool(lane_routing_payload.get("protocol_feedback_triggered", False)),
            protocol_feedback_paths=list(lane_routing_payload.get("protocol_feedback_paths") or []),
            lane_routing_status=str(lane_routing_payload.get("work_layer_gate_set_routing_status", "")),
            lane_routing_error_code=str(lane_routing_payload.get("error_code", "")),
        )
        report.update(
            {
                "upgrade_required": False,
                "trigger_reasons": [f"metrics_artifact_missing:{metrics_path}"],
                "required_checks": required_checks,
                "checks": skipped_checks,
                "check_results": skipped_checks,
                "actions_taken": [
                    f"patch_plan_written:{plan_path}",
                    "validator_execution_skipped_metrics_missing",
                ],
                "artifacts": [str(plan_path)],
                "permission_state": "PRECHECK",
                "permission_error_code": "IP-UPG-001",
                "escalation_recommendation": "generate metrics artifact then rerun update",
                "writeback_precheck": {"all_writable": False, "reason": "metrics_missing"},
                "next_action": "generate_metrics_and_rerun",
                "failure_reason": f"metrics artifact not found: {metrics_path}",
            }
        )
        report["experience_writeback"].update(
            {
                "required": False,
                "status": "NOT_REQUIRED",
                "error_code": "IP-UPG-001",
                "notes": "metrics artifact missing; no writeback attempted",
            }
        )
        report["writeback_status"] = str(report["experience_writeback"]["status"])
        report.update(
            _derive_writeback_continuity_fields(
                upgrade_required=bool(report.get("upgrade_required", False)),
                all_ok=bool(report.get("all_ok", False)),
                writeback_status=str(report.get("writeback_status", "")),
                writeback_error_code=str((report.get("experience_writeback") or {}).get("error_code", "")),
                permission_error_code=str(report.get("permission_error_code", "")),
                next_action=str(report.get("next_action", "")),
            )
        )
        report_path = out_dir / f"{run_id}.json"
        _write_json(report_path, report)
        print(f"report={report_path}")
        print("upgrade_required=False")
        print("all_ok=False")
        print("next_action=generate_metrics_and_rerun")
        return 2
    metrics = _load_json(metrics_path)

    upgrade_required, reasons = _needs_upgrade(metrics, thresholds)

    safe_auto = ((arb.get("safe_auto_patch_surface") or {}) if isinstance(arb, dict) else {}) or {}
    touched_paths = [
        str(pack / "RULEBOOK.jsonl"),
        str(pack / "TASK_HISTORY.md"),
        str(runtime_state_target),
        str(runtime_output_root / "logs" / "arbitration" / f"{args.identity_id}-{run_id}.json"),
    ]
    if args.mode == "safe-auto":
        patch_surface = touched_paths
    else:
        patch_surface = [
            str(current_task_path),
            str(runtime_state_target),
            str(pack / "RULEBOOK.jsonl"),
            str(pack / "TASK_HISTORY.md"),
        ]

    # Always produce patch plan (even if no trigger) for audit clarity
    patch_plan = {
        "run_id": run_id,
        "identity_id": args.identity_id,
        "generated_at": now,
        "mode": args.mode,
        "upgrade_required": upgrade_required,
        "trigger_reasons": reasons,
        "patch_surface": patch_surface,
        "planned_actions": [
            "append arbitration decision record",
            "append rulebook learning row",
            "append TASK_HISTORY upgrade note",
            "run required validators and replay checks",
        ],
    }
    patch_plan.update(
        {
            "protocol_mode": protocol["protocol_mode"],
            "protocol_root": protocol["protocol_root"],
            "protocol_commit_sha": protocol["protocol_commit_sha"],
            "protocol_ref": protocol["protocol_ref"],
            "identity_home": str(default_identity_home()),
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "resolved_scope": str(args.resolved_scope or ""),
            "resolved_pack_path": report_pack_path,
            "capability_activation_status": capability_status,
            "capability_activation_error_code": capability_error_code,
        }
    )

    plan_path = out_dir / f"{run_id}-patch-plan.json"
    _write_json(plan_path, patch_plan)

    actions_taken: list[str] = [f"patch_plan_written:{plan_path}"]
    artifacts = [str(plan_path), str(metrics_path)]
    permission_state = "PRECHECK"
    permission_error_code = ""
    escalation_required = False
    escalation_recommendation = ""
    experience_writeback: dict[str, Any] = {
        "required": bool(upgrade_required),
        "status": "SKIPPED",
        "error_code": "",
        "mode": args.mode,
        "rulebook_path": str(pack / "RULEBOOK.jsonl"),
        "task_history_path": str(pack / "TASK_HISTORY.md"),
        "rule_entry_id": "",
        "history_contains_run_id": False,
        "notes": "",
    }
    writeback_paths = [str(pack / "RULEBOOK.jsonl"), str(pack / "TASK_HISTORY.md"), str(runtime_state_target)]
    precheck = {
        "rulebook_path": str(pack / "RULEBOOK.jsonl"),
        "task_history_path": str(pack / "TASK_HISTORY.md"),
        "results": [],
        "all_writable": True,
    }
    if upgrade_required:
        for target in [pack / "RULEBOOK.jsonl", pack / "TASK_HISTORY.md", runtime_state_target]:
            ok, reason = _writable_precheck(target)
            precheck["results"].append({"path": str(target), "ok": ok, "reason": reason})
            if not ok:
                precheck["all_writable"] = False
        if not precheck["all_writable"]:
            permission_state = "NEEDS_ESCALATION"
            permission_error_code = "IP-PERM-001"
            escalation_required = True
            escalation_recommendation = (
                "Switch to repo-local runtime root or run with approved elevated permission; "
                "then rerun identity_creator update."
            )
            experience_writeback.update(
                {
                    "status": "DEFERRED_PERMISSION_BLOCKED",
                    "error_code": "IP-PERM-001",
                    "notes": "write targets are not writable in current execution context",
                }
            )
            actions_taken.append("permission_precheck_blocked_writeback")

    prompt_change_required = bool(upgrade_required)
    prompt_change_applied = False
    prompt_change_note = ""
    prompt_hash_before = str(prompt_contract.get("identity_prompt_sha256", ""))
    prompt_hash_after = str(prompt_contract.get("identity_prompt_sha256", ""))
    runtime_state_artifact_path = str(prompt_contract.get("runtime_state_artifact_path", ""))
    runtime_state_artifact_hash = str(prompt_contract.get("runtime_state_artifact_hash", ""))
    prompt_runtime_state_binding_status = str(prompt_contract.get("prompt_runtime_state_binding_status", "MISSING"))
    prompt_runtime_state_externalization_status = str(
        prompt_contract.get("prompt_runtime_state_externalization_status", "MISSING")
    )
    prompt_runtime_state_externalization_error_code = str(
        prompt_contract.get("prompt_runtime_state_externalization_error_code", "")
    )

    if upgrade_required and args.mode == "safe-auto" and precheck.get("all_writable", True):
        if safe_auto.get("enforce_path_policy") is True:
            allowlist = [str(x) for x in (safe_auto.get("allowlist") or [])]
            denylist = [str(x) for x in (safe_auto.get("denylist") or [])]
            violations: list[dict[str, str]] = []
            for pth in touched_paths:
                ok, reason = _path_allowed(pth, allowlist, denylist)
                if not ok:
                    violations.append({"path": pth, "reason": reason})
            if violations:
                skipped_checks = _build_skipped_check_results(
                    check_cmds=check_cmds,
                    log_dir=log_dir,
                    run_id=run_id,
                    reason="safe_auto_path_policy_violation",
                    exit_code=98,
                )
                report = {
                    **_base_report(
                        run_id=run_id,
                        identity_id=args.identity_id,
                        now=now,
                        mode=args.mode,
                        protocol=protocol,
                        catalog_path=args.catalog,
                        resolved_scope=str(args.resolved_scope or ""),
                        resolved_pack_path=report_pack_path,
                        runtime_output_root=str(runtime_output_root),
                        metrics_path=str(metrics_path),
                        prompt_contract=prompt_contract,
                        capability_contract=capability_contract,
                        required_checks=required_checks,
                        required_checks_raw=required_checks_raw,
                        skipped_protocol_publish_checks=skipped_protocol_publish_checks,
                        work_layer=work_layer,
                        source_layer=source_layer,
                        applied_gate_set=applied_gate_set,
                        lane_transition_reason=lane_transition_reason,
                        protocol_feedback_triggered=bool(lane_routing_payload.get("protocol_feedback_triggered", False)),
                        protocol_feedback_paths=list(lane_routing_payload.get("protocol_feedback_paths") or []),
                        lane_routing_status=str(lane_routing_payload.get("work_layer_gate_set_routing_status", "")),
                        lane_routing_error_code=str(lane_routing_payload.get("error_code", "")),
                    ),
                    "upgrade_required": upgrade_required,
                    "trigger_reasons": reasons,
                    "required_checks": required_checks,
                    "actions_taken": actions_taken,
                    "checks": skipped_checks,
                    "check_results": skipped_checks,
                    "artifacts": artifacts,
                    "all_ok": False,
                    "path_policy_violations": violations,
                    "permission_state": "BLOCKED",
                    "permission_error_code": "IP-UPG-001",
                    "writeback_precheck": precheck,
                    "next_action": "blocked_by_safe_auto_path_policy",
                    "failure_reason": "safe_auto_path_policy_violation",
                }
                report["experience_writeback"].update(
                    {
                        "required": True,
                        "status": "DEFERRED_POLICY_BLOCKED",
                        "error_code": "IP-SAFEAUTO-001",
                        "mode": args.mode,
                        "rulebook_path": str(pack / "RULEBOOK.jsonl"),
                        "task_history_path": str(pack / "TASK_HISTORY.md"),
                        "notes": "safe-auto blocked before writeback by path policy",
                    }
                )
                report["writeback_status"] = str(report["experience_writeback"]["status"])
                report.update(
                    _derive_writeback_continuity_fields(
                        upgrade_required=bool(report.get("upgrade_required", False)),
                        all_ok=bool(report.get("all_ok", False)),
                        writeback_status=str(report.get("writeback_status", "")),
                        writeback_error_code=str((report.get("experience_writeback") or {}).get("error_code", "")),
                        permission_error_code=str(report.get("permission_error_code", "")),
                        next_action=str(report.get("next_action", "")),
                    )
                )
                report_path = out_dir / f"{run_id}.json"
                _write_json(report_path, report)
                print(f"report={report_path}")
                print("upgrade_required=True")
                print("all_ok=False")
                print("next_action=blocked_by_safe_auto_path_policy")
                return 3

        # 1) append arbitration decision record
        decision = {
            "arbitration_id": f"{run_id}-arb",
            "task_id": str(task.get("task_id", "")),
            "identity_id": args.identity_id,
            "conflict_pair": "routing_vs_learning",
            "inputs": {
                "metrics": {
                    "misroute_rate": metrics.get("misroute_rate"),
                    "replay_success_rate": metrics.get("replay_success_rate"),
                    "first_pass_success_rate": metrics.get("first_pass_success_rate"),
                },
                "thresholds": thresholds,
            },
            "decision": "trigger_identity_update_cycle",
            "impact": "force patch/validate/replay cycle",
            "rationale": "; ".join(reasons) if reasons else "threshold trigger",
            "decided_at": now,
        }
        decision_path = runtime_output_root / "logs" / "arbitration" / f"{args.identity_id}-{run_id}.json"
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(decision_path, {"records": [decision]})
        actions_taken.append("arbitration_record_written")
        artifacts.append(str(decision_path))

        # 2) append rulebook learning row
        rulebook_path = pack / "RULEBOOK.jsonl"
        try:
            _append_jsonl(
                rulebook_path,
                {
                    "rule_id": f"{run_id}-auto-upgrade",
                    "type": "negative",
                    "trigger": "arbitration_threshold_hit",
                    "action": "execute_identity_upgrade_safe_auto",
                    "evidence_run_id": run_id,
                    "scope": "identity_update_cycle",
                    "confidence": 0.75,
                    "updated_at": now,
                },
            )
            actions_taken.append("rulebook_row_appended")
        except PermissionError:
            permission_state = "ESCALATION_DENIED"
            permission_error_code = "IP-PERM-002"
            escalation_required = True
            experience_writeback.update(
                {
                    "status": "DEFERRED_PERMISSION_BLOCKED",
                    "error_code": "IP-PERM-002",
                    "notes": "permission denied while appending RULEBOOK during safe-auto",
                }
            )

        # 3) append TASK_HISTORY note
        history_path = pack / "TASK_HISTORY.md"
        try:
            _append_task_history(
                history_path,
                f"{now} | auto-upgrade trigger | run_id={run_id} | mode=safe-auto | reasons={'; '.join(reasons)}",
            )
            actions_taken.append("task_history_appended")
            if experience_writeback.get("status") != "DEFERRED_PERMISSION_BLOCKED":
                experience_writeback.update(
                    {
                        "status": "WRITTEN",
                        "rule_entry_id": f"{run_id}-auto-upgrade",
                        "history_contains_run_id": True,
                        "notes": "safe-auto writeback appended before validator execution",
                    }
                )
        except PermissionError:
            permission_state = "ESCALATION_DENIED"
            permission_error_code = "IP-PERM-002"
            escalation_required = True
            experience_writeback.update(
                {
                    "status": "DEFERRED_PERMISSION_BLOCKED",
                    "error_code": "IP-PERM-002",
                    "notes": "permission denied while appending TASK_HISTORY during safe-auto",
                }
            )

    # Run required validators + replay-equivalent gate checks
    checks = [_run(cmd, log_dir=log_dir, run_id=run_id, idx=i + 1) for i, cmd in enumerate(check_cmds)]
    baseline_signal = _extract_baseline_signal(
        checks,
        protocol_head_sha_at_run_start=str(
            protocol.get("protocol_head_sha_at_run_start") or protocol.get("protocol_commit_sha") or ""
        ),
    )

    all_ok = all(c["ok"] for c in checks)
    if upgrade_required and args.mode == "review-required" and all_ok and precheck.get("all_writable", True):
        rulebook_path = pack / "RULEBOOK.jsonl"
        history_path = pack / "TASK_HISTORY.md"
        rule_id = f"{run_id}-review-required-upgrade"
        try:
            _append_jsonl(
                rulebook_path,
                {
                    "rule_id": rule_id,
                    "type": "positive",
                    "trigger": "review_required_upgrade_validated",
                    "action": "preserve_trigger_patch_validate_replay_chain",
                    "evidence_run_id": run_id,
                    "scope": "identity_update_cycle",
                    "confidence": 0.9,
                    "updated_at": now,
                },
            )
            _append_task_history(
                history_path,
                (
                    f"{now} | review-required upgrade validated | run_id={run_id} | mode=review-required "
                    f"| checks_passed={len(checks)} | reasons={'; '.join(reasons) if reasons else 'none'}"
                ),
            )
            actions_taken.append("rulebook_row_appended_review_required")
            actions_taken.append("task_history_appended_review_required")
            artifacts.append(str(rulebook_path))
            artifacts.append(str(history_path))
            experience_writeback.update(
                {
                    "status": "WRITTEN",
                    "error_code": "",
                    "rule_entry_id": rule_id,
                    "history_contains_run_id": True,
                    "notes": "review-required success writeback appended after validator execution",
                }
            )
        except PermissionError:
            permission_state = "ESCALATION_DENIED"
            permission_error_code = "IP-PERM-002"
            escalation_required = True
            experience_writeback.update(
                {
                    "status": "DEFERRED_PERMISSION_BLOCKED",
                    "error_code": "IP-PERM-002",
                    "notes": "permission denied during review-required writeback",
                }
            )
            all_ok = False
    elif upgrade_required and args.mode == "review-required" and all_ok and not precheck.get("all_writable", True):
        all_ok = False
        actions_taken.append("writeback_skipped_due_to_permission_precheck")
    elif upgrade_required:
        # Track-A contract hardening:
        # upgrade-required + non-closure must emit explicit degraded writeback status
        # (never leave writeback_status as MISSING).
        existing_status = str(experience_writeback.get("status", "")).strip().upper()
        existing_error = str(experience_writeback.get("error_code", "")).strip()
        deferred_statuses = {
            "WRITTEN",
            "DEFERRED_PERMISSION_BLOCKED",
            "DEFERRED_POLICY_BLOCKED",
            "DEFERRED_VALIDATION_FAILED",
            "DEFERRED_NOT_EXECUTED",
        }
        if existing_status not in deferred_statuses:
            if permission_error_code.startswith("IP-PERM-"):
                status = "DEFERRED_PERMISSION_BLOCKED"
                code = existing_error or permission_error_code or "IP-PERM-002"
                note = "upgrade required but writeback deferred due to permission boundary"
            elif permission_error_code == "IP-UPG-001" or existing_error.startswith("IP-SAFEAUTO-"):
                status = "DEFERRED_POLICY_BLOCKED"
                code = existing_error or "IP-SAFEAUTO-001"
                note = "upgrade required but writeback deferred by safe-auto policy boundary"
            elif not all_ok:
                status = "DEFERRED_VALIDATION_FAILED"
                code = existing_error or "IP-UPG-002"
                note = "upgrade required but writeback deferred because one or more validators failed"
            else:
                status = "DEFERRED_NOT_EXECUTED"
                code = existing_error or "IP-UPG-002"
                note = "upgrade required but writeback was not executed"
            experience_writeback.update(
                {
                    "status": status,
                    "error_code": code,
                    "notes": note,
                }
            )
    else:
        experience_writeback.update(
            {
                "required": False,
                "status": "NOT_REQUIRED",
                "error_code": "",
                "notes": "thresholds not triggered; no upgrade writeback required",
            }
        )

    if prompt_change_required and precheck.get("all_writable", True):
        if all_ok:
            try:
                applied, note, h_before, h_after, state_path, state_hash = _apply_prompt_contract_update(
                    prompt_path=prompt_path,
                    run_id=run_id,
                    mode=args.mode,
                    trigger_reasons=reasons,
                )
                prompt_change_applied = True
                prompt_change_note = note
                prompt_hash_before = h_before
                prompt_hash_after = h_after
                runtime_state_artifact_path = state_path
                runtime_state_artifact_hash = state_hash
                prompt_runtime_state_binding_status = "PASS_REQUIRED"
                prompt_runtime_state_externalization_status = "PASS_REQUIRED"
                prompt_runtime_state_externalization_error_code = ""
                actions_taken.append("identity_prompt_contract_updated")
                artifacts.append(state_path)
            except PermissionError:
                permission_state = "ESCALATION_DENIED"
                permission_error_code = "IP-PERM-002"
                escalation_required = True
                prompt_change_note = "prompt_update_permission_denied"
                prompt_runtime_state_binding_status = "FAIL_REQUIRED"
                prompt_runtime_state_externalization_status = "FAIL_REQUIRED"
                prompt_runtime_state_externalization_error_code = "IP-PROMPT-STATE-001"
                all_ok = False
            except Exception as exc:
                prompt_change_note = f"prompt_update_failed:{exc}"
                prompt_runtime_state_binding_status = "FAIL_REQUIRED"
                prompt_runtime_state_externalization_status = "FAIL_REQUIRED"
                prompt_runtime_state_externalization_error_code = "IP-PROMPT-STATE-001"
                all_ok = False
        else:
            prompt_change_note = "prompt_change_deferred_due_to_failed_validators"
    elif prompt_change_required:
        prompt_change_note = "prompt_change_deferred_due_to_permission_precheck"
        all_ok = False

    next_action = ""
    if args.mode == "review-required" and upgrade_required:
        next_action = "review_required_create_pr_from_patch_plan"
    elif args.mode == "safe-auto" and upgrade_required:
        next_action = "safe_auto_applied_and_validated"
    else:
        next_action = "no_upgrade_triggered"
    if prompt_change_required and not prompt_change_applied:
        if not next_action.startswith("review_required"):
            next_action = "prompt_contract_update_required"

    prompt_contract_final = _resolve_prompt_contract(
        identity_id=args.identity_id,
        catalog_path=Path(args.catalog),
        repo_catalog_path=Path(args.repo_catalog),
        resolved_scope=str(args.resolved_scope or ""),
        resolved_pack_path=str(args.resolved_pack_path or str(effective_pack)),
    )
    report = {
        "run_id": run_id,
        "identity_id": args.identity_id,
        "generated_at": now,
        "creator_invocation": {
            "tool": "identity-creator",
            "mode": "update",
            "entrypoint": "scripts/execute_identity_upgrade.py",
            "base_contract": "identity_update_lifecycle_contract",
            "run_id": run_id,
        },
        "mode": args.mode,
        "execution_context": {
            "generated_by": "ci" if os.environ.get("CI") else "local",
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_sha": os.environ.get("GITHUB_SHA", ""),
        },
        "required_checks": required_checks,
        "required_checks_raw": required_checks_raw,
        "skipped_protocol_publish_checks": skipped_protocol_publish_checks,
        "upgrade_required": upgrade_required,
        "trigger_reasons": reasons,
        "actions_taken": actions_taken,
        "checks": checks,
        "check_results": checks,
        "artifacts": artifacts,
        "experience_writeback": experience_writeback,
        "writeback_paths": writeback_paths,
        "writeback_status": str(experience_writeback.get("status", "")),
        "writeback_rule_id": str(experience_writeback.get("rule_entry_id", "")),
        "all_ok": all_ok,
        "permission_state": permission_state if not (all_ok and experience_writeback.get("status") == "WRITTEN") else "WRITEBACK_WRITTEN",
        "permission_error_code": permission_error_code,
        "escalation_required": escalation_required,
        "escalation_recommendation": escalation_recommendation,
        "writeback_precheck": precheck,
        "runtime_output_root": str(runtime_output_root),
        "metrics_path": str(metrics_path),
        "skills_used": list(capability_contract.get("skills_used") or []),
        "mcp_tools_used": list(capability_contract.get("mcp_tools_used") or []),
        "tool_calls_used": list(capability_contract.get("tool_calls_used") or []),
        "active_skills": list(capability_contract.get("active_skills") or []),
        "mcp_servers_checked": list(capability_contract.get("mcp_servers_checked") or []),
        "tool_routes": list(capability_contract.get("tool_routes") or []),
        "capability_activation_status": str(capability_contract.get("capability_activation_status", "UNKNOWN")),
        "capability_activation_error_code": str(capability_contract.get("capability_activation_error_code", "")),
        "capability_activation_notes": list(capability_contract.get("capability_activation_notes") or []),
        "capability_contract_required": bool(capability_contract.get("capability_contract_required", True)),
        "capability_activation_validator_rc": capability_contract.get("capability_activation_validator_rc"),
        "capability_activation_report_path": str(capability_contract.get("capability_activation_report_path", "")),
        "next_action": next_action,
        "failure_reason": "" if all_ok else "one_or_more_checks_failed_or_writeback_not_written",
        "work_layer": work_layer,
        "source_layer": source_layer,
        "applied_gate_set": applied_gate_set,
        "lane_transition_reason": lane_transition_reason,
        "protocol_feedback_triggered": bool(lane_routing_payload.get("protocol_feedback_triggered", False)),
        "protocol_feedback_paths": list(lane_routing_payload.get("protocol_feedback_paths") or []),
        "lane_routing_status": str(lane_routing_payload.get("work_layer_gate_set_routing_status", "")),
        "lane_routing_error_code": str(lane_routing_payload.get("error_code", "")),
        "phase_a_refresh_applied": bool(args.phase_a_refresh_applied),
        "phase_b_strict_revalidate_status": str(args.phase_b_strict_revalidate_status or "NOT_APPLICABLE"),
        "phase_transition_reason": str(args.phase_transition_reason or ""),
        "phase_transition_error_code": str(args.phase_transition_error_code or ""),
    }
    report.update(
        _derive_writeback_continuity_fields(
            upgrade_required=bool(upgrade_required),
            all_ok=bool(all_ok),
            writeback_status=str(report.get("writeback_status", "")),
            writeback_error_code=str((report.get("experience_writeback") or {}).get("error_code", "")),
            permission_error_code=str(report.get("permission_error_code", "")),
            next_action=str(report.get("next_action", "")),
        )
    )
    report.update(
        {
            "protocol_mode": protocol["protocol_mode"],
            "protocol_root": protocol["protocol_root"],
            "protocol_commit_sha": protocol["protocol_commit_sha"],
            "protocol_head_sha_at_run_start": str(
                baseline_signal.get("protocol_head_sha_at_run_start")
                or protocol.get("protocol_head_sha_at_run_start")
                or protocol.get("protocol_commit_sha")
                or ""
            ),
            "baseline_reference_mode": str(baseline_signal.get("baseline_reference_mode") or "run_pinned"),
            "current_protocol_head_sha": str(baseline_signal.get("current_protocol_head_sha") or ""),
            "head_drift_detected": bool(baseline_signal.get("head_drift_detected", False)),
            "baseline_status": str(baseline_signal.get("baseline_status") or "UNKNOWN"),
            "baseline_error_code": str(baseline_signal.get("baseline_error_code") or ""),
            "protocol_ref": protocol["protocol_ref"],
            "identity_home": str(default_identity_home()),
            "catalog_path": str(Path(args.catalog).expanduser().resolve()),
            "resolved_scope": str(args.resolved_scope or ""),
            "resolved_pack_path": report_pack_path,
            "prompt_change_required": prompt_change_required,
            "prompt_change_applied": prompt_change_applied,
            "identity_prompt_hash_before": prompt_hash_before,
            "identity_prompt_hash_after": prompt_hash_after,
            "identity_prompt_change_note": prompt_change_note,
            "prompt_policy_hash": prompt_hash_after or prompt_hash_before,
            "runtime_state_artifact_path": runtime_state_artifact_path,
            "runtime_state_artifact_hash": runtime_state_artifact_hash,
            "prompt_runtime_state_binding_status": prompt_runtime_state_binding_status,
            "prompt_runtime_state_externalization_status": prompt_runtime_state_externalization_status,
            "prompt_runtime_state_externalization_error_code": prompt_runtime_state_externalization_error_code,
            **prompt_contract_final,
        }
    )
    report_path = out_dir / f"{run_id}.json"
    _write_json(report_path, report)

    print(f"report={report_path}")
    print(f"upgrade_required={upgrade_required}")
    print(f"all_ok={all_ok}")
    print(f"next_action={next_action}")

    return 0 if all_ok else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PermissionError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
