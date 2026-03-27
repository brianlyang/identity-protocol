# Success-Path State Admissibility Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that governs which state classes may legitimately enter the
current-turn success path and which states must remain optional, recovery-only,
or demoted away from active execution.

It is not:

1. a runtime state dump;
2. a dashboard summary or status memo;
3. a replay ledger for one lane;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain success-path state admissibility law for the machine world.
2. It is not a stream-local state machine, a convenience rollout checklist, or a workspace-specific progress board.
3. It does not let visible status labels, local vividness, or support artifacts silently upgrade themselves into active success-path state.
4. It must not be treated as a current-turn success receipt, recovery log, or shortcut around machine-consumed state enforcement surfaces.

## Purpose

Define which state classes may enter the active success path, which states may
remain outside it without poisoning legality, which states must redirect into
governed recovery, and which states must remain demoted support or quarantine
material.

This file remains the authoritative root-domain contract for success-path state
admissibility law.

## Foundational design philosophy anchor

This success-path state admissibility contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why the protocol must decide which states may enter the success path and which state classes must remain outside active execution;
2. this file freezes the concrete state-admissibility law: state classes, required differentiations, state-collapse prohibitions, and fail-close boundaries for success-path admission;
3. this file is authoritative for root-domain success-path state admissibility law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this success-path state admissibility specification.

## Constitutional inheritance and authority boundary

This root-domain success-path state admissibility contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundary for active success paths, fail-close exposure, compatibility confinement, and state-class discipline that success-path state admissibility must preserve.
2. `IDENTITY_RUNTIME.md` freezes how success-path state admission becomes embodied in runtime state, readiness, route/tool admission, startup entry, and recovery redirect behavior.
3. this file freezes the root-domain contract for success-path state admissibility itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances and runtime maintainers that must decide which states may enter active execution;
- validators and probes that fail-close when visible state or support state tries to impersonate success-path state.

It is not optimized as a human-comfort progress summary.

## Runtime adjudication boundary

This file does not itself decide whether a concrete state is legal in the present turn.

Current-turn success-path state legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. mappings, validators, probes, and readiness surfaces that check state class, admissibility, recovery redirect, demotion, and success-path admission;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live state binding, live route/tool admission, or live execution progression.

So this file freezes success-path state admissibility law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Success-path state admissibility law

The identity protocol must distinguish state classes rather than flattening every visible status into one vague notion of “being green enough to proceed.”

Success-path state admissibility law must also remain machine-readable as separate state-class, differentiation, proof, state-class-proof-alignment, limit, and collapse row families rather than one narrative progress claim.

Only states admitted by law may enter the current-turn success path.

Optional non-entry, governed recovery, blocked, redirected, replay, diagnostics, archive, migration, fixture, or quarantine states may preserve context or motivate convergence, but they do not silently become active success-path state.

## Six state classes

### 1. Frozen state definition

A state may be defined by shared law, contract, or registry before it becomes a live current-turn state.

State role: `frozen_state_definition`.

### 2. Admissible current-turn state

A current-turn state may be admissible for the present turn when it has passed the relevant identity, path, gate, and state-class checks.

State role: `admissible_current_turn_state`.

### 3. Bound active success-path state

A current-turn state may enter the active success path only when it is not merely admissible in abstraction, but actually bound to the current run / current thread / current identity context and driving active execution.

State role: `bound_active_success_path_state`.

### 4. Optional non-entry state

A state may legitimately remain outside the active success path because the law does not require it for this turn, this lane, or this identity context.

State role: `optional_non_entry_state`.

### 5. Governed recovery-only state

A missing, ambiguous, contradictory, blocked, failed, or redirected state may enter governed recovery, repair, or replay lanes without being admitted to the active success path.

State role: `governed_recovery_only_state`.

### 6. Demoted support or quarantine state

Migration, replay, diagnostics, fixture, archive, support-only, and quarantine states may preserve context or proof, but they must remain outside active success-path admission.

State role: `demoted_support_or_quarantine_state`.

## Required state differentiations

The protocol must preserve the following differentiations:

