# Identity Native-Chat Bootstrap Entry Governance (v1.6.12)

Status: Active (doc-first stream opened + local replay verified, 2026-03-19; motherline promotion pending)  
Layer: protocol  
Scope: native-chat bootstrap entry governance across protocol renderer boundary and workspace bootstrap entry boundary

Execution mode: topic-level canonical SSOT for v1.6.12 native-chat bootstrap entry governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `native_chat_bootstrap_entry`.
2. v1.6.1, v1.6.10, and v1.6.11 remain inherited unless explicitly superseded here.
3. This stream does not reopen native-chat visible order, failure-envelope semantics, compatibility-mirror semantics, or outer relay semantics.
4. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json`
5. Protocol-side authoritative identity resolution remains session-primary and fail-close.
6. Compatibility projection / active pointer remain diagnostic mirrors only and must not be reused as bootstrap tuple truth.
7. `stream_opening_status=PASS_REQUIRED` in this stream certifies only that the bootstrap-entry governance lane is opened with accepted evidence; it does not certify motherline promotion, required-gate uplift, or stable outer native-chat final visible surface binding.
8. If a host-native panel still emits a silent headerless turn after tuple injection and authoritative resolve both passed, that incident must be classified as an outer final visible surface binding residual, not as automatic evidence that v1.6.12 bootstrap semantics regressed.

## 1) Why v1.6.12 is required

1. Protocol renderer and pointer semantics were already separated, but native-chat entry bootstrap was still easy to interpret loosely.
2. Naked `codex`, `codex resume`, and `codex exec` can launch a process without proving that the current-turn tuple came from actor-session truth.
3. A resume thread UUID is host-chat state, not the identity authoritative session tuple.
4. Without a dedicated bootstrap contract, tuple-missing fail-close, host-runtime panics, and true identity drift can be misread as the same incident class.
5. v1.6.12 closes this interpretation gap by freezing wrapper-bound bootstrap as the standard entry model and by isolating host thread identifiers from identity tuple truth.

## 2) Frozen bootstrap model (no ambiguity)

### 2.1 Standard entry model

1. Wrapper-bound bootstrap is the standard native-chat entry model.
2. The bootstrap wrapper must resolve actor-session primary truth before launching native chat and must inject the current-turn tuple explicitly.
3. Workspace helpers may implement the wrapper, but protocol semantics stay source-first and tuple-first.
4. When a workspace helper needs a later-turn reread surface, it must inject a process-local project-doc fallback file bound to the resolved identity session rather than rely on a shared workspace-global identity projection file.
5. That process-local project-doc fallback is a reread aid only; it is not a send-time egress binding, not a governed receipt, and not proof by itself that the final host-visible reply was emitted through the controlled visible surface.
6. Native-chat renderer stays a thin consumer of injected truth and must not reconstruct identity from ambient host-only state.

### 2.2 Non-negotiable tuple rules

1. `resume UUID != identity session tuple`.
2. Current-turn tuple must use the governed `run:<...>` identity session token sourced from actor/session binding truth.
3. Bootstrap tuple resolution must reject compatibility-mirror, active-pointer, and ambient latest-mutation fallback.
4. Manual `model_instructions_file` or `project_doc_fallback_filenames` override that bypasses wrapper bootstrap is non-qualified and must fail-close.
5. Shared workspace-global fallback docs remain forbidden for this stream because they recreate cross-process projection drift.
6. Success headstamp remains governed by v1.6.1; missing tuple remains fail-close rather than silent no-headstamp.

### 2.3 Runtime switching boundary

1. Live Codex runtime defaults to no in-place identity switch.
2. Multi-identity collaboration is achieved by distinct wrapped processes or other governed execution targets, not by mutable shared active-pointer guesses.
3. Naked entry is currently `unsupported / non-qualified` evidence, not yet a protocol blocker.
4. This stream does not reopen whether naked entry should later become a required-gate blocker.

## 3) Four-track cross-verification boundary

### 3.1 T1 roundtable / topology

1. `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` already freezes allowed topology: shared runtime means one governed active identity, while parallel multi-identity work requires isolated runtime contexts or a governed shared-session handshake.
2. v1.6.12 reuses that topology and narrows it specifically to native-chat entry bootstrap.

### 3.2 T2 execution/runtime semantics

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` already freezes execution-target tuple isolation and prohibits execution-state hard identity switch.
2. Supported execution-target kinds remain `tmux_session | codex_home | process_call | worker_queue`.
3. Bootstrap wrapper is the native-chat specialization of that execution-target contract; it does not invent a separate identity arbitration model.

