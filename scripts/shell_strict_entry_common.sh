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

protocol_shell_entry_require_session_id() {
  local explicit_session_id="${1:-}"
  local session_id="${explicit_session_id:-${CODEX_SESSION_ID:-${IDENTITY_SESSION_ID:-}}}"
  if [[ -z "${session_id}" ]]; then
    echo "[FAIL] IP-SESSION-ENTRY-001 session-id required: export CODEX_SESSION_ID / IDENTITY_SESSION_ID or pass --session-id explicitly." >&2
    return 1
  fi
  printf '%s\n' "${session_id}"
}

protocol_shell_entry_resolve_session_primary_identity() {
  local catalog_path="${1:-}"
  local actor_id="${2:-}"
  local session_id="${3:-}"
  local explicit_identity_id="${4:-}"
  local payload=""

  local cmd=(
    python3
    "${STRICT_ENTRY_REPO_ROOT}/scripts/resolve_runtime_authoritative_identity.py"
    --catalog
    "${catalog_path}"
    --actor-id
    "${actor_id}"
    --session-id
    "${session_id}"
    --json-only
  )
  if [[ -n "${explicit_identity_id}" ]]; then
    cmd+=(--identity-id "${explicit_identity_id}")
  fi

  if ! payload="$("${cmd[@]}")"; then
    printf '%s\n' "${payload}" >&2
    return 1
  fi

  python3 - "${payload}" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
identity_id = str(payload.get("authoritative_identity_id", "")).strip()
if not identity_id:
    raise SystemExit(json.dumps(payload, ensure_ascii=False))
print(identity_id)
PY
}
