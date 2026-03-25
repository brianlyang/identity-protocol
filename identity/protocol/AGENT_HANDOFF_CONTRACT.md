# Agent Handoff Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It exists to freeze the concrete machine-law rules for governed handoff between
master and sub agents.

It is not:

1. an operator tutorial;
2. a workspace-local execution memo;
3. a stream-closure narrative;
4. a substitute for machine-consumed adjudication surfaces such as validators,
   runtime logs, or receipts.

## Root-law scope and non-goals

1. This file freezes root-domain handoff law for governed coordination between master and sub agents.
2. It is not an execution playbook for any single stream, workspace, or business scenario.
3. It is not a substitute for constitutional law in `IDENTITY_PROTOCOL.md` / `IDENTITY_RUNTIME.md`.
4. It must not be treated as a current-turn success receipt or as a shortcut around machine-consumed handoff evidence.

## Purpose

Define governed handoff law for bounded orchestration between master and sub agents, including role boundaries, payload requirements, evidence and next-step anchors, validation-track separation, and fail-close handoff collapses.

This file remains the authoritative root-domain contract for governed agent-handoff law.

## Foundational design philosophy anchor

This handoff contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why identity protocol treats handoff as machine-law coordination rather than informal collaboration;
2. this file freezes the concrete handoff law: role boundaries, payload law, evidence and next-step anchors, validation-track separation, and fail-close collapses;
3. this file is authoritative for root-domain handoff law, but current-turn legality is still adjudicated through machine-consumed validators, logs, and receipts;
4. philosophical grounding does not replace the fail-close authority of this contract.

## Constitutional inheritance and authority boundary

This root-domain handoff contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the shared-law boundaries for delegation, ownership split, escalation, and protocol-governed control loops that handoff must preserve.
2. `IDENTITY_RUNTIME.md` freezes how governed handoff becomes embodied in runtime execution, evidence production, merge/replay blocking, and current-turn answer surfaces.
3. this file freezes the root-domain handoff contract that must be obeyed by orchestrators, validators, and replay lanes without scenario-specific reinterpretation.
4. root-contract authority must not be collapsed into either philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- identity instances;
- launchers and orchestrators;
- validators and probes;
- runtime gates;
- protocol maintainers acting on behalf of machine truth.

It is not optimized as a human-memory aid. Its job is to make handoff law
stable enough for machine-world consumption.

## Runtime adjudication boundary

This file does not itself decide whether a concrete handoff was legal in the present turn.

Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed handoff validators and probes;
2. runtime logs, evidence artifacts, and receipts produced for the current run;
3. merge/replay gates that fail-close on missing or contradictory evidence.

So this file freezes handoff law, while runtime adjudication determines whether that law has actually been satisfied in execution.

## Governed handoff law

Governed handoff is not informal collaboration. It is a law-bounded transfer of
scoped execution responsibility that must preserve ownership boundaries,
evidence continuity, and next-step executability.

A handoff is lawful only when role ownership, payload completeness, evidence
binding, and validation-track discipline remain explicit rather than inferred
from narrative goodwill, memory, or local convenience.

Sample or self-test material may strengthen validator confidence, but it must
not silently replace current-run production handoff proof.

## Two governed handoff roles

### 1. Master orchestration role

The master orchestrator may decompose objectives, assign bounded scope, choose
routing, decide phase gates, and accept or reject handoff evidence for
continuation.

Handoff role: `master_orchestrator`.

### 2. Delegated sub-agent execution role

The delegated sub-agent may execute only within assigned scope, emit structured
evidence, report failure hypotheses, and return bounded next-step outputs
without mutating shared identity law.

Handoff role: `delegated_sub_agent_execution`.

## Mandatory handoff payload fields

Each lawful handoff record must include:

- `handoff_id`
- `task_id`
- `from_agent`
- `to_agent`
- `input_scope`
- `actions_taken`
- `artifacts`
- `result`
- `next_action`
- `rulebook_update`

