# Protocol Remediation Audit Ledger (v1.6.12 native-chat bootstrap entry stream)

Status: Active (doc-first stream opened + local replay verified, 2026-03-19; non-promotional)  
Scope: protocol review ledger for native-chat bootstrap entry governance and workspace bootstrap separation

## 0) Stream objective

1. Freeze wrapper-bound bootstrap as the standard native-chat entry model.
2. Keep identity authoritative truth on actor/session primary resolution rather than on active-pointer or projection fallback.
3. Separate protocol-side renderer semantics from workspace-side entry bootstrap so later follow-up can stay stream-isolated.

## 1) Problem statement frozen for audit

1. The remaining ambiguity is not the native-chat renderer contract itself; it is whether current-turn tuple injection happened before the process launched.
2. Host resume UUID and identity session tuple are different identifiers and must stay different.
3. Naked entry can still produce confusing operator observations, so v1.6.12 freezes it as unsupported or non-qualified evidence instead of treating it as protocol success.
4. Live host-runtime panics may still break smoke replay, but that does not reopen protocol renderer semantics by itself.
5. Stream opening in v1.6.12 does not by itself prove that the outer native-chat final visible surface is already hard-bound to the controlled visible emitter.
6. Implementation closure may still wire the host-visible `final` channel to the frozen `v1.6.11` exact relay receipt so sender-side proof is explicit without reopening bootstrap semantics.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces

1. `scripts/native_chat_headstamp_common.py`
2. `scripts/render_identity_response_stamp.py`
3. `scripts/run_native_chat_headstamp_smoke.sh`
4. `scripts/validate_native_chat_bootstrap_entry_stream.py`
5. `scripts/ci/run_native_chat_bootstrap_entry_probes_ci.sh`
6. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
7. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`

### 2.2 Workspace / instance-owned surfaces consumed by this stream

1. Native-chat bootstrap bridge and bootstrap-audit helper under the workspace scripts/identity tree.
2. Workspace shell entry wrappers that inject tuple truth before launching `codex`, `codex resume`, or `codex exec`.
3. Workspace wrappers may pair the bootstrap instructions file with a process-local project-doc fallback file so later turns can reread the same two governed native-chat lines without relying on a shared workspace-global projection file.
4. These helpers are evidence sources for v1.6.12, not protocol motherline promotion by themselves.
5. The process-local project-doc fallback remains a reread aid only; it is not a send-time egress binding and cannot be used as proof that the final host-visible answer was emitted through the controlled visible surface.

## 3) Four-track review checklist

### 3.1 T1 roundtable / topology

1. Reuse `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` as the topology baseline.
2. Require isolated runtime contexts or governed shared-session handshake for parallel multi-identity operation.

### 3.2 T2 execution/runtime semantics

1. Reuse `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` for execution-target tuple isolation and hard no-switch-in-execution semantics.
2. Freeze the interpretation that resume UUID is host-thread state and not an identity tuple.

### 3.3 T3 protocol/kernel semantics

1. Reuse `identity/protocol/IDENTITY_PROTOCOL.md` and `identity/protocol/IDENTITY_RUNTIME.md` as kernel baselines.
2. Keep `scripts/response_stamp_common.py` and `scripts/sync_session_identity.py` aligned with session-primary truth plus compatibility-mirror diagnostics only.

### 3.4 T4 replay bundle

1. Accept the v1.6.12 replay bundle indexed by:
   - `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`
   - `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json`
2. Treat the fast audit, wrapper dry-run, and protocol authoritative resolve as opening evidence.
3. Treat current live smoke as inconclusive host-runtime evidence, not as stream-promotion proof.

## 4) Files landed in this stream

1. `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
5. `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
6. `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`
7. `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json`

### 4.1) Implementation closure progress snapshot (2026-03-19)

1. Sender-side implementation closure in this stream now consumes the frozen `v1.6.11` exact relay receipt at the host-visible `final` channel instead of inventing a new relay semantics layer.
2. The protocol-owned implementation surfaces landed for that closure are:
   - `scripts/host_visible_final_channel_relay_common.py`
   - `scripts/create_identity_pack.py`
   - `scripts/validate_send_time_reply_gate.py`
   - `scripts/validate_host_transport_wiring_attestation.py`
   - `scripts/validate_protocol_unique_entry_gate.py`
   - `scripts/repair_contract_backfill.py`
   - `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
