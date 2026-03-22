# Identity Codex Launcher Governance (v1.6.14)

Status: Active (implementation closure plus isolated historical replay capability verified, 2026-03-22; legacy fleet rollout continues)  
Layer: protocol  
Scope: identity-bound Codex launcher model, install-path ownership, and fail-close startup governance

Execution mode: topic-level canonical SSOT for v1.6.14 identity-Codex launcher governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_codex_launcher_governance`.
2. `v1.6.12` remains the semantic owner for native-chat bootstrap entry and current-turn tuple rules.
3. `v1.6.13` remains the semantic owner for canonical identity-instance pack topology and the pack-root `scripts/` surface.
4. `v1.6.14` does not reopen headstamp semantics, outer relay semantics, MCP provider health, Codex product semantics, or host-final visible-surface promotion claims.
5. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
6. This stream freezes launcher/install/startup ownership and canonical paths; it does not certify that every host-native chat surface is already auto-bound.
7. Workspace helper assets under `scripts/codex_native_chat/` remain compatibility bridge evidence only; the protocol-owned launcher install path is now the canonical installed home for `v1.6.14`.

## 1) Why v1.6.14 is required

1. `v1.6.12` froze wrapper-bound bootstrap semantics, and `v1.6.13` froze where instance-owned helper code belongs, but neither stream froze how a user gets a simple, installed, repeatable identity-bound Codex command.
2. That gap leaves room for drift:
   - workspace-local wrappers being mistaken for protocol motherline,
   - ad hoc command names such as bare `<identity-id>`,
   - accidental attempts to override the `codex` product command,
   - launcher assets being parked in ambiguous shared directories.
3. OpenAI Codex docs already define startup-scoped instruction/config surfaces such as project-scoped `.codex/config.toml`, `model_instructions_file`, and `project_doc_fallback_filenames`; that makes launcher/install governance a startup-entry concern rather than a late-turn patch concern.
4. OpenAI Codex docs also state that instruction discovery is built when Codex starts, once per run, so identity bootstrap must be attached at process entry rather than reconstructed later from ambient state.
5. MCP reference material distinguishes client/runtime initialization from server-exposed capabilities (`tools`, `resources`, `prompts`); therefore launcher/install governance belongs to the identity/Codex entry boundary, not to MCP server business semantics.
6. `v1.6.14` closes this by freezing:
   - the canonical generic launcher command,
   - the canonical per-identity installed shortcut,
   - the canonical install directories,
   - the canonical ownership split between protocol, instance pack, and compatibility bridge.

## 2) Frozen launcher model (no ambiguity)

### 2.1 Canonical command model

1. The canonical generic launcher command is:
   - `identity-codex --identity-id <identity-id> -- <codex args>`
2. The canonical installed convenience command is:
   - `id-<identity-id> <codex args>`
3. `id-<identity-id>` is a generated shortcut bound to one governed identity id; it is not a free-form manually named shell alias.
4. Bare identity command names such as `<identity-id> ...` are forbidden as canonical launcher names.
5. Overriding, shadowing, or mutating the product command `codex` is forbidden.
6. `resume <uuid>` keeps the host-thread UUID as host state only; launcher logic must never reinterpret that UUID as the identity session tuple.

### 2.2 Canonical path contract

1. Protocol-owned launcher install surfaces belong under protocol-controlled tooling in `identity-protocol-local/scripts/`.
2. Instance-pack-local launcher assets belong under pack-root `scripts/launchers/`.
3. The canonical installed executable directory is `${CODEX_HOME}/bin/`, where:
   - `${CODEX_HOME}/bin/identity-codex` is the generic launcher,
   - `${CODEX_HOME}/bin/id-<identity-id>` is the per-identity shortcut.
4. `scripts/codex_native_chat/` in a workspace may exist as migration/evidence bridge, but it is not the canonical installed launcher directory once `v1.6.14` is implemented.
5. `runtime/` remains non-executable runtime space per `v1.6.13`; launcher assets must not be installed under `runtime/`.
6. `scripts/identity/` is not a valid canonical home for identity-Codex launcher motherline assets.

### 2.3 Ownership boundary freeze

1. Protocol owns:
   - launcher template/render logic,
   - launcher install logic,
   - launcher validator logic,
   - creator/update/activate wiring,
   - canonical command naming rules.
2. Identity instance packs own only the pack-local launcher material rendered into their canonical root `scripts/launchers/` subtree.
3. Workspace compatibility bridges may orchestrate current flows during migration, but they must remain thin consumers of protocol semantics and must not become the canonical installed standard.
4. MCP server configuration, provider credentials, vendor tool health, and downstream business tooling are outside the ownership scope of this stream.

### 2.4 Canonical launcher surfaces

The canonical implementation surface for `v1.6.14` is now:

1. Protocol-owned launcher renderer:
   - `identity-protocol-local/scripts/render_identity_codex_launcher.py`
2. Protocol-owned launcher installer:
   - `identity-protocol-local/scripts/install_identity_codex_launcher.py`
3. Protocol-owned launcher validator:
   - `identity-protocol-local/scripts/validate_identity_codex_launcher.py`
4. Canonical pack-local launcher manifest:
   - `<pack_path>/scripts/launchers/identity-codex-launcher.manifest.json`
5. Canonical pack-local launcher README:
   - `<pack_path>/scripts/launchers/README.md`
6. Canonical installed launchers:
   - `${CODEX_HOME}/bin/identity-codex`
   - `${CODEX_HOME}/bin/id-<identity-id>`
7. Canonical workspace-level convergence entry:
   - `identity-protocol-local/scripts/run_identity_codex_launcher_workspace_convergence.py`

These names and directories are frozen by this stream. The renderer / installer / validator / pack-local manifest / installed shim family has landed, and later extensions may add manifest fields but must not relocate these canonical homes without a new governed stream.

### 2.5 Bootstrap ownership rules

1. The launcher owns process-entry injection of the governed startup tuple and the launch-time instruction/fallback files required by `v1.6.12`.
2. Manual overrides that attempt to replace launcher-owned `model_instructions_file` or `project_doc_fallback_filenames` on the same launch are non-qualified and must fail-close.
3. Launcher-owned startup injection must remain process-local; shared workspace-global projection files are forbidden as authoritative startup truth.
4. Launchers must not require in-place mutation of global `~/.codex/config.toml` as their normal operating mode.
5. Launchers may rely on local runtime resolution through `CODEX_HOME`, `IDENTITY_HOME`, `IDENTITY_CATALOG`, and the governed identity id, but they must not hardcode user-specific workspace paths as the protocol contract.
6. Failure to resolve identity context, pack path, or tuple truth must fail-close before `codex` starts.

### 2.6 Standard path vs compatibility bridge

1. The long-term standard path is: installed protocol-owned launcher under `${CODEX_HOME}/bin/`.
2. The currently accepted migration bridge is: workspace helper flow under `scripts/codex_native_chat/`.
3. The migration bridge is valid evidence for design and replay, but it is not sufficient by itself to claim that `v1.6.14` implementation closure has landed.
4. Bare `codex`, `codex resume`, and `codex exec` remain product commands; under identity protocol governance they are unsupported or non-qualified as identity-bound launcher evidence unless invoked through the canonical launcher path.

## 3) Four-track cross-verification boundary

### 3.1 T1 roundtable / internal topology

1. `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` already freezes explicit identity binding, isolated runtime contexts for parallel multi-identity work, and no hidden inheritance from ambient workspace state.
2. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` already freezes execution-target tuple isolation and prohibits execution-state hard identity switch.
3. `v1.6.14` reuses those invariants and specializes them to launcher/install/startup UX instead of inventing a new identity arbitration model.

