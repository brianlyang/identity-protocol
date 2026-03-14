# Protocol Remediation Audit Ledger (v1.6.8 downsink path immutability stream)

Status: Active (implementation replay verified on 2026-03-14)  
Scope: protocol-only review ledger for path immutability of all protocol-governed downsink assets.

## 0) Stream objective

1. Freeze all protocol-governed downsink paths into a machine-verifiable registry.
2. Convert path governance from “convention” to “fail-close contract + required CI probes”.
3. Keep v1.6.6 wrapper channel and v1.6.7 cross-layer uniqueness contracts intact while adding path immutability closure.

## 1) Problem statement frozen for audit

1. Gate/broadcast/protocol-feedback have canonical path intent but uneven immutability strength.
2. Contract-consistent path drift can still occur if write surfaces are not registry-bound.
3. Without mandatory negative probes, path drift regressions can become false-green.

## 2) Files planned for implementation phase (v1.6.8)

### 2.1 New or updated protocol scripts (planned)

1. `validate_protocol_downsink_path_immutability` (new validator entrypoint)
2. `validate_protocol_downsink_path_write_guard` (new validator entrypoint)
3. `validate_protocol_downsink_path_literal_lock` (new validator entrypoint)
4. `downsink_path_immutability_probe_runner` (new CI probe runner entrypoint)
4. `create_identity_pack` (update: skeleton + materialization)
5. `repair_contract_backfill` (update: backfill contract/path registry)

### 2.2 New/updated contracts and docs (planned)

1. `protocol_downsink_path_immutability_contract_v1` in `CURRENT_TASK.json`
2. runtime mirror of the same registry block under canonical gate/runtime contract path
3. governance + review stream docs (this file + v1.6.8 governance doc)

## 3) Frozen implementation checklist (item-by-item)

### 3.1 Contract layer

1. `protocol_downsink_path_immutability_contract_v1.required == true`
2. `contract_id` and `validator` fields present and canonical
3. `path_registry` has mandatory domains (`runtime_gate`, `runtime_broadcast`, `runtime_protocol_feedback`, `protocol_broadcast_source`)
4. `anchor_policy` forbids parent and symlink escape
5. strict schema rejects additional properties

### 3.2 Materialization layer

1. init/update generates registry-consistent runtime mirror
2. backfill can auto-repair missing registry entries without manual edits
3. registry paths are anchor-resolved (no user hardcoded source literals)

### 3.3 Validation layer

1. immutability validator enforces path canonicality + containment
2. write-guard validator enforces artifact writes inside registered paths
3. source literal lock validator enforces no unregistered governed literals in protocol source
4. `CURRENT_TASK` vs runtime mirror parity enforced

### 3.4 CI layer

1. required workflow executes v1.6.8 path validators
2. required workflow executes negative probe matrix
3. probe failure blocks merge

## 4) Negative probe matrix (must be required)

1. `probe_path_registry_mutation_noncanonical`
   - mutate one canonical path to sibling path
   - expected: `FAIL_REQUIRED`
2. `probe_parent_escape`
   - inject `../` traversal in registry or write target
   - expected: `FAIL_REQUIRED`
3. `probe_symlink_escape`
   - symlink a canonical leaf to external path and emit write
   - expected: `FAIL_REQUIRED`
4. `probe_feedback_nonregistry_write`
   - write FEEDBACK_BATCH into non-canonical directory
   - expected: `FAIL_REQUIRED`
5. `probe_broadcast_nonregistry_receipt`
   - write broadcast receipt outside canonical reports pattern
   - expected: `FAIL_REQUIRED`
6. `probe_unregistered_literal_fail`
   - inject unregistered governed literal path
   - expected: `FAIL_REQUIRED`

## 5) Positive probe matrix (serial)

1. canonical gate paths pass immutability validator
2. canonical broadcast state/receipt/ack paths pass write-guard
3. canonical protocol-feedback outbox/index/proposals pass write-guard
4. parity between declaration and runtime mirror passes
5. all positive probes pass in at least 5 serial rounds

## 6) Audit verdict rules (frozen)

1. **Policy PASS** requires:
   - governance/review docs registered + allowlist + docs gates pass.
2. **Implementation PASS** requires:
   - checklist 3.x complete
   - negative probe matrix all red-as-expected
   - positive probe matrix all green
   - serial replay evidence complete.
3. If any required item remains open, stream verdict remains:
   - `Policy PASS / Implementation CONDITIONAL_PASS`

## 7) Evidence contract for this stream

Evidence root pattern (strict docs):

1. `activity/evidence/v168-path-immutability/<YYYY-MM-DD>/EVIDENCE_MANIFEST.*.json`
2. `activity/evidence/v168-path-immutability/<YYYY-MM-DD>/*_summary.json`
3. `activity/evidence/v168-path-immutability/<YYYY-MM-DD>/path_registry_snapshot.*.json`
4. `activity/evidence/v168-path-immutability/<YYYY-MM-DD>/path_probe_matrix.*.json`
5. `activity/evidence/v168-path-immutability/<YYYY-MM-DD>/ci_required_probe_report.*.json`

