# Protocol-Instance Responsibility Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the responsibility law that separates protocol-defined world law from
instance-owned adaptation, convergence, and escalation behavior.

It is not:

1. an issue triage notebook;
2. a temporary ownership memo for one stream;
3. a local residue diary;
4. a substitute for current-turn runtime adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain responsibility law for the machine world.
2. It is not a runtime task planner, escalation ticket, or instance repair checklist.
3. It does not promote local pain, local vividness, or one-off residue directly into shared protocol law.
4. It must not be treated as a merge receipt, runtime success receipt, or operator-side convenience override.

## Purpose

Define which obligations belong to protocol law, which obligations belong to
identity instances, how those layers meet at the operator-facing surface, and
when a problem is admissible for protocol escalation rather than instance
self-repair.

This file remains the authoritative root-domain contract for protocol-vs-instance
responsibility law.

## Foundational design philosophy anchor

This responsibility contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why shared law and instance adaptation must remain separate, why the protocol defines the world, and why the instance converges its runtime back to law;
2. this file freezes the concrete responsibility law: the four-layer relation, protocol and instance obligations, operator-surface compression boundary, escalation admission law, and non-compliant boundary collapses;
3. this file is authoritative for root-domain responsibility law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this responsibility specification.

## Constitutional inheritance and authority boundary

This root-domain responsibility contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes shared-law ownership, escalation, and no-backstop boundaries that responsibility law must preserve.
2. `IDENTITY_RUNTIME.md` freezes how responsibility law becomes embodied in runtime integration, evidence production, and instance convergence behavior.
3. this file freezes the root-domain contract for protocol-vs-instance responsibility and escalation admissibility.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances determining whether a residue is local adaptation or shared-law debt;
- validators and probes that fail-close when responsibility boundaries blur.

It is not optimized as a human-comfort explanation or operator troubleshooting note.

## Runtime adjudication boundary

This file does not itself decide whether a concrete residue or escalation is legal in the present turn.

Current-turn responsibility legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. validators, probes, mappings, and readiness surfaces that check whether responsibility boundaries are actually installed;
3. runtime state, receipts, and current-run evidence whenever a claim depends on real convergence or real escalation proof.

So this file freezes responsibility law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Four-layer relation

These layers are not substitutes for each other. They are distinct responsibility strata.

### 1. Standard Codex layer

Standard Codex supplies the general execution substrate:

1. reasoning capability;
2. code and tool execution capability;
3. generalized task advancement capability.

Its layer role is `general_execution_substrate`.

### 2. Identity protocol layer

The identity protocol supplies the machine-governance law layer:

1. freezing canonical truth, state, evidence, and recovery boundaries;
2. defining what may enter the success path and what must fail-close;
3. publishing shared validators, probes, and machine-readable law.

Its layer role is `machine_governance_law_layer`.

### 3. Identity instance layer

Identity instances embody governed role runtimes:

1. carrying role responsibility under protocol law;
2. adapting local runtime surfaces back into compliance;
3. proving through real execution that the role still holds.

Its layer role is `embodied_role_runtime`.

### 4. Operator layer

The operator is the natural-language collaboration entry:

1. the operator should not carry protocol memory burden;
2. the operator should receive a stable answer surface compressed by law;
3. the operator does not become the author of lower-layer machine law.

Its layer role is `natural_language_collaboration_entry`.

## Responsibility law

The protocol defines the law of the world; the instance converges its runtime back to that law.

Protocol-instance responsibility law must also remain machine-readable as
separate layer, responsibility, escalation-trigger, escalation-proof,
escalation-limit, and boundary-collapse row families rather than one narrative
ownership claim.

### 1. Protocol-layer obligations

The protocol layer must:

1. freeze unambiguous terms;
2. define canonical paths, states, receipts, and families;
3. provide shared validators, probes, readiness checks, CI, and replay wiring;
4. resolve shared semantic contradictions, shared implementation conflicts, and machine-truth gaps;
5. define fail-close and success-path boundaries.