### 3.3 T3 protocol/kernel semantics

1. `identity/protocol/IDENTITY_PROTOCOL.md` keeps `session_primary_binding` mandatory in strict lanes.
2. `scripts/response_stamp_common.py` resolves reply truth from `actor_session_primary` rather than from compatibility mirrors.
3. `scripts/sync_session_identity.py` labels the compatibility pointer as `authority_role=compatibility_mirror` with `authoritative_decision_allowed=false`.
4. Therefore v1.6.12 must not reintroduce active-pointer guessing on native-chat entry.

### 3.4 T4 local replay / evidence

1. The fast bootstrap audit already passes for `base-repo-closure-orchestrator` and `base-repo-architect`.
2. Wrapper dry-run proves that `resume` keeps the host UUID while the injected tuple stays on the governed `run:<...>` identity session.
3. Protocol authoritative resolve passes for the architect replay and remains `actor_binding_session_scoped`.
4. Live smoke remains host-runtime-dependent and is currently inconclusive because OTEL / system-configuration panics fire before a reusable protocol verdict can be claimed.

### 3.5 Inherited-stream owner matrix

1. `v1.6.12` owns native-chat bootstrap entry semantics:
   - wrapper-bound bootstrap as the standard entry model
   - current-turn tuple injection requirements
   - `resume UUID != identity session tuple`
   - unsupported/non-qualified interpretation for naked entry
2. `v1.6.1` remains the semantic owner for:
   - native-chat visible line order
   - success/failure envelope semantics
   - `mini/standard/audit` machine-verification profile meaning
3. `v1.6.6` remains the execution-channel owner for:
   - wrapper-only ingress/egress routing
   - unique canonical egress path expectations
   - project-side user-visible outbound wrapper contract
4. `v1.6.11` remains the owner for outer relay exact-governed-delivery semantics and must not be silently collapsed into bootstrap-entry claims.
5. Therefore an outer final visible surface residual must not be misreported as a `v1.6.12` semantic reopen unless bootstrap tuple truth itself is what failed.

## 4) Closure scope and explicit non-goals

1. This stream opens the governance lane and evidence contract for native-chat bootstrap entry.
2. This stream does not claim contract-binding or required-gate promotion is complete.
3. This stream does not claim validator maturity is promotion-grade.
4. This stream does not claim naked entry is already blocked by protocol required gates.
5. This stream does not reopen v1.6.1 renderer semantics, v1.6.10 compatibility-mirror semantics, or v1.6.11 outer relay semantics.
6. This stream does not authorize active pointer or compatibility projection to speak for current-turn identity.
7. This stream does not certify that the current outer native-chat final visible surface is already hard-bound to the controlled visible emitter.
8. Implementation closure in this stream may consume the existing `v1.6.11` exact relay receipt at the host-visible `final` channel so the sender side proves controlled visible projection without reopening relay semantics.

## 4.1) Standard implementation freeze vs enhancement boundary

1. The standard native-chat implementation for this stream is frozen as:
   - machine verification first,
   - assistant-visible `Identity-Context` + `Machine-Verification` injection second,
   - next-turn re-verification on later turns.
2. The assistant-visible injected lines must come from the governed native-chat renderer output and must remain bound to current-turn tuple truth; they are not free-form commentary and they are not manual identity guessing.
3. Current speaking identity MUST be sourced from current-turn authoritative render only; the pack under repair, audit target, work subject, or any other foreign identity is never an authority source for the injected lines.
4. The canonical runtime helper for this source boundary is `python3 scripts/codex_native_chat/native_chat_bootstrap_bridge.py render-current --catalog .identity/catalog.local.yaml`; it intentionally has no `--identity-id` input because subject-of-work override is forbidden.
5. Any explicit `requested_identity_id` path remains selector-only and must fail-close unless it exactly matches the current-turn authoritative identity.
6. This standard implementation is sufficient for stream-level closure and for downstream feature work; it does not require the host final surface to be automatically hard-controlled before the stream may be considered closed at the standard level.
7. Host final surface controlled display remains a stronger sender-side proof enhancement:
   - controlled visible emitter on the final host-visible surface,
   - exact relay receipt at the `final` channel,
   - post-check recovery that can reseed the exact relay metadata from the actual reply transport ref,
   - `no_silent_headerless_turn` proof, satisfied either by a stable live smoke pass or by the governed host-visible continuity bundle when host runtime smoke is inconclusive but the controlled path is fully machine-attested.
