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
- `scripts/docs_command_contract_check.py` -> `PASS` (`docs checked: 82`, `command snippets checked: 891`)
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

- multiple active scope/state/repair scripts still default straight to `~/.codex/.identity/catalog.local.yaml` instead of shared runtime-path resolution or explicit `--catalog`;
- the same command therefore fails for project-local identities unless the caller manually supplies the project catalog, or worse, silently passes against the wrong global tenant;
- this produces “false green on the wrong catalog” behavior, which is more dangerous than an explicit fail-close.



Root cause:

- project-runtime selection has been hardened in some core entrypoints, but a separate older script family still carries direct global-home catalog defaults from the `v1.4.x` era; because these scripts remain active and are still referenced by current protocol contracts, the old default semantics continue to leak into live validation and repair paths.

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

## 5) Architecture reinforcement intake (non-reopen, workbook-routed)

1. The rows below capture desensitized follow-on reinforcement for active streams; they are routed through this workbook so the protocol architect can land them on canonical governance/review surfaces without reopening the closed `ISSUE-001..023` correctness family.
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
