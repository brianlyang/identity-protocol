#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TMP_ROOT="$(mktemp -d /tmp/skill-supply-chain-probes.XXXXXX)"
cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

PACK_PATH="$TMP_ROOT/identity-probe"
SKILLS_ROOT="$TMP_ROOT/skills"
RUNTIME_SKILLS_ROOT="$TMP_ROOT/runtime-skills"
CATALOG_PATH="$TMP_ROOT/catalog.local.yaml"

CATALOG_DIR="$TMP_ROOT/.identity"
CATALOG_PATH="$CATALOG_DIR/catalog.local.yaml"

mkdir -p "$PACK_PATH" "$SKILLS_ROOT/demo-skill" "$RUNTIME_SKILLS_ROOT/demo-skill" "$CATALOG_DIR"

cat > "$CATALOG_PATH" <<YAML
identities:
  - id: skill-probe
    status: active
    profile: runtime
    runtime_mode: local_only
    pack_path: $PACK_PATH
YAML

python3 - "$PACK_PATH" <<'PY'
import json
import sys
from pathlib import Path

pack = Path(sys.argv[1])
task = {
    "skill_path_integrity_contract_v1": {
        "required": True,
        "required_skills": ["demo-skill"],
        "allowed_skill_roots": ["{active_repo_root}/skills"],
    },
    "skill_frontmatter_contract_v1": {
        "required": True,
        "required_frontmatter_fields": ["skill_id", "version", "owner", "source"],
    },
    "skill_sync_drift_guard_contract_v1": {
        "required": True,
        "sync_roots": [
            "{active_repo_root}/skills",
            "{active_repo_root}/runtime-skills"
        ],
        "allow_missing_skills": False,
    },
    "skill_installation_supply_chain_contract_v1": {
        "required": True,
        "dependent_contract_keys": [
            "tool_installation_contract",
            "vendor_api_discovery_contract",
            "vendor_api_solution_contract",
            "skill_path_integrity_contract_v1",
        ],
        "required_capability_drivers": [
            "scripts/validate_identity_tool_installation.py",
            "scripts/validate_identity_vendor_api_discovery.py",
            "scripts/validate_identity_vendor_api_solution.py",
        ],
    },
    "tool_installation_contract": {"required": False},
    "vendor_api_discovery_contract": {"required": False},
    "vendor_api_solution_contract": {"required": False},
    "required_validators": [
        "scripts/validate_identity_tool_installation.py",
        "scripts/validate_identity_vendor_api_discovery.py",
        "scripts/validate_identity_vendor_api_solution.py",
    ],
}
(pack / "CURRENT_TASK.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(pack / "IDENTITY_PROMPT.md").write_text("# skill probe\n", encoding="utf-8")
PY

cat > "$SKILLS_ROOT/demo-skill/SKILL.md" <<'MD'
# Demo Skill
missing frontmatter
MD

set +e
python3 scripts/validate_skill_frontmatter.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/frontmatter_fail.json"
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  echo "[FAIL] expected frontmatter missing to fail"
  exit 1
fi
python3 - "$TMP_ROOT/frontmatter_fail.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SFRONT-001", obj
print("[PASS] probe frontmatter_missing_blocked")
PY

cat > "$SKILLS_ROOT/demo-skill/SKILL.md" <<'MD'
---
skill_id: demo-skill
version: 1.0.0
owner: protocol
source: internal
---
# Demo Skill
ready
MD

python3 scripts/validate_skill_frontmatter.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/frontmatter_pass.json"
python3 - "$TMP_ROOT/frontmatter_pass.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("skill_frontmatter_status") == "PASS_REQUIRED", obj
print("[PASS] probe frontmatter_pass")
PY

cat > "$RUNTIME_SKILLS_ROOT/demo-skill/SKILL.md" <<'MD'
---
skill_id: demo-skill
version: 1.0.1
owner: protocol
source: runtime-copy
---
# Demo Skill drift
MD

set +e
python3 scripts/validate_skill_sync_drift_guard.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/drift_fail.json"
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  echo "[FAIL] expected skill drift to fail"
  exit 1
fi
python3 - "$TMP_ROOT/drift_fail.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SDRIFT-001", obj
print("[PASS] probe drift_detected_blocked")
PY

cp "$SKILLS_ROOT/demo-skill/SKILL.md" "$RUNTIME_SKILLS_ROOT/demo-skill/SKILL.md"
python3 scripts/validate_skill_sync_drift_guard.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/drift_pass.json"
python3 - "$TMP_ROOT/drift_pass.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("skill_sync_drift_guard_status") == "PASS_REQUIRED", obj
print("[PASS] probe drift_pass")
PY

python3 - "$PACK_PATH/CURRENT_TASK.json" <<'PY'
import json,sys
path=sys.argv[1]
obj=json.load(open(path))
obj.pop("vendor_api_solution_contract",None)
json.dump(obj,open(path,'w'),ensure_ascii=False,indent=2)
open(path,'a').write('\n')
PY

set +e
python3 scripts/validate_skill_installation_supply_chain.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/supply_chain_fail.json"
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  echo "[FAIL] expected supply-chain dependent contract probe to fail"
  exit 1
fi
python3 - "$TMP_ROOT/supply_chain_fail.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("error_code") == "IP-SSUP-001", obj
print("[PASS] probe supply_chain_dependency_blocked")
PY

python3 - "$PACK_PATH/CURRENT_TASK.json" <<'PY'
import json,sys
path=sys.argv[1]
obj=json.load(open(path))
obj["vendor_api_solution_contract"]={"required":False}
json.dump(obj,open(path,'w'),ensure_ascii=False,indent=2)
open(path,'a').write('\n')
PY

python3 scripts/validate_skill_installation_supply_chain.py \
  --catalog "$CATALOG_PATH" \
  --identity-id skill-probe \
  --operation validate \
  --force-required \
  --json-only > "$TMP_ROOT/supply_chain_pass.json"
python3 - "$TMP_ROOT/supply_chain_pass.json" <<'PY'
import json,sys
obj=json.load(open(sys.argv[1]))
assert obj.get("skill_installation_supply_chain_status") == "PASS_REQUIRED", obj
print("[PASS] probe supply_chain_pass")
PY

echo "[PASS] run_skill_supply_chain_probes_ci.sh complete"
