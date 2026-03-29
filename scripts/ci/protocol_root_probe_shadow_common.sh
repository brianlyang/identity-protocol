#!/usr/bin/env bash

protocol_root_probe_bootstrap() {
  local script_dir="$1"
  local tmp_prefix="$2"
  ROOT="$(cd "${script_dir}/../.." && pwd)"
  # shellcheck source=./probe_runtime_tmp_common.sh
  source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"
  probe_runtime_tmp_bootstrap "${ROOT}" "protocol-root-probes" "${tmp_prefix}"
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

protocol_root_probe_swap_numbered_surface_order_rows() {
  local path="$1"
  local section_marker="$2"
  local next_marker="$3"
  local first="$4"
  local second="$5"
  python3 - "$path" "$section_marker" "$next_marker" "$first" "$second" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
section_marker = sys.argv[2]
next_marker = sys.argv[3]
first = sys.argv[4]
second = sys.argv[5]

if not first.startswith("1. "):
    raise SystemExit(f"first row must start with '1. ': {first}")
if not second.startswith("2. "):
    raise SystemExit(f"second row must start with '2. ': {second}")

text = path.read_text(encoding="utf-8")
assert section_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, sep, after = rest.partition(next_marker)
assert sep, rest[:4000]
assert first in section_body, section_body
assert second in section_body, section_body

swapped_first = "1. " + second[3:]
swapped_second = "2. " + first[3:]
section_body = section_body.replace(first, "__TEMP__", 1)
section_body = section_body.replace(second, swapped_second, 1)
section_body = section_body.replace("__TEMP__", swapped_first, 1)
path.write_text(before + section_marker + section_body + sep + after, encoding="utf-8")
PY
}
