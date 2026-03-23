# Protocol Remediation Audit Ledger (v1.6.14 identity-Codex launcher stream)

Status: Active (implementation closure plus isolated historical replay capability verified, 2026-03-22; legacy fleet rollout continues)  
Scope: protocol review ledger for identity-bound Codex launcher/install/startup governance

## 0) Stream objective

1. Freeze the canonical generic identity-bound Codex command.
2. Freeze the canonical per-identity installed shortcut command.
3. Freeze the canonical install-path split between protocol, instance pack, and `${CODEX_HOME}/bin/`.
4. Freeze the interpretation that workspace wrappers are migration bridge evidence, not the final launcher motherline.

## 1) Problem statement frozen for audit

1. `v1.6.12` and `v1.6.13` reduced semantic ambiguity, but users still lacked one simple installed identity-bound command that is protocol-owned and repeatable.
2. Without a dedicated launcher stream, successful workspace wrappers can be misread as the final protocol standard even when they still live in ad hoc workspace paths.
3. That ambiguity encourages three recurring errors:
   - treating bare `<identity-id>` commands as acceptable launcher names,
   - trying to hijack the `codex` product command,
   - parking launcher logic in non-canonical shared directories.
4. The stream exists to separate “launcher UX/install governance” from:
   - bootstrap semantics,
   - pack topology,
   - MCP provider/tool health,
   - host-visible final surface behavior.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces

1. `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
5. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
6. `identity/protocol/IDENTITY_PROTOCOL.md`
7. `identity/protocol/IDENTITY_RUNTIME.md`
8. `identity/protocol/mappings/control-plane-status.current.yaml`
9. Landed implementation targets under the protocol `scripts` directory are:
   - render_identity_codex_launcher.py
   - install_identity_codex_launcher.py
   - validate_identity_codex_launcher.py

### 2.2 Workspace / instance-owned surfaces consumed by this stream

1. Compatibility bridge evidence under `scripts/codex_native_chat/`.
2. Canonical pack-local launcher destination under `<pack_path>/scripts/launchers/`.
3. Installed executable destination under `${CODEX_HOME}/bin/`.
4. Runtime pack topology guarantees inherited from `v1.6.13`.

## 3) Four-track review checklist

### 3.1 T1 roundtable / internal topology

1. Reuse `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` for explicit identity binding and runtime-isolation baseline.
2. Reuse `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` for execution-target tuple isolation and hard no-switch-in-execution semantics.
3. Confirm that launcher design does not create a new shared mutable identity arbitration model.

### 3.2 T2 vendor / OpenAI Codex evidence

1. Confirm that startup instruction discovery and config surfaces are vendor-documented at process start.
2. Confirm that `model_instructions_file` and `project_doc_fallback_filenames` are valid startup surfaces.
3. Confirm that project-scoped `.codex/config.toml` and MCP launcher commands are existing Codex concepts rather than protocol inventions.
4. Canonical vendor anchors:
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`

### 3.3 T3 Context7 / MCP / reference boundary

1. Confirm that MCP initialization and capability negotiation separate client/runtime entry from server-exposed primitives.
2. Confirm that launcher/install governance is therefore a client/runtime entry topic, not an MCP server business topic.
3. Keep provider-specific MCP launch failures out of the `v1.6.14` semantic scope.
4. Canonical reference family:
   - `/modelcontextprotocol/modelcontextprotocol`

### 3.4 T4 protocol / inherited-stream references

1. Reuse `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md` for bootstrap semantics.
2. Reuse `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md` for pack-root `scripts/` ownership.
3. Reuse `docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md` as inherited review baselines.
4. Reuse `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` for the four-track intake requirement itself.

## 4) Frozen implementation checklist

