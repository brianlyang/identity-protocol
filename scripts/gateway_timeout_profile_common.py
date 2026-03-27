from __future__ import annotations

import json
import os
from typing import Any

from protocol_infra_contract import (
    GATEWAY_CONTEXT_RESOLVE_TIMEOUT_SECONDS_DEFAULT,
    GATEWAY_WRAPPER_DIRECT_RUNTIME_OPERATION_TIMEOUT_PROFILE_SECONDS,
    GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT,
    GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS,
)

RUNTIME_INGRESS_WRAPPER_NAME = "protocol_ingress_wrapper.py"


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return int(default)
    return parsed if parsed > 0 else int(default)


def _script_hint_from_cmd(cmd: list[str]) -> str:
    if len(cmd) < 2:
        return ""
    return str(cmd[1] or "").strip()


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


def _is_context_resolve_cmd(cmd: list[str]) -> bool:
    return _script_hint_from_cmd(cmd).endswith("resolve_identity_context.py")


def _parse_envelope_json(raw: str) -> dict[str, Any]:
    token = str(raw or "").strip()
    if not token:
        return {}
    try:
        data = json.loads(token)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_runtime_wrapper_operation(cmd: list[str]) -> str:
    operation = _arg_value(cmd, "--operation")
    if operation:
        return operation.strip().lower()
    envelope = _parse_envelope_json(_arg_value(cmd, "--envelope-json"))
    return str(envelope.get("operation", "") or "").strip().lower()


def resolve_gateway_command_timeout_seconds(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    default_timeout_env: str,
    context_timeout_env: str,
) -> int:
    env_map = env if isinstance(env, dict) else os.environ
    default_timeout = int(GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT)
    script_hint = _script_hint_from_cmd(cmd)
    for script_name, timeout_value in GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS:
        name_token = str(script_name or "").strip()
        if name_token and script_hint.endswith(name_token):
            default_timeout = _safe_positive_int(timeout_value, default_timeout)
            break
    else:
        if script_hint.endswith(RUNTIME_INGRESS_WRAPPER_NAME):
            operation = _resolve_runtime_wrapper_operation(cmd)
            for operation_name, timeout_value in GATEWAY_WRAPPER_DIRECT_RUNTIME_OPERATION_TIMEOUT_PROFILE_SECONDS:
                if operation == str(operation_name or "").strip().lower():
                    default_timeout = _safe_positive_int(timeout_value, default_timeout)
                    break

    env_token = str(env_map.get(default_timeout_env, "")).strip()
    if _is_context_resolve_cmd(cmd):
        default_timeout = int(GATEWAY_CONTEXT_RESOLVE_TIMEOUT_SECONDS_DEFAULT)
        context_token = str(env_map.get(context_timeout_env, "")).strip()
        if context_token:
            env_token = context_token
    return _safe_positive_int(env_token, default_timeout)


def prepare_nested_gateway_timeout_env(
    *,
    entry_cmd: list[str],
    wrapper_cmd: list[str],
    child_env: dict[str, str],
    default_timeout_env: str,
    context_timeout_env: str,
) -> int:
    entry_timeout = resolve_gateway_command_timeout_seconds(
        entry_cmd,
        env=child_env,
        default_timeout_env=default_timeout_env,
        context_timeout_env=context_timeout_env,
    )
    wrapper_timeout = resolve_gateway_command_timeout_seconds(
        wrapper_cmd,
        env=child_env,
        default_timeout_env=default_timeout_env,
        context_timeout_env=context_timeout_env,
    )
    effective_timeout = max(entry_timeout, wrapper_timeout)
    current_env_timeout = _safe_positive_int(child_env.get(default_timeout_env), default=0)
    if current_env_timeout < effective_timeout:
        child_env[default_timeout_env] = str(effective_timeout)
    return effective_timeout
