# Identity v1.6.x Release Closure Governance

Status: Active static closure boundary (2026-03-26)
Layer: protocol
Scope: final version-boundary governance for closing `1.6.x` on root / machine / runtime terms without silently exporting current-universe closure debt into `1.7.x`
Execution mode: canonical static SSOT for `1.6.x` release-closure interpretation and `1.7.x` admission boundary.

## 0) State interpretation guard (mandatory)

1. This document is a release-closure governance surface, not a replacement semantic owner for any individual `v1.6.x` stream.
2. Current-state judgment for this boundary must anchor to:
   - identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md
   - identity/protocol/IDENTITY_PROTOCOL.md
   - identity/protocol/IDENTITY_RUNTIME.md
   - identity/protocol/mappings/stream-doc-registry.current.yaml
   - identity/protocol/mappings/contract-binding.current.yaml
   - identity/protocol/mappings/control-plane-status.current.yaml
   - identity/protocol/mappings/control-plane-budget.current.yaml
   - identity/protocol/mappings/workbook-registry.current.yaml
   - docs/workbook/protocol-issue-register-v1.6.md
   - docs/workbook/protocol-deep-audit-workbook-v1.6.md
3. This document freezes the version-boundary interpretation for `1.6.x`; it does **not** by itself declare a tag issuance, bypass stream owners, or replace release gates/readiness validators.
4. `1.6.x` closure means current-protocol-universe debt is closed on the `1.6.x` side rather than narratively deferred into `1.7.x`.
5. `1.7.x` admission is future-facing only after `1.6.x` is treated as root-closed, machine-closed, and runtime-closed on the problems that already belong to the current protocol universe.
6. The authoritative current workbook horizon for this release boundary is `ISSUE-001` through `ISSUE-039`; if that horizon moves, this boundary doc must truth-sync instead of freezing a stale issue universe.
7. The canonical derived summary surface for this boundary is `docs/release/identity-v1.6x-release-closure-summary.md`; it may compress this law for handoff, but it must not replace this governance surface, current runtime verdict surfaces, or fleet-scope closure matrices.
8. Historical `docs/release/*.md` surfaces must remain explicitly archival and must not silently reclaim current release-boundary authority.

## 1) Why this boundary must be frozen

1. The bottom theory in identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md already fixes source-order:
   - bottom theory -> constitutions -> root contracts -> machine-consumed enforcement surfaces.
2. Under that order, a new version line must not become a dumping ground for already-known closure debt from the current protocol universe.
3. If `1.6.x` leaves current-universe closure debt intentionally open and rebrands it as `1.7.x` work, the system loses:
   - semantic boundary clarity,
   - machine adjudication clarity,
   - release-history truth,
   - future-version cleanliness.
4. Therefore `1.6.x` must close what it already discovered about the current identity-protocol universe before `1.7.x` is allowed to define genuinely new futures.

## 2) Three release-closure classes for `1.6.x`

### 2.1 Root-closed

`1.6.x` is root-closed when:

1. the relevant stream semantics are derivable from the philosophy root and constitutional root rather than only from local review prose;
2. stream-local interpretations do not reverse-author the protocol root;
3. root corpus / ontology / gateway / no-downgrade boundaries stay explicit.

### 2.2 Machine-closed

`1.6.x` is machine-closed when:

1. known issues are no longer only human-recognized;
2. they are projected into machine-consumed contracts, mappings, validators, probes, CI, and required-gate/readiness surfaces;
3. the machine can fail-close the relevant drift without pack-local narrative rescue.

### 2.3 Runtime-closed

`1.6.x` is runtime-closed when:

1. closure is not asserted from hermetic proof alone;
2. creator / backfill / producer / consumer lanes are all shared and protocol-owned where needed;
3. real runtime identities can replay the closure on the governed lane.

## 3) Frozen release-boundary law

### 3.1 What must stay inside `1.6.x`

The following stay in `1.6.x` until closed:

1. any already-discovered current-universe semantic gap whose owner lane already exists in the `1.6.x` protocol world;
2. any gap that can be closed by additive shared infrastructure on top of already-landed owners;
3. any gap whose real fix is still creator/backfill/producer/consumer wiring rather than a new protocol ontology;
4. any gap that would otherwise force `1.7.x` to inherit residual `1.6.x` release debt.

### 3.2 What must **not** be misreported as `1.7.x`

The following do **not** justify version rollover by themselves:

1. hermetic proof without real runtime closure;
2. pack-local workaround desire;
3. historical wording that predates newer machine closure;
4. control-plane sprawl that is still closing the current protocol universe;
5. an already-open `1.6.x` stream that still has shared-infrastructure closure left to land.

