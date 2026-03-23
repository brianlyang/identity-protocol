# Identity Protocol v1.6 Deep Audit Workbook

Status: Canonical intake and routing workbook
Layer: protocol
Scope: serial deep-audit intake for the `v1.6` workbook family, radiating over the active `v1.6.x` stream lanes
Authority boundary: this workbook is canonical only as the protocol-side intake/routing surface selected by `identity/protocol/mappings/workbook-registry.current.yaml`; it does not override `docs/workbook/protocol-issue-register-v1.6.md` for current status authority.

## 0) Fixed role boundary

1. This workbook exists to concentrate scattered issue discovery into one protocol-owned routing surface inside `identity-protocol-local`.
2. It is allowed to span multiple stream files and owner lanes because the cleanup family itself crosses the current `v1.6.x` stream set.
3. It must not drift into a second semantic SSOT; stream semantics still belong to owner governance docs and owner review ledgers under `docs/governance/` and `docs/review/`.
4. Status mirroring in this file must remain byte-for-byte consistent with `docs/workbook/protocol-issue-register-v1.6.md`.
5. Optional workspace projections may mirror this workbook for operator convenience, but they never outrank this protocol-internal intake surface.

## 1) Current control-plane alias refs

- `identity/protocol/mappings/workbook-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`

## 2) Current machine recheck lock

- `scripts/validate_issue_register_consistency.py --json-only` -> `PASS_REQUIRED`
- `scripts/docs_command_contract_check.py` -> `PASS` (`docs checked: 87`, `command snippets checked: 938`)
- `scripts/validate_native_chat_bootstrap_entry_stream.py --json-only` -> `PASS_REQUIRED` with `promotion_status=PROMOTION_REVIEW_ELIGIBLE`

## 3) Root-cause clusters (compressed)

### RC-01 Stream integration model is still partial

Symptoms:

- active stream docs can land in registry without corresponding scope-matrix completion;
- stream-opening validator can pass while motherline/supporting matrices remain incomplete.
- required-gate bundle order can lag behind newly added motherline rows, leaving new stream requirements outside strict bundle coverage even after contract-binding is updated.
- contract-first stream docs can also land with executable snippets and required current-alias references that the repository cannot yet satisfy, turning the doc-contract checker red after the stream is registered.



Root cause:

- stream registration and stream-scope completeness are not enforced by one end-to-end completeness gate, required-gate bundle parity still relies on a frozen manual requirement order that can miss newly added motherline rows, and stream doc publication can still outrun executable/current-alias closure on newly opened lanes.

### RC-02 Authority and compatibility concerns are still colocated

Symptoms:

- strict consumer code still carries compatibility-pointer diagnostics or references;
- some live status/validator surfaces still read `session/active_identity.json` directly.



Root cause:

- authority consumers, replay/compiled consumers, and compatibility/status consumers are not enforced as separate classes at the API boundary.

### RC-03 Anti-forget guards are parser- and launch-context-fragile

Symptoms:

- drift guard can report missing lineage even when the delegate really invokes the required scripts through variables;
- probe suite and tracked fixture can silently diverge;
- multiple validators still depend on caller cwd because `--repo-root` defaults to `.`.
- operational control-plane tools still depend on caller cwd outside the repaired validator lane, so workspace-root and protocol-root launches diverge or fail.
- the authoritative identity resolver still picks its default local catalog from the ambient parent git root on workspace-root launches, so omission of `--local-catalog` can break project-local resolution even when the canonical workspace `.identity/catalog.local.yaml` is present.
- several active direct-entry scripts still bind `--repo-catalog` to the caller launch root, so the same project-local replay fails from the workspace root and advances from the protocol root.
- some older operational validators still derive `repo_root = Path.cwd().resolve()` internally, so even absolute governed inputs can flip pass/fail across workspace-root and protocol-root launches.



Root cause:

- text matching, fixture snapshot assumptions, and cwd-relative repo-root defaults are doing work that should be handled by semantic invocation parsing plus self-rooted fixture/live parity enforcement; launch-context invariance was fixed piecemeal for validators and some operational tools, but not yet generalized into direct-entry `--repo-catalog` defaults, hidden `Path.cwd()` repo-root consumers, or the machine gates that should exercise those paths directly.

### RC-04 Historical baseline docs still act as live defaults and active anchors

Symptoms:

- `v1.6.0` governance and `v1.6` review docs still appear as default builder/validator inputs;
- `contract-binding` still anchors many live rows back into the large historical motherline docs;
- prompt-bootstrap and protocol SSOT docs still reuse the historical motherline as active anchor instead of pure archive context.



Root cause:

- historical traceability assets were not fully demoted after stream extraction; they remain in active defaults.

### RC-05 Old-version-named active carriers were never normalized

Symptoms:

- `*.current.yaml` resolves to older-version active files across mapping/plugin surfaces;
- plugin registry and evidence allowlist still use older version names as current carriers.



Root cause:

- current-pointer semantics were layered on top of versioned filenames, but the naming strategy was never re-normalized once those files became long-term active carriers.

### RC-06 Shared infra exists, but adoption is not enforced

Symptoms:

- temp/probe shared helpers exist;
- multiple live scripts still default to `/tmp` or direct `mktemp -d /tmp/...` usage.
- machine checkers exist for docs and catalog-default hygiene, but they still miss launch-context-broken executable snippets and direct-entry repo-catalog defaults.



Root cause:

- shared infra was introduced as an available helper, not as an enforced construction pattern; the corresponding checkers were built around syntax/flag presence and pattern scans, not around governed launch-context execution semantics.

### RC-07 `v1.6.12` standard closure and promotion closure are properly separated, and promotion proof now depends on governed continuity evidence rather than flaky smoke alone

Symptoms:

- stream opening stays closed even when host-runtime smoke remains inconclusive;
- promotion no longer depends on live smoke alone and is now lifted by a governed continuity bundle on the controlled emitter path;
- unrelated control-plane reds must not be allowed to reopen the headstamp lane once the continuity bundle has satisfied the promotion proof contract.



Root cause:

- host-runtime smoke is not stable enough to be the sole promotion proof source; the repaired lane therefore has to force validator-required probe names, tracked fixture contents, live-suite expectations, and governed continuity compensation to evolve together as one machine evidence bundle.

### RC-08 Compatibility mirror semantic demotion is incomplete at terminology/schema layer

Symptoms:

- runtime/repair/status tooling correctly treats `session/active_identity.json` as non-authoritative, but still names it `canonical_session_pointer` in helper names, payload fields, and receipts;
- this leaves the compatibility-mirror semantic boundary correct in some places and linguistically polluted in others.



Root cause:

- semantic demotion from “canonical pointer” to “compatibility mirror” was enforced at authority rules first, but not fully normalized across helper naming and payload schema.

### RC-09 Top-level kernel/release metadata keeps drifting back into active gating

Symptoms:

- the original `v1.4.10`/`v1.5` top-level story was removed, but the same lane still drifts whenever the active draft head advances without the other top-level release markers moving with it;
- `identity/protocol/IDENTITY_PROTOCOL.md` now advertises `v1.6.14` while `README.md`, `VERSIONING.md`, and `requirements-dev.txt` still advertise `v1.6.13`;
- active readiness/e2e/upgrade flows still execute the release metadata validator, so this drift immediately re-enters machine gating instead of remaining a harmless doc lag.



Root cause:

- top-level overview/release markers were repaired once, but the repo still lacks a single machine-maintained draft-head writer for all four top-level markers; active gates therefore keep inheriting whichever marker drifts last, even after the original legacy baseline has been removed.

### RC-10 Direct global-home catalog fallback still bypasses project runtime selection

Symptoms:

- the original deep audit reproduced active entrypoints defaulting to `~/.codex/.identity/catalog.local.yaml` instead of shared runtime-path resolution or explicit runtime-catalog authority;
- that defect used to create “false green on the wrong catalog” behavior across project-local identities and launch-context-sensitive replays;
- current resolver / strict-entry / semantic-clarity lanes are now green, so the remaining RC-10 tail is metadata hygiene and regression prevention rather than live precedence ambiguity.



Root cause:

- the original root cause was a `v1.4.x`-era family of direct global-home catalog defaults that outlived the newer runtime-path contract; resolver / launcher / strict-entry closure has now removed that live leak, so remaining RC-10 work is raw metadata backfill and regression prevention, not active fallback semantics.

### RC-11 No motherline no-downgrade rule freezes compatibility surfaces to migration-only

Symptoms:

