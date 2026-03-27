#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHONPATH="${REPO_ROOT}/scripts" python3 - <<'PY'
from gateway_timeout_profile_common import (
    prepare_nested_gateway_timeout_env,
    resolve_gateway_command_timeout_seconds,
)

DEFAULT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CMD_TIMEOUT_SECONDS"
CONTEXT_TIMEOUT_ENV = "IDENTITY_PROTOCOL_GATEWAY_CONTEXT_TIMEOUT_SECONDS"

entry_cmd = ["python3", "scripts/identity_creator.py", "update"]
wrapper_cmd = [
    "python3",
    "/tmp/probe/runtime/gate/protocol_ingress_wrapper.py",
    "--envelope-json",
    '{"operation":"update","identity_id":"probe"}',
]
update_timeout = resolve_gateway_command_timeout_seconds(
    wrapper_cmd,
    env={},
    default_timeout_env=DEFAULT_TIMEOUT_ENV,
    context_timeout_env=CONTEXT_TIMEOUT_ENV,
)
assert update_timeout == 300, update_timeout
print("gateway_wrapper_direct_runtime_update_timeout_profile=PASS_REQUIRED")

inspection_wrapper_cmd = [
    "python3",
    "/tmp/probe/runtime/gate/protocol_ingress_wrapper.py",
    "--envelope-json",
    '{"operation":"inspection","identity_id":"probe"}',
]
inspection_timeout = resolve_gateway_command_timeout_seconds(
    inspection_wrapper_cmd,
    env={},
    default_timeout_env=DEFAULT_TIMEOUT_ENV,
    context_timeout_env=CONTEXT_TIMEOUT_ENV,
)
assert inspection_timeout == 30, inspection_timeout
print("gateway_wrapper_direct_runtime_light_timeout_profile=PASS_REQUIRED")

child_env = {}
effective_timeout = prepare_nested_gateway_timeout_env(
    entry_cmd=entry_cmd,
    wrapper_cmd=wrapper_cmd,
    child_env=child_env,
    default_timeout_env=DEFAULT_TIMEOUT_ENV,
    context_timeout_env=CONTEXT_TIMEOUT_ENV,
)
assert effective_timeout == 300, effective_timeout
assert child_env[DEFAULT_TIMEOUT_ENV] == "300", child_env
print("gateway_wrapper_nested_env_timeout_projection=PASS_REQUIRED")
PY

echo "[PASS] gateway wrapper timeout profile probes passed"
