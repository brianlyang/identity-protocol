#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

IDS="${1:-${IDS:-}}"
BASE_SHA="${2:-${BASE_SHA:-$(git rev-parse HEAD~1)}}"
HEAD_SHA="${3:-${HEAD_SHA:-$(git rev-parse HEAD)}}"

if [ -z "${IDS}" ]; then
  echo "[FAIL] IDS is empty"
  exit 1
fi

CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH:-}")"
REPO_CATALOG_PATH="$(protocol_shell_entry_repo_catalog_path "${REPO_CATALOG_PATH:-}")"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-$PWD}/.tmp-runtime}}"
mkdir -p "${TMP_ROOT_BASE}"
CATALOG_PARENT="$(dirname "$(realpath "${CATALOG_PATH}")")"
REPO_CATALOG_ABS="$(REPO_CATALOG_PATH="${REPO_CATALOG_PATH}" python3 -c 'from pathlib import Path; import os; print(Path(os.environ.get("REPO_CATALOG_PATH", "identity/catalog/identities.yaml")).expanduser().resolve())')"

HEADSTAMP_ACTOR_ID="$(protocol_shell_entry_require_actor_id "${HEADSTAMP_ACTOR_ID:-}")"
HEADSTAMP_SESSION_ID="${HEADSTAMP_SESSION_ID:-run:${GITHUB_RUN_ID:-ci-local}}"

run_cmd() {
  echo "[RUN] $*"
  "$@"
}

run_global_protocol_gates() {
  run_cmd python3 scripts/validate_required_gate_surface_drift.py --json-only
  run_cmd bash scripts/ci/run_required_gate_surface_drift_probes_ci.sh
  run_cmd python3 scripts/sync_plugin_join_wiring.py --check --json-only
  run_cmd python3 scripts/docs_command_contract_check.py
  run_cmd python3 scripts/validate_control_plane_budget_sync.py --json-only
  run_cmd bash scripts/ci/run_control_plane_budget_sync_probes_ci.sh
  run_cmd bash scripts/ci/run_control_plane_surface_materialization_probes_ci.sh
  run_cmd bash scripts/ci/run_release_doc_surface_governance_probes_ci.sh
  run_cmd bash scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh
  run_cmd bash scripts/ci/run_v16x_release_closure_summary_probes_ci.sh
  run_cmd bash scripts/ci/run_release_closure_control_plane_status_probes_ci.sh
  run_cmd python3 scripts/validate_issue_register_consistency.py --json-only
  run_cmd bash scripts/ci/run_identity_runtime_mode_guard_probes_ci.sh
  run_cmd python3 scripts/validate_identity_switch_closure_semantics.py --catalog "${CATALOG_PATH}" --json-only
  run_cmd bash scripts/ci/run_identity_context_continuity_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_dialogue_retention_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_artifact_family_routing_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_weak_live_linkage_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh
  run_cmd bash scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh
  run_cmd bash scripts/ci/run_post_execution_report_repair_probes_ci.sh
  run_cmd bash scripts/ci/run_execution_report_selection_convergence_probes_ci.sh
  run_cmd bash scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh
  run_cmd bash scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_update_preflight_terminal_truth_split_probes_ci.sh
  run_cmd bash scripts/ci/run_terminal_truth_boundary_projection_probes_ci.sh
  run_cmd bash scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_health_report_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_heal_replay_closure_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_broadcast_delivery_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_communication_transport_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh
  run_cmd bash scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh
  run_cmd bash scripts/ci/run_executable_surface_runtime_literal_lock_probes_ci.sh
  run_cmd python3 scripts/validate_executable_surface_runtime_literal_lock.py --catalog "${CATALOG_PATH}" --include-active-pack-scripts --json-only
  run_cmd bash scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh
  run_cmd bash scripts/ci/run_workbook_control_plane_probes_ci.sh
  run_cmd bash scripts/ci/run_workbook_family_scaffold_probes_ci.sh
  run_cmd bash scripts/ci/run_feedback_to_judgement_loopback_probes_ci.sh
  run_cmd python3 scripts/validate_native_chat_bootstrap_entry_stream.py --json-only
  run_cmd bash scripts/ci/run_native_chat_bootstrap_entry_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_instance_pack_topology_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_codex_launcher_probes_ci.sh
  run_cmd bash scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh
  run_cmd bash scripts/ci/run_repair_contract_backfill_status_profile_probes_ci.sh
  run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --json-only
  run_cmd python3 scripts/validate_resolve_identity_context_default_local_catalog.py --json-only
  run_cmd python3 scripts/validate_runtime_catalog_metadata_hygiene.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --require-active --json-only
  run_cmd python3 scripts/validate_identity_instance_script_cross_pack_adoption.py --catalog "${CATALOG_PATH}" --json-only
  run_cmd python3 scripts/validate_gateway_wrapper_trust_boundary_cross_cwd.py --json-only
}