### 3.3 What may legitimately enter `1.7.x`

A topic is a legitimate `1.7.x` starter only when it primarily requires one or more of:

1. a genuinely new protocol object class;
2. a genuinely new relation/topology between already-legal objects;
3. a genuinely new machine-world capability boundary not already implied by the current `1.6.x` owner lanes.

## 4) Version-boundary interpretation for late `1.6.x` streams

Late `1.6.x` streams demonstrate the correct closure pattern and therefore establish the boundary for `1.7.x` admission:

1. `v1.6.14` closes launcher/operator surfaces back onto machine executability truth;
2. `v1.6.16` closes continuity/re-entry as governed runtime law rather than operator memory;
3. `v1.6.17` closes upper-layer loop strengthening and bounded `4 -> 1` loopback as machine-consumed law;
4. `v1.6.18` closes artifact-family ontology so persisted protocol objects stop collapsing into generic “memory” language;
5. `v1.6.19` closes weak-live-linkage by requiring contract / artifact / run-binding / consumption closure on real runtime identities;
6. `v1.6.20` closes broadcast-delivery and aggregate communication transport as protocol-owned fleet/runtime convergence lanes.
7. `v1.6.21` closes higher-order clean terminal truth / canonical publishability / explicit pending-state equivalence / generic completed-done alias drift inside one shared machine-law lane.

Interpretive consequence:

1. `1.6.x` is the line that must finish closing the current protocol universe;
2. `1.7.x` inherits a cleaned ground, not an unfinished workbook tail.

### 4.1 Outer runtime verdict / summary surfaces remain bounded

