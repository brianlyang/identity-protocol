# Identity Headstamp Last-Hop Closure Governance v1.6.9

## Scope

This governance item formalizes the closure model for user-visible headstamp continuity:

1. Pre-send strong control on governed outlet (`send-time` gate).
2. 100% post-check detectability on host-visible runtime state.
3. Next-hop hard block when post-check state is missing/invalid/active.

The model is designed for infrastructure operation in protocol scripts, not instance-local manual patching.

## Control Model

### 1) Pre-send (target >=95%)

- All user-visible traffic must pass `scripts/validate_send_time_reply_gate.py`.
- In strict operations, reply outlet must be governed and guarded.
- Missing reply evidence and malformed first-line are split by error family:
  - `IP-HDSTAMP-004`: reply evidence missing.
  - `IP-HDSTAMP-001`: first-line missing/malformed.

### 2) Post-check detectability (required 100%)

- Host-visible live closure is written to:
  - `runtime/state/host_visible_surface_live_closure_state.json`
- `scripts/validate_host_transport_wiring_attestation.py` writes fail-close closure state on:
  - missing state
  - invalid state
  - blocker active
  - stale/mismatch live receipts

### 3) Next-hop hard block (required 100%)

- `scripts/validate_send_time_reply_gate.py` blocks before first-line gate when:
  - post-check state missing/invalid
  - post-check blocker active
- Block stage is explicit:
  - `pre_first_line_post_check_state_unavailable`
  - `pre_first_line_post_check_blocker_active`

## Source Policy (runtime vs fixture)

`ci_fixture` source is operation-scoped:

- Allowed: `scan`, `ci`, `three-plane`
- Forbidden by default: `validate`, `update`, `activate`, `mutation`, `readiness`, `e2e`, `inspection`, `send-time`

If forbidden operation still requests `ci_fixture`, validation fails closed.

This policy is enforced in two places and must stay equivalent:

1. Validator side (`validate_host_transport_wiring_attestation.py`, `recover_host_visible_post_check_state.py`)
2. Runtime wrapper template side (`create_identity_pack.py` -> generated `protocol_session_chain_wrapper.py`)

Any policy drift between these two surfaces is treated as a protocol defect.

## Wrapper Regeneration Baseline

Template fixes are not complete until runtime wrappers are regenerated for active instances.

Required regeneration path:

```bash
python3 scripts/repair_contract_backfill.py --catalog <catalog_path> --identity-id <identity_id> --apply --json-only
```

Acceptance signals:

- `host_gateway_wrapper_artifacts_refreshed=true` when wrapper hash changes
- `applied=true` whenever wrapper artifacts changed, even if task/catalog/meta payloads were already up-to-date

## Canonical Latest Template Parity (required 100%)

`runtime==contract` is not sufficient for closure. Protocol must also enforce:

1. Contract wrapper-template attestation equals canonical template attestation from protocol source.
2. Runtime wrapper file hashes equal canonical template hashes.
3. Runtime gateway contract wrapper-template attestation equals canonical template attestation.

Fail-close validator surface:

- `scripts/validate_protocol_unique_entry_gate.py`
  - `protocol_host_gateway_wrapper_template_canonical_load_status`
  - `protocol_host_gateway_wrapper_template_latest_status`

Failure examples (all must hard fail):

- `host_gateway_wrapper_template_canonical_policy_unavailable:*`
- `host_gateway_wrapper_template_attestation_not_latest:*`
- `host_gateway_*_wrapper_template_sha256_not_latest`
- `host_gateway_runtime_contract_wrapper_template_attestation_not_latest:*`

## Official One-Command Closure

Use:

```bash
python3 scripts/run_host_visible_live_closure.py \
  --catalog <catalog_path> \
  --repo-catalog identity/catalog/identities.yaml \
  --identity-id <identity_id> \
  --actor-id <actor_id> \
  --session-id <session_id> \
  --run-id <run_id> \
  --reply-file <governed_reply_file> \
  --operation validate \
  --outlet-channel-id commentary \
  --json-only
```

The command performs, in order:

1. `recover_host_visible_post_check_state` (runtime source only)
2. `validate_host_transport_wiring_attestation --require-live-receipts`
3. `validate_send_time_reply_gate --enforce-send-time-gate`

Single JSON output carries step status + closure status.

## Official Feedback Channel Direction

- `outbox-to-protocol`: instance -> protocol feedback lane (upstream escalation).
- `inbox-from-protocol`: protocol -> instance feedback lane (downstream governance notice).

Both lanes are canonical runtime paths under `runtime/protocol-feedback/` and both must be index-linked via `evidence-index/INDEX.md`.

## Official Feedback Outbox Routing

Human-generated P0 notices must be emitted through canonical identity feedback outbox,
not ad-hoc project activity folders.

Use:

```bash
python3 scripts/emit_protocol_feedback_batch.py \
  --catalog <catalog_path> \
  --identity-id <identity_id> \
  --title "<feedback title>" \
  --slug <short_slug> \
  --body-file <markdown_notice_file> \
  --summary-json <optional_summary_json> \
  --json-only
```

The command resolves `<pack>/runtime/protocol-feedback/outbox-to-protocol` from
catalog + identity and auto-links refs into `evidence-index/INDEX.md`.

## Official Feedback Inbox Routing

Protocol-side governance notices to an instance must use inbox lane, not outbox lane.

Use:

```bash
python3 scripts/emit_protocol_feedback_batch.py \
  --catalog <catalog_path> \
  --identity-id <identity_id> \
  --lane inbox \
  --title "<protocol notice title>" \
  --slug <short_slug> \
  --body-file <markdown_notice_file> \
  --summary-json <optional_summary_json> \
  --json-only
```

The command resolves `<pack>/runtime/protocol-feedback/inbox-from-protocol` from
catalog + identity and auto-links refs into `evidence-index/INDEX.md`.

## Metrics (Protocol Constants)

- `HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE = 0.95`
- `HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE = 1.0`
- `HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE = 1.0`
- `HOST_VISIBLE_FALSE_GREEN_MAX_RATE = 0.0`
- `HOST_GATEWAY_WRAPPER_TEMPLATE_CANONICAL_LATEST_REQUIRED_RATE = 1.0`
- `PROTOCOL_FEEDBACK_OUTBOX_CANONICAL_RATE = 1.0`
- `PROTOCOL_FEEDBACK_INBOX_CANONICAL_RATE = 1.0`
- `PROTOCOL_FEEDBACK_INDEX_LINKAGE_REQUIRED_RATE = 1.0`

These thresholds are contract-level and must remain fail-close.