1. frozen law-defined state is separated from admissible current-turn state;
2. admissible current-turn state is separated from bound active success-path state;
3. optional non-entry state is separated from governed recovery-only state;
4. governed recovery-only state is separated from demoted support or quarantine state;
5. visible status projection is separated from success-path state admission proof;
6. local progress feeling or convenience is separated from lawful state admission.

When a success-path state claim relies on governed proof, the proof stratum
behind that claim must match the state-admission claim being asserted.

## State-class proof alignment

Success-path state classes must preserve the proof stratum appropriate to the
state-admission class being asserted.

1. frozen-state-definition class requires frozen-definition state-admission proof;
2. admissible-current-turn-state class requires current-turn-admissibility state-admission proof;
3. bound-active-success-path-state class requires active-binding state-admission proof;
4. optional-non-entry-state class requires non-entry/recovery-classification proof;
5. governed-recovery-only-state class requires non-entry/recovery-classification proof;
6. demoted-support-or-quarantine-state class requires support/quarantine-confinement proof.

State summaries may compress these classes for readability, but they must not
pretend that one state-admission proof stratum is sufficient for all state
classes.

## State-admission proof discipline

Success-path state claims may be supported only by proof whose stratum matches
the state-admission claim being asserted.

### 1. Frozen-definition state-admission proof

Supports claims that a state class was defined by shared law or registry rather
than improvised from local vividness or convenience.

Proof role: `frozen_definition_state_admission_proof`.

### 2. Current-turn-admissibility state-admission proof

Supports claims that a state passed the relevant identity, path, gate, and
state-class checks for the present turn.

Proof role: `current_turn_admissibility_state_admission_proof`.

### 3. Active-binding state-admission proof

Supports claims that a state was not only admissible in abstraction but bound
to the current run / current thread / current identity context for active
success-path execution.

Proof role: `active_binding_state_admission_proof`.

### 4. Non-entry/recovery-classification proof

Supports claims that optional non-entry and governed recovery-only states were
classified lawfully rather than silently promoted into active execution.

Proof role: `non_entry_recovery_classification_state_admission_proof`.

### 5. Support/quarantine-confinement proof

Supports claims that migration, replay, diagnostics, archive, fixture,
support-only, or quarantine states remained demoted outside active success-path
admission.

Proof role: `support_quarantine_confinement_state_admission_proof`.

## State-admission proof limits

The protocol must preserve these state-admission proof limits:

1. frozen-definition state-admission proof is not proof of current-turn admissibility;
2. current-turn-admissibility state-admission proof is not proof of active binding;
3. active-binding state-admission proof is not proof of lawful non-entry or recovery classification;
4. non-entry/recovery-classification proof is not proof of support or quarantine confinement;
5. support/quarantine-confinement proof is not proof of active success-path admission.

## Non-compliant state collapses

The following are non-compliant:

1. `defined_state_as_live_success_state`: a law-defined or declared state is treated as if it were already live success-path admission.
2. `admissible_unbound_state_as_active_path_state`: an admissible but unbound state is treated as if it were already on the active success path.
3. `optional_state_as_failure_or_failure_as_optional`: optional non-entry state and governed recovery-only state are treated as if they were interchangeable.
4. `recovery_state_as_success_state`: a governed recovery, blocked, or redirected state is treated as if it were active success-path state.
5. `support_quarantine_state_as_active_state`: demoted support, migration, replay, diagnostics, archive, or quarantine state is treated as if it were active success-path state.
6. `status_projection_as_state_admission_proof`: a visible status label, projection, or dashboard summary is treated as if it proved lawful state admission.
7. `state_class_proof_flattening`: frozen-definition, admissible-current-turn, bound-active, optional-non-entry, governed-recovery, and demoted-support state classes are treated as if one state-admission proof stratum were sufficient for all of them.

## Validation

Use:

- `python3 scripts/validate_protocol_root_success_path_state_admissibility.py --json-only`
- `bash scripts/ci/run_protocol_root_success_path_state_admissibility_probes_ci.sh`

These checks validate:

1. the root contract file and its success-path state admissibility law;
2. the machine-consumed success-path state admissibility mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