1. Canonical generic command is `identity-codex --identity-id <identity-id> -- <codex args>`.
2. Canonical convenience command is `id-<identity-id> <codex args>`.
3. Bare `<identity-id>` command names are rejected as canonical launcher UX.
4. The `codex` product command is never overridden or renamed by protocol launcher governance.
5. For operator-facing daily entry, the preferred installed surface remains the short generated shortcut `id-<identity-id>`; the longer generic command remains the explicit generic/repair/documentation form.
6. Operator-facing command discovery is protocol-owned rather than chat-assembled:
   - `identity-codex commands --identity-id <identity-id>`
   - `id-<identity-id> commands`
   must return already assembled copyable start/resume commands for the target identity.
7. Instance/runtime consumption also remains protocol-owned:
   - `identity-codex commands --identity-id <identity-id> --json-only`
   must return a structured command bundle so identity instances can answer concretely without inventing launcher logic.
8. Embedded internal support bundles from other streams, such as `v1.6.16` continuity support, are acceptable only inside that structured JSON bundle and must not become independent operator command folklore.
9. The protocol-owned recommended command surfaces must be judged by **fresh-shell executability**, not by shortcut discoverability or host-thread presence alone.
10. If the resolved identity catalog differs from the ambient shell catalog, the recommended command must switch to the generic launcher form carrying explicit `--catalog <resolved-catalog>`.
11. If resume requires identity-session tuple closure, the recommended resume command must carry explicit `--session-id run:<...>`; a short launcher shortcut that cannot encode that tuple is not an auditable recommendation surface.
12. Audit interpretation of resume readiness is decomposed and fail-close:
    - `host_thread_id_status`
    - `identity_session_tuple_status`
    - `resume_command_fresh_shell_executable_status`
    together determine whether `resume_status` may be `PASS_REQUIRED`.
13. Recovery semantics are frozen and must not drift during implementation:
    - `resume <host-thread-uuid>` remains the Codex recovery target for prior records;
    - `--session-id run:<...>` is only launcher-side tuple closure;
    - auditing must fail any implementation that swaps, collapses, or conflates those two identifiers.
14. Pack-local launcher assets land only under `<pack_path>/scripts/launchers/`.
15. Installed launchers land only under `${CODEX_HOME}/bin/`.
16. Workspace `scripts/codex_native_chat/` remains compatibility bridge only until protocol-owned launcher assets land.
17. Launcher ownership of `model_instructions_file` and `project_doc_fallback_filenames` injection remains explicit and fail-close.

## 5) Audit verdict rules (frozen)

