#!/usr/bin/env bash
set -euo pipefail

CATALOG_PATH=${IDENTITY_CATALOG:-}
if [ -z "$CATALOG_PATH" ]; then
  echo "[FAIL] IDENTITY_CATALOG is required (implicit catalog fallback is disabled)."
  echo "       select runtime mode first:"
  echo "       source ./scripts/identity_runtime_select.sh project"
  echo "       # or"
  echo "       source ./scripts/identity_runtime_select.sh global"
  exit 1
fi
if [ ! -f "$CATALOG_PATH" ]; then
  echo "[FAIL] IDENTITY_CATALOG does not exist: $CATALOG_PATH"
  exit 1
fi

echo "[1/30] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/30] validate local-instance persistence boundary"
python3 scripts/validate_identity_local_persistence.py

echo "[2.5/30] validate identity state consistency (catalog vs META)"
python3 scripts/validate_identity_state_consistency.py --catalog "$CATALOG_PATH"

echo "[3/30] validate governance snapshot index"
python3 scripts/validate_audit_snapshot_index.py

echo "[4/30] validate changelog freshness linkage"
python3 scripts/validate_changelog_updated.py

echo "[5/30] validate release metadata synchronization"
python3 scripts/validate_release_metadata_sync.py

echo "[6/30] validate release freeze boundary"
BASE_SHA_GLOBAL="$(git rev-parse HEAD~1)"
HEAD_SHA_GLOBAL="$(git rev-parse HEAD)"
python3 scripts/validate_release_freeze_boundary.py --base "${BASE_SHA_GLOBAL}" --head "${HEAD_SHA_GLOBAL}"

echo "[6.5/30] validate release workspace cleanliness"
python3 scripts/validate_release_workspace_cleanliness.py

IDS=${IDENTITY_IDS:-}
echo "[10/30] active identities: $IDS"
echo "[10.1/30] catalog path: $CATALOG_PATH"

if [ -z "$IDS" ]; then
  echo "[FAIL] IDENTITY_IDS is required for deterministic target consistency."
  echo "       example: IDENTITY_IDS=office-ops-expert bash scripts/e2e_smoke_test.sh"
  exit 1
fi
echo "[2.4/30] validate identity scope resolution/isolation/persistence + health (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_identity_scope_resolution.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/validate_identity_scope_isolation.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/validate_identity_scope_persistence.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/collect_identity_health_report.py --identity-id "$ID" --catalog "$CATALOG_PATH" --out-dir /tmp/identity-health-reports --enforce-pass
  python3 scripts/validate_identity_health_contract.py --identity-id "$ID" --report-dir /tmp/identity-health-reports --require-pass
done

echo "[7/30] compile runtime brief (for each target identity)"
for ID in $IDS; do
  python3 scripts/compile_identity_runtime.py --catalog "$CATALOG_PATH" --identity-id "$ID"
done

echo "[8/30] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[9/30] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

