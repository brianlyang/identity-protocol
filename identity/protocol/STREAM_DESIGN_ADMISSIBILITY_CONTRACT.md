# Stream Design Admissibility Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the admissibility law for when a proposed protocol stream, shared
strengthening, owner split, or runtime extension is sufficiently specified to
enter governed protocol implementation.

It is not:

1. a stream-local planning memo;
2. a business/scenario checklist;
3. an implementation backlog;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain admissibility law for protocol-owned design work.
2. It is not a substitute for constitutional law in `IDENTITY_PROTOCOL.md` / `IDENTITY_RUNTIME.md`.
3. It is not a shortcut that promotes local technique, local residue, or one-off execution pressure directly into shared law.
4. It must not be treated as a current-turn approval receipt, merge receipt, or runtime success-path artifact.

## Purpose

Define the admissibility law that must be satisfied before a local idea becomes
a governed identity-protocol stream or shared strengthening lane.

This contract is scenario-agnostic and machine-world oriented.

This file remains the authoritative root-domain contract for stream-design
admissibility.

## Foundational design philosophy anchor

This admissibility contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why stream design must begin from ontology, truth lifecycle, normativity, responsibility split, and answer surface rather than from implementation appetite alone;
2. this file freezes the concrete admissibility law: required design questions, mandatory projection surfaces, outcome classes, and fail-close boundaries for protocol-owned design work;
3. this file is authoritative for root-domain stream-design admissibility law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, and runtime evidence;
4. philosophical grounding does not replace the contract authority of this admissibility specification.

## Constitutional inheritance and authority boundary

This root-domain admissibility contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the shared protocol-law boundaries for promotion, re-entry, conflict precedence, and root-vs-instance responsibility split that admissibility must preserve.
2. `IDENTITY_RUNTIME.md` freezes how admissible design later becomes embodied in runtime integration, evidence production, and machine adjudication.
3. this file freezes the root-domain admissibility contract that decides whether a proposal is specified enough to become governed protocol work at all.
4. root-contract authority must not be collapsed into either philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances surfacing protocol-strengthening candidates;
- validators and probes that fail-close on premature promotion into shared law.

It is not optimized as a human persuasion memo or stream-local coordination aid.

## Runtime adjudication boundary

This file does not itself decide whether a concrete proposal is legal in the present turn.

Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. validators, probes, mappings, and bundle/readiness surfaces that check whether the proposed law is actually installed;
3. runtime state, receipts, and current-run evidence whenever the proposal claims live operational closure.

So this file freezes admissibility law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Admissibility law

No protocol stream, shared strengthening, owner split, or runtime extension may enter governed implementation unless the five required design questions below are answered at protocol-law grade.

If a proposal cannot answer them, it remains one of the following:

1. a local technique;
2. an instance-adaptation concern;
3. an observation that may motivate strengthening later, but is not yet admissible as shared law.

Admissibility therefore precedes implementation. Implementation pressure does not create admissibility retroactively.

## Five required design questions

### 1. Ontology question

The proposal must define:

1. what exact object is being introduced, strengthened, or reclassified;
2. what neighboring objects it must not collapse into;
3. which non-goals remain outside that object.

If ontology is ambiguous, the proposal is not admissible.

### 2. Truth-lifecycle question

The proposal must define:

1. where canonical truth lives;
2. how that truth is discovered;
3. how that truth is admitted into governed law;
4. how that truth is bound to the current run / current thread when needed;
5. how that truth is consumed by the next hop.

If lifecycle closure is vague, the proposal is not admissible.

### 3. Normative question

The proposal must define:

1. which actions are permitted;
2. which boundaries must fail-close;
3. which success-path conditions are required;
4. which shortcuts are explicitly forbidden.

If normativity is only implied, the proposal is not admissible.

### 4. Responsibility-split question

The proposal must define:

1. which obligations belong to protocol law;
2. which obligations belong to identity instances;
3. which obligations belong to operator-facing collaboration;
4. which residues must not be mis-promoted across those layers.

If responsibility split is blurry, the proposal is not admissible.

### 5. Answer-surface question

The proposal must define:

1. what stable answer surface the operator ultimately receives;
2. which machine surfaces supply that answer;
3. which lower-layer artifacts may motivate strengthening without becoming the answer surface themselves.

If answer delivery is unstable, the proposal is not admissible.

## Admissibility-proof discipline

Claims that a proposal has answered the five required design questions at
protocol-law grade may be supported only by proof whose stratum matches the
question being claimed.

### 1. Ontology-closure proof

Supports claims that the proposal's object identity, non-collapse boundary, and
non-goals are explicitly closed.

Proof role: `object_identity_non_collapse_proof`.

### 2. Truth-lifecycle-closure proof

Supports claims that canonical truth, discovery, admissibility, run binding,
and next-hop consumption have been defined as one governed lifecycle.

Proof role: `truth_lifecycle_closure_proof`.

### 3. Normative-closure proof

Supports claims that permitted actions, fail-close boundaries, success-path
conditions, and forbidden shortcuts have been explicitly frozen.

Proof role: `normative_boundary_closure_proof`.

### 4. Responsibility-split-closure proof

Supports claims that protocol, instance, operator, and residue boundaries have
been explicitly split without laundering one layer into another.

Proof role: `responsibility_split_closure_proof`.

### 5. Answer-surface-closure proof

Supports claims that the operator-facing answer surface, supporting machine
surfaces, and non-answer artifacts have been explicitly distinguished.

Proof role: `operator_answer_surface_closure_proof`.

## Admissibility-proof limits

The protocol must preserve these admissibility-proof limits:

1. ontology-closure proof is not proof of truth-lifecycle closure;
2. truth-lifecycle-closure proof is not proof of normative closure;
3. normative-closure proof is not proof of responsibility-split closure;
4. responsibility-split-closure proof is not proof of answer-surface closure;
5. no admissibility proof may substitute for mandatory projection into governed surfaces.

## Mandatory projection surfaces

Admissible answers to the five design questions must be projected into governed surfaces appropriate to the proposal, including:

1. governance/review surfaces that freeze the intended strengthening scope;
2. root-contract and/or machine-registry surfaces that formalize the law-bearing shape;
3. validators and probes that fail-close on drift;
4. runtime answer surfaces and evidence paths when the proposal claims current-run or operational closure.

Presence in one surface alone is insufficient.

A required design question is not closed merely because this contract names
it. When the question points to a dedicated downstream root-domain contract,
lawful ingress also requires that downstream closure to remain
machine-governed.

## Admissibility outcome classes

A proposal must be classified into one of these outcome classes before implementation is treated as shared-law work:

1. `local_technique_only`
2. `instance_adaptation_only`
3. `governed_extension_strengthening`
4. `root_contract_strengthening`
5. `constitutional_strengthening`

The class must match the proposal's real layer. Misclassification is non-compliant.

## Non-compliant admission patterns

The following are non-compliant:

1. implementation-first promotion: code exists, therefore law exists;
2. scenario-first promotion: vivid local usage is treated as ontology proof;
3. checker-backfill promotion: latest validator behavior is treated as bottom-theory authority;
4. residue laundering: instance debt is relabeled as protocol debt without responsibility proof;
5. answer-surface collapse: internal evidence or support material is treated as operator answer merely because it exists.

## Validation

Use:

- `python3 scripts/validate_protocol_root_stream_design_admissibility.py --json-only`
- `bash scripts/ci/run_protocol_root_stream_design_admissibility_probes_ci.sh`

These checks validate:

1. the root contract file and its five-question law;
2. the machine-consumed admissibility mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
