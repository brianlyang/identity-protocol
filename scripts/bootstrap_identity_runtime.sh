#!/usr/bin/env bash
set -euo pipefail

# Bootstrap identity runtime paths for a project-scoped workflow.
# Defaults are REPO-scoped (skills-like), but can be overridden by args.
#
# Usage:
#   scripts/bootstrap_identity_runtime.sh
#   scripts/bootstrap_identity_runtime.sh /abs/runtime/root /abs/protocol/root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RUNTIME_ROOT="${1:-${REPO_ROOT}/.agents/identity}"
PROTOCOL_ROOT="${2:-${REPO_ROOT}}"
CONFIG_PATH="${RUNTIME_ROOT}/config/runtime-paths.env"

mkdir -p "${RUNTIME_ROOT}/config"

python3 "${SCRIPT_DIR}/configure_identity_runtime_paths.py" \
  --identity-home "${RUNTIME_ROOT}" \
  --protocol-home "${PROTOCOL_ROOT}" \
  --config-path "${CONFIG_PATH}"

cat <<EOF
[OK] project runtime bootstrap completed
     IDENTITY_HOME=${RUNTIME_ROOT}
     IDENTITY_PROTOCOL_HOME=${PROTOCOL_ROOT}
     CONFIG_PATH=${CONFIG_PATH}

Next:
  export IDENTITY_HOME="${RUNTIME_ROOT}"
  export IDENTITY_PROTOCOL_HOME="${PROTOCOL_ROOT}"
EOF
