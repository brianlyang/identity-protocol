#!/usr/bin/env bash
set -euo pipefail

echo "[1/11] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/11] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[3/11] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[4/11] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

IDS=$(python3 - <<'PY'
import yaml
from pathlib import Path
c=yaml.safe_load(Path('identity/catalog/identities.yaml').read_text())
ids=[x['id'] for x in c.get('identities',[]) if isinstance(x,dict) and str(x.get('status','')).lower()=='active']
if not ids:
    d=c.get('default_identity')
    if d:
        ids=[d]
print(' '.join(ids))
PY
)

echo "[5/11] active identities: $IDS"

for ID in $IDS; do
  echo "[6/11][$ID] validate runtime ORRL contract"
  python3 scripts/validate_identity_runtime_contract.py --identity-id "$ID"

  echo "[7/11][$ID] validate update prereq baseline gate"
  python3 scripts/validate_identity_upgrade_prereq.py --identity-id "$ID"

  echo "[8/11][$ID] validate update lifecycle contract"
  python3 scripts/validate_identity_update_lifecycle.py --identity-id "$ID"

  echo "[9/11][$ID] validate trigger regression contract"
  python3 scripts/validate_identity_trigger_regression.py --identity-id "$ID"

  echo "[10/11][$ID] validate learning-loop linkage"
  python3 scripts/validate_identity_learning_loop.py --identity-id "$ID"
done

echo "[11/11] ensure compile output is stable and contains baseline refs"
python3 scripts/compile_identity_runtime.py >/dev/null
grep -q "Runtime baseline review references:" identity/runtime/IDENTITY_COMPILED.md

echo "E2E smoke test PASSED"