1. three-plane verdict remains a governed outer runtime-state surface.
2. `scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
3. `scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
4. `scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.
5. All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.
6. `scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh` is the dedicated additive freeze for this requirement and must keep verifying:
   - `scripts/report_three_plane_status.py` emits `terminal_truth_boundary_projection` and preserves the same split in `instance_plane_detail.terminal_truth_boundary_projection`;
   - `scripts/release_readiness_check.py --summary-out` emits `terminal_truth_boundary_projection` and compresses it into one-look fields such as `one_look.terminal_truth_boundary_projection_status`;
   - `scripts/full_identity_protocol_scan.py` emits per-row `three_plane_terminal_truth_boundary_projection` and aggregate `summary_terminal_truth_boundary`.
   - when that probe only needs the terminal-truth outer-surface contract, it may invoke `scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection` and `scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection`; these profiles are protocol-owned, preserve the same `terminal_truth_boundary_projection` / `three_plane_terminal_truth_boundary_projection` / `summary_terminal_truth_boundary` surfaces, and exclude unrelated full-verdict lanes rather than relying on ad hoc probe-local filtering.
   - the three-plane projection surface must self-describe `projection_profile`, `projection_profile_execution_mode`, and `projection_excluded_areas`; when the profile is `terminal_truth_boundary_projection`, it must fail-close by projecting repo/release/release-cloud-adapter/required-gate/current-chat/m2m/tuple/governance exclusions as machine-readable `SKIPPED_NOT_REQUIRED` lanes rather than silently pretending to be a full verdict.
   - deliberate projection-only exclusions must project machine scope fields rather than stale/debt-like residue: `projection_profile_exclusion_scope=projection_skip_status=SKIPPED_NOT_REQUIRED|projection_skip_scope_class=bounded_projection_profile_exclusion|projection_skip_scope_reason=projection_profile_out_of_scope|projection_excluded_area`.
   - the full-scan projection surface must self-describe `projection_profile`, `projection_profile_execution_mode`, `projection_excluded_areas`, and per-row forwarding markers such as `scan_projection_profile` / `check_matrix_mode`; when the profile is `terminal_truth_boundary_projection`, it must preserve the terminal-truth boundary surface while machine-describing release-cloud-evidence adapter and host-visible metrics as `SKIPPED_NOT_REQUIRED` scope exclusions instead of silently dropping them or leaking projection-only stale reasons.
7. `scripts/release_readiness_check.py --check-name <script>` must also preserve explicit targeted-subset semantics:
   - report-independent targeted checks must not be blocked by unrelated `identity_creator.py update` auto-generation or execution-report freshness/baseline preflights;
   - the summary surface must self-describe that skip through machine-readable fields such as `selected_check_dependency_mode`, `execution_report_resolution_mode`, and `execution_report_resolution_status=SKIPPED_NOT_REQUIRED`;
   - when a targeted subset does not execute the required-gate bundle lane, the summary must machine-describe scope exclusion rather than leaking a residual-like stale reason: `targeted_subset_required_gate_bundle_scope=required_gate_bundle_status=SKIPPED_NOT_REQUIRED|required_gate_bundle_projection_status=SKIPPED_NOT_REQUIRED|required_gate_bundle_scope_class=bounded_targeted_subset_exclusion`;
   - the same bounded exclusion must remain explicit through `targeted_subset_required_gate_bundle_scope_reason=required_gate_bundle_scope_reason=required_gate_bundle_out_of_scope_for_targeted_subset`;
   - targeted subsets must also self-describe omitted selected-check-owned summary lanes as governed scope exclusions rather than leaking cross-lane `UNKNOWN` noise: `targeted_subset_selected_check_scope=selected_check_scope_projection_status=PASS_REQUIRED|selected_check_scope_class=bounded_targeted_subset_exclusion|selected_check_scope_reason=selected_check_out_of_scope_for_targeted_subset|selected_check_scope_excluded_summary_key_count`;
   - report-dependent targeted checks remain fail-close on those same preflights rather than silently downgrading them;
   - report-dependent post-execution checks that are materialized later in the readiness lane must still be discoverable/selectable by `--check-name` instead of being rejected as unknown selections.
8. `ASB16-RQ-006` release-plane cloud evidence must also self-describe its acquisition boundary:
   - materialized external evidence (`checks_json`, `jobs_json`, `gh-runs-json`) is the canonical local replay surface;
   - protocol consumers remain the semantic aggregation authority;
   - shell/API live fetch paths are acquisition mechanisms only and must not be overclaimed as stronger semantic truth than the materialized evidence they produce.
9. The canonical sequenced refresh lane for release-boundary control-plane artifacts is `python3 scripts/materialize_control_plane_surfaces.py --write --json-only`; release-readiness may dry-run the same machine action for health projection, but that projection must not replace the direct control-plane validators or the current canonical files themselves.
10. The release-readiness summary lifecycle is itself governed rather than ad hoc:
   - bounded batch checkpoints must emit `summary_lifecycle_status=IN_PROGRESS` and `summary_checkpoint_kind=checkpoint`;
   - finalized runs must emit `summary_lifecycle_status=FINALIZED` and `summary_checkpoint_kind=final`;
   - when `--resume-from-summary` reuses the same path as `--summary-out`, resume authority must derive from a stable prewrite snapshot of the prior governed summary rather than from the current-round file after bootstrap/preflight overwrite.
11. The canonical bounded continuation lane for that governed summary is `python3 scripts/run_release_readiness_continuation.py ...`; it may advance `scripts/release_readiness_check.py --summary-out <path> --max-command-sequence-checks <n>` across multiple rounds, but it must fail-close on invalid lifecycle states, missing summary after a successful round, stalled progress, or forbidden forwarded flags that would let callers override shared summary ownership. Its inner `release_readiness_check.py` invocation must resolve from protocol-owned repo-root/script path rather than caller cwd.
12. `scripts/ci/run_release_readiness_summary_binding_probes_ci.sh` and `scripts/ci/run_release_readiness_continuation_probes_ci.sh` are additive machine-law freezes for the lifecycle/binding/continuation rules above and must remain green alongside `scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh`.
    - the same governed summary must also self-describe `active_runtime_closure_projection=one_look.identity_codex_launcher_status|one_look.identity_context_continuity_status|one_look.identity_context_continuity_receipt_family_status|one_look.identity_reentry_brief_status|one_look.identity_reentry_consumption_status|one_look.protocol_dialogue_retention_status|one_look.artifact_family_routing_status|one_look.identity_broadcast_delivery_status|one_look.identity_communication_transport_status|one_look.identity_weak_live_linkage_status|one_look.identity_terminal_truth_cleanliness_status`;
    - active-runtime closure one-look export must keep high-value companion detail visible too, including `one_look.identity_codex_launcher_ambient_runtime_default_status`, `one_look.identity_communication_transport_reply_transport_status`, `one_look.identity_weak_live_operational_closure_class`, and `one_look.identity_terminal_truth_class`, so operator-facing compression does not erase semantic class or known secondary residual surfaces.
    - the direct owner lanes behind that bounded active-runtime projection are `scripts/validate_identity_codex_launcher.py`, `scripts/validate_identity_context_continuity.py`, `scripts/validate_identity_context_continuity_receipts.py`, `scripts/validate_identity_reentry_brief.py`, `scripts/validate_identity_reentry_consumption.py`, `scripts/validate_identity_dialogue_retention.py`, `scripts/validate_identity_artifact_family_routing.py`, `scripts/validate_identity_broadcast_delivery.py`, `scripts/validate_identity_communication_transport.py`, `scripts/validate_identity_weak_live_linkage.py`, and `scripts/validate_terminal_truth_cleanliness.py`;
    - the same governed summary must self-describe `governance_probe_projection=one_look.terminal_truth_boundary_outer_surface_e2e_probe_status|one_look.runtime_summary_surface_governance_probe_status|one_look.required_gate_surface_drift_probe_status|one_look.release_readiness_summary_binding_probe_status|one_look.release_readiness_continuation_probe_status|one_look.release_plane_context_resolution_probe_status|one_look.active_execution_report_pointer_locality_probe_status|one_look.strict_live_active_pointer_locality_probe_status|one_look.execution_report_selection_convergence_probe_status|one_look.identity_codex_launcher_convergence_probe_status|one_look.identity_transport_fleet_closure_convergence_probe_status|one_look.active_runtime_pack_closure_convergence_probe_status`;
    - the same governed summary must keep pointer-locality companions explicit too, including `one_look.active_execution_report_pointer_external_rejection_status`, `one_look.active_execution_report_pointer_external_resolution_mode`, `one_look.active_execution_report_pointer_external_selection_mode`, `one_look.active_execution_report_pointer_external_authority_class`, `one_look.active_execution_report_pointer_external_selected_report`, `one_look.active_execution_report_pointer_pack_local_authority_status`, `one_look.active_execution_report_pointer_pack_local_resolution_mode`, `one_look.active_execution_report_pointer_pack_local_selection_mode`, `one_look.active_execution_report_pointer_pack_local_authority_class`, `one_look.active_execution_report_pointer_pack_local_selected_report`, `one_look.strict_live_active_pointer_external_rejection_status`, `one_look.strict_live_active_pointer_rehome_status`, `one_look.strict_live_active_pointer_candidate_root_status`, `one_look.strict_live_active_pointer_external_resolution_mode`, `one_look.strict_live_active_pointer_rehome_resolution_mode`, and `one_look.strict_live_active_pointer_candidate_root_resolution_mode`, so one-look compression preserves pointer-authority class, bounded rehome semantics, and pack-local fallback truth instead of flattening them into one green probe;
    - the same governed summary must keep high-value execution-report convergence companions explicit too, including `one_look.execution_report_selection_convergence_candidate_count`, `one_look.execution_report_selection_convergence_freshness_status`, `one_look.execution_report_selection_convergence_baseline_status`, and `one_look.execution_report_selection_convergence_run_id_selection_strategy`, so governance does not compress that convergence lane into status-only memory;
    - the same governed summary must also keep launcher/transport/pack convergence companions explicit, including `one_look.identity_codex_launcher_convergence_probe_context_status`, `one_look.identity_codex_launcher_convergence_metadata_hygiene_apply_status`, `one_look.identity_codex_launcher_convergence_truth_sync_apply_status`, `one_look.identity_codex_launcher_convergence_repo_catalog_rejection_status`, `one_look.identity_codex_launcher_convergence_repaired_identity_count`, `one_look.identity_transport_fleet_closure_convergence_workspace_checked_identity_count`, `one_look.identity_transport_fleet_closure_convergence_repo_inclusive_violation_count`, `one_look.identity_transport_fleet_closure_convergence_policy_id`, `one_look.active_runtime_pack_closure_convergence_workspace_checked_identity_count`, `one_look.active_runtime_pack_closure_convergence_repo_inclusive_violation_count`, and `one_look.active_runtime_pack_closure_convergence_policy_id`, so one-look compression preserves bounded repair semantics, shared convergence policy identity, and proof-strength counts instead of collapsing them into green status only;
    - the direct proof lanes behind that bounded projection now explicitly include `scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh`, `scripts/ci/run_required_gate_surface_drift_probes_ci.sh`, `scripts/ci/run_release_plane_context_resolution_probes_ci.sh`, `scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh`, `scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh`, `scripts/ci/run_execution_report_selection_convergence_probes_ci.sh`, `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`, `scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh`, and `scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh` in addition to the lifecycle/binding/terminal-truth probes already listed;
    - the same governed summary must also self-describe `repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status|one_look.required_gate_surface_drift_status|one_look.issue_register_consistency_status|one_look.protocol_broadcast_doc_control_status|one_look.protocol_governed_subdomain_doc_control_registry_status|one_look.identity_codex_launcher_migration_closure_status|one_look.identity_broadcast_migration_closure_status|one_look.identity_communication_transport_closure_status|one_look.unique_entry_contract_migration_closure_status|one_look.version_baseline_migration_closure_status`;
    - for active-runtime closure lanes, one-look proof strength must stay visible too through companion count fields such as `one_look.identity_codex_launcher_migration_closure_checked_identity_count`, `one_look.identity_broadcast_migration_closure_checked_identity_count`, `one_look.identity_communication_transport_closure_checked_identity_count`, `one_look.unique_entry_contract_migration_closure_checked_identity_count`, and `one_look.version_baseline_migration_closure_checked_identity_count`, so status-only compression cannot hide empty or weak fleet proof.
    - the direct owner lanes behind that bounded repo-global projection are `scripts/validate_executable_surface_runtime_literal_lock.py`, `scripts/validate_required_gate_surface_drift.py`, `scripts/validate_issue_register_consistency.py`, `scripts/validate_protocol_broadcast_doc_control.py`, `scripts/validate_protocol_governed_subdomain_doc_control_registry.py`, `scripts/check_identity_codex_launcher_migration_closure.py`, `scripts/check_identity_broadcast_migration_closure.py`, `scripts/check_identity_communication_transport_closure.py`, `scripts/check_unique_entry_contract_migration_closure.py`, and `scripts/check_version_baseline_migration_closure.py`;
    - those `one_look.*` fields remain derived probe projections rather than owner receipts.
13. `active_execution_report` pointer authority remains pack-local rather than clone-portable.
    - this `active_execution_report pointer` is a pack-local authority hint, not a portable cross-pack alias;
    - `latest_identity_upgrade_report()` may trust `runtime/state/active_execution_report.json` only when the pointed report still resolves under the current pack's pack-local candidate roots;
    - copied or relocated packs can inherit a stale absolute pointer to the source pack, and that cross-pack absolute pointer drift must be rejected rather than used as a mutation target;
    - when that drift is rejected, selection must fall back to pack-local candidate roots instead of mutating a foreign report through inherited absolute paths.
    - the shared selector must also expose `selection_mode` plus `selected_report_authority_class`, so operator surfaces can distinguish `active_execution_pointer_pack_local_report` from `candidate_root_latest_pack_local_report` instead of inferring authority from path strings alone.
14. `scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh` is the additive machine-law freeze for the rule above.
    - It must prove that an external `active_execution_report` pointer is rejected.
    - It must also prove that pack-local candidate roots still converge to the cloned pack's own report.
    - It must keep the shared `latest_identity_upgrade_report()` primitive honest so cloned/self-driven replay cannot silently write back into a source pack, and it must prove authority-class projection (`selection_mode`, `selected_report_authority_class`) alongside the selected path.
    - The same shared provenance lane must remain consumable beyond release/closeout owners too: `scripts/validate_multimodal_plugin_enforcement.py`, `scripts/validate_outlet_matrix.py`, `scripts/validate_promotion_pipeline.py`, `scripts/validate_phase_bootstrap_before_strict.py`, `scripts/validate_fallback_taxonomy_normalization.py`, `scripts/validate_cross_workflow_schema.py`, and `scripts/validate_identity_experience_writeback.py` must project explicit-vs-pointer authority (`*_selection_mode`, `*_selected_authority_class`, `*_pointer_resolution_mode`) instead of collapsing back to a bare path string once downstream required-gate and post-execution operational consumers absorb the selected report/evidence.
15. strict-live current-run pointer locality remains separately frozen from the mutation-selection rule above.
    - `resolve_active_execution_context()` is the current-run live-binding primitive consumed by prompt / feedback / route / weak-live linkage shared lanes, so it must not bind a foreign active report as present-turn live truth merely because a stale pointer still exists.
    - when the pointed report already lives under a valid candidate root, the primitive may classify it as `pointer_candidate_root_report`;
    - when the pointer drifts to a foreign pack but an identically named local report exists under the current pack's candidate roots, the primitive may rehome to that local report and classify it as `pointer_report_name_rehomed_candidate_root`;
    - otherwise the foreign pointer must fail-close as `external_pointer_report_rejected`.
16. `scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh` is the additive machine-law freeze for the rule above.
    - It must prove that strict-live consumers reject a foreign current-run report instead of projecting it as live-bound truth.
    - It must also prove that candidate-root-local current-run reports remain admissible and that report-name rehome stays bounded to the current pack's candidate roots only.
17. weak-live differential-audit owner absorption must remain aligned with that same shared primitive.
    - `scripts/validate_identity_weak_live_linkage.py` must not reparse `runtime/state/active_execution_report.json` independently after the shared strict-live pointer-locality rule is frozen;
    - it must consume `resolve_active_execution_context()`, expose `current_run_pointer_resolution_mode`, and fail-close foreign active pointers as `external_pointer_report_rejected` rather than silently upgrading a contract/path hint into live-binding proof.
18. `scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh` is the additive machine-law freeze for the owner-side rule above.
    - It must prove that a foreign active pointer cannot elevate weak-live sample/history evidence into current-run truth merely because a contract path equals the inherited stale pointer target.
19. primary execution report selection must also converge on one shared primitive rather than drifting by validator family.
    - `execution_report_selection_common.py` is the shared owner for primary execution report selection across `validate_execution_report_freshness.py`, `validate_identity_protocol_baseline_freshness.py`, and `validate_run_id_report_selection.py`;
    - those consumers must resolve the same primary execution report under the same candidate roots instead of each re-inventing report collection, tuple filtering, or run-id matching;
    - derivative report artifacts must remain demoted support material rather than promotion candidates for current-round primary selection.
20. `scripts/ci/run_execution_report_selection_convergence_probes_ci.sh` is the additive machine-law freeze for the convergence rule above.
    - It must prove that `validate_execution_report_freshness.py`, `validate_identity_protocol_baseline_freshness.py`, and `validate_run_id_report_selection.py` converge on the same primary execution report under a shared runtime fixture.
    - It must also prove that derivative report artifacts such as `-patch-plan.json`, `postexec/`, and `-receipt.json` stay outside the primary execution report selection lane.
21. transport fleet closure must likewise remain shared rather than checker-local.
    - `runtime_fleet_closure_common.py` is the shared owner for `check_identity_broadcast_migration_closure.py` and `check_identity_communication_transport_closure.py`;
    - those consumers must expose the same `active_runtime_validator_fleet_closure_v1` projection, keep `workspace_runtime_only` bounded to the explicitly supplied runtime catalog set, and keep `repo_catalog_inclusive` replay explicit instead of silently widening the scan surface;
    - validator-specific status fields remain separate, but catalog selection, active-runtime iteration, subprocess JSON decoding, and violation aggregation must stay shared.
22. `scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh` is the additive machine-law freeze for the convergence rule above.
    - It must prove that broadcast and communication fleet closure checkers share the same active-runtime fleet projection policy in both bounded `workspace_runtime_only` mode and explicit `repo_catalog_inclusive` mode.
    - It must also prove that repo-inclusive replay fails closed on a stray repo runtime identity instead of silently collapsing the scan surface back to the local runtime catalog.
23. active-runtime pack closure scan must also remain shared rather than checker-local.
    - `runtime_pack_closure_common.py` is the shared owner for `check_unique_entry_contract_migration_closure.py` and `check_version_baseline_migration_closure.py`;
    - those consumers must expose the same `active_runtime_pack_closure_scan_v1` projection, keep `workspace_runtime_only` bounded to the explicitly supplied runtime catalog set, and keep `repo_catalog_inclusive` replay explicit instead of silently widening or collapsing the pack scan surface;
    - semantic owners remain separate: v1.6.6 still owns unique-entry migration law, and v1.6.8 still owns version-baseline migration law.
24. `scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh` is the additive machine-law freeze for the convergence rule above.
    - It must prove that unique-entry migration closure and version-baseline migration closure share the same active-runtime pack scan policy in both bounded `workspace_runtime_only` mode and explicit `repo_catalog_inclusive` mode.
    - It must also prove that repo-inclusive replay fails closed on a stray repo runtime identity instead of silently collapsing back to the workspace-only catalog set.
25. workspace-runtime closure command construction must also remain shared rather than orchestrator-local.
    - `workspace_runtime_closure_command_common.py` is the shared owner for launcher / transport / pack closure replay commands;
    - `release_readiness_check.py`, `identity_creator.py`, `identity_codex_launcher_evidence_common.py`, and `validate_workspace_runtime_closure_command_surface.py` must reuse that shared builder instead of checker-local command spelling that can drift away from bounded `workspace_runtime_only` replay semantics.
26. shell/runtime executable surfaces must consume the same bounded closure lane instead of re-spelling family-by-family invocations.
    - `scripts/run_workspace_runtime_closure_checks.py` is the shared executable runner for launcher / transport / pack closure replay under bounded `workspace_runtime_only` mode;
    - `scripts/ci/run_required_runtime_gates_ci.sh` must consume that runner instead of spelling five separate checker commands that can drift out of sync with the shared builder.
    - that shared runner must stay full-surface rather than selector-shrunk: `workspace_runtime_runner_required_tokens=--catalog|--repo-catalog|--json-only`, `workspace_runtime_runner_forbidden_selector_tokens=--family|--checker-id`, `workspace_runtime_runner_selector_policy=full_surface_non_shrinkable`, `workspace_runtime_runner_validator=scripts/validate_required_gate_surface_drift.py`, and `workspace_runtime_runner_governance_probe=scripts/ci/run_required_gate_surface_drift_probes_ci.sh`.
    - `scripts/validate_required_gate_surface_drift.py` is the direct validator for that executable-surface boundary, and `scripts/ci/run_required_gate_surface_drift_probes_ci.sh` is the additive machine-law freeze proving missing `--repo-catalog`, forbidden selector flags, or selector-policy drift in `workspace_runtime_closure_command_common.py` all fail closed.
27. creator/update admission must consume the full bounded pack-closure pair.
    - `identity_creator.py` must enforce both `check_unique_entry_contract_migration_closure.py` and `check_version_baseline_migration_closure.py` through the shared workspace-runtime closure command builder;
    - instance preflight must not silently widen unique-entry closure back to repo-inclusive scan semantics, and it must not skip version-baseline migration closure while claiming active-runtime pack closure is already shared.

### 4.2 Repair / observation / admission split remains frozen

`v1.6.21` also freezes one release-boundary reading rule that must stay explicit across `1.6.x` closure:

1. the **repair lane** may pass when shared post-execution repair successfully restores mandatory writeback/runtime projection fields;
2. the **terminal-truth observation lane** remains the direct owner of clean terminal truth and canonical publishability verdicts;
3. the **creator/update admission lane** must keep clean-terminal admission distinct from shared repair/backfill projection health;
4. `repair success != clean terminal truth`;
5. dirty current-run terminal truth must not be upgraded into admissible update closure merely because a repair executor projected mandatory fields successfully.

Frozen consequence:

1. `scripts/repair_identity_post_execution_mandatory.py` is a shared repair executor, not the clean-terminal-truth owner;
2. `scripts/validate_terminal_truth_cleanliness.py` keeps fail-close authority over non-clean terminal truth;
3. `scripts/repair_contract_backfill.py` must fail-close only when current-run terminal-truth projection integrity is not green; a coherently projected dirty/review-pending verdict remains observation, not a projection failure;
4. shared probes must preserve this split rather than collapsing coherent dirty terminal truth back into “repair executor failed”.

## 5) Release-closure and future-admission rule

1. The authoritative current workbook rows for `ISSUE-001` through `ISSUE-039` remain the machine-readable release-closure ledger for the known `1.6.x` universe.
2. Release issuance still depends on the active machine gates, not this document alone.
3. But any attempt to classify a still-current-universe closure debt as a `1.7.x` item must fail the interpretation test in this document.
4. The admission rule for `1.7.x` is therefore:
   - first prove the current topic is not unresolved `1.6.x` closure debt;
   - only then treat it as a new object / relation / capability stream.

### 5.1 Outer runtime verdict / summary surfaces must stay explicitly bounded

1. three-plane verdict remains a governed outer runtime-state surface.
2. `scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
3. `scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
4. `scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.
5. `scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh` must keep the three surfaces above honest by verifying `terminal_truth_boundary_projection`, `three_plane_terminal_truth_boundary_projection`, and `summary_terminal_truth_boundary` on real emitted payloads.
6. The same probe may use `scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection` and `scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection` when it only needs the terminal-truth outer-surface contract; these bounded projection profiles remain protocol-owned and must not be replaced by probe-local shell filtering or hand-written JSON assembly.
7. Projection-only profiles must remain self-describing: three-plane must expose `projection_profile`, `projection_profile_execution_mode`, and `projection_excluded_areas`, while full-scan must expose the same profile fields plus row-level forwarding markers such as `scan_projection_profile` / `check_matrix_mode`.
8. Projection-only profiles must fail-close on excluded lanes through explicit `SKIPPED_NOT_REQUIRED` payload state, not by omission or prose-only operator guidance.
9. All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.
10. Release-plane cloud evidence summaries must expose whether their evidence came from materialized input or live fetch, so local replay never depends on operator memory about `gh`/API transport behavior.
11. The canonical control-plane refresh sequence remains owned by `scripts/materialize_control_plane_surfaces.py`; summary surfaces may project its health, but they must not silently collapse direct validator receipts into derived prose.
12. The release-readiness summary lifecycle remains governed:
   - batch checkpoints are explicitly `IN_PROGRESS`/`checkpoint`;
   - finalized summaries are explicitly `FINALIZED`/`final`;
   - same-path resume is legal only through a stable prewrite snapshot of the prior governed summary, never by reinterpreting the freshly overwritten current-round file as if it were old resume authority.
