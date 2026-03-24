# Operator Answer Surface Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that governs how operator-facing answer surfaces are formed,
how lower-layer machine proof may support them, and how law-preserving
compression must remain distinct from machine-law bypass.

It is not:

1. a UI copy guide;
2. a prompt-style memo;
3. a runtime transcript sink;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain operator answer-surface law for the machine world.
2. It is not a template library for phrasing style or presentation preference.
3. It does not let operator comfort, local vividness, or convenient prose override machine-law boundaries.
4. It must not be treated as a receipt, terminal runtime verdict, or substitute for machine-consumed enforcement surfaces.

## Purpose

Define the stable operator answer surface, the supporting lower-layer proof
surfaces around it, and the boundary that lets an instance compress law into a
natural collaboration surface without betraying the law.

This file remains the authoritative root-domain contract for operator
answer-surface law.

## Foundational design philosophy anchor

This answer-surface contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why question class and answer surface must stay paired, why the operator should not bear low-level protocol memory burden, and why a mature instance compresses law into a stable answer surface without betraying the law;
2. this file freezes the concrete answer-surface law: surface strata, support-vs-answer boundaries, law-preserving compression rules, and non-compliant collapses;
3. this file is authoritative for root-domain operator answer-surface law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this answer-surface specification.

## Constitutional inheritance and authority boundary

This root-domain answer-surface contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the shared protocol-law boundary for question routing, machine-truth terminals, and lawful operator delivery that answer-surface law must preserve.
2. `IDENTITY_RUNTIME.md` freezes how answer surfaces become embodied in governed execution paths and protocol-owned operator-facing simplicity.
3. this file freezes the root-domain contract for operator answer-surface law itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances responsible for returning operator-facing answers without collapsing machine-law layers;
- validators and probes that fail-close when answer surface and machine proof collapse into each other.

It is not optimized as a UI design brief or convenience note for local usage.

## Runtime adjudication boundary

This file does not itself decide whether a concrete answer is legal in the present turn.

Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. validators, probes, mappings, and readiness surfaces that check whether answer-surface boundaries are actually installed;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live legality, live route consumption, or live proof.

So this file freezes answer-surface law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Operator answer-surface law

The operator-facing answer surface must remain stable, law-preserving, and
layered.

The protocol must not confuse support material, machine terminals, or internal
artifacts with the answer surface actually delivered to the operator.

## Four answer-surface strata

### 1. Operator entry surface

The operator enters through a natural-language collaboration surface rather than by carrying protocol-law internals directly.

Surface role: `natural_language_collaboration_entry`.

### 2. Stable instance answer surface

The instance must return a stable, natural, executable answer surface that compresses law without betraying the law.

Surface role: `law_compressed_operator_answer`.

### 3. Supporting machine-truth surface

Mappings, validators, probes, runtime state, receipts, and other governed machine-truth surfaces may support the answer surface without replacing it.

Surface role: `supporting_machine_truth_surface`.

### 4. Terminal machine-enforcement surface

Current-turn legality still terminates in machine-consumed enforcement surfaces; those terminals constrain the answer surface but do not become the operator collaboration surface themselves.

Surface role: `current_turn_legality_terminal`.

## Compression boundary

The protocol must preserve these answer-surface rules:

1. the operator should not bear the memory burden of low-level protocol law;
2. lower-layer proof may support the answer without replacing the answer surface itself;
3. operator simplicity must be achieved by law-preserving compression rather than by bypassing machine-law boundaries;
4. current-turn legality must still terminate in machine-consumed enforcement surfaces rather than in answer prose alone.

## Non-compliant answer-surface collapses

The following are non-compliant:

1. `support_proof_equals_answer`: supporting proof is treated as the operator answer itself.
2. `raw_internal_artifact_dumping`: internal artifacts or raw protocol burden are dumped directly onto the operator as if dumping were an answer surface.
3. `convenience_overrides_law_compression`: operator comfort or local convenience is used to bypass law-preserving compression and enforcement boundaries.
4. `answer_surface_seized_by_terminality`: a machine terminal or receipt blob is treated as if it were the operator collaboration surface.
5. `prose_without_machine_truth`: fluent answer prose is treated as sufficient despite missing machine-truth backing when such backing is required.

## Validation

Use:

- `python3 scripts/validate_protocol_root_operator_answer_surface.py --json-only`
- `bash scripts/ci/run_protocol_root_operator_answer_surface_probes_ci.sh`

These checks validate:

1. the root contract file and its answer-surface law;
2. the machine-consumed answer-surface mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
