# Identity Instance Pack Topology Governance (v1.6.13)

Status: Active (implementation closure stream, 2026-03-20)  
Layer: protocol  
Scope: identity-instance pack topology, root-level `scripts/` surface, and fail-close topology locking

Execution mode: topic-level canonical SSOT for v1.6.13 identity-instance pack topology governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_instance_pack_topology`.
2. `v1.6.10` remains the semantic owner for runtime dynamic file governance; `v1.6.13` specializes the instance-pack topology and the instance-owned executable source surface.
3. `v1.6.13` does not reopen native-chat bootstrap, relay final answer, or host-visible outer delivery semantics.
4. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
5. This stream freezes directory topology, not business/domain behavior.
6. Any instance-helper implementation that needs local automation must fit inside the canonical pack topology defined here; “temporary” path drift is non-compliant.

## 1) Why v1.6.13 is required

1. Identity protocol already froze runtime/autonomy boundaries, but instance-owned executable helpers still lacked a canonical pack-local home.
2. That gap encouraged topology drift such as `runtime/scripts/`, workspace-level shared helper dropzones, and ad hoc per-instance directory conventions.
3. Those drifts pollute runtime surfaces, blur ownership, and make validators/creator/backfill logic depend on historical accidents instead of a stable topology contract.
4. Skills already own pack-root `scripts/`; MCP defines transport primitives (`tools`, `resources`, `prompts`) rather than identity-instance ownership topology.
5. Codex config also exposes multiple instruction/config surfaces, so identity instances need their own frozen executable source surface instead of continuing to overload runtime state directories.
6. v1.6.13 closes this by freezing pack-root `scripts/` as the only canonical instance-owned script surface and by fail-closing any topology drift.

## 2) Frozen pack topology (no ambiguity)

### 2.1 Required pack-root layout

Every governed identity instance pack must expose exactly these canonical root directories:

- `agents/`
- `runtime/`
- `scripts/`

Required pack-root files remain:

- `CURRENT_TASK.json`
- `IDENTITY_PROMPT.md`
- `TASK_HISTORY.md`
- `META.yaml`
- `RULEBOOK.jsonl`
- `agents/identity.yaml`
- `scripts/README.md`

### 2.2 Root `scripts/` ownership freeze

1. Pack-root `scripts/` is the instance-owned executable source surface.
2. Scripts under this directory may consume shared protocol/workspace resolvers or renderers, but they must remain thin consumers rather than semantic forks.
3. Scripts here must stay identity-local, relative-path-friendly, and free of user-specific absolute path requirements.
4. Shared protocol semantics, validators, CI bundles, and creator/backfill logic remain protocol-owned surfaces under `identity-protocol-local/`.

### 2.3 Runtime boundary freeze

1. `runtime/` stays reserved for runtime/autonomy/state/report/downsink surfaces.
2. `runtime/scripts/` is forbidden.
3. Generated cache directories such as `__pycache__` and `.pytest_cache` are forbidden inside governed pack topology and must fail-close in strict validation.
4. Unknown directories under the pack root or runtime subtree are non-compliant until explicitly registered by contract.

### 2.4 No shared instance helper dropzone

1. Identity-instance helper scripts must not be parked in a workspace-global shared “instance patch” directory as their canonical home.
2. A workspace helper may orchestrate entry/bootstrap across instances, but instance-owned autonomous helpers still belong in that instance pack's root `scripts/`.
3. Protocol repository scripts may be reused as shared dependencies; they do not replace the instance-owned surface.

## 3) Machine contract frozen in this stream

### 3.1 Canonical contract + validator

1. Canonical kernel contract: `rq_043_identity_instance_pack_topology_contract_v1`
2. Canonical mapping row: `ASB16-RQ-043`
3. Canonical validator: `scripts/validate_identity_instance_pack_topology.py`
4. Canonical task contract key: `instance_pack_topology_contract_v1`

### 3.2 Validator obligations

The topology validator must fail-close when any of the following holds:

- required pack-root files are missing
- required root directories are missing
- runtime-only directories are misplaced or unknown
- `runtime/scripts/` exists
- generated cache directories exist inside the governed pack topology
- the contract id / validator id / fail mode drift away from the canonical tuple

### 3.3 Creator / bootstrap obligations

1. `scripts/create_identity_pack.py` must scaffold the canonical root `scripts/` directory and seed `scripts/README.md`.
2. Generated `CURRENT_TASK.json` must include `instance_pack_topology_contract_v1`.
3. Bootstrap validation must execute `scripts/validate_identity_instance_pack_topology.py` before claiming scaffold success.
4. Update/replay required checks must also include the topology validator so later topology drift cannot silently survive pack evolution.

## 4) Inherited-stream owner matrix

1. `v1.6.10` remains the owner for runtime-file governance classification, generated artifact family semantics, and mirror/wrapper/runtime boundary language.
2. `v1.6.11` remains the owner for outer relay exact-governed final answer semantics.
3. `v1.6.12` remains the owner for native-chat bootstrap entry semantics.
4. `v1.6.13` owns only:
   - identity-instance pack root topology
   - pack-root `scripts/` ownership semantics
   - `runtime/scripts/` prohibition
   - topology drift fail-close validation and creator wiring

## 5) Closure scope and explicit non-goals

1. This stream closes the topology contract for identity instances.
2. This stream does not define new Codex native features.
3. This stream does not convert instance-local scripts into protocol-owned business logic.
4. This stream does not reopen runtime path semantics already frozen in `v1.6.10`; it specializes the allowed instance-pack topology that sits on top of that boundary.
5. This stream does not authorize free-form new root directories. Any topology expansion requires a new governed contract revision first.

## 6) Frozen implementation guidance

1. Put instance-local execution helpers in pack-root `scripts/`.
2. Keep runtime outputs in `runtime/`.
3. When migrating a legacy pack from `runtime/scripts/`, move helpers to root `scripts/`, update contracts, then delete the forbidden path.
4. Keep the validator authoritative; do not hand-maintain side notes that disagree with the task contract.
5. Treat topology as infrastructure: creator, validator, mappings, and example packs must all agree.

## 7) Future extension rule

1. Additional pack-root directories are prohibited unless promoted by a later governed stream.
2. Additional runtime subtrees are prohibited unless registered in the topology contract.
3. New instance helper capabilities must reuse the canonical root `scripts/` surface instead of creating parallel executable roots.
