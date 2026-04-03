#!/usr/bin/env bash
set -euo pipefail

identity_runtime_temp_root_sh() {
  local root="${IDENTITY_RUNTIME_TMP_ROOT:-${RUNNER_TEMP:-${TMPDIR:-${TEMP:-${TMP:-}}}}}"
  if [[ -z "${root}" ]]; then
    root="$(python3 - <<'PY'
import tempfile
print(tempfile.gettempdir())
PY
)"
  fi
  mkdir -p "${root}"
  printf '%s\n' "${root}"
}

identity_runtime_slug_sh() {
  local raw="${1:-runtime-temp}"
  raw="${raw//[^A-Za-z0-9_.-]/-}"
  raw="${raw##[-._]}"
  raw="${raw%%[-._]}"
  if [[ -z "${raw}" ]]; then
    raw="runtime-temp"
  fi
  printf '%s\n' "${raw}"
}

identity_runtime_named_temp_root_sh() {
  local name
  name="$(identity_runtime_slug_sh "${1:-runtime-temp}")"
  local root
  root="$(identity_runtime_temp_root_sh)"
  local path="${root}/identity-runtime/${name}"
  mkdir -p "${path}"
  printf '%s\n' "${path}"
}

identity_runtime_mktemp_dir_sh() {
  local name="${1:-runtime-temp}"
  local prefix="${2:-run}"
  local base
  base="$(identity_runtime_named_temp_root_sh "${name}")"
  mktemp -d "${base}/$(identity_runtime_slug_sh "${prefix}").XXXXXX"
}
