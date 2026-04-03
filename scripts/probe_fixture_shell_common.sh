#!/usr/bin/env bash
# Shared helpers for fixture-mutating probe scripts.
# These helpers resolve protocol-owned Python constants/expressions and mutate
# copied fixture files without hardcoding per-probe Python snippets.

probe_fixture_repo_root() {
  if [ -n "${PROBE_FIXTURE_REPO_ROOT:-}" ]; then
    printf '%s\n' "${PROBE_FIXTURE_REPO_ROOT}"
    return 0
  fi
  pwd
}

resolve_probe_project_identity_home() {
  local repo_root="${1:-}"
  local repo_catalog_path="${2:-}"
  if [ -z "${repo_root}" ]; then
    repo_root="$(probe_fixture_repo_root)"
  fi
  if [ -z "${repo_catalog_path}" ]; then
    repo_catalog_path="${repo_root}/identity/catalog/identities.yaml"
  fi
  python3 - "$repo_root" "$repo_catalog_path" <<'PY'
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
repo_catalog_path = Path(sys.argv[2]).expanduser().resolve()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))

from resolve_identity_context import _project_identity_home_from_repo_catalog

print(str(_project_identity_home_from_repo_catalog(repo_root, repo_catalog_path)))
PY
}

resolve_python_module_constant() {
  local module_name="$1"
  local attr_name="$2"
  local repo_root
  repo_root="$(probe_fixture_repo_root)"
  python3 - "$module_name" "$attr_name" "$repo_root" <<'PY'
import importlib
import sys
from pathlib import Path

repo_root = Path(sys.argv[3]).resolve()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))
module = importlib.import_module(sys.argv[1])
value = getattr(module, sys.argv[2])
print(str(value))
PY
}

resolve_python_module_expression() {
  local module_name="$1"
  local expression="$2"
  local repo_root
  repo_root="$(probe_fixture_repo_root)"
  python3 - "$module_name" "$expression" "$repo_root" <<'PY'
import importlib
import sys
from pathlib import Path

repo_root = Path(sys.argv[3]).resolve()
scripts_dir = repo_root / "scripts"
sys.path.insert(0, str(scripts_dir))
module = importlib.import_module(sys.argv[1])
namespace = vars(module).copy()
value = eval(sys.argv[2], namespace, namespace)
print(str(value))
PY
}

mutate_probe_literal() {
  local path="$1"
  local needle="$2"
  local replacement="${3:-}"
  local repo_root
  repo_root="$(probe_fixture_repo_root)"
  python3 "${repo_root}/scripts/probe_fixture_literal_mutation.py" \
    --path "$path" \
    --needle "$needle" \
    --replacement "$replacement" \
    --require-absent-after
}
