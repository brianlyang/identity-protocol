# Decision Evidence Admissibility Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that governs which evidence classes may legitimately drive a
machine decision and which materials must remain non-terminal support only.

It is not:

1. a runtime evidence bundle;
2. a replay summary or migration memo;
3. a prose explanation for why a local verdict felt reasonable;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain decision-evidence admissibility law for the machine world.
2. It is not a receipt sink, a diagnostics report, or a convenience list of whatever evidence happened to be nearby.
3. It does not let recency, historical familiarity, support narration, or compatibility residue upgrade themselves into terminal decision evidence.
4. It must not be treated as a direct success-path override, a local confidence memo, or an implementation shortcut around machine-consumed enforcement surfaces.

## Purpose

Define which evidence classes may legitimately motivate, support, or terminally
justify a machine decision, and which evidence classes must remain demoted,
non-terminal, or off the active success path.

This file remains the authoritative root-domain contract for decision-evidence admissibility law.

## Foundational design philosophy anchor

This decision-evidence admissibility contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why the protocol must decide which receipts may serve as decision evidence and which historical or compatibility materials must remain confined;
2. this file freezes the concrete admissibility law: decision-evidence classes, required differentiations, evidence-collapse prohibitions, and fail-close boundaries for machine decisions;
3. this file is authoritative for root-domain decision-evidence admissibility law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this decision-evidence admissibility specification.

## Constitutional inheritance and authority boundary

This root-domain decision-evidence admissibility contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundary for current truth, active success paths, compatibility confinement, and canonical machine-evidence separation that decision-evidence admissibility must preserve.
2. `IDENTITY_RUNTIME.md` freezes how runtime state, receipts, validators, gates, and answer surfaces embody those boundaries in present-turn operation.
3. this file freezes the root-domain contract for decision-evidence admissibility itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances and runtime maintainers that must decide what may legitimately drive a machine decision;
- validators and probes that fail-close when non-terminal support material tries to impersonate terminal decision evidence.

It is not optimized as a human-comfort explanation of why a verdict felt plausible.

## Runtime adjudication boundary

This file does not itself decide whether a concrete evidence bundle is legal in the present turn.

Current-turn decision-evidence legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. mappings, validators, probes, and readiness surfaces that check evidence provenance, admissibility, run-binding, family legality, and terminal decision scope;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live decision justification, live gate passage, or live terminal consumption.

So this file freezes decision-evidence admissibility law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Decision-evidence admissibility law

A machine decision may be motivated, supported, or terminally justified only by evidence classes whose provenance, admissibility, binding, and terminal scope are appropriate for that decision.

No support material, historical residue, or compatibility lane may silently promote itself into terminal decision evidence for the active success path.

## Six decision-evidence classes

### 1. Frozen-law evidence

Frozen protocol law, constitutions, and root contracts may justify what the law permits or forbids, but they do not by themselves prove that a present-turn runtime condition has been satisfied.

Evidence role: `frozen_law_evidence`.

### 2. Machine-registry evidence

Machine-consumed registries and mappings may justify canonical aliases, active files, ordering, authority projection, and routing projection when the question is registry-resolvable.

Evidence role: `machine_registry_evidence`.

### 3. Validator-and-probe verdict evidence

Validators and probes may justify whether governed checks passed or failed, but only within the scope defined by their status keys, provenance, and fail-close boundaries.

Evidence role: `validator_probe_verdict_evidence`.

### 4. Bound runtime evidence

Runtime state, canonical receipts, and current-run evidence may justify present-turn operational legality only when they are canonically sourced, admissible, and bound to the current run / current thread / current identity context.

Evidence role: `bound_runtime_evidence`.

### 5. Adjudicated verdict closure evidence

Canonical receipts and governed closure artifacts may justify that an already lawful adjudication chain actually closed, but only when they summarize a path that was already lawfully admitted, evaluated, drift-negated, and live-bound.

They do not back-author frozen law, registry resolution, validator verdicts, or runtime-state live binding.

Evidence role: `adjudicated_verdict_closure_evidence`.

### 6. Demoted support evidence

Samples, fixtures, diagnostics, replay material, migration aids, handoff payloads, and operator-facing prose may motivate review or convergence work, but they must not terminate current-turn legality or silently enter the active success path as terminal decision evidence.

Evidence role: `demoted_support_evidence`.

## Required decision-evidence differentiations

The protocol must preserve the following differentiations:

1. motivating evidence is separated from terminal decision evidence;
2. latest visible receipt is separated from bound admissible receipt;
3. runtime evidence is separated from shared-law evidence;
4. summary, projection, or commentary is separated from source evidence;
5. sample, fixture, diagnostics, migration, and replay evidence are separated from active success-path evidence;
6. bound runtime evidence is separated from adjudicated verdict closure evidence;
7. handoff payload or operator-facing prose is separated from machine decision evidence.

When a decision-evidence claim relies on governed proof, the proof stratum
behind that claim must match the evidence-admissibility commitment being
asserted.

## Adjudication-phase evidence alignment

Current-turn legality may not use one adjudication phase's evidence stratum as if it automatically satisfied a later phase.

The minimum root alignment is:

1. runtime-state live binding requires bound runtime evidence and bound-runtime decision-evidence proof;
2. receipt-driven closure requires adjudicated verdict closure evidence and adjudicated-verdict-closure decision-evidence proof;
3. receipt closure may summarize a lawful adjudication chain, but it does not replace frozen law, registry resolution, validator verdict passage, or runtime-state live binding.

## Decision-evidence proof discipline

Decision evidence may support a machine decision only when the proof stratum
behind that support matches the admissibility class being asserted.

### 1. Frozen-law decision-evidence proof

Supports claims that a decision boundary was grounded in frozen protocol law
rather than in local convenience or historical residue.

Proof role: `frozen_law_decision_evidence_proof`.

### 2. Registry-resolution decision-evidence proof

Supports claims that canonical aliases, active files, ordering, authority
projection, or routing projection were resolved from machine registries when the
question is registry-resolvable.

Proof role: `registry_resolution_decision_evidence_proof`.

### 3. Validator-verdict decision-evidence proof

Supports claims that governed validators or probes passed, failed, or confined
decision evidence within the scope defined by their status keys and fail-close
boundaries.

Proof role: `validator_verdict_decision_evidence_proof`.

### 4. Bound-runtime decision-evidence proof

Supports claims that runtime evidence was canonically sourced, admissible, and
bound to the current run / current thread / current identity context for
present-turn terminal decision scope.

Proof role: `bound_runtime_decision_evidence_proof`.

### 5. Adjudicated-verdict-closure decision-evidence proof

Supports claims that canonical receipts or governed closure artifacts closed an
already lawful adjudication chain without rewriting the earlier legality phases
they summarize.

Proof role: `adjudicated_verdict_closure_decision_evidence_proof`.

### 6. Demotion-confinement decision-evidence proof

Supports claims that support-only, replay, migration, diagnostics, fixture, or
operator-facing material remained demoted and did not silently promote itself
into terminal decision evidence.

Proof role: `demotion_confinement_decision_evidence_proof`.

## Decision-evidence proof limits

The protocol must preserve these decision-evidence proof limits:

1. frozen-law decision-evidence proof is not proof of registry resolution;
2. registry-resolution decision-evidence proof is not proof of validator-and-probe verdict passage;
3. validator-verdict decision-evidence proof is not proof of bound runtime evidence;
4. bound-runtime decision-evidence proof is not proof of adjudicated verdict closure;
5. adjudicated-verdict-closure decision-evidence proof is not proof of upstream legality authorship or earlier-phase substitution;
6. adjudicated-verdict-closure decision-evidence proof is not proof that demoted support evidence may terminate the decision;
7. demotion-confinement decision-evidence proof is not proof that support material may enter active success-path terminal scope.

## Non-compliant decision-evidence collapses

The following are non-compliant:

1. `motivation_surface_as_terminal_evidence`: motivating or contextual material is treated as if it were terminal decision evidence.
2. `latest_visible_receipt_as_admissible_evidence`: the latest visible receipt is treated as if it were automatically bound admissible evidence.
3. `runtime_residue_as_shared_law_evidence`: runtime residue is treated as if it rewrote shared law or constitutional authority.
4. `summary_projection_as_source_evidence`: summary, projection, or commentary is treated as if it were source evidence.
5. `sample_fixture_diagnostic_as_live_decision_evidence`: sample, fixture, diagnostics, migration, or replay material is treated as if it were active success-path evidence.
6. `receipt_closure_as_upstream_legality_evidence`: receipt closure is treated as if it authored or replaced earlier legality phases.
7. `prose_payload_as_machine_decision_evidence`: handoff prose or operator-facing narration is treated as if it were machine decision evidence.

## Validation

Use:

- `python3 scripts/validate_protocol_root_decision_evidence_admissibility.py --json-only`
- `bash scripts/ci/run_protocol_root_decision_evidence_admissibility_probes_ci.sh`

These checks validate:

1. the root contract file and its decision-evidence admissibility law;
2. the machine-consumed decision-evidence admissibility mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