8. That stronger sender-side proof stays in the same `v1.6.12` stream as a promotion-grade enhancement and must not be used to reopen or invalidate the standard implementation once the standard boundary above is satisfied.

## 5) Evidence contract for this stream

1. Strict governance/review docs may cite only these persistent evidence anchors directly:
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/<YYYY-MM-DD>/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/<YYYY-MM-DD>/bootstrap_entry_summary.v1.6.12.json`
2. Local runtime mirrors may still be generated under `activity/evidence/v1612-native-chat-bootstrap-entry/<YYYY-MM-DD>/...`, but strict docs and protocol validators must not depend on ignored runtime-only paths for reproducible stream judgment.
3. Deeper replay artifacts stay indexed from the manifest and should not be copied into new strict docs unless the allowlist is expanded first.
4. The current accepted replay bundle for stream opening is:
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`
   - `identity/protocol/fixtures/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json`

## 6) Frozen implementation guidance

1. Keep protocol truth on actor/session primary resolution and current-turn tuple consumption.
2. Keep workspace bootstrap responsibility out of protocol motherline until promotion evidence is sufficient.
3. Keep multi-agent or multi-identity scaling on isolated wrapped processes, tmux lanes, process-call lanes, or governed sub-agent handoff; do not route through shared mutable pointer guesses.
4. Keep host-runtime panic evidence classified as host-runtime instability, not as proof that protocol renderer semantics regressed.
5. Machine-consumable stream opening checks should use `scripts/validate_native_chat_bootstrap_entry_stream.py`; host-runtime inconclusive live smoke must never be interpreted as a stream-opening semantic regression, and it remains non-promotional unless the governed continuity bundle separately proves the same current-turn no-headerless-turn boundary.
6. `scripts/validate_native_chat_bootstrap_entry_stream.py` must prefer the tracked canonical fixture bundle under `identity/protocol/fixtures/...` and use `activity/evidence/...` only as a local fallback when the tracked fixture is unavailable.
7. Keep this stream infrastructure-first: no ad hoc prompt patches, no identity guessing from projection files, and no hidden in-place switching path.

## 7) Future promotion exit criteria (frozen for clarity)

1. Promotion from stream opening to stronger closure claims requires more than tuple bootstrap evidence.
2. At minimum, future promotion evidence must prove all of the following together:
   - current-turn tuple is present,
   - authoritative resolve passes on session-primary truth,
   - final channel relay receipt remains `PASS_REQUIRED`,
   - sender-side controlled emitter path remains `PASS_REQUIRED`,
   - the outer native-chat final visible surface does not emit a silent headerless turn, proven either by stable live smoke or by a governed host-visible continuity bundle that already binds the admitted reply to the controlled emitter path,
   - the final host-visible answer is bound to the controlled visible emitter path rather than to a free-form outer reply path.
3. Until those conditions are proven, the correct status is:
   - bootstrap-entry stream opening may still be `PASS_REQUIRED`,
   - promotion remains locked,
   - outer visible surface instability remains a residual implementation-side closure item rather than a semantic contradiction inside v1.6.12.
4. `scripts/validate_native_chat_bootstrap_entry_stream.py` is the machine gate for this bundle and must report the promotion-side evidence fields explicitly:
   - `tuple_present_status`
   - `authoritative_resolve_status`
   - `post_check_recovery_status`
   - `final_channel_relay_receipt_status`
   - `controlled_emitter_path_status`
   - `governed_headstamp_continuity_status`
   - `no_silent_headerless_turn_status`
5. The same machine gate must also report the closure boundary explicitly so later work cannot reinterpret the stream by chat text alone:
   - `standard_implementation_mode=assistant_visible_inject`
   - `standard_closure_status=CLOSED`
   - `promotion_enhancement_mode=host_final_surface_controlled_display`
   - `promotion_enhancement_status=OPEN` while `promotion_status=NON_PROMOTIONAL_LOCK`
   - `promotion_enhancement_status=READY` when the governed continuity bundle closes promotion even if host-runtime smoke remains diagnostically inconclusive
