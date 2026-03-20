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

### 2.1.1 Identity pack three-layer interpretation

1. A governed identity instance pack must be read as a three-layer structure:
   - `IDENTITY_PROMPT.md`: prompt kernel / role-guidance layer
   - `CURRENT_TASK.json`: runtime SSOT / machine-contract layer
   - pack-root `scripts/`: canonical instance-owned executable surface
2. `v1.6.13` specializes only the third layer plus the pack topology needed to hold it stable; it does not redefine the semantic owner of the prompt kernel or the runtime contract.
3. The existence of `IDENTITY_PROMPT.md` means identity instances already have a pack-level guidance artifact; reviewers must not misdiagnose later route or execution gaps as “missing prompt kernel”.
4. Comparisons with skill bundles are allowed only at the guidance/resource-shape level:
   - `IDENTITY_PROMPT.md` is analogous to the guidance body of `SKILL.md`
   - pack-root `scripts/` is analogous to bundled executable resources
5. `v1.6.13` does not freeze a skill-style trigger/discovery contract for identity packs, and it does not imply that `IDENTITY_PROMPT.md` alone is equivalent to a whole skill bundle.
6. `agents/identity.yaml` remains a valid sidecar metadata artifact for activation/display/dependency hints, analogous in role to skill-side agent metadata, but it is not promoted by this stream into a fourth execution/governance layer beyond the three-layer interpretation above.

### 2.1.2 Canonical topology example

The frozen pack shape for a governed identity instance is:

```text
<pack_root>/
├── IDENTITY_PROMPT.md
├── CURRENT_TASK.json
├── TASK_HISTORY.md
├── META.yaml
├── RULEBOOK.jsonl
├── agents/
│   └── identity.yaml
├── runtime/
│   ├── state/
│   ├── reports/
│   └── autonomy/
└── scripts/
    ├── README.md
    └── <instance_owned_helpers>.py|.sh
```

Frozen interpretation:

1. `scripts/` is the only canonical home for instance-owned executable sources.
2. `runtime/` may contain runtime state, receipts, reports, autonomy outputs, and other generated artifacts, but it is not an executable source root.
3. `agents/identity.yaml` remains descriptive sidecar metadata and must not be used to justify extra executable roots.
4. If a helper must be invoked by the instance and is owned by the instance, its source belongs under pack-root `scripts/` even if the helper later writes reports into `runtime/`.

### 2.2 Root `scripts/` ownership freeze

1. Pack-root `scripts/` is the instance-owned executable source surface.
2. Scripts under this directory may consume shared protocol/workspace resolvers or renderers, but they must remain thin consumers rather than semantic forks.
3. Scripts here must stay identity-local, relative-path-friendly, and free of user-specific absolute path requirements.
4. Shared protocol semantics, validators, CI bundles, and creator/backfill logic remain protocol-owned surfaces under `identity-protocol-local/`.

### 2.2.1 Path responsibility matrix

Use the following matrix when implementing or reviewing code:

| Path | Owner | Allowed content | Forbidden content |
| --- | --- | --- | --- |
| pack-root `scripts/` | instance | thin instance-owned helpers, renderers, emitters, launcher consumers that reuse governed semantics | protocol semantic forks, user-specific absolute-path hacks, generated cache/state |
| pack-root `runtime/` | runtime | state, reports, receipts, autonomy outputs, other generated artifacts | executable source trees, hand-maintained helper libraries |
| pack-root `agents/` | metadata | identity display/activation/dependency sidecar metadata | executable source trees, runtime receipts |
| `identity-protocol-local/scripts/` | protocol | shared validators, creator/backfill logic, canonical builders/renderers/installers | instance-owned business/helper code parked as canonical home |

This matrix is frozen for `v1.6.13` and is intentionally narrow: if a future capability needs a new canonical path family, that requires a later governed stream instead of local expansion.

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
5. Runtime receipt/report families already frozen by earlier streams remain valid only when their runtime subtrees are explicitly registered in the topology contract; for the current baseline this includes `runtime/reports/agent-relay-final-answer`.

### 3.4 Standard capability profile (fused, not parallel)

1. `v1.6.13` does not create a second execution-gate system; it composes with the already-governed gateway four-piece:
   - `entry_receipt_policy`
   - `ingress_proof_policy`
   - `egress_grant_policy`
   - `headstamp_policy`
2. The frozen readiness model for an instance that claims the standard native-chat scheme is:
   - `topology-ready`: `scripts/validate_identity_instance_pack_topology.py` returns `PASS_REQUIRED`.
   - `gate-ready`: the instance task/runtime contract already carries the required gateway four-piece.
   - `entry-ready`: the process enters through the governed bootstrap wrapper so current-turn tuple truth is injected before `codex`, `codex resume`, or `codex exec`.
   - `exit-ready`: the instance pack exposes root-level scripts that render the current-thread headstamp and emit the final governed reply without forking protocol semantics.
3. Standard scheme means `topology-ready + gate-ready + entry-ready + exit-ready`; creating directories alone is scaffold success, not full standard-capability readiness.
4. Fallback behavior remains fail-close only: when standard readiness is missing, the instance may emit a withheld/conflict envelope, but it must not emit an ungoverned success headstamp.
5. Enhanced host-auto-binding remains a later host/runtime concern; `v1.6.13` freezes the instance-owned topology and standard-capability composition, not outer-surface promotion claims.
6. `exit-ready` proves the instance-owned executable surface is present and can consume governed protocol truth; it does not by itself prove that task-type routing already declaratively targets those scripts.

