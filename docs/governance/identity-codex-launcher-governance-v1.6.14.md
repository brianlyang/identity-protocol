# Identity Codex Launcher Governance (v1.6.14)

Status: Active (implementation closure + shell ingress hardening + launcher-owned continuity consumer bridge + install-vs-shell-discoverability command projection verified, 2026-03-24; legacy fleet rollout continues)
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

### 0.1A Cross-stream breakthrough sequence atlas (2026-03-24)

1. The canonical explanatory visual atlas for this stream is:
   - `docs/references/identity-protocol-breakthrough-sequence-visual-atlas-v1.6.md`
   - asset root: `docs/references/assets/identity-protocol-breakthrough-sequence-visual-atlas/`
2. This atlas preserves the fixed order `headstamp -> runtime authority -> launcher command surface -> governed continuity proof -> cross-context stable short-command closure`.
3. For this stream, the atlas highlights that launcher stability became real only after headstamp truth and runtime authority were already machine-owned; normative truth remains this governance doc, the protocol motherline, and machine validators.

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
7. For operator-facing daily use, the preferred already-installed surface is `id-<identity-id>` **only when the ambient shell catalog already matches the resolved identity catalog**, because the generated shortcut keeps host/UI/tab naming short and stable without weakening protocol ownership; when command discovery classifies `ambient_catalog_mismatch_requires_explicit_catalog`, the preferred primary surface must switch to the explicit generic launcher carrying `--catalog <resolved-catalog>`. `identity-codex --identity-id <identity-id> -- ...` remains the explicit generic form for documentation, automation, repair flows, and any mismatch-safe primary surface.
8. Command discovery is also protocol-owned: when an operator asks “`identity_id=XXX` 如何启动 / 如何续接”, the canonical answer surface is:
   - `identity-codex commands --identity-id <identity-id>`
   - or, when the per-identity launcher already exists, `id-<identity-id> commands`
9. That command-discovery surface must print already assembled copyable commands; operators must not need to manually splice identity ids, launcher names, or resume thread UUIDs in chat.
10. The same command-discovery surface must also expose a structured `--json-only` bundle for instance/runtime consumers, so protocol remains the guidance owner while the concrete user-facing answer remains the identity instance’s responsibility.
11. That structured launcher bundle may embed internal support bundles from other governed streams, such as `v1.6.16` continuity support, but those embedded bundles remain internal-only and must not create a second operator-facing command family.
12. The protocol-owned recommendation surface must be **fresh-shell executable**, not merely path-aware:
   - `recommended_start_command`,
   - `recommended_resume_command`,
   - and `recommended_user_command`
   must already be self-contained for the shell that requested the bundle.
13. `installed` and `discoverable in the current shell` are separate protocol facts:
   - `installed` means the governed launcher file exists at the protocol-owned `${CODEX_HOME}/bin/` target and passes install validation;
   - `discoverable in the current shell` means the requesting shell can actually resolve the bare launcher command through its live `PATH`.
14. The structured launcher bundle and launcher validator must surface those facts separately for both launcher families, including at least:
   - `shortcut_install_status`,
   - `shortcut_shell_discoverability_status`,
   - `generic_launcher_install_status`,
   - `generic_launcher_shell_discoverability_status`.
15. When the resolved identity catalog differs from the ambient shell catalog, the command bundle must switch its preferred/recommended primary start/resume surfaces to the generic launcher form carrying explicit `--catalog <resolved-catalog>`.
    - Under that mismatch state, short launcher commands may remain visible only as convenience/reference surfaces (for example `copyable_commands.*.shortcut`); they must not remain labeled as `preferred_*`.
    - The installed `id-<identity-id>` shim itself must remain pinned to its governed install catalog by forwarding explicit `--catalog <resolved-catalog>` internally; ambient shell/catalog drift must not silently rebind that shortcut to another catalog.
    - That execution-time catalog pinning does **not** promote the short launcher back onto the preferred discovery lane under mismatch; command discovery must still expose the explicit generic primary surface so the catalog requirement stays operator-visible and machine-auditable.
    - Launcher command-bundle and exec surfaces may consume the runtime-mode guard in an **observational admissibility mode** so they inherit shared runtime-admitted vs repo-metadata-fallback truth without collapsing the launcher-owned mismatch semantics: repo-metadata fallback identities must fail-close machine-readably, while ambient catalog mismatch remains projected by the launcher bundle itself rather than being turned into a second launcher-local truth owner.
