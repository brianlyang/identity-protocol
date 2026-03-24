# Truth Lifecycle Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that distinguishes truth existence, discoverability,
admissibility, current-run binding, and next-hop consumption inside the machine
world.

It is not:

1. a runtime evidence log;
2. a stream-local replay note;
3. a convenience explanation for one validator;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain truth-lifecycle law for the identity protocol.
2. It is not a runtime report, a historical replay summary, or an artifact sink.
3. It does not let later-stage evidence rewrite earlier-stage lifecycle meaning.
4. It must not be treated as a receipt, current-run proof blob, or direct success-path override.

## Purpose

Define the canonical lifecycle by which machine truth moves from frozen law into
current-turn operational closure.

This file remains the authoritative root-domain contract for truth-lifecycle
law.

## Foundational design philosophy anchor

This truth-lifecycle contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why truth existence, discoverability, admissibility, binding, and consumption are not the same thing;
2. this file freezes the concrete lifecycle law: lifecycle stages, required differentiations, lifecycle-collapse prohibitions, and fail-close boundaries for truth claims;
3. this file is authoritative for root-domain truth-lifecycle law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this truth-lifecycle specification.

## Constitutional inheritance and authority boundary

This root-domain truth-lifecycle contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundary for canonical truth, success-path admission, and current-turn enforcement terminals that truth lifecycle must preserve.
2. `IDENTITY_RUNTIME.md` freezes how truth lifecycle becomes embodied in runtime state, receipts, bindings, and next-hop consumption.
3. this file freezes the root-domain contract for truth-lifecycle law itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances and validators reasoning about what qualifies as present truth;
- probes and readiness surfaces that fail-close on lifecycle collapse.

It is not optimized as a human memory aid or retrospective narrative.

## Runtime adjudication boundary

This file does not itself decide whether a concrete truth claim is legal in the present turn.

Current-turn truth lifecycle legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. validators, probes, mappings, and readiness surfaces that check whether lifecycle stages are actually distinguished and installed;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live binding or live next-hop consumption.

So this file freezes truth-lifecycle law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Truth-lifecycle law

The identity protocol must distinguish lifecycle stages rather than flatten them into one vague notion of “having truth.”

No truth claim may be treated as full operational closure unless all required lifecycle stages have been carried through.

## Five lifecycle stages

### 1. Truth exists in protocol law

The truth has been defined, frozen, or registered by the protocol and exists as part of shared law.

Lifecycle role: `truth_exists`.

### 2. Truth is discoverable by instance

The instance can find the truth from the correct canonical source rather than only inferring it from historical discussion, incidental files, or sidecar residue.

Lifecycle role: `truth_discoverable`.

### 3. Truth is admissible as current-turn authority

The truth has passed the identity, path, state, receipt, validator, and gate constraints required for the current turn, and is qualified to serve as current authority.

Lifecycle role: `truth_admissible`.

### 4. Truth is bound to current run / current thread

The truth is not merely abstractly correct; it is actually bound to the current run, current thread, and current instance context.

Lifecycle role: `truth_bound`.

### 5. Truth is consumed by the next operational step

The truth has actually been consumed by the next hop and has driven a launcher path, runtime hook, route, receipt, gate, or operator-facing answer surface.

Lifecycle role: `truth_consumed`.

## Required lifecycle differentiations

The protocol must reject equivalence between adjacent lifecycle stages.

At minimum, it must preserve these distinctions:

1. truth exists in protocol law ≠ the instance has actually discovered it;
2. the instance discovered it ≠ it is admissible as current-turn authority;
3. it is admissible as current-turn authority ≠ it is bound to the current run / current thread;
4. it is bound to the current run / current thread ≠ the next operational step has actually consumed it;
5. some artifact or declaration exists ≠ full operational closure has been achieved.

## Non-compliant lifecycle collapses

The following are non-compliant:

1. `existence_equals_discovery`: shared-law existence is treated as if the instance has already discovered the truth.
2. `discovery_equals_admissibility`: discovery alone is treated as if current-turn authority has already been granted.
3. `admissibility_equals_binding`: admissibility is treated as if current-run or current-thread binding has already happened.
4. `binding_equals_consumption`: bound truth is treated as if the next hop has already consumed it.
5. `artifact_presence_equals_operational_closure`: the existence of an artifact or declaration is treated as full operational closure.

## Validation

Use:

- `python3 scripts/validate_protocol_root_truth_lifecycle.py --json-only`
- `bash scripts/ci/run_protocol_root_truth_lifecycle_probes_ci.sh`

These checks validate:

1. the root contract file and its lifecycle law;
2. the machine-consumed truth-lifecycle mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