### 3.2 T2 vendor / OpenAI Codex evidence

1. OpenAI Codex config reference documents:
   - user-level `~/.codex/config.toml`,
   - project-scoped `.codex/config.toml`,
   - `model_instructions_file`,
   - `project_doc_fallback_filenames`,
   - `mcp_servers.<id>.command`.
2. OpenAI Codex AGENTS guidance documents that Codex builds its instruction chain at startup, once per run, and that project fallback filenames participate in startup discovery order.
3. Therefore launcher/install/startup governance is the correct place to bind identity-aware startup files; late-turn manual reconstruction is the wrong boundary.
4. Canonical vendor anchors for this stream:
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`

### 3.3 T3 Context7 / MCP / reference boundary

1. MCP initialization exchanges protocol version, client/server capabilities, and readiness state before normal operations.
2. MCP server capabilities explicitly describe `tools`, `resources`, and `prompts`; launcher/install ownership is therefore a client/runtime entry concern, not an MCP server business contract.
3. This stream must not absorb provider-specific MCP failures into identity launcher semantics.
4. Canonical reference family for this track:
   - Context7 library id: `/modelcontextprotocol/modelcontextprotocol`
   - MCP initialize lifecycle and capability declaration materials

### 3.4 T4 protocol / inherited-stream references

1. `v1.6.12` remains the owner for bootstrap tuple semantics and wrapper-bound entry interpretation.
2. `v1.6.13` remains the owner for canonical pack-root `scripts/` topology and the prohibition on `runtime/scripts/`.
3. `v1.6.11` remains the owner for governed outer final-answer relay semantics.
4. `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` already freezes the four-track evidence bundle requirement (`T1/T2/T3/T4`) for promotion-grade updates.
5. `v1.6.14` owns only launcher/install/startup contract closure and must not be used to reopen the inherited streams above.

## 4) Closure scope and explicit non-goals

1. This stream freezes the canonical launcher names, canonical directories, and ownership split needed for identity-bound Codex startup.
2. This stream does not define new Codex product behavior.
3. This stream does not define MCP provider configuration, provider permission recovery, or business-tool launch semantics.
4. This stream does not reopen `v1.6.12` bootstrap semantics, `v1.6.13` pack topology semantics, or `v1.6.11` final relay semantics.
5. This stream does not claim that the workspace bridge is already the final protocol-owned launcher.
6. This stream does not claim that host final visible-surface auto-binding is complete.
7. This stream does not authorize mutation of the bare `codex` command as the mechanism for identity binding.
8. This stream does not authorize arbitrary alternate launcher directories or alternate shortcut naming schemes.

## 5) Frozen implementation guidance

1. Treat launcher installation as infrastructure, not as handwritten per-instance patching.
2. Render a pack-local launcher manifest under the canonical `scripts/launchers/` subtree.
3. Render installed executable shims under `${CODEX_HOME}/bin/` only.
4. Keep per-identity convenience on `id-<identity-id>` instead of on bare identity names.
5. Keep the generic entrypoint on `identity-codex` instead of on `codex`.
6. Keep bootstrap injection process-local and generated at launch time rather than persisted as mutable shared global projection.
7. Keep creator/update/activate responsible for refreshing launcher assets; manual operator editing of installed launcher shims is non-canonical.
8. Keep compatibility bridge code thin and explicitly temporary; migrate responsibility to protocol-owned launcher/install/validate surfaces.

## 6) Accepted migration path

1. Preserve the current workspace bridge under `scripts/codex_native_chat/` as compatibility evidence during legacy-operator migration only.
2. Use `v1.6.13` canonical pack-root `scripts/` topology as the destination for pack-local launcher manifests.
3. Protocol-owned renderer / installer / validator are now the motherline standard for this stream.
4. Workspace bridge status is downgraded to “migration bridge / replay artifact,” not the canonical launcher home.
5. Only after protocol-owned validator + creator/update/activate wiring are green may reviewers treat non-launcher naked entry as a stricter governance violation.

### 6.1 Workspace-level convergence entry is the canonical rollout path

1. Hand-repairing individual identities may be used as pilot evidence only; it is **not** the target operating model for fleet rollout.
2. The canonical follow-on rollout path for `v1.6.14` is the landed **workspace-level launcher convergence entry** owned by protocol infrastructure:
   - `scripts/run_identity_codex_launcher_workspace_convergence.py`
3. That convergence entry operates over the workspace-local runtime catalog rather than over ad hoc operator memory.
4. The frozen minimum behavior of that convergence entry is:
   - discover the local runtime catalog for the current workspace,
   - scan active runtime identities for launcher migration closure debt,
   - run protocol-owned backfill + launcher rollout for violating identities,
   - revalidate launcher migration closure after repair,
   - emit a governed convergence receipt that records repaired identities, remaining violations, and evidence refs.
5. The convergence entry must not invent alternate launcher semantics, alternate install directories, or per-workspace shortcut naming.
6. The convergence entry is a rollout/orchestration surface for the already frozen `v1.6.14` launcher standard; it does not reopen command naming or path ownership.
7. Cross-workspace validation should proceed by running that same convergence entry in another workspace catalog such as `fqsh`, not by introducing workspace-specific wrapper exceptions.

### 6.2 Discussion-package boundary before coding

1. The discussion and decision package for this convergence entry is frozen at `docs/governance/identity-codex-launcher-workspace-convergence-roundtable-v1.6.14.md`.
2. Reviewers must not collapse this topic into a mere startup-command convenience discussion; the accepted positive reinforcement is that launcher convergence acts as the first family pilot for protocol-owned authoritative discovery plus family-based convergence dispatch inside a workspace.
3. That positive reinforcement does **not** reopen `v1.6.14` semantics and does **not** claim that a generic multi-lane convergence framework is already landed.
4. Future families may later include health/heal, update/adoption, continuity/re-entry, or instance-script-orchestration convergence, but those semantics remain owned by their respective streams unless explicitly promoted.
5. The package exists to align architecture, audit, and implementation owners on the orchestration/control-plane shape before coding begins.
6. The package does **not** create a new stream by default; launcher-specific convergence remains owned by `v1.6.14`.
7. The workbook family may track decision status and rollout readiness, but it does not become the semantic owner of launcher convergence.
8. The roundtable package holds the open questions and recommended defaults; reviewers must not treat those questions as pre-resolved by this subsection alone.

### 6.3 Deferred generic-framework promotion guard

1. `v1.6.14` explicitly accepts launcher convergence as the **first family pilot only**; it does **not** automatically promote that pilot into a generic workspace convergence framework.
2. A new generic-framework stream is therefore **deferred by design** at this stage rather than forgotten or implicitly denied.
3. That promotion is **not automatic** after launcher convergence code lands, after a single cross-workspace pilot passes, or after workbook follow-on notes are updated.
4. Opening a later generic workspace convergence framework stream is allowed only through a new architect + audit promotion review after all of the following are machine-proven together:
   - launcher convergence is fully landed as a protocol-owned control-plane asset, including the canonical entry, governed receipt family, probes, and passive-gate boundary;
   - the **same** convergence entry is proven across more than one workspace-local runtime catalog with no workspace-specific wrapper exception;
   - at least one additional non-launcher family proves that it can reuse the same convergence control-plane grammar without transferring semantic ownership away from its existing stream;
   - the proposed abstraction does **not** require compatibility downgrades, weaker catalog authority, diluted receipt semantics, or any weakest-common-denominator relaxation of the launcher lane.
5. Until that explicit promotion review passes, future families such as health/heal, update/adoption, continuity/re-entry, or instance-script-orchestration convergence remain owned by their respective streams and may not be summarized as an already-open generic framework.
6. Workbook follow-on tracking is acceptable as reminder state only, but it must never be treated as the authority that upgrades this deferred promotion into an approved new stream.

## 7) Future promotion exit criteria

1. `v1.6.14` implementation closure now requires machine proof, not chat description.
2. The closure proof for this stream is the combined existence of:
   - protocol-owned launcher renderer / installer / validator,
   - `create_identity_pack.py` scaffolding for pack-local launcher manifest + README,
   - creator/update/activate + installer rollout that refreshes launcher assets deterministically,
   - installed `identity-codex` and `id-<identity-id>` shims under `${CODEX_HOME}/bin/`,
   - launcher fail-close on forbidden runtime override or missing tuple truth,
   - dedicated launcher probes under `scripts/ci/run_identity_codex_launcher_probes_ci.sh`,
   - dedicated convergence-entry probes under `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`,
   - active-runtime launcher migration closure checker under `scripts/check_identity_codex_launcher_migration_closure.py`,
   - protocol-owned workspace-level convergence entry under `scripts/run_identity_codex_launcher_workspace_convergence.py`,
   - strict lifecycle enforcement where `identity_creator validate` fail-closes on active-runtime launcher migration debt and `identity_creator update` performs governed auto-repair + recheck,
   - required-runtime-gates inclusion for the launcher probe lane,
   - explicit `scripts/release_readiness_check.py` consumption of the aggregate launcher migration closure checker for readiness symmetry.
3. The correct interpretation after closure is:
   - `1.6.14` semantic ownership is frozen,
   - core implementation is landed,
   - legacy fleet adoption outside the currently repaired catalogs may continue as follow-on rollout work, but active runtime identities inside governed lifecycle surfaces are no longer allowed to remain launcher-unrequired,
   - workspace bridge remains compatibility evidence rather than launcher motherline.

## 8) Post-closure audit summary boundary

1. `v1.6.14` now also accepts a dedicated launcher-lane audit summary control plane:
   - `scripts/render_protocol_lane_audit_summary.py`
   - `scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh`
2. This control plane is governance-qualified only because it is consumed by required gate surfaces and not merely by ad hoc chat review.
3. The accepted behavior class for this summary control plane is:
   - range / commit metadata pinning,
   - fail-close JSON validator consumption,
   - **two negative flips plus one applicability flip**.
4. The two negative flips are:
   - projection freshness replay that upgrades projection docs-checker from boundary-only to parity-required gating,
   - canonical workbook docs-checker drift replay that forces summary fail-close.
5. The applicability flip is:
   - stream-touch evidence classification moving from `NOT_APPLICABLE_NO_STREAM_DOCS_TOUCHED` to `APPLICABLE_*` when the pinned diff truly touches launcher stream docs.
6. This stream freezes that third class as applicability proof, not as a fail-close negative proof.
7. The current boundary is also frozen:
   - `--base` / `--head` / `--commit` pin diff scope and stream-touch evidence,
   - but docs checker / workbook consistency / launcher probe execution still runs against the provided workspace tree,
   - therefore current summary pinning does not by itself claim arbitrary historical full-tree replay unless the caller supplies an isolated historical workspace.
8. The accepted maturity statement for this stream is scoped precisely as follows:
   - **for the `v1.6.14` identity-Codex-launcher lane**, the stream has advanced from topic governance into a protocol-owned formal control-plane subsystem,
   - current-state note (2026-03-22): `python3 scripts/validate_protocol_lane_isolated_historical_replay.py --repo-root identity-protocol-local --workspace-root . --commit HEAD --json-only` returned `PASS_REQUIRED` with `projection_parity_match=true`,
   - remaining work is limited primarily to legacy rollout and broader evidence breadth,
   - the isolated historical replay capability is landed, but the isolated-workspace caveat above still applies before anyone claims arbitrary full-tree historical replay,
   - reviewers must not restate the residual work as proof that launcher semantics remain unclosed.