16. Even when the ambient catalog already matches, the bundle must never label bare `id-<identity-id>` as `preferred_start_command` / `preferred_resume_command` unless `shortcut_shell_discoverability_status=PASS_REQUIRED` for the requesting shell; if current-shell discoverability is absent, the preferred lane must downgrade to a discoverability-safe generic or absolute launcher surface while leaving the short launcher visible only as a convenience/reference field.
17. Shell `command not found` is therefore a launcher-preflight shell ingress failure, not a post-launch runtime failure:
   - the shell either resolves `id-<identity-id>` or it does not;
   - if it does not, launcher code has not started yet;
   - protocol may detect that state, project it, and downgrade the preferred surface,
   - but protocol must not misdescribe that shell failure as a runtime resume failure that the launcher itself can recover after the command was never invoked.
18. Resume readiness is fail-close and decomposed:
   - host-thread UUID presence alone must **not** upgrade `resume_status` to `PASS_REQUIRED`;
   - `resume_status` may be `PASS_REQUIRED` only when the host thread id and the authoritative identity session tuple are both resolved;
   - when resume requires tuple closure, the recommended resume command must carry explicit `--session-id run:<...>` rather than promoting a short launcher shortcut that cannot encode that tuple.
19. The structured JSON bundle must therefore surface machine-readable readiness decomposition for at least:
   - `catalog_context_status`,
   - `host_thread_id_status`,
   - `identity_session_tuple_status`,
   - `resume_command_fresh_shell_executable_status`.
20. Semantic freeze for recovery correctness:
   - `resume <host-thread-uuid>` remains the Codex-side recovery target for prior transcript/state;
   - `--session-id run:<...>` is launcher-side tuple closure only;
   - the launcher must never substitute the session tuple for the host thread UUID, and must never reinterpret the host thread UUID as the session tuple.
21. When the embedded internal support bundle from `v1.6.16` recommends `consume_governed_reentry_brief`, the launcher-owned startup path must consume that governed brief through the canonical pack-local continuity guard and must emit/verify the governed runtime `instance_reentry_consumption_receipt` before any downstream Codex delegation.
22. That continuity bridge remains launcher-internal:
   - it must not invent a second user-facing startup command family,
   - it must not duplicate continuity semantics inside launcher code,
   - it must reuse the protocol-owned continuity bundle plus canonical pack-local producer path.

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
8. Current-state note (2026-03-26): launcher runtime authority is now frozen as a **three-part governed split**:
   - the shared bootstrap file under `${CODEX_HOME}/.identity/config/runtime-paths.env` owns only fresh-shell `IDENTITY_PROTOCOL_HOME` discovery for the generic launcher entry,
   - explicit runtime-selection surfaces (`source ./scripts/use_project_identity_runtime.sh`, `source ./scripts/use_local_identity_env.sh`, explicit `--catalog`) own current-shell `IDENTITY_HOME` / `IDENTITY_CATALOG`,
   - installed `id-<identity-id>` shortcut shims own identity-local runtime authority by exporting their bound `IDENTITY_HOME`, `IDENTITY_CATALOG`, and `IDENTITY_PROTOCOL_HOME` before delegating to the shared generic launcher.
9. Therefore launcher closure must distinguish bootstrap truth from explicit shortcut truth:
   - `IDENTITY_HOME` / `IDENTITY_CATALOG` drift inside the shared bootstrap file is an ambient-default observation surface, not a shortcut-closure blocker,
   - `IDENTITY_PROTOCOL_HOME` in that shared bootstrap file remains blocking because the generic fresh-shell entry still depends on it,
   - shortcut launcher closure is blocking on explicit identity/catalog/protocol-home binding inside the installed `id-<identity-id>` shim.
10. Current launcher closure therefore includes runtime-path authority as machine truth rather than as post-hoc operator knowledge:
   - `scripts/validate_identity_codex_launcher.py` now exports `runtime_paths_status`,
   - plus `runtime_paths_bootstrap_status`, `runtime_paths_protocol_home_status`, `shortcut_binding_status`, and `ambient_runtime_default_status`,
   - `scripts/check_identity_codex_launcher_migration_closure.py` now surfaces the same runtime-path closure family for aggregate active-runtime proof.
11. Live control-plane consumers are frozen accordingly:
   - required runtime gates,
   - readiness checks,
   - and `identity_creator` launcher auto-repair enforcement
   must all consume launcher closure in `workspace-runtime-only` mode so repo fixture catalogs never dilute active-runtime launcher proof.
