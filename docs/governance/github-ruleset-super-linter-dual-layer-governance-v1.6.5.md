# GitHub Rulesets + Super-Linter Dual-Layer Governance (v1.6.5)

Status: Active (pre-development governance freeze)  
Layer: protocol  
Scope: platform-native file-governance offload + repository lint hardening with semantic fail-close retention

Execution mode: topic-level canonical SSOT for v1.6.5 dual-layer control-plane hardening.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.5 dual-layer hardening.
2. Historical statements in v1.6.0-v1.6.4 remain valid only when not superseded by this stream.
3. Current-state judgment must prioritize machine outputs from:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. `/tmp/*` and ad-hoc logs are replay artifacts only and are never normative contract input.
5. Normative mapping entrypoints are current-pointer files only:
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`

## 1) Why v1.6.5 exists

v1.6.3 established GitHub-native control-plane direction and v1.6.4 stabilized monotonic semantic gates.  
The remaining optimization target is execution efficiency with strict anti-bypass behavior:

1. Platform-expressible controls (path/extension/size restrictions) should be enforced by GitHub rulesets, not hand-rolled repo scripts.
2. Repo-plane syntactic/format governance should be concentrated into one stable check surface (super-linter), not fragmented ad-hoc lint scripts.
3. Protocol semantic contracts (`asb16-rq-019`, `asb16-rq-034`, `asb16-rq-035`) must remain in repository validators and are not offload candidates.
4. Business preflight latency should stay bounded (`P95 < 3 minutes`) while strict release lanes remain fail-close.

## 2) v1.6.5 architecture contract (dual-layer, no ambiguity)

### 2.1 Layer split contract

1. **Platform layer (GitHub rulesets / branch policy)** handles:
   - branch merge policy
   - required checks binding
   - file path restrictions
   - file extension restrictions
   - file size restrictions
2. **Repository layer (super-linter + protocol validators)** handles:
   - syntax/format consistency for changed files
   - protocol semantic contracts and fail-close logic
   - control-plane mapping/document parity checks
3. Any control that can be represented faithfully by rulesets must not be duplicated as bespoke repo enforcement unless redundancy is explicitly justified.

### 2.2 Offload boundary (retain semantic contracts)

Repo-retained semantic contracts remain mandatory:

1. `asb16-rq-019` (`scripts/required_gate_bundle_runner.py`)
2. `asb16-rq-034` (`scripts/validate_multimodal_plugin_enforcement.py`)
3. `asb16-rq-035` (`scripts/validate_reasoning_loop_failclose.py`)

No offload action may weaken these semantics or downgrade `FAIL_REQUIRED` behavior.

### 2.3 Single-configuration entry contract

For v1.6.5 planning and execution, mutation intent must be anchored in:

1. `identity/protocol/mappings/github-control-plane-offload.current.yaml`
2. `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`
5. `docs/review/protocol-remediation-audit-ledger-v1.6.5.md`

Hard boundary:

1. Workflow/script hardcoded one-off policy that bypasses mapping intent is invalid.
2. If mapping and document intent diverge, mapping+required-gate outputs win.

## 3) Section-3 execution contract (newcomer/recall safe)

### 3.0 Role lock (why this section exists)

1. Section 3 is the execution checklist for newcomer handoff and memory-loss recovery.
2. This checklist is triggered on governance mutation/update/review actions, not per-round chat runtime.
3. Runtime per-round wrapper enforcement remains the v1.6.6 scope; v1.6.5 Section 3 guarantees operators can always recover the correct governance actions from machine-checkable steps.
4. No closure claim is valid if Section 3 cannot be executed by a fresh operator without tribal-memory assumptions.

### 3.1 Minimal fixed profile (avoid sprawl)

Super-linter must run with a fixed narrow profile first:

1. changed-files scope only (`VALIDATE_ALL_CODEBASE=false`)
2. governance-critical paths prioritized:
   - `.github/workflows/**`
   - `identity/protocol/**`
   - `docs/governance/**`
   - `docs/review/**`
3. initial validator family:
   - YAML
   - JSON
   - Markdown
   - GitHub Actions workflow syntax
4. check name must remain stable across `pull_request` + `merge_group` surfaces so required-check bindings do not drift.

### 3.2 Health + wiring contract (machine-first)

Section-3 completion requires both health and wiring proofs:

1. Machine health checks must stay green:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
2. Required-gate workflow must include fixed-profile super-linter and delegated required-runtime gate lane (`scripts/ci/run_required_runtime_gates_ci.sh`) as auditable wiring surface.
3. Drift/invariant validators must fail-close if super-linter/check-name/wiring tokens are missing or renamed.
4. This contract is the attach-ready prerequisite for v1.6.6 unique-entry governance hooks (health broadcast, gate wiring, and status publication).

### 3.2.1 Runtime SLO guard (front-door loop)

1. Pre-merge business preflight target: `P95 < 3 minutes`.
2. If profile expansion breaks this bound, expansion must be rolled back or split into non-blocking lanes before re-promotion.
3. Release lanes may remain heavier; this SLO applies to front-door developer feedback loop.

### 3.3 Supply-chain control contract

1. super-linter action references must be pinned and policy-reviewed.
2. ruleset required-check binding must use stable check names to avoid merge-queue/required-check drift.
3. action source policy (GitHub-owned/verified/pinning strategy) remains governed by offload mapping and platform receipts.

### 3.4 Governance broadcast-readiness contract (for downstream runtime hooks)

1. Section 3 must keep stream docs, allowlist, and control-plane status pointers machine-synchronized so runtime wrappers can consume one current governance state.
2. Required-gate outcomes must publish canonical statuses/error families (not ad-hoc log text) for deterministic downstream broadcast and recovery guidance.
3. Broadcast source paths are fixed protocol paths and must not drift:
   - `identity/protocol/broadcast/items`
   - `identity/protocol/broadcast/index.json`
   - `identity/protocol/broadcast/schema/broadcast-item.v1.json`
4. Broadcast runtime state/receipts are fixed instance paths:
   - `runtime/state/broadcast_state.json`
   - `runtime/reports/broadcast/broadcast-receipt-*.json`
   - `runtime/reports/broadcast/broadcast-ack-*.json`
5. Broadcast state machine must be machine-verifiable:
   - ingress updates `visible/unread/pending_ack/critical_unacked`
   - `identity_broadcast_ack.py` consumes pending IDs and writes ack receipt
   - next ingress reflects ack delta (`pending_ack`/`critical_unacked` converge)
6. If Section-3 status is stale, pointer-drifted, or broadcast contract breaks, downstream runtime broadcast is non-authoritative and release posture remains `CONDITIONAL_GO`.

### 3.5 Canonical configuration scheme (explicit, one-to-one)

Section-3 execution must use contract-driven config, not ad-hoc script parameters.

Minimal `CURRENT_TASK.json` fragment (identity pack):

```json
{
  "protocol_host_unique_channel_contract_v1": {
    "protocol_ingress_script": "scripts/required_gate_bundle_runner.py",
    "protocol_egress_script": "scripts/final_emit_governed.py",
    "ingress_wrapper_path": "identity/runtime/gate/protocol_ingress_wrapper.py",
    "egress_wrapper_path": "identity/runtime/gate/protocol_egress_wrapper.py",
    "gateway_contract_path": "identity/runtime/gate/protocol_gateway_contract.json",
    "host_dispatch_mode": "wrapper_only",
    "host_release_mode": "wrapper_only",
    "entry_receipt_policy": {
      "required": true,
      "required_surface_label": "host_ingress_wrapper",
      "required_wrapper_surface_status": "PASS_REQUIRED",
      "required_wrapper_dispatch_token_status": "PASS_REQUIRED"
    },
    "ingress_proof_policy": {
      "required": true,
      "max_age_seconds": 300,
      "signer_mode": "runtime_env_secret",
      "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_<IDENTITY>"
    },
    "egress_grant_policy": {
      "required": true,
      "max_age_seconds": 300,
      "signer_mode": "runtime_env_secret",
      "signer_secret_env": "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_<IDENTITY>"
    },
    "headstamp_policy": {
      "required": true
    },
    "operation_profile_policy": {
      "strict_operations": ["activate", "update", "mutation", "readiness", "e2e", "ci", "validate", "three-plane"],
      "light_operations": ["inspection", "scan"],
      "strict_gate_profile": "strict_full",
      "light_gate_profile": "inspection_targeted",
      "allow_upgrade_only": true
    },
    "broadcast_policy": {
      "required": true,
      "protocol_broadcast_items_dir": "identity/protocol/broadcast/items",
      "protocol_broadcast_index_file": "identity/protocol/broadcast/index.json",
      "protocol_broadcast_schema_file": "identity/protocol/broadcast/schema/broadcast-item.v1.json",
      "instance_state_file": "identity/runtime/state/broadcast_state.json",
      "instance_receipt_pattern": "runtime/reports/broadcast/broadcast-receipt-*.json",
      "instance_ack_pattern": "runtime/reports/broadcast/broadcast-ack-*.json",
      "block_on_critical_unacked": false
    }
  }
}
```

Minimal `.identity/<id>/runtime/gate/protocol_gateway_contract.json` fragment:

```json
{
  "protocol_ingress_script": "scripts/required_gate_bundle_runner.py",
  "protocol_egress_script": "scripts/final_emit_governed.py",
  "host_dispatch_mode": "wrapper_only",
  "host_release_mode": "wrapper_only",
  "entry_receipt_policy": {
    "required": true
  },
  "ingress_proof_policy": {
    "required": true,
    "max_age_seconds": 300
  },
  "egress_grant_policy": {
    "required": true,
    "max_age_seconds": 300
  },
  "headstamp_policy": {
    "required": true
  },
  "operation_profile_policy": {
    "strict_gate_profile": "strict_full",
    "light_gate_profile": "inspection_targeted",
    "allow_upgrade_only": true
  },
  "broadcast_policy": {
    "required": true,
    "protocol_broadcast_items_dir": "identity/protocol/broadcast/items",
    "protocol_broadcast_index_file": "identity/protocol/broadcast/index.json",
    "protocol_broadcast_schema_file": "identity/protocol/broadcast/schema/broadcast-item.v1.json",
    "instance_state_file": "runtime/state/broadcast_state.json",
    "instance_receipt_pattern": "runtime/reports/broadcast/broadcast-receipt-*.json",
    "instance_ack_pattern": "runtime/reports/broadcast/broadcast-ack-*.json",
    "block_on_critical_unacked": false
  }
}
```

### 3.6 Three-layer health-check recipe (command-level, serial closure)

1. Contract/static layer (schema + parity):
   - `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
2. Routing/dynamic layer (positive + negative probes):
   - `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
3. Session layer (tuple + headstamp/send-time continuity on required surfaces):
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`

Interpretation lock:

1. Any layer fails => Section-3 execution pack is not closed.
2. Layer-1 only green is not accepted as runtime attach-readiness closure.
3. Mandatory serial self-test loop (`>=5` rounds, no parallel):
   - `repair_contract_backfill --apply`
   - `validate_protocol_unique_entry_gate --force-check`
   - `protocol_ingress_wrapper.py` (observe broadcast counters + receipt write)
   - `identity_broadcast_ack.py --ack-all-pending`
   - `protocol_ingress_wrapper.py` again (verify pending/critical converge after ack)
4. Mandatory serial deep-scan loop (`>=5` rounds, no parallel):
   - `validate_control_plane_invariants.py --json-only`
   - `validate_required_gate_surface_drift.py --json-only`
   - `validate_control_plane_status_sync.py --json-only`
   - `validate_doc_evidence_persistence.py --json-only`
   - `validate_protocol_unique_entry_gate.py --operation scan --force-check --json-only`
5. `full_identity_protocol_scan --scan-mode target` is diagnostic for this stream; it is recorded as supplemental evidence and must not replace the five mandatory deep-scan rounds above.

### 3.7 One-to-one traceability matrix (frozen)

| Governance intent | Required config keys | Canonical scripts/surfaces | Machine verdict source | Closure condition |
|---|---|---|---|---|
| Unique ingress/egress ownership | `protocol_ingress_script`, `protocol_egress_script`, `host_dispatch_mode`, `host_release_mode` | `scripts/required_gate_bundle_runner.py`, `scripts/final_emit_governed.py` | `validate_protocol_unique_entry_gate` | both modes are `wrapper_only` and scripts match canonical |
| Health checks (3-layer) | `entry_receipt_policy`, `ingress_proof_policy`, `egress_grant_policy`, `headstamp_policy` | `validate_protocol_unique_entry_gate`, `run_gateway_wrapper_trust_boundary_probes_ci.sh`, required-gates workflow | `PASS_REQUIRED` + negative probes blocked | static+dynamic+session all pass |
| Wiring (no hardcode) | `operation_profile_policy`, current-pointer mappings | `.github/workflows/_identity-required-gates.yml`, `validate_required_gate_surface_drift.py` | drift/invariant/status checks | missing tokens/renames fail-close |
| Broadcast attach readiness | `broadcast_policy` fixed protocol paths + instance state/receipt/ack patterns | ingress wrapper snapshot + `identity_broadcast_ack.py` + egress release state | `validate_protocol_unique_entry_gate` + ingress/ack receipts | unread/pending/critical counters and ack receipts stay machine-parseable with fixed paths |
| Acceptance metrics | same as above + evidence tuples | stream docs + allowlist + status mappings | command + rc + sha256 + timestamp | any metric below threshold => `CONDITIONAL_GO` |

## 4) GitHub rulesets hardening contract

### 4.1 Required control set for v1.6.5

1. restrict high-risk file extensions
2. restrict non-governed file paths for protocol-critical branch
3. restrict oversized files in critical paths
4. keep required check binding stable (`required-gates / validate-identity` + super-linter check once enabled)
5. preserve required PR/code-owner review behavior from v1.6.3 activation baseline

### 4.2 Merge-queue compatibility guard

1. `merge_group` trigger coverage in CI workflows must stay present and drift-checked.
2. If platform `merge_queue` rule capability remains unavailable for this repository, status must remain explicitly tracked as platform exception in offload mapping receipts (no silent omission).

## 5) Evidence and auditability contract

1. Governance/review evidence must use persistent paths only:
   - `activity/evidence/<stream>/<date>/...`
   - `.identity/<id>/runtime/reports/...`
2. `/tmp` cannot be the sole evidence path in governance documents.
3. Evidence rows must keep tuple fields:
   - `sha256`
   - `command`
   - `rc`
   - `timestamp`
4. Evidence references in strict stream docs must match:
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`

## 6) Cross-verification synthesis (roundtable + vendor + network + reference + context7)

### T1 Roundtable (repo-machine)

1. v1.6.3 platform offload foundations are active in mapping and workflow surfaces.
2. v1.6.4 semantic hardening gates are wired and retained.
3. Current optimization opportunity is governance complexity reduction without semantic dilution.

### T2 Vendor (GitHub + OpenAI)

1. GitHub rulesets support repository-native restrictions (path/extension/size, required checks, PR controls).
2. GitHub merge queue/required checks documentation confirms `merge_group` trigger compatibility requirement.
3. OpenAI Codex GitHub Action security checklist reinforces narrow triggers, explicit boundaries, and policy-safe automation.

### T3 Network/platform references

1. Rulesets composition semantics follow restrictive layering model.
2. Required-check troubleshooting guidance confirms skipped/pending states can block merges and therefore check naming stability is mandatory.

### T4 Protocol reference anchors

1. `identity/protocol/mappings/github-control-plane-offload.current.yaml`
2. `scripts/validate_control_plane_invariants.py`
3. `scripts/validate_required_gate_surface_drift.py`
4. `.github/workflows/_identity-required-gates.yml`
5. `scripts/docs_command_contract_check.py`

### T5 Context7 track

1. GitHub Actions trigger semantics in Context7 corpus align with merge-group compatibility guard.
2. MCP capability/change-notification model supports explicit control-plane capability surfaces rather than implicit behavior drift.

## 7) v1.6.5 phase plan

### Phase A — governance/review freeze (this checkpoint)

1. lock stream contract and acceptance criteria
2. register stream docs and alias requirements
3. register strict evidence allowlist for stream docs

### Phase B — repository implementation

1. add super-linter required check with fixed minimal profile
2. wire drift/invariant checks for new lint surface
3. keep semantic fail-close validators unchanged except wiring updates needed for check integration

### Phase C — platform activation

1. apply/verify ruleset restrictions (path/extension/size)
2. bind stable required checks in ruleset
3. capture activation receipts in offload mapping

## 8) Release gate for v1.6.5 claim

No “v1.6.5 closed” claim is valid unless all items pass:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. super-linter required check green on PR + merge-group compatible surface
6. ruleset receipts updated for path/extension/size controls (or explicit platform exception recorded)
7. Section-3 serial self-test loop (`>=5` rounds) completed in strict order with broadcast ack closure evidence.
8. Section-3 serial deep-scan loop (`>=5` rounds) completed in strict order with all mandatory rounds `PASS/PASS_REQUIRED`.

Interpretation lock:

1. v1.6.5 governance model suitability can be judged `YES` once sections 2-4 are accepted.
2. v1.6.5 stream closure can be judged `CLOSED` only when all 8 release gates above are green.
3. If only items 1-4 are green while 5-8 are pending, status must be `CONDITIONAL_GO` (never “fully closed”).

### 8.1 Status artifact truthfulness contract (mandatory)

1. `identity/protocol/mappings/control-plane-status.v1.6.json` is a machine-generated mirror, not a manual narrative file.
2. Whenever live checks change (including transitions to `FAIL_REQUIRED`), status file must be regenerated by:
   - `python3 scripts/render_control_plane_status.py --write --json-only`
3. `validate_control_plane_status_sync.py` is required to fail-close on any drift between:
   - live check outputs, and
   - persisted status artifact fields.
4. Persisting stale green status while live checks fail is non-compliant with v1.6.5 governance.

### 8.2 Budget baseline sync contract (mandatory)

1. `identity/protocol/mappings/control-plane-budget.v1.6.yaml` is a machine-maintained control-plane budget artifact and must stay synchronized with live observed metrics after approved control-plane expansions.
2. Manual ad-hoc edits are not accepted as the default maintenance path; budget refresh must be executed through:
   - `python3 scripts/render_control_plane_budget.py --write --json-only`
3. Budget refresh is valid only when followed by live validator replay:
   - `python3 scripts/validate_control_plane_budget.py --json-only`
   - `python3 scripts/render_control_plane_status.py --write --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. Any budget refresh must remain stream-governed:
   - update this governance doc and its paired review ledger in the same stream PR,
   - keep one-stream-per-PR boundary green via `validate_stream_version_pr_boundary.py`.
5. No hardcoded stream branching is allowed in budget tooling; active mappings must resolve through `*.current.yaml` aliases.
6. If control-plane core scripts evolve in adjacent streams and trigger no-rebound ceiling drift, v1.6.5 budget/status mirrors must be resynchronized immediately via renderer + status mirror flow in the same checkpoint (never deferred to later manual cleanup).

### 8.3 Status mirror refresh contract after delegated probe growth (mandatory)

1. Any approved expansion of required-gate delegate probes that changes observed control-plane counters (for example `required_gate_delegate_inclusive_*`) must trigger a status mirror refresh in the same stream PR.
2. The refresh path is always machine-generated and alias-resolved:
   - `python3 scripts/render_control_plane_status.py --write --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
3. Persisting outdated counter snapshots after delegated probe growth is non-compliant, even if the final status remains `PASS_REQUIRED`.
4. Stream closure reporting must cite the refreshed status artifact (`control-plane-status.current.yaml` -> active file) and keep one-stream-per-PR boundary green.

### 8.4 Rebound absorber contract for adjacent-stream growth (mandatory)

1. v1.6.5 no-rebound guard remains authoritative even when observed telemetry growth originates from adjacent streams (for example v1.6.6/v1.6.8 core-gate additions).
2. Any rebound that pushes live counters above the current no-rebound ceiling must be absorbed by the canonical renderer flow in the same checkpoint:
   - `python3 scripts/render_control_plane_budget.py --write --json-only`
   - `python3 scripts/render_control_plane_status.py --write --json-only`
3. The absorber checkpoint is valid only when serial validators all return pass:
   - `python3 scripts/validate_control_plane_budget.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. One-stream-per-PR boundary remains mandatory:
   - rebound absorption updates must stay in the v1.6.5 stream doc pair and pass `validate_stream_version_pr_boundary.py`.

### 8.5 Rebound re-entry handling contract (mandatory)

1. rebound absorption is iterative by design: if live telemetry grows again after a valid absorber checkpoint, the same renderer+validator sequence must be replayed immediately.
2. re-entry absorption must stay machine-generated and alias-resolved; manual literal counter edits are non-compliant.
3. each re-entry checkpoint must be recorded in the paired review ledger with:
   - observed delta,
   - replay commands,
   - pass evidence.
4. status payload-level drifts (for example `checks.control_plane_budget.payload`) are part of the same mirror contract and require immediate renderer resync in the same checkpoint.

### 8.6 Invariant-coupled rebound handling (mandatory)

1. if rebound is caused by mapping row growth (for example new motherline requirement rows), absorber replay must include invariants parity, not only budget/status pair:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
2. when `contract_binding_meta_row_count != contract_binding_actual_row_count`, closure is invalid until:
   - mapping meta is corrected in the authoritative mapping file,
   - budget + status mirrors are re-rendered,
   - budget/status/invariants all return `PASS_REQUIRED`.
3. this clause is still v1.6.5 scope because it is a control-plane no-rebound closure behavior, independent from whichever adjacent stream introduced the row growth.

### 8.7 Skill supply-chain absorber contract (motherline RQ-039..041, mandatory)

1. skill supply-chain controls (`installation/frontmatter/sync-drift`) are absorbed into v1.6.5 no-rebound governance and must not be attached to v1.6.10 stream semantics.
2. motherline requirement rows:
   - `asb16-rq-039` -> `rq_039_skill_installation_supply_chain_contract_v1`
   - `asb16-rq-040` -> `rq_040_skill_frontmatter_contract_v1`
   - `asb16-rq-041` -> `rq_041_skill_sync_drift_guard_contract_v1`
3. absorber replay for this set must satisfy the same canonical sequence:
   - `python3 scripts/render_control_plane_budget.py --write --json-only`
   - `python3 scripts/render_control_plane_status.py --write --json-only`
   - `python3 scripts/validate_control_plane_budget.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
4. stream boundary lock:
   - v1.6.10 remains reserved for runtime dynamic file governance;
   - skill supply-chain contract closure evidence belongs to v1.6.5 governance/review pair.

## 9) External references

1. GitHub rulesets available rules:
   - https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
2. GitHub rulesets overview:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
3. GitHub required status checks troubleshooting:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/troubleshooting-required-status-checks
4. GitHub merge queue:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
5. GitHub Actions `merge_group` event:
   - https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group
6. OpenAI Codex GitHub Action security checklist:
   - https://developers.openai.com/codex/github-action/#security-checklist
7. Super-linter documentation:
   - https://github.com/super-linter/super-linter
