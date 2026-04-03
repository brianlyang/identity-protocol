# Protocol Remediation Audit Ledger (v1.6.20 broadcast-delivery / communication-transport convergence stream)

Status: Active (`ISSUE-038` closed on 2026-03-24; broadcast-delivery and communication-transport fleet convergence is now protocol-owned and workspace-runtime green)
Scope: protocol review ledger for additive broadcast-delivery / identity-communication-transport convergence across active runtime identities

## 0) Stream objective

Current-state judgment for this stream must remain anchored to:

- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/mappings/contract-binding.current.yaml`
- `identity/protocol/IDENTITY_RUNTIME.md`
- `docs/workbook/protocol-issue-register-v1.6.md`
- `docs/workbook/protocol-deep-audit-workbook-v1.6.md`

This stream freezes one bounded review judgment:

1. the residual gap was active-fleet adoption/convergence, not missing component-owner semantics;
2. the fix had to be shared infrastructure, not pack-local edits;
3. the transport topic had to remain broader than strict identity-to-identity messaging;
4. closure had to be proven on a real workspace fleet, including `base-repo-audit-expert-v3` as a direct runtime replay target.

## 1) Opening diagnosis absorbed into this stream

### 1.1 Broadcast-delivery adoption drift was real

Initial workspace replay showed:

1. `base-repo-audit-expert-v3` already passed the dedicated broadcast-delivery lane;
2. `custom-creative-ecom-analyst`, `base-repo-architect`, and `base-repo-closure-orchestrator` still failed `scripts/check_identity_broadcast_migration_closure.py` because `identity_broadcast_delivery_contract_v1` was not yet materially adopted on those packs.

Audit interpretation:

- the upstream broadcast source already existed;
- what was missing was dedicated active-pack adoption plus a fleet closure checker.

### 1.2 Communication-transport adoption drift was real

Initial workspace replay also showed:

1. `base-repo-audit-expert-v3` already carried the aggregate communication-transport contract after shared backfill;
2. the same three lagging identities still failed `scripts/check_identity_communication_transport_closure.py` because the aggregate contract had not yet been restored/adopted there.

Audit interpretation:

- the component contracts already existed across multiple owner streams;
- what was missing was one protocol-owned convergence row plus fleet closure wiring.

### 1.3 Aggregate transport needed bounded live bootstrap, not structure-only green

A direct replay on `custom-creative-ecom-analyst` after contract backfill proved one more important point:

1. structural contract adoption alone was insufficient;
2. the aggregate transport validator still failed while `protocol_feedback_atomic_emit` remained `SKIPPED_NOT_REQUIRED` on a pack with no materialized atomic receipt;
3. therefore the stream needed a shared convergence executor that could perform bounded live bootstrap instead of leaving atomic/bootstrap proof implicit or manual.

This is why `v1.6.20` closes through a dedicated shared runner rather than by weakening validator semantics.

## 2) Landed shared remediation

### 2.1 ASB16-RQ-053 broadcast-delivery remediation landed

Landed shared remediation:

1. `scripts/identity_broadcast_delivery_common.py`
2. `scripts/run_identity_broadcast_delivery.py`
3. `scripts/validate_identity_broadcast_delivery.py`
4. `scripts/check_identity_broadcast_migration_closure.py`
5. `scripts/ci/run_identity_broadcast_delivery_probes_ci.sh`

Audit judgment:

- `rq_053` is now a dedicated machine-consumed lane rather than piggybacking on host-gateway structure.

Additional extension-law judgment:

- the broadcast subdomain now carries explicit philosophy inheritance, truth-lifecycle language, and runtime adjudication boundaries through `identity/protocol/broadcast/README.md` + `BROADCAST_DOC_CONTROL.current.yaml`, with machine checks in `scripts/validate_protocol_broadcast_doc_control.py` and `scripts/ci/run_protocol_broadcast_doc_control_probes_ci.sh`; this prevents subdomain law from collapsing into prose-only explanation.

### 2.2 ASB16-RQ-054 identity-communication-transport remediation landed

Landed shared remediation:

1. `scripts/identity_communication_transport_common.py`
2. `scripts/run_identity_communication_transport.py`
3. `scripts/validate_identity_communication_transport.py`
4. `scripts/check_identity_communication_transport_closure.py`
5. `scripts/ci/run_identity_communication_transport_probes_ci.sh`

Audit judgment:

- `rq_054` is now a dedicated aggregate convergence lane with its own shared executor, validator, and fleet closure checker.
- Cross-CWD repo-catalog resolution is now hardened inside the transport chain itself, not left to caller luck: the aggregate validator, shared executor, canonical reply-channel validator, and split-receipt sub-validator now all canonicalize `repo-catalog` via the shared `resolve_repo_catalog_path(...)` primitive before spawning downstream replay.

### 2.3 Creator/backfill/gate wiring landed

Shared infrastructure now also consumes the stream through:

1. `scripts/create_identity_pack.py`
2. `scripts/repair_contract_backfill.py`
3. `scripts/identity_creator.py`
4. `scripts/required_gate_bundle_runner.py`
5. `scripts/ci/run_required_runtime_gates_ci.sh`
6. `scripts/release_readiness_check.py`
7. `identity/protocol/broadcast/README.md`
8. `identity/protocol/broadcast/BROADCAST_DOC_CONTROL.current.yaml`
9. `scripts/validate_protocol_broadcast_doc_control.py`
10. `scripts/ci/run_protocol_broadcast_doc_control_probes_ci.sh`
11. `scripts/runtime_fleet_closure_common.py`
12. `scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh`

Audit judgment:

- the stream is not isolated tooling; it is now wired into creator/update/gate/readiness surfaces.

### 2.4 Shared fleet-closure projection convergence landed

Shared remediation now also freezes the fleet-scan primitive itself:

1. `scripts/check_identity_broadcast_migration_closure.py` and `scripts/check_identity_communication_transport_closure.py` now consume `scripts/runtime_fleet_closure_common.py` rather than each reimplementing catalog selection, active-runtime iteration, validator subprocess decoding, and violation aggregation.
2. The shared primitive exposes `active_runtime_validator_fleet_closure_v1`, keeps `workspace_runtime_only` bounded to the explicit runtime catalog set, and keeps `repo_catalog_inclusive` replay explicit instead of silently widening the scan surface.
3. `scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh` is the additive proof that both closure checkers preserve the same fleet projection semantics while still surfacing their own validator-specific status rows.

## 3) Live proof and cross-verification

Cross-verified machine proof accepted in this stream:

1. `python3 -m py_compile` passed for the new/changed shared scripts, including `run_identity_communication_transport.py`.
2. `bash scripts/ci/run_identity_broadcast_delivery_probes_ci.sh` -> `PASS`.
3. `bash scripts/ci/run_identity_communication_transport_probes_ci.sh` -> `PASS`.
4. Direct runtime replay on `base-repo-audit-expert-v3` now returns `PASS_REQUIRED` for `scripts/run_identity_communication_transport.py`.
5. Shared backfill + shared convergence execution then replayed green on:
   - `custom-creative-ecom-analyst`
   - `base-repo-architect`
   - `base-repo-closure-orchestrator`
6. `python3 scripts/check_identity_broadcast_migration_closure.py --catalog <project-local absolute catalog> --workspace-runtime-only --json-only` now returns `PASS_REQUIRED`.
7. `python3 scripts/check_identity_communication_transport_closure.py --catalog <project-local absolute catalog> --workspace-runtime-only --json-only` now returns `PASS_REQUIRED`.
8. `bash scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh` -> `PASS`, proving the two closure checkers share one active-runtime fleet projection in both `workspace_runtime_only` and `repo_catalog_inclusive` modes.
9. `scripts/validate_required_contract_coverage.py --catalog ../.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --operation scan --json-only` continues to return overall green required coverage after the stream landed, confirming the new adoption did not reopen the required-coverage floor.
10. `bash scripts/ci/run_identity_communication_transport_probes_ci.sh` now also proves the prefixed relative `repo-catalog` surface stays green for both `scripts/validate_identity_communication_transport.py` and `scripts/run_identity_communication_transport.py`, closing the cross-CWD false-red that previously surfaced only when the aggregate validator spawned the reply-channel validator from protocol-root CWD.

## 4) Closed-state audit judgment

### 4.1 ASB16-RQ-053 broadcast-delivery closure accepted

Audit accepts `ASB16-RQ-053` as closed because:

1. dedicated contract adoption is now machine-restorable;
2. dedicated sync execution is now reusable;
3. dedicated fleet closure checking is now wired;
4. live workspace runtime replay is green;
5. the validator/sync projection is now bundle-compatible, so strict required-gate bundle consumption does not need a transport-specific bypass;
6. own-identity replay no longer false-fails at lane routing just because `execute_identity_upgrade.py` omitted actor-context forwarding into `validate_work_layer_gate_set_routing.py`.

### 4.2 ASB16-RQ-054 identity-communication-transport closure accepted

Audit accepts `ASB16-RQ-054` as closed because:

1. dedicated aggregate contract adoption is now machine-restorable;
2. a shared convergence executor now materializes the bounded live bootstrap steps instead of relying on manual atomic fixture writes;
3. dedicated fleet closure checking is now wired;
4. live workspace runtime replay is green.

### 4.3 Residual boundary kept explicit

This stream intentionally does **not** absorb unrelated open work:

1. `ISSUE-037` / `v1.6.19` tool/vendor live-link strengthening remains an independent open stream.
2. strict actor-session entry validation remains owned by the actor/session binding streams; it must not be relabeled as a transport residual merely because a synthetic `identity_creator.py validate` run used an unbound ad hoc session id.

## 5) Final frozen judgment

Audit closes `ISSUE-038` with one precise interpretation:

- the protocol already owned the component semantics,
- the residual gap was fleet adoption + convergence execution,
- the fix is now protocol-owned shared infrastructure,
- and the active workspace runtime fleet has demonstrably consumed it.