12. The first cross-workspace pilot proof is now machine-landed through `scripts/ci/run_identity_codex_launcher_cross_workspace_pilot_probes_ci.sh`, which reuses the same convergence entry against another workspace-local runtime catalog inside a temporary workspace and temporary `CODEX_HOME` with no workspace-specific wrapper exception.
13. Current-state note (2026-03-22): that cross-workspace pilot now also freezes the direct-entry/runtime-authority edge conditions exposed by the `fqsh` feedback:
   - a fresh `run_identity_codex_launcher_workspace_convergence.py --mode apply` bundle must already be truth-synced, so an immediate `refresh_identity_codex_launcher_evidence_truth_sync.py --json-only` dry-run returns `PASS_REQUIRED` with zero manifest rewrites;
   - `check_identity_codex_launcher_migration_closure.py --catalog .identity/catalog.local.yaml` must resolve the **caller workspace** catalog rather than rebinding to the protocol repo;
   - `resolve_identity_context.py resolve --identity-id <id>` from a sibling workspace must classify the workspace-local runtime catalog as `source_layer=project` with `resolved_scope=USER` instead of degrading to `unknown`.
   - `identity-codex commands --identity-id <id>` and `id-<id> commands` must emit full copyable start/resume commands from protocol truth instead of requiring operators to manually assemble launcher invocations.
   - those copyable commands must be terminal-native direct commands (`id-<id> ...`, `identity-codex --identity-id <id> ...`), not shell-wrapped helper strings such as `zsh -lic '...'`.
   - `recommended_user_command` must remain protocol-owned, environment-aware, and fresh-shell executable: when the canonical short launcher is not discoverable on the current `PATH`, the bundle must switch to the absolute direct launcher path; when the ambient shell catalog mismatches the resolved identity catalog, it must emit explicit `--catalog`; when resume requires tuple closure, it must emit explicit `--session-id run:<...>` rather than promoting a stale short launcher.
   - launcher install truth and launcher shell-discoverability truth must remain separately machine-visible (`*_install_status` vs `*_shell_discoverability_status`) so “installed but not discoverable in this shell” is not misreported as either “not installed” or “runtime resume failed”.
   - the protocol-owned shell env loaders must expose `${CODEX_HOME}/bin` on `PATH` idempotently in fresh shells, so launcher availability is not left to manual operator shell edits; this PATH hardening reinforces the canonical install root rather than replacing it.
   - even under ambient catalog match, `preferred_start_command` / `preferred_resume_command` may use bare `id-<id>` only when the current shell actually resolves that shortcut; otherwise the preferred lane must downgrade to a discoverability-safe generic or absolute launcher surface while leaving the short launcher visible only as a reference field.
   - under `ambient_catalog_mismatch_requires_explicit_catalog`, the bundle must also align `preferred_start_command` / `preferred_resume_command` with that same canonical fresh-shell primary surface; any short launcher form may survive only as a reference/convenience field, not as the preferred operator surface.
   - host-thread UUID presence alone must not promote resume readiness; the machine-visible decomposition must distinguish `host_thread_id_status`, `identity_session_tuple_status`, and `resume_command_fresh_shell_executable_status`.
   - explicit `--continuity-intent migrate_new_window|reload_after_clear` is a governed operator-goal selector, not a new terminal command family; launcher command discovery must bridge to the `v1.6.16` reentry answer bundle rather than inventing continuity semantics locally.
   - that bridge must fail-close unless the consumed owner bundle still declares `identity_context_reentry_answer_bundle_status=PASS_REQUIRED`, `continuity_owner_stream=v1.6.16`, `question_family=identity_context_reentry_recovery`, and an admitted `bridge_admission_contract`; launcher-side default injection of any missing owner field is forbidden.
   - launcher machine output must therefore keep three facts separate instead of collapsing them: bridge integrity, owner semantic answer status, and launcher operator projection.
   - under that explicit fresh-window / clear-reload intent, `recommended_user_command` must promote the fresh-start launcher surface rather than transcript resume, while any resume command may survive only as a reference lane inside the same bundle.
   - if the bridged governed reentry answer is `FAIL_REQUIRED`, launcher command discovery must fail-close that operator goal instead of relabeling a bare fresh start as continuity closure.
   - if bridge integrity itself is not admitted, launcher command discovery must also fail-close the operator projection even when the owner answer row still renders a semantic `PASS` or `SKIPPED` value.
   - `identity-codex commands --identity-id <id> --json-only` must emit a structured command bundle (`recommended_user_command`, `copyable_commands`, `instance_answer_guidance`) so identity instances can answer concretely without inventing their own launcher logic.
   - `scripts/render_identity_codex_launcher.py` command-bundle output remains a governed launcher command bundle surface on an outer runtime-state layer.
   - It may project canonical start/resume commands and operator guidance, but it must not replace root-law owners, direct validator receipts, actor-session tuple truth, or host-thread recovery target authority.
   - It must not promote convenience/reference fields, shell-wrapper helper strings, or manual command assembly into canonical operator authority.
   - The command-bundle payload must self-describe this bounded authority in machine-readable form.
