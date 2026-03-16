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

1. Promote the v1.6.8 downsink validator trio from side-route explicit calls into motherline requirement rows in `contract-binding.current.yaml`.
2. Upgrade coverage validation from single-doc hardcoding to dynamic stream-registry resolution plus `stream_version` regex enforcement.
3. Ensure future streams (for example `v1.6.9`, `v1.7.x`) are protected by automatic wiring checks rather than memory-based process discipline.

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

## 15) Round-31.3 addendum: one-stream-per-PR boundary enforcement (2026-03-14)

### 15.1 Audit objective

1. Convert "one stream per PR" from recommendation to required CI policy.
2. Reject multi-stream or anchor-missing PR ranges in fail-close mode.
3. Keep enforcement dynamic and alias-driven (no stream hardcoding).

### 15.2 Landed implementation

1. New validator:
   - `scripts/validate_stream_version_pr_boundary.py`
2. Required CI integration:
   - `.github/workflows/_identity-required-gates.yml`
3. Registry authority:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`

### 15.3 Error-code closure contract

1. `IP-STREAM-PR-001`: core changes without stream-doc anchor.
2. `IP-STREAM-PR-002`: multiple stream versions touched in one range.
3. `IP-STREAM-PR-003`: governance/review pair not both present.
4. `IP-STREAM-PR-004`: stream registry missing or invalid.

Any of these outcomes is `FAIL_REQUIRED` and blocks merge in the required gate workflow.

### 15.4 Replay checklist (serial)

1. `python3 -m py_compile scripts/validate_stream_version_pr_boundary.py`
2. `python3 scripts/validate_stream_version_pr_boundary.py --base <base> --head <head> --json-only`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_doc_evidence_persistence.py --json-only`

### 15.5 Verdict impact

1. v1.6.8 anti-forget governance is strengthened with merge-time mandatory enforcement.
2. Future stream upgrades inherit this policy automatically through registry aliases.

## 16) Round-31.4 addendum: closure-axis semantics + host-visible freshness floor (2026-03-15)

### 16.1 Audit conclusion

1. Three-plane decision semantics are now aligned with tuple-context closure axis.
2. Host-visible live receipt checks now include an explicit runtime freshness window.
3. Handbook continuity is bound into v1.6.8 governance (alias-driven, non-hardcoded).

### 16.2 Fix set audited

1. `scripts/report_three_plane_status.py`
   - `governance_closure_axes.decision_mode=FULL_GO` now requires:
     - infrastructure closed
     - runtime closed
     - release closed
     - tuple context consistency pass
2. Host-visible freshness floor:
   - `scripts/protocol_infra_contract.py`
     - adds `HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS`.
   - `scripts/create_identity_pack.py`
     - host-visible contract skeleton now includes `runtime_receipt_max_age_seconds`.
   - `scripts/validate_host_transport_wiring_attestation.py`
     - validates positive `runtime_receipt_max_age_seconds`.
     - fail-closes stale live receipts:
       - `host_visible_surface_live_channel_receipt_stale:<channel>:age_seconds=<n>:max_age_seconds=<m>`
   - `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
     - adds stale-receipt negative probe.
3. Governance handbook binding:
   - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
     now requires alias-driven handbook linkage via:
     - `PLUGIN_WIRING_PLAYBOOK.current.md`
     - `PLUGIN_DOC_CONTROL.current.yaml`

### 16.3 Replay evidence

1. `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - `host_visible_contract_static`: PASS
   - `host_visible_live_receipts_pass`: PASS
   - `host_visible_receipt_stale_blocked`: expected block
   - `host_visible_commentary_bypass_blocked`: expected block
2. tuple probe suite remains PASS after freshness floor additions:
   - `bash scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`

### 16.4 Verdict impact

1. v1.6.8 now provides consistent machine semantics from scan summary to three-plane decision mode.
2. host-visible runtime freshness is no longer “receipt-presence only”.
3. anti-forget guidance is integrated into governance control surfaces rather than manual memory.

### 16.5 Cross-verification evidence capture hardening (2026-03-15)

Problem:

1. cross-verification statements can degrade into prose-only claims when roundtable/vendor/context7/openai-doc references are not consistently captured.
2. this creates recall risk in later streams even when technical controls are correct.

Fix landed:

1. governance doc now includes an explicit evidence capture contract for:
   - roundtable/internal synthesis,
   - vendor/reference URLs,
   - Context7 retrieval track,
   - OpenAI official doc retrieval track.
2. closure interpretation is tightened:
   - missing ledger-citable evidence refs keeps stream at `Implementation CONDITIONAL_PASS`.

Checkpoint verdict update:

