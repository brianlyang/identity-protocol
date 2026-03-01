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
CATALOG_PARENT="$(python3 - "$CATALOG_PATH" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve().parent)
PY
)"

INSTANCE_PLANE_STATUS="NOT_STARTED"
RELEASE_PLANE_STATUS="NOT_STARTED"

echo "[1/30] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/30] validate local-instance persistence boundary"
python3 scripts/validate_identity_local_persistence.py

echo "[2.2/30] validate identity creation boundary regression"
python3 scripts/validate_identity_creation_boundary.py

echo "[2.5/30] validate identity state consistency (catalog vs META)"
python3 scripts/validate_identity_state_consistency.py --catalog "$CATALOG_PATH"

echo "[2.55/30] validate session pointer consistency (catalog-scoped canonical + legacy mirror)"
python3 scripts/validate_identity_session_pointer_consistency.py --catalog "$CATALOG_PATH"

echo "[3/30] validate governance snapshot index"
python3 scripts/validate_audit_snapshot_index.py

echo "[3.2/30] validate protocol SSOT source boundary"
python3 scripts/validate_protocol_ssot_source.py

echo "[4/30] validate changelog freshness linkage"
python3 scripts/validate_changelog_updated.py

echo "[4.2/30] validate protocol handoff coupling (core changes require handoff update)"
python3 scripts/validate_protocol_handoff_coupling.py --base HEAD~1 --head HEAD

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

echo "[10.15/30] validate runtime mode/catalog binding guard (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_identity_runtime_mode_guard.py --identity-id "$ID" --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --expect-mode auto
done

echo "[10.16/30] validate identity_home/catalog alignment gate (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_identity_home_catalog_alignment.py --identity-id "$ID" --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-home "$CATALOG_PARENT"
done

echo "[10.17/30] validate fixture/runtime boundary gate (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_fixture_runtime_boundary.py --identity-id "$ID" --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --operation e2e
done

echo "[10.18/30] validate actor-scoped session isolation gates (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_actor_session_binding.py --identity-id "$ID" --catalog "$CATALOG_PATH" --operation e2e
  python3 scripts/validate_no_implicit_switch.py --identity-id "$ID" --catalog "$CATALOG_PATH" --operation e2e
  python3 scripts/validate_cross_actor_isolation.py --identity-id "$ID" --catalog "$CATALOG_PATH" --operation e2e
done

echo "[10.19/30] validate anytime session refresh status contract (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_identity_session_refresh_status.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --operation e2e \
    --baseline-policy strict
done

if [[ "$CATALOG_PATH" == "$HOME/.codex/identity/"* ]]; then
  echo "[10.2/30] preflight writeability probe for global runtime targets"
  if ! python3 - "$CATALOG_PATH" "$IDS" <<'PY'
import os
import sys
from pathlib import Path
import yaml

catalog = Path(sys.argv[1]).expanduser().resolve()
ids = [x.strip() for x in sys.argv[2].split() if x.strip()]
doc = yaml.safe_load(catalog.read_text(encoding="utf-8")) or {}
rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
lookup = {str(x.get("id", "")).strip(): x for x in rows}
errs = []
for iid in ids:
    row = lookup.get(iid)
    if not row:
        errs.append(f"{iid}:missing_in_catalog")
        continue
    pack = Path(str(row.get("pack_path", "")).strip()).expanduser().resolve()
    probe = pack / "runtime" / ".e2e-write-probe"
    try:
        probe.mkdir(parents=True, exist_ok=False)
        probe.rmdir()
    except Exception as exc:
        errs.append(f"{iid}:{exc}")
if errs:
    print("[FAIL] global runtime writeability preflight failed:")
    for e in errs:
        print(f"  - {e}")
    sys.exit(1)
print("[OK] global runtime writeability preflight passed")
PY
  then
    echo "[FAIL] global catalog preflight blocked in current execution context."
    echo "       recommendation: switch to project mode before e2e:"
    echo "       source ./scripts/identity_runtime_select.sh project"
    exit 1
  fi
fi
echo "[2.45/30] repair historical rulebook schema debt (identity-scoped, safe backfill)"
for ID in $IDS; do
  python3 scripts/repair_rulebook_schema_backfill.py --catalog "$CATALOG_PATH" --identity-id "$ID" --apply
