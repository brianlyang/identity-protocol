#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task
from final_emit_contract_common import (
    FINAL_EMIT_CHANNEL_ID,
    FINAL_EMIT_POLICY_MODE,
    FINAL_EMIT_SCHEMA_ID,
)
from protocol_infra_contract import (
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
    CHAT_EGRESS_POST_CHECK_STATE_UNAVAILABLE_ERROR_CODE,
    CTX_TOOL_TIMEOUT_ERROR_CODE,
    CTX_TOOL_TIMEOUT_MARKER,
    CTX_TOOL_TIMEOUT_REASON_PREFIX,
    GATEWAY_CONTEXT_RESOLVE_TIMEOUT_SECONDS_DEFAULT,
    GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT,
    GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS,
    HOST_GATEWAY_CONTRACT_KEYS as INFRA_HOST_GATEWAY_CONTRACT_KEYS,
    HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER as INFRA_HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER as INFRA_HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
    HOST_GATEWAY_DEFAULT_SIGNING_KEY as INFRA_HOST_GATEWAY_DEFAULT_SIGNING_KEY,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE as INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE as INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_TRANSPORT_REACHABILITY_ERROR_CODE,
    HOST_TRANSPORT_REACHABILITY_REASON_PREFIX,
    PRIVILEGE_ESCALATION_ERROR_CODE,
    PRIVILEGE_ESCALATION_REASON_PREFIX,
    PRIVILEGE_ESCALATION_REMEDIATION_HINT,
)

HOST_GATEWAY_CONTRACT_KEYS = INFRA_HOST_GATEWAY_CONTRACT_KEYS
HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER = INFRA_HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER
HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER = INFRA_HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER
HOST_GATEWAY_DEFAULT_SIGNING_KEY = INFRA_HOST_GATEWAY_DEFAULT_SIGNING_KEY
FINAL_EMIT_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
REQUIRED_GATE_BUNDLE_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
TIMEOUT_RETURN_CODE = 124
DEFAULT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CMD_TIMEOUT_SECONDS"
CONTEXT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CONTEXT_TIMEOUT_SECONDS"
FINAL_EMIT_TUPLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "outlet_channel_id",
    "outlet_preflight_receipt",
    "outlet_bypass_detected",
    "final_emit_channel_id",
    "final_emit_policy_mode",
    "final_emit_schema_id",
    "final_emit_schema_status",
    "final_emit_contract_status",
)


def _arg_index(cmd: list[str], flag: str) -> int:
    try:
        return cmd.index(flag)
    except ValueError:
        return -1


def _arg_value(cmd: list[str], flag: str, default: str = "") -> str:
    idx = _arg_index(cmd, flag)
    if idx < 0 or idx + 1 >= len(cmd):
        return default
    return str(cmd[idx + 1] or "").strip() or default


def _has_flag(cmd: list[str], flag: str) -> bool:
    return _arg_index(cmd, flag) >= 0


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = str(value or "").strip().lower()
    return token in {"1", "true", "yes", "y", "on"}


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except Exception:
        return int(default)
    if parsed <= 0:
        return int(default)
    return parsed


def _looks_like_json_dict(raw: str) -> bool:
    text = str(raw or "").strip()
    if not text:
        return False
    try:
        payload = json.loads(text)
    except Exception:
        return False
    return isinstance(payload, dict)


def _classify_subprocess_failure(*, stdout_text: str, stderr_text: str) -> tuple[str, str] | None:
    merged = "\n".join([str(stdout_text or ""), str(stderr_text or "")]).strip().lower()
    if not merged:
        return None
    privilege_tokens = (
        "permission denied",
        "operation not permitted",
        "read-only file system",
        "eacces",
        "eperm",
        "erofs",
        "privilege_escalation_required",
    )
    if any(token in merged for token in privilege_tokens):
        return (
            PRIVILEGE_ESCALATION_ERROR_CODE,
            (
                f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:gateway_subprocess:"
                f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
            ),
        )
    reachability_tokens = (
        "127.0.0.1:3001",
        "connection refused",
        "failed to connect",
        "network is unreachable",
        "connection reset",
        "connect timeout",
        "connection timed out",
        "socket",
    )
    if any(token in merged for token in reachability_tokens):
        return (
            HOST_TRANSPORT_REACHABILITY_ERROR_CODE,
            f"{HOST_TRANSPORT_REACHABILITY_REASON_PREFIX}:localhost_or_socket_unreachable",
        )
    return None


