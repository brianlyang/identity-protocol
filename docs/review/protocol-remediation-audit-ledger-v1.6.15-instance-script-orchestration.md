# Protocol Remediation Audit Ledger (v1.6.15 instance-script orchestration stream)

Status: Active (contract freeze plus core validator/readiness landing, 2026-03-21; broader rollout still in progress)  
Scope: protocol review ledger for route -> instance-script declarative join, pack-local script manifest governance, and execution receipt-family modeling

## 0) Stream objective

1. Freeze the canonical route-to-script additive fields under `CURRENT_TASK.json`.
2. Freeze the canonical pack-local script manifest path under pack-root `scripts/`.
3. Freeze the lower-capability join model that connects instance scripts to skills, MCP servers, and tool pipelines.
4. Freeze the canonical receipt-family interpretation for governed instance-script execution.

## 1) Problem statement frozen for audit

1. `v1.6.13` made pack-root `scripts/` canonical, and `v1.6.14` made identity-bound launcher/startup governance explicit, but neither stream froze how governed routes bind to pack-local scripts.
2. Without a dedicated orchestration stream, teams can still drift into:
   - filename-based script discovery,
   - undocumented route-to-script pairing,
   - lower-capability dependencies declared only in human prose,
   - per-pack receipt conventions that do not compose.
3. That ambiguity encourages recurring misdiagnosis between:
   - protocol orchestration debt,
   - instance migration debt,
   - lower capability availability failures,
   - runtime dirt,
   - outer-delivery gaps.
4. The stream exists to freeze the orchestration join without reopening topology, launcher, bootstrap, or relay semantics.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces

1. `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
5. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
6. `identity/protocol/IDENTITY_PROTOCOL.md`
7. `identity/protocol/IDENTITY_RUNTIME.md`
8. `identity/protocol/mappings/control-plane-status.current.yaml`
9. `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md`
10. Landed implementation surfaces for this stream now include:
   - `scripts/validate_identity_instance_script_orchestration.py`
   - `scripts/validate_instance_script_manifest.py`
   - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - `scripts/release_readiness_check.py`
   - `scripts/validate_identity_capability_activation.py`
11. Remaining follow-on implementation targets are:
   - `scripts/validate_route_script_receipt_join.py`
   - shared creator/backfill consumers that still need the same contract family

### 2.2 Workspace / instance-owned surfaces consumed by this stream

1. `CURRENT_TASK.json` route entries under `capability_orchestration_contract.task_type_routes`.
2. Pack-local manifest destination under `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`.
3. Pack-root `scripts/` executable sources inherited from `v1.6.13`.
4. Lower-capability dependencies already expressed as `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
5. Runtime receipt/report destinations under governed `runtime/` subtrees.

## 3) Four-track review checklist

### 3.1 T1 roundtable / internal topology

1. Reuse `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` for explicit identity binding and runtime-isolation baseline.
2. Reuse `identity/protocol/AGENT_HANDOFF_CONTRACT.md` for identity/skill/MCP-tool layer attribution and structured failure ownership.
3. Confirm that route-to-script governance does not create a hidden ambient arbitration layer.

### 3.2 T2 vendor / OpenAI Codex evidence

1. Confirm that Codex startup guidance and config surfaces remain startup-scoped rather than late-turn orchestration patches.
2. Confirm that `model_instructions_file`, `project_doc_fallback_filenames`, and `mcp_servers.<id>.command` are real Codex concepts.
3. Keep launcher/startup semantics (`v1.6.14`) separate from route/script orchestration semantics (`v1.6.15`).
4. Canonical vendor anchors:
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`

### 3.3 T3 Context7 / MCP / reference boundary

1. Confirm that MCP initialization negotiates readiness and capabilities before normal operations.
2. Confirm that MCP servers expose `tools`, `resources`, and `prompts` as lower capability primitives.
3. Keep route/script orchestration above MCP rather than collapsing the two layers.
4. Canonical reference family:
   - Context7 library id `/modelcontextprotocol/modelcontextprotocol`
   - MCP initialize lifecycle and capability declaration materials
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

### 3.4 T4 protocol / inherited-stream references

1. Reuse `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md` for pack-root `scripts/` ownership.
2. Reuse `docs/governance/identity-codex-launcher-governance-v1.6.14.md` for launcher/startup ownership.
3. Reuse `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md` for bootstrap tuple semantics.
4. Reuse `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md` as inherited review baselines.
5. Treat `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md` as pre-freeze design record only; this stream is the active owner.

## 4) Frozen implementation checklist

1. Canonical route fields are:
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
   - `script_receipt_pattern`
2. A single route may bind multiple role-distinct `script_id` values when execution legitimately separates probe/render/emit/recovery stages.
3. Canonical script catalog file is `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`.
4. Manifest entries resolve only to pack-local paths under `scripts/`.
5. Lower dependencies remain explicit through `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
6. `script_preconditions.required_contracts` and `script_preconditions.gate_policies` may reference inherited gateway/headstamp/host-visible/relay contracts, but that does not transfer ownership of those contracts into this stream.
7. Receipt families stay runtime-owned and classify at least:
   - route admission,
   - execution,
   - emit,
   - recovery.
