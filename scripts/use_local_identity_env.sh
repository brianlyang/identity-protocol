#!/usr/bin/env bash
# shellcheck shell=bash

# Source this script to switch identity runtime to a user/global root.
# Usage:
#   source ./scripts/use_local_identity_env.sh
#   source ./scripts/use_local_identity_env.sh /custom/identity/home /custom/protocol/root

# NOTE: this script is intended to be sourced; avoid mutating caller shell
# strict flags (set -e/-u) globally.

if [[ -n "${ZSH_VERSION:-}" ]]; then
  SOURCE_FILE="${(%):-%N}"
elif [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SOURCE_FILE="${BASH_SOURCE[0]}"
else
  SOURCE_FILE="$0"
fi

SCRIPT_DIR="$(cd "$(dirname "${SOURCE_FILE}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CODEX_HOME_DEFAULT="${HOME}/.codex"
IDENTITY_HOME_DEFAULT="${CODEX_HOME_DEFAULT}/identity"
IDENTITY_HOME="${1:-${IDENTITY_HOME_DEFAULT}}"
IDENTITY_PROTOCOL_HOME="${2:-${REPO_ROOT}}"
IDENTITY_CATALOG="${IDENTITY_HOME}/catalog.local.yaml"

mkdir -p "${IDENTITY_HOME}/config"
RUNTIME_ENV_PATH="${IDENTITY_HOME}/config/runtime-paths.env"
if [[ -w "${IDENTITY_HOME}/config" ]] && [[ ! -e "${RUNTIME_ENV_PATH}" || -w "${RUNTIME_ENV_PATH}" ]]; then
  if ! python3 "${SCRIPT_DIR}/configure_identity_runtime_paths.py" \
    --identity-home "${IDENTITY_HOME}" \
    --protocol-home "${IDENTITY_PROTOCOL_HOME}" \
    --config-path "${RUNTIME_ENV_PATH}" >/dev/null 2>&1; then
    echo "[FAIL] unable to write runtime-paths.env under global identity home."
    echo "       target=${RUNTIME_ENV_PATH}"
    echo "       in restricted sandbox sessions, either:"
    echo "       1) approve escalation for global mode, or"
    echo "       2) switch to project mode:"
    echo "          source ./scripts/use_project_identity_runtime.sh"
    return 1 2>/dev/null || exit 1
  fi
else
  echo "[FAIL] runtime-paths.env target is not writable under global identity home."
  echo "       target=${RUNTIME_ENV_PATH}"
  echo "       in restricted sandbox sessions, either:"
  echo "       1) approve escalation for global mode, or"
  echo "       2) switch to project mode:"
  echo "          source ./scripts/use_project_identity_runtime.sh"
  return 1 2>/dev/null || exit 1
fi

export IDENTITY_HOME
export IDENTITY_PROTOCOL_HOME
export IDENTITY_CATALOG
export IDENTITY_SCOPE="USER"

echo "[OK] global identity runtime loaded"
echo "     IDENTITY_HOME=${IDENTITY_HOME}"
echo "     IDENTITY_PROTOCOL_HOME=${IDENTITY_PROTOCOL_HOME}"
echo "     IDENTITY_CATALOG=${IDENTITY_CATALOG}"
echo "     IDENTITY_SCOPE=${IDENTITY_SCOPE}"
echo "     [note] in restricted sandbox sessions, global mode may require escalation for writeback."
