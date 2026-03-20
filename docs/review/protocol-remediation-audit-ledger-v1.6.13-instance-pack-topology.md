# Protocol Remediation Audit Ledger (v1.6.13 identity-instance pack topology stream)

Status: Active (implementation closure stream, 2026-03-20)  
Scope: protocol review ledger for identity-instance pack topology and root `scripts/` surface locking

## 0.1) State interpretation guard (mandatory)

1. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
2. This review ledger evaluates topology closure through the active current-pointer mappings; replay snapshots and historical packs remain audit evidence only.

## 0) Stream objective

1. Freeze pack-root `scripts/` as the canonical identity-instance executable source surface.
2. Forbid `runtime/scripts/` and other topology drift.
3. Wire creator + validator + mappings so topology is enforced as infrastructure instead of tribal knowledge.

## 1) Problem statement frozen for audit

1. Identity instances needed a canonical place for autonomous helper scripts, but protocol only had runtime boundary language and ad hoc local practice.
2. That gap produced drift such as `runtime/scripts/` and cache pollution under governed runtime paths.
3. Without a dedicated topology validator, creator and local examples could keep generating technically-usable but semantically-wrong layouts.
4. This stream closes that ambiguity by turning topology into a machine contract.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces

1. `scripts/create_identity_pack.py`
2. `scripts/validate_identity_instance_pack_topology.py`
3. `identity/protocol/IDENTITY_PROTOCOL.md`
4. `identity/protocol/IDENTITY_RUNTIME.md`
5. `identity/protocol/mappings/contract-binding.v1.6.yaml`
6. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
7. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
8. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`

### 2.2 Instance-owned surfaces consumed by this stream

1. Pack-root `scripts/` content itself stays instance-owned.
2. Current example migration uses `base-repo-closure-orchestrator` as a proof pack.
3. Instance-owned scripts may call shared protocol/workspace helpers, but the ownership home remains the instance pack.

## 3) Frozen implementation checklist

1. Creator scaffolds `scripts/README.md` at the pack root.
2. Generated `CURRENT_TASK.json` carries `instance_pack_topology_contract_v1`.
3. Bootstrap validation runs `scripts/validate_identity_instance_pack_topology.py`.
4. Update/replay required checks include the same topology validator.
5. Example pack `base-repo-closure-orchestrator` is migrated off `runtime/scripts/`.
6. Forbidden topology residue (`runtime/scripts/`, `__pycache__`) is removed from the governed example pack.

## 3.1) Proof-pack worked example frozen in this stream

The current proof pack for `v1.6.13` is `base-repo-closure-orchestrator`. The worked example is intentionally split into entry proof and exit proof so topology does not get confused with outer-host delivery claims.

Entry-side proof:

1. Workspace bootstrap helper:
   - `scripts/codex_native_chat/codex_with_native_chat_entry.sh`
2. Entry validator:
   - `scripts/codex_native_chat/validate_native_chat_entry_bootstrap.py`
3. Verified outcome:
   - explicit bootstrap passes
   - missing identity fails close
   - resume UUID cannot impersonate `run:<...>` identity session tuple

Exit-side proof:

1. Instance-owned canonical helpers:
   - `.identity/base-repo-closure-orchestrator/scripts/render_current_thread_headstamp.py`
   - `.identity/base-repo-closure-orchestrator/scripts/emit_current_thread_final_reply.py`
2. Verified outcome:
   - current-thread headstamp render returns `PASS_REQUIRED`
   - final emitter refreshes host-visible receipts and exact relay receipt before writing the visible reply
3. Evidence family:
   - `.identity/base-repo-closure-orchestrator/runtime/reports/host-visible-surface/host-visible-surface-*.json`
   - `.identity/base-repo-closure-orchestrator/runtime/reports/agent-relay-final-answer/agent-relay-final-answer-*.json`

This worked example proves the standard instance-owned path:

- process entry is workspace-owned
- final visible reply emission is instance-owned
- protocol semantics stay shared and authoritative

## 3.2) Gate fusion verdict

1. `v1.6.13` has no semantic conflict with the gateway four-piece already present in governed instance tasks.
2. The fusion model is frozen as:
   - `topology-ready`
   - `gate-ready`
   - `entry-ready`
   - `exit-ready`
3. `pack-root scripts/` answers where instance-owned helper execution lives.
4. `entry_receipt_policy + ingress_proof_policy` answer how governed entry is proven.
5. `egress_grant_policy + headstamp_policy` answer how governed visible output is proven.
6. Reviewers must not force a false choice between `v1.6.13` topology governance and the gateway four-piece; they are complementary layers of one infrastructure model.

## 4) Audit verdict rules (frozen)

1. **Policy PASS** requires:
   - governance/review docs registered in the stream registry
   - scope matrix row present
   - doc evidence allowlist rows present
   - audit index updated
2. **Implementation PASS** requires:
   - creator writes root `scripts/README.md`
   - creator injects `instance_pack_topology_contract_v1`
   - topology validator is callable in bootstrap mode and pack mode
   - required checks include the topology validator
   - registered runtime receipt/report directories cover the active governed families, including `runtime/reports/agent-relay-final-answer`
3. **Topology PASS** requires:
   - required root dirs/files present
   - `runtime/scripts/` absent
   - no cache-dir residue
   - no unknown topology drift rows

## 5) Accepted closure boundary

1. This stream is closed when topology is machine-enforced across creator, mappings, and the migrated example pack.
2. This stream is not waiting on host-runtime live smoke or outer visible surface behavior.
3. This stream is independent from Codex native feature evolution; it governs only the identity-instance pack surface that the protocol owns.

## 6) Boundary lock for reviewers

1. Do not reinterpret this stream as permission to add arbitrary new pack-root directories.
2. Do not treat `runtime/scripts/` as an acceptable compatibility path.
3. Do not push instance-owned helper code back into protocol/shared paths just because multiple instances may reuse similar logic.
4. Do not reopen `v1.6.10`, `v1.6.11`, or `v1.6.12` semantics while reviewing this stream.
5. Do not fold unrelated host/provider/runtime failures into this stream; `v1.6.13` governs pack topology and the standard capability composition only.
