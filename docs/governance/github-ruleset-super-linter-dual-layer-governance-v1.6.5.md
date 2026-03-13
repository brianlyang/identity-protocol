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
3. If Section-3 status is stale or pointer-drifted, downstream runtime broadcast is treated as non-authoritative and release posture remains `CONDITIONAL_GO`.

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

Interpretation lock:

1. v1.6.5 governance model suitability can be judged `YES` once sections 2-4 are accepted.
2. v1.6.5 stream closure can be judged `CLOSED` only when all 6 release gates above are green.
3. If only items 1-4 are green while 5-6 are pending, status must be `CONDITIONAL_GO` (never “fully closed”).

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