14. Current-state note (2026-03-26): the same cross-workspace pilot now also freezes the **repair status-profile split** for borrowed runtime catalogs:
   - the probe seeds a generic current-run projection failure inside the temporary borrowed workspace and proves `repair_contract_backfill.py` with `status_profile=strict_full` still fail-closes that identity;
   - the same borrowed workspace must still converge through `run_identity_codex_launcher_workspace_convergence.py --mode apply`, where `status_profile=launcher_workspace_convergence` keeps those current-run projection failures machine-visible as observation-only residuals instead of laundering them into launcher truth;
   - this boundary is additive only: launcher rollout may close workspace adoption, but it must not claim terminal-truth or weak-live closure for semantics still owned by other streams.
15. Current-state note (2026-03-26): the same status-profile split is now also frozen as a dedicated reusable CI surface under `scripts/ci/run_repair_contract_backfill_status_profile_probes_ci.sh`, so required gates and release readiness prove the shared primitive boundary directly rather than relying only on the broader cross-workspace pilot.
16. Current-state note (2026-03-26): borrowed-workspace probe setup is now also infrastructure-owned through `scripts/materialize_cross_workspace_runtime_probe_context.py` plus `scripts/cross_workspace_runtime_probe_context_common.py`, so sibling-runtime discovery, `.identity` materialization, and active-report selection stay shared across launcher probe families instead of drifting as duplicated shell-local logic.
17. Current-state note (2026-03-26): the seeded strict-profile fail-close precheck is now also shared through `scripts/run_repair_contract_backfill_strict_profile_probe.py` plus `scripts/repair_contract_backfill_strict_profile_probe_common.py`, so the cross-workspace pilot and the dedicated status-profile lane reuse the same failure-seeding and strict-assertion grammar instead of drifting as parallel embedded Python blocks.
18. Current-state note (2026-03-26): the single-identity launcher-convergence probe workspace is now likewise infrastructure-owned through `scripts/materialize_launcher_convergence_probe_context.py` plus `scripts/launcher_convergence_probe_context_common.py`, so the temporary runtime catalog materialization, pack copy, and launcher-asset stripping used by `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh` no longer drift as another embedded shell-local Python block.
19. Current-state note (2026-03-26): launcher convergence evidence-bundle assertion is now also infrastructure-owned through `scripts/validate_identity_codex_launcher_evidence_bundle.py` plus reusable inspection helpers in `scripts/identity_codex_launcher_evidence_common.py`, so manifest `summary_ref`, `evidence_records.kind`, and `mirror_path -> sha256` validation no longer drift as duplicated embedded Python across the convergence and cross-workspace pilot probe lanes.
20. Current-state note (2026-03-26): explicit relative local catalog paths now resolve caller-anchor-first in `scripts/resolve_identity_context.py`, so borrowed/temp workspace invocations such as `--catalog .identity/catalog.local.yaml` keep binding to the caller workspace even after launcher rollout writes runtime defaults into `${CODEX_HOME}/.identity/config/runtime-paths.env`; the convergence and cross-workspace probe lanes now also consume `scripts/validate_runtime_catalog_metadata_hygiene.py` for post-apply metadata proof instead of ad hoc YAML row inspection.
21. Current-state note (2026-03-26): that caller-anchor-first invariant is now also frozen as a dedicated owner validator through `scripts/validate_resolve_identity_context_default_local_catalog.py` plus the shared temp-workspace helper `scripts/resolve_identity_context_probe_common.py`; required gates and release readiness now consume that direct resolver proof instead of relying only on the broader launcher cross-workspace pilot to catch ambient runtime-default hijack regressions.
22. Startup continuity bridge note (2026-03-23, refined 2026-03-27): launcher ownership now also covers the first governed `v1.6.16` startup-consumer bridge through the same protocol-owned launcher path:
   - `scripts/identity_codex_launcher_common.py` must consume the internal continuity bundle rather than re-deriving continuity semantics ad hoc;
   - when the bundle reports `recommended_launcher_bind_mode=consume_governed_reentry_brief`, launcher-owned prelaunch preparation must invoke the canonical pack-local `run_identity_context_continuity_guard.sh post-recover --json-only` path before any downstream Codex delegation;
   - when the embedded continuity bundle is startup-ready but the receipt-family evidence is only recoverably stale (`missing migration_handoff` / joinable lineage drift), that same launcher-owned prelaunch preparation must first repair through the canonical pack-local `run_identity_context_continuity_guard.sh pre-migrate --json-only` path and only then consume `post-recover`, so the same short launcher surface remains valid across project-shell and fresh/global-shell resumes instead of depending on manual operator repair steps;
   - launcher may expose a governed `prepare-only` execution mode for this owner boundary, materializing continuity/bootstrap proof and returning structured launcher payload without claiming downstream Codex execution;
   - `scripts/ci/run_identity_codex_launcher_probes_ci.sh` must prove the real launcher-owned sequence `pre-migrate -> launcher prepare-only prelaunch materialization -> reentry-consumption-receipt` in an isolated runtime, not merely a dry-run prediction.
