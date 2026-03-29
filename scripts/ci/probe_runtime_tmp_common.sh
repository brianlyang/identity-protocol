#!/usr/bin/env bash

probe_runtime_tmp_bootstrap() {
  local repo_root="$1"
  local temp_scope="$2"
  local temp_prefix="${3:-run}"
  # shellcheck source=../runtime_temp_path_common.sh
  source "${repo_root}/scripts/runtime_temp_path_common.sh"
  export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-${repo_root}/.tmp}"
  TMP_ROOT="$(identity_runtime_mktemp_dir_sh "${temp_scope}" "${temp_prefix}")"
  trap 'rm -rf "${TMP_ROOT}"' EXIT
}