Missing any required field means the handoff is not lawfully deliverable.

## Required handoff evidence and next-step anchors

The protocol must preserve all of the following:

1. each artifact item includes `path` and `kind`;
2. `rulebook_update.evidence_run_id` is required when `rulebook_update.applied=true`;
3. `next_action` includes `owner`, `action`, and `input`;
4. production handoff evidence remains freshness-bounded and identity/task scoped when current-turn legality is claimed;
5. production and sample validation tracks remain separated so sample proof never stands in for current-run runtime proof.

When a handoff claim relies on governed proof, the proof stratum behind that
claim must match the handoff claim being made.

## Handoff-proof discipline

Governed handoff may be supported only by proof whose stratum matches the
handoff claim being asserted.

### 1. Role-boundary proof

Supports claims that master and delegated roles remained within their lawful
ownership boundaries during handoff.

Proof role: `role_boundary_governed_handoff_proof`.

### 2. Payload-completeness proof

Supports claims that the handoff record contains the full required governed
payload rather than an informal narrative summary.

Proof role: `payload_completeness_governed_handoff_proof`.

### 3. Evidence-binding proof

Supports claims that handoff artifacts, freshness, identity/task scope, and
rulebook evidence binding remain lawful for the claimed result.

Proof role: `evidence_binding_governed_handoff_proof`.

### 4. Next-step-executability proof

Supports claims that the handoff delivered an executable next action rather
than a non-actionable summary.

Proof role: `next_step_executability_governed_handoff_proof`.

### 5. Validation-track-separation proof

Supports claims that production runtime handoff proof and sample/self-test proof
remain separated without track laundering.

Proof role: `validation_track_separation_governed_handoff_proof`.

## Handoff-proof limits

The protocol must preserve these handoff-proof limits:

1. role-boundary proof is not proof of payload completeness;
2. payload-completeness proof is not proof of evidence binding;
3. evidence-binding proof is not proof of next-step executability;
4. next-step-executability proof is not proof of validation-track separation;
5. validation-track-separation proof is not proof of current-turn production handoff legality by itself.

## Non-compliant handoff collapses

The following are non-compliant:

1. `delegated_scope_as_global_contract_authority`: a delegated sub-agent mutates top-level identity or protocol contract surfaces as if delegated execution granted global law authorship.
2. `completion_without_evidence_artifacts`: a handoff claims completion without evidence artifacts that support the claimed result.
3. `missing_executable_next_action_as_valid_delivery`: a handoff omits an executable next action but is treated as a valid delivery.
4. `contradictory_evidence_as_successful_handoff`: a handoff result is treated as valid even when it contradicts the provided evidence.
5. `sample_track_as_production_runtime_proof`: sample or self-test validation is treated as if it proved present-turn production handoff legality.

## Validation

Use:

- `python3 scripts/validate_protocol_root_agent_handoff.py --json-only`
- `bash scripts/ci/run_protocol_root_agent_handoff_probes_ci.sh`
- `python3 scripts/validate_agent_handoff_contract.py --identity-id <id>`
- `python3 scripts/validate_agent_handoff_contract.py --identity-id <id> --self-test`

These checks validate:

1. the root-domain handoff law, machine-consumed handoff mapping, and root-corpus integration;
2. production handoff logs from runtime paths;
3. positive and negative sample fixtures in self-test mode.

## Runtime validation tracks

Production track:

- validate runtime logs from production paths such as `identity/runtime/logs/handoff/*.json`;
- enforce freshness, minimum evidence, and identity/task scoping when current-turn legality is claimed.

Sample track:

- run self-test fixtures under `identity/runtime/examples/handoff/positive/` and `identity/runtime/examples/handoff/negative/`.

Production and sample tracks must not be collapsed into one vague notion of “some handoff proof exists.”

## Merge policy

If handoff validation fails:

- identity update merge is blocked;
- return to update loop;
- replay is required after fix.