done
echo "[2.4/30] validate identity scope resolution/isolation/persistence + health (for each target identity)"
for ID in $IDS; do
  python3 scripts/validate_identity_scope_resolution.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/validate_identity_scope_isolation.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/validate_identity_scope_persistence.py --catalog "$CATALOG_PATH" --identity-id "$ID"
  python3 scripts/collect_identity_health_report.py --identity-id "$ID" --catalog "$CATALOG_PATH" --out-dir /tmp/identity-health-reports --enforce-pass
  python3 scripts/validate_identity_health_contract.py --identity-id "$ID" --report-dir /tmp/identity-health-reports --require-pass
done

echo "[7/30] compile runtime brief (for each target identity)"
COMPILED_TMP_DIR="/tmp/identity-compiled-runtime"
mkdir -p "$COMPILED_TMP_DIR"
for ID in $IDS; do
  python3 scripts/compile_identity_runtime.py --catalog "$CATALOG_PATH" --identity-id "$ID" --output "${COMPILED_TMP_DIR}/${ID}.md"
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

  STAMP_JSON="/tmp/identity-response-stamp-${ID}.json"
  STAMP_BLOCKER_RECEIPT="/tmp/identity-stamp-blocker-receipt-${ID}.json"
  REPLY_FIRST_LINE_BLOCKER_RECEIPT="/tmp/identity-reply-first-line-blocker-receipt-${ID}.json"

  echo "[12.2/30][$ID] render dynamic response identity stamp"
  python3 scripts/render_identity_response_stamp.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --view external --out "$STAMP_JSON" --json-only

  echo "[12.3/30][$ID] validate response identity stamp hard gate (user-visible channel)"
  python3 scripts/validate_identity_response_stamp.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --stamp-json "$STAMP_JSON" --force-check --enforce-user-visible-gate --operation e2e --blocker-receipt-out "$STAMP_BLOCKER_RECEIPT"

  echo "[12.4/30][$ID] validate response stamp blocker receipt schema"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --force-check --receipt "$STAMP_BLOCKER_RECEIPT"

  echo "[12.45/30][$ID] validate reply first-line Identity-Context hard gate (HOTFIX-P0-004)"
  python3 scripts/validate_reply_identity_context_first_line.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --stamp-json "$STAMP_JSON" --force-check --enforce-first-line-gate --operation e2e --blocker-receipt-out "$REPLY_FIRST_LINE_BLOCKER_RECEIPT"

  echo "[12.46/30][$ID] validate reply first-line blocker receipt schema"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --force-check --receipt "$REPLY_FIRST_LINE_BLOCKER_RECEIPT"

  echo "[12.5/30][$ID] validate identity prompt quality"
  # scope is resolved from bound catalog/runtime context; avoid hard-coded scope injection drift.
  python3 scripts/validate_identity_prompt_quality.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[13/30][$ID] validate update prereq baseline gate"
  python3 scripts/validate_identity_upgrade_prereq.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[14/30][$ID] validate update lifecycle contract"
  python3 scripts/validate_identity_update_lifecycle.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[15/30][$ID] validate trigger regression contract"
  python3 scripts/validate_identity_trigger_regression.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[16/30][$ID] validate collaboration trigger contract"
  python3 scripts/validate_identity_collab_trigger.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[16.5/30][$ID] bootstrap identity-scoped learning sample if missing"
  python3 scripts/repair_identity_learning_sample.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[17/30][$ID] validate learning-loop linkage"
  python3 scripts/validate_identity_learning_loop.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[18/30][$ID] validate master/sub handoff contract"
  python3 scripts/validate_agent_handoff_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[19/30][$ID] validate orchestration contract"
  python3 scripts/validate_identity_orchestration_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[19.5/30][$ID] probe capability activation (skill/mcp/tool attachment)"
  python3 scripts/validate_identity_capability_activation.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID"

  echo "[19.6/30][$ID] validate dialogue synthesis governance (optional contract)"
  python3 scripts/validate_identity_dialogue_content.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[19.7/30][$ID] validate dialogue cross-validation governance (optional contract)"
  python3 scripts/validate_identity_dialogue_cross_validation.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[19.8/30][$ID] validate dialogue result-support governance (optional contract)"
  python3 scripts/validate_identity_dialogue_result_support.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[20/30][$ID] validate knowledge contract (self-test)"
  python3 scripts/validate_identity_knowledge_contract.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[21/30][$ID] validate experience feedback contract (self-test)"
  python3 scripts/validate_identity_experience_feedback.py --catalog "$CATALOG_PATH" --identity-id "$ID" --self-test

  echo "[22/30][$ID] validate install safety contract"
  python3 scripts/validate_identity_install_safety.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23/30][$ID] validate install provenance contract"
  python3 scripts/validate_identity_install_provenance.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23.2/30][$ID] validate tool installation closure contract (contract-first)"
  python3 scripts/validate_identity_tool_installation.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23.3/30][$ID] validate vendor/api discovery closure contract (contract-first)"
  python3 scripts/validate_identity_vendor_api_discovery.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23.4/30][$ID] validate vendor/api solution closure contract (contract-first)"
  python3 scripts/validate_identity_vendor_api_solution.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[23.42/30][$ID] validate semantic routing guard contract (Track-B)"
  python3 scripts/validate_semantic_routing_guard.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.423/30][$ID] validate instance/protocol split receipt contract (ASB-RQ-055..058)"
  python3 scripts/validate_instance_protocol_split_receipt.py --catalog "$CATALOG_PATH" --repo-catalog identity/catalog/identities.yaml --identity-id "$ID" --operation e2e --json-only

  echo "[23.425/30][$ID] validate protocol-vendor semantic isolation contract (P0-D)"
  python3 scripts/validate_protocol_vendor_semantic_isolation.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.428/30][$ID] validate external source trust-chain contract (P0-E)"
  python3 scripts/validate_external_source_trust_chain.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.429/30][$ID] validate protocol data sanitization boundary contract (P0-F)"
  python3 scripts/validate_protocol_data_sanitization_boundary.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4295/30][$ID] trigger platform optimization discovery (P1-D non-blocking)"
  python3 scripts/trigger_platform_optimization_discovery.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4297/30][$ID] build vibe-coding feeding pack (P1-E non-blocking)"
  python3 scripts/build_vibe_coding_feeding_pack.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e --out-root /tmp/vibe-coding-feeding-packs

  echo "[23.4298/30][$ID] validate capability-fit optimization matrix contract (P1-F)"
  python3 scripts/validate_identity_capability_fit_optimization.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4299/30][$ID] validate compose-before-discover gate (P1-F)"
  python3 scripts/validate_capability_composition_before_discovery.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.430/30][$ID] validate capability-fit review freshness visibility (P1-F)"
  python3 scripts/validate_capability_fit_review_freshness.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4301/30][$ID] validate capability-fit roundtable evidence mapping (P1-G)"
  python3 scripts/validate_capability_fit_roundtable_evidence.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4302/30][$ID] trigger capability-fit review (P1-H non-blocking)"
  python3 scripts/trigger_capability_fit_review.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.4303/30][$ID] build capability-fit matrix artifact (P1-H non-blocking)"
  python3 scripts/build_capability_fit_matrix.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e --out-root /tmp/capability-fit-matrices

  echo "[23.43/30][$ID] validate vendor namespace separation contract (Track-B)"
  python3 scripts/validate_vendor_namespace_separation.py --catalog "$CATALOG_PATH" --identity-id "$ID" --operation e2e

  echo "[23.45/30][$ID] summarize required-contract coverage semantics (PASS_REQUIRED/SKIPPED_NOT_REQUIRED)"
  python3 scripts/validate_required_contract_coverage.py \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --identity-id "$ID" \
    --operation e2e

  echo "[24/30][$ID] validate experience feedback governance"
  python3 scripts/validate_identity_experience_feedback_governance.py --catalog "$CATALOG_PATH" --identity-id "$ID"

  echo "[25/30][$ID] enforce self-upgrade evidence for identity-core edits"
  BASE_SHA="$(git rev-parse HEAD~1)"
  HEAD_SHA="$(git rev-parse HEAD)"
  python3 scripts/validate_identity_self_upgrade_enforcement.py --catalog "$CATALOG_PATH" --identity-id "$ID" --base "$BASE_SHA" --head "$HEAD_SHA"

  echo "[26/30][$ID] execute identity upgrade cycle via identity-creator (review-required)"
  set +e
  CI=true python3 scripts/identity_creator.py update --catalog "$CATALOG_PATH" --identity-id "$ID" --mode review-required
  UPDATE_RC=$?
  set -e
  UPGRADE_REPORT=$(python3 - "$ID" "$CATALOG_PATH" "${IDENTITY_HOME:-}" <<'PY'
import glob,os,sys
from pathlib import Path
import yaml

identity_id=sys.argv[1]
catalog_path=Path(sys.argv[2]).expanduser().resolve()
identity_home=sys.argv[3].strip()

roots=[]
if catalog_path.exists():
    try:
        doc=yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
        rows=[x for x in (doc.get("identities") or []) if isinstance(x, dict)]
        row=next((x for x in rows if str(x.get("id","")).strip()==identity_id), None)
        if row:
            pack=Path(str((row or {}).get("pack_path","")).strip()).expanduser().resolve()
            if pack.exists():
                roots.append(str(pack / "runtime" / "reports"))
                roots.append(str(pack / "runtime"))
    except Exception:
        pass
roots.extend(["/tmp/identity-upgrade-reports","/tmp/identity-runtime"])
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
  echo "[26.15/30][$ID] validate execution report freshness/binding preflight"
  python3 scripts/validate_execution_report_freshness.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --report "$UPGRADE_REPORT" \
    --execution-report-policy strict

  echo "[26.2/30][$ID] validate protocol baseline freshness (strict)"
  python3 scripts/validate_identity_protocol_baseline_freshness.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --execution-report "$UPGRADE_REPORT" \
    --baseline-policy strict

  echo "[26.22/30][$ID] validate protocol version alignment tuple (strict)"
  python3 scripts/validate_identity_protocol_version_alignment.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --execution-report "$UPGRADE_REPORT" \
    --operation e2e \
    --alignment-policy strict \
    --json-only

  echo "[26.25/30][$ID] validate writeback continuity contract (Track-A)"
  python3 scripts/validate_writeback_continuity.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --report "$UPGRADE_REPORT" \
    --operation e2e

  echo "[26.3/30][$ID] validate post-execution mandatory contract (Track-A)"
  python3 scripts/validate_post_execution_mandatory.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --report "$UPGRADE_REPORT" \
    --operation e2e

  echo "[26.35/30][$ID] validate protocol-feedback sidecar escalation contract (A/B coexistence)"
  python3 scripts/validate_protocol_feedback_sidecar_contract.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --report "$UPGRADE_REPORT" \
    --operation e2e \
    --enforce-blocking

  echo "[26.36/30][$ID] validate instance/base-repo write boundary gate (HOTFIX-P0-005)"
  python3 scripts/validate_instance_base_repo_write_boundary.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --report "$UPGRADE_REPORT" \
    --operation e2e

  echo "[26.37/30][$ID] validate protocol-feedback SSOT archival gate (HOTFIX-P0-006)"
  python3 scripts/validate_protocol_feedback_ssot_archival.py \
    --identity-id "$ID" \
    --catalog "$CATALOG_PATH" \
    --repo-catalog identity/catalog/identities.yaml \
    --operation e2e

  UPG_META_LINE=$(python3 - "$UPGRADE_REPORT" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p))