11. `scripts/run_release_readiness_continuation.py` is the protocol-owned bounded continuation surface for the governed release-readiness summary; it must preserve shared summary ownership, resolve `release_readiness_check.py` from protocol-owned repo-root/script path rather than caller cwd, and fail-close on missing summary materialization, invalid lifecycle, stalled progress, or caller attempts to override `--summary-out`, `--resume-from-summary`, or `--max-command-sequence-checks`.
12. `scripts/ci/run_release_readiness_summary_binding_probes_ci.sh` and `scripts/ci/run_release_readiness_continuation_probes_ci.sh` must continue replaying same-path binding plus multi-round continuation so this lifecycle remains machine-checked instead of operator-remembered.
13. The same governed release-readiness summary must also project the bounded probe lane `governance_probe_projection=one_look.terminal_truth_boundary_outer_surface_e2e_probe_status|one_look.runtime_summary_surface_governance_probe_status|one_look.required_gate_surface_drift_probe_status|one_look.release_readiness_summary_binding_probe_status|one_look.release_readiness_continuation_probe_status|one_look.release_plane_context_resolution_probe_status|one_look.active_execution_report_pointer_locality_probe_status|one_look.strict_live_active_pointer_locality_probe_status|one_look.execution_report_selection_convergence_probe_status|one_look.identity_codex_launcher_convergence_probe_status|one_look.identity_transport_fleet_closure_convergence_probe_status|one_look.active_runtime_pack_closure_convergence_probe_status`, while keeping the direct probe owners (`scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh`, `scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh`, `scripts/ci/run_required_gate_surface_drift_probes_ci.sh`, `scripts/ci/run_release_readiness_summary_binding_probes_ci.sh`, `scripts/ci/run_release_readiness_continuation_probes_ci.sh`, `scripts/ci/run_release_plane_context_resolution_probes_ci.sh`, `scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh`, `scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh`, `scripts/ci/run_execution_report_selection_convergence_probes_ci.sh`, `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`, `scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh`, and `scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh`) as the machine-law receipts behind those derived `one_look.*` fields.
    - governance likewise requires pointer-locality companions such as `one_look.active_execution_report_pointer_external_rejection_status`, `one_look.active_execution_report_pointer_external_resolution_mode`, `one_look.active_execution_report_pointer_external_selection_mode`, `one_look.active_execution_report_pointer_external_authority_class`, `one_look.active_execution_report_pointer_external_selected_report`, `one_look.active_execution_report_pointer_pack_local_authority_status`, `one_look.active_execution_report_pointer_pack_local_resolution_mode`, `one_look.active_execution_report_pointer_pack_local_selection_mode`, `one_look.active_execution_report_pointer_pack_local_authority_class`, `one_look.active_execution_report_pointer_pack_local_selected_report`, `one_look.strict_live_active_pointer_external_rejection_status`, `one_look.strict_live_active_pointer_rehome_status`, `one_look.strict_live_active_pointer_candidate_root_status`, `one_look.strict_live_active_pointer_external_resolution_mode`, `one_look.strict_live_active_pointer_rehome_resolution_mode`, and `one_look.strict_live_active_pointer_candidate_root_resolution_mode` to remain machine-readable after outer-surface compression.
    - governance also requires the same one-look export to preserve high-value execution-report convergence companions such as `one_look.execution_report_selection_convergence_candidate_count`, `one_look.execution_report_selection_convergence_freshness_status`, `one_look.execution_report_selection_convergence_baseline_status`, and `one_look.execution_report_selection_convergence_run_id_selection_strategy`, so convergence proof strength and selector semantics remain machine-readable after outer-surface compression.
    - governance likewise requires launcher/transport/pack convergence companions such as `one_look.identity_codex_launcher_convergence_probe_context_status`, `one_look.identity_codex_launcher_convergence_metadata_hygiene_apply_status`, `one_look.identity_codex_launcher_convergence_truth_sync_apply_status`, `one_look.identity_codex_launcher_convergence_repo_catalog_rejection_status`, `one_look.identity_codex_launcher_convergence_repaired_identity_count`, `one_look.identity_transport_fleet_closure_convergence_workspace_checked_identity_count`, `one_look.identity_transport_fleet_closure_convergence_repo_inclusive_violation_count`, `one_look.identity_transport_fleet_closure_convergence_policy_id`, `one_look.active_runtime_pack_closure_convergence_workspace_checked_identity_count`, `one_look.active_runtime_pack_closure_convergence_repo_inclusive_violation_count`, and `one_look.active_runtime_pack_closure_convergence_policy_id` to remain machine-readable after outer-surface compression.

## 6) Frozen one-line version law

1. `1.6.x` must close the current identity-protocol universe to root-closed, machine-closed, and runtime-closed terms.
2. `1.7.x` begins only as a future-facing line for new objects, new relations, and new capabilities on top of that closed ground.
