#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

tmp_root="${TMPDIR:-$repo_root/.tmp}"
mkdir -p "$tmp_root"
probe_dir="$(mktemp -d "$tmp_root/control-plane-registration-probes.XXXXXX")"
trap 'rm -rf "$probe_dir"' EXIT

python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only > "$probe_dir/validator.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data' "$probe_dir/validator.json"

python3 scripts/control_plane_lane_preflight.py --lane-id control_plane_lane_registration_transaction_only --json-only > "$probe_dir/preflight.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["lane_id"]=="control_plane_lane_registration_transaction_only"; assert data["scope_lock_status"]=="LOCKED"' "$probe_dir/preflight.json"

python3 scripts/control_plane_lane_render.py --lane-id control_plane_lane_registration_transaction_only --json-only > "$probe_dir/render.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["requested_lane_id"]=="control_plane_lane_registration_transaction_only"; assert data["active_lane_id"]=="control_plane_role_binding_overlay_hardening"; assert data["lane_card"]["admitted_delta_only"]==["control_plane_protocol_feedback_instance_state_runner_hardening"]; assert data["owner_binding_overlay"]["truth_class"]=="owner_binding_overlay"' "$probe_dir/render.json"

python3 scripts/control_plane_lane_render.py --lane-id control_plane_protocol_feedback_instance_state_runner_hardening --json-only > "$probe_dir/registered-target-render.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["requested_lane_id"]=="control_plane_protocol_feedback_instance_state_runner_hardening"; assert data["active_lane_id"]=="control_plane_role_binding_overlay_hardening"; assert data["lane_card"]["lane_id"]=="control_plane_protocol_feedback_instance_state_runner_hardening"' "$probe_dir/registered-target-render.json"

mkdir -p "$probe_dir/identity/protocol/mappings"
cp identity/protocol/mappings/control-plane-lane-registry.v1.yaml "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.v1.yaml"
cp identity/protocol/mappings/control-plane-owner-binding.current.yaml "$probe_dir/identity/protocol/mappings/control-plane-owner-binding.current.yaml"
cp identity/protocol/mappings/control-plane-owner-binding.v1.yaml "$probe_dir/identity/protocol/mappings/control-plane-owner-binding.v1.yaml"
cat > "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" <<'EOF'
schema_version: control_plane_lane_registry.current.v1
contract_id: control_plane_lane_registration_transaction_only
classification: existing_surface_alignment
active_file: control-plane-lane-registry.v1.yaml
active_lane_id: control_plane_lane_registration_transaction_only
owner_binding_file: control-plane-owner-binding.current.yaml
authoritative_checkout:
  repo_root_mode: script_anchored
  binding_mode: cwd_must_equal_repo_root
  git_top_level_mode: must_equal_repo_root
execution_workspace:
  success_requires_commit_resolution_in_authoritative_checkout: true
  fail_close_on_divergence: true
runtime_tuple_policy:
  concrete_tuple_literals_allowed: false
  allowed_literal_exception_surfaces:
    - owner_binding_overlay
    - actor_session_store
    - runtime_reports
    - ci_probe_fixtures
    - docs_examples
read_only_input_surfaces: []
EOF

python3 scripts/control_plane_lane_preflight.py --registry-current "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" --lane-id control_plane_lane_registration_transaction_only --write-back --json-only > "$probe_dir/preflight-write.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["status_transition"]["to"]=="preflight_passed"' "$probe_dir/preflight-write.json"

head_commit="$(git rev-parse HEAD)"
cat > "$probe_dir/success-receipt.json" <<EOF
{
  "receipt_schema_version": "control_plane_receipt.v1",
  "validator_result": {
    "status": "PASS_REQUIRED"
  },
  "probe_result": {
    "status": "PASS"
  },
  "staged_paths": [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.current.yaml",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/control_plane_lane_render.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh"
  ],
  "commit_id": "$head_commit",
  "observed_actions": [
    "run_validator",
    "run_probe",
    "stage_and_commit"
  ]
}
EOF

python3 scripts/control_plane_lane_stream_guard.py --registry-current "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" --lane-id control_plane_lane_registration_transaction_only --receipt-file "$probe_dir/success-receipt.json" --phase closeout --require-exact --json-only > "$probe_dir/guard-pass.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data' "$probe_dir/guard-pass.json"

python3 scripts/control_plane_lane_ingest.py --registry-current "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" --lane-id control_plane_lane_registration_transaction_only --receipt-file "$probe_dir/success-receipt.json" --write-back --json-only > "$probe_dir/ingest.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["new_status"]=="closure_done"; assert data["next_role"]["identity_id"]=="base-repo-audit-expert-v3"' "$probe_dir/ingest.json"

python3 scripts/control_plane_lane_next.py --registry-current "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" --lane-id control_plane_lane_registration_transaction_only --status-override closure_done --json-only > "$probe_dir/next-after-closure.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data; assert data["next_role"]["identity_id"]=="base-repo-audit-expert-v3"; assert data["next_role"]["suggested_next_status"]=="audit_ready"' "$probe_dir/next-after-closure.json"

cat > "$probe_dir/bad-receipt.json" <<EOF
{
  "receipt_schema_version": "control_plane_receipt.v1",
  "validator_result": {
    "status": "PASS_REQUIRED"
  },
  "probe_result": {
    "status": "PASS"
  },
  "staged_paths": [
    "scripts/validate_actor_session_binding.py"
  ],
  "commit_id": "not-a-real-commit",
  "observed_actions": [
    "reread"
  ]
}
EOF

if python3 scripts/control_plane_lane_stream_guard.py --registry-current "$probe_dir/identity/protocol/mappings/control-plane-lane-registry.current.yaml" --lane-id control_plane_lane_registration_transaction_only --receipt-file "$probe_dir/bad-receipt.json" --phase closeout --require-exact --json-only > "$probe_dir/guard-fail.json"; then
  echo "expected stream guard to fail-close" >&2
  exit 1
fi
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="FAIL_REQUIRED", data; tokens=data["failure_tokens"]; assert "forbidden_actions_after_scope_lock" in tokens; assert "staged_paths_not_exact_fixed_write_set" in tokens; assert "registration_transaction_commit_not_materialized" in tokens' "$probe_dir/guard-fail.json"

printf '{
  "status": "PASS",
  "probe": "run_identity_control_plane_bootstrap_mvp_probes_ci",
  "coverage": [
    "validator_baseline",
    "preflight_lock",
    "render_historical_registration_lane",
    "render_registered_target_lane",
    "guard_exact_receipt",
    "ingest_commit_resolution",
    "next_role_routing",
    "fail_close_on_divergence"
  ]
}
'
