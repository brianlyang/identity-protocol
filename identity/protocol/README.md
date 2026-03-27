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
   - the terminal machine chain stays explicit as mappings → validators → probes → runtime state → receipts
   - answers: how current-turn legality and machine verdict are determined.

Do not collapse these orders:

- a stream, checker, validator, or runtime verdict is not the source of bottom theory;
- this README's reading order is not itself the origin of protocol law;
- philosophy explains why law exists in its current shape, but does not replace machine adjudication.

---

## Root adjudication-surface discipline

Current-turn legality must not flatten the machine surfaces that participate in adjudication.

1. mappings admit applicable machine law and registry truth for current-turn legality;
2. validators test legality against that admitted law rather than inventing new origin law;
3. probes negate drift by fail-closing weakened or hidden legality assumptions;
4. runtime state binds live current-turn truth only after prior legality phases have remained lawful;
5. receipts close the adjudicated verdict and must not back-author earlier legality phases.

That also means runtime-state binding evidence is not the same as receipt-closure evidence:

- runtime state proves live lawful binding;
- receipts prove lawful closure of an already-valid chain.

So the terminal chain is ordered and phase-governed at the same time:

- mappings are admissible-law resolution;
- validators are governed legality evaluation;
- probes are fail-close drift negation;
- runtime state is live-truth binding;
- receipts are adjudicated verdict closure.

No machine surface in that chain may silently inherit another surface's role merely because it is later, more vivid, or closer to operator visibility.

Operator-facing compression must preserve that discipline as well: a realized-effect
answer claim cannot borrow the backing stratum of a live-bound status claim, and
neither may borrow the backing stratum of frozen law or discovery.

Operator-facing compression must preserve epistemic posture as well: realized-effect
projection cannot borrow the current-truth posture of source grounding, governed
resolution, fail-close admissibility, or live-bound status.

Current-truth justification itself must preserve commitment-specific proof
posture as well: source grounding, governed resolution, present-turn authority,
derivational provenance, and fail-close justification do not share one generic
epistemic proof layer.

Success-path state handling must preserve state-class proof posture as well:
defined, admissible, bound-active, optional, recovery, and demoted-support
state classes do not share one generic state-admission proof layer.

Decision-evidence handling must preserve evidence-class proof posture as well:
frozen-law, registry, validator-verdict, bound-runtime, closure, and
demoted-support evidence classes do not share one generic decision-evidence
proof layer.

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

The governed re-entry chain stays explicit as: constitution -> runtime constitution
-> root contract -> machine-registry.

No outer or demoted surface may directly self-promote into root law without that governed re-entry path.

---

## Root gateway-admissibility discipline

Gateway admission must stay narrower than general motivation to strengthen.

1. gateway admission decides which non-origin surfaces may legally motivate each root gateway;
2. a gateway is not an origin substitute; admission only permits governed re-entry at that gateway's own effect scope and effect target class;
3. gateway effect target stays fixed by gateway class itself; incoming motivation may not choose a different root output class;
4. gateway effect target also keeps the question class governed for that target layer; incoming motivation may not retag gateway output as a different answer class;
5. constitutional, runtime-constitutional, and root-contract gateways refreeze law at their own layer;
6. machine-registry gateway projects machine-consumable registry truth and may terminate current-turn legality, but it does not let incoming motivation surfaces author upstream law;
7. gateway admission does not let an incoming surface inherit the gateway's authorship.

So the protocol must preserve two distinctions at once:

- a surface may be strong enough to motivate a gateway without becoming the semantic author of the gateway output;
- current-turn legality may terminate at machine-registry law while still preserving philosophy, constitution, and root-contract source order above it.

---

## Root conflict-precedence discipline

Conflict precedence must stay scoped to the kind of conflict being resolved.

1. semantic-meaning conflict resolves by source order, not by convenience, recency, or current checker vividness;
2. current-turn legality conflict resolves at machine-consumed enforcement terminals, not at philosophy prose, README text, or frozen contract prose alone;
3. gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and source order, not by the identity of the incoming motivating surface;
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
8. gateway-mediated refreezing or projection keeps the question class governed by the gateway target layer:
   - it does not inherit a new answer class from incoming motivation or local convenience.

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
4. an admitted root mapping family must disclose its validator, probe, shared-common, emitted status-key, and emitted error-code enforcement surfaces to the machine world;