ew=d.get("experience_writeback") or {}
mandatory = all(
    k in d for k in ("permission_state","writeback_status","next_action","skills_used","mcp_tools_used","tool_calls_used","capability_activation_status","capability_activation_error_code")
) and isinstance(ew, dict) and ("status" in ew) and ("error_code" in ew)
vals = [
    str(bool(d.get("all_ok", False))).lower(),
    str(d.get("writeback_status","")) or "__EMPTY__",
    str(d.get("permission_state","")) or "__EMPTY__",
    str(d.get("next_action","")) or "__EMPTY__",
    str(ew.get("error_code","") or d.get("permission_error_code","")) or "__EMPTY__",
    str(d.get("capability_activation_status","")) or "__EMPTY__",
    str(d.get("capability_activation_error_code","")) or "__EMPTY__",
    str(bool(mandatory)).lower(),
]
print("\t".join(vals))
PY
)
  IFS=$'\t' read -r UPG_ALL_OK UPG_WB_STATUS UPG_PERMISSION UPG_NEXT_ACTION UPG_ERR_CODE UPG_CAP_STATUS UPG_CAP_ERR_CODE UPG_MANDATORY_OK <<<"$UPG_META_LINE"
  [ "${UPG_WB_STATUS}" = "__EMPTY__" ] && UPG_WB_STATUS=""
  [ "${UPG_PERMISSION}" = "__EMPTY__" ] && UPG_PERMISSION=""
  [ "${UPG_NEXT_ACTION}" = "__EMPTY__" ] && UPG_NEXT_ACTION=""
  [ "${UPG_ERR_CODE}" = "__EMPTY__" ] && UPG_ERR_CODE=""
  [ "${UPG_CAP_STATUS}" = "__EMPTY__" ] && UPG_CAP_STATUS=""
  [ "${UPG_CAP_ERR_CODE}" = "__EMPTY__" ] && UPG_CAP_ERR_CODE=""
  echo "[26.1/30][$ID] update report summary: rc=${UPDATE_RC} all_ok=${UPG_ALL_OK} writeback=${UPG_WB_STATUS} permission=${UPG_PERMISSION} capability=${UPG_CAP_STATUS} next_action=${UPG_NEXT_ACTION} error_code=${UPG_ERR_CODE} capability_error=${UPG_CAP_ERR_CODE}"
  if [ "$UPG_MANDATORY_OK" != "true" ]; then
    echo "[FAIL] update report missing mandatory fields for recoverable flow semantics"
    exit 1
  fi
  python3 scripts/validate_identity_self_upgrade_enforcement.py --catalog "$CATALOG_PATH" --identity-id "$ID" --execution-report "$UPGRADE_REPORT"

  echo "[27/30][$ID] validate experience writeback linkage"
  python3 scripts/validate_identity_experience_writeback.py --repo-catalog identity/catalog/identities.yaml --local-catalog "$CATALOG_PATH" --identity-id "$ID" --execution-report "$UPGRADE_REPORT"

  echo "[27.5/30][$ID] validate permission-state contract"
  # Instance-plane fail-operational semantics:
  # - review-required with all_ok=false is acceptable only for recoverable (non-hard-boundary) flow,
  #   with complete report fields and executable next_action.
  HARD_BOUNDARY="false"
  case "${UPG_ERR_CODE}" in
    IP-PATH-*|IP-PERM-*)
      HARD_BOUNDARY="true"
      ;;
  esac
  if [ "${UPG_ALL_OK}" = "true" ] && [ "${UPG_WB_STATUS}" = "WRITTEN" ] && [ "${UPG_PERMISSION}" = "WRITEBACK_WRITTEN" ]; then
    python3 scripts/validate_identity_permission_state.py --identity-id "$ID" --report "$UPGRADE_REPORT" --ci --require-written
    INSTANCE_PLANE_STATUS="CLOSED"
  else
    if [ "${HARD_BOUNDARY}" = "true" ] || [ -z "${UPG_NEXT_ACTION}" ]; then
      echo "[FAIL] hard-boundary or non-recoverable update state for $ID (error_code=${UPG_ERR_CODE}, next_action=${UPG_NEXT_ACTION})"
      exit 1
    fi
    python3 scripts/validate_identity_permission_state.py --identity-id "$ID" --report "$UPGRADE_REPORT" --ci
    echo "[INFO] review-required recoverable flow accepted for instance-plane: $ID"
    INSTANCE_PLANE_STATUS="CLOSED"
  fi

  echo "[27.6/30][$ID] validate identity binding tuple contract"
  python3 scripts/validate_identity_binding_tuple.py --identity-id "$ID" --report "$UPGRADE_REPORT"

  echo "[27.7/30][$ID] validate identity prompt activation contract"
  python3 scripts/validate_identity_prompt_activation.py --identity-id "$ID" --catalog "$CATALOG_PATH" --report "$UPGRADE_REPORT"

  echo "[27.8/30][$ID] validate identity prompt lifecycle contract"
  python3 scripts/validate_identity_prompt_lifecycle.py --identity-id "$ID" --report "$UPGRADE_REPORT"

  echo "[27.9/30][$ID] validate capability activation evidence in upgrade report"
  CAP_ARGS=(--identity-id "$ID" --report "$UPGRADE_REPORT")
  if [ "${UPG_ALL_OK}" = "true" ] && [ "${UPG_WB_STATUS}" = "WRITTEN" ] && [ "${UPG_PERMISSION}" = "WRITEBACK_WRITTEN" ]; then
    CAP_ARGS+=(--require-activated)
  fi
  python3 scripts/validate_identity_capability_activation.py "${CAP_ARGS[@]}"

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
  python3 scripts/compile_identity_runtime.py --catalog "$CATALOG_PATH" --identity-id "$ID" --output "${COMPILED_TMP_DIR}/${ID}.md" >/dev/null
  grep -q "Runtime baseline review references:" "${COMPILED_TMP_DIR}/${ID}.md"
done

echo "E2E smoke test PASSED"
echo "instance_plane_status=${INSTANCE_PLANE_STATUS}"
echo "release_plane_status=${RELEASE_PLANE_STATUS}"