run_global_protocol_gates

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
  THREE_PLANE_REPORT_JSON="${TMP_ROOT}/three-plane-${ID}.json"
  IS_FIXTURE_ID="$(ID="$ID" CATALOG_PATH="$CATALOG_PATH" python3 -c 'import os,yaml,pathlib; identity_id=os.environ.get("ID","").strip(); catalog_path=os.environ["CATALOG_PATH"]; doc=yaml.safe_load(pathlib.Path(catalog_path).read_text(encoding="utf-8")) or {}; rows=[x for x in (doc.get("identities") or []) if isinstance(x,dict)]; row=next((x for x in rows if str(x.get("id","")).strip()==identity_id), {}); profile=str(row.get("profile","")).strip().lower(); runtime_mode=str(row.get("runtime_mode","")).strip().lower(); print("1" if (profile=="fixture" or runtime_mode=="demo_only") else "0")')"

  python3 scripts/validate_identity_runtime_contract.py --identity-id "$ID" --catalog "${CATALOG_PATH}"
  python3 scripts/validate_identity_instance_pack_topology.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_instance_script_manifest.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_instance_script_orchestration.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --work-layer instance --source-layer project --json-only
  python3 scripts/validate_route_script_receipt_join.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --work-layer instance --source-layer project --json-only
  python3 scripts/validate_route_execution_lane_admission.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --work-layer instance --source-layer project --json-only
  python3 scripts/validate_identity_context_continuity.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_reentry_brief.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_reentry_consumption.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_context_continuity_receipts.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_dialogue_retention.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_artifact_family_routing.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_identity_weak_live_linkage.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_terminal_truth_cleanliness.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_identity_broadcast_delivery.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_communication_transport.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --json-only
  python3 scripts/validate_identity_prompt_quality.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --scope AUTO
  python3 scripts/validate_identity_role_binding.py --identity-id "$ID" --catalog "${CATALOG_PATH}"
  python3 scripts/validate_identity_home_catalog_alignment.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --identity-home "$CATALOG_PARENT"
  python3 scripts/validate_fixture_runtime_boundary.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci
  python3 scripts/validate_actor_session_binding.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci
  python3 scripts/validate_actor_session_multibinding_concurrency.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci --json-only
  python3 scripts/validate_no_implicit_switch.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_cross_actor_isolation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --scope-mode actor_primary --operation ci
  python3 scripts/validate_identity_session_refresh_status.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --operation ci --baseline-policy warn
  python3 scripts/validate_e2e_hermetic_runtime_import.py --operation ci --pythonpath-bootstrap-mode internal_bootstrap --json-only
  python3 scripts/render_identity_response_stamp.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --work-layer protocol --source-layer project --view external --disclosure-level standard --out "${STAMP_JSON}" --json-only
  python3 scripts/validate_response_stamp_operator_envelope.py --stamp-json "${STAMP_JSON}" --repo-root "${PWD}" --json-only
  if [ "${IS_FIXTURE_ID}" = "1" ]; then
    echo "[INFO] fixture identity ${ID}: skipping user-visible stamp hard gates in ci lane."
  else
    python3 scripts/validate_identity_response_stamp.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-user-visible-gate --operation ci --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${STAMP_BLOCKER_RECEIPT}"
    python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${STAMP_BLOCKER_RECEIPT}"
    python3 scripts/validate_reply_identity_context_first_line.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-first-line-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${FIRST_LINE_BLOCKER_RECEIPT}"
    python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${FIRST_LINE_BLOCKER_RECEIPT}"
  fi
  python3 scripts/validate_layer_intent_resolution.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-layer-intent-gate --operation ci --json-only
  if [ "${IS_FIXTURE_ID}" != "1" ]; then
    python3 scripts/validate_send_time_reply_gate.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-send-time-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${SEND_TIME_BLOCKER_RECEIPT}"
    python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${SEND_TIME_BLOCKER_RECEIPT}"
  fi
  python3 scripts/validate_headstamp_recurrence_closure.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --json-only
  if [ "${IS_FIXTURE_ID}" != "1" ]; then
    python3 scripts/validate_execution_reply_identity_coherence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --force-check --enforce-coherence-gate --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --blocker-receipt-out "${COHERENCE_BLOCKER_RECEIPT}"
    python3 scripts/validate_identity_response_stamp_blocker_receipt.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --force-check --receipt "${COHERENCE_BLOCKER_RECEIPT}"
  fi
  python3 scripts/validate_identity_upgrade_prereq.py --identity-id "$ID"
  python3 scripts/validate_identity_update_lifecycle.py --identity-id "$ID"
  python3 scripts/validate_identity_trigger_regression.py --identity-id "$ID"
  python3 scripts/validate_identity_learning_loop.py --identity-id "$ID"
  if [ "${IS_FIXTURE_ID}" = "1" ]; then
    echo "[INFO] fixture identity ${ID}: skipping collaboration/handoff self-test examples in ci lane."
  else
    python3 scripts/validate_identity_collab_trigger.py --identity-id "$ID" --self-test
    python3 scripts/validate_agent_handoff_contract.py --identity-id "$ID" --self-test
  fi
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
  python3 scripts/validate_identity_routing_learning_strengthening.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_feedback_to_judgement_loopback.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/trigger_capability_fit_review.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/build_capability_fit_matrix.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --out-root "${CAPABILITY_FIT_ROOT}" --json-only
  python3 scripts/validate_vendor_namespace_separation.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci
  python3 scripts/validate_gated_switch_guard.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci --json-only
  python3 scripts/validate_protocol_lane_headstamp_continuity.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --stamp-json "${STAMP_JSON}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --run-id "${GITHUB_RUN_ID:-ci-local}" --expected-work-layer protocol --expected-source-layer project --operation ci --json-only
  python3 scripts/validate_unlock_formula.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_release_plane_cloud_evidence.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --target-branch "${GITHUB_REF_NAME:-main}" --release-head-sha "${HEAD_SHA}" --required-gates-run-id "${GITHUB_RUN_ID:-}" --run-url "https://github.com/${GITHUB_REPOSITORY:-unknown}/actions/runs/${GITHUB_RUN_ID:-0}" --workflow-file-sha "${HEAD_SHA}" --run-head-sha "${HEAD_SHA}" --run-workflow-file-sha "${HEAD_SHA}" --operation ci --json-only
  python3 scripts/validate_cross_cwd_absolute_input.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_ABS}" --operation ci --json-only
  python3 scripts/validate_run_id_report_selection.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "${GITHUB_RUN_ID:-ci-local}" --operation ci --json-only
  python3 scripts/validate_phase_bootstrap_before_strict.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_tmp_collision_safety.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "${GITHUB_RUN_ID:-ci-local}" --operation ci --json-only
  python3 scripts/materialize_contract_bootstrap_emitters.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --apply --json-only
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
  python3 scripts/validate_prompt_kernel_executable_coupling.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --operation ci --json-only
  python3 scripts/required_gate_bundle_runner.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "$BUNDLE_RUN_TOKEN" --send-time-gate-status NOT_APPLICABLE --outlet-bypass-detected false --final-emit-contract-status NOT_APPLICABLE --final-emit-policy-mode tool_choice_required --final-emit-schema-status NOT_APPLICABLE --actor-id "$HEADSTAMP_ACTOR_ID" --resolved-work-layer protocol --resolved-source-layer project --lock-state LOCK_MATCH --surface-label ci_validate --operation validate --out "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --json-only
  python3 scripts/required_gate_bundle_runner.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --run-id "$BUNDLE_RUN_TOKEN" --send-time-gate-status NOT_APPLICABLE --outlet-bypass-detected false --final-emit-contract-status NOT_APPLICABLE --final-emit-policy-mode tool_choice_required --final-emit-schema-status NOT_APPLICABLE --actor-id "$HEADSTAMP_ACTOR_ID" --resolved-work-layer protocol --resolved-source-layer project --lock-state LOCK_MATCH --surface-label ci_three_plane --operation three-plane --out "$REQUIRED_GATE_BUNDLE_RECEIPT_THREE_PLANE" --json-only
  python3 scripts/validate_required_gate_recurrence_escalator.py --identity-id "$ID" --surface ci --operation ci --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --enforce-blocking --json-only
  python3 scripts/validate_required_gate_tuple_parity.py --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_VALIDATE" --receipt "$REQUIRED_GATE_BUNDLE_RECEIPT_THREE_PLANE" --require-distinct-operations --json-only
  python3 scripts/validate_required_contract_coverage.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --operation ci --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --run-id "$BUNDLE_RUN_TOKEN"
  python3 scripts/validate_replay_archive_contract.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --operation ci --json-only
  python3 scripts/validate_identity_experience_feedback_governance.py --identity-id "$ID"
  if [ "${IS_FIXTURE_ID}" = "1" ]; then
    echo "[INFO] fixture identity ${ID}: skipping diff-only self-upgrade enforcement in ci lane."
  else
    python3 scripts/validate_identity_self_upgrade_enforcement.py --identity-id "$ID" --base "${BASE_SHA}" --head "${HEAD_SHA}"
  fi

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
    python3 scripts/report_three_plane_status.py --identity-id "$ID" --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --actor-id "$HEADSTAMP_ACTOR_ID" --session-id "$HEADSTAMP_SESSION_ID" --execution-report "$UPGRADE_REPORT" --expected-work-layer protocol --expected-source-layer project --out "$THREE_PLANE_REPORT_JSON"
    IDENTITY_ID="$ID" CATALOG_PATH="$CATALOG_PATH" REPO_CATALOG_PATH="$REPO_CATALOG_PATH" HEAD_SHA="$HEAD_SHA" GITHUB_REF_NAME="${GITHUB_REF_NAME:-main}" HEADSTAMP_ACTOR_ID="$HEADSTAMP_ACTOR_ID" HEADSTAMP_SESSION_ID="$HEADSTAMP_SESSION_ID" UPGRADE_REPORT_PATH="$UPGRADE_REPORT" THREE_PLANE_REPORT_PATH="$THREE_PLANE_REPORT_JSON" python3 - <<'PY'
