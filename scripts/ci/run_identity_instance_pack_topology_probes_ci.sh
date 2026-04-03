#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/scripts/runtime_temp_path_common.sh"
export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-$ROOT/.tmp}"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "instance-pack-topology-probes" "run")"
trap 'rm -rf "$TMP_ROOT"' EXIT

LEGACY_ROOT="$TMP_ROOT/legacy-pack"
LEGACY_CATALOG="$TMP_ROOT/catalog.local.yaml"
BACKFILL_JSON="$TMP_ROOT/backfill.json"
POSITIVE_JSON="$TMP_ROOT/positive.json"
NEG_RUNTIME_JSON="$TMP_ROOT/neg-runtime-scripts.json"
NEG_CACHE_JSON="$TMP_ROOT/neg-cache.json"
NEG_README_JSON="$TMP_ROOT/neg-readme.json"

python3 - "$LEGACY_ROOT" "$LEGACY_CATALOG" "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

import yaml

pack_root = Path(sys.argv[1]).resolve()
catalog_path = Path(sys.argv[2]).resolve()
repo_root = Path(sys.argv[3]).resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from create_identity_pack import _default_identity_agent_yaml  # noqa: E402

identity_id = "v1613-topology-probe"
pack_root.mkdir(parents=True, exist_ok=True)
(pack_root / "IDENTITY_PROMPT.md").write_text("# Probe Prompt\n", encoding="utf-8")
(pack_root / "TASK_HISTORY.md").write_text("# Task History\n", encoding="utf-8")
(pack_root / "RULEBOOK.jsonl").write_text("", encoding="utf-8")
(pack_root / "META.yaml").write_text(
    'id: "v1613-topology-probe"\n'
    'title: "v1613 topology probe"\n'
    'description: "legacy probe pack"\n'
    'status: "active"\n'
    'profile: "runtime"\n'
    'runtime_mode: "local_only"\n',
    encoding="utf-8",
)
(pack_root / "agents").mkdir(parents=True, exist_ok=True)
(pack_root / "agents" / "identity.yaml").write_text(
    _default_identity_agent_yaml(identity_id, "v1613 topology probe", "legacy probe pack"),
    encoding="utf-8",
)
(pack_root / "CURRENT_TASK.json").write_text(
    json.dumps(
        {
            "identity_id": identity_id,
            "identity_update_lifecycle_contract": {
                "validation_contract": {
                    "required_checks": [],
                }
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
catalog_path.write_text(
    yaml.safe_dump(
        {
            "identities": [
                {
                    "id": identity_id,
                    "pack_path": str(pack_root),
                    "status": "active",
                    "profile": "runtime",
                    "runtime_mode": "local_only",
                }
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    ),
    encoding="utf-8",
)
PY

python3 "$ROOT/scripts/repair_contract_backfill.py" \
  --catalog "$LEGACY_CATALOG" \
  --identity-id "v1613-topology-probe" \
  --apply \
  --json-only > "$BACKFILL_JSON"

python3 "$ROOT/scripts/validate_identity_instance_pack_topology.py" \
  --catalog "$LEGACY_CATALOG" \
  --identity-id "v1613-topology-probe" \
  --json-only > "$POSITIVE_JSON"

cp -R "$LEGACY_ROOT" "$TMP_ROOT/neg-runtime-pack"
mkdir -p "$TMP_ROOT/neg-runtime-pack/runtime/scripts"
if python3 "$ROOT/scripts/validate_identity_instance_pack_topology.py" \
  --identity-id "v1613-topology-probe" \
  --current-task "$TMP_ROOT/neg-runtime-pack/CURRENT_TASK.json" \
  --json-only > "$NEG_RUNTIME_JSON"; then
  echo "[FAIL] runtime/scripts negative probe unexpectedly passed"
  exit 1
fi

cp -R "$LEGACY_ROOT" "$TMP_ROOT/neg-cache-pack"
mkdir -p "$TMP_ROOT/neg-cache-pack/scripts/__pycache__"
if python3 "$ROOT/scripts/validate_identity_instance_pack_topology.py" \
  --identity-id "v1613-topology-probe" \
  --current-task "$TMP_ROOT/neg-cache-pack/CURRENT_TASK.json" \
  --json-only > "$NEG_CACHE_JSON"; then
  echo "[FAIL] __pycache__ negative probe unexpectedly passed"
  exit 1
fi

cp -R "$LEGACY_ROOT" "$TMP_ROOT/neg-readme-pack"
rm -f "$TMP_ROOT/neg-readme-pack/scripts/README.md"
if python3 "$ROOT/scripts/validate_identity_instance_pack_topology.py" \
  --identity-id "v1613-topology-probe" \
  --current-task "$TMP_ROOT/neg-readme-pack/CURRENT_TASK.json" \
  --json-only > "$NEG_README_JSON"; then
  echo "[FAIL] missing scripts/README negative probe unexpectedly passed"
  exit 1
fi

python3 - "$BACKFILL_JSON" "$POSITIVE_JSON" "$NEG_RUNTIME_JSON" "$NEG_CACHE_JSON" "$NEG_README_JSON" <<'PY'
import json
import sys

backfill, positive, neg_runtime, neg_cache, neg_readme = [
    json.loads(open(path, encoding="utf-8").read()) for path in sys.argv[1:]
]

assert backfill["contract_backfill_status"] == "PASS_REQUIRED", backfill
assert backfill["instance_pack_topology_contract_auto_wire_status"] == "PASS_REQUIRED", backfill
assert "instance_pack_topology_contract_v1" in (backfill.get("restored_topology_contract_keys") or []), backfill
assert backfill["topology_assets_backfill"]["status"] == "PASS_REQUIRED", backfill
assert backfill["topology_assets_backfill"]["applied"] is True, backfill

assert positive["instance_pack_topology_status"] == "PASS_REQUIRED", positive
assert positive["pack_root_dir_lock_status"] == "PASS_REQUIRED", positive
assert positive["runtime_dir_lock_status"] == "PASS_REQUIRED", positive
assert positive["scripts_surface_status"] == "PASS_REQUIRED", positive

assert neg_runtime["instance_pack_topology_status"] == "FAIL_REQUIRED", neg_runtime
assert "runtime_scripts_forbidden_present" in (neg_runtime.get("forbidden_dir_rows") or []), neg_runtime

assert neg_cache["instance_pack_topology_status"] == "FAIL_REQUIRED", neg_cache
assert "forbidden_dir:scripts/__pycache__" in (neg_cache.get("forbidden_dir_rows") or []), neg_cache

assert neg_readme["instance_pack_topology_status"] == "FAIL_REQUIRED", neg_readme
assert "scripts/README.md" in (neg_readme.get("missing_required_file_rows") or []), neg_readme

print(
    json.dumps(
        {
            "identity_instance_pack_topology_probe_status": "PASS_REQUIRED",
            "backfill_status": backfill["contract_backfill_status"],
            "topology_auto_wire_status": backfill["instance_pack_topology_contract_auto_wire_status"],
            "topology_assets_backfill_status": backfill["topology_assets_backfill"]["status"],
            "positive_topology_status": positive["instance_pack_topology_status"],
            "negative_runtime_failure": "runtime_scripts_forbidden_present",
            "negative_cache_failure": "forbidden_dir:scripts/__pycache__",
            "negative_readme_failure": "missing_required_file:scripts/README.md",
            "tmp_root": sys.argv[1].rsplit("/", 1)[0],
        },
        ensure_ascii=False,
    )
)
PY