Runtime or validator code may consume only admitted root mapping families, not
the most convenient file discovered on disk.

Hidden enforcement knowledge does not satisfy registry completeness.

Repo-relative descriptor surfaces must also stay repo-root relative and
repo-contained; absolute paths and parent-escape paths are non-compliant even
if they exist locally.

Repo-relative descriptor surfaces must also remain role-typed; validator,
probe, and shared-common paths are not interchangeable repo files.

Those role-typed surfaces must also remain cross-role coherent; validator,
probe, and shared-common paths for one admitted family may not silently point
at different root surface stems.

Those cross-role coherent descriptor surfaces must also remain family-congruent;
if an admitted family borrows another family's coherent descriptor stem, that
binding must be explicitly declared in registry completeness law.

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

Local waiver of descriptor concordance must remain forbidden inside the
bundle.

A bundle row may not silently drift from a component family's own disclosed
validator, probe, shared-common, emitted status-key, or emitted error-code
surfaces.

Nor may the bundle silently drift descriptor-field mode:

- repo-relative paths must remain repo-relative paths;
- validator-emitted status keys must remain validator-emitted status keys;
- validator-emitted error-code families must remain validator-emitted
  error-code families.

The bundle may not locally reauthor that descriptor schema either; the field
set and field-mode law used by the root-law bundle must stay aligned with the
admitted machine-registry completeness law for self-describing mapping
families.

The bundle's descriptor schema must remain source-singular as well.

It may not substitute a different source component/current mapping pair or
fallback source for convenience.

Local reauthoring of descriptor schema governance must remain forbidden
inside the bundle.

If that admitted source is unavailable or invalid, the machine world must
fail-close rather than locally reconstructing descriptor schema.

The bundle must also inherit machine-registry completeness
self-describing-family requirement law.

The admitted requirement that root mapping families stay self-describing may
not be silently redeclared, weakened, or guessed inside the bundle.

If the admitted source does not disclose that self-describing-family
requirement law, the machine world must fail-close rather than locally
reconstructing self-describing-family legality.

Local redeclaration of self-describing-family requirement governance must
remain forbidden inside the bundle.

The bundle must also inherit machine-registry completeness family-surface
binding law.

If the admitted source does not disclose that family-surface binding law, the
machine world must fail-close rather than locally reconstructing
descriptor-family binding legality.

Local redeclaration of family-surface binding governance must remain
forbidden inside the bundle.

If machine-registry completeness explicitly declares a cross-family
descriptor-stem binding, the bundle must not locally override or suppress that
binding.

The bundle must also inherit machine-registry completeness repo-relative
descriptor path-pattern law.

It must inherit those repo-relative path patterns rather than locally
redeclaring, loosening, or guessing descriptor-stem capture from naming
convention.

If the admitted source does not disclose those patterns, the machine world
must fail-close rather than locally reconstructing descriptor-stem capture
law.

The bundle must also inherit machine-registry completeness repo-relative
descriptor discipline law.

Repo-root-relative scope, parent-escape rejection, role-typed path law, and
cross-role surface-stem coherence may not be silently redeclared or weakened
inside the bundle.

Local redeclaration of repo-relative discipline governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that repo-relative discipline, the
machine world must fail-close rather than locally reconstructing descriptor
path legality.

The bundle must also inherit machine-registry completeness current/version
naming law.

Root family prefix, current-entry suffix, active-version regex, and the
requirement that admitted mapping families remain current/version paired may
not be silently redeclared or weakened inside the bundle.

Local redeclaration of current/version naming governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that naming law, the machine world
must fail-close rather than locally reconstructing current/version mediation.

The bundle must also inherit machine-registry completeness registry-child
admission law.

The canonical registry directory, the admitted registry-current entry, and
the registered child set that legalizes component current/version files may
not be silently redeclared or weakened inside the bundle.

