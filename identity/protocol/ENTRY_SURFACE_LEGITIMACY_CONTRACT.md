# Entry Surface Legitimacy Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes the law that governs which entry surfaces are legitimate for the
machine world, which entry surfaces may drive active execution, and which
surfaces must remain recovery-only, helper-only, or outside entry legitimacy
altogether.

It is not:

1. a launcher installation checklist;
2. a host-specific startup memo;
3. a migration note for one workspace;
4. a substitute for current-turn machine adjudication.

## Root-law scope and non-goals

1. This file freezes root-domain entry-surface legitimacy law for the machine world.
2. It is not a convenience guide for whichever filename or helper happened to work locally.
3. It does not let discoverability helpers, fallback bridges, replay entry points, or support surfaces silently upgrade themselves into canonical execution entry.
4. It must not be treated as a startup receipt, launcher success log, or shortcut around machine-consumed entry enforcement surfaces.

## Purpose

Define which entry surfaces are legitimate, which entry surfaces may drive
active execution, which entry surfaces are confined to governed recovery, and
which surfaces must remain helper-only or demoted support material.

This file remains the authoritative root-domain contract for entry-surface
legitimacy law.

## Foundational design philosophy anchor

This entry-surface legitimacy contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why the protocol must decide which entry surfaces are legitimate and why entry surfaces must not drift over time;
2. this file freezes the concrete entry-surface legitimacy law: entry classes, required differentiations, entry-collapse prohibitions, and fail-close boundaries for entry admission;
3. this file is authoritative for root-domain entry-surface legitimacy law, but current-turn legality still depends on machine-consumed governance, mappings, validators, probes, runtime state, and receipts;
4. philosophical grounding does not replace the contract authority of this entry-surface legitimacy specification.

## Constitutional inheritance and authority boundary

This root-domain entry-surface legitimacy contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundary for active execution entry, no-backstop semantics, compatibility confinement, and governed launcher surfaces that entry legitimacy must preserve.
2. `IDENTITY_RUNTIME.md` freezes how lawful entry becomes embodied in launcher/startup entry, route/tool admission, active runtime entry, and governed recovery redirect behavior.
3. this file freezes the root-domain contract for entry-surface legitimacy itself.
4. root-contract authority must not be collapsed into philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- protocol architects and maintainers;
- auditors and reviewers acting on behalf of machine truth;
- identity instances and runtime maintainers that must decide whether an entry surface is legitimate;
- validators and probes that fail-close when helper, fallback, or support surfaces try to impersonate canonical entry.

It is not optimized as a human-comfort launcher tutorial.

## Runtime adjudication boundary

This file does not itself decide whether a concrete entry surface is legal in the present turn.

Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed governance/review documentation and admitted protocol deltas;
2. mappings, validators, probes, and readiness surfaces that check entry class, canonicality, recovery confinement, and active entry admission;
3. runtime state, receipts, and current-run evidence whenever a claim depends on live launcher/startup entry, live route/tool admission, or live recovery redirect behavior.

So this file freezes entry-surface legitimacy law, while runtime adjudication determines whether that law has actually been satisfied in the present turn.

## Entry-surface legitimacy law

The identity protocol must distinguish entry classes rather than flattening every visible path, helper, filename, or discoverable command into one vague notion of “some way in.”

Entry-surface legitimacy law must also remain machine-readable as separate
entry-class, differentiation, proof, limit, and collapse row families rather
than one narrative legitimacy claim.

Only governed entry surfaces admitted by law may drive active execution.

Recovery, migration, replay, diagnostics, helper, discoverability, fixture, import, or support surfaces may assist convergence, but they do not silently become canonical execution entry.

## Six entry classes

### 1. Frozen entry definition

An entry surface may be defined by shared law, contract, or registry before it becomes a live current-turn entry surface.

Entry role: `frozen_entry_definition`.

### 2. Natural-language collaboration entry surface

The operator may enter through the natural-language collaboration surface, but that does not by itself constitute machine execution entry.

Entry role: `natural_language_collaboration_entry_surface`.

### 3. Governed execution entry surface

A launcher/startup entry surface may drive active execution only when it is the governed canonical execution-entry surface for the present turn.

Entry role: `governed_execution_entry_surface`.

