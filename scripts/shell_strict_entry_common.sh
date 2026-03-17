#!/usr/bin/env bash
# shellcheck shell=bash

if [[ -n "${ZSH_VERSION:-}" ]]; then
  STRICT_ENTRY_SOURCE_FILE="${(%):-%N}"
elif [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  STRICT_ENTRY_SOURCE_FILE="${BASH_SOURCE[0]}"
else
  STRICT_ENTRY_SOURCE_FILE="$0"
fi

STRICT_ENTRY_SCRIPT_DIR="$(cd "$(dirname "${STRICT_ENTRY_SOURCE_FILE}")" && pwd)"
STRICT_ENTRY_REPO_ROOT="$(cd "${STRICT_ENTRY_SCRIPT_DIR}/.." && pwd)"

protocol_shell_entry_repo_root() {
  printf '%s\n' "${STRICT_ENTRY_REPO_ROOT}"
}

protocol_shell_entry_repo_catalog_path() {
  local repo_catalog_path="${1:-identity/catalog/identities.yaml}"
  printf '%s\n' "${repo_catalog_path}"
}

protocol_shell_entry_resolve_project_catalog() {
  local explicit_catalog="${1:-}"
  if [[ -n "${explicit_catalog}" ]]; then
    printf '%s\n' "${explicit_catalog}"
    return 0
  fi
  if [[ -z "${IDENTITY_CATALOG:-}" ]]; then
    # Reuse the protocol-owned runtime selector instead of open-coding path defaults.
    source "${STRICT_ENTRY_REPO_ROOT}/scripts/use_project_identity_runtime.sh" >/dev/null
  fi
  if [[ -z "${IDENTITY_CATALOG:-}" ]]; then
    echo "[FAIL] IP-CATALOG-ENTRY-001 runtime catalog unresolved; export IDENTITY_CATALOG or pass CATALOG_PATH explicitly." >&2
    return 1
  fi
  if [[ ! -f "${IDENTITY_CATALOG}" ]]; then
    echo "[FAIL] IP-CATALOG-ENTRY-002 runtime catalog missing: ${IDENTITY_CATALOG}" >&2
    return 1
  fi
  printf '%s\n' "${IDENTITY_CATALOG}"
}

protocol_shell_entry_require_actor_id() {
  local explicit_actor_id="${1:-}"
  local actor_id="${explicit_actor_id:-${CODEX_ACTOR_ID:-}}"
  if [[ -z "${actor_id}" ]]; then
    echo "[FAIL] IP-ACTOR-ENTRY-001 actor-id required: export CODEX_ACTOR_ID or set HEADSTAMP_ACTOR_ID explicitly." >&2
    return 1
  fi
  printf '%s\n' "${actor_id}"
}