### 3.5 Diagnostic interpretation ladder (frozen)

1. `contract_not_required` / `SKIPPED_NOT_REQUIRED` means the instance has not yet absorbed the topology contract; it is not evidence that the protocol stream is incomplete.
2. `topology-ready` means the canonical pack structure is in place; it does not by itself prove that current-turn runtime state or historical actor-session bindings are already clean.
3. When `topology-ready` is green but live entry or exit still fail-closes, diagnosis must proceed in this order:
   - current-turn tuple validity,
   - actor-session binding hygiene,
   - exit-side receipt generation,
   - then outer host/runtime residuals.
4. A stale or non-`run:<...>` identity session binding is instance-owned runtime debt and must be repaired instance-side; it must not be relabeled as a `v1.6.13` protocol semantic gap.
5. Informative fail-close after migration is a positive signal in this stream: it proves the instance is now executing governed checks instead of silently guessing through dirty runtime state.
6. The intended self-heal order for this stream is:
   - topology contract absorption,
   - canonical root `scripts/` surface present,
   - governed entry truth clean,
   - exit-ready scripts pass under current-turn tuple,
   - live receipts / relay receipts land,
   - then the instance may claim standard-capability readiness.
7. If an instance is topology-ready but its `CURRENT_TASK` routes still do not explicitly bind to pack-root scripts, that is an orchestration/join gap outside this stream unless some separate validator proves a topology violation.

## 4) Inherited-stream owner matrix

1. `v1.6.10` remains the owner for runtime-file governance classification, generated artifact family semantics, and mirror/wrapper/runtime boundary language.
2. `v1.6.11` remains the owner for outer relay exact-governed final answer semantics.
3. `v1.6.12` remains the owner for native-chat bootstrap entry semantics.
4. `v1.6.13` owns only:
   - identity-instance pack root topology
   - pack-root `scripts/` ownership semantics
   - `runtime/scripts/` prohibition
   - topology drift fail-close validation and creator wiring
5. `v1.6.13` does not own route-to-script declarative binding, instance-script manifest semantics, or a generic instance-script execution receipt family.
6. `v1.6.13` also does not promote `agents/identity.yaml` sidecar metadata into an independent execution layer; that artifact may describe the pack, but it does not replace prompt-kernel, machine-contract, or canonical script-surface responsibilities.

## 5) Closure scope and explicit non-goals

1. This stream closes the topology contract for identity instances.
2. This stream does not define new Codex native features.
3. This stream does not convert instance-local scripts into protocol-owned business logic.
4. This stream does not reopen runtime path semantics already frozen in `v1.6.10`; it specializes the allowed instance-pack topology that sits on top of that boundary.
5. This stream does not authorize free-form new root directories. Any topology expansion requires a new governed contract revision first.
6. This stream does not define `CURRENT_TASK` route fields such as `primary_instance_scripts`, `fallback_instance_scripts`, or script-level precondition/receipt schemas.
7. This stream does not define a generic instance-script manifest contract; any promotion of pack-local script manifests into protocol motherline must happen in a later governed stream.

## 6) Frozen implementation guidance

1. Put instance-local execution helpers in pack-root `scripts/`.
2. Keep runtime outputs in `runtime/`.
3. When migrating a legacy pack from `runtime/scripts/`, move helpers to root `scripts/`, update contracts, then delete the forbidden path.
4. Keep runtime-binding repair separate from topology judgment: once the pack is topology-ready, stale actor-session state should be repaired as instance runtime debt rather than folded back into protocol topology semantics.
5. Keep the validator authoritative; do not hand-maintain side notes that disagree with the task contract.
6. Treat topology as infrastructure: creator, validator, mappings, and example packs must all agree.

### 6.1 Developer-ready coding checklist

Any implementation that claims to follow `v1.6.13` should satisfy this checklist before code review:

1. New instance-owned helper source files are added only under pack-root `scripts/`.
2. Any new generated output path lands under `runtime/` and is either already registered by contract or introduced by a later governed stream.
3. Shared semantic logic stays protocol-owned; instance scripts consume it rather than copy/fork it.
4. `scripts/README.md` is updated so pack-local helper intent stays auditable.
5. `CURRENT_TASK.json` continues to reference the canonical topology contract instead of introducing ad hoc topology keys.
6. Legacy `runtime/scripts/` residue and cache directories are removed rather than tolerated as compatibility leftovers.

## 7) Future extension rule

1. Additional pack-root directories are prohibited unless promoted by a later governed stream.
2. Additional runtime subtrees are prohibited unless registered in the topology contract.
3. New instance helper capabilities must reuse the canonical root `scripts/` surface instead of creating parallel executable roots.
4. If a later stream promotes route-to-script declarative join, it must build on the three-layer pack model above rather than reopening the topology freeze.
5. If a later stream promotes an instance-script manifest or execution receipt family, it must treat `v1.6.13` as the topology prerequisite rather than as the owner of that orchestration contract.
