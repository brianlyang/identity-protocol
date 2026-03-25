# Error Terminality Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that governs which error classes must fail-close, which must
redirect into governed recovery, and which may remain non-blocking observation
without silently laundering active-path illegality.

It is not:

1. a stack-trace archive;
2. an incident postmortem;
3. a local retry memo;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain error terminality law for the machine world.
2. It is not a list of whatever warnings or failures happened to appear in one implementation lane.
3. It does not let contradiction, missing canonical truth, binding mismatch, contamination, or recovery conditions silently downgrade themselves into non-blocking comfort.
4. It must not be treated as a receipt, dashboard alert stream, or shortcut around machine-consumed error enforcement surfaces.

## Purpose

Define which error classes lawfully terminate current-turn legality, which error
classes lawfully redirect into governed recovery, and which materials must
remain observation-only or explanatory rather than terminal machine error
authority.

This file remains the authoritative root-domain contract for error terminality law.

## Foundational design philosophy anchor

This error terminality contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why the protocol must decide which errors must fail-close, why long-term order requires stable error meaning, and why convenience cannot demote active-path illegality into comfort;
2. this file freezes the concrete error-terminality law: error classes, required differentiations, error-collapse prohibitions, and fail-close versus redirect versus observation boundaries;
3. this file is authoritative for root-domain error terminality law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this error terminality specification.

## Constitutional inheritance and authority boundary

This root-domain error terminality contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundary for fail-close exposure, success-path admissibility, compatibility confinement, and recovery redirect semantics that error terminality must preserve.
2. `IDENTITY_RUNTIME.md` freezes how error terminality becomes embodied in runtime validators, probes, gates, redirect behavior, and current-run evidence.
3. this file freezes the root-domain contract for error terminality itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances, launchers, and runtime maintainers that must classify errors without semantic drift;
- validators and probes that fail-close when terminal, redirect, observation, and explanatory error classes collapse into one another.

It is not optimized as a troubleshooting narrative or operator-comfort summary.

## Runtime adjudication boundary

This file does not itself decide whether a concrete error is legal in the present turn.

Current-turn error terminality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. mappings, validators, probes, and readiness surfaces that check error class, terminality, redirect scope, demotion, and non-blocking boundaries;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live contradiction, live binding mismatch, live contamination, live redirect, or live observation classification.

So this file freezes error terminality law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Error terminality law

The identity protocol must distinguish error classes rather than flattening every anomaly into one vague notion of “some issue happened.”

Only lawfully classified errors may fail-close, redirect, or remain non-blocking in current-turn execution.

Contradiction, missing canonical truth, broken binding, active-path contamination, governed recovery redirect, observation-only drift, and explanatory materials are not interchangeable categories.

## Seven error classes

### 1. Frozen error definition

An error class may be defined by shared law, contract, or registry before it becomes a live current-turn error condition.

Error role: `frozen_error_definition`.

### 2. Fail-close legality error

A contradiction, missing canonical truth, admissibility blocker, or other legality-denying condition must terminate current-turn legality rather than being silently softened.

Error role: `fail_close_legality_error`.

### 3. Binding-integrity error

A run, thread, identity, path, or receipt binding mismatch must block continuation because current-turn integrity has been broken.

Error role: `binding_integrity_error`.

### 4. Active-path contamination error

Support, compatibility, recovery, replay, diagnostics, sample, or other demoted material entering the active path unlawfully is an error class of its own.

Error role: `active_path_contamination_error`.

### 5. Governed recovery-redirect error

Some errors lawfully redirect execution into governed recovery, replay, repair, or diagnostics lanes without being reclassified as active success-path continuation.

Error role: `governed_recovery_redirect_error`.

### 6. Non-blocking observation error

Some observations may remain visible, attributable, and machine-governed without terminating the present turn when the law explicitly confines them to non-blocking scope.

Error role: `non_blocking_observation_error`.

### 7. Demoted support or explanatory error material

Commentary, summaries, retrospective explanations, and other support material may explain an error or motivate strengthening, but they do not become terminal machine error authority by themselves.

Error role: `demoted_support_or_explanatory_error_material`.

## Required error differentiations

The protocol must preserve the following differentiations:

1. frozen law-defined error is separated from live fail-close legality error;
2. fail-close legality error is separated from binding-integrity error;
3. binding-integrity error is separated from active-path contamination error;
4. active-path contamination error is separated from governed recovery-redirect error;
5. governed recovery-redirect error is separated from non-blocking observation error;
6. non-blocking observation error is separated from demoted support or explanatory error material;
7. visible warning tone or local urgency is separated from lawful error terminality classification.

## Non-compliant error collapses

The following are non-compliant:

1. `defined_error_as_live_terminal_error`: a law-defined or declared error class is treated as if it were already a live current-turn terminal error.
2. `legality_blocker_as_warning`: a contradiction, missing canonical truth, or admissibility blocker is treated as if it were only a warning or soft suggestion.
3. `binding_mismatch_as_active_progress`: a run, thread, identity, path, or receipt mismatch is treated as if active execution may continue unchanged.
4. `contamination_blocker_as_normal_execution`: contamination of the active path by support, compatibility, recovery, replay, diagnostics, sample, or demoted material is treated as normal active execution.
5. `recovery_redirect_as_success_continuation`: a governed recovery or redirect condition is treated as if the active success path may continue or complete.
6. `observation_or_explanatory_material_as_terminal_authority`: a non-blocking observation or explanatory artifact is treated as if it were terminal machine error authority.
7. `local_convenience_as_error_demotion`: convenience, impatience, or local familiarity is treated as if it could lawfully demote a fail-close error.

## Validation

Use:

- `python3 scripts/validate_protocol_root_error_terminality.py --json-only`
- `bash scripts/ci/run_protocol_root_error_terminality_probes_ci.sh`

These checks validate:

1. the root contract file and its error terminality law;
2. the machine-consumed error terminality mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
