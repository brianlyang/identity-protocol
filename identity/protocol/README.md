# Identity Protocol Root Reading Order

## Purpose

This file is the root index for `identity/protocol/`.

It exists to make the protocol-root reading order explicit for the machine world:

- identity instances;
- launchers;
- validators;
- probes;
- runtime gates;
- protocol maintainers;
- reviewers and auditors acting on behalf of machine truth.

This file is not a runtime truth source, not a machine-consumed contract row, and not a substitute for governance/review docs, mappings, validators, runtime state, or receipts.

---

## Root reading order

When entering `identity/protocol/`, read in this order:

1. **`IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`**
   - the bottom theory;
   - the generative reason the identity protocol exists at all;
   - the interpretive source for machine-law priorities, semantic singularity, fail-close preference, lifecycle closure, and shared-law vs instance-adaptation boundaries.
2. **`IDENTITY_PROTOCOL.md`**
   - the protocol-law constitution;
   - the root protocol boundary, governance stack, and active stream framing.
3. **`IDENTITY_RUNTIME.md`**
   - the runtime constitution;
   - how protocol law is embodied in runtime integration, startup, execution checks, and active-runtime boundaries.
4. **root contract files**
   - `IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
   - `IDENTITY_DISCOVERY.md`
   - `AGENT_HANDOFF_CONTRACT.md`
   - these freeze concrete contract law for their specific domains.
5. **machine-consumed registries and mappings**
   - `mappings/`
   - these freeze machine-facing rows, bindings, and registry truth.
6. **specialized subdomain protocol packs**
   - `broadcast/`
   - `plugins/`
   - these extend the root protocol into narrower governed surfaces.
7. **non-runtime or support material**
   - `fixtures/`
   - these are never active-runtime truth.

---

## What belongs at protocol root

`identity/protocol/` is the law-bearing root corpus of the identity protocol
for the machine world.

The following classes belong here:

1. **bottom theory / interpretive source**
   - `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`
2. **constitutions**
   - `IDENTITY_PROTOCOL.md`
   - `IDENTITY_RUNTIME.md`
3. **root contract law**
   - prompt bootstrap, discovery, handoff, and other root-domain contracts
4. **machine-consumed registries and mappings**
   - canonical bindings, term registries, stream registries, scope matrices, and related SSOT rows
5. **governed subdomain protocol extensions**
   - subdirectories such as `broadcast/` and `plugins/`
6. **clearly demoted support material**
   - only when it is explicit that the material is not active-runtime truth

The root directory should remain sparse, law-bearing, and semantically stable.

---

## What must not be treated as protocol-root law

The following do **not** belong in `identity/protocol/` as law-bearing root
material:

1. stream-local closure chatter or temporary remediation narration;
2. workbook issue projections or cross-stream cleanup ledgers;
3. workspace-specific convenience notes;
4. business strategy, domain tactics, or scenario heuristics;
5. instance-local residue diaries, one-off troubleshooting notes, or operator memory aids;
6. temporary persuasion text that is not part of bottom theory, constitutional law, contract law, or machine-consumed registry truth.

When such material is valuable, it should live in the appropriate outer surface
instead:

- `docs/governance/`
- `docs/review/`
- `docs/workbook/`
- `activity/evidence/`
- runtime-pack or instance-local governed roots

---

## Why philosophy comes first

In philosophical order, the identity protocol exists because `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` exists first.

That means:

1. the protocol does not invent its own reason for being at the contract layer;
2. the protocol formalizes, freezes, and operationalizes the machine-world bottom theory defined there;
3. every root constitution or contract file in this directory should be interpreted as a more concrete freezing of those bottom-theory commitments.

Philosophical primacy, however, is not the same as runtime-source primacy.

---

## Authority layering

The authority order is layered, not flattened:

1. **bottom-theory primacy**
   - `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`
   - explains *why* protocol law has the shape it has.
2. **constitutional / contract authority**
   - `IDENTITY_PROTOCOL.md`
   - `IDENTITY_RUNTIME.md`
   - root contract files such as prompt bootstrap, discovery, and handoff contracts
   - these define *what law is concretely frozen*.
3. **machine-consumed enforcement authority**
   - governance/review docs
   - mappings
   - validators
   - probes
   - runtime state
   - receipts
   - these determine *current machine truth and pass/fail authority*.

So the reading rule is:

- philosophy first for interpretation;
- constitution and contracts next for frozen law;
- machine-consumed truth last for current authority and runtime verdict.

---

## Source-order, reading-order, and adjudication-order

These three orders must remain distinct for the machine world:

1. **source-order / generative-order**
   - `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`
   - `IDENTITY_PROTOCOL.md` / `IDENTITY_RUNTIME.md`
   - root contract files
   - machine-consumed enforcement surfaces
   - answers: where protocol law comes from.
2. **root reading-order**
   - the entry sequence defined at the top of this file
   - answers: how to enter the root corpus without semantic confusion.
3. **adjudication-order**
   - governance/review docs, mappings, validators, probes, runtime state, and receipts
   - answers: how current-turn legality and machine verdict are determined.

Do not collapse these orders:

- a stream, checker, validator, or runtime verdict is not the source of bottom theory;
- this README's reading order is not itself the origin of protocol law;
- philosophy explains why law exists in its current shape, but does not replace machine adjudication.

---

## Conflict-handling rule

If two layers seem to disagree, resolve them with the following discipline:

1. do not use local convenience or historical familiarity to override protocol law;
2. do not use philosophy text to override a concrete contract row or runtime truth source;
3. do use philosophy text to interpret why a contract should be strengthened, split, or fail-closed;
4. do use machine-consumed sources to determine current-turn truth, validation status, and active-runtime legality.

---

## Root maintenance guardrails

When root protocol files are authored or updated, the following guardrails must remain explicit:

1. **stream/version is manifestation, not origin**
   - stream or release labels mark governed freeze history;
   - they do not become the philosophical source of protocol existence;
   - no root contract should be written as if a stream label were prior to bottom theory.
2. **machine verdict is adjudication, not philosophy source**
   - validators, probes, mappings, runtime state, and receipts determine current machine verdict;
   - they do not retroactively define the meaning of design philosophy;
   - philosophy explains why law has the shape it has, while machine-consumed surfaces decide current-turn legality.
3. **root contracts must preserve layer clarity**
   - each root contract should state what bottom-theory commitments it inherits;
   - each root contract should also state which concrete law it freezes;
   - no root contract should blur philosophical grounding, contract freezing, and runtime-source authority into one layer.
4. **root corpus admission must stay law-bearing**
   - the root directory should accept only bottom theory, constitutions, root contracts, machine-consumed registries/mappings, governed subdomain protocol packs, and clearly demoted support material;
   - stream-local commentary, workbook material, business strategy, or workspace residue must not be promoted into protocol-root law-bearing position.
5. **root-corpus admission must be machine-governed**
   - law-bearing admission, classification, and exclusion at `identity/protocol/` should be mirrored in protocol-owned registry / validator / probe surfaces rather than left to reviewer taste or oral memory;
   - if root purity depends only on human recollection, the root corpus has already started to drift away from machine law.

---

## Machine-world entry summary

If a machine-governed participant enters `identity/protocol/` and needs the minimum correct path:

1. read `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` to understand the bottom theory;
2. read `IDENTITY_PROTOCOL.md` and `IDENTITY_RUNTIME.md` to understand protocol and runtime constitutions;
3. read the relevant root contract file for the concrete domain being executed;
4. read mappings / governance / validators / runtime truth sources for the final machine-consumed verdict.

That is the canonical reading order for this directory.