Local redeclaration of registry-child admission governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that registry-child admission law,
the machine world must fail-close rather than locally reconstructing
component admission.

Bundle component descriptors must also remain current-entry mediated.

The bundle must point to admitted component current rows and resolve active
version truth through those rows, not pin directly to version files.

If a component current row is absent or invalid, the machine world must
fail-close rather than bypassing current mediation.

Bundle component legality must also remain validator-live.

Each bound component validator must execute through its disclosed validator
surface and emit `PASS_REQUIRED` through its disclosed status key.

Descriptor concordance and file presence are not enough if that validator
fails execution or emits a weaker verdict.

Bundle component validator execution-failure handling must also stay
fail-closed.

If a bound validator cannot execute, exits nonzero, emits invalid machine
output, or omits its disclosed status key, runtime may not synthesize a
passing verdict from surrounding bundle metadata.

Bundle component validators must also keep returncode-observation contract
explicit.

The admitted validator returncode-observation contract is nonzero returncode
observed without host exception overlay.

Runtime may not let a host-language subprocess helper raise on nonzero exit,
bypass the governed execution-failure policy, or convert host exception
convenience into validator truth.

Bundle component validators must also remain machine-readable.

Runtime consumes them through structured machine output carrying the disclosed
status key, not by scraping prose, logs, or incidental terminal text.

Bundle component validators must also keep their invocation contract explicit.

Bundle legality invokes them as `python3 <validator_script> --repo-root
<repo_root> --json-only`.

Runtime may not swap interpreter, omit repo-root binding, or omit compact
machine-output mode.

Bundle component validators must also keep output-channel contract explicit.

The verdict-bearing machine-output channel is stdout only.

stderr diagnostics do not become an alternate status-bearing channel and may
not replace missing stdout truth.

Bundle component validators must also keep stderr-isolation contract explicit.

The admitted stderr channel remains separately captured from verdict-bearing
stdout.

Runtime may not merge stderr into stdout or treat a mixed stream as admitted
validator truth.

Bundle component validators must also keep stdio text-decoding contract
explicit.

The admitted validator stdio text-decoding contract is utf-8 strict text
decode with no locale overlay.

Runtime may not let ambient locale choose the decoder, substitute an
alternate codec or replacement policy, or treat locale-shaped text coercion
as admitted validator truth.

Bundle component validators must also keep stdout-normalization contract
explicit.

The admitted validator stdout-normalization contract is outer-whitespace trim
only before JSON decode.

Runtime may not line-scrape, select a preferred line, trim inner content, or
reconstruct JSON from mixed stdout.

Bundle component validators must also keep stdout-presence contract explicit.

The admitted validator stdout-presence contract is nonempty after
outer-whitespace trim.

Runtime may not treat empty or whitespace-only stdout as implicit success, an
invented empty object, or an advisory no-op verdict surface.

Bundle component validators must also keep stdout-framing contract explicit.

The verdict-bearing machine output occupies whole stdout as a single JSON
object.

Runtime may not line-scrape, trailer-strip, or extract a JSON fragment from
mixed stdout preamble, trailer, or incidental shell text.

Bundle component validators must also keep status-key resolution contract
explicit.

The disclosed status key is resolved only as a direct top-level member of the
verdict-bearing JSON object.

Runtime may not search nested objects, alias keys, pointer paths, or other
local convenience structures to recover missing status truth.

Bundle component validators must also keep status-literal contract explicit.

The disclosed status value is admitted only as the exact canonical string
literal.

Runtime may not trim whitespace, fold case, coerce non-string values, or map
alternate literals into admitted status truth.

Bundle component validators must also keep execution-input contract explicit.

The admitted validator execution input is devnull-backed noninteractive stdin.

Runtime may not let bound validators inherit ambient stdin, wait for operator
keystrokes, or convert interactive prompt dialogue into validator truth.

Bundle component validators must also keep verdict-admission timing contract
explicit.

The admitted validator verdict is consumed only after completed process exit.

Runtime may not stream partial stdout into verdict truth, parse pre-exit
fragments, or treat background-launched validators as already admitted.

Bundle component validators must also keep execution-timeout contract
explicit.

