#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

tmp_root="${TMPDIR:-$repo_root/.tmp}"
mkdir -p "$tmp_root"
probe_dir="$(mktemp -d "$tmp_root/control-plane-mvp-probes.XXXXXX")"
trap 'rm -rf "$probe_dir"' EXIT

python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only > "$probe_dir/validator.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data' "$probe_dir/validator.json"

python3 scripts/control_plane_lane_preflight.py --json-only > "$probe_dir/preflight.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED"; assert data["lane_id"]=="identity_control_plane_bootstrap_mvp"; assert data["scope_lock_status"]=="LOCKED"' "$probe_dir/preflight.json"

python3 scripts/control_plane_lane_render.py --lane-id identity_control_plane_bootstrap_mvp --json-only > "$probe_dir/render.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED"; assert data["lane_card"]["execution_mode"]=="bootstrap_stream"; assert data["read_only_issue_043_consumption"]["contract_id"]=="non_owner_machine_law_reinforcement_admission_contract_v1"' "$probe_dir/render.json"

cp identity/protocol/mappings/control-plane-lane-registry.v1.yaml "$probe_dir/control-plane-lane-registry.v1.yaml"
cat > "$probe_dir/control-plane-lane-registry.current.yaml" <<'EOF'
active_file: control-plane-lane-registry.v1.yaml
EOF

python3 scripts/control_plane_lane_preflight.py \
  --registry-current "$probe_dir/control-plane-lane-registry.current.yaml" \
  --lane-id identity_control_plane_bootstrap_mvp \
  --write-back \
  --json-only > "$probe_dir/preflight-write.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED"; assert data["status_transition"]["to"]=="preflight_passed"' "$probe_dir/preflight-write.json"

cat > "$probe_dir/success-receipt.json" <<'EOF'
{
  "receipt_schema_version": "control_plane_receipt.v1",
  "validator_result": {
    "status": "PASS_REQUIRED",
    "details": ["validator baseline pass"]
  },
  "probe_result": {
    "status": "PASS",
    "details": ["probe baseline pass"]
  },
  "staged_paths": [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.current.yaml",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/control_plane_lane_preflight.py",
    "scripts/control_plane_lane_render.py",
    "scripts/control_plane_lane_ingest.py",
    "scripts/control_plane_lane_next.py",
    "scripts/control_plane_lane_stream_guard.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh"
  ],
  "commit_id": "control-plane-mvp-probe-commit",
  "warnings": ["report_older_than_key_inputs"],
  "observed_actions": ["mutate_fixed_write_set", "run_validator", "run_probe", "stage_fixed_write_set", "make_isolated_commit", "ingest_structured_receipt"]
}
EOF

python3 scripts/control_plane_lane_stream_guard.py \
  --registry-current "$probe_dir/control-plane-lane-registry.current.yaml" \
  --lane-id identity_control_plane_bootstrap_mvp \
  --receipt-file "$probe_dir/success-receipt.json" \
  --phase closeout \
  --require-exact \
  --json-only > "$probe_dir/guard-pass.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED", data' "$probe_dir/guard-pass.json"

python3 scripts/control_plane_lane_ingest.py \
  --registry-current "$probe_dir/control-plane-lane-registry.current.yaml" \
  --lane-id identity_control_plane_bootstrap_mvp \
  --receipt-file "$probe_dir/success-receipt.json" \
  --write-back \
  --json-only > "$probe_dir/ingest.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED"; assert data["new_status"]=="closure_done"' "$probe_dir/ingest.json"

python3 scripts/control_plane_lane_next.py \
  --registry-current "$probe_dir/control-plane-lane-registry.current.yaml" \
  --lane-id identity_control_plane_bootstrap_mvp \
  --json-only > "$probe_dir/next-after-closure.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="PASS_REQUIRED"; assert data["next_role"]["identity_id"]=="base-repo-audit-expert-v3"; assert data["next_role"]["suggested_next_status"]=="audit_ready"' "$probe_dir/next-after-closure.json"

cat > "$probe_dir/bad-receipt.json" <<'EOF'
{
  "receipt_schema_version": "control_plane_receipt.v1",
  "validator_result": {
    "status": "PASS_REQUIRED"
  },
  "probe_result": {
    "status": "PASS"
  },
  "staged_paths": [
    "scripts/outside-fixed-write-set.py"
  ],
  "observed_actions": ["reread"]
}
EOF

if python3 scripts/control_plane_lane_stream_guard.py \
  --registry-current "$probe_dir/control-plane-lane-registry.current.yaml" \
  --lane-id identity_control_plane_bootstrap_mvp \
  --receipt-file "$probe_dir/bad-receipt.json" \
  --phase closeout \
  --json-only > "$probe_dir/guard-fail.json"; then
  echo "expected stream guard to fail-close on forbidden action and escaped staged paths" >&2
  exit 1
fi
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["status"]=="FAIL_REQUIRED"; tokens=data["failure_tokens"]; assert any("forbidden_actions_after_scope_lock" in token for token in tokens); assert "staged_paths_escape_fixed_write_set" in tokens' "$probe_dir/guard-fail.json"

python3 scripts/control_plane_lane_next.py --lane-id autonomous_reinforcement_pattern_reference --json-only > "$probe_dir/autonomous-next.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["execution_mode"]=="autonomous_reinforcement"; assert data["handoff_required"] is False; assert data["next_role"]["identity_id"]=="base-repo-closure-orchestrator"' "$probe_dir/autonomous-next.json"

python3 scripts/control_plane_lane_next.py --lane-id split_roles_reference --json-only > "$probe_dir/split-next.json"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["execution_mode"]=="split_roles"; assert data["handoff_required"] is True; assert data["next_role"]["identity_id"]=="base-repo-closure-orchestrator"' "$probe_dir/split-next.json"

printf '{\n  "status": "PASS",\n  "probe": "run_identity_control_plane_bootstrap_mvp_probes_ci",\n  "coverage": [\n    "baseline_validator",\n    "preflight",\n    "render",\n    "ingest",\n    "next_routing",\n    "stream_guard_fail_close",\n    "autonomous_reinforcement",\n    "split_roles",\n    "warn_preservation"\n  ]\n}\n'