## 8) Dialogue-derived baseline (2026-03-14, frozen)

1. Governance agreement: protocol-governed downsink paths must be fixed and non-negotiable.
2. Implementation rule: changes land through protocol tooling (creator/installer/backfill), not instance hand wiring.
3. Runtime interpretation: project/global layer support remains, but path immutability applies in both layers.
4. Broadcast and protocol-feedback are representative domains; rule scope is generic to future governed domains.

## 9) Stream continuity alias pointers

1. `identity/protocol/mappings/contract-binding.current.yaml`
2. `identity/protocol/mappings/control-plane-status.current.yaml`
3. `identity/protocol/mappings/control-plane-invariants.current.yaml`
4. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
5. `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 10) Implementation landing + serial replay closure (2026-03-14)

### 10.1 Landed code surfaces

1. Contract generation/materialization:
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
2. New validators:
   - `scripts/validate_protocol_downsink_path_immutability.py`
   - `scripts/validate_protocol_downsink_path_write_guard.py`
   - `scripts/validate_protocol_downsink_path_literal_lock.py`
3. Required workflow + probe runner:
   - `.github/workflows/_identity-required-gates.yml`
   - `scripts/ci/run_downsink_path_immutability_probes_ci.sh`
4. Runtime/deep-scan integration:
   - `scripts/identity_creator.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`

### 10.2 Serial replay evidence (meets 5 + 5 requirement)

1. Self-test 5 rounds (serial):
   - `activity/evidence/v168-path-immutability/2026-03-14/selftest_overview_summary.json`
2. Deep-scan 5 rounds (serial):
   - `activity/evidence/v168-path-immutability/2026-03-14/deep_scan_overview_summary.json`
3. Required CI negative probe matrix:
   - `activity/evidence/v168-path-immutability/2026-03-14/path_probe_matrix.v168.20260314.json`
   - `activity/evidence/v168-path-immutability/2026-03-14/ci_required_probe_report.v168.20260314.json`
   - Includes `probe_unregistered_literal_fail` for anti-forget source literal lock.
4. Registry parity snapshot:
   - `activity/evidence/v168-path-immutability/2026-03-14/path_registry_snapshot.v168.20260314.json`
5. Unified manifest:
   - `activity/evidence/v168-path-immutability/2026-03-14/EVIDENCE_MANIFEST.v168.20260314.json`

### 10.3 Verdict

1. Policy verdict: `PASS`.
2. Implementation verdict: `PASS`.
3. Stream conclusion: v1.6.8 path immutability closure is landed and replay-verified under serial constraints, including anti-forget literal lock.

## 11) Requirement mapping closure motherline v1.6.8

### 11.1 Closure objective (frozen)

1. 将 v1.6.8 downsink 三个验证器从“侧链显式调用”提升为 `contract-binding.current.yaml` 母线 requirement rows；
2. 将 coverage 判定从“单文档硬编码（v1.6.0）”升级为“stream registry 动态解析 + stream_version 正则校验”；
3. 保证后续版本（v1.6.9 / v1.7.x）新增 stream 时，系统自动拦截漏接线，而不是依赖记忆。

### 11.2 Requirement rows integrated

| Requirement ID | Mapping Key | Validator | Status |
| --- | --- | --- | --- |
| ASB16-RQ-036 | asb16-rq-036 | scripts/validate_protocol_downsink_path_immutability.py | integrated |
| ASB16-RQ-037 | asb16-rq-037 | scripts/validate_protocol_downsink_path_write_guard.py | integrated |
| ASB16-RQ-038 | asb16-rq-038 | scripts/validate_protocol_downsink_path_literal_lock.py | integrated |

### 11.3 Audit pass criteria

1. `validate_control_plane_invariants`: `mapping_rows_missing_in_bundle_count == 0`.
2. `validate_contract_mapping_coverage --force-required`: `contract_mapping_coverage_status == PASS_REQUIRED` with no alias or stream-version error.
3. `docs_command_contract_check` + `validate_doc_evidence_persistence`: stream-registry format checks pass (including `stream_version` regex validation).

## 12) Serial replay refresh (2026-03-14, motherline-r2)

### 12.1 Infrastructure replay (5 rounds self-test, serial)

Evidence:

1. `activity/evidence/v168-path-immutability/2026-03-14/selftest_motherline_overview_summary.json`
2. `activity/evidence/v168-path-immutability/2026-03-14/selftest_motherline_round_01_summary.json` ... `_05_...`

Observed result:

1. `round_count=5`
2. `overall_passed=true`
3. Every round passes:
   - contract backfill
   - downsink immutability validator
   - downsink write-guard validator
   - downsink literal-lock validator
   - dynamic mapping coverage validator (`--force-required`)

### 12.2 Deep-scan replay (5 rounds, serial)

Evidence:

1. `activity/evidence/v168-path-immutability/2026-03-14/deep_scan_motherline_overview_summary.json`
2. `activity/evidence/v168-path-immutability/2026-03-14/deep_scan_motherline_round_01_summary.json` ... `_05_...`

Observed result:

1. `round_count=5`
2. Target instance (`base-repo-architect`) remains stable at `p0=1` for all rounds.
3. Interpretation: infrastructure motherline closure is validated; target runtime debt remains explicit (not hidden by governance greenwashing).

### 12.3 Probe + registry artifacts (r2 snapshot)

1. `activity/evidence/v168-path-immutability/2026-03-14/path_probe_matrix.v168.20260314-r2.json`
2. `activity/evidence/v168-path-immutability/2026-03-14/ci_required_probe_report.v168.20260314-r2.json`
3. `activity/evidence/v168-path-immutability/2026-03-14/path_registry_snapshot.v168.20260314-r2.json`
4. `activity/evidence/v168-path-immutability/2026-03-14/EVIDENCE_MANIFEST.v168.20260314-r2.json`

## 13) Round-31.1 addendum: host-visible live receipt source/state attestation hardening (2026-03-14)

### 13.1 Audit conclusion

1. Host-visible live coverage checks are upgraded from “receipt presence” to “receipt + runtime state parity + source attestation”.
2. Session-chain wrapper now fail-closes when host-visible runtime receipt emission is not `PASS_REQUIRED`.
3. CI fixture probes remain deterministic through explicit source allowlist extension, without weakening production defaults.

### 13.2 Fix set audited

1. `scripts/create_identity_pack.py`
   - session-chain wrapper now records host-visible runtime receipts and blocks on non-pass status (`IP-HDSTAMP-003` path).
2. `scripts/validate_host_transport_wiring_attestation.py`
   - adds `--allowed-live-receipt-sources`.
   - verifies both receipt payload and `host_visible_surface_registry_state.json` channel parity.
3. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - writes fixture receipts with `receipt_source=ci_fixture`.
   - writes matching state mirror entries.
   - executes validator with explicit allowlist `runtime_dialogue,ci_fixture`.

### 13.3 Replay evidence

1. `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - `host_visible_contract_static`: `PASS`
   - `host_visible_live_receipts_pass`: `PASS`
   - `host_visible_commentary_bypass_blocked`: expected block (`rc=1`)