1. v1.6.8 cross-verification is now enforceable as a machine-auditable capture discipline, not memory-dependent narration.

### 16.6 Active-runtime unique-entry migration preflight integration (2026-03-15)

Problem:

1. CI tuple probe coverage can be green while local project active-runtime packs still contain migration debt.
2. This creates a “single identity pass vs global active-runtime pass” interpretation mismatch.

Fix landed:

1. `scripts/identity_creator.py`
   - adds preflight closure helper bound to:
     - `scripts/check_unique_entry_contract_migration_closure.py`
     - `scripts/repair_contract_backfill.py`
2. `validate` operation:
   - executes migration closure check in fail-close mode before required validator bundle.
3. `update` operation:
   - executes migration closure check;
   - auto-repairs violating active runtime identities with protocol toolchain (no manual edits);
   - rechecks closure and blocks update if still non-pass.
4. identity discovery is payload-driven from checker `violations` rows (no hardcoded identity IDs).

Replay:

1. before repair:
   - `check_unique_entry_contract_migration_closure --catalog .identity/catalog.local.yaml --json-only`
   - `FAIL_REQUIRED`, violation identity included `custom-creative-ecom-analyst`.
2. protocol auto-repair command:
   - `repair_contract_backfill.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --apply --json-only`
   - `PASS_REQUIRED`.
3. after repair:
   - same migration closure check returns `PASS_REQUIRED` with zero violations.

Checkpoint verdict update:

1. global active-runtime migration closure can now be enforced from creator preflight path, not only from fixture probes.
2. closure claim semantics are aligned: global claim requires global active-runtime pass.

## 17) Round-32 addendum: version-baseline SSOT closure (2026-03-15)

### 17.1 Problem confirmed

1. Scaffold version fields were drifting across runtime identities (`v1.2.3`, `v1.3`, missing scaffold metadata).
2. Creator/installer paths still relied on hardcoded literals.
3. Existing protocol-version alignment check did not fail-close scaffold tuple drift.

### 17.2 Landed fix set

1. Added alias-driven baseline mapping:
   - `identity/protocol/mappings/version-baseline.current.yaml`
   - `identity/protocol/mappings/version-baseline.v1.6.yaml`
2. Added shared resolver/apply utility:
   - `scripts/version_baseline_common.py`
3. Removed scaffold hardcoded literals from generation/install flows:
   - `scripts/create_identity_pack.py`
   - `scripts/identity_installer.py`
4. Extended protocol backfill to include version tuple normalization across:
   - `CURRENT_TASK.json`
   - runtime catalog row (`methodology_version`)
   - `META.yaml`
   (`scripts/repair_contract_backfill.py`)
5. Extended alignment validator with scaffold-baseline fail-close:
   - `scripts/validate_identity_protocol_version_alignment.py`
   - fail-close branch under `IP-PVA-002` (scaffold-baseline alignment)
6. Added active-runtime migration closure checker:
   - `scripts/check_version_baseline_migration_closure.py`
7. Update flow resilience:
   - `scripts/identity_creator.py` now runs protocol backfill auto-repair when scaffold-baseline branch of `IP-PVA-002` is detected during strict update preflight.

### 17.3 Replay evidence (serial)

1. compile sanity:
   - `python3 -m py_compile scripts/version_baseline_common.py scripts/create_identity_pack.py scripts/identity_installer.py scripts/repair_contract_backfill.py scripts/validate_identity_protocol_version_alignment.py`
2. pre-repair scaffold mismatch proof:
   - `validate_identity_protocol_version_alignment --identity-id base-repo-architect ... --operation validate --alignment-policy strict --json-only`
   - result: `FAIL_REQUIRED`, `error_code=IP-PVA-002` with `tuple_checks.scaffold_version_baseline_alignment=false`
3. protocol repair apply:
   - `repair_contract_backfill.py --catalog .identity/catalog.local.yaml --identity-id base-repo-architect --apply --json-only`
   - `repair_contract_backfill.py --catalog .identity/catalog.local.yaml --identity-id base-repo-closure-orchestrator --apply --json-only`
4. post-repair tuple check:
   - `validate_identity_protocol_version_alignment ...`
   - `tuple_checks.scaffold_version_baseline_alignment=true`

### 17.4 Verdict impact

1. v1.6.8 now closes the scaffold-version anti-forget gap with alias-driven infrastructure controls.
2. Future stream upgrades can rotate baseline via mapping alias without script hardcoding or identity-specific patches.
3. "Version governance" is now machine-enforced instead of memory-enforced.

## 18) Installer atomic closure + report selector isolation (2026-03-16)

### 18.1 Problem reconfirmed

