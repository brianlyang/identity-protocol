#!/usr/bin/env bash

probe_mirror_repo() {
  local root="$1"
  local dst="$2"
  mkdir -p "${dst}"
  _probe_mirror_copy_tree "${root}/identity" "${dst}/identity"
  _probe_mirror_copy_tree "${root}/scripts" "${dst}/scripts"
}

probe_mirror_repo_with_relpaths() {
  local root="$1"
  local dst="$2"
  shift 2
  mkdir -p "${dst}"
  _probe_mirror_copy_tree "${root}/identity" "${dst}/identity"
  local relpath=""
  for relpath in "$@"; do
    _probe_mirror_copy_relpath "${root}" "${dst}" "${relpath}"
  done
}

_probe_mirror_copy_relpath() {
  local root="$1"
  local dst_root="$2"
  local relpath="$3"
  local src="${root}/${relpath}"
  local dst="${dst_root}/${relpath}"
  mkdir -p "$(dirname "${dst}")"
  rm -rf "${dst}"
  if [ -d "${src}" ]; then
    _probe_mirror_copy_tree "${src}" "${dst}"
    return 0
  fi
  _probe_mirror_copy_file "${src}" "${dst}"
}

_probe_mirror_copy_tree() {
  local src="$1"
  local dst="$2"
  rm -rf "${dst}"
  if cp -cR "${src}" "${dst}" 2>/dev/null; then
    return 0
  fi
  cp -R "${src}" "${dst}"
}

_probe_mirror_copy_file() {
  local src="$1"
  local dst="$2"
  if cp -c "${src}" "${dst}" 2>/dev/null; then
    return 0
  fi
  cp "${src}" "${dst}"
}
