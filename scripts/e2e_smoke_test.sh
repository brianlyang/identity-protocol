#!/usr/bin/env bash
set -euo pipefail

echo "[1/28] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/28] validate governance snapshot index"
python3 scripts/validate_audit_snapshot_index.py

echo "[3/28] validate changelog freshness linkage"
python3 scripts/validate_changelog_updated.py

echo "[4/28] validate release metadata synchronization"
python3 scripts/validate_release_metadata_sync.py

echo "[5/28] validate release freeze boundary"
BASE_SHA_GLOBAL="$(git rev-parse HEAD~1)"
HEAD_SHA_GLOBAL="$(git rev-parse HEAD)"
python3 scripts/validate_release_freeze_boundary.py --base "${BASE_SHA_GLOBAL}" --head "${HEAD_SHA_GLOBAL}"

IDS=${IDENTITY_IDS:-}
if [ -z "$IDS" ]; then
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
fi

echo "[9/28] active identities: $IDS"

if [ -z "$IDS" ]; then
  echo "[FAIL] no active/default identities resolved. set IDENTITY_IDS explicitly (e.g. IDENTITY_IDS=store-manager)."
  exit 1
fi

PRIMARY_ID="$(printf '%s\n' "$IDS" | awk '{print $1}')"

echo "[6/28] compile runtime brief"
python3 scripts/compile_identity_runtime.py --identity-id "$PRIMARY_ID"

echo "[7/28] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[8/28] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

for ID in $IDS; do
  echo "[10/28][$ID] validate runtime ORRLC contract"
  python3 scripts/validate_identity_runtime_contract.py --identity-id "$ID"

  echo "[11/28][$ID] validate role-binding contract"
  python3 scripts/validate_identity_role_binding.py --identity-id "$ID"

  echo "[12/28][$ID] validate update prereq baseline gate"
  python3 scripts/validate_identity_upgrade_prereq.py --identity-id "$ID"

  echo "[13/28][$ID] validate update lifecycle contract"
  python3 scripts/validate_identity_update_lifecycle.py --identity-id "$ID"

  echo "[14/28][$ID] validate trigger regression contract"
  python3 scripts/validate_identity_trigger_regression.py --identity-id "$ID"

  echo "[15/28][$ID] validate collaboration trigger contract"
  python3 scripts/validate_identity_collab_trigger.py --identity-id "$ID" --self-test

  echo "[16/28][$ID] validate learning-loop linkage"
  python3 scripts/validate_identity_learning_loop.py --identity-id "$ID"

  echo "[17/28][$ID] validate master/sub handoff contract"
  python3 scripts/validate_agent_handoff_contract.py --identity-id "$ID" --self-test

  echo "[18/28][$ID] validate orchestration contract"
  python3 scripts/validate_identity_orchestration_contract.py --identity-id "$ID"

  echo "[19/28][$ID] validate knowledge contract (self-test)"
  python3 scripts/validate_identity_knowledge_contract.py --identity-id "$ID" --self-test

  echo "[20/28][$ID] validate experience feedback contract (self-test)"
  python3 scripts/validate_identity_experience_feedback.py --identity-id "$ID" --self-test

  echo "[21/28][$ID] validate install safety contract"
  python3 scripts/validate_identity_install_safety.py --identity-id "$ID"

  echo "[22/28][$ID] validate install provenance contract"
  python3 scripts/validate_identity_install_provenance.py --identity-id "$ID"

  echo "[23/28][$ID] validate experience feedback governance"
  python3 scripts/validate_identity_experience_feedback_governance.py --identity-id "$ID"

  echo "[24/28][$ID] enforce self-upgrade evidence for identity-core edits"
  BASE_SHA="$(git rev-parse HEAD~1)"
  HEAD_SHA="$(git rev-parse HEAD)"
  python3 scripts/validate_identity_self_upgrade_enforcement.py --identity-id "$ID" --base "$BASE_SHA" --head "$HEAD_SHA"

  echo "[25/28][$ID] execute identity upgrade cycle via identity-creator (review-required)"
  CI=true python3 scripts/identity_creator.py update --identity-id "$ID" --mode review-required --out-dir /tmp/identity-upgrade-reports
  UPGRADE_REPORT=$(ls -1t /tmp/identity-upgrade-reports/identity-upgrade-exec-"$ID"-*.json | head -n 1)
  python3 scripts/validate_identity_self_upgrade_enforcement.py --identity-id "$ID" --execution-report "$UPGRADE_REPORT"

  echo "[26/28][$ID] validate capability arbitration contract (self-test + upgrade linkage)"
  python3 scripts/validate_identity_capability_arbitration.py --identity-id "$ID" --self-test --upgrade-report "$UPGRADE_REPORT"

  echo "[27/28][$ID] validate CI enforcement contract"
  python3 scripts/validate_identity_ci_enforcement.py --identity-id "$ID"

  echo "[28/28][$ID] export route quality metrics"
  python3 scripts/export_route_quality_metrics.py --identity-id "$ID"
done

echo "[post] ensure compile output is stable and contains baseline refs"
python3 scripts/compile_identity_runtime.py --identity-id "$PRIMARY_ID" >/dev/null
grep -q "Runtime baseline review references:" identity/runtime/IDENTITY_COMPILED.md

echo "E2E smoke test PASSED"