The admitted validator execution-timeout contract is no local timeout overlay.

Runtime may not inject a bundle-local deadline, kill-after policy, or timeout
overlay and then treat timeout-shaped termination as admitted validator truth.

Bundle component validators must also keep working-directory contract explicit.

The admitted validator execution working directory is repo_root.

Runtime may not substitute arbitrary cwd or ambient shell location for that
governed execution context.

Bundle component validators must also keep execution-environment contract
explicit.

The admitted validator execution environment is the inherited parent-process
environment with no local overlay.

Runtime may not inject a local env map, scrub inherited variables, or
substitute a shadow environment overlay for that governed execution context.

Bundle component validators must also keep execution-transport contract
explicit.

The admitted transport is local direct subprocess vector execution.

Runtime may not substitute shell mediation, remote hop, or other ambient
transport for that governed execution path.

Bundle component validators must also keep contract-drift execution policy
explicit.

The admitted validator policy is execute under canonical contract and
fail-closed on drift.

Runtime may not obey a drifted disclosed contract row during validator
execution or treat drift-shaped execution as admitted validator truth.

Bundle component validators must also keep contract-surface projection policy
explicit.

The admitted validator surface split is disclosed bundle summary plus
effective component execution rows.

Runtime may not hide disclosed drift by rewriting summary to canonical values
or project drifted declared rows as applied execution truth.

Bundle component validators must also keep observation-continuity policy
explicit.

The admitted runtime policy is continue bound component observation under
canonical surface before final fail-close.

Runtime may not use bundle drift as a reason to suppress otherwise bindable
component observation before final verdict.

Bundle component status-row coverage policy must also stay explicit.

The admitted runtime policy is every bound component emits one status row
before final status.

Runtime may not finalize on partial component-row coverage when the bound
component set is already known.

Bundle violation-projection policy must also stay explicit.

The admitted runtime policy is all structure, bundle, and anchor violations
are projected into stale reasons before final status.

Runtime may not keep violation rows private while presenting a final verdict
surface that withholds their stale-reason projection.

Bundle final-status derivation policy must also stay explicit.

The admitted runtime policy is `PASS_REQUIRED` if and only if stale reasons
remain empty after violation projection; otherwise final status is
`FAIL_REQUIRED`.

Runtime may not derive a clean final verdict from pre-projection
convenience, raw green component counts, or any alternate local verdict
path.

Bundle error-code precedence policy must also stay explicit.

The admitted runtime policy is registry-class failure preempts
structure-class failure, structure-class failure preempts bundle-class
failure, and pass-state emits empty error code.

Runtime may not derive failure code from first local convenience, last
mutation side effect, or any alternate precedence order.

Bundle failure-classification policy must also stay explicit.

The admitted runtime policy is registry class derives from direct stale
reasons present before violation projection, structure class derives from
structure violations, bundle class derives from bundle and anchor
violations, and otherwise failure class is pass.

Runtime may not invent an anchor-only failure class, bypass direct stale
reasons, or classify failure from local convenience surfaces.

Bundle registry-class admission policy must also stay explicit.

The admitted runtime policy is only direct stale reasons already present
before violation projection may admit registry failure class.

Projected structure, bundle, and anchor stale reasons must not
retroactively upgrade failure class to registry.

Bundle registry direct-stale-reason origin policy must also stay explicit.

The admitted runtime origins are alias error, document invalidity,
canonical contract-row invalidity, and required-surface absence, all
before violation projection.

Bundle registry direct-stale-reason alias origin policy must also stay
explicit.

The admitted runtime alias direct stale reasons are rows containing the
`_alias_error:` marker before document, required-surface, and
contract-row classification.

Bundle registry direct-stale-reason document origin policy must also
stay explicit.

The admitted runtime document direct stale reasons are rows ending with
`_empty_or_invalid` after alias exclusion and before required-surface
and contract-row classification.

Bundle registry direct-stale-reason required-surface origin policy must
also stay explicit.

The admitted runtime required-surface direct stale reasons are
required-component-descriptor-fields missing, surface-missing rows,
anchor-checks missing, and components missing before violation
projection.