1. Install/adopt paths could leave non-atomic scaffold drift (`catalog` aligned but `CURRENT_TASK`/`META` stale) under legacy source packs.
2. Freshness auto-selection could surface cross-identity reports and amplify non-actionable noise.

### 18.2 Landed closure set

1. `scripts/identity_installer.py`
   - applies baseline to task/meta/catalog in install/adopt paths.
   - verifies baseline tuple before activation.
   - blocks activation/downsink when baseline closure is non-pass.
   - emits machine report fields:
     - `version_baseline_apply_status`
     - `version_baseline_catalog_sync_status`
     - `version_baseline_verify_status`
     - `install_block_reasons`
2. New required probe suite:
   - `scripts/ci/run_installer_version_baseline_probes_ci.sh`
   - probes:
     - `install_legacy_pack_version_drift_blocked`
     - `install_then_migration_closure_pass`
3. Required workflow wiring:
   - `.github/workflows/_identity-required-gates.yml` executes installer baseline probe suite.
4. Surface drift lock:
   - `scripts/validate_required_gate_surface_drift.py` now enforces installer probe delegate + token wiring.
5. Report selector isolation hardening:
   - `scripts/validate_execution_report_freshness.py`
   - `scripts/validate_identity_protocol_baseline_freshness.py`
   enforce strict identity tuple candidate selection in auto mode.

### 18.3 Replay acceptance (serial)

1. `bash scripts/ci/run_installer_version_baseline_probes_ci.sh` => both probes PASS.
2. `python3 scripts/check_version_baseline_migration_closure.py --repo-catalog <fixture> --catalog <fixture> --json-only` => `PASS_REQUIRED`.
3. Freshness validators in auto mode now fail-close when only cross-identity candidates exist (`report_selector_identity_tuple_no_match_candidates`).

### 18.4 Verdict update

1. v1.6.8 now closes installer-path anti-forget drift at install-time, not only post-repair.
2. Runtime readiness interpretation is protected from cross-identity report selection noise by tuple-isolated auto mode.

## 19) Skill path root-binding hardening (2026-03-16)

### 19.1 Problem reconfirmed

1. `validate_skill_path_integrity` could degrade to cwd-dependent repo-root inference when caller omitted `--active-repo-root`.
2. In strict operations this ambiguity could blur root-misalignment vs true skill-path failures.
3. Bundle caller omissions could reintroduce this gap across scan/three-plane delegated execution.

### 19.2 Landed closure set

1. Shared deterministic resolver:
   - `scripts/tool_vendor_governance_common.py`
   - new `derive_active_repo_root(catalog_path, pack_path, cwd)` helper (catalog/pack markers first, cwd fallback last).
2. Validator hardening:
   - `scripts/validate_skill_path_integrity.py`
   - emits:
     - `active_repo_root_resolution_source`
     - `active_repo_root_explicit`
   - strict fail-close branch:
     - when root resolution degrades to ambiguous cwd fallback without explicit root
     - error family: `IP-SPATH-005`
3. Required bundle runner wiring:
   - `scripts/required_gate_bundle_runner.py`
   - always injects `--active-repo-root` for target `skill_path_integrity`, derived from runtime context when caller omits it.
4. Surface drift enforcement:
   - `scripts/validate_required_gate_surface_drift.py`
   - adds token contract for bundle-side `skill_path_integrity` root wiring.
5. Kernel contract note update:
   - `identity/protocol/IDENTITY_RUNTIME.md` (`rq_020_skill_path_integrity_contract_v1` semantics + `IP-SPATH-005`).

### 19.3 Replay evidence (serial)

1. Compile sanity:
   - `python3 -m py_compile scripts/tool_vendor_governance_common.py scripts/validate_skill_path_integrity.py scripts/required_gate_bundle_runner.py scripts/validate_required_gate_surface_drift.py`
2. Positive deterministic-root replay (project catalog):
   - `validate_skill_path_integrity ... --operation validate --json-only`
   - result includes `active_repo_root_resolution_source=catalog_project_identity_home` and `PASS_REQUIRED`.
3. Negative strict ambiguity replay (`/tmp` catalog + strict operation + no root):
   - result `FAIL_REQUIRED`, `error_code=IP-SPATH-005`, stale reason includes `active_repo_root_cwd_fallback_not_allowed_for_strict`.
4. Drift gate replay:
   - `validate_required_gate_surface_drift.py --json-only` confirms bundle-side root wiring tokens present.

### 19.4 Verdict update

1. `ASB16-RQ-020` now has deterministic root-resolution provenance and strict ambiguity fail-close semantics.
2. Bundle-level propagation closes caller-omission risk without identity-specific hardcoding.