Its governing responsibility role is `defines_the_law_of_the_world`.

### 2. Instance-layer obligations

The instance layer must:

1. self-driven absorb protocol upgrades;
2. clean pack-local residue;
3. fill runtime state, receipt, and lane-adoption gaps;
4. repair path, surface, script, and evidence drift;
5. make its real runtime surface converge back to law.

Its governing responsibility role is `continuous_convergence_under_law`.

### 3. Operator-surface compression boundary

The operator-facing surface must remain compressed and law-preserving:

1. the operator receives a stable answer surface rather than raw machine-law burden;
2. lower-layer proof may support the answer without replacing the answer surface itself;
3. operator simplicity must be achieved by law-preserving compression, not by bypassing responsibility boundaries.

Its governing responsibility role is `stable_answer_surface_without_memory_burden`.

## Escalation admission law

A problem may rise from instance adaptation into protocol strengthening only if at least one of the following is true:

1. `protocol_semantics_not_unambiguous`: protocol semantics themselves are not unambiguous.
2. `shared_implementation_contradicts_shared_law`: shared implementation contradicts shared documentation or shared law.
3. `multi_instance_structural_gap`: multiple instances will reliably hit the same structural gap.
4. `machine_truth_incomplete`: machine truth itself is incomplete, so no amount of instance self-repair can achieve alignment.

If none of those triggers apply, the residue remains an instance-owned adaptation task.

When a residue is proposed for protocol escalation, the escalation-proof stratum
behind that proposal must match the trigger being claimed.

## Escalation-proof discipline

Escalation into shared protocol strengthening may be supported only by proof
whose stratum matches the trigger being asserted.

### 1. Semantic-ambiguity proof

Supports claims that protocol law lacks enough semantic singularity to decide
the case without upstream clarification.

Proof role: `shared_law_semantic_ambiguity_proof`.

### 2. Shared-law contradiction proof

Supports claims that shared implementation and shared law contradict each other
at the shared layer.

Proof role: `shared_law_implementation_contradiction_proof`.

### 3. Multi-instance structural-gap proof

Supports claims that the same structural gap recurs across instances and
therefore exceeds one instance's local adaptation boundary.

Proof role: `cross_instance_structural_gap_proof`.

### 4. Machine-truth incompleteness proof

Supports claims that the machine truth required for lawful convergence is
itself incomplete and cannot be completed by one instance acting alone.

Proof role: `machine_truth_incompleteness_proof`.

## Escalation-proof limits

The protocol must preserve these escalation-proof limits:

1. semantic-ambiguity proof is not proof of shared implementation contradiction;
2. shared-law contradiction proof is not proof of multi-instance structural gap;
3. multi-instance structural-gap proof is not proof of machine-truth incompleteness;
4. machine-truth incompleteness proof is not proof that instance convergence duty disappears;
5. no escalation proof may launder unproved local residue into protocol debt.

## Non-compliant boundary collapses

The following are non-compliant:

1. `instance_residue_laundering`: instance residue is relabeled as protocol debt without responsibility proof.
2. `protocol_backstop_laundering`: the protocol is treated as a shelter for unresolved instance convergence debt.
3. `operator_memory_dumping`: low-level protocol burden is pushed directly onto the operator instead of being compressed by the governed instance surface.
4. `runtime_authorship_inversion`: runtime evidence or current vividness is treated as if it authored the upstream law that interprets it.
5. `local_vividness_promotion`: one local pressure point is treated as sufficient proof of shared-law promotion.

## Validation

Use:

- `python3 scripts/validate_protocol_root_protocol_instance_responsibility.py --json-only`
- `bash scripts/ci/run_protocol_root_protocol_instance_responsibility_probes_ci.sh`

These checks validate:

1. the root contract file and its responsibility/escalation law;
2. the machine-consumed responsibility mapping;
3. the root-corpus integration rows that make this contract law-bearing rather than decorative.
