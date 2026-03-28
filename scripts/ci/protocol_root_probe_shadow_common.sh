#!/usr/bin/env bash

protocol_root_probe_bootstrap() {
  local script_dir="$1"
  local tmp_prefix="$2"
  ROOT="$(cd "${script_dir}/../.." && pwd)"
  TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/${tmp_prefix}.XXXXXX")"
  trap 'rm -rf "${TMP_ROOT}"' EXIT
  # shellcheck source=./probe_repo_mirror_common.sh
  source "${script_dir}/probe_repo_mirror_common.sh"
}

protocol_root_probe_define_full_mirror() {
  mirror_repo() {
    local dst="$1"
    probe_mirror_repo "${ROOT}" "${dst}"
  }
}

protocol_root_probe_define_relpath_mirror() {
  PROTOCOL_ROOT_PROBE_REL_PATHS=("$@")
  mirror_repo() {
    local dst="$1"
    probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROTOCOL_ROOT_PROBE_REL_PATHS[@]}"
  }
}
