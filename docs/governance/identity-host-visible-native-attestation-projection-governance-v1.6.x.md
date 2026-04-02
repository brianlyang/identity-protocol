# Identity Host-Visible Native Attestation Projection Governance v1.6.x

- `family_id`: `host_visible_native_attestation_projection`
- `classification`: `net_new_governed_family_bootstrap`
- `status`: `ACTIVE`
- `fail_close_token`: `none_required_bootstrap_lane_stable`

## Governing law

This family is a standalone bootstrap lane outside ISSUE-040 through ISSUE-048.
It must not reopen or absorb ISSUE-040 through ISSUE-048, must not absorb the
`requested_session_binding_required` residual, and must not expand into broader
headstamp, handoff, or continuation semantics.

The admitted machine-visible delta is limited to the following host-visible
native attestation projection fields:

- `current_chat_surface_native_machine_attested`
- `next_hop_admission_status`
- `host_visible_post_check_metrics_status`

## Exact failing evidence

Evidence source:

- `identity-protocol-local/.tmp/full_identity_protocol_scan_base_repo_architect.log`

Required anchors:

- `current_chat_surface_native_machine_attested=false`
- `next_hop_admission_status=FAIL_REQUIRED`
- `"host_visible_post_check_metrics_status": "FAIL_REQUIRED"`
- `surface_class=host_native_chat_panel`
- `native_attestation_wiring_capability=unavailable`

## Fixed write set

The governed bootstrap write set is exactly:

- `identity-protocol-local/docs/governance/identity-host-visible-native-attestation-projection-governance-v1.6.x.md`
- `identity-protocol-local/docs/review/protocol-remediation-audit-ledger-v1.6.x-host-visible-native-attestation-projection.md`
- `identity-protocol-local/scripts/host_visible_native_attestation_projection_common.py`
- `identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py`
- `identity-protocol-local/scripts/ci/run_host_visible_native_attestation_projection_probes_ci.sh`

The following surfaces are read-only inputs and must not be mutated by this
family:

- `identity-protocol-local/scripts/native_chat_headstamp_common.py`
- `identity-protocol-local/scripts/render_identity_response_stamp.py`
- `identity-protocol-local/scripts/full_identity_protocol_scan.py`

## Contract boundary

This family only bootstraps governance, review, common, validator, and probe
coverage around already-existing host-visible projection fields. It does not
rewrite projection semantics.

The bootstrap remains valid only while:

1. the three admitted fields remain the only managed outputs;
2. the evidence log continues to carry the declared anchors;
3. the read-only input surfaces remain outside the mutation boundary; and
4. validation and probes continue to pass without reopening ISSUE-040 through
   ISSUE-048.

## Acceptance gate

The bootstrap is acceptable only when:

- the exact staged paths strictly equal the fixed write set;
- `python3 identity-protocol-local/scripts/validate_host_visible_native_attestation_projection.py --json-only`
  returns `PASS`;
- `bash identity-protocol-local/scripts/ci/run_host_visible_native_attestation_projection_probes_ci.sh`
  returns `PASS` or `PASS_REQUIRED`; and
- the work lands as a single isolated commit and then enters hold.
