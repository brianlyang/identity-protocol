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

## Metrics (Protocol Constants)

- `HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE = 0.95`
- `HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE = 1.0`
- `HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE = 1.0`
- `HOST_VISIBLE_FALSE_GREEN_MAX_RATE = 0.0`

These thresholds are contract-level and must remain fail-close.
