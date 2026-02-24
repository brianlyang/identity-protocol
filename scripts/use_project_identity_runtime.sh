#!/usr/bin/env bash
# shellcheck shell=bash

# Source this script to switch identity runtime to a project-scoped root.
# Usage:
#   source ./scripts/use_project_identity_runtime.sh
#   source ./scripts/use_project_identity_runtime.sh /custom/runtime/root /custom/protocol/root

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

# Prefer parent project root when protocol repo is checked out as a subdirectory
# (e.g. <project>/identity-protocol-local). This keeps runtime artifacts outside
# protocol_root and avoids IP-PATH-001 boundary failures.
if [[ "$(basename "${REPO_ROOT}")" == "identity-protocol-local" ]]; then
  PROJECT_ROOT_DEFAULT="$(cd "${REPO_ROOT}/.." && pwd)"
  IDENTITY_HOME_DEFAULT="${PROJECT_ROOT_DEFAULT}/.agents/identity"
else
  PROJECT_ROOT_DEFAULT="${REPO_ROOT}"
  IDENTITY_HOME_DEFAULT="/tmp/codex-identity-runtime/${USER}/$(basename "${REPO_ROOT}")"
fi

PROJECT_ROOT="${PROJECT_ROOT:-${PROJECT_ROOT_DEFAULT}}"
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
    echo "[WARN] unable to persist runtime-paths.env; continue with in-shell exports only."
    echo "       target=${RUNTIME_ENV_PATH}"
  fi
else
  echo "[WARN] runtime-paths.env target not writable; continue with in-shell exports only."
  echo "       target=${RUNTIME_ENV_PATH}"
fi

export IDENTITY_HOME
export IDENTITY_PROTOCOL_HOME
export IDENTITY_CATALOG
export IDENTITY_SCOPE="USER"

echo "[OK] project identity runtime loaded"
echo "     PROJECT_ROOT=${PROJECT_ROOT}"
echo "     IDENTITY_HOME=${IDENTITY_HOME}"
echo "     IDENTITY_PROTOCOL_HOME=${IDENTITY_PROTOCOL_HOME}"
echo "     IDENTITY_CATALOG=${IDENTITY_CATALOG}"
echo "     IDENTITY_SCOPE=${IDENTITY_SCOPE}"