import json
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

report_path = os.environ["UPGRADE_REPORT_PATH"]
three_plane_path = os.environ["THREE_PLANE_REPORT_PATH"]
identity_id = os.environ["IDENTITY_ID"]
catalog_path = os.environ["CATALOG_PATH"]
repo_catalog_path = os.environ["REPO_CATALOG_PATH"]
head_sha = os.environ["HEAD_SHA"]
github_ref_name = os.environ["GITHUB_REF_NAME"]
headstamp_actor_id = os.environ["HEADSTAMP_ACTOR_ID"]
headstamp_session_id = os.environ["HEADSTAMP_SESSION_ID"]

with open(report_path, encoding="utf-8") as fh:
    report = json.load(fh)
with open(three_plane_path, encoding="utf-8") as fh:
    three_plane = json.load(fh)

strict_non_upgrade = (
    bool(report.get("all_ok"))
    and not bool(report.get("upgrade_required"))
    and str(report.get("writeback_mode", "")).strip().upper() == "STRICT_WRITEBACK"
    and str(report.get("writeback_status", "")).strip().upper() == "NOT_REQUIRED"
)
post_exec = (
    (three_plane.get("instance_plane_detail") or {}).get("post_execution_mandatory") or {}
)

if not strict_non_upgrade:
    print("[INFO] skip three-plane non-upgrade closure assertion: current report is not strict non-upgrade")