### 4. Governed recovery-only entry surface

A migration, replay, diagnostics, or repair entry surface may be legitimate for governed recovery without becoming the primary active execution entry.

Entry role: `governed_recovery_only_entry_surface`.

### 5. Discoverability-helper surface

A helper path, installation alias, visibility aid, or discoverability surface may help locate canonical entry without itself becoming canonical execution entry.

Entry role: `discoverability_helper_surface`.

### 6. Demoted support or non-entry surface

Fixtures, imports, support directories, commentary, and other demoted support materials may remain visible, but they must stay outside entry legitimacy for active execution.

Entry role: `demoted_support_or_non_entry_surface`.

## Required entry differentiations

The protocol must preserve the following differentiations:

1. frozen law-defined entry is separated from live governed execution entry;
2. natural-language collaboration entry is separated from machine execution entry;
3. governed execution entry is separated from governed recovery-only entry;
4. discoverability-helper surface is separated from canonical execution entry;
5. demoted support or non-entry surface is separated from any active entry surface;
6. visible installation or discoverability is separated from lawful entry admission.

When an entry-surface claim relies on governed proof, the proof stratum behind
that claim must match the entry-admission claim being asserted.

## Entry-admission proof discipline

Entry-surface legitimacy claims may be supported only by proof whose stratum
matches the entry-admission claim being asserted.

### 1. Frozen-definition entry-admission proof

Supports claims that an entry surface was defined by shared law or registry
rather than improvised from local convenience.

Proof role: `frozen_definition_entry_admission_proof`.

### 2. Collaboration-boundary entry-admission proof

Supports claims that natural-language collaboration entry remained distinct from
machine execution entry rather than collapsing operator presence into launcher
legality.

Proof role: `collaboration_boundary_entry_admission_proof`.

### 3. Governed-execution entry-admission proof

Supports claims that an entry surface was the governed canonical execution entry
for the present turn rather than merely visible, installed, or easy to invoke.

Proof role: `governed_execution_entry_admission_proof`.

### 4. Recovery-confinement entry-admission proof

Supports claims that migration, replay, diagnostics, or repair entry surfaces
remained confined to governed recovery rather than promoting themselves into
primary execution entry.

Proof role: `recovery_confinement_entry_admission_proof`.

### 5. Helper/support-demotion entry-admission proof

Supports claims that discoverability helpers, aliases, imports, fixtures, and
other support or non-entry surfaces remained demoted outside canonical entry.

Proof role: `helper_support_demotion_entry_admission_proof`.

## Entry-admission proof limits

The protocol must preserve these entry-admission proof limits:

1. frozen-definition entry-admission proof is not proof of collaboration-boundary preservation;
2. collaboration-boundary entry-admission proof is not proof of governed execution entry;
3. governed-execution entry-admission proof is not proof of recovery confinement;
4. recovery-confinement entry-admission proof is not proof of helper or support demotion;
5. helper/support-demotion entry-admission proof is not proof of lawful active execution entry.

## Non-compliant entry collapses

The following are non-compliant:

1. `declared_entry_as_live_execution_entry`: a law-defined or declared entry surface is treated as if it were already live governed execution entry.
2. `operator_surface_as_machine_execution_entry`: the operator collaboration surface is treated as if it were sufficient machine execution entry.
3. `recovery_entry_as_primary_execution_entry`: a recovery, replay, diagnostics, or repair entry surface is treated as if it were the canonical primary execution entry.
4. `helper_surface_as_canonical_entry`: a helper path, discoverability aid, or installation alias is treated as if it were canonical execution entry.
5. `support_surface_as_active_entry`: a demoted support or non-entry surface is treated as if it were active execution entry.
6. `installation_visibility_as_entry_legality`: visibility, installation presence, or easy discovery is treated as if it proved lawful entry admission.

## Validation

Use:

- `python3 scripts/validate_protocol_root_entry_surface_legitimacy.py --json-only`
- `bash scripts/ci/run_protocol_root_entry_surface_legitimacy_probes_ci.sh`

These checks validate:

1. the root contract file and its entry-surface legitimacy law;
2. the machine-consumed entry-surface legitimacy mapping;
3. the root-corpus integration rows that make the contract law-bearing rather than decorative.
