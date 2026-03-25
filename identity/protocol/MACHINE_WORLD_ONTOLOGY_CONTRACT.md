# Machine World Ontology Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that defines what objects are allowed to exist in the
machine world, what each object is, and which semantic boundaries must remain
uncollapsed.

It is not:

1. a runtime troubleshooting memo;
2. a glossary appendix detached from machine law;
3. a stream-local naming cleanup note;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain machine-world ontology law for the machine world.
2. It is not a decorative vocabulary list or a prose style guide for naming things.
3. It does not let summary, history, path familiarity, or vague memory language override object boundaries.
4. It must not be treated as a runtime receipt, a local dictionary override, or a substitute for machine-consumed enforcement surfaces.

## Purpose

Define what objects actually exist in the identity protocol machine world, what
class each object belongs to, and what boundary prevents one object from
borrowing the meaning of another.

This file remains the authoritative root-domain contract for machine-world ontology law.

## Foundational design philosophy anchor

This machine-world ontology contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why the protocol must first define what exists in the world before it can govern discovery, truth, admission, binding, or recovery;
2. this file freezes the concrete machine-world ontology law: ontology strata, required world objects, object-boundary discipline, and non-compliant ontology collapses;
3. this file is authoritative for root-domain machine-world ontology, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this machine-world ontology specification.

## Constitutional inheritance and authority boundary

This root-domain machine-world ontology contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the shared protocol-law boundary for canonical truth sources, semantic separation, and root-law ordering that ontology law must preserve.
2. `IDENTITY_RUNTIME.md` freezes how those objects become embodied through governed runtime resolution, canonical state, canonical receipts, and admissible current-turn truth.
3. this file freezes the root-domain contract for machine-world ontology itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances and runtime maintainers that must distinguish object classes rather than merge them through convenience language;
- validators and probes that fail-close when world objects lose singular meaning.

It is not optimized as a human-comfort glossary or a local mnemonic note.

## Runtime adjudication boundary

This file does not itself decide whether a concrete object claim is legal in the present turn.

Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. validators, probes, mappings, and readiness surfaces that check whether object classes, paths, state, receipts, and evidence remain canonically separated;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live identity resolution, live authority binding, or live object consumption.

So this file freezes machine-world ontology law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Machine-world ontology law

The protocol must first define what objects are allowed to exist in the machine world, what each object is, and what it is not.

If object boundaries become vague, the machine world collapses into borrowed meanings, drifting paths, latest-as-current confusion, summary-as-truth confusion, history-as-authority confusion, or vague “memory” swallowing multiple distinct families.

## Four ontology strata

### 1. Identity-resolution objects

These objects establish who is currently resolved and from where:

- `identity_id`
- `scope`
- `work_layer`
- `source_layer`
- `catalog_path`
- `pack_path`
- actor / session tuple

Stratum role: `identity_resolution_object_stratum`.

### 2. Authority and execution-boundary objects

These objects establish how governed execution and current authority are recognized:

- launcher surface
- current-turn authoritative truth
- canonical state
- canonical receipt
- canonical artifact family

Stratum role: `authority_execution_object_stratum`.

### 3. Continuity and retention objects

These objects establish governed continuity and thread-scoped carry-forward:

- continuity brief
- dialogue-retention current-thread

Stratum role: `continuity_retention_object_stratum`.

### 4. Feedback, gate, and verdict objects

These objects establish governed evaluation, closeout, and cross-plane decision surfaces:

- protocol-feedback lane
- required gate bundle
- three-plane verdict

Stratum role: `feedback_gate_verdict_object_stratum`.

## Required ontology objects

The protocol must keep the following objects singular and machine-recognizable:

1. `identity_id` is the stable identity-resolution key rather than a prompt nickname or narrative persona label.
2. `scope` is the resolved operating scope rather than a free-form situational impression.
3. `work_layer` is the active execution layer rather than a vague locality intuition.
4. `source_layer` is the authority-bearing source layer rather than a convenience alias.
5. `catalog_path` is the canonical identity catalog source rather than a guessed filesystem memory.
6. `pack_path` is the canonical resolved pack location rather than a repo fixture substitute.
7. actor / session tuple is the machine-attested speaking/runtime tuple rather than a narrative self-claim.
8. launcher surface is the governed execution-entry surface rather than filename discovery by habit.
9. current-turn authoritative truth is the present-turn admissible authority rather than the latest visible artifact.
10. canonical state is the governed state object rather than an arbitrary local snapshot.
11. canonical receipt is the governed execution/admission receipt rather than any artifact that merely looks recent.
12. canonical artifact family is the governed output family rather than an undifferentiated memory bucket.
13. continuity brief is the governed re-entry object rather than raw transcript persistence.
14. dialogue-retention current-thread is the thread-scoped continuity object rather than global memory.
15. protocol-feedback lane is the governed feedback object rather than free-form commentary.
16. required gate bundle is the machine admission bundle rather than an informal checklist.
17. three-plane verdict is the governed cross-plane verdict object rather than a prose summary.

## Non-compliant ontology collapses

The following are non-compliant:

1. `term_meaning_borrowing`: terms borrow meaning from each other as if object boundaries were optional.
2. `arbitrary_path_drift`: paths drift arbitrarily and are treated as if path-bearing objects did not need canonical meaning.
3. `latest_as_current`: the latest visible artifact is treated as if it were automatically current-turn authority.
4. `summary_as_truth`: summary or projection is treated as if it were truth itself.
5. `history_as_authority`: history is treated as if it were present authority.
6. `memory_as_vague_bucket`: `memory` becomes a vague bucket that swallows multiple distinct object families and boundaries.

## Validation

Use:

- `python3 scripts/validate_protocol_root_machine_world_ontology.py --json-only`
- `bash scripts/ci/run_protocol_root_machine_world_ontology_probes_ci.sh`

These checks validate:

1. the root contract file and its machine-world ontology law;
2. the machine-consumed machine-world ontology mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