else:
    if str(post_exec.get("post_execution_mandatory_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit(
            "[FAIL] expected post_execution_mandatory_status=PASS_REQUIRED for strict non-upgrade closure assertion"
        )

    if str(three_plane.get("instance_plane_status", "")).strip().upper() != "CLOSED":
        raise SystemExit(
            "[FAIL] strict non-upgrade report must close instance plane when post_execution_mandatory passed"
        )

    print("[OK] strict non-upgrade closure assertion passed: instance_plane_status=CLOSED")

release_status = str(three_plane.get("release_plane_status", "")).strip().upper()
release_conditions = ((three_plane.get("release_plane_detail") or {}).get("conditions") or {})
if release_status != "BLOCKED":
    raise SystemExit(
        "[FAIL] expected release_plane_status=BLOCKED when release baseline is known but cloud evidence is still missing"
    )
if release_conditions.get("run_head_matches_release_head") is not True:
    raise SystemExit("[FAIL] expected run_head_matches_release_head=true after release baseline normalization")
if release_conditions.get("workflow_file_sha_matches") is not True:
    raise SystemExit("[FAIL] expected workflow_file_sha_matches=true after release baseline normalization")
if release_conditions.get("required_gates_run_id_accessible") is not False:
    raise SystemExit("[FAIL] expected required_gates_run_id_accessible=false without release cloud evidence")
if release_conditions.get("required_checks_all_success") is not False:
    raise SystemExit("[FAIL] expected required_checks_all_success=false without release checks evidence")

print("[OK] release-plane baseline normalization assertion passed: baseline_known_missing_cloud_evidence=>BLOCKED")

baseline_unlinked_probe = subprocess.run(
    [
        sys.executable,
        "scripts/validate_release_plane_cloud_evidence.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog_path,
        "--operation",
        "update",
        "--force-required",
        "--json-only",
    ],
    capture_output=True,
    text=True,
    check=False,
)
try:
    baseline_unlinked_payload = json.loads(baseline_unlinked_probe.stdout)
except Exception as exc:
    raise SystemExit(f"[FAIL] unable to parse release cloud evidence baseline-unlinked probe output: {exc}")

if baseline_unlinked_probe.returncode != 0:
    raise SystemExit("[FAIL] expected release cloud evidence baseline-unlinked probe to skip rather than fail")
if str(baseline_unlinked_payload.get("release_plane_cloud_evidence_status", "")).strip().upper() != "SKIPPED_NOT_REQUIRED":
    raise SystemExit("[FAIL] expected release_plane_cloud_evidence_status=SKIPPED_NOT_REQUIRED when release baseline is absent")
if (
    "required_contract_not_applicable_missing_release_evidence"
    not in {str(x).strip() for x in (baseline_unlinked_payload.get("stale_reasons") or []) if str(x).strip()}
):
    raise SystemExit("[FAIL] expected canonical missing-release-evidence skip reason when release baseline is absent")

print("[OK] release cloud evidence baseline-unlinked assertion passed: missing_release_evidence=>SKIPPED_NOT_REQUIRED")

probe = subprocess.run(
    [
        sys.executable,
        "scripts/validate_release_plane_cloud_evidence.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog_path,
        "--target-branch",
        github_ref_name,
        "--release-head-sha",
        head_sha,
        "--workflow-file-sha",
        head_sha,
        "--run-head-sha",
        head_sha,
        "--run-workflow-file-sha",
        head_sha,
        "--operation",
        "ci",
        "--force-required",
        "--json-only",
    ],
    capture_output=True,
    text=True,
    check=False,
)
try:
    probe_payload = json.loads(probe.stdout)
except Exception as exc:
    raise SystemExit(f"[FAIL] unable to parse release cloud evidence probe output: {exc}")

if probe.returncode == 0:
    raise SystemExit("[FAIL] expected release cloud evidence probe to fail when release baseline is known but cloud evidence is absent")
if str(probe_payload.get("release_plane_cloud_evidence_status", "")).strip().upper() != "FAIL_REQUIRED":
    raise SystemExit("[FAIL] expected release_plane_cloud_evidence_status=FAIL_REQUIRED for missing cloud evidence probe")
if str(probe_payload.get("error_code", "")).strip().upper() != "IP-RCLOUD-001":
    raise SystemExit("[FAIL] expected IP-RCLOUD-001 for missing cloud evidence probe")

probe_conditions = probe_payload.get("conditions") or {}
if probe_conditions.get("required_gates_run_id_present") is not False:
    raise SystemExit("[FAIL] expected required_gates_run_id_present=false for missing cloud evidence probe")
if probe_conditions.get("run_url_present") is not False:
    raise SystemExit("[FAIL] expected run_url_present=false for missing cloud evidence probe")
if str(probe_conditions.get("required_checks_status", "")).strip().upper() != "EVIDENCE_MISSING":
    raise SystemExit("[FAIL] expected required_checks_status=EVIDENCE_MISSING for missing cloud evidence probe")

print("[OK] release cloud evidence validator assertion passed: baseline_known_missing_evidence=>FAIL_REQUIRED/IP-RCLOUD-001")

with tempfile.TemporaryDirectory(prefix="release-cloud-evidence-ci-") as tmpdir:
    empty_checks_path = os.path.join(tmpdir, "checks-empty.json")
    failed_checks_path = os.path.join(tmpdir, "checks-failed.json")
    jobs_pass_path = os.path.join(tmpdir, "jobs-pass.json")
    gh_runs_pass_path = os.path.join(tmpdir, "gh-runs-pass.json")

    with open(empty_checks_path, "w", encoding="utf-8") as fh:
        json.dump({"required_checks_set": []}, fh)
    with open(failed_checks_path, "w", encoding="utf-8") as fh:
        json.dump({"required_checks_set": [{"name": "ci", "status": "failure"}]}, fh)
    with open(jobs_pass_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "jobs": [
                    {"id": 1, "name": "build", "status": "completed", "conclusion": "success"},
                    {"id": 2, "name": "lint", "status": "completed", "conclusion": "success"},
                ]
            },
            fh,
        )
    with open(gh_runs_pass_path, "w", encoding="utf-8") as fh:
        json.dump(
            [
                {
                    "databaseId": 300,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/300",
                    "workflowName": "protocol-ci",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-03-25T00:02:00Z",
                },
                {
                    "databaseId": 250,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/250",
                    "workflowName": "protocol-ci",
                    "status": "completed",
                    "conclusion": "failure",
                    "createdAt": "2026-03-25T00:01:00Z",
                },
                {
                    "databaseId": 200,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/200",
                    "workflowName": "identity-protocol-ci",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-03-25T00:00:00Z",
                },
            ],
            fh,
        )

    def run_checks_probe(checks_path: str) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_release_plane_cloud_evidence.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog_path,
                "--target-branch",
                github_ref_name,
                "--release-head-sha",
                head_sha,
                "--required-gates-run-id",
                "ci-synthetic-run",
                "--run-url",
                "https://example.invalid/run/ci-synthetic-run",
                "--workflow-file-sha",
                head_sha,
                "--run-head-sha",
                head_sha,
                "--run-workflow-file-sha",
                head_sha,
                "--checks-json",
                checks_path,
                "--operation",
                "ci",
                "--force-required",
                "--json-only",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            payload = json.loads(result.stdout)
        except Exception as exc:
            raise SystemExit(f"[FAIL] unable to parse release checks probe output: {exc}")
        payload["_rc"] = result.returncode
        return payload

    empty_probe = run_checks_probe(empty_checks_path)
    if empty_probe["_rc"] == 0:
        raise SystemExit("[FAIL] expected EMPTY_SET release checks probe to fail-close")
    if str(empty_probe.get("error_code", "")).strip().upper() != "IP-RCLOUD-003":
        raise SystemExit("[FAIL] expected IP-RCLOUD-003 for EMPTY_SET release checks probe")
    if str((empty_probe.get("conditions") or {}).get("required_checks_status", "")).strip().upper() != "EMPTY_SET":
        raise SystemExit("[FAIL] expected required_checks_status=EMPTY_SET for EMPTY_SET release checks probe")

    failed_probe = run_checks_probe(failed_checks_path)
    if failed_probe["_rc"] == 0:
        raise SystemExit("[FAIL] expected FAILED release checks probe to fail-close")
    if str(failed_probe.get("error_code", "")).strip().upper() != "IP-RCLOUD-003":
        raise SystemExit("[FAIL] expected IP-RCLOUD-003 for FAILED release checks probe")
    if str((failed_probe.get("conditions") or {}).get("required_checks_status", "")).strip().upper() != "FAILED":
        raise SystemExit("[FAIL] expected required_checks_status=FAILED for FAILED release checks probe")

    jobs_probe = subprocess.run(
        [
            sys.executable,
            "scripts/validate_release_plane_cloud_evidence.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog_path,
            "--target-branch",
            github_ref_name,
            "--release-head-sha",
            head_sha,
            "--required-gates-run-id",
            "ci-synthetic-run",
            "--run-url",
            "https://example.invalid/run/ci-synthetic-run",
            "--workflow-file-sha",
            head_sha,
            "--run-head-sha",
            head_sha,
            "--run-workflow-file-sha",
            head_sha,
            "--jobs-json",
            jobs_pass_path,
            "--operation",
            "ci",
            "--force-required",
            "--json-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        jobs_payload = json.loads(jobs_probe.stdout)
    except Exception as exc:
        raise SystemExit(f"[FAIL] unable to parse release jobs probe output: {exc}")

    if jobs_probe.returncode != 0:
        raise SystemExit("[FAIL] expected jobs-json release evidence probe to pass")
    if str(jobs_payload.get("release_plane_cloud_evidence_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected release_plane_cloud_evidence_status=PASS_REQUIRED for jobs-json probe")
    if str(jobs_payload.get("release_cloud_evidence_adapter_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected release_cloud_evidence_adapter_status=PASS_REQUIRED for jobs-json probe")
    if str(jobs_payload.get("release_cloud_evidence_adapter_acquisition_mode", "")).strip() != "materialized_input":
        raise SystemExit("[FAIL] expected jobs-json probe to expose materialized_input acquisition mode")
    if not bool(jobs_payload.get("release_cloud_evidence_adapter_local_dev_canonical", False)):
        raise SystemExit("[FAIL] expected jobs-json probe to expose local-dev canonical materialized evidence")
    if str((jobs_payload.get("conditions") or {}).get("required_checks_status", "")).strip().upper() != "PASS":
        raise SystemExit("[FAIL] expected required_checks_status=PASS for jobs-json probe")

    sys.path.insert(0, str(Path(os.getcwd()) / "scripts"))
    import resolve_release_plane_cloud_evidence as release_adapter_mod

    original_fetch_gh_run_list = release_adapter_mod._fetch_gh_run_list
    try:
        release_adapter_mod._fetch_gh_run_list = lambda **kwargs: (
            [
                {
                    "databaseId": 300,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/300",
                    "workflowName": "protocol-ci",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-03-25T00:02:00Z",
                },
                {
                    "databaseId": 250,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/250",
                    "workflowName": "protocol-ci",
                    "status": "completed",
                    "conclusion": "failure",
                    "createdAt": "2026-03-25T00:01:00Z",
                },
                {
                    "databaseId": 200,
                    "headBranch": github_ref_name,
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/200",
                    "workflowName": "identity-protocol-ci",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-03-25T00:00:00Z",
                },
                {
                    "databaseId": 150,
                    "headBranch": "other-branch",
                    "headSha": head_sha,
                    "url": "https://github.com/example/repo/actions/runs/150",
                    "workflowName": "foreign-workflow",
                    "status": "completed",
                    "conclusion": "failure",
                    "createdAt": "2026-03-24T23:59:00Z",
                },
            ],
            "",
        )
        gh_aggregate_payload = release_adapter_mod.resolve_release_cloud_evidence(
            identity_id=identity_id,
            operation="ci",
            target_branch=github_ref_name,
            release_head_sha=head_sha,
            required_gates_run_id="",
            run_url="",
            checks_json="",
            jobs_json="",
            github_repository="example/repo",
            github_server_url="https://github.com",
            github_token_env="MISSING_GITHUB_TOKEN_FOR_PROBE",
        )
    finally:
        release_adapter_mod._fetch_gh_run_list = original_fetch_gh_run_list

    if str(gh_aggregate_payload.get("release_cloud_evidence_adapter_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected gh-run-list aggregate adapter probe to pass")
    if str(gh_aggregate_payload.get("adapter_source_kind", "")).strip() != "gh_run_list_commit_aggregate":
        raise SystemExit("[FAIL] expected gh-run-list aggregate adapter source kind")
    if str(gh_aggregate_payload.get("required_gates_run_id", "")).strip() != "300":
        raise SystemExit("[FAIL] expected newest matching gh workflow run to become carrier run")
    if int(gh_aggregate_payload.get("required_checks_count", 0) or 0) != 2:
        raise SystemExit("[FAIL] expected gh-run-list aggregate probe to de-duplicate workflow names")

    gh_runs_probe = subprocess.run(
        [
            sys.executable,
            "scripts/validate_release_plane_cloud_evidence.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog_path,
            "--target-branch",
            github_ref_name,
            "--release-head-sha",
            head_sha,
            "--workflow-file-sha",
            head_sha,
            "--run-head-sha",
            head_sha,
            "--run-workflow-file-sha",
            head_sha,
            "--gh-runs-json",
            gh_runs_pass_path,
            "--operation",
            "ci",
            "--force-required",
            "--json-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        gh_runs_payload = json.loads(gh_runs_probe.stdout)
    except Exception as exc:
        raise SystemExit(f"[FAIL] unable to parse release gh-runs probe output: {exc}")

    if gh_runs_probe.returncode != 0:
        raise SystemExit("[FAIL] expected gh-runs-json release evidence probe to pass")
    if str(gh_runs_payload.get("release_plane_cloud_evidence_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected release_plane_cloud_evidence_status=PASS_REQUIRED for gh-runs-json probe")
    if str(gh_runs_payload.get("release_cloud_evidence_adapter_source_kind", "")).strip() != "gh_run_list_json":
        raise SystemExit("[FAIL] expected gh-runs-json adapter source kind")
    if str(gh_runs_payload.get("release_cloud_evidence_adapter_acquisition_mode", "")).strip() != "materialized_input":
        raise SystemExit("[FAIL] expected gh-runs-json probe to expose materialized_input acquisition mode")
    if not bool(gh_runs_payload.get("release_cloud_evidence_adapter_local_dev_canonical", False)):
        raise SystemExit("[FAIL] expected gh-runs-json probe to expose local-dev canonical materialized evidence")
    if str(gh_runs_payload.get("required_gates_run_id", "")).strip() != "300":
        raise SystemExit("[FAIL] expected gh-runs-json probe to select newest matching carrier run")
    if str((gh_runs_payload.get("conditions") or {}).get("required_checks_status", "")).strip().upper() != "PASS":
        raise SystemExit("[FAIL] expected required_checks_status=PASS for gh-runs-json probe")

    jobs_three_plane_path = os.path.join(tmpdir, "three-plane-jobs-pass.json")
    jobs_three_plane = subprocess.run(
        [
            sys.executable,
            "scripts/report_three_plane_status.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog_path,
            "--repo-catalog",
            repo_catalog_path,
            "--actor-id",
            headstamp_actor_id,
            "--session-id",
            headstamp_session_id,
            "--target-branch",
            github_ref_name,
            "--release-head-sha",
            head_sha,
            "--required-gates-run-id",
            "ci-synthetic-run",
            "--run-url",
            "https://example.invalid/run/ci-synthetic-run",
            "--workflow-file-sha",
            head_sha,
            "--run-head-sha",
            head_sha,
            "--run-workflow-file-sha",
            head_sha,
            "--jobs-json",
            jobs_pass_path,
            "--out",
            jobs_three_plane_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if jobs_three_plane.returncode != 0:
        raise SystemExit("[FAIL] expected jobs-json three-plane probe to complete successfully")
    with open(jobs_three_plane_path, encoding="utf-8") as fh:
        jobs_three_plane_payload = json.load(fh)
    if str(jobs_three_plane_payload.get("release_plane_status", "")).strip().upper() != "CLOSED":
        raise SystemExit("[FAIL] expected release_plane_status=CLOSED for jobs-json three-plane probe")
    adapter_payload = jobs_three_plane_payload.get("release_cloud_evidence_adapter") or {}
    if str(adapter_payload.get("release_cloud_evidence_adapter_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected three-plane adapter status PASS_REQUIRED for jobs-json probe")
    if str(adapter_payload.get("adapter_acquisition_mode", "")).strip() != "materialized_input":
        raise SystemExit("[FAIL] expected three-plane jobs-json adapter acquisition mode materialized_input")
    if not bool(adapter_payload.get("adapter_local_dev_canonical", False)):
        raise SystemExit("[FAIL] expected three-plane jobs-json adapter to expose local-dev canonical materialized evidence")

    gh_runs_three_plane_path = os.path.join(tmpdir, "three-plane-gh-runs-pass.json")
    gh_runs_three_plane = subprocess.run(
        [
            sys.executable,
            "scripts/report_three_plane_status.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog_path,
            "--repo-catalog",
            repo_catalog_path,
            "--actor-id",
            headstamp_actor_id,
            "--session-id",
            headstamp_session_id,
            "--target-branch",
            github_ref_name,
            "--release-head-sha",
            head_sha,
            "--workflow-file-sha",
            head_sha,
            "--run-head-sha",
            head_sha,
            "--run-workflow-file-sha",
            head_sha,
            "--gh-runs-json",
            gh_runs_pass_path,
            "--out",
            gh_runs_three_plane_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if gh_runs_three_plane.returncode != 0:
        raise SystemExit("[FAIL] expected gh-runs-json three-plane probe to complete successfully")
    with open(gh_runs_three_plane_path, encoding="utf-8") as fh:
        gh_runs_three_plane_payload = json.load(fh)
    if str(gh_runs_three_plane_payload.get("release_plane_status", "")).strip().upper() != "CLOSED":
        raise SystemExit("[FAIL] expected release_plane_status=CLOSED for gh-runs-json three-plane probe")
    gh_three_plane_adapter = gh_runs_three_plane_payload.get("release_cloud_evidence_adapter") or {}
    if str(gh_three_plane_adapter.get("adapter_acquisition_mode", "")).strip() != "materialized_input":
        raise SystemExit("[FAIL] expected gh-runs-json three-plane adapter acquisition mode materialized_input")
    if not bool(gh_three_plane_adapter.get("adapter_local_dev_canonical", False)):
        raise SystemExit("[FAIL] expected gh-runs-json three-plane adapter to expose local-dev canonical materialized evidence")

    repo_root = os.getcwd()
    full_scan_script = Path(repo_root) / "scripts" / "full_identity_protocol_scan.py"
    sys.path.insert(0, str(Path(repo_root) / "scripts"))
    sys.path.insert(0, repo_root)
    spec = importlib.util.spec_from_file_location("full_scan_release_adapter_probe_mod", full_scan_script)
    if spec is None or spec.loader is None:
        raise SystemExit("[FAIL] unable to load full_identity_protocol_scan.py for release adapter parity probe")
    full_scan_mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = full_scan_mod
    spec.loader.exec_module(full_scan_mod)

    command_log = []

    def fake_full_scan_run(cmd, cwd, env=None):
        command_log.append(list(cmd))
        target = cmd[1] if len(cmd) > 1 else ""
        if target.endswith("validate_release_plane_cloud_evidence.py"):
            return full_scan_mod.CheckResult(
                rc=0,
                ok=True,
                tail="PASS_REQUIRED",
                stdout=json.dumps(jobs_payload),
                stderr="",
            )
        if target.endswith("report_three_plane_status.py"):
            return full_scan_mod.CheckResult(
                rc=0,
                ok=True,
                tail="CLOSED",
                stdout=json.dumps(jobs_three_plane_payload),
                stderr="",
            )
        return full_scan_mod.CheckResult(rc=0, ok=True, tail="PASS_REQUIRED", stdout="{}", stderr="")

    full_scan_mod._run = fake_full_scan_run
    full_scan_out_path = Path(tmpdir) / "full-scan-jobs-pass.json"
    argv = [
        str(full_scan_script),
        "--repo-root",
        repo_root,
        "--scan-mode",
        "target",
        "--identity-ids",
        identity_id,
        "--project-catalog",
        catalog_path,
        "--actor-id",
        headstamp_actor_id,
        "--session-id",
        headstamp_session_id,
        "--target-branch",
        github_ref_name,
        "--release-head-sha",
        head_sha,
        "--required-gates-run-id",
        "ci-synthetic-run",
        "--run-url",
        "https://example.invalid/run/ci-synthetic-run",
        "--workflow-file-sha",
        head_sha,
        "--run-head-sha",
        head_sha,
        "--run-workflow-file-sha",
        head_sha,
        "--jobs-json",
        jobs_pass_path,
        "--out",
        str(full_scan_out_path),
    ]
    old_argv = sys.argv
    sys.argv = argv
    full_scan_stdout = io.StringIO()
    with redirect_stdout(full_scan_stdout):
        rc = full_scan_mod.main()
    sys.argv = old_argv
    if rc != 0:
        raise SystemExit(f"[FAIL] expected full-scan adapter parity probe to pass, got rc={rc}: {full_scan_stdout.getvalue()}")

    full_scan_payload = json.loads(full_scan_out_path.read_text(encoding="utf-8"))
    full_scan_row = ((full_scan_payload.get("catalogs") or [{}])[0].get("identities") or [{}])[0]
    full_scan_release = ((full_scan_row.get("checks") or {}).get("release_plane_cloud_evidence") or {})
    if str(full_scan_release.get("release_plane_cloud_evidence_status", "")).strip().upper() != "PASS_REQUIRED":
        raise SystemExit("[FAIL] expected full-scan release-plane consumer to preserve validator PASS_REQUIRED")
    if str((full_scan_release.get("conditions") or {}).get("required_checks_status", "")).strip().upper() != "PASS":
        raise SystemExit("[FAIL] expected full-scan release-plane consumer to preserve required_checks_status=PASS")
    if str((full_scan_row.get("three_plane") or {}).get("release", "")).strip().upper() != "CLOSED":
        raise SystemExit("[FAIL] expected full-scan three-plane projection to preserve release=CLOSED")

    release_cmd = next(
        cmd for cmd in command_log if len(cmd) > 1 and str(cmd[1]).endswith("validate_release_plane_cloud_evidence.py")
    )
    three_cmd = next(
        cmd for cmd in command_log if len(cmd) > 1 and str(cmd[1]).endswith("report_three_plane_status.py")
    )
    if "--checks-json" not in release_cmd or "--checks-json" not in three_cmd:
        raise SystemExit("[FAIL] expected full-scan parity probe to route both consumers through canonical checks-json")
    if "--jobs-json" in release_cmd or "--jobs-json" in three_cmd:
        raise SystemExit("[FAIL] full-scan parity probe must fan out canonical checks-json, not raw jobs-json")
    release_checks_idx = release_cmd.index("--checks-json") + 1
    three_checks_idx = three_cmd.index("--checks-json") + 1
    if release_cmd[release_checks_idx] != three_cmd[three_checks_idx]:
        raise SystemExit("[FAIL] expected full-scan consumers to share one canonical checks-json path")

    print("[OK] release adapter consumer parity probe passed: validator/three-plane/full-scan stay aligned")

print("[OK] release cloud evidence checks-state probes passed: EVIDENCE_MISSING/EMPTY_SET/FAILED/PASS remain distinct")
PY
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
