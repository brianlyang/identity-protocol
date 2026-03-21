# Protocol Remediation Audit Ledger (v1.6.14 identity-Codex launcher stream)

Status: Active (implementation closure landed, 2026-03-21; legacy fleet rollout continues)  
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
5. Pack-local launcher assets land only under `<pack_path>/scripts/launchers/`.
6. Installed launchers land only under `${CODEX_HOME}/bin/`.
7. Workspace `scripts/codex_native_chat/` remains compatibility bridge only until protocol-owned launcher assets land.
8. Launcher ownership of `model_instructions_file` and `project_doc_fallback_filenames` injection remains explicit and fail-close.

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
   - creator/update/activate and installer rollout wiring,
   - canonical pack-local launcher manifest + README,
   - canonical installed `identity-codex` and `id-<identity-id>` shims,
   - launcher probe lane `scripts/ci/run_identity_codex_launcher_probes_ci.sh`,
   - required-runtime-gates inclusion for the launcher probe lane.
4. Reviewers must not collapse `Architecture PASS` into `Implementation PASS`.

## 6) Accepted closure boundary

1. `v1.6.14` is closed at the implementation level when the command model, directories, ownership boundary, launcher assets, installed shims, and probe lane are all machine-verifiable together.
2. The workspace bridge may remain operational after that closure, but only as bridge-only compatibility evidence.
4. This stream is independent from provider/MCP runtime incidents and from host-final visible-surface promotion work.

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