for ID in $IDS; do
  echo "[10.5/32][$ID] validate identity instance isolation boundary"
  python3 scripts/validate_identity_instance_isolation.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[10.6/32][$ID] validate scope isolation boundary"
  python3 scripts/validate_identity_scope_isolation.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[10.7/32][$ID] validate scope persistence boundary"
  python3 scripts/validate_identity_scope_persistence.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[10.8/32][$ID] collect + validate health report"
  python3 scripts/collect_identity_health_report.py --identity-id "$ID" --catalog "$CATALOG_PATH" --out-dir /tmp/identity-health-reports --enforce-pass
  python3 scripts/validate_identity_health_contract.py --identity-id "$ID" --report-dir /tmp/identity-health-reports --require-pass

  echo "[11/30][$ID] validate runtime ORRLC contract"
  python3 scripts/validate_identity_runtime_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[12/30][$ID] validate role-binding contract"
  python3 scripts/validate_identity_role_binding.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[13/30][$ID] validate update prereq baseline gate"
  python3 scripts/validate_identity_upgrade_prereq.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[14/30][$ID] validate update lifecycle contract"
  python3 scripts/validate_identity_update_lifecycle.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[15/30][$ID] validate trigger regression contract"
  python3 scripts/validate_identity_trigger_regression.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[16/30][$ID] validate collaboration trigger contract"
  python3 scripts/validate_identity_collab_trigger.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[17/30][$ID] validate learning-loop linkage"
  python3 scripts/validate_identity_learning_loop.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[18/30][$ID] validate master/sub handoff contract"
  python3 scripts/validate_agent_handoff_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[19/30][$ID] validate orchestration contract"
  python3 scripts/validate_identity_orchestration_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[20/30][$ID] validate knowledge contract (self-test)"
  python3 scripts/validate_identity_knowledge_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[21/30][$ID] validate experience feedback contract (self-test)"
  python3 scripts/validate_identity_experience_feedback.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[22/30][$ID] validate install safety contract"
  python3 scripts/validate_identity_install_safety.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23/30][$ID] validate install provenance contract"
  python3 scripts/validate_identity_install_provenance.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[24/30][$ID] validate experience feedback governance"
  python3 scripts/validate_identity_experience_feedback_governance.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[25/30][$ID] enforce self-upgrade evidence for identity-core edits"
  BASE_SHA="$(git rev-parse HEAD~1)"
  HEAD_SHA="$(git rev-parse HEAD)"
  python3 scripts/validate_identity_self_upgrade_enforcement.py --catalog "$CATALOG_PATH" --identity-id "$ID" --base "$BASE_SHA" --head "$HEAD_SHA"

  echo "[26/30][$ID] execute identity upgrade cycle via identity-creator (review-required)"
  CI=true python3 scripts/identity_creator.py update --catalog "$CATALOG_PATH" --identity-id "$ID" --mode review-required
  UPGRADE_REPORT=$(python3 - "$ID" "${IDENTITY_HOME:-}" <<'PY'
import glob,os,sys
identity_id=sys.argv[1]
identity_home=sys.argv[2].strip()
roots=["/tmp/identity-upgrade-reports","/tmp/identity-runtime"]
if identity_home:
    roots.append(identity_home)
cands=[]
for r in roots:
    cands.extend(glob.glob(os.path.join(r,"**",f"identity-upgrade-exec-{identity_id}-*.json"),recursive=True))
cands=[p for p in cands if not p.endswith("-patch-plan.json")]
if not cands:
    sys.exit(1)
cands.sort(key=lambda p: os.path.getmtime(p))
print(cands[-1])
PY
)
  if [ -z "${UPGRADE_REPORT:-}" ] || [ ! -f "$UPGRADE_REPORT" ]; then
    echo "[FAIL] unable to locate latest upgrade report for $ID"
    exit 1
  fi
  python3 scripts/validate_identity_self_upgrade_enforcement.py --catalog "$CATALOG_PATH" --identity-id "$ID" --execution-report "$UPGRADE_REPORT"

  echo "[27/30][$ID] validate experience writeback linkage"
  python3 scripts/validate_identity_experience_writeback.py --catalog "$CATALOG_PATH" --identity-id "$ID" --execution-report "$UPGRADE_REPORT"

  echo "[27.5/30][$ID] validate permission-state contract"
  python3 scripts/validate_identity_permission_state.py --identity-id "$ID" --report "$UPGRADE_REPORT" --ci --require-written

  echo "[27.6/30][$ID] validate identity binding tuple contract"
  python3 scripts/validate_identity_binding_tuple.py --identity-id "$ID" --report "$UPGRADE_REPORT"

  echo "[28/30][$ID] validate capability arbitration contract (self-test + upgrade linkage)"
  python3 scripts/validate_identity_capability_arbitration.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test --upgrade-report "$UPGRADE_REPORT"

  echo "[29/30][$ID] validate CI enforcement contract"
  python3 scripts/validate_identity_ci_enforcement.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[30/32][$ID] validate protocol root evidence"
  python3 scripts/validate_identity_protocol_root_evidence.py --identity-id "$ID" --report "$UPGRADE_REPORT"

  echo "[31/32][$ID] validate mode promotion arbitration"
  python3 scripts/validate_identity_mode_promotion_arbitration.py --identity-id "$ID" --base "$BASE_SHA" --head "$HEAD_SHA" --report "$UPGRADE_REPORT"

  echo "[32/32][$ID] export route quality metrics"
  python3 scripts/export_route_quality_metrics.py --catalog "$CATALOG_PATH" --identity-id "$ID"
done

echo "[post] ensure compile output is stable and contains baseline refs"
for ID in $IDS; do
  python3 scripts/compile_identity_runtime.py --catalog "$CATALOG_PATH" --identity-id "$ID" >/dev/null
done
grep -q "Runtime baseline review references:" identity/runtime/IDENTITY_COMPILED.md

echo "E2E smoke test PASSED"
