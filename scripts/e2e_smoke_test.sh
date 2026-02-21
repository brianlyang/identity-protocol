#!/usr/bin/env bash
set -euo pipefail

echo "[1/20] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/20] validate governance snapshot index"
python3 scripts/validate_audit_snapshot_index.py

echo "[3/20] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[4/20] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[5/20] test discovery contract"
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

echo "[6/20] active identities: $IDS"

for ID in $IDS; do
  echo "[7/20][$ID] validate runtime ORRLC contract"
  python3 scripts/validate_identity_runtime_contract.py --identity-id "$ID"

  echo "[8/20][$ID] validate update prereq baseline gate"
  python3 scripts/validate_identity_upgrade_prereq.py --identity-id "$ID"

  echo "[9/20][$ID] validate update lifecycle contract"
  python3 scripts/validate_identity_update_lifecycle.py --identity-id "$ID"

  echo "[10/20][$ID] validate trigger regression contract"
  python3 scripts/validate_identity_trigger_regression.py --identity-id "$ID"

  echo "[11/20][$ID] validate collaboration trigger contract"
  python3 scripts/validate_identity_collab_trigger.py --identity-id "$ID" --self-test

  echo "[12/20][$ID] validate learning-loop linkage"
  python3 scripts/validate_identity_learning_loop.py --identity-id "$ID"

  echo "[13/20][$ID] validate master/sub handoff contract"
  python3 scripts/validate_agent_handoff_contract.py --identity-id "$ID" --self-test

  echo "[14/20][$ID] validate orchestration contract"
  python3 scripts/validate_identity_orchestration_contract.py --identity-id "$ID"

  echo "[15/20][$ID] validate knowledge contract (self-test)"
  python3 scripts/validate_identity_knowledge_contract.py --identity-id "$ID" --self-test

  echo "[16/20][$ID] validate experience feedback contract (self-test)"
  python3 scripts/validate_identity_experience_feedback.py --identity-id "$ID" --self-test

  echo "[17/20][$ID] execute identity upgrade cycle (review-required)"
  python3 scripts/execute_identity_upgrade.py --identity-id "$ID" --mode review-required --out-dir /tmp/identity-upgrade-reports
  UPGRADE_REPORT=$(ls -1t /tmp/identity-upgrade-reports/identity-upgrade-exec-"$ID"-*.json | head -n 1)

  echo "[18/20][$ID] validate capability arbitration contract (self-test + upgrade linkage)"
  python3 scripts/validate_identity_capability_arbitration.py --identity-id "$ID" --self-test --upgrade-report "$UPGRADE_REPORT"

  echo "[19/20][$ID] validate CI enforcement contract"
  python3 scripts/validate_identity_ci_enforcement.py --identity-id "$ID"

  echo "[20/20][$ID] export route quality metrics"
  python3 scripts/export_route_quality_metrics.py --identity-id "$ID"
done

echo "[post] ensure compile output is stable and contains baseline refs"
python3 scripts/compile_identity_runtime.py >/dev/null
grep -q "Runtime baseline review references:" identity/runtime/IDENTITY_COMPILED.md

echo "E2E smoke test PASSED"