8. Route/script join must never rely on operator memory, workspace-global shared helper directories, or filename guessing.
9. Route-scoped capability admission must be evaluable without blocking a route on lower dependencies that it does not itself declare unless a stronger activation policy explicitly says otherwise.
10. Receipt outputs must preserve machine-readable route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`.
11. Reviewers may accept layered receipt mapping where probe/helper scripts satisfy execution receipts first and emitter scripts later satisfy emit receipts plus delegated refs to inherited host-visible or relay receipts.
12. Any governed user-visible final output route must bind to a pack-local emitter script and declare an emit-family receipt before outer relay or visible-surface handling is considered valid evidence.

## 5) Audit verdict rules (frozen)

1. **Policy PASS** for this stream requires:
   - governance doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - review doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - scope-matrix row present in `identity/protocol/mappings/stream-scope-matrix.current.yaml`,
   - allowlist rows present in `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`,
   - audit index discoverability updated in `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
2. **Architecture PASS** for this stream requires:
   - route/script binding fields are frozen,
   - multi-role route-to-script binding semantics are frozen,
   - manifest path is frozen,
   - lower capability join is frozen,
   - inherited precondition reference semantics are frozen,
   - route-scoped capability-attribution rules are frozen,
   - receipt-family interpretation is frozen,
   - receipt-provenance projection expectations are frozen,
   - reviewer failure-attribution order is explicit.
3. **Implementation PASS** for this stream is not satisfied by documentation alone. The following implementation pieces are now landed:
   - protocol-owned manifest and route/script validators,
   - readiness wiring through `scripts/release_readiness_check.py`,
   - capability-activation awareness of instance scripts through `scripts/validate_identity_capability_activation.py`.
4. Full **Implementation PASS** still requires:
   - creator/backfill/update wiring on the same contract family,
   - a dedicated route/script receipt-join validator,
   - route-scoped activation behavior that does not union-block unrelated routes unless an explicit stronger policy is selected,
   - reusable positive and negative probes,
   - proof-pack adoption without topology drift,
   - receipt-provenance projection that keeps `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts` machine-visible.
5. Reviewers must not collapse `Architecture PASS` into `Implementation PASS`.
6. **Diagnostic Attribution PASS** requires reviewers to classify failures in this order:
   - `route_contract_missing`: one or more of `primary_instance_scripts`, `fallback_instance_scripts`, `script_preconditions`, or `script_receipt_pattern` is absent, contradictory, or unresolved in `CURRENT_TASK.json`.
   - `manifest_binding_missing`: route fields are present, but `scripts/INSTANCE_SCRIPT_MANIFEST.json` has no matching entry or resolves outside pack-root `scripts/`.
   - `script_precondition_blocked`: route and manifest are valid, but `script_preconditions` are unsatisfied before execution starts.
   - `mcp_capability_unavailable`: route/manifest/preconditions are valid, but a declared `required_mcp` server fails readiness for the required primitive.
   - `tool_pipeline_failure`: declared lower-capability surfaces are ready, but the governed tool pipeline fails during execution.
   - `script_receipt_mismatch`: execution returns, but runtime receipts do not satisfy `script_receipt_pattern`.
   - `outer_delivery_gap`: route/script/receipt checks pass, but governed host-visible delivery still fails later.

## 6) Accepted closure boundary

1. `v1.6.15` is closed at the contract-freeze level when the route/script/dependency/receipt model is frozen in protocol docs and mappings.
2. `v1.6.15` is not closed at the full implementation level until receipt-join/probe surfaces and the remaining shared consumers land in addition to the core validators/readiness wiring that already exist.
3. Instance packs may already be able to self-organize around pack-root `scripts/`, but chat evidence alone does not promote a private local pattern into protocol motherline.
4. This stream remains independent from provider runtime incidents, launcher install incidents, and host-visible final-surface auto-binding work.
5. A pack may be `topology-ready` and `exit-ready` yet still be pre-adoption for `v1.6.15` until manifest and additive route fields land; that migration state must not be misreported as a reopen of inherited streams.
6. Even before host auto-binding is solved, `v1.6.15` may require the governed producer for final user-visible text to be a route-bound emitter script instead of direct free-form assistant delivery.

## 7) Boundary lock for reviewers

1. Do not reinterpret this stream as permission to add new pack-root directories or revive `runtime/scripts/`.
2. Do not reinterpret this stream as permission to override launcher or bootstrap ownership already frozen by `v1.6.14` and `v1.6.12`.
3. Do not classify lower-capability outages as proof that route/script orchestration semantics are wrong.
4. Do not accept user-specific absolute paths, shared workspace helper dropzones, or per-pack hardcoded receipts as canonical answers.
5. Do not reopen `v1.6.13` or `v1.6.14` while reviewing this stream; `v1.6.15` exists specifically to keep those layers separate.
6. Do not classify route blocks caused only by undeclared lower dependencies as proof that the route/script contract failed; first verify whether the route actually declared those skills, MCP servers, or tool constraints.
7. Do not accept receipt families that drop `route_selected` / `skills_used` / `mcp_tools_used` provenance and then compensate with narrative-only explanation.
