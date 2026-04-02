# Protocol Remediation Audit Ledger v1.6.x — Host-Visible Native Attestation Projection

- `family_id`: `host_visible_native_attestation_projection`
- `classification`: `net_new_governed_family_bootstrap`
- `status`: `IMPLEMENTED`
- `scope_class`: `host_native_chat_panel`

## Residual scope

This ledger tracks only the host-visible native attestation projection residual
for the following fields:

- `current_chat_surface_native_machine_attested`
- `next_hop_admission_status`
- `host_visible_post_check_metrics_status`

Explicit exclusions:

- ISSUE-040 through ISSUE-048 reopen
- `requested_session_binding_required`
- broader headstamp, handoff, or continuation semantics

## Bootstrap evidence

- evidence file: `identity-protocol-local/.tmp/full_identity_protocol_scan_base_repo_architect.log`
- anchor: `current_chat_surface_native_machine_attested=false`
- anchor: `next_hop_admission_status=FAIL_REQUIRED`
- anchor: `"host_visible_post_check_metrics_status": "FAIL_REQUIRED"`
- context: `surface_class=host_native_chat_panel`
- context: `native_attestation_wiring_capability=unavailable`

## Read-only input surfaces

- `identity-protocol-local/scripts/native_chat_headstamp_common.py`
- `identity-protocol-local/scripts/render_identity_response_stamp.py`
- `identity-protocol-local/scripts/full_identity_protocol_scan.py`

## Bootstrap verdict

The governed family is valid only if the bootstrap validator and probe confirm
that governance, review, and common-layer expectations stay aligned with the
host-visible native attestation projection evidence while preserving the
read-only boundary.

- validator: `identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py`
- probe: `identity-protocol-local/scripts/ci/run_host_visible_native_attestation_projection_probes_ci.sh`
- fail-close token: `none_required_bootstrap_lane_stable`
