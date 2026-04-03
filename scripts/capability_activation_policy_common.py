#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

CAPABILITY_ACTIVATION_PRIMARY_POLICY = "strict-union"
CAPABILITY_ACTIVATION_ENV_AUTH_FALLBACK_POLICY = "route-any-ready"
CAPABILITY_ACTIVATION_ENV_AUTH_ERROR_CODE = "IP-CAP-003"


def normalize_capability_activation_policy(value: Any) -> str:
    token = str(value or "").strip().lower()
    if token in {
        CAPABILITY_ACTIVATION_PRIMARY_POLICY,
        CAPABILITY_ACTIVATION_ENV_AUTH_FALLBACK_POLICY,
    }:
        return token
    return CAPABILITY_ACTIVATION_PRIMARY_POLICY


def replace_capability_activation_policy(cmd: list[str], policy: str) -> list[str]:
    out = list(cmd)
    normalized_policy = normalize_capability_activation_policy(policy)
    if "--activation-policy" in out:
        idx = out.index("--activation-policy")
        if idx + 1 < len(out):
            out[idx + 1] = normalized_policy
            return out
    out.extend(["--activation-policy", normalized_policy])
    return out


def capability_env_auth_fallback_eligible(
    *,
    requested_policy: str,
    error_code: str,
    status: str = "",
    rc: int = 0,
) -> bool:
    normalized_policy = normalize_capability_activation_policy(requested_policy)
    normalized_error_code = str(error_code or "").strip()
    normalized_status = str(status or "").strip().upper()
    return (
        normalized_policy == CAPABILITY_ACTIVATION_PRIMARY_POLICY
        and normalized_error_code == CAPABILITY_ACTIVATION_ENV_AUTH_ERROR_CODE
        and (rc != 0 or normalized_status == "BLOCKED")
    )