1. **Policy PASS** for this stream requires:
   - governance doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - review doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - scope-matrix row present in `identity/protocol/mappings/stream-scope-matrix.current.yaml`,
   - allowlist rows present in `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`,
   - audit index discoverability updated in `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
2. **Architecture PASS** for this stream requires:
   - command naming rules are frozen,
   - install directories are frozen,
   - workspace bridge is explicitly downgraded to compatibility evidence,
   - protocol vs instance vs installed-bin ownership is unambiguous.
3. **Implementation PASS** for this stream now requires the landed assets and lanes to stay green together:
   - protocol-owned launcher renderer / installer / validator,
   - protocol-owned workspace-level convergence entry `scripts/run_identity_codex_launcher_workspace_convergence.py`,
   - creator/update/activate and installer rollout wiring,
   - canonical pack-local launcher manifest + README,
   - canonical installed `identity-codex` and `id-<identity-id>` shims,
   - protocol-owned command-bundle output from `identity-codex commands --identity-id <identity-id>` and `id-<identity-id> commands`,
   - launcher probe lane `scripts/ci/run_identity_codex_launcher_probes_ci.sh`,
   - convergence-entry probe lane `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`,
   - active-runtime launcher migration closure checker `scripts/check_identity_codex_launcher_migration_closure.py`,
   - governed launcher convergence evidence bundles whose receipts self-pin `evidence_ref` / `manifest_ref` and whose archival root carries `EVIDENCE_MANIFEST.<run_token>.json`,
   - post-closure evidence truth-sync/backfill through `scripts/refresh_identity_codex_launcher_evidence_truth_sync.py`,
   - lifecycle enforcement where `identity_creator validate` fail-closes on active-runtime launcher migration debt and `identity_creator update` performs governed auto-repair + recheck,
   - required-runtime-gates inclusion for the launcher probe lane,
   - explicit `scripts/release_readiness_check.py` consumption of both the convergence-entry probe lane and the aggregate launcher migration closure checker so readiness no longer depends only on the single-identity launcher validator.
4. Reviewers must not collapse `Architecture PASS` into `Implementation PASS`.

## 6) Accepted closure boundary

1. `v1.6.14` is closed at the implementation level when the command model, directories, ownership boundary, launcher assets, installed shims, and probe lane are all machine-verifiable together.
2. The workspace bridge may remain operational after that closure, but only as bridge-only compatibility evidence.
4. This stream is independent from provider/MCP runtime incidents and from host-final visible-surface promotion work.

## 6.1 Accepted rollout direction after closure

1. The accepted rollout direction after closure is **not** “continue hand-fixing identities one by one.”
2. Manual repair of a single identity is acceptable only as pilot proof that the protocol-owned launcher migration toolchain works end-to-end.
3. The accepted protocol-owned rollout target is the landed **workspace-level launcher convergence entry** `scripts/run_identity_codex_launcher_workspace_convergence.py`, which:
   - resolves the workspace-local runtime catalog,
   - aggregates launcher migration closure debt for active runtime identities,
   - executes governed backfill + launcher rollout on violating identities,
   - reruns closure validation after repair,
   - emits a convergence receipt plus governed evidence manifest for audit, replay, and post-closure archival truth-sync.
4. Reviewers must treat that convergence entry as rollout/orchestration infrastructure layered on top of the already frozen `v1.6.14` launcher contract, not as permission to reopen launcher semantics.
5. Cross-workspace proof should therefore come from running the same convergence entry against another workspace catalog, rather than from granting workspace-specific wrapper exceptions.

### 6.2 Accepted discussion package and reviewer responsibilities

1. Reviewers and auditors should use `docs/governance/identity-codex-launcher-workspace-convergence-roundtable-v1.6.14.md` as the shared discussion package for the convergence-entry landing.
2. Reviewers should positively reinforce that this topic is not only about the launcher command line; the accepted framing is protocol-owned authoritative discovery and family-based convergence dispatch, with launcher as the first family pilot.
3. That framing is acceptable only if reviewers keep the scope honest: launcher convergence remains inside `v1.6.14`, and a generic multi-lane convergence framework must not be overclaimed as already landed.
4. Future convergence families such as health/heal, update/adoption, continuity/re-entry, or instance-script-orchestration may later reuse the same control-plane shape, but they do not transfer semantic ownership away from their existing streams by implication alone.
5. That package is acceptable because it keeps launcher convergence inside `v1.6.14` while exposing the orchestration/control-plane questions that still require explicit decisions before coding.
6. Reviewers must keep the workbook family in its proper role: workbook surfaces may track decision status, issue routing, and rollout readiness, but they do not replace the stream owner docs as launcher-semantics authority.
7. Implementation start still requires explicit architect and audit agreement on the open questions captured in the roundtable package; this subsection does not pre-resolve those decisions by itself.

### 6.3 Deferred promotion rule for generic workspace convergence

1. Reviewers should explicitly record that later promotion to a generic workspace convergence framework is **deferred by design**, not forgotten, and not already approved.
2. Reviewers must not restate launcher convergence landing as automatic permission to open a generic framework stream.
3. A future generic-framework recommendation is acceptable only after a new architect + audit promotion review confirms all of the following:
   - the launcher convergence entry is fully landed as a protocol-owned control-plane asset with governed receipts, probes, and passive-gate separation;
   - the same entry has passed unchanged portability proof across more than one workspace-local runtime catalog with no workspace-specific exceptions;
   - at least one non-launcher family demonstrates reuse of the same convergence control-plane grammar without semantic-owner drift;
   - the recommendation is framed as consolidation of existing protocol assets (notification/trigger surfaces, protocol-feedback inbox/outbox, family convergence entries, probe/validator fact surfaces, receipt/manifest truth-sync) rather than as invention of a new transport plane, side channel, or parallel command family;
   - the proposed framework does not depend on compatibility downgrades, weaker authority rules, diluted receipt families, or weakened launcher semantics.
4. Until those gates are met, reviewers must keep future convergence-family discussion in the owner streams for those families rather than implying that a generic framework is already open.
5. Workbook reminders may help keep this deferred promotion visible, but workbook status alone must never be treated as the approval surface for opening a new framework stream.

### 6.4 Current machine-proof note and closer handoff boundary

1. Current-state note (2026-03-22): reviewers may now treat launcher runtime-path authority as part of formal launcher closure rather than as install-time operator folklore.
2. The machine-proof family for that claim is:
   - `scripts/validate_identity_codex_launcher.py`, which now exports `runtime_paths_status`,
   - `scripts/check_identity_codex_launcher_migration_closure.py`, which now carries the same runtime-path closure family into aggregate active-runtime proof,
   - runtime-only consumers in required gates, readiness, and `identity_creator`.
3. Cross-workspace portability proof is also now machine-landed through `scripts/ci/run_identity_codex_launcher_cross_workspace_pilot_probes_ci.sh`, which replays the **same** convergence entry against another workspace-local runtime catalog with no workspace-specific wrapper exception.
4. Current-state note (2026-03-22): the cross-workspace pilot now also verifies the direct-entry/runtime-authority conditions raised by the `fqsh` feedback:
   - fresh convergence apply emits a receipt/manifest bundle that is already truth-synced on the first dry-run;
   - aggregate closure with `--catalog .identity/catalog.local.yaml` resolves against the caller workspace rather than the protocol repo;
   - `resolve_identity_context.py resolve --identity-id <id>` from the sibling workspace classifies that runtime catalog as `source_layer=project` with `resolved_scope=USER`.
   - `identity-codex commands --identity-id <id>` and `id-<id> commands` return a ready-to-copy command bundle rather than leaving command assembly to the operator.
   - that bundle is terminal-native and direct (`id-<id> ...`, `identity-codex --identity-id <id> ...`), not shell-wrapped helper text such as `zsh -lic '...'`.
   - the protocol-owned `recommended_user_command` is also environment-aware **and** fresh-shell executable: if the current shell cannot discover the short launcher on `PATH`, the bundle falls back to the absolute direct launcher path; if the ambient catalog mismatches the resolved identity catalog, the bundle emits explicit `--catalog`; if resume requires tuple closure, the bundle emits explicit `--session-id run:<...>` rather than a stale short shortcut.
   - host-thread UUID presence alone must not be audited as resume readiness; the machine-visible decomposition must distinguish `host_thread_id_status`, `identity_session_tuple_status`, and `resume_command_fresh_shell_executable_status`.
   - `identity-codex commands --identity-id <id> --json-only` returns a structured bundle with `recommended_user_command`, `copyable_commands`, and `instance_answer_guidance`, preserving the boundary “protocol guides, instance answers”.
5. Audit follow-on closure note (2026-03-23): the raw runtime-catalog metadata follow-on is now closed on its own `v1.6.10` lane:
   - `scripts/validate_runtime_catalog_metadata_hygiene.py` / `scripts/repair_runtime_catalog_metadata_hygiene.py` now own raw row self-description;
   - launcher closure now projects `runtime_catalog_metadata_hygiene_status`;
   - convergence probes seed stale metadata and prove apply-time repair.
   Review interpretation is frozen: launcher truth remains closed, and raw metadata cleanup must not be misreported as launcher-semantic debt.
6. The closer handoff boundary after this landing is therefore narrow and explicit:
   - continue using the same convergence entry, the same receipt family, and the same runtime-only closure semantics,
   - treat launcher convergence receipt/manifest truth-sync as already landed, and keep remaining work mainly on broader rollout breadth plus additional archival coverage,
   - do **not** reopen launcher semantics,
   - do **not** overclaim that generic workspace convergence promotion is already approved.

## 7) Boundary lock for reviewers

1. Do not reinterpret this stream as permission to override the `codex` product command.
2. Do not accept bare identity names as canonical launcher commands.
3. Do not relocate launcher motherline assets into `scripts/identity/`, `runtime/`, or other shared drift paths.
4. Do not reopen `v1.6.12` bootstrap semantics or `v1.6.13` pack-topology semantics while reviewing this stream.
5. Do not classify MCP/provider startup failures as proof that the `v1.6.14` launcher contract is wrong.
6. Do not promote workspace bridge code to canonical launcher motherline by chat text alone; promotion requires protocol-owned install/validate assets.

## 8) Post-closure lane-audit summary control plane

1. The launcher lane now has a dedicated summary renderer/control plane asset:
   - `scripts/render_protocol_lane_audit_summary.py`
   - `scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh`
2. This asset is no longer review-only helper tooling; it is formally consumed by:
   - `scripts/release_readiness_check.py`
   - `scripts/ci/run_required_runtime_gates_ci.sh`
3. The accepted machine interpretation is:
   - the renderer is a **single-lane formal control-plane asset** for `v1.6.14`,
   - it supports range metadata pinning through `--base`, `--head`, and `--commit`,
   - it supports fail-close JSON validator consumption for summary rendering,
   - it proves summary behavior through **two negative flips plus one applicability flip**.
4. The required replay classes are:
   - negative flip: projection freshness changes from boundary-only to parity-required and the summary must mark projection docs-checker gating as active,
   - negative flip: canonical workbook docs-checker drift forces summary fail-close with non-zero canonical violation count,
   - applicability flip: stream-touch evidence changes from `NOT_APPLICABLE_NO_STREAM_DOCS_TOUCHED` to `APPLICABLE_*` when the pinned diff truly touches launcher stream docs.
5. Reviewers must not misstate the third class as fail-close-negative proof; it is applicability-scope proof, not a red-state proof.
6. Current caveat is frozen explicitly:
   - the renderer already pins diff/range metadata and stream-touch evidence,
   - but docs checker / workbook consistency / launcher probes still evaluate against the provided `workspace_root` tree,
   - therefore the current asset is **not yet** a universal isolated historical replay engine for arbitrary commits unless it is run against an isolated clone/worktree representing that historical tree.
7. This caveat does **not** downgrade the asset back to “explanatory only”; it only limits how far reviewers may promote the history-replay claim.

## 9) Accepted external closure statement

1. The audit-approved external statement for this stream is:
   - **for the `v1.6.14` identity-Codex-launcher lane**, it has advanced from topic governance into a protocol-owned formal control-plane subsystem:
     - semantics are in the main protocol,
     - discovery is in registry,
     - evidence is in allowlist,
     - execution is in required gates,
     - audit is in the lane-summary control plane.
2. The remaining tail is also frozen precisely:
   - current-state note (2026-03-22): `python3 scripts/validate_protocol_lane_isolated_historical_replay.py --repo-root identity-protocol-local --workspace-root . --commit HEAD --json-only` returned `PASS_REQUIRED` with `projection_parity_match=true`,
   - remaining work belongs mainly to legacy rollout outside the already governed catalogs and broader evidence breadth,
   - the current asset is **not** a universal isolated historical replay engine for arbitrary commits unless it is run against an isolated clone/worktree representing that historical tree,
   - it does **not** belong to unresolved launcher semantics.
3. Reviewers may use the statement above as the auditable closure summary, but must keep the lane scope and replay caveat attached.