- earlier deep scans found live compatibility residue on multiple surfaces: shared pointers were treated as warning-level drift, helper interfaces exposed drift-allow semantics, active scaffolds normalized legacy overlays/aliases, and canonical docs still lacked a bottom-layer no-downgrade clause;
- the motherline rule is now frozen and the live pointer/control-plane leak has been closed, so the remaining RC-11 surface is residual helper/doc truth-sync and regression prevention;
- any future compatibility, fallback, or bridge wording must stay quarantined to migration/replay/diagnostic lanes and must not re-enter active defaults, validator green paths, current-turn truth, active execution entry, or protocol-owned success paths.

Root cause:

- the original root cause was the absence of one explicit motherline principle saying compatibility, fallback, and bridge surfaces are migration/replay/diagnostic-only and may not re-enter active defaults, validator green paths, or current-turn runtime truth; `rq_047_protocol_no_downgrade_motherline_contract_v1` now freezes that principle, so the remaining RC-11 work is residual cleanup/truth-sync and regression prevention rather than missing motherline definition.

### RC-12 Route/lane governance still begins too late in the execution chain

Symptoms:

- declared route contracts can look complete for the route -> instance-script -> receipt path while real rescue execution still happens through direct MCP/browser tool calls in conversation;
- browser-manual/editor-interactive lanes can become the only live-success path without being declared in `allowed_execution_lanes`, so the system achieves success outside the governed lane family instead of through it;
- some packs carry only receipt/emitter/recovery helper scripts in `INSTANCE_SCRIPT_MANIFEST.json`, leaving no instance-owned business executor that can actually own lane choice, auth preflight, or session freshness before tools fire.

Root cause:

- `v1.6.15` currently hardens the route -> instance-script -> lane-admission chain, but direct conversation-level tool execution is not yet required to enter through that chain; as a result, undeclared live rescue lanes can still succeed outside protocol-owned route/lane admission.
- protocol closure note (2026-03-23): the shared owner lane now closes this blind spot at protocol level by freezing additive direct-tool admission plus the canonical execution-lane taxonomy for webhook and interactive direct-tool lanes. Remaining browser-manual rollout gaps are instance-owned adoption debt, not missing protocol semantics.

### RC-13 Third/fourth-loop source contracts exist, but runtime-consumable strengthening symmetry is still missing

Symptoms:

- `identity/protocol/IDENTITY_PROTOCOL.md` already freezes the third/fourth source contracts as `Auto-routing contract` and `Rule learning contract`, so the kernel has not forgotten these loops;
- the active runtime contract family and validator family already touch nearby surfaces such as orchestration, knowledge acquisition, experience feedback, discovery requiredization, and capability arbitration;
- `scripts/ci/run_required_runtime_gates_ci.sh` already executes those validators, proving the problem is not complete absence from required CI;
- active packs such as `office-ops-expert` and `custom-creative-ecom-analyst` already expose `accurate_judgement_enforcement` and `reasoning_loop_enforcement` under `capability_arbitration_contract`, but do not yet expose symmetric `route_discovery_enforcement` / `feedback_operational_prompt_enforcement` hooks;
- the third loop still lacks one frozen roundtable/vendor/reference/runtime-probe four-track cross-validation primitive, so AI-parallel discovery can degrade into scattered probes rather than governed serial convergence;
- the fourth loop still lacks the same shared cross-validation primitive plus a governed loop-back into the first loop, so prompt optimization can drift into self-reinforcing injection instead of returning through multimodal accurate judgement;
- required-gate bundle status and release-readiness projection still do not expose the same class of loop-level strengthening citizenship for the third/fourth loops that the protocol already provides for the first two.

Root cause:

- the protocol froze the third/fourth loops at kernel-source level and partial validator/runtime-contract level, but never fully lifted them into symmetric upper-layer strengthening surfaces that instances can consume as first-class runtime capability primitives while preserving independent third-loop and fourth-loop centers over one shared four-track cross-validation primitive plus a fourth-loop-to-first-loop governed reentry path.

### RC-14 Fourth-loop-to-first-loop loopback semantics can still collapse into generic fourth-loop wording unless frozen as a distinct bridge

Symptoms:

- `ASB16-RQ-048` / `ASB16-RQ-049` are now machine-landed for third/fourth-loop strengthening, but the 4→1 return path can still be misread as merely a fourth-loop sub-bullet unless it is tracked as its own semantic object;
- the shared `roundtable_four_track_cross_validation_contract_v1` primitive can be misclassified as the loopback bridge unless the bridge is named and bounded separately;
- without a standalone bridge contract, prompt-derived artifacts can drift semantically toward “current-round truth” instead of staying governed preflight aids that must re-enter first-loop revalidation;
- workbook/register surfaces previously had no standalone row to keep this bridge open as docs-owned debt after `ISSUE-030` closure.

Root cause:

- the protocol now has independent third-loop and fourth-loop strengthening centers plus a shared four-track primitive, but the fourth-loop-to-first-loop reentry path still needs its own frozen bridge contract (`feedback_to_judgement_loopback_contract_v1`) so that promotion evidence, prompt derivation, and first-loop truth are not semantically collapsed into one object.

### RC-15 Protocol artifact families remain semantically overloaded under generic "memory" wording

Symptoms:

- pack-root `RULEBOOK.jsonl` and runtime `runtime/rulebooks/*.jsonl` are easy to miscall as one undifferentiated rule memory;
- `TASK_HISTORY.md` can be misread as continuity or recovery state instead of chronology;
- runtime dialogue-governance, experience-feedback, protocol-feedback, and continuity families already exist but were frozen in separate owner streams with no single motherline routing matrix;
- `runtime/memory-absorption/**` is path-registered and therefore easy to over-read as an active generic sink unless explicitly quarantined;
- declaration keys and gates such as `reject_memory_gate` or `*_contract` blocks are easy to misreport as if they were the storage family itself.

Root cause:

- the protocol froze individual lanes over time, but it never froze one cross-family routing matrix that classifies protocol-owned persisted artifacts by semantic owner, fixed path family, payload class, production method, and primary consumer. Without that matrix, multiple distinct families keep collapsing into generic “memory” wording.

## 4) Routed issue sections

### ISSUE-001 - Active stream scope matrix incompleteness