def _script_hint_from_cmd(cmd: list[str]) -> str:
    if len(cmd) < 2:
        return ""
    return str(cmd[1] or "").strip()


def _is_context_resolve_cmd(cmd: list[str]) -> bool:
    script = _script_hint_from_cmd(cmd)
    return script.endswith("resolve_identity_context.py")


def _resolve_command_timeout_seconds(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    env_map = env if isinstance(env, dict) else os.environ
    default_timeout = int(GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT)
    script_hint = _script_hint_from_cmd(cmd)
    for script_name, timeout_value in GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS:
        name_token = str(script_name or "").strip()
        if not name_token:
            continue
        if script_hint.endswith(name_token):
            default_timeout = _safe_positive_int(timeout_value, default_timeout)
            break
    env_token = str(env_map.get(DEFAULT_TIMEOUT_ENV, "")).strip()
    if _is_context_resolve_cmd(cmd):
        default_timeout = int(GATEWAY_CONTEXT_RESOLVE_TIMEOUT_SECONDS_DEFAULT)
        context_token = str(env_map.get(CONTEXT_TIMEOUT_ENV, "")).strip()
        if context_token:
            env_token = context_token
    return _safe_positive_int(env_token, default_timeout)


def _timeout_reason(*, cmd: list[str], timeout_seconds: int, scope: str) -> str:
    script = _script_hint_from_cmd(cmd) or "unknown_command"
    return (
        f"{CTX_TOOL_TIMEOUT_MARKER}:{CTX_TOOL_TIMEOUT_REASON_PREFIX}:"
        f"{scope}:{script}:timeout_seconds={int(timeout_seconds)}"
    )


def _project_final_emit_tuple_from_session_chain(
    *,
    chain_payload: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    projected: dict[str, Any] = {}
    projected["outlet_channel_id"] = (
        str(chain_payload.get("outlet_channel_id", "")).strip()
        or str(chain_payload.get("final_emit_channel_id", "")).strip()
        or FINAL_EMIT_CHANNEL_ID
    )
    projected["outlet_preflight_receipt"] = (
        str(chain_payload.get("outlet_preflight_receipt", "")).strip()
        or str(chain_payload.get("ingress_receipt_path", "")).strip()
    )
    projected["outlet_bypass_detected"] = _normalize_bool(
        chain_payload.get("outlet_bypass_detected", False)
    )
    projected["final_emit_channel_id"] = (
        str(chain_payload.get("final_emit_channel_id", "")).strip()
        or str(projected["outlet_channel_id"]).strip()
        or FINAL_EMIT_CHANNEL_ID
    )
    projected["final_emit_policy_mode"] = (
        str(chain_payload.get("final_emit_policy_mode", "")).strip() or FINAL_EMIT_POLICY_MODE
    )
    projected["final_emit_schema_id"] = (
        str(chain_payload.get("final_emit_schema_id", "")).strip() or FINAL_EMIT_SCHEMA_ID
    )
    projected["final_emit_schema_status"] = (
        _normalize_status(chain_payload.get("final_emit_schema_status", ""))
        or STATUS_PASS_REQUIRED
    )
    projected["final_emit_contract_status"] = (
        _normalize_status(chain_payload.get("final_emit_contract_status", ""))
        or _normalize_status(chain_payload.get("final_emit_guard_status", ""))
        or STATUS_FAIL_REQUIRED
    )

    missing: list[str] = []
    for field in FINAL_EMIT_TUPLE_REQUIRED_FIELDS:
        value = projected.get(field)
        if field == "outlet_bypass_detected":
            continue
        if not str(value or "").strip():
            missing.append(field)
    return projected, missing


def infer_source_domain_from_catalog(catalog_path: str) -> str:
    token = str(catalog_path or "").strip().lower()
    if "/.codex/.identity/" in token or token.endswith("/.codex/.identity/catalog.local.yaml"):
        return "global"
    return "project"


def resolve_pack_relative_path(pack_path: Path, raw_path: str, default_rel: str) -> Path:
    token = str(raw_path or "").strip() or str(default_rel or "").strip()
    if not token:
        return Path("")
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def pick_host_gateway_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def resolve_gateway_signing_secret(pack_path: Path, host_gateway_contract: dict[str, Any]) -> tuple[str, str]:
    ingress_policy = host_gateway_contract.get("ingress_proof_policy")
    egress_policy = host_gateway_contract.get("egress_grant_policy")
    ingress_policy = ingress_policy if isinstance(ingress_policy, dict) else {}
    egress_policy = egress_policy if isinstance(egress_policy, dict) else {}
    signer_secret_env = str(
        ingress_policy.get("signer_secret_env")
        or egress_policy.get("signer_secret_env")
        or ""
    ).strip()
    if signer_secret_env:
        existing = str(os.environ.get(signer_secret_env, "")).strip()
        if existing:
            return signer_secret_env, existing

    candidate_paths: list[Path] = []
    for raw in (
        str(ingress_policy.get("signing_key_path", "")).strip(),
        str(egress_policy.get("signing_key_path", "")).strip(),
        HOST_GATEWAY_DEFAULT_SIGNING_KEY,
    ):
        resolved = resolve_pack_relative_path(pack_path, raw, HOST_GATEWAY_DEFAULT_SIGNING_KEY)
        if resolved and resolved not in candidate_paths:
            candidate_paths.append(resolved)
    for path in candidate_paths:
        if not path.exists():
            continue
        secret = path.read_text(encoding="utf-8", errors="ignore").strip()
        if secret:
            return signer_secret_env, secret
    return signer_secret_env, ""


def run_final_emit_via_instance_wrappers(*, cmd: list[str], protocol_root: Path) -> tuple[int, str, str]:
    def _emit_fail_payload(stale_reason: str) -> tuple[int, str, str]:
        payload = {
            "final_emit_guard_status": "FAIL_REQUIRED",
            "error_code": "IP-HDSTAMP-003",
            "stale_reasons": [str(stale_reason or "final_emit_wrapper_route_failed")],
        }
        out = json.dumps(payload, ensure_ascii=False)
        print(out)
        return 1, out, ""

    catalog = _arg_value(cmd, "--catalog")
    identity_id = _arg_value(cmd, "--identity-id")
    actor_id = _arg_value(cmd, "--actor-id")
    body_text = _arg_value(cmd, "--body-text")
    caller_json_only = _has_flag(cmd, "--json-only")
    if not catalog or not identity_id or not actor_id or not body_text:
        return _emit_fail_payload("final_emit_wrapper_required_args_missing")

    try:
        pack_path, task_path = resolve_pack_and_task(
            Path(catalog).expanduser().resolve(),
            identity_id,
        )
        task = load_json(task_path)
    except Exception as exc:
        err = f"wrapper_runtime_resolve_failed:{exc}"
        print(f"[FAIL] {err}")
        return _emit_fail_payload(err)

    host_gateway_contract = pick_host_gateway_contract(task if isinstance(task, dict) else {})
    host_release_mode = str(host_gateway_contract.get("host_release_mode", "")).strip().lower()
    if host_release_mode != INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE:
        return _emit_fail_payload(f"host_release_mode_not_wrapper_only:{host_release_mode or 'missing'}")

    session_chain_wrapper = resolve_pack_relative_path(
        pack_path,
        str(host_gateway_contract.get("session_chain_wrapper_path", "")).strip(),
        HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
    )
    if not session_chain_wrapper.exists():
        err = f"session_chain_wrapper_missing:{session_chain_wrapper}"
        print(f"[FAIL] {err}")
        return _emit_fail_payload(err)

    signer_secret_env, signer_secret_value = resolve_gateway_signing_secret(pack_path, host_gateway_contract)
    child_env = dict(os.environ)
    if signer_secret_env and signer_secret_value and not str(child_env.get(signer_secret_env, "")).strip():
        child_env[signer_secret_env] = signer_secret_value

    run_id = _arg_value(cmd, "--run-id")
    if not run_id:
        run_id = f"identity-creator-final-emit-{identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
    session_id = _arg_value(cmd, "--session-id")
    if not session_id:
        session_id = f"run:{run_id}"
    work_layer = _arg_value(cmd, "--work-layer", "instance")
    source_layer = _arg_value(cmd, "--source-layer", infer_source_domain_from_catalog(catalog))
    layer_intent_text = _arg_value(cmd, "--layer-intent-text")
    out_reply_file = _arg_value(cmd, "--out-reply-file")
    session_chain_cmd = [
        sys.executable,
        str(session_chain_wrapper),
        "--catalog",
        catalog,
        "--identity-id",
        identity_id,
        "--actor-id",
        actor_id,
        "--session-id",
        session_id,
        "--run-id",
        run_id,
        "--work-layer",
        work_layer,
        "--source-layer",
        source_layer,
        "--operation",
        "inspection",
        "--message",
        body_text,
        "--json-only",
    ]
    if out_reply_file:
        session_chain_cmd.extend(["--out-reply-file", out_reply_file])

    print("$", " ".join(session_chain_cmd))
    timeout_seconds = _resolve_command_timeout_seconds(session_chain_cmd, env=child_env)
    try:
        p_chain = subprocess.run(
            session_chain_cmd,
            capture_output=True,
            text=True,
            cwd=str(protocol_root),
            env=child_env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return _emit_fail_payload(
            _timeout_reason(
                cmd=session_chain_cmd,
                timeout_seconds=timeout_seconds,
                scope="session_chain_wrapper",
            )
        )
    if p_chain.stderr.strip():
        print(p_chain.stderr.strip())
    if p_chain.returncode != 0:
        classified = _classify_subprocess_failure(
            stdout_text=p_chain.stdout or "",
            stderr_text=p_chain.stderr or "",
        )
        if classified and not _looks_like_json_dict(p_chain.stdout or ""):
            code, reason = classified
            payload = {
                "final_emit_guard_status": STATUS_FAIL_REQUIRED,
                "error_code": code,
                "stale_reasons": [reason],
                "compose_rc": int(p_chain.returncode),
                "gateway_wrapper_failure_scope": "session_chain_wrapper_subprocess",
            }
            out = json.dumps(payload, ensure_ascii=False)
            print(out)
            return p_chain.returncode, out, p_chain.stderr or ""
        if p_chain.stdout.strip():
            print(p_chain.stdout.strip())
        return p_chain.returncode, p_chain.stdout or "", p_chain.stderr or ""

    try:
        chain_payload = json.loads(p_chain.stdout or "{}")
        if not isinstance(chain_payload, dict):
            chain_payload = {}
    except Exception:
        chain_payload = {}

    if not chain_payload:
        if p_chain.stdout.strip():
            print(p_chain.stdout.strip())
        return _emit_fail_payload("session_chain_payload_missing_or_non_json")

    if chain_payload:
        final_guard = str(
            chain_payload.get("final_emit_guard_status")
            or chain_payload.get("egress_guard_status")
            or ""
        ).strip()
        if final_guard:
            chain_payload["final_emit_guard_status"] = final_guard
        if layer_intent_text:
            chain_payload.setdefault("layer_intent_text", layer_intent_text)
        if final_guard != "PASS_REQUIRED":
            return _emit_fail_payload("session_chain_final_emit_guard_not_pass_required")
        out_reply_file = str(chain_payload.get("out_reply_file", "")).strip()
        if not out_reply_file:
            return _emit_fail_payload("session_chain_out_reply_file_missing")
        out_reply_path = Path(out_reply_file).expanduser().resolve()
        if not out_reply_path.exists():
            return _emit_fail_payload("session_chain_out_reply_file_not_found")
        reply_text = out_reply_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not reply_text.startswith("Identity-Context:"):
            return _emit_fail_payload("session_chain_reply_first_line_missing_identity_context")
        projected_tuple, tuple_missing = _project_final_emit_tuple_from_session_chain(
            chain_payload=chain_payload
        )
        for key, value in projected_tuple.items():
            chain_payload[key] = value
        tuple_fallback_fields: list[str] = []
        for key, expected in (
            ("run_id", run_id),
            ("actor_id", actor_id),
            ("session_id", session_id),
        ):
            if str(chain_payload.get(key, "")).strip():
                continue
            expected_token = str(expected or "").strip()
            if expected_token:
                chain_payload[key] = expected_token
                tuple_fallback_fields.append(key)
        if tuple_fallback_fields:
            chain_payload["session_chain_tuple_fallback_fields"] = sorted(tuple_fallback_fields)
        chain_payload["emit_channel_id"] = str(chain_payload.get("final_emit_channel_id", "")).strip()
        chain_payload["reply_transport_ref"] = out_reply_file
        chain_payload["reply_transport_binding_status"] = STATUS_PASS_REQUIRED
        chain_payload["headstamp_first_line_status"] = STATUS_PASS_REQUIRED
        wrapper_surface_status = _normalize_status(chain_payload.get("wrapper_surface_status", ""))
        if not wrapper_surface_status:
            wrapper_surface_status = (
                STATUS_PASS_REQUIRED
                if _normalize_status(chain_payload.get("ingress_bundle_status", "")) == STATUS_PASS_REQUIRED
                else STATUS_FAIL_REQUIRED
            )
        chain_payload["wrapper_surface_status"] = wrapper_surface_status
        tuple_status = STATUS_PASS_REQUIRED
        if tuple_missing:
            tuple_status = STATUS_FAIL_REQUIRED
        run_id_status = (
            STATUS_PASS_REQUIRED
            if str(chain_payload.get("run_id", "")).strip() == str(run_id or "").strip()
            else STATUS_FAIL_REQUIRED
        )
        actor_id_status = (
            STATUS_PASS_REQUIRED
            if str(chain_payload.get("actor_id", "")).strip() == str(actor_id or "").strip()
            else STATUS_FAIL_REQUIRED
        )
        session_id_status = (
            STATUS_PASS_REQUIRED
            if str(chain_payload.get("session_id", "")).strip() == str(session_id or "").strip()
            else STATUS_FAIL_REQUIRED
        )
        if STATUS_FAIL_REQUIRED in {run_id_status, actor_id_status, session_id_status}:
            tuple_status = STATUS_FAIL_REQUIRED
            tuple_missing.extend(
                [
                    "run_id_mismatch" if run_id_status == STATUS_FAIL_REQUIRED else "",
                    "actor_id_mismatch" if actor_id_status == STATUS_FAIL_REQUIRED else "",
                    "session_id_mismatch" if session_id_status == STATUS_FAIL_REQUIRED else "",
                ]
            )
        chain_payload["entry_receipt_tuple_status"] = tuple_status
        chain_payload["entry_receipt_tuple_run_id_status"] = run_id_status
        chain_payload["entry_receipt_tuple_actor_id_status"] = actor_id_status
        chain_payload["entry_receipt_tuple_session_id_status"] = session_id_status
        send_time_status = _normalize_status(chain_payload.get("send_time_gate_status", ""))
        if send_time_status == STATUS_PASS_REQUIRED and tuple_status != STATUS_PASS_REQUIRED:
            missing_tokens = [token for token in tuple_missing if token]
            reason = "session_chain_canonical_tuple_missing"
            if missing_tokens:
                reason += ":" + ",".join(sorted(set(missing_tokens)))
            return _emit_fail_payload(reason)
        normalized = json.dumps(chain_payload, ensure_ascii=False)
        if caller_json_only:
            print(normalized)
            return 0, normalized, p_chain.stderr or ""
        print(reply_text)
        return 0, reply_text, p_chain.stderr or ""
    return _emit_fail_payload("session_chain_payload_missing_or_non_json")


def run_required_gate_bundle_via_ingress_wrapper(*, cmd: list[str], protocol_root: Path) -> tuple[int, str, str]:
    def _emit_fail_payload(stale_reason: str) -> tuple[int, str, str]:
        payload = {
            "bundle_status": "FAIL_REQUIRED",
            "error_code": "IP-GATE-ENTRY-001",
            "stale_reasons": [str(stale_reason or "required_gate_wrapper_route_failed")],
        }
        out = json.dumps(payload, ensure_ascii=False)
        print(out)
        return 1, out, ""

    catalog = _arg_value(cmd, "--catalog")
    identity_id = _arg_value(cmd, "--identity-id")
    operation = _arg_value(cmd, "--operation")
    run_id = _arg_value(cmd, "--run-id")
    actor_id = _arg_value(cmd, "--actor-id")
    if not catalog or not identity_id or not operation or not run_id or not actor_id:
        return _emit_fail_payload("required_gate_wrapper_required_args_missing")

    try:
        pack_path, task_path = resolve_pack_and_task(
            Path(catalog).expanduser().resolve(),
            identity_id,
        )
        task = load_json(task_path)
    except Exception as exc:
        err = f"wrapper_runtime_resolve_failed:{exc}"
        print(f"[FAIL] {err}")
        return _emit_fail_payload(err)

    host_gateway_contract = pick_host_gateway_contract(task if isinstance(task, dict) else {})
    host_dispatch_mode = str(host_gateway_contract.get("host_dispatch_mode", "")).strip().lower()
    if host_dispatch_mode != INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE:
        return _emit_fail_payload(f"host_dispatch_mode_not_wrapper_only:{host_dispatch_mode or 'missing'}")

    ingress_wrapper = resolve_pack_relative_path(
        pack_path,
        str(host_gateway_contract.get("ingress_wrapper_path", "")).strip(),
        HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
    )
    if not ingress_wrapper.exists():
        return _emit_fail_payload(f"ingress_wrapper_missing:{ingress_wrapper}")

    signer_secret_env, signer_secret_value = resolve_gateway_signing_secret(pack_path, host_gateway_contract)
    child_env = dict(os.environ)
    if signer_secret_env and signer_secret_value and not str(child_env.get(signer_secret_env, "")).strip():
        child_env[signer_secret_env] = signer_secret_value

    session_id = _arg_value(cmd, "--session-id")
    if not session_id:
        session_id = f"run:{run_id}"
    work_layer = _arg_value(cmd, "--resolved-work-layer", "instance")
    source_layer = _arg_value(cmd, "--resolved-source-layer", infer_source_domain_from_catalog(catalog))
    gate_profile = _arg_value(cmd, "--gate-profile")
    target_name = _arg_value(cmd, "--target-name")
    out_path = _arg_value(cmd, "--out")
    repo_catalog = _arg_value(cmd, "--repo-catalog")

    envelope: dict[str, str | bool] = {}
    for flag, key in (
        ("--lock-state", "lock_state"),
        ("--send-time-gate-status", "send_time_gate_status"),
        ("--final-emit-contract-status", "final_emit_contract_status"),
        ("--final-emit-policy-mode", "final_emit_policy_mode"),
        ("--final-emit-schema-status", "final_emit_schema_status"),
        ("--report-selected-path", "report_selected_path"),
        ("--reply-text", "reply_text"),
        ("--reply-file", "reply_file"),
        ("--reply-log", "reply_log"),
        ("--reply-transport-ref", "reply_transport_ref"),
    ):
        value = _arg_value(cmd, flag)
        if value:
            envelope[key] = value
    if _has_flag(cmd, "--reply-outlet-guard-applied"):
        envelope["reply_outlet_guard_applied"] = True
    outlet_bypass = _arg_value(cmd, "--outlet-bypass-detected")
    if outlet_bypass:
        envelope["outlet_bypass_detected"] = str(outlet_bypass).strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }

    ingress_cmd = [
        sys.executable,
        str(ingress_wrapper),
        "--catalog",
        catalog,
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--run-id",
        run_id,
        "--actor-id",
        actor_id,
        "--session-id",
        session_id,
        "--work-layer",
        work_layer,
        "--source-layer",
        source_layer,
        "--json-only",
    ]
    if gate_profile:
        ingress_cmd.extend(["--gate-profile", gate_profile])
    if target_name:
        ingress_cmd.extend(["--target-name", target_name])
    if out_path:
        ingress_cmd.extend(["--out", out_path])
    if repo_catalog:
        ingress_cmd.extend(["--repo-catalog", repo_catalog])
    if envelope:
        ingress_cmd.extend(["--envelope-json", json.dumps(envelope, ensure_ascii=False)])

    print("$", " ".join(ingress_cmd))
    timeout_seconds = _resolve_command_timeout_seconds(ingress_cmd, env=child_env)
    try:
        p_ingress = subprocess.run(
            ingress_cmd,
            capture_output=True,
            text=True,
            cwd=str(protocol_root),
            env=child_env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return _emit_fail_payload(
            _timeout_reason(
                cmd=ingress_cmd,
                timeout_seconds=timeout_seconds,
                scope="ingress_wrapper",
            )
        )
    if p_ingress.stdout.strip():
        print(p_ingress.stdout.strip())
    if p_ingress.stderr.strip():
        print(p_ingress.stderr.strip())
    if p_ingress.returncode != 0:
        classified = _classify_subprocess_failure(
            stdout_text=p_ingress.stdout or "",
            stderr_text=p_ingress.stderr or "",
        )
        if classified and not _looks_like_json_dict(p_ingress.stdout or ""):
            code, reason = classified
            payload = {
                "bundle_status": STATUS_FAIL_REQUIRED,
                "error_code": code,
                "stale_reasons": [reason],
                "gateway_wrapper_failure_scope": "ingress_wrapper_subprocess",
            }
            out = json.dumps(payload, ensure_ascii=False)
            print(out)
            return p_ingress.returncode, out, p_ingress.stderr or ""
    return p_ingress.returncode, p_ingress.stdout or "", p_ingress.stderr or ""


def run_gateway_wrapped_command(
    *,
    cmd: list[str],
    protocol_root: Path,
    passthrough_cwd: Path | None = None,
    passthrough_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    if len(cmd) >= 2 and str(cmd[1]).strip() == FINAL_EMIT_SCRIPT:
        return run_final_emit_via_instance_wrappers(cmd=cmd, protocol_root=protocol_root)
    if len(cmd) >= 2 and str(cmd[1]).strip() == REQUIRED_GATE_BUNDLE_SCRIPT:
        return run_required_gate_bundle_via_ingress_wrapper(cmd=cmd, protocol_root=protocol_root)
    print("$", " ".join(cmd))
    run_cwd = passthrough_cwd.resolve() if isinstance(passthrough_cwd, Path) else protocol_root
    timeout_seconds = _resolve_command_timeout_seconds(cmd, env=passthrough_env)
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(run_cwd),
            env=passthrough_env,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        payload = {
            "gateway_wrapper_status": STATUS_FAIL_REQUIRED,
            "context_timeout_guard_status": STATUS_FAIL_REQUIRED,
            "context_timeout_marker": CTX_TOOL_TIMEOUT_MARKER,
            "error_code": CTX_TOOL_TIMEOUT_ERROR_CODE,
            "timeout_seconds": int(timeout_seconds),
            "stale_reasons": [
                _timeout_reason(
                    cmd=cmd,
                    timeout_seconds=timeout_seconds,
                    scope="gateway_passthrough",
                )
            ],
        }
        out = json.dumps(payload, ensure_ascii=False)
        print(out)
        return TIMEOUT_RETURN_CODE, out, str(exc)
    if p.stdout.strip():
        print(p.stdout.strip())
    if p.stderr.strip():
        print(p.stderr.strip())
    if p.returncode != 0:
        classified = _classify_subprocess_failure(
            stdout_text=p.stdout or "",
            stderr_text=p.stderr or "",
        )
        if classified and not _looks_like_json_dict(p.stdout or ""):
            code, reason = classified
            payload = {
                "gateway_wrapper_status": STATUS_FAIL_REQUIRED,
                "error_code": code,
                "stale_reasons": [reason],
                "gateway_wrapper_failure_scope": "gateway_passthrough_subprocess",
            }
            out = json.dumps(payload, ensure_ascii=False)
            print(out)
            return p.returncode, out, p.stderr or ""
    return p.returncode, p.stdout or "", p.stderr or ""
