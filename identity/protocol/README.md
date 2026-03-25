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
   - `MACHINE_LAW_PRIMACY_CONTRACT.md`
   - `MACHINE_WORLD_ONTOLOGY_CONTRACT.md`
   - `CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md`
   - `DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md`
   - `SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md`
   - `ENTRY_SURFACE_LEGITIMACY_CONTRACT.md`
   - `ERROR_TERMINALITY_CONTRACT.md`
   - `ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md`
   - `IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
   - `IDENTITY_DISCOVERY.md`
   - `AGENT_HANDOFF_CONTRACT.md`
   - `IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md`
   - `PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md`
   - `STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md`
   - `TRUTH_LIFECYCLE_CONTRACT.md`
   - `OPERATOR_ANSWER_SURFACE_CONTRACT.md`
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
   - machine-law primacy, machine-world ontology, current-truth epistemology, decision-evidence admissibility, success-path state admissibility, entry-surface legitimacy, error terminality, artifact-family admissibility, prompt bootstrap, discovery, handoff, instance self-judgement, protocol-instance responsibility, stream-design admissibility, truth lifecycle, operator answer surface, and other root-domain contracts
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
   - root contract files such as machine-law primacy, machine-world ontology, current-truth epistemology, decision-evidence admissibility, success-path state admissibility, entry-surface legitimacy, error terminality, artifact-family admissibility, prompt bootstrap, discovery, handoff, instance self-judgement, protocol-instance responsibility, stream-design admissibility, truth-lifecycle, and operator answer-surface contracts
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

## One-way derivation discipline

The root corpus must also preserve one-way derivation.

1. bottom theory may ground constitutions, root contracts, registries, and governed extensions;
2. constitutions and root contracts may freeze that grounding into more concrete law;
3. machine-consumed registries and runtime adjudication may operationalize and test that law;
4. a later enforcement verdict may expose incompleteness, but it must not become the semantic parent of the earlier layer it tests.

Explanatory or evidence surfaces may motivate strengthening, but they must re-enter root law only through governed refreezing at the proper layer.

So:

- root navigation may summarize root law, but it does not reverse-author it;
- support material may assist understanding, but it does not become a law-bearing parent of protocol meaning;
- current-turn evidence may justify strengthening, but it does not become generative source law by itself.

---

## Root promotion-demotion discipline

Promotion, demotion, and re-entry across protocol surfaces must remain governed.

1. outer governance, review, workbook, reference, evidence, runtime, receipt, and implementation surfaces may motivate strengthening, but they do not directly promote themselves into root law;
2. demoted support material cannot directly climb back into law-bearing root status;
3. root navigation may summarize root law, but it does not promote itself into constitutional or contract authorship;
4. runtime or receipt evidence may expose a real gap, but the gap re-enters root law only through governed refreezing at an allowed root gateway;
5. machine-registry and governed-extension surfaces may expose the need for upstream strengthening, but they do not reverse-author bottom theory or constitutions.

The allowed re-entry gateways for non-origin surfaces are narrower than the full root corpus:

- constitutional law;
- runtime constitutional law;
- root contract law;
- machine-registry law.

No outer or demoted surface may directly self-promote into root law without that governed re-entry path.

---

## Root gateway-admissibility discipline

Gateway admission must stay narrower than general motivation to strengthen.

1. gateway admission decides which non-origin surfaces may legally motivate each root gateway;
2. a gateway is not an origin substitute; admission only permits governed re-entry at that gateway's own effect scope;
3. constitutional, runtime-constitutional, and root-contract gateways refreeze law at their own layer;
4. machine-registry gateway projects machine-consumable registry truth and may terminate current-turn legality, but it does not let incoming motivation surfaces author upstream law;
5. gateway admission does not let an incoming surface inherit the gateway's authorship.

So the protocol must preserve two distinctions at once:

- a surface may be strong enough to motivate a gateway without becoming the semantic author of the gateway output;
- current-turn legality may terminate at machine-registry law while still preserving philosophy, constitution, and root-contract source order above it.

---

## Root conflict-precedence discipline

Conflict precedence must stay scoped to the kind of conflict being resolved.

1. semantic-meaning conflict resolves by source order, not by convenience, recency, or current checker vividness;
2. current-turn legality conflict resolves at machine-consumed enforcement terminals, not at philosophy prose, README text, or frozen contract prose alone;
3. gateway-authorship conflict resolves by gateway effect scope plus source order, not by the identity of the incoming motivating surface;
4. demotion-status conflict resolves by governed reclassification, not by later reuse, copying, or local familiarity.

So the protocol must reject these precedence collapses:

- a current validator result being treated as if it rewrote bottom theory;
- a motivating runtime artifact being treated as if gateway admission made it the author of gateway output;
- a reused demoted support artifact being treated as if it automatically recovered law-bearing status.

---

## Root question-routing discipline

Different root entries answer different classes of machine-world questions.

1. `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` answers the **generative why-question**:
   - why identity protocol law exists in this shape at all.
2. `README.md` answers the **root-entry question**:
   - how to enter the root corpus without semantic confusion.
3. `IDENTITY_PROTOCOL.md` and `IDENTITY_RUNTIME.md` answer the **constitutional law question**:
   - what protocol-law and runtime-law are concretely frozen.
4. Root contract files answer the **domain-law question**:
   - what machine-law primacy, machine-world ontology, current-truth epistemology, decision-evidence admissibility, success-path state admissibility, entry-surface legitimacy, error terminality, artifact-family admissibility, prompt, discovery, handoff, instance self-judgement, protocol-instance responsibility, stream-design admissibility, truth lifecycle, operator answer surface, and related root-domain law are concretely frozen.
5. `mappings/` answers the **machine-registry question**:
   - which aliases, active files, bindings, and registry rows are machine-consumed truth.
6. `broadcast/` and `plugins/` answer the **governed extension question**:
   - what narrower subdomain law is frozen under the root corpus.
7. `fixtures/` answers the **support-material question** only:
   - what demoted support material exists without becoming runtime truth.

The most important prohibition is strict:

- current-turn legality question must never terminate in philosophy text, README text, or frozen contract prose alone.

Current-turn legality must instead resolve from machine-consumed enforcement surfaces such as:

1. mappings and active-file aliases;
2. validators and probes;
3. runtime state and receipts.

---

## Root machine-registry completeness discipline

`identity/protocol/mappings/` is not a loose storage folder.

1. a law-bearing root mapping family does not gain canonical status from on-disk presence alone;
2. a governed root mapping family must appear in the admitted machine-registry child set, normally as a current file plus its active versioned file;
3. if a root mapping family exists on disk but is absent from that admitted child set, registry completeness has failed and current-turn consumption must fail-close.
4. an admitted root mapping family must disclose its validator, probe, shared-common, and emitted status-key enforcement surfaces to the machine world;

Runtime or validator code may consume only admitted root mapping families, not
the most convenient file discovered on disk.

Hidden enforcement knowledge does not satisfy registry completeness.

---

## Root-law bundle discipline

The root corpus is not governed by one monolithic text or one isolated
validator.

Constitutional spine, root admission/governance, source-order, authority
layering, question-routing, derivation, promotion/demotion transition,
gateway-admissibility, machine-registry completeness, and conflict precedence
must stay explicit and machine-governed together.

No single slice is sufficient by itself; the machine world must preserve them
as one governed root-law bundle.

If one slice drifts while the others stay green, the root corpus is not
partially healthy; it has a coherence failure that must fail-close and be
repaired at the matching root-law layer.

Bundle membership must also remain descriptor-concordant with the admitted
component families it binds.

A bundle row may not silently drift from a component family's own disclosed
validator, probe, shared-common, or emitted status-key surfaces.

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
