#!/usr/bin/env bash
# shellcheck shell=bash

# NOTE: this script is intended to be sourced; avoid mutating caller shell
# strict flags (set -e/-u) globally.

# Unified runtime mode selector.
# Recommended to source so selected mode exports remain in current shell.
#
# Usage:
#   source ./scripts/identity_runtime_select.sh project
#   source ./scripts/identity_runtime_select.sh global
#   source ./scripts/identity_runtime_select.sh            # interactive prompt

if [[ -n "${ZSH_VERSION:-}" ]]; then
  SOURCE_FILE="${(%):-%N}"
elif [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SOURCE_FILE="${BASH_SOURCE[0]}"
else
  SOURCE_FILE="$0"
fi

SCRIPT_DIR="$(cd "$(dirname "${SOURCE_FILE}")" && pwd)"
MODE="${1:-}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ -z "${MODE}" ]]; then
  if [[ -t 0 ]]; then
    echo "Select identity runtime mode:"
    echo "  1) project (recommended) -> <repo>/.agents/identity"
    echo "  2) global                -> ~/.codex/identity"
    read -r -p "Enter choice [1/2]: " choice
    case "${choice}" in
      1) MODE="project" ;;
      2) MODE="global" ;;
      *) echo "[FAIL] invalid choice: ${choice}"; return 1 2>/dev/null || exit 1 ;;
    esac
  else
    echo "[FAIL] mode is required in non-interactive shell. use: project|global"
    return 1 2>/dev/null || exit 1
  fi
fi

MODE="$(echo "${MODE}" | tr '[:upper:]' '[:lower:]')"
case "${MODE}" in
  project|p)
    # shellcheck disable=SC1091
    if ! source "${SCRIPT_DIR}/use_project_identity_runtime.sh" "$@"; then
      echo "[FAIL] project mode bootstrap failed."
      return 1 2>/dev/null || exit 1
    fi
    SELECTED_MODE="project"
    ;;
  global|g|local)
    # shellcheck disable=SC1091
    if ! source "${SCRIPT_DIR}/use_local_identity_env.sh" "$@"; then
      echo "[FAIL] global mode bootstrap failed."
      echo "       suggestion: source ./scripts/identity_runtime_select.sh project"
      return 1 2>/dev/null || exit 1
    fi
    SELECTED_MODE="global"
    ;;
  *)
    echo "[FAIL] unsupported mode: ${MODE}. use project|global"
    return 1 2>/dev/null || exit 1
    ;;
esac

echo "[OK] identity runtime mode selected: ${SELECTED_MODE}"
echo "     IDENTITY_HOME=${IDENTITY_HOME:-}"
echo "     IDENTITY_CATALOG=${IDENTITY_CATALOG:-}"
echo "     IDENTITY_PROTOCOL_HOME=${IDENTITY_PROTOCOL_HOME:-}"
