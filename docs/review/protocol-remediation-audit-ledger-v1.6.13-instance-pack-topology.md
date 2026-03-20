# Protocol Remediation Audit Ledger (v1.6.13 identity-instance pack topology stream)

Status: Active (implementation closure stream, 2026-03-20)  
Scope: protocol review ledger for identity-instance pack topology and root `scripts/` surface locking

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