23. Audit follow-on closure note (2026-03-23): the formerly separate raw catalog metadata hygiene boundary is now protocol-owned and closed on `v1.6.10`:
   - `scripts/validate_runtime_catalog_metadata_hygiene.py` and `scripts/repair_runtime_catalog_metadata_hygiene.py` now own raw row self-description such as `canonical_scope` / `canonical_pack_path`;
   - `scripts/check_identity_codex_launcher_migration_closure.py` now projects `runtime_catalog_metadata_hygiene_status`;
   - launcher convergence probes seed stale metadata and prove apply-time repair through the same convergence entry.
   This remains **separate** from launcher semantics: launcher convergence stays closed, and raw metadata cleanup must not be folded back into `v1.6.14`.

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
   - the promotion package explicitly shows that the proposed framework is a consolidation of existing protocol assets (notification/trigger surfaces, protocol-feedback inbox/outbox, family convergence entries, probe/validator fact surfaces, receipt/manifest truth-sync) rather than a newly invented transport plane, side channel, or parallel command family;
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
   - dedicated status-profile boundary probes under `scripts/ci/run_repair_contract_backfill_status_profile_probes_ci.sh`,
   - active-runtime launcher migration closure checker under `scripts/check_identity_codex_launcher_migration_closure.py`,
   - protocol-owned workspace-level convergence entry under `scripts/run_identity_codex_launcher_workspace_convergence.py`,
   - governed launcher convergence evidence bundles whose receipts keep `evidence_ref` / `manifest_ref` machine-visible and whose archival root now carries `EVIDENCE_MANIFEST.<run_token>.json`,
   - post-closure truth-sync/backfill through `scripts/refresh_identity_codex_launcher_evidence_truth_sync.py` so earlier convergence receipts can be normalized without reopening launcher semantics, while fresh convergence applies already emit no-op truth-sync bundles on first dry-run,
   - strict lifecycle enforcement where `identity_creator validate` fail-closes on active-runtime launcher migration debt and `identity_creator update` performs governed auto-repair + recheck,
   - required-runtime-gates inclusion for the launcher probe lane and the status-profile boundary probe lane,
   - explicit `scripts/release_readiness_check.py` consumption of the convergence-entry probe lane, the status-profile boundary probe lane, and the aggregate launcher migration closure checker for readiness symmetry,
   - direct-entry resolver parity where sibling-workspace `resolve_identity_context.py` and relative `--catalog` closure checks both bind to the caller workspace runtime catalog rather than to protocol-repo defaults.
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
8. `scripts/render_protocol_lane_audit_summary.py` remains a single-lane formal control-plane summary surface on an outer runtime-state layer.
9. It must not replace root-law owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority.
10. The renderer must self-describe this bounded authority in machine-readable payload form.
11. The accepted maturity statement for this stream is scoped precisely as follows:
   - **for the `v1.6.14` identity-Codex-launcher lane**, the stream has advanced from topic governance into a protocol-owned formal control-plane subsystem,
   - current-state note (2026-03-22): `python3 scripts/validate_protocol_lane_isolated_historical_replay.py --repo-root identity-protocol-local --workspace-root . --commit HEAD --json-only` returned `PASS_REQUIRED` with `projection_parity_match=true`,
   - the isolated replay validator now keeps requested commit/diff scope machine-pinned to source history while materializing the current worktree as a governed baseline, so unrelated dirty multi-stream worktree edits no longer hijack single-lane replay scope,
   - pure committed-tree replay remains available as an explicit historical mode rather than being silently assumed by the default lane-summary replay path,
   - launcher convergence evidence truth-sync is now machine-landed through governed receipts plus `EVIDENCE_MANIFEST` archival bundles, so remaining work is limited primarily to legacy rollout and broader evidence breadth beyond the already-synced launcher convergence bundle family,
   - the isolated historical replay capability is landed, but the isolated-workspace caveat above still applies before anyone claims arbitrary full-tree historical replay,
   - reviewers must not restate the residual work as proof that launcher semantics remain unclosed.