3. Local replay on 2026-03-19 confirms that the producer, send-time gate, and host-visible attestation layers now agree on the final-channel relay proof path:
   - `python3 scripts/validate_native_chat_bootstrap_entry_stream.py --json-only` returns `stream_opening_status=PASS_REQUIRED`, `promotion_status=NON_PROMOTIONAL_LOCK`, and `live_smoke_status=INCONCLUSIVE_HOST_RUNTIME_PANIC`
   - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh` returns passing positive/negative probes including `host_visible_live_receipts_pass`, `host_visible_final_channel_relay_missing_blocked`, and `send_time_governed_pass_headstamp_required`
4. This progress raises confidence that sender-side controlled visible projection is no longer relying on a naked outer delivery assumption.
5. Closure blockers identified during review on 2026-03-19 are now reduced on the protocol side:
   - the previously untracked v1.6.12/final-relay protocol files are landed in commit `3e6ca34`
   - `scripts/ci/run_host_visible_surface_live_probes_ci.sh` now resolves repo-root-owned script paths explicitly, so prefixed invocation from the workspace root no longer depends on `cwd`
6. This progress note does not upgrade the stream to promotion-grade closure: the outer native-chat final visible surface still needs stable host-runtime proof before reviewers may claim that the final visible reply is always hard-bound to the controlled visible emitter.

## 5) Audit verdict rules (frozen)

1. **Policy PASS** requires:
   - governance doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - review doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - allowlist rows present in `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - index discoverability updated in `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
2. **Evidence PASS for stream opening** requires:
   - fast bootstrap audit remains `PASS_REQUIRED`
   - wrapper dry-run resume proves host UUID and identity tuple stay separated
   - wrapper dry-run exec proves explicit tuple injection on a fresh closure launch
   - wrapper-owned project-doc fallback remains process-local and session-bound rather than workspace-global
   - protocol authoritative resolve remains `actor_binding_session_scoped`
3. **Non-promotion lock** remains mandatory while live smoke is still host-runtime-dependent or inconclusive.
4. `scripts/validate_native_chat_bootstrap_entry_stream.py` is the protocol-owned stream-opening consumer: it may pass stream opening while still returning `promotion_status=NON_PROMOTIONAL_LOCK`.
5. Any proposal that reintroduces active-pointer or projection guessing for bootstrap truth remains `FAIL_REQUIRED` for this stream.
6. Future promotion or stronger closure claims must additionally prove:
   - `tuple_present + authoritative_resolve_pass + no_silent_headerless_turn`
   - outer final native-chat visible surface is bound to the controlled visible emitter path rather than to a free-form outer reply path
7. A repeated silent headerless turn with tuple truth already present must be logged as an outer final visible surface residual; it does not invalidate v1.6.12 stream opening by itself, but it does block stronger promotion claims.
8. Sender-side implementation closure is acceptable only when the host-visible `final` channel records a passing exact relay receipt instead of treating naked outer delivery as equivalent proof.

## 6) Local verification accepted for this opening

1. See `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json`.
2. See `activity/evidence/v1612-native-chat-bootstrap-entry/2026-03-19/bootstrap_entry_summary.v1.6.12.json`.
3. The current summary freezes one accurate conclusion: fast audit + wrapper dry-run + authority resolve are green enough to open v1.6.12, while live smoke remains host-runtime-dependent and therefore non-promotional.

## 7) Boundary lock for reviewers

1. Do not rewrite this stream into a generic headstamp or prompt stream.
2. Do not use v1.6.12 evidence to claim naked entry is already a protocol blocker.
3. Do not claim protocol motherline uplift is complete from this landing alone.
4. Do not let workspace helper debt reopen v1.6.1, v1.6.10, or v1.6.11 semantics.
5. Do not reintroduce a shared workspace-global fallback doc for native-chat headstamp carry-forward.
6. Do not mislabel outer final visible surface instability as a bootstrap-entry semantic contradiction unless tuple injection or session-primary resolve is the failing layer.