2. Probe manifest:
   - `/private/var/folders/.../identity-host-visible-surface-probes/manifest.host_visible_surface_live.json`

### 13.4 Boundary statement

1. This addendum strengthens v1.6.8 infra-level host-visible provenance checks.
2. It does not claim closure of unrelated instance business debt.
3. Verdict impact: infrastructure hardening improved; stream closure remains tied to full motherline gate outcomes.

## 14) Round-31.2 addendum: protocol-feedback SSOT index auto-repair + summary segregation (2026-03-14)

### 14.1 Audit conclusion

1. `IP-GOV-FEEDBACK-002` linkage drift is now repairable through protocol tooling, not manual index editing.
2. Full-scan summary now isolates active runtime from fixture/non-active lanes to avoid closure noise.
3. Requested session binding is enforced only on active runtime rows, preventing false P0 in mixed-layer target scans.

### 14.2 Fix set audited

1. `scripts/repair_protocol_feedback_ssot_index.py` (new)
   - appends missing outbox batch links to protocol-feedback index using contract-driven roots.
2. `scripts/identity_creator.py`
   - update path includes mandatory `repair_protocol_feedback_ssot_index --apply`.
   - heal/validate fallback now auto-runs the same repair when `IP-GOV-FEEDBACK-002` is detected.
3. `scripts/full_identity_protocol_scan.py`
   - adds summary buckets:
     - `summary_runtime_active`
     - `summary_fixture_or_demo`
     - `summary_non_active_or_non_runtime`
   - requested session-binding hard-fail now applies only to active runtime rows.

### 14.3 Replay evidence

1. protocol-feedback repair tool probe (synthetic root):
   - `protocol_feedback_ssot_index_repair_status=PASS_REQUIRED`
   - `appended_batch_links=1`
   - `index_unlinked_batches_after=0`
2. full-scan mixed-layer replay (`base-repo-architect`, source-layer both):
   - `summary.p0=0`
   - `summary_runtime_active.ok=1`
   - `summary_non_active_or_non_runtime.ok=1`
   - inactive row no longer triggers requested-session-binding P0.
3. update integration smoke replay (`custom-creative-ecom-analyst`):
   - `identity_creator.py update` returns `rc=0` with in-band SSOT index repair path executed.

### 14.4 Three-plane structured closure axes

1. `scripts/report_three_plane_status.py` now emits:
   - `governance_closure_axes.infrastructure_closure_status`
   - `governance_closure_axes.runtime_readiness_status`
   - `governance_closure_axes.release_readiness_status`
   - `governance_closure_axes.decision_mode`
   - `governance_closure_axes.conditional_reasons`
2. This converts “Conditional Go” from textual-only output to machine-consumable closure axes.
