#!/usr/bin/env bash
set -euo pipefail

IDS="${1:-${IDS:-}}"
BASE_SHA="${2:-${BASE_SHA:-$(git rev-parse HEAD~1)}}"
HEAD_SHA="${3:-${HEAD_SHA:-$(git rev-parse HEAD)}}"

if [ -z "${IDS}" ]; then
  echo "[FAIL] IDS is empty"
  exit 1
fi

CATALOG_PATH="${CATALOG_PATH:-identity/catalog/identities.yaml}"
REPO_CATALOG_PATH="${REPO_CATALOG_PATH:-identity/catalog/identities.yaml}"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-$PWD}/.tmp-runtime}}"
mkdir -p "${TMP_ROOT_BASE}"
CATALOG_PARENT="$(dirname "$(realpath "${CATALOG_PATH}")")"

HEADSTAMP_ACTOR_ID="${HEADSTAMP_ACTOR_ID:-${CODEX_ACTOR_ID:-assistant:codex}}"
HEADSTAMP_SESSION_ID="${HEADSTAMP_SESSION_ID:-run:${GITHUB_RUN_ID:-ci-local}}"

python3 scripts/validate_required_gate_surface_drift.py --json-only

echo "target identities: ${IDS}"
for ID in ${IDS}; do
  TMP_ROOT="${TMP_ROOT_BASE}"
  mkdir -p "${TMP_ROOT}"
  RUNTIME_TMP_ROOT="${TMP_ROOT}/identity-runtime"
  STAMP_JSON="${TMP_ROOT}/identity-response-stamp-${ID}.json"
  STAMP_BLOCKER_RECEIPT="${TMP_ROOT}/identity-stamp-blocker-receipt-${ID}.json"
  FIRST_LINE_BLOCKER_RECEIPT="${TMP_ROOT}/identity-reply-first-line-blocker-receipt-${ID}.json"
  SEND_TIME_BLOCKER_RECEIPT="${TMP_ROOT}/identity-send-time-reply-gate-blocker-receipt-${ID}.json"
  COHERENCE_BLOCKER_RECEIPT="${TMP_ROOT}/identity-execution-reply-coherence-blocker-receipt-${ID}.json"
  BUNDLE_RUN_TOKEN="${GITHUB_RUN_ID:-ci-local}"
  REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE="${TMP_ROOT}/required-gate-bundle-validate-${ID}-${BUNDLE_RUN_TOKEN}.json"
  REQUIRED_GATE_BUNDLE_RECEIPT_THREE_PLANE="${TMP_ROOT}/required-gate-bundle-three-plane-${ID}-${BUNDLE_RUN_TOKEN}.json"
  VIBE_PACK_ROOT="${TMP_ROOT}/vibe-coding-feeding-packs"
  CAPABILITY_FIT_ROOT="${TMP_ROOT}/capability-fit-matrices"
  UPGRADE_REPORT_ROOT="${TMP_ROOT}/identity-upgrade-reports"
  IS_FIXTURE_ID="$(ID="$ID" python3 -c 'import os,yaml,pathlib; identity_id=os.environ.get("ID","").strip(); doc=yaml.safe_load(pathlib.Path("identity/catalog/identities.yaml").read_text(encoding="utf-8")) or {}; rows=[x for x in (doc.get("identities") or []) if isinstance(x,dict)]; row=next((x for x in rows if str(x.get("id","")).strip()==identity_id), {}); profile=str(row.get("profile","")).strip().lower(); runtime_mode=str(row.get("runtime_mode","")).strip().lower(); print("1" if (profile=="fixture" or runtime_mode=="demo_only") else "0")')"

  python3 scripts/validate_identity_runtime_contract.py --identity-id "$ID"
  python3 scripts/validate_identity_prompt_quality.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --scope AUTO
  python3 scripts/validate_identity_role_binding.py --identity-id "$ID"
  python3 scripts/validate_identity_home_catalog_alignment.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --identity-home "$CATALOG_PARENT"
  python3 scripts/validate_fixture_runtime_boundary.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci
  python3 scripts/validate_actor_session_binding.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci
  python3 scripts/validate_actor_session_multibinding_concurrency.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci --json-only
  python3 scripts/validate_no_implicit_switch.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_cross_actor_isolation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_identity_session_refresh_status.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --operation ci --baseline-policy warn
  python3 scripts/validate_e2e_hermetic_runtime_import.py --operation ci --pythonpath-bootstrap-mode internal_bootstrap --json-only
  python3 scripts/render_identity_response_stamp.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --view external --disclosure-level standard --out "${STAMP_JSON}" --json-only
  python3 scripts/validate_identity_response_stamp.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-user-visible-gate --operation ci --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${STAMP_BLOCKER_RECEIPT}"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${STAMP_BLOCKER_RECEIPT}"
  python3 scripts/validate_reply_identity_context_first_line.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-first-line-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${FIRST_LINE_BLOCKER_RECEIPT}"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${FIRST_LINE_BLOCKER_RECEIPT}"
  python3 scripts/validate_layer_intent_resolution.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-layer-intent-gate --operation ci --json-only
  python3 scripts/validate_send_time_reply_gate.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-send-time-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${SEND_TIME_BLOCKER_RECEIPT}"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${SEND_TIME_BLOCKER_RECEIPT}"
  python3 scripts/validate_headstamp_recurrence_closure.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --json-only
  python3 scripts/validate_execution_reply_identity_coherence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-coherence-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${COHERENCE_BLOCKER_RECEIPT}"
  python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${COHERENCE_BLOCKER_RECEIPT}"
  python3 scripts/validate_identity_upgrade_prereq.py --identity-id "$ID"
  python3 scripts/validate_identity_update_lifecycle.py --identity-id "$ID"
  python3 scripts/validate_identity_trigger_regression.py --identity-id "$ID"
  python3 scripts/validate_identity_learning_loop.py --identity-id "$ID"
  python3 scripts/validate_identity_collab_trigger.py --identity-id "$ID" --self-test
  python3 scripts/validate_agent_handoff_contract.py --identity-id "$ID" --self-test
  IDENTITY_RUNTIME_OUTPUT_ROOT="${RUNTIME_TMP_ROOT}" python3 scripts/export_route_quality_metrics.py --catalog "${CATALOG_PATH}" --identity-id "$ID"
  python3 scripts/validate_identity_orchestration_contract.py --identity-id "$ID"
  python3 scripts/validate_identity_dialogue_content.py --identity-id "$ID"
  python3 scripts/validate_identity_dialogue_cross_validation.py --identity-id "$ID"
  python3 scripts/validate_identity_dialogue_result_support.py --identity-id "$ID"
  python3 scripts/validate_identity_knowledge_contract.py --identity-id "$ID" --self-test
  python3 scripts/validate_identity_experience_feedback.py --identity-id "$ID" --self-test
  python3 scripts/validate_identity_install_safety.py --identity-id "$ID"
  python3 scripts/validate_identity_install_provenance.py --identity-id "$ID"
  python3 scripts/validate_identity_tool_installation.py --identity-id "$ID"
  python3 scripts/validate_identity_vendor_api_discovery.py --identity-id "$ID"
  python3 scripts/validate_identity_vendor_api_solution.py --identity-id "$ID"
  python3 scripts/validate_semantic_routing_guard.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_instance_protocol_split_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_work_layer_gate_set_routing.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --base "${BASE_SHA}" --head "${HEAD_SHA}" --applied-gate-set instance_required_checks --force-check --json-only
  python3 scripts/validate_protocol_feedback_reply_channel.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --force-check --json-only
  python3 scripts/validate_protocol_feedback_bootstrap_ready.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --force-check --json-only
  python3 scripts/validate_protocol_entry_candidate_bridge.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --force-check --json-only
  python3 scripts/validate_protocol_inquiry_followup_chain.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --force-check --json-only
  python3 scripts/validate_protocol_vendor_semantic_isolation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_external_source_trust_chain.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_protocol_data_sanitization_boundary.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/trigger_platform_optimization_discovery.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_discovery_requiredization.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/build_vibe_coding_feeding_pack.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --out-root "${VIBE_PACK_ROOT}"
  python3 scripts/validate_identity_capability_fit_optimization.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_capability_composition_before_discovery.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_capability_fit_review_freshness.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_capability_fit_roundtable_evidence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/trigger_capability_fit_review.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/build_capability_fit_matrix.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --out-root "${CAPABILITY_FIT_ROOT}" --json-only
  python3 scripts/validate_vendor_namespace_separation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_required_contract_coverage.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID"
  python3 scripts/validate_unlock_formula.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_release_plane_cloud_evidence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --target-branch "${GITHUB_REF_NAME:-main}" --release-head-sha "${HEAD_SHA}" --required-gates-run-id "${GITHUB_RUN_ID:-}" --run-url "https://github.com/${GITHUB_REPOSITORY:-unknown}/actions/runs/${GITHUB_RUN_ID:-0}" --workflow-file-sha "${HEAD_SHA}" --run-head-sha "${HEAD_SHA}" --run-workflow-file-sha "${HEAD_SHA}" --operation ci --json-only
  python3 scripts/validate_cross_cwd_absolute_input.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "$(python3 -c 'from pathlib import Path;print(Path("identity/catalog/identities.yaml").resolve())')" --operation ci --json-only
  python3 scripts/validate_run_id_report_selection.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "${GITHUB_RUN_ID:-ci-local}" --operation ci --json-only
  python3 scripts/validate_phase_bootstrap_before_strict.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_tmp_collision_safety.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "${GITHUB_RUN_ID:-ci-local}" --operation ci --json-only
  python3 scripts/validate_handoff_collab_freshness_rotation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_protocol_feedback_atomic_emit.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_capability_boundary_classification.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_promotion_pipeline.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_outlet_matrix.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_sidecar_cwd_parity.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_docs_bridge_consistency.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_contract_mapping_coverage.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_prompt_bootstrap_capability.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_prompt_capability_matrix.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_refresh_strict_business_interference.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_kernel_ssot_source.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_prompt_derivation_conformance.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_semantic_convergence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_prompt_kernel_executable_coupling.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "${SESSION_ACTOR_ID:-assistant:codex}" --session-id "$HEADSTAMP_SESSION_ID" --operation ci --json-only
  python3 scripts/required_gate_bundle_runner.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "$BUNDLE_RUN_TOKEN" --send-time-gate-status NOT_APPLICABLE --outlet-bypass-detected false --final-emit-contract-status NOT_APPLICABLE --final-emit-policy-mode tool_choice_required --final-emit-schema-status NOT_APPLICABLE --actor-id "$HEADSTAMP_ACTOR_ID" --resolved-work-layer protocol --resolved-source-layer project --lock-state LOCK_MATCH --surface-label ci_validate --operation validate --out "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --json-only
  python3 scripts/required_gate_bundle_runner.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "$BUNDLE_RUN_TOKEN" --send-time-gate-status NOT_APPLICABLE --outlet-bypass-detected false --final-emit-contract-status NOT_APPLICABLE --final-emit-policy-mode tool_choice_required --final-emit-schema-status NOT_APPLICABLE --actor-id "$HEADSTAMP_ACTOR_ID" --resolved-work-layer protocol --resolved-source-layer project --lock-state LOCK_MATCH --surface-label ci_three_plane --operation three-plane --out "$REQUIRED_GATE_BUNDLE_RECEIPT_THREE_PLANE" --json-only
  python3 scripts/validate_required_gate_recurrence_escalator.py --identity-id "$ID" --surface ci --operation ci --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --enforce-blocking --json-only
  python3 scripts/validate_required_gate_tuple_parity.py --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_THREE_PLANE" --require-distinct-operations --json-only
  python3 scripts/validate_replay_archive_contract.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_identity_experience_feedback_governance.py --identity-id "$ID"
  python3 scripts/validate_identity_self_upgrade_enforcement.py --identity-id "$ID" --base "${BASE_SHA}" --head "${HEAD_SHA}"

  if [ "${IS_FIXTURE_ID}" = "1" ]; then
    echo "[INFO] fixture identity ${ID}: skipping mutation/update report validation chain in required-gates (inspection-only lane)."
  else
    PR_BASE_SHA="${BASE_SHA}" PR_HEAD_SHA="${HEAD_SHA}" CI=true python3 scripts/identity_creator.py update --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --mode review-required --out-dir "${UPGRADE_REPORT_ROOT}" --expected-work-layer instance
    UPGRADE_REPORT="$(find "${UPGRADE_REPORT_ROOT}" -maxdepth 1 -type f -name "identity-upgrade-exec-${ID}-*.json" -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)"
    if [ -z "${UPGRADE_REPORT}" ]; then
      echo "[FAIL] missing identity upgrade report for ${ID}"
      exit 1
    fi
    python3 scripts/validate_writeback_continuity.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --report "$UPGRADE_REPORT" --operation ci
    python3 scripts/validate_post_execution_mandatory.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --report "$UPGRADE_REPORT" --operation ci
    python3 scripts/validate_protocol_feedback_sidecar_contract.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --report "$UPGRADE_REPORT" --operation ci --enforce-blocking
    python3 scripts/validate_instance_base_repo_write_boundary.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --report "$UPGRADE_REPORT" --operation ci
    python3 scripts/validate_protocol_feedback_ssot_archival.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci
    python3 scripts/validate_identity_protocol_baseline_freshness.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --execution-report "$UPGRADE_REPORT" --baseline-policy strict
    python3 scripts/validate_identity_protocol_version_alignment.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --execution-report "$UPGRADE_REPORT" --operation ci --alignment-policy strict --json-only
    python3 scripts/validate_identity_self_upgrade_enforcement.py --identity-id "$ID" --execution-report "$UPGRADE_REPORT" --require-ci-binding --expect-github-run-id "${GITHUB_RUN_ID:-}" --expect-github-sha "${GITHUB_SHA:-}"
    python3 scripts/validate_identity_protocol_root_evidence.py --identity-id "$ID" --report "$UPGRADE_REPORT"
    python3 scripts/validate_identity_mode_promotion_arbitration.py --identity-id "$ID" --base "${BASE_SHA}" --head "${HEAD_SHA}" --report "$UPGRADE_REPORT"
    python3 scripts/validate_identity_prompt_activation.py --identity-id "$ID" --report "$UPGRADE_REPORT"
    python3 scripts/validate_identity_capability_arbitration.py --identity-id "$ID" --self-test --upgrade-report "$UPGRADE_REPORT"
  fi

  python3 scripts/validate_identity_ci_enforcement.py --identity-id "$ID"
done