- `status`: CLOSED
- `problem_statement`: `v1.6.11` and `v1.6.12` are present in stream registry but missing from active stream-scope matrix.
- `primary_owner_doc`: `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.8.md`
  - `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
- `machine_gate`: `scripts/validate_stream_scope_semantic_integrity.py`
- `root_cause`: RC-01
- `stop_condition`:
  - `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml` includes `v1.6.11` and `v1.6.12`;
  - validator no longer fails on missing row;
  - future-stream completeness is checked in a way that does not depend only on touched diff docs.

### ISSUE-002 - Strict authority consumer still touches compatibility pointer literal

- `status`: CLOSED
- `problem_statement`: strict response-stamp consumer path still reads `session/active_identity.json` literal.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
- `machine_gate`: `scripts/validate_response_authority_consumer_semantics.py`
- `root_cause`: RC-02
- `stop_condition`:
  - strict authority consumers no longer directly read compatibility pointer files;
  - any compatibility diagnostics are routed through exempt replay/status consumers only.

### ISSUE-003 - Required-gate drift validator remains parser- and launch-context-fragile

- `status`: CLOSED
- `problem_statement`: delegated script lineage and repo-root resolution are still launch-context fragile; the validator can report missing lineage on variable-based shell invocation and can false-red when launched outside the protocol repo root.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
- `machine_gate`: `scripts/validate_required_gate_surface_drift.py`
- `root_cause`: RC-03
- `stop_condition`:
  - variable-based invocation and literal invocation are treated equivalently by the drift validator;
  - current host-visible delegate no longer appears as false-red;
  - strict validators produce the same verdict regardless of caller cwd.

### ISSUE-004 - Historical baseline docs still behave as live defaults

- `status`: CLOSED
- `problem_statement`: live builder/validator defaults no longer point directly to `v1.6.0` governance and `v1.6` review historical motherline docs; the remaining historical literals are frozen to explicit checker/traceability surfaces only.
- `primary_owner_doc`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `machine_gate`:
  - `scripts/validate_historical_baseline_default_boundary.py`
- `root_cause`: RC-04
- `stop_condition`:
  - active builder/validator defaults no longer route through historical motherline docs unless explicitly requested for replay/traceability;
  - machine gate proves the only remaining literals live in explicit checker surfaces, not runtime default resolution.

### ISSUE-005 - Old-version-named active carriers remain current pointers

- `status`: CLOSED
- `problem_statement`: multiple `*.current.yaml` pointers still resolve to old-version-named active files, but those carriers are now explicitly frozen as intentional compatibility aliases instead of incidental drift.
- `primary_owner_doc`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `machine_gate`:
  - `scripts/validate_current_alias_versioned_carrier.py`
- `root_cause`: RC-05
- `stop_condition`:
  - explicit naming strategy is frozen;
  - versioned current carriers carry `pointer_contract=frozen_versioned_active_carrier`, `upgrade_switch_mode=pointer_only`, and `replay_snapshot_immutable=true`, and the machine gate validates them.

### ISSUE-006 - Temp/probe shared infra is not mandatory yet

- `status`: CLOSED
- `problem_statement`: shared temp-path helper now backs the remaining live temp/probe surfaces that were still defaulting to `/tmp` or direct `mktemp`.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `machine_gate`:
  - `scripts/validate_runtime_temp_path_contract.py`
- `root_cause`: RC-06
- `stop_condition`:
  - live scripts and probe runners converge on shared temp-path helpers or an equivalently frozen contract.
  - targeted machine gate blocks reintroduction of direct `/tmp` and raw probe `mktemp` usage on the repaired surfaces.

### ISSUE-007 - Batch-6/7 compatibility wrapper residue closure

- `status`: CLOSED
- `problem_statement`: the reopened active-pack residue is now closed: protocol strict targets remain canonical, active runtime-pack `CURRENT_TASK.json` surfaces are inventoried from the local runtime catalog, and the stale `validate_v16_*` literals were backfilled to canonical validator ids.
- `primary_owner_doc`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
- `machine_gate`:
  - `scripts/validate_active_validator_alias_residue.py`
  - supporting evidence scan: `rg -n '"validator": "scripts/validate_v16_' .identity/*/CURRENT_TASK.json`
- `root_cause`: RC-04 and RC-05
- `stop_condition`:
  - wrappers remain explicitly classified as replay-only compatibility aliases in contract-binding;
  - protocol strict targets continue using canonical validator ids only;
  - active runtime-pack `CURRENT_TASK.json` task surfaces stay backfilled to canonical validator ids;
  - the machine gate continues covering both protocol strict targets and active runtime-pack inventory discovered from the local catalog.

### ISSUE-008 - Archived `v1.6.9` remains a semantic pollution risk

- `status`: CLOSED
- `problem_statement`: `v1.6.9` is archived, but still remains present in active registry/evidence references and is therefore still easy to reuse as if it were an active stream.
- `primary_owner_doc`: `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.8.md`
  - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
- `machine_gate`:
  - currently social/documentation discipline; no explicit active-citation guard yet.
- `root_cause`: RC-01 and RC-05
- `stop_condition`:
  - active/archived citation boundary is frozen in docs and, if needed, enforced by a doc-level guard.

### ISSUE-009 - `v1.6.12` promotion-lane parity drift is closed on the current branch

- `status`: CLOSED
- `problem_statement`: validator-required promotion probes, tracked fixture manifest, and live suite behavior were previously drifting; current-branch recheck confirms that this drift no longer reproduces and the owner governance/review lane now reflects the repaired state.
- `primary_owner_doc`: `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md`
  - `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `machine_gate`:
  - `scripts/validate_native_chat_bootstrap_entry_stream.py`
  - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh`
- `root_cause`: RC-03 and RC-07
- `stop_condition`:
  - tracked fixture manifest contains every required promotion probe;
  - live suite passes fully;
  - validator-required probe names, fixture manifest, and live suite are parity-checked by one mechanism;
  - owner governance/review surfaces explicitly record that this lane is no longer an active red residual.

### ISSUE-010 - Compatibility pointer still carries canonical-pointer terminology in live tooling

- `status`: CLOSED
- `problem_statement`: compatibility mirror files and payloads are no longer labeled as `canonical_session_pointer` in live runtime/repair/status tooling; live payloads now use compatibility-only terminology.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `machine_gate`:
  - `scripts/validate_compatibility_pointer_terminology.py`
- `root_cause`: RC-08
- `stop_condition`:
  - live helper names, payload field names, and receipt fields stop presenting compatibility mirror paths as canonical session pointers;
  - machine gate validates the renamed compatibility-only terminology on every repaired live surface.

### ISSUE-011 - Validator repo-root resolution is still cwd-coupled

- `status`: CLOSED
- `problem_statement`: multiple active validators still default `--repo-root` to `.`, so machine verdicts can change with caller cwd instead of being invariant to launch location.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `machine_gate`:
  - `scripts/validate_stream_scope_semantic_integrity.py`
  - `scripts/validate_required_gate_surface_drift.py`
  - supporting evidence scan: `rg -n 'add_argument\\(\"--repo-root\", default=\"\\.\"\\)' scripts/validate_*.py`
- `root_cause`: RC-03
- `stop_condition`:
  - strict validators self-resolve repo root from script/repo location or canonical contract instead of caller cwd;
  - equivalent invocations from parent repo and protocol repo produce the same verdict.

### ISSUE-012 - Top-level release metadata drift against the active draft head

- `status`: CLOSED
- `problem_statement`: the rebound release-metadata drift is re-closed: `README.md`, `VERSIONING.md`, and `requirements-dev.txt` now move in lock-step with `identity/protocol/IDENTITY_PROTOCOL.md`, so the active draft head no longer diverges across top-level markers.
- `primary_owner_doc`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
- `machine_gate`:
  - `scripts/validate_release_metadata_sync.py`
  - supporting live surfaces: `scripts/release_readiness_check.py`, `scripts/e2e_smoke_test.sh`, `scripts/execute_identity_upgrade.py`
- `root_cause`: RC-09
- `stop_condition`:
  - every top-level draft-head marker (`IDENTITY_PROTOCOL.md`, `README.md`, `VERSIONING.md`, `requirements-dev.txt`) moves in lock-step with the active draft head;
  - `scripts/validate_release_metadata_sync.py` returns `PASS_REQUIRED` again without weakening the validator or hardcoding a stale version token.

### ISSUE-013 - Stream-doc command and current-alias contract drift closure

- `status`: CLOSED
- `problem_statement`: the doc-command/current-alias drift is now closed: the checker is repo-root invariant, understands workspace-owned script references, the affected `v1.6.11` / `v1.6.13` docs now carry their required `*.current.yaml` alias refs, and `IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` now references the canonical prompt-kernel executable coupling validator.
- `primary_owner_doc`: `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `secondary_refs`:
  - `docs/governance/agent-relay-final-answer-governance-v1.6.11.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.11-agent-relay-final-answer.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md`
  - `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
- `machine_gate`:
  - `scripts/docs_command_contract_check.py`
- `root_cause`: RC-01 and RC-04
- `stop_condition`:
  - current stream governance/review docs continue including every required `*.current.yaml` alias ref enforced by the checker;
  - command snippets continue referencing live validator paths only;
  - `python3 scripts/docs_command_contract_check.py` stays clean from both workspace root and protocol root.

### ISSUE-014 - Legacy compatibility taxonomy has crossed into an active machine-gate default

- `status`: CLOSED
- `problem_statement`: former `WATCH-001` is now closed as issue-grade debt: compiled-brief pass-default surfaces were moved onto the neutral token `tracked_compiled_brief_frozen_path`, while `legacy_canonical_compatibility_path` is explicitly narrowed to governance/migration taxonomy and no longer serves as the positive compiled-brief gate token.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/p0-compiled-brief-directory-taxonomy-governance-plan-2026-03-18.md`
- `machine_gate`:
  - `scripts/validate_compiled_brief_projection_boundary.py`
  - `scripts/ci/run_semantic_clarity_probes_ci.sh`
  - `scripts/validate_compatibility_legacy_boundary.py`
- `root_cause`: RC-03 and RC-08
- `stop_condition`:
  - compiled-brief positive validation and semantic-clarity CI stop requiring `legacy_canonical_compatibility_path` as a PASS-default token; satisfied.
  - compatibility terminology remains outside current-turn authoritative payloads and strict visible lanes; satisfied.
  - the old watch claim is replaced by a machine-checked taxonomy that no longer depends on the legacy term; satisfied via `tracked_compiled_brief_frozen_path`.

### ISSUE-015 - Batch-6/7 active docs still normalize compatibility wrappers as canonical executables

- `status`: CLOSED
- `problem_statement`: active `v1.6.0` / `v1.6` governance-review docs were canonicalized to non-versioned executables, `contract-binding.v1.6.yaml` now records the remaining versioned aliases as `wrapper_compatibility_optional`, and `scripts/validate_contract_binding_reference_integrity.py` now fail-closes on doc executable-role drift instead of checking anchors only.
- `primary_owner_doc`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `identity/protocol/mappings/contract-binding.v1.6.yaml`
  - `scripts/create_identity_pack.py`
- `machine_gate`:
  - `scripts/validate_contract_binding_reference_integrity.py`
  - supporting evidence scan: `rg -n 'validate_v16_intake_evidence_core.py|validate_v16_cross_workflow_schema.py|validate_v16_skill_path_integrity.py' docs/governance/identity-actor-session-binding-governance-v1.6.0.md docs/review/protocol-remediation-audit-ledger-v1.6.md identity/protocol/mappings/contract-binding.v1.6.yaml`
- `root_cause`: RC-01 and RC-04
- `stop_condition`:
  - active governance/review docs switch canonical validator/normalizer refs to the non-versioned ids already used in mapping/scaffolding; satisfied.
  - wrapper ids appear only as explicit compatibility aliases where mapping says they are optional; satisfied.
  - the checker grows executable-role parity validation so docs cannot drift back while still returning a false green; satisfied.

### ISSUE-016 - Required-gate bundle parity for new motherline rows `ASB16-RQ-042` / `ASB16-RQ-043`

- `status`: CLOSED
- `problem_statement`: the initial bundle-parity red was caused by `required_gate_bundle_runner.py` stopping at `asb16-rq-041` while `contract-binding.v1.6.yaml` already carried `ASB16-RQ-042` / `ASB16-RQ-043`.
- `primary_owner_doc`: `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `secondary_refs`:
  - `docs/governance/agent-relay-final-answer-governance-v1.6.11.md`
  - `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.11-agent-relay-final-answer.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md`
- `machine_gate`:
  - `scripts/validate_control_plane_budget.py`
  - `scripts/validate_control_plane_invariants.py`
  - `scripts/validate_control_plane_status_sync.py`
- `root_cause`: RC-01 and RC-03
- `stop_condition`:
  - required-gate bundle order or its generator absorbs `asb16-rq-042` and `asb16-rq-043`; satisfied.
  - control-plane budget and invariants return `mapping_rows_missing_in_bundle_count=0`; satisfied.
  - machine-maintained control-plane budget/status refresh lands without hand-editing and status sync returns `PASS_REQUIRED`; satisfied.

### ISSUE-017 - Operational repo-root invariance outside the repaired validator lane

- `status`: CLOSED
- `problem_statement`: repo-root/cwd invariance had been repaired only for validators; operational tooling still depended on caller cwd until this pass generalized self-resolution.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `machine_gate`:
  - direct replay: `python3 identity-protocol-local/scripts/render_control_plane_status.py --json-only`
  - direct replay: `python3 identity-protocol-local/scripts/sync_plugin_join_wiring.py --check --json-only`
  - direct replay: `python3 scripts/scan_identity_path_residue.py --identity-id <ID> --json-only`
- `root_cause`: RC-03
- `stop_condition`:
  - operational control-plane tools self-resolve protocol/workspace roots from script location or governed catalog semantics instead of caller cwd; satisfied.
  - workspace-root and protocol-root launches yield the same semantic verdict or fail-close for the same reason; satisfied.
  - the path-residue scanner can discover project-local identity homes without manual `--repo-root` pinning; satisfied.

### ISSUE-018 - `v1.6.14` launcher stream docs-contract red

- `status`: CLOSED
- `problem_statement`: the new `v1.6.14` launcher lane did introduce a real docs-contract red: the review ledger initially omitted a required current-alias reference and overpromoted future launcher scripts into executable-looking snippets.
- `primary_owner_doc`: `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
  - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
  - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
- `machine_gate`:
  - `scripts/docs_command_contract_check.py`
  - downstream visibility: `scripts/validate_control_plane_status_sync.py`
- `root_cause`: RC-01
- `stop_condition`:
  - the `v1.6.14` review/governance docs carry every required current-alias reference enforced by the checker; satisfied.
  - any launcher command snippet promoted to executable status points at landed scripts only; satisfied.
  - `python3 scripts/docs_command_contract_check.py` returns clean from both workspace root and protocol root without special casing this lane; satisfied.

### ISSUE-019 - Authoritative resolver default local catalog ambient-root coupling

- `status`: CLOSED
- `problem_statement`: the authoritative resolver now self-roots its default local catalog to the project runtime, so omitting `--local-catalog` no longer changes the resolved source layer/canonical pack tuple between workspace-root and protocol-root replays.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `scripts/validate_resolve_identity_context_default_local_catalog.py`
- `machine_gate`:
  - direct replay: `python3 identity-protocol-local/scripts/resolve_identity_context.py resolve --identity-id base-repo-architect`
  - invariant replay: `python3 identity-protocol-local/scripts/validate_resolve_identity_context_default_local_catalog.py --json-only`
- `root_cause`: RC-03
- `stop_condition`:
  - authoritative default resolution self-roots to the active project runtime from both workspace and protocol roots when `--local-catalog` is omitted;
  - omission of `--local-catalog` no longer changes the resolved source layer for the same project-local identity;
  - a machine gate covers the direct authoritative-resolve path rather than only scanning `--catalog` repo-fixture defaults.

### ISSUE-020 - Active script default catalog routing on scope/state/repair surfaces

- `status`: CLOSED
- `problem_statement`: the affected scope/state/repair scripts now default through shared runtime-path semantics, so omitting `--catalog` no longer silently falls back to `~/.codex/.identity/catalog.local.yaml` for active project-local work.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
- `machine_gate`:
  - direct replay: `python3 identity-protocol-local/scripts/validate_identity_scope_resolution.py --identity-id base-repo-architect`
  - direct replay: `python3 identity-protocol-local/scripts/validate_identity_scope_persistence.py --identity-id base-repo-architect`
  - direct replay: `python3 identity-protocol-local/scripts/validate_identity_state_consistency.py`
  - static guard: `python3 identity-protocol-local/scripts/validate_cli_catalog_default_semantics.py --json-only`
- `root_cause`: RC-10
- `stop_condition`:
  - active scope/state/repair scripts stop embedding direct `~/.codex/.identity/catalog.local.yaml` defaults;
  - omission of `--catalog` either resolves through shared runtime-path semantics or fail-closes explicitly instead of silently validating the wrong catalog;
  - a machine gate scans for direct global-home catalog defaults on active scripts referenced by current protocol contracts.

### ISSUE-021 - Active direct-entry scripts still bind `--repo-catalog` to caller launch root

- `status`: CLOSED
- `problem_statement`: the direct-entry lane previously resolved bare `--repo-catalog identity/catalog/identities.yaml` against caller cwd; it is now closed by a shared resolver plus parity replays that keep workspace-root and protocol-root launches on the same semantic surface.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `scripts/validate_cli_catalog_default_semantics.py`
- `machine_gate`:
  - workspace/protocol parity replay: `python3 identity-protocol-local/scripts/validate_fixture_runtime_boundary.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
  - workspace/protocol parity replay: `python3 identity-protocol-local/scripts/validate_protocol_entry_candidate_bridge.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --json-only`
  - workspace/protocol parity replay: `python3 identity-protocol-local/scripts/render_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --actor-id assistant:codex --session-id test-session --json-only`
- `root_cause`: RC-03
- `stop_condition`:
  - active direct-entry scripts self-root default `--repo-catalog` to the protocol repository or a shared path-resolution helper instead of caller cwd;
  - the same relative/default replay yields the same semantic result from workspace-root and protocol-root launches;
  - a dedicated machine gate exercises direct-entry repo-catalog defaults rather than only scanning for global-home catalog literals.
- `closure_evidence`:
  - `scripts/resolve_identity_context.py` now exports `resolve_repo_catalog_path(...)`, and the three direct-entry scripts consume it.
  - `python3 identity-protocol-local/scripts/validate_cli_catalog_default_semantics.py --json-only` now returns `launch_context_parity_status=PASS_REQUIRED` with green replays for `validate_fixture_runtime_boundary.py`, `validate_protocol_entry_candidate_bridge.py`, and `render_identity_response_stamp.py`.

### ISSUE-022 - `validate_identity_local_persistence.py` still derives repo root from caller cwd

- `status`: CLOSED
- `problem_statement`: the local-persistence lane previously mixed `Path.cwd()` repo-root semantics with non-self-rooted local-catalog defaults; it is now closed by shared repo/local catalog resolvers that produce the same governed interpretation from workspace-root and protocol-root launches.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/local-instance-persistence-boundary-v1.4.6.md`
  - `scripts/release_readiness_check.py`
  - `scripts/e2e_smoke_test.sh`
- `machine_gate`:
  - workspace/protocol parity replay: `python3 identity-protocol-local/scripts/validate_identity_local_persistence.py --repo-catalog /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/catalog/identities.yaml --local-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
  - supporting direct replay: `python3 identity-protocol-local/scripts/identity_status.py --identity-id base-repo-architect --json`
- `root_cause`: RC-03
- `stop_condition`:
  - local-persistence and adjacent operational tooling resolve repo root from script/protocol location instead of `Path.cwd()`;
  - default local-catalog selection for these tools self-roots to the project runtime when no explicit catalog/env override is supplied;
  - workspace-root and protocol-root replays with the same absolute inputs produce the same verdict.
- `closure_evidence`:
  - `validate_identity_local_persistence.py` now derives its protocol root from the resolved repo catalog and passes from both workspace root and protocol root with the same absolute governed inputs.
  - `identity_status.py`, `collect_identity_health_report.py`, `validate_identity_experience_writeback.py`, and the scope validators now self-root default local catalogs to the project runtime.

### ISSUE-023 - Docs command checker still misses launch-context-broken executable snippets

- `status`: CLOSED
- `problem_statement`: the docs checker previously stopped at executable existence/flag syntax and could not distinguish a workspace-safe command from a protocol-root-only launch-context fragment; it is now closed by workspace semantic probes plus workspace-root invariant active snippets on the affected lane.
- `primary_owner_doc`: `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
- `secondary_refs`:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
  - `scripts/docs_command_contract_check.py`
- `machine_gate`:
  - `python3 identity-protocol-local/scripts/docs_command_contract_check.py`
  - correlated replay: `python3 identity-protocol-local/scripts/render_identity_response_stamp.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --actor-id assistant:codex --session-id test-session --json-only`
- `root_cause`: RC-06
- `stop_condition`:
  - the docs checker validates launch-context/path semantics for executable snippets, not just script presence and flag names;
  - active docs stop publishing executable commands whose relative path arguments fail from workspace-root replays;
  - doc checker green and direct replay green become coupled on this lane.
- `closure_evidence`:
  - `scripts/docs_command_contract_check.py` now recognizes workspace-root invariant `identity-protocol-local/scripts/...` commands and runs workspace semantic probes for safe path-sensitive executables.
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.md` now publish workspace-root invariant commands on the cited headstamp/actor-session-binding snippets.

### ISSUE-024 - `v1.6.14` launcher convergence runtime authority and cross-workspace pilot proof were not yet machine-frozen

- `status`: CLOSED
- `problem_statement`: the launcher convergence lane had already landed the canonical entry, receipt family, and synthetic convergence probes, but runtime-path authority still was not part of formal launcher closure, live control-plane consumers still mixed launcher closure with non-runtime catalog scope, and cross-workspace pilot proof remained a discussion goal instead of a machine-executed proof lane.
- `primary_owner_doc`: `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
  - `docs/governance/identity-codex-launcher-workspace-convergence-roundtable-v1.6.14.md`
  - `scripts/ci/run_required_runtime_gates_ci.sh`
- `machine_gate`:
  - `scripts/validate_identity_codex_launcher.py`
  - `scripts/check_identity_codex_launcher_migration_closure.py`
  - `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`
  - `scripts/ci/run_identity_codex_launcher_cross_workspace_pilot_probes_ci.sh`
  - supporting consumers: `scripts/release_readiness_check.py`, `scripts/identity_creator.py`
- `root_cause`: RC-03 and RC-06
- `stop_condition`:
  - launcher install validation proves both asset presence and runtime-path authority against the selected workspace-local runtime catalog; satisfied.
  - aggregate launcher closure proof, required gates, readiness, and creator enforcement all consume launcher closure in `workspace-runtime-only` mode rather than mixing repo fixture catalogs into live runtime proof; satisfied.
  - the same convergence entry is machine-proven against more than one workspace-local runtime catalog with no workspace-specific wrapper exception; satisfied for the launcher pilot proof lane.
  - generic workspace-convergence promotion remains deferred; closer follow-on work stays on evidence breadth / archival / truth-sync rather than on semantic reopening; satisfied.
- `closure_evidence`:
  - launcher runtime authority is now surfaced as `runtime_paths_status` in both the single-identity validator and the aggregate launcher migration-closure checker.
  - `install_identity_codex_launcher.py` now writes launcher config under the launcher config home while binding `IDENTITY_HOME` / `IDENTITY_CATALOG` to the selected runtime catalog surface.
  - the cross-workspace pilot probe now copies a sibling workspace runtime catalog into a temporary workspace, rewrites pack paths to the copied runtime surface, and proves dry-run/apply/closure/validator parity on the same convergence entry with no workspace-specific wrapper branch.
  - launcher convergence receipts now keep `evidence_ref` / `manifest_ref` machine-visible, emit governed `EVIDENCE_MANIFEST.<run_token>.json` bundles under `activity/evidence/v1614-identity-codex-launcher/<date>/`, and the post-closure truth-sync surface `scripts/refresh_identity_codex_launcher_evidence_truth_sync.py` can normalize older convergence receipts without reopening launcher semantics.
  - `scripts/release_readiness_check.py` now consumes the convergence-entry probe lane itself, so readiness symmetry covers both the aggregate closure checker and the governed receipt/manifest truth-sync bundle.

### ISSUE-025 - Authoritative resolver and active health entrypoints now freeze explicit runtime-catalog authority; remaining raw metadata hygiene stays separate

- `status`: CLOSED
- `problem_statement`: the deep audit originally reproduced a live precedence bug on the authority resolver family: the foreign-project env precedence lane in `scripts/ci/run_semantic_clarity_probes_ci.sh` failed because `scripts/resolve_identity_context.py` did not consume `IDENTITY_CATALOG` as the runtime-local catalog unless `--local-catalog` was passed explicitly, while several active utility surfaces still derived default catalogs from script-root path heuristics instead of explicit runtime-catalog authority.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `identity/protocol/IDENTITY_RUNTIME.md`
  - `scripts/validate_cli_catalog_default_semantics.py`
- `machine_gate`:
  - `scripts/ci/run_semantic_clarity_probes_ci.sh`
  - `scripts/validate_cli_catalog_default_semantics.py`
  - direct replay: `python3 scripts/resolve_identity_context.py resolve --identity-id global-authority --repo-catalog identity/catalog/identities.yaml`
- `root_cause`: RC-03, RC-10, and RC-11
- `stop_condition`:
  - `resolve_identity_context.py` consumes explicit runtime-catalog authority (`--local-catalog` / `IDENTITY_CATALOG`) before any script-root-derived fallback and the foreign-project precedence lane turns green; satisfied.
  - active health/runtime utilities stop embedding script-root catalog defaults on current runtime surfaces and either resolve through the shared runtime-path contract or fail-close explicitly; satisfied.
  - launch-context parity stays machine-checked from both workspace-root and protocol-root launches; satisfied.
- `closure_evidence`:
  - `bash scripts/ci/run_semantic_clarity_probes_ci.sh` now passes both `foreign project env ignored when current project has no session pointer` and `current project session pointer wins over foreign project env`.
  - `python3 scripts/validate_cli_catalog_default_semantics.py --json-only` now reports `cli_catalog_default_semantics_status=PASS_REQUIRED`, zero runtime global-home default hits, and launch-context parity across workspace-root/protocol-root replays.
  - resolver truth now stays closed while any remaining raw catalog metadata underdescription is tracked separately by `ISSUE-029`.

### ISSUE-026 - Session-primary authority now fail-closes compatibility drift; remaining compatibility work stays quarantined

- `status`: CLOSED
- `problem_statement`: protocol runtime originally could hold the correct session-primary authoritative identity while the shared compatibility pointer family (`session/active_identity.json` + `session/mirror/current.json`) still pointed at an older identity; active health/status tooling downgraded that state to warning-level drift and the canonical repair surface rebuilt pointer payloads from actor-global compatibility projection state rather than from current session-primary truth.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
  - `scripts/repair_actor_session_authority_residue.py`
- `machine_gate`:
  - `scripts/validate_identity_session_pointer_consistency.py`
  - `scripts/refresh_identity_session_status.py`
  - `scripts/collect_identity_health_report.py`
  - supporting runtime feedback: `system-requirements-analyst` active-runtime re-entry report
- `root_cause`: RC-02 and RC-11
- `stop_condition`:
  - current runtime health/status surfaces stop classifying compatibility-pointer drift as warn-level residue once session-primary truth is available; satisfied.
  - protocol-owned convergence rewrites canonical/mirror pointer surfaces from authoritative `(actor_id,session_id)->identity_id` truth first and treats compatibility projection as diagnostic metadata only; satisfied.
  - pointer-drift repair/convergence becomes a protocol-owned fail-close lane rather than a repeated manual/operator interpretation problem; satisfied.
- `closure_evidence`:
  - `python3 scripts/validate_identity_switch_closure_semantics.py --json-only` now returns `PASS_REQUIRED` with `compatibility_pointer_identity_authority=diagnostic_only`.
  - `scripts/refresh_identity_session_status.py` now classifies stale/missing compatibility projection under available session-primary truth as `POINTER_FAIL`, not warning-level drift.
  - `scripts/collect_identity_health_report.py` now invokes the pointer guard through `--strict-session-primary`, and `scripts/repair_actor_session_authority_residue.py` rebuilds canonical/mirror pointer surfaces from authoritative binding first.
  - `scripts/validate_identity_session_pointer_consistency.py` no longer exposes the old `--allow-compatibility-projection-drift` interface residue on strict lanes.

### ISSUE-027 - Motherline no-downgrade contract is now frozen and live residue is quarantined off active payloads

- `status`: CLOSED
- `problem_statement`: the bottom-layer no-downgrade / no-backstop / no backward-compatibility rule is frozen, and the remaining live compatibility residue has now been pushed off active payload surfaces. The closure target was not “invent a new principle” but “hold the existing principle everywhere so active defaults, validator green paths, current-turn runtime truth, active execution entry, and protocol-owned success paths do not regress back into compatibility behavior.”
- `primary_owner_doc`: `identity/protocol/IDENTITY_PROTOCOL.md`
- `secondary_refs`:
  - `identity/protocol/IDENTITY_RUNTIME.md`
  - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`
  - `identity/protocol/mappings/contract-binding.v1.6.yaml`
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
- `machine_gate`:
  - `scripts/validate_compatibility_legacy_boundary.py`
  - `scripts/validate_strict_actor_entry_semantics.py`
  - `scripts/validate_identity_switch_closure_semantics.py`
  - `scripts/validate_identity_session_pointer_consistency.py`
  - `scripts/validate_identity_runtime_contract.py`
  - `scripts/validate_identity_collab_trigger.py`
  - supporting audit scan: `rg -n 'legacy_alias_bridge|legacy-commerce-overlay|assistant:codex|compatibility backstop|backward compatibility' identity/protocol docs scripts`
- `root_cause`: RC-11
- `stop_condition`:
  - `rq_047_protocol_no_downgrade_motherline_contract_v1` remains frozen in protocol kernel text, contract binding, governance, and review surfaces;
  - active scaffold/validator/helper families stay green only when compatibility residue is quarantined away from active defaults, validator green paths, current-turn runtime truth, active execution entry, and protocol-owned success paths;
  - active governed payload families keep canonical `error_code` only; replay/migration alias echo is explicit rather than implicit;
  - canonical docs/workbook/review truth stays synchronized so residual wording cannot quietly reopen downgrade/backstop semantics.
- `closure_evidence`:
  - `identity/protocol/IDENTITY_PROTOCOL.md` now freezes `rq_047_protocol_no_downgrade_motherline_contract_v1`;
  - `identity/protocol/mappings/contract-binding.v1.6.yaml` now binds the rule as `ASB16-RQ-047`;
  - `identity/protocol/IDENTITY_RUNTIME.md` now hard-freezes active-runtime no-downgrade semantics, including current-turn truth, active entry, and validator-green-path boundaries;
  - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml` now explicitly says the protocol does not provide backward compatibility on active surfaces;
  - `scripts/headstamp_error_family_common.py` now keeps active payload projection canonical-only by default and requires explicit replay/migration opt-in before alias echo can appear;
  - `scripts/validate_compatibility_legacy_boundary.py --json-only` now returns `PASS_REQUIRED` only when active payload projection stays canonical-only and replay alias echo remains explicit/quarantined;
  - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md` truth-syncs that `legacy_error_code` / `compat_error_code` are replay-only and forbidden on active governed payload surfaces.

### ISSUE-028 - Declared route/script lane governance is now protocol-owned; remaining browser-manual gaps are instance adoption only

- `status`: CLOSED
- `problem_statement`: `v1.6.15` originally left a protocol-owned blind spot because direct MCP/browser rescue could still feel extra-contractual. The shared owner lane now closes that gap generically: direct tool entry must enter via route/script/lane admission or fail closed, and the canonical execution-lane taxonomy now freezes both webhook and interactive direct-tool lanes without importing business-scene semantics. Remaining browser-manual rollout gaps belong to pack adoption, not protocol semantics.
- `primary_owner_doc`: `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
  - `scripts/instance_script_orchestration_common.py`
  - `scripts/validate_route_execution_lane_admission.py`
  - `scripts/validate_identity_capability_activation.py`
- `machine_gate`:
  - `scripts/validate_route_execution_lane_admission.py`
  - `scripts/validate_identity_capability_activation.py`
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
  - supporting live adoption audit: target-pack route/manifest/session evidence scan
- `root_cause`: RC-12 and RC-11
- `stop_condition`:
  - direct tool execution for a declared route must either enter through route/script/lane admission or fail-close before MCP/browser tools run;
  - browser/manual rescue, when it is a legitimate supported lane, must be expressed through the canonical lane taxonomy rather than private pack-local token invention;
  - remaining target-pack business executor rollout, auth preflight scripts, session-freshness scripts, and optional skill binding stay below protocol once the shared lane family is closed.
- `closure_evidence`:
  - the protocol-owned validator family freezes additive `direct_tool_entry_policy` semantics on top of the existing execution-lane contract; declared direct-tool lanes must use canonical `lane_source=governed_direct_tool_entry`, carry `receipt_timing=pre_tool_execution`, and report `tool_entry_admission_timing`, `auth_preflight_status`, and `session_freshness_status` through the shared `instance_script_admission_receipt` validator instead of relying on pack-local narrative;
  - `scripts/instance_script_orchestration_common.py` now also freezes the canonical execution-lane taxonomy for current supported generic lanes: `governed_webhook` -> `webhook_single_flight` + `analysis_webhook`, and `governed_direct_tool_entry` -> `tool_admission_serialized` + `interactive_session`;
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh` now proves positive direct-tool admission plus negative fail-close on missing `direct_tool_entry_policy`, mismatched `tool_entry_admission_timing`, and mismatched direct-tool lane taxonomy;
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md` now truth-sync that remaining browser-manual gaps are instance adoption only and must not be misreported as missing protocol semantics.

### ISSUE-029 - Workspace-local runtime catalog metadata hygiene is now protocol-owned and closed on its own lane

- `status`: CLOSED
- `problem_statement`: the raw metadata follow-on that used to remain after resolver repair is now owned by a dedicated protocol hygiene lane rather than by launcher semantics. Runtime resolver truth stays authority-first, while raw workspace-local catalog self-description is now validated and repaired directly through shared infrastructure.
- `primary_owner_doc`: `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
  - `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
- `machine_gate`:
  - `scripts/validate_runtime_catalog_metadata_hygiene.py`
  - `scripts/repair_runtime_catalog_metadata_hygiene.py`
  - `scripts/check_identity_codex_launcher_migration_closure.py`
  - `scripts/run_identity_codex_launcher_workspace_convergence.py`
  - `scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh`
  - `scripts/ci/run_identity_codex_launcher_cross_workspace_pilot_probes_ci.sh`
- `root_cause`: RC-03 and RC-10
- `stop_condition`:
  - raw workspace-local runtime catalog rows become self-descriptive enough that protocol-owned truth no longer needs to correct `canonical_scope=UNKNOWN`-class residue for healthy rows;
  - creator/backfill-equivalent hygiene tooling normalizes catalog metadata without changing the already-correct resolver truth path;
  - the cleanup remains explicitly separate from `v1.6.14` launcher semantics, so launcher convergence stays closed while metadata hygiene advances on its own lane.
- `current_evidence`:
  - `python3 scripts/validate_runtime_catalog_metadata_hygiene.py --catalog ../.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --require-active --json-only` now returns `PASS_REQUIRED` with `checked_identity_count=4`, `violation_count=0`;
  - `scripts/check_identity_codex_launcher_migration_closure.py --catalog ../.identity/catalog.local.yaml --workspace-runtime-only --json-only` now projects `runtime_catalog_metadata_hygiene_status=PASS_REQUIRED` alongside launcher closure for all active runtime identities;
  - `scripts/run_identity_codex_launcher_workspace_convergence.py` now performs metadata hygiene repair before launcher closure, and both launcher convergence probe families seed `canonical_scope=UNKNOWN` / empty `canonical_pack_path` and prove apply-time repair;
  - required gates and readiness now consume `scripts/validate_runtime_catalog_metadata_hygiene.py`, so raw metadata hygiene is no longer an informal follow-on note.

### ISSUE-030 - Routing/learning strengthening symmetry is now landed as a protocol-owned upper-layer runtime contract

- `status`: CLOSED
- `problem_statement`: the protocol kernel already froze the third/fourth source contracts as `Auto-routing contract` and `Rule learning contract`; the remaining work was to land symmetric runtime-consumable strengthening above them. That symmetry is now protocol-owned: packs can carry the strengthening hooks, validators can fail-close them, and required-gate/readiness surfaces now project them directly.
- `primary_owner_doc`: `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md`
  - `identity/protocol/IDENTITY_PROTOCOL.md`
  - `/Users/yangxi/.codex/.identity/office-ops-expert/CURRENT_TASK.json`
  - `/Users/yangxi/claude/codex_project/weixinstore/.identity/custom-creative-ecom-analyst/CURRENT_TASK.json`
- `machine_gate`:
  - `scripts/validate_identity_routing_learning_strengthening.py`
  - `scripts/validate_identity_capability_arbitration.py`
  - `scripts/validate_discovery_requiredization.py`
  - `scripts/validate_capability_fit_roundtable_evidence.py`
  - `scripts/validate_identity_orchestration_contract.py`
  - `scripts/validate_identity_knowledge_contract.py`
  - `scripts/validate_identity_experience_feedback.py`
  - `scripts/validate_identity_experience_feedback_governance.py`
  - `scripts/required_gate_bundle_runner.py`
  - `scripts/release_readiness_check.py`
- `root_cause`: RC-13
- `stop_condition`:
  - third-loop strengthening lands above the kernel `Auto-routing contract` as a symmetric runtime-consumable binding with explicit route-discovery convergence evidence;
  - fourth-loop strengthening lands above the kernel `Rule learning contract` as a symmetric runtime-consumable binding with scoped operational-prompt injection, replay verification, and rollback semantics;
  - both loops consume the same `roundtable_four_track_cross_validation_contract_v1` primitive without introducing a fallback/backstop compatibility bridge;
  - active packs gain governed `route_discovery_enforcement` and `feedback_operational_prompt_enforcement` surfaces beside the already-landed first-two-loop hooks;
  - required-gate bundle and release-readiness surfaces project the strengthened third/fourth loops as first-class citizenship.
- `current_evidence`:
  - `create_identity_pack.py` and `repair_contract_backfill.py` now materialize `route_discovery_enforcement` / `feedback_operational_prompt_enforcement` under `capability_arbitration_contract`;
  - `scripts/validate_identity_routing_learning_strengthening.py` now fail-closes the strengthening pair and currently returns `PASS_REQUIRED` for all four active workspace-local runtime identities (`base-repo-audit-expert-v3`, `custom-creative-ecom-analyst`, `base-repo-architect`, `base-repo-closure-orchestrator`);
  - `scripts/validate_identity_capability_arbitration.py` now consumes the strengthening hooks directly and replays `Capability arbitration contract validation PASSED` across the same four active runtime identities;
  - `required_gate_bundle_runner.py` now binds `ASB16-RQ-048` / `ASB16-RQ-049`, while `scripts/ci/run_required_runtime_gates_ci.sh` and `scripts/release_readiness_check.py` now include the strengthening validator family;
  - the strengthening lane remains generic protocol infrastructure only: no business-specific routing policy, prompt content, or backward-compatibility bridge was introduced.

### ISSUE-031 - Fourth-loop-to-first-loop loopback bridge is now machine-consumed and closed without semantic collapse back into ISSUE-030

- `status`: CLOSED
- `problem_statement`: the third/fourth-loop strengthening centers were landed under `ISSUE-030`, and the remaining 4→1 return path required its own explicit machine consumer lane so that fourth-loop prompt artifacts could not be misread as first-loop truth, and the shared four-track primitive could not be misread as the loopback transport/admission surface.
- `primary_owner_doc`: `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md`
  - `identity/protocol/mappings/contract-binding.v1.6.yaml`
  - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`
- `machine_gate`:
  - `scripts/docs_command_contract_check.py`
  - `scripts/validate_issue_register_consistency.py`
  - `scripts/validate_contract_binding_reference_integrity.py`
  - `scripts/validate_identity_routing_learning_strengthening.py`
  - `scripts/validate_feedback_to_judgement_loopback.py`
  - `scripts/ci/run_feedback_to_judgement_loopback_probes_ci.sh`
- `root_cause`: RC-14
- `stop_condition`:
  - `feedback_to_judgement_loopback_contract_v1` remains frozen as a standalone bridge contract rather than being folded into either the fourth-loop center or the shared four-track primitive;
  - loopback artifacts are explicitly bounded as governed preflight aids only, never as current-round truth;
  - the bounded closed-loop topology (`third-loop exploration -> fourth-loop promotion -> first-loop revalidation`) is machine-visible as a round trip rather than a narrative claim;
  - first-loop revalidation authority, TTL expiry, conflict demotion, rollback, and negative-feedback writeback are all machine-visible on the canonical bridge evidence family;
  - a dedicated machine consumer lane can consume `ASB16-RQ-050` without reopening `ISSUE-030` or weakening no-downgrade boundaries.
- `current_evidence`:
  - `scripts/validate_feedback_to_judgement_loopback.py` now owns the canonical `ASB16-RQ-050` machine consumer lane and fail-closes on replay-gate drift, missing loopback field anchors, broken first-loop revalidation prerequisites, or missing negative-feedback preservation;
  - `scripts/validate_identity_routing_learning_strengthening.py` now republishes the same closed-loop proof as `third_loop_exploration_status`, `fourth_loop_promotion_status`, `first_loop_revalidation_status`, `conflict_demotion_status`, `negative_feedback_writeback_status`, and `live_roundtrip_proof_status`, so the bounded round trip stays machine-visible without reopening the third/fourth-loop center;
  - `scripts/required_gate_bundle_runner.py`, `scripts/release_readiness_check.py`, and `scripts/ci/run_required_runtime_gates_ci.sh` now consume the dedicated loopback validator lane directly, while `scripts/ci/run_feedback_to_judgement_loopback_probes_ci.sh` proves positive and negative fixture coverage plus round-trip projection assertions;
  - `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`, `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md`, and `identity/protocol/mappings/contract-binding.v1.6.yaml` now truth-sync the bridge as machine-consumed closure instead of a docs-only opening.

### ISSUE-032 - Protocol artifact-family routing remains semantically overloaded under generic "memory" wording

- `status`: OPEN
- `problem_statement`: protocol-owned persisted artifact families inside identity packs/runtime already exist, but they are still too easy to collapse into generic “memory” language. Without one routing matrix, pack rulebook, pack task-history, runtime dialogue-governance, runtime experience-feedback, runtime protocol-feedback, runtime continuity/reentry, and runtime memory-absorption quarantine can be semantically polluted into one bucket.
- `primary_owner_doc`: `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md`
- `secondary_refs`:
  - `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md`
  - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`
  - `identity/protocol/IDENTITY_PROTOCOL.md`
  - `identity/protocol/IDENTITY_RUNTIME.md`
  - `README.md`
- `machine_gate`:
  - `scripts/docs_command_contract_check.py`
  - `scripts/validate_issue_register_consistency.py`
- `root_cause`: RC-15
- `stop_condition`:
  - one canonical matrix freezes each protocol-owned persisted family by semantic owner, fixed path, payload class, production method, and primary consumer;
  - `memory` is no longer used as a canonical sink name in active protocol docs for these families;
  - `RULEBOOK.jsonl` stays distinct from runtime experience-feedback rulebooks;
  - `TASK_HISTORY.md` stays distinct from continuity/reentry state;
  - raw dialogue retention stays distinct from dialogue-governance summaries and continuity/reentry bind artifacts;
  - `runtime/protocol-feedback/**` stays governance communication-only;
  - `runtime/memory-absorption/**` stays quarantine/re-materialization only;
  - at least one machine-consumed family landing proves the matrix can drive shared validator/creator/readiness/runtime-hook wiring without per-pack folklore;
  - later broader matrix enforcement reuses the same matrix instead of re-deriving semantics pack by pack.
- `current_evidence`:
  - `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` now freezes the canonical routing matrix across eight protocol-scoped persisted families and explicitly classifies declaration keys/gates as non-artifact control-plane surfaces;
  - `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md` now records the current protocol/runtime scan basis, the new raw dialogue-retention family, and the quarantine-only interpretation of `runtime/memory-absorption/**`;
  - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`, `identity/protocol/IDENTITY_PROTOCOL.md`, `identity/protocol/IDENTITY_RUNTIME.md`, and `README.md` now truth-sync the family names, fixed paths, forbidden conflations, and `rq_051_identity_dialogue_retention_contract_v1`;
  - `scripts/identity_dialogue_retention_common.py`, `scripts/run_identity_dialogue_retention_guard_runtime.py`, `scripts/run_identity_delivery_runtime_hooks.py`, `scripts/validate_identity_dialogue_retention.py`, and `scripts/ci/run_identity_dialogue_retention_probes_ci.sh` now land the first machine-consumed family closure for this stream;
  - `scripts/create_identity_pack.py`, `scripts/repair_contract_backfill.py`, `scripts/release_readiness_check.py`, `scripts/ci/run_required_runtime_gates_ci.sh`, `scripts/validate_required_contract_coverage.py`, and `scripts/required_gate_bundle_runner.py` now consume the same family instead of leaving raw dialogue truth routing as docs-only guidance.

## 5) Architecture reinforcement intake (non-reopen, workbook-routed)

1. The rows below capture desensitized follow-on reinforcement for active streams; they are routed through this workbook so the protocol architect can land them on canonical governance/review surfaces without reopening the closed `ISSUE-001..024` correctness family.
2. These rows are routing/intake metadata only; semantic ownership remains with the target stream governance doc and its review ledger.

### RF-ORCH-001 - Aggregate route-scope/cardinality projection closure

- `classification`: architecture reinforcement intake, non-reopen
- `judgment`: landed shared builders/validators now freeze aggregate capability-activation artifacts as multi-route summaries rather than route-scoped receipts, so the protocol-owned requirement is explicit scope/cardinality projection instead of a synthetic `route_selected`.
- `canonical_landings`:
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- `implementation_follow_on`:
  - `scripts/instance_script_orchestration_common.py`
  - `scripts/validate_identity_capability_activation.py`
  - `scripts/validate_route_script_receipt_join.py`
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
- `machine_acceptance`:
  - aggregate artifacts reuse one canonical field family: `route_scope`, `route_scope_mode`, `route_activation_strategy`, `route_ready_count`, `route_total_count`, `route_ids`, and `route_selection_cardinality`;
  - route-scoped admission/execution/emit/recovery receipts continue requiring `route_selected` and keep `route_scope_mode=route_receipt` plus `route_ids=[route_selected]`;
  - validator/probe coverage fail-closes if an artifact claims single-route scope without route provenance or drifts into parallel alias vocabulary.
- `non_goals`:
  - do not invent an arbitrary selected route for aggregate `route-any-ready` status;
  - do not weaken `route_selected` on route-scoped receipts;
  - do not mint parallel aliases such as `projection_scope`, `route_count`, or `cardinality`.

### RF-ORCH-002 - Declared-vs-observed dependency projection closure

- `classification`: architecture reinforcement intake, non-reopen
- `judgment`: landed shared builders/validators now standardize one declared-vs-observed dependency projection across route-scoped and aggregate artifacts instead of leaving the diff fragmented across report families.
- `canonical_landings`:
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- `implementation_follow_on`:
  - `scripts/instance_script_orchestration_common.py`
  - `scripts/validate_route_script_receipt_join.py`
  - `scripts/validate_identity_capability_activation.py`
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
- `machine_acceptance`:
  - declared dependencies, observed activations/executions, and gap reasons are machine-visible through `declared_dependency_projection`, `observed_dependency_projection`, `dependency_gap_reasons`, `undeclared_usage_*`, and `missing_declared_dependency_*`;
  - undeclared observed usage and missing declared dependency are surfaced through one governed gap model rather than per-artifact narrative-only wording;
  - the same declared/observed projection stays reusable across route-scoped and aggregate artifacts where applicable.
- `non_goals`:
  - do not replace machine-readable diff with narrative-only explanations;
  - do not absorb instance-specific business heuristics into dependency provenance;
  - do not create pack-local dependency dialects outside the shared validator/probe/control family.

### RF-ORCH-003 - Semantic-anchor extension-hook gap

- `classification`: architecture reinforcement intake, non-reopen
- `judgment`: downstream semantic narrowing can occur even when route/script orchestration remains correct; protocol should carry a generic semantic-anchor envelope by ref/schema/digest rather than domain-specific business fields.
- `canonical_landings`:
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- `implementation_follow_on`:
  - `scripts/instance_script_orchestration_common.py`
  - `scripts/validate_route_script_receipt_join.py`
  - `scripts/validate_identity_capability_activation.py`
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
- `machine_acceptance`:
  - anchor ref/schema/source/revision/digest/status remain machine-visible;
  - downstream consumers cannot silently drop a declared anchor without a governed mismatch signal;
  - partial anchor families fail closed once any anchor field is emitted;
  - aggregate promotion occurs only under single-family, non-ambiguous projection across contributing route rows;
  - anchor projection remains on the shared validator/probe/control path.
- `non_goals`:
  - do not freeze product-specific keywords, scoring models, or supplier logic into protocol SSOT;
  - do not reinterpret semantic-anchor support as protocol ownership of downstream business judgment.

### RF-ORCH-004 - Outcome sentinel reference-hook gap

- `classification`: architecture reinforcement intake, non-reopen
- `judgment`: protocol needs a way to reference downstream risk signals without promoting business KPIs or thresholds into the core orchestration contract.
- `canonical_landings`:
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- `implementation_follow_on`:
  - `scripts/instance_script_orchestration_common.py`
  - `scripts/validate_route_script_receipt_join.py`
  - `scripts/validate_identity_capability_activation.py`
  - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
  - release/audit consumers only when a stream explicitly opts into sentinel gating
- `machine_acceptance`:
  - sentinel ref/schema/status remain machine-visible when present;
  - partial sentinel families fail closed once any sentinel field is emitted;
  - aggregate promotion occurs only under single-family, non-ambiguous projection across contributing route rows;
  - advisory vs fail-close semantics are explicit;
  - sentinel support does not bypass route/script/dependency provenance requirements.
- `non_goals`:
  - do not freeze universal business scoring thresholds in protocol core;
  - do not use sentinel refs to relabel business drift as proof that orchestration semantics are wrong.

### RF-ORCH-005 - Role-boundary non-substitution matrix gap

- `classification`: architecture reinforcement intake, non-reopen
- `judgment`: the stream already freezes that instance scripts do not replace skills / MCP / tools, but review can still drift unless the four-role matrix and non-substitution rule become an explicit canonical clause.
- `canonical_landings`:
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- `implementation_follow_on`:
  - reviewer boundary wording only where a natural diagnostic surface already exists
  - no standalone fake machine gate for semantic misuse wording
- `machine_acceptance`:
  - `agent/codex`, `identity instance/scripts`, `skills/scripts`, and `mcp/tool` roles are explicitly separated;
  - protocol review wording classifies “identity instance/scripts must replace skill business scripts” as semantic misuse rather than contract defect;
  - the reinforcement stays on the existing shared consumer / review motherline without reopening inherited streams.
- `non_goals`:
  - do not reinterpret identity-pack instance scripts as a replacement for business execution libraries;
  - do not use this reinforcement to smuggle category heuristics, pricing logic, SKU semantics, or other business vocabulary into protocol SSOT.

## 6) Frozen operating rule

1. New scans must update the owning stream docs and machine gates before a row here can move to `CLOSED`.
2. This workbook may aggregate evidence, but it may not locally reinterpret already-frozen owner semantics.
3. This workbook remains protocol-internal; no external mirror may supersede it.