Bundle registry direct-stale-reason contract-row origin policy must also
stay explicit.

The admitted runtime contract-row direct stale reasons are
root-corpus-law-bundle prefixed rows and
root-machine-registry-completeness prefixed rows that remain after
alias, document, and required-surface classification.

Bundle registry direct-stale-reason source policy must also stay
explicit.

The admitted runtime source is local stale reasons already present before
violation projection.

Projected structure, bundle, and anchor stale reasons do not become
substitute direct stale-reason source.

Bundle registry direct-stale-reason partition policy must also stay
explicit.

Each local stale reason present before violation projection must classify
exactly once as alias, document, contract-row, required-surface, or
unknown ontology drift.

Bundle registry direct-stale-reason origin-classifier precedence policy
must also stay explicit.

Alias runtime classification preempts document classification, document
classification preempts required-surface classification, required-surface
classification preempts contract-row classification, and otherwise
runtime origin remains unknown.

Bundle registry direct-stale-reason unclassified policy must also stay
explicit.

The admitted runtime policy is fail-closed on unclassified direct
stale-reason origin.

Runtime must fail-close on unclassified direct stale-reason origin rather
than silently expanding registry ontology.

Bundle component-validator observation-reason policy must also stay
explicit.

The admitted runtime observation reasons are parse/status failure,
nonzero returncode after admitted parse/status resolution, and non-pass
component status, all before bundle-violation projection.

Bundle component-validator parse/status origin policy must also stay
explicit.

The admitted runtime parse/status reasons are validator-output missing,
validator-output invalid-json, validator-output not-json-object,
validator-status-key missing, and validator-status-literal not-string,
all before nonzero returncode, non-pass component status, explicit
non-execution exclusion, and bundle-violation projection.

Bundle component-validator nonzero-returncode origin policy must also
stay explicit.

The admitted runtime nonzero-returncode reason is component-validator
nonzero returncode only, after admitted parse/status resolution and
before non-pass component status, explicit non-execution exclusion, and
bundle-violation projection.

Bundle component-validator non-pass-status origin policy must also stay
explicit.

The admitted runtime non-pass-status reason is component-status
not-pass-required only, after admitted parse/status and nonzero
returncode resolution and before explicit non-execution exclusion and
bundle-violation projection.

Bundle component-validator prefixed ontology-drift origin policy must
also stay explicit.

The admitted runtime prefixed ontology-drift rows are validator-output,
validator-status, component-status, and component-validator prefixed
rows only, after admitted parse/status, nonzero returncode,
non-pass-status, and exclusion-origin resolution and before
not-applicable classification.

Bundle component-validator observation-reason classifier precedence
policy must also stay explicit.

Parse/status runtime classification preempts nonzero returncode
classification, nonzero returncode classification preempts non-pass
component-status classification, non-pass component-status
classification preempts explicit non-execution row exclusion, explicit
non-execution row exclusion preempts prefixed observation-family
ontology drift, and otherwise runtime classification remains
not-applicable.

Bundle component-validator observation-reason exclusion-origin policy
must also stay explicit.

The admitted excluded runtime non-observation rows are
component-validator missing and component-status-row coverage
incomplete, both before bundle-violation projection.

Runtime observation reasons and prefixed observation-family ontology
drift must not be silently re-bucketed as excluded non-observation
rows.

Non-execution bundle rows must remain outside component-validator
observation ontology rather than being silently re-bucketed as runtime
observation reasons.

Bundle component-validator observation-reason source policy must also
stay explicit.

The admitted runtime observation source is bundle-violation rows only,
before violation projection.

Direct stale reasons, structure violations, anchor violations, and
projected stale-reason strings do not become substitute runtime
observation source.

Bundle component-validator observation-reason partition policy must also
stay explicit.

Each bundle-violation row must classify exactly once as admitted runtime
observation reason, excluded non-observation row, or unknown ontology
drift, all before violation projection.

Bundle component-validator observation-reason unclassified policy must
also stay explicit.

The admitted runtime policy is fail-closed on unclassified
component-validator observation reason.

Runtime must fail-close on unclassified component-validator observation
reason rather than silently expanding bundle observation ontology.

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
