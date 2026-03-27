#!/usr/bin/env bash

probe_mirror_repo() {
  local root="$1"
  local dst="$2"
  mkdir -p "${dst}"
  _probe_mirror_copy_tree "${root}/identity" "${dst}/identity"
  _probe_mirror_copy_tree "${root}/scripts" "${dst}/scripts"
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
