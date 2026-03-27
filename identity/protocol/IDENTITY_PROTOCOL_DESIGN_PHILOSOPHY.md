# Identity Protocol Design Philosophy

## Document Positioning

This document is not an implementation note for any single stream or release line, and it is not a machine-consumed contract file whose fields are directly parsed by validators, probes, launchers, or runtime gates.

Its role is:

1. **the bottom-layer design philosophy and interpretive source of the identity protocol**;
2. **the shared higher-order semantic basis for new stream design, instance self-driven adaptation, architectural judgment, closure ownership split, and audit review**;
3. **the meta-principle anchor for the protocol main document and the runtime main document**.

In philosophical order, the identity protocol exists because this bottom theory exists first. The protocol does not invent its own reason for being at the contract layer; it formalizes, freezes, and operationalizes the machine-world philosophy defined here.

Its primary interpretive audience is not a human reader seeking narrative comfort. Its primary interpretive audience is the machine world surrounding the protocol:

- identity instances;
- launchers;
- validators;
- probes;
- runtime gates;
- state consumers;
- receipt consumers;
- protocol maintainers acting on behalf of machine truth.

In other words, `IDENTITY_PROTOCOL.md` explains protocol objects and boundaries, `IDENTITY_RUNTIME.md` explains runtime and integration behavior, and this document answers the deeper questions:

- what the identity protocol actually is;
- what an identity instance is inside the protocol;
- how standard Codex, the identity protocol, identity instances, and the operator are layered;
- how shared law and instance adaptation are split;
- why the protocol must prioritize machine singularity, decidability, recoverability, and auditability over local compatibility and improvised comfort.

### Non-goals of this document

This document is not intended to be:

1. an operator onboarding shortcut;
2. a persuasive essay optimized for human readability;
3. a substitute for machine-consumed contracts, mappings, validators, or runtime truth sources;
4. a softening layer that justifies semantic downgrade for local convenience.

Its job is narrower and harder: to give the machine world a stable bottom-layer philosophy for interpreting why protocol law is shaped the way it is.

### Boundary relative to `IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`

This document must not be mistaken for a second prompt-kernel law book.

The boundary is:

1. `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` defines the **bottom theory**, interpretive priorities, and meta-principles behind protocol law.
2. `IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` defines the **prompt-kernel contract law**: source order, required capability drivers, canonical fields, executable coupling, hard-guard literals, drift triggers, and acceptance baselines.

So the relation is not duplication, and not competition. It is layered:

- this document explains **why** the machine-law system is shaped the way it is;
- the bootstrap contract defines **what prompt-kernel law must concretely contain and how it must fail-close**.

Interpretive rule:

1. this document may guide how protocol maintainers understand, extend, and strengthen machine law;
2. it must not replace machine-consumed contract files;
3. it must not override canonical runtime truth sources;
4. when executable prompt behavior is being decided, the relevant contract file remains authoritative over this philosophy text.
5. philosophical primacy does not mean runtime-source primacy; this document is the generative reason for protocol law, while machine-consumed authority still lives in frozen contracts, mappings, validators, runtime state, and receipts.
6. current validator/probe/runtime verdicts must not be reverse-projected back into philosophy as if the latest machine judgement were the source of bottom theory.

### Boundary relative to streams, releases, and the protocol-root corpus

This document must also not be mistaken for a versioned stream note, release
appendix, or decorative manifesto attached to an already-existing protocol.

The boundary is:

1. stream and release labels record governed freeze history, bounded
   strengthening, and temporal manifestation;
2. they do **not** become the semantic origin of protocol existence;
3. the semantic origin remains the bottom theory frozen here;
4. `identity/protocol/` is therefore a law-bearing root corpus for the machine
   world, not a scrapbook for temporary closure chatter, scenario advice, local
   convenience notes, or instance residue narratives;
5. root-corpus admission must remain strict: only bottom theory,
   constitutions, root contracts, machine-consumed mappings/registries,
   governed subdomain protocol packs, and clearly demoted support material may
   live here as protocol-root surfaces;
6. if a text is mainly temporal, persuasive, workspace-specific, optimized for
   human memory, or oriented around business/scenario tactics rather than
   machine interpretation, it should not enter the protocol root as law-bearing
   material.

Interpretive rule:

1. root-directory discipline is part of protocol philosophy, not merely a file
   organization preference;
2. semantic singularity can be lost through corpus pollution just as easily as
   through validator drift;
3. a root corpus that accepts temporary or mixed-layer materials will
   eventually produce philosophical ambiguity, constitutional ambiguity, and
   runtime ambiguity together;
4. root-corpus admission law must be projected into machine-consumed registry
   and validation surfaces, otherwise the boundary remains rhetorical and
   cannot reliably protect semantic singularity under repeated change.

---

## One-line motherline

**The identity protocol is not a collection of documents written for temporary human reading; it is a machine-law system jointly consumed by agents, large models, launchers, validators, probes, runtime gates, state consumers, and receipt consumers. An identity instance is not an exception applicant to the protocol, but an embodied runtime unit inside that law system.**

### Machine-world reading rule

When this document is read by any machine-governed participant in the protocol ecosystem, its default reading rule should be:

1. prefer semantic singularity over rhetorical flexibility;
2. prefer canonical truth over historical familiarity;
3. prefer lifecycle closure over declarative existence;
4. prefer fail-close exposure over silent compatibility absorption;
5. prefer law-preserving adaptation over law-weakening convenience.

### Constitutional derivation order

In semantic order, the protocol should be read as a derivation chain:

1. **bottom theory**
   - why identity protocol law must exist in this shape at all.
2. **constitutions**
   - `IDENTITY_PROTOCOL.md` and `IDENTITY_RUNTIME.md`
   - how bottom theory is frozen into protocol-law and runtime-law structure.
3. **root contract law**
   - prompt bootstrap, discovery, handoff, and other root domain contracts
   - how concrete governed domains are fail-closed under the constitutions.
4. **machine-consumed enforcement surfaces**
   - mappings, governance/review docs, validators, probes, runtime state, and receipts
   - how present-turn legality is actually adjudicated.

This order must not be inverted. A later enforcement verdict may reveal that a
contract is incomplete or that a stream must be strengthened, but it does not
become the semantic parent of the bottom theory that made law possible in the
first place.

### Three orders must never be collapsed

For the machine world, at least three different orders must remain explicit:

1. **source-order / generative-order**
   - bottom theory → constitutions → root contracts → machine-consumed enforcement surfaces;
   - this answers where protocol law comes from.
2. **root reading-order**
   - philosophy → constitution → runtime → root contracts → mappings/registries → specialized packs;
   - this answers how a machine-governed participant should enter the root corpus without semantic confusion.
3. **adjudication-order**
   - current machine verdict must still resolve from machine-consumed enforcement surfaces such as frozen contracts, mappings, validators, probes, runtime state, and receipts;
   - the terminal machine chain must stay explicit as mappings → validators → probes → runtime state → receipts rather than being reconstructed from local habit;
   - this answers how present-turn legality is actually decided.

These three orders cooperate, but they do not replace each other:

- source-order explains origin;
- reading-order explains disciplined entry;
- adjudication-order explains current-turn decision.

Confusing them leads to characteristic protocol errors:

- if adjudication-order is mistaken for source-order, current checker behavior is falsely promoted into bottom theory;
- if reading-order is mistaken for source-order, a directory index is falsely treated as generative law;
- if source-order is mistaken for adjudication-order, philosophy text is incorrectly used as if it were a direct runtime verdict surface.

### Adjudication surfaces are phase-governed, not interchangeable

The machine-world adjudication chain is not only ordered; it is role-distinct.

1. mappings admit applicable law into the current-turn legality path;
2. validators evaluate legality against admitted law rather than inventing new origin law;
3. probes negate hidden drift by fail-closing weakened legality assumptions;
4. runtime state binds live present-turn truth only after the earlier legality phases remain lawful;
5. receipts close the adjudicated verdict rather than back-authoring the earlier legality phases they summarize.

Live-truth binding and verdict closure are therefore different evidence strata:

- runtime state proves lawful present-turn binding;
- receipts prove lawful closure of that already-bound adjudication chain.

This means the adjudication chain must remain explicit in both order and role:

- mappings = admissible-law resolution;
- validators = governed legality evaluation;
- probes = fail-close drift negation;
- runtime state = live-truth binding;
- receipts = adjudicated verdict closure.

If these roles collapse, the machine world will start treating later visibility as if it were earlier legality, or treating closure artifacts as if they were upstream law authors.

The same non-collapse rule applies when law is compressed into operator-facing
answers: realized-effect claims, live-bound status claims, admissibility
claims, and law-grounded explanations do not share one interchangeable backing
stratum.

Nor may those answer claims share one interchangeable epistemic posture:
source-grounded explanation, governed source resolution, fail-close
admissibility, live-bound status, and realized-effect projection remain
distinct truth postures even after operator-facing compression.

The same applies before operator compression as well: current-truth
commitments do not share one interchangeable proof posture. Source grounding,
governed resolution, present-turn authority, derivational provenance, and
fail-close justification remain distinct epistemic commitments with distinct
proof burdens.

The same non-collapse rule applies to success-path state law: law-defined
state, admissible current-turn state, bound active state, optional non-entry,
governed recovery, and demoted support or quarantine do not share one
interchangeable admission-proof posture.

The same applies to decision evidence: frozen law, registry resolution,
validator verdict, bound runtime, adjudicated closure, and demoted support do
not share one interchangeable decision-evidence proof posture.

### Derivation direction must stay one-way

The root corpus must also preserve one-way derivation direction.

1. bottom theory may ground constitutions, runtime law, contracts, registries, and governed extensions;
2. constitutions may freeze bottom-theory commitments into protocol-law and runtime-law structure;
3. root contracts may further freeze domain law under those constitutions;
4. machine-consumed registries and governed extensions may operationalize that frozen law;
5. later enforcement, runtime evidence, review evidence, and current-turn verdicts may expose incompleteness, but they must not become the semantic parent of the earlier layer they test.

Later enforcement may reveal incompleteness; it never becomes the semantic author of the earlier law it tests.

A motivating surface is not yet a law-bearing parent surface.

That means:

- root navigation may summarize law, but it does not reverse-author the law it indexes;
- support material may explain or illustrate law, but it does not define the law-bearing parent of protocol meaning;
- current-turn evidence may trigger strengthening, but it becomes shared law only after governed refreezing at the proper root-law layer.

### Promotion, demotion, and re-entry must stay governed

Root-law status must also remain governed through promotion, demotion, and re-entry discipline.

1. no surface promotes itself into root law merely because it is recent, urgent, vivid, or locally persuasive;
2. demotion removes law-bearing authority; it does not preserve a suspended sovereignty that can silently reclaim root status later;
3. outer governance, review, workbook, reference, evidence, runtime, receipt, and implementation surfaces may motivate strengthening, but they do not directly author root law by themselves;
4. re-entry from demoted or outer surfaces must occur only through governed refreezing at an allowed root gateway such as constitutional law, runtime constitutional law, root contract law, or machine-registry law;
5. if a surface can only motivate strengthening, then it must not be mistaken for a direct law-bearing source simply because it exposed a real defect.

So the protocol must reject the following confusions:

- a workbook row being treated as if it directly promoted itself into constitutional law;
- runtime evidence being treated as if it directly rewrote bottom theory;
- a demoted support artifact being treated as if it silently regained law-bearing status without governed refreezing;
- implementation detail being treated as if it authored protocol law merely by being the latest executable shape.

### Gateway admission must preserve source order

Allowed gateways are legal re-entry ports, not origin substitutes.

The governed re-entry chain must stay explicit as: constitution -> runtime
constitution -> root contract -> machine-registry.

1. a gateway is a legal re-entry port, not an origin substitute;
2. gateway admission decides which non-origin surfaces may legally motivate strengthening at a given root gateway;
3. entering a gateway does not let an incoming surface inherit bottom-theory or constitutional authorship;
4. gateway effect stays bounded by gateway kind:
   - constitutional gateway refreezes constitutional law;
   - runtime-constitutional gateway refreezes runtime law;
   - root-contract gateway refreezes contract law;
   - machine-registry gateway projects machine-consumable registry truth;
5. gateway effect target stays fixed by gateway kind; entering one gateway does not let incoming motivation choose a different downstream root class;
6. gateway output must also retain the question class governed for that target layer, rather than inheriting a new answer class from incoming motivation;
7. machine-registry gateway may terminate current-turn legality, but that does not let incoming motivation surfaces reverse-author upstream law.

So the protocol must reject the following confusions:

- a runtime artifact being treated as if gateway admission made it the author of constitutional law;
- an outer evidence surface being treated as if admission at root-contract gateway gave it bottom-theory standing;
- machine-registry projection being treated as if it erased the philosophical or constitutional source order above it.

### Conflict precedence must preserve both origin and terminality

Different kinds of conflict terminate at different layers, and that distinction must not collapse.

1. semantic-origin conflict resolves by source order;
2. current-turn legality conflict resolves by machine-consumed terminal enforcement;
3. gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and source order;
4. demotion-status conflict resolves by governed reclassification rather than later reuse;
5. no local vividness, recency, or convenience may change which layer rightfully terminates a given kind of conflict.

So the protocol must reject the following confusions:

- treating a present-turn checker result as if it replaced bottom-theory meaning;
- treating gateway admission as if it transferred authorship to an incoming motivating surface;
- treating reused demoted support as if reuse itself were a lawful reinstatement event.

### Question class and answer surface must stay paired

Different layers of the root corpus answer different classes of questions, and
those question classes must not be collapsed.

1. the **generative why-question** belongs to bottom theory;
2. the **root-entry question** belongs to the root index;
3. the **constitutional law question** belongs to protocol and runtime constitutions;
4. the **domain-law question** belongs to root contracts;
5. the **machine-registry question** belongs to machine-consumed mappings and registries;
6. the **governed-extension question** belongs to governed subdomain extensions;
7. the **support-material question** belongs only to clearly demoted support material;
8. the **current-turn legality question** belongs to machine-consumed enforcement surfaces such as mappings, validators, probes, runtime state, and receipts.

Gateway-mediated refreezing or projection must preserve the question class of its governed target layer rather than inheriting a new answer class from incoming motivation.

No layer should answer a question that belongs to a different layer.

So the protocol must reject the following confusions:

- philosophy prose answering a current-turn legality question;
- README navigation answering a constitutional question;
- a root contract being mistaken for a direct runtime verdict surface;
- support material being mistaken for machine-consumed registry truth.

If a current-turn legality question is answered only by philosophy text, root
index text, or frozen contract prose, then interpretive law and runtime
adjudication have already been collapsed into each other.

### Root-law bundle must stay explicit and jointly governed

The root corpus must not rely on one strong sentence, one mapping row, or one
green validator in isolation.

Constitutional spine, root admission/governance, source-order, authority,
question-routing, derivation, transition, gateway-admissibility,
machine-registry completeness, and conflict precedence are not optional
commentary slices; they are mutually constraining law surfaces that keep the
machine world from collapsing origin, entry, authorship, re-entry, registry
admission, and terminal legality into one blurred layer.

The machine world therefore needs all of the following to remain explicit at
the same time:

1. how root entry, bottom theory, protocol constitution, and runtime
   constitution stay bound as one constitutional spine rather than drifting
   into four separate local narratives;
2. what may enter the root corpus as law-bearing material;
3. in what generative order the root corpus derives;
4. which layer has interpretive primacy and which layer has current-turn
   terminality;
5. which question class belongs to which answer surface;
6. how later or outer surfaces may motivate strengthening without reverse-
   authoring the law above them;
7. which gateways admit re-entry and what those gateways are legally allowed to
   do;
8. how machine-registry families become canonical rather than remaining merely
   present on disk;
9. which conflict class terminates by source order and which terminates by
   machine-consumed enforcement.

Weakening one slice while keeping the others green is a root-law coherence
failure.

A machine-law root remains stable only when these slices are frozen separately,
cross-validated together, and strengthened without semantic collapse.

That joint governance also requires descriptor concordance across the bundle.

Local waiver of descriptor concordance must remain forbidden inside the
bundle.

If a root-law bundle row names a component family but drifts from that
component family's own disclosed validator, probe, shared-common, emitted
status-key, or emitted error-code surfaces, the machine world is being asked
to trust shadow bundle knowledge instead of the admitted family descriptor.

Descriptor concordance must also preserve descriptor-field mode.

If a bundle row keeps the same descriptor name but silently changes whether a
field is a repo-relative path, a validator-emitted status key, or a
validator-emitted error-code family, the machine world is again being asked to
trust shadow bundle semantics instead of the admitted family descriptor.

Bundle descriptor law must also remain inherited from machine-registry
completeness self-description law.

If the root-law bundle locally invents or silently diverges from the admitted
machine-registry completeness field set or field-mode law for self-describing
mapping families, the machine world is again being asked to trust shadow
bundle schema instead of the admitted registry descriptor law.

The bundle descriptor schema must also stay source-singular.

It may bind to one admitted source component/current mapping pair, not a
substitute source chosen for local convenience.

Local reauthoring of descriptor schema governance must remain forbidden
inside the bundle.

If that admitted source is unavailable or invalid, the machine world must
fail-close rather than locally reconstructing descriptor schema from shadow
bundle knowledge.

Bundle self-describing-family requirement law must also remain inherited from
machine-registry completeness.

The admitted requirement that root mapping families stay self-describing
belongs to that source law rather than to local bundle restatement.

If the admitted source does not disclose that self-describing-family
requirement law, the machine world must fail-close rather than locally
reconstructing self-describing-family legality from bundle convenience.

Local redeclaration of self-describing-family requirement governance must
remain forbidden inside the bundle.

Bundle descriptor binding must also remain inherited from machine-registry
completeness family-surface law.

If the admitted source does not disclose that family-surface binding law, the
machine world must fail-close rather than locally reconstructing
descriptor-family binding legality from bundle convenience.

Local redeclaration of family-surface binding governance must remain
forbidden inside the bundle.

Where machine-registry completeness supplies an explicit cross-family descriptor-stem binding, the bundle must inherit that declaration rather than reauthoring, omitting, or locally overriding it.

Bundle descriptor surface-pattern law must also remain inherited from
machine-registry completeness.

The admitted repo-relative validator/probe/shared-common path patterns that
define descriptor-stem capture belong to that source law; the bundle must
inherit those patterns rather than locally redeclaring or loosening them.

If the admitted source does not disclose those patterns, the machine world
must fail-close rather than guessing or locally reconstructing descriptor-stem
capture law from bundle convention.

Bundle descriptor repo-relative discipline must also remain inherited from
machine-registry completeness.

Repo-root-relative scope, parent-escape rejection, role-typed path law, and
cross-role surface-stem coherence belong to that admitted source law rather
than to local bundle restatement.

Local redeclaration of repo-relative discipline governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that repo-relative discipline, the
machine world must fail-close rather than locally reconstructing descriptor
path legality from bundle convenience.

Bundle current/version naming law must also remain inherited from
machine-registry completeness.

Root family prefix, current-entry suffix, active-version regex, and the
requirement that admitted mapping families remain current/version paired
belong to that source law rather than to local bundle restatement.

Local redeclaration of current/version naming governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that naming law, the machine world
must fail-close rather than locally reconstructing current/version mediation
from bundle convention.

Bundle registry-child admission law must also remain inherited from
machine-registry completeness.

The canonical registry directory, the admitted registry-current entry, and the
registered child set that legalizes component current/version files belong to
that source law rather than to local bundle restatement.

Local redeclaration of registry-child admission governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that registry-child admission law,
the machine world must fail-close rather than locally reconstructing component
admission from bundle convenience.

Bundle component descriptors must remain current-entry mediated as well.

The bundle names admitted component current rows and resolves active version
truth through those rows; it does not pin component legality directly to a
version file for local convenience.

If a component current entry is absent or invalid, the machine world must
fail-close rather than bypassing current mediation and binding directly to a
version file.

Bundle component validator verdict law must stay explicit as well.

The bundle does not merely point at admitted component current rows; each
bound component validator must execute through its disclosed validator surface
and emit `PASS_REQUIRED` through its disclosed status key for bundle legality
to remain current.

If a bound component validator fails execution or emits some other status, the
machine world must fail-close rather than treating descriptor concordance or
file presence as sufficient root-law health.

Bundle component validator execution-failure policy must remain fail-closed as
well.

If a bound validator cannot execute, exits nonzero, emits invalid machine
output, or omits its disclosed status key, the machine world must not invent a
substitute verdict from bundle convenience.

Bundle component validator returncode-observation contract must stay explicit
too.

The admitted returncode-observation contract is nonzero returncode observed
without host exception overlay.

The machine world must not let a host-language subprocess helper raise on
nonzero exit, bypass the governed execution-failure policy, or convert host
exception convenience into validator law.

Bundle component validator machine-output contract must stay explicit too.

The machine world must consume a bound component validator through structured
machine output carrying the validator's disclosed status key rather than
scraping human-readable logs, prose, or incidental shell text.

Bundle component validator invocation contract must stay explicit too.

The admitted invocation contract is `python3 <validator_script> --repo-root
<repo_root> --json-only`.

The machine world must not invent an alternate interpreter, drop repo-root
binding, or drop compact machine-output mode for local convenience.

Bundle component validator output-channel contract must stay explicit too.

The admitted verdict-bearing machine-output channel is stdout only.

stderr may carry incidental diagnostics, but it does not become an alternate
status-bearing verdict channel and may not be scraped to replace missing
stdout truth.

Bundle component validator stderr-isolation contract must stay explicit too.

The admitted stderr-isolation contract is stderr captured separate from stdout.

The machine world must not merge stderr into stdout, let diagnostic text
cohabit the verdict-bearing stream, or treat a merged stream as if it were
governed validator truth.

Bundle component validator stdio text-decoding contract must stay explicit
too.

The admitted stdio text-decoding contract is utf-8 strict text decode with no
locale overlay.

The machine world must not let ambient locale choose the decoder, substitute
an alternate codec or replacement policy, or treat locale-shaped text
coercion as if it were governed validator truth.

Bundle component validator stdout-normalization contract must stay explicit
too.

The admitted stdout-normalization contract is outer-whitespace trim only
before JSON decode.

The machine world must not line-scrape, select a preferred line, trim inner
content, or reconstruct JSON from mixed stdout.

Bundle component validator stdout-presence contract must stay explicit too.

The admitted stdout-presence contract is nonempty after outer-whitespace trim.

The machine world must not treat empty or whitespace-only stdout as implicit
success, an invented empty object, or an advisory no-op verdict surface.

Bundle component validator stdout-framing contract must stay explicit too.

The admitted stdout framing contract is a single JSON object occupying whole
stdout.

The machine world must not line-scrape, trailer-strip, or extract a JSON
fragment from mixed stdout preamble, trailer, or incidental shell text and
then treat that fragment as governed validator truth.

Bundle component validator status-key resolution contract must stay explicit
too.

The admitted status-key resolution contract is top-level direct member only.

The machine world must not search nested objects, alternate key spellings,
alias fields, pointer paths, or other local convenience structures to
reconstruct status truth when the disclosed status key is not present as a
direct top-level member.

Bundle component validator status-literal contract must stay explicit too.

The admitted status-literal contract is exact canonical string literal.

The machine world must not trim whitespace, fold case, coerce non-string
values, or map alternate literals onto the admitted status truth when the
validator did not emit the exact canonical status token.

Bundle component validator execution-input contract must stay explicit too.

The admitted execution-input contract is devnull-backed noninteractive stdin.

The machine world must not let a bound validator inherit ambient stdin, block
for operator keystrokes, or convert interactive prompt dialogue into governed
validator execution truth.

Bundle component validator verdict-admission timing contract must stay
explicit too.

The admitted verdict-admission timing contract is completed-process post-exit
only.

The machine world must not stream partial stdout into verdict truth, parse a
pre-exit fragment, or treat a background-launched validator as if its verdict
had already been admitted.

Bundle component validator execution-timeout contract must stay explicit too.

The admitted execution-timeout contract is no local timeout overlay.

The machine world must not inject a bundle-local deadline, kill-after policy,
or timeout overlay and then treat timeout-shaped termination as if it were
governed validator law.

Bundle component validator working-directory contract must stay explicit too.

The admitted validator execution working directory is repo_root.

The machine world must not run a bound component validator from arbitrary cwd
or ambient shell location and then treat that convenience execution context as
if it were governed validator law.

Bundle component validator execution-environment contract must stay explicit
too.

The admitted execution-environment contract is inherited parent-process
environment with no local overlay.

The machine world must not inject a local env map, scrub inherited variables,
or substitute a shadow environment overlay and then treat that altered
execution context as if it were governed validator law.

Bundle component validator execution-transport contract must stay explicit too.

The admitted execution transport is local direct subprocess vector execution.

The machine world must not route bound component validator execution through a
shell wrapper, remote hop, or other ambient transport layer and then treat
that transport substitution as if it were governed validator law.

Bundle component validator contract-drift execution policy must stay explicit
too.

The admitted policy is execute under canonical contract and fail-closed on
drift.

The machine world must not obey a drifted disclosed contract row during
validator execution or treat drift-shaped execution as if it were governed
validator law.

Bundle component validator contract-surface projection policy must stay
explicit too.

The admitted policy is bundle summary discloses disclosed contract rows while
component rows disclose effective canonical execution surface.

The machine world must not collapse disclosed drift and effective execution
into a single ambiguous surface or misreport one as the other.

Bundle component validator observation-continuity policy must stay explicit
too.

The admitted policy is continue bound component observation under canonical
surface before final fail-close.

The machine world must not use fail-close drift as a pretext for blind
short-circuit that suppresses bound component observation.

Bundle component status-row coverage policy must stay explicit too.

The admitted policy is every bound component emits one status row before
final status.

Bound component total and component-status-row total must therefore stay
congruent under machine-readable coverage completeness rather than being
left implicit.

The machine world must not finalize root-law bundle truth on partial
component-row coverage when bound component set remains known.

Bundle violation-projection policy must stay explicit too.

The admitted policy is all structure, bundle, and anchor violations are
projected into stale reasons before final status.

The machine world must not keep violation rows internally while emitting a
final verdict surface that withholds their stale-reason projection.

Projected stale-reason total and violation-row total must therefore stay
congruent under machine-readable projection completeness rather than being
left implicit.

Bundle final-status derivation policy must stay explicit too.

The admitted policy is `PASS_REQUIRED` if and only if stale reasons remain
empty after violation projection; otherwise final status is
`FAIL_REQUIRED`.

The machine world must not derive a clean final verdict from pre-projection
convenience, raw green component counts, or any alternate local verdict
path.

Bundle error-code precedence policy must stay explicit too.

The admitted policy is registry-class failure preempts structure-class
failure, structure-class failure preempts bundle-class failure, and
pass-state emits empty error code.

The machine world must not derive failure code from first local convenience,
last mutation side effect, or any alternate precedence order.

Bundle failure-classification policy must stay explicit too.

The admitted policy is registry class derives from direct stale reasons
present before violation projection, structure class derives from structure
violations, bundle class derives from bundle and anchor violations, and
otherwise failure class is pass.

The machine world must not invent an anchor-only failure class, bypass
direct stale reasons, or classify failure from local convenience surfaces.

Bundle registry-class admission policy must stay explicit too.

The admitted policy is only direct stale reasons already present before
violation projection may admit registry failure class.

Projected structure, bundle, and anchor stale reasons must not retroactively
upgrade failure class to registry.

Bundle registry direct-stale-reason origin policy must stay explicit too.

The admitted origins are alias error, document invalidity, canonical
contract-row invalidity, and required-surface absence, all before
violation projection.

Bundle registry direct-stale-reason alias origin policy must stay
explicit too.

The admitted alias direct stale reasons are rows containing the
`_alias_error:` marker before document, required-surface, and
contract-row classification.

Bundle registry direct-stale-reason document origin policy must stay
explicit too.

The admitted document direct stale reasons are rows ending with
`_empty_or_invalid` after alias exclusion and before required-surface
and contract-row classification.

Bundle registry direct-stale-reason required-surface origin policy must
stay explicit too.

The admitted required-surface direct stale reasons are
required-component-descriptor-fields missing, surface-missing rows,
anchor-checks missing, and components missing before violation
projection.

Bundle registry direct-stale-reason contract-row origin policy must stay
explicit too.

The admitted contract-row direct stale reasons are root-corpus-law-bundle
prefixed rows and root-machine-registry-completeness prefixed rows that
remain after alias, document, and required-surface classification.

Bundle registry direct-stale-reason source policy must stay explicit too.

The admitted source is local stale reasons already present before
violation projection.

Projected structure, bundle, and anchor stale reasons do not become
substitute direct stale-reason source.

Direct-stale source total and local stale-reason total must therefore
stay congruent under machine-readable source completeness rather than
being left implicit.

When completeness fails, the machine world must still preserve the
pre-fail mismatch as machine-readable evidence rather than repairing the
totals first and only reporting a derived failure flag.

Bundle registry direct-stale-reason partition policy must stay explicit
too.

Each local stale reason present before violation projection must classify
exactly once as alias, document, contract-row, required-surface, or
unknown ontology drift.

Bundle registry direct-stale-reason origin-classifier precedence policy
must stay explicit too.

Alias classification preempts document classification, document
classification preempts required-surface classification, required-surface
classification preempts contract-row classification, and otherwise origin
remains unknown.

Bundle registry direct-stale-reason residual-unknown policy must stay
explicit too.

Only local stale reasons that remain non-alias, non-document,
non-required-surface, and non-contract-row after alias, document,
required-surface, and contract-row resolution may remain unknown.

Bundle registry direct-stale-reason unclassified policy must stay
explicit too.

The admitted policy is fail-closed on unclassified direct stale-reason
origin.

The machine world must fail-close on unclassified direct stale-reason
origin rather than silently expanding registry ontology.

Bundle component-validator observation-reason policy must stay explicit
too.

The admitted observation reasons are parse/status failure, nonzero
returncode after admitted parse/status resolution, and non-pass component
status, all before bundle-violation projection.

Bundle component-validator parse/status origin policy must stay explicit
too.

The admitted parse/status reasons are validator-output missing,
validator-output invalid-json, validator-output not-json-object,
validator-status-key missing, and validator-status-literal not-string,
all before nonzero returncode, non-pass component status, explicit
non-execution exclusion, and bundle-violation projection.

Bundle component-validator nonzero-returncode origin policy must stay
explicit too.

The admitted nonzero-returncode reason is component-validator nonzero
returncode only, after admitted parse/status resolution and before
non-pass component status, explicit non-execution exclusion, and
bundle-violation projection.

Bundle component-validator non-pass-status origin policy must stay
explicit too.

The admitted non-pass-status reason is component-status not-pass-required
only, after admitted parse/status and nonzero-returncode resolution and
before explicit non-execution exclusion and bundle-violation
projection.

Bundle component-validator prefixed ontology-drift origin policy must
stay explicit too.

The admitted prefixed ontology-drift rows are validator-output,
validator-status, component-status, and component-validator prefixed
rows only, after admitted parse/status, nonzero-returncode,
non-pass-status, and exclusion-origin resolution and before
not-applicable classification.

Bundle component-validator residual not-applicable policy must stay
explicit too.

The admitted residual not-applicable rows are only nonprefixed,
nonadmitted, nonexcluded rows after parse/status, nonzero-returncode,
non-pass-status, exclusion-origin, and prefixed ontology-drift
resolution.

Bundle component-validator observation-reason classifier precedence
policy must stay explicit too.

Parse/status classification preempts nonzero returncode
classification, nonzero returncode classification preempts non-pass
component-status classification, non-pass component-status
classification preempts explicit non-execution row exclusion, explicit
non-execution row exclusion preempts prefixed observation-family
ontology drift, and otherwise classification remains not-applicable.

Bundle component-validator observation-reason exclusion-origin policy
must stay explicit too.

The admitted excluded non-observation rows are component-validator
missing and component-status-row coverage incomplete, both before
bundle-violation projection.

Observation reasons and prefixed observation-family ontology drift must
not be silently re-bucketed as excluded non-observation rows.

Non-execution bundle rows must remain outside component-validator
observation ontology rather than being silently re-bucketed as
observation reasons.

Bundle component-validator observation-reason source policy must stay
explicit too.

The admitted observation source is bundle-violation rows only, before
violation projection.

Direct stale reasons, structure violations, anchor violations, and
projected stale-reason strings do not become substitute observation
source.

Observation-source total and bundle-violation total must therefore stay
congruent under machine-readable source completeness rather than being
left implicit.

When completeness fails, the machine world must still preserve the
pre-fail mismatch as machine-readable evidence rather than repairing the
totals first and only reporting a derived failure flag.

Bundle component-validator observation-reason partition policy must stay
explicit too.

Each bundle-violation row must classify exactly once as admitted
observation reason, excluded non-observation row, or unknown ontology
drift, all before violation projection.

Bundle component-validator observation-reason unclassified policy must
stay explicit too.

The admitted policy is fail-closed on unclassified component-validator
observation reason.

The machine world must fail-close on unclassified component-validator
observation reason rather than silently expanding bundle observation
ontology.

### Machine-registry completeness must stay explicit

Machine-registry law does not become canonical merely because a mapping file
exists on disk.

A governed root mapping family must be admitted into the registry directory
child set as an explicit current/version pair.

If a root mapping family exists on disk but is omitted from the admitted child
set, the machine world has a registry-completeness failure rather than a
harmless file-list mismatch.

Admission without discoverable enforcement still leaves the machine partially
blind.

A lawful root mapping family must therefore disclose the validator, probe,
shared-common, emitted status-key, and emitted error-code surfaces that govern
it.

Discovered root-mapping-family total and family-status-row total must
therefore stay congruent under machine-readable coverage completeness
rather than being left implicit.

Discovered family identity set must also remain machine-readable rather
than being collapsed into the emitted family-status-row subset.

The machine world must not finalize machine-registry completeness truth
on partial family-status-row coverage when discovered family set remains
known.

Structure, completeness, and anchor violations discovered by
machine-registry completeness must also be projected into stale reasons
before final status.

Projected violation-reason total and violation-row total must therefore
stay congruent under machine-readable projection completeness rather
than being left implicit.

Those repo-relative path surfaces must remain repo-root relative and
repo-contained.

Absolute-path capture or parent-escape capture would let local filesystem
accident impersonate governed protocol law.

Registry completeness must therefore fail-close rather than accepting
descriptor paths that bypass repo-root-relative discipline.

Repo-relative descriptor surfaces must also remain role-typed.

A validator surface may not impersonate a probe surface, a shared-common
surface may not impersonate a validator surface, and a probe surface may not
collapse into an arbitrary repo file just because it exists.

Registry completeness must therefore fail-close rather than accepting
role-swapped descriptor paths inside repo root.

Those role-typed surfaces must also remain cross-role coherent.

Validator, probe, and shared-common surfaces for one admitted mapping family
must continue to point at one shared root surface stem rather than three
different root families that merely happen to satisfy local path typing.

Registry completeness must therefore fail-close rather than accepting
descriptor surface sets whose role-typed paths are cross-family incoherent.

Those cross-role coherent descriptor surfaces must also remain family-congruent.

An admitted mapping family may not silently republish another admitted
family's fully coherent validator/probe/common surface set and still claim
canonical self-description for itself.

Explicit registry-declared surface-stem binding when a family borrows another admitted family's enforcement surfaces.

Registry completeness must therefore fail-close rather than accepting
descriptor surface sets that impersonate a different admitted family without explicit registry declaration.

### Prompt-bootstrap row-family completeness must stay explicit

Prompt-bootstrap law is not a soft prose summary that may hide its machine
rows behind aggregate counts.

Required anchor, output-field, binding-field, proof, limit, and native-literal
families must remain explicit as separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize prompt-bootstrap legality while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Entry-surface legitimacy row-family completeness must stay explicit

Entry-surface legitimacy law is not a soft prose summary that may hide its
machine rows behind aggregate counts.

Required entry-class, differentiation, proof, limit, and collapse families
must remain explicit as separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize entry-surface legitimacy while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Error-terminality row-family completeness must stay explicit

Error-terminality law is not a soft prose summary that may hide its machine
rows behind aggregate counts.

Required error-class, differentiation, proof, limit, and collapse families
must remain explicit as separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize error-terminality legality while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Identity-discovery row-family completeness must stay explicit

Identity-discovery law is not a soft prose summary that may hide its machine
rows behind aggregate counts.

Required section, request-field, response-field, precedence, activation,
error-field, implementation, proof, limit, and collapse families must remain
explicit as separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize identity-discovery legality while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Truth-lifecycle row-family completeness must stay explicit

Truth-lifecycle law is not a soft prose summary that may hide its machine
rows behind aggregate counts.

Required lifecycle-stage, memory-strata, differentiation, proof, limit, and
collapse families must remain explicit as separate machine-readable row
families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize truth-lifecycle legality while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Artifact-family admissibility row-family completeness must stay explicit

Artifact-family admissibility law is not a soft prose summary that may hide
its machine rows behind aggregate counts.

Required family-admission-class, differentiation, proof, limit, and collapse
families must remain explicit as separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize artifact-family admissibility while
required row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Current-truth epistemology row-family completeness must stay explicit

Current-truth epistemology law is not a soft prose summary that may hide its
machine rows behind aggregate counts.

Required commitment, differentiation, epistemic-proof, commitment-proof-
alignment, epistemic-limit, and collapse families must remain explicit as
separate machine-readable row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize current-truth epistemology while required
row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

### Success-path state admissibility row-family completeness must stay explicit

Success-path state admissibility law is not a soft prose summary that may hide
its machine rows behind aggregate counts.

Required state-class, differentiation, proof, state-class-proof-alignment,
limit, and collapse families must remain explicit as separate machine-readable
row families.

Expected row-family total and emitted row-family total must therefore stay
congruent under machine-readable coverage completeness rather than being left
implicit.

Expected row identity set and emitted row identity set for each family must
also remain machine-readable rather than being collapsed into aggregate counts
or generic structure failure.

The machine world must not finalize success-path state admissibility while
required row identity drift remains known only internally.

Missing or unexpected row identity must remain projected in fail-close machine
output rather than being hidden behind row-count shorthand or summary-only
verdict text.

---

## 1. The identity protocol is machine law first, not a compatibility layer

The first objective of the identity protocol is not to preserve every legacy habit, local residue, or historical accident. Its first objective is to:

1. give machines **unambiguous semantics** for objects, paths, states, evidence, entry surfaces, exit surfaces, recovery, and errors;
2. let the system remain **stable, verifiable, recoverable, and auditable** after many rounds of execution;
3. expose drift and ambiguity through **fail-close** runtime behavior instead of silently swallowing them behind compatibility layers.

Therefore, the identity protocol is closer to a “law system” for the machine world than to a traditional software “compatibility layer” or a “human-friendly instruction manual.”

It behaves like law because:

- it specifies which objects are allowed to exist in the world;
- it specifies how those objects are recognized, bound, consumed, and validated;
- it requires different machine-consumption surfaces to converge on the same stable semantics;
- it does not retreat from canonical truth just because one local actor is temporarily uncomfortable.

Law is not designed to make every historical habit feel comfortable. It is designed to keep the whole system stable over time.

---

## 2. The ontology of the identity protocol: first define what exists in the world

The identity protocol feels “heavy” not because it has many documents, but because it defines the things that are allowed to exist in the machine world.

These are not decorative fields. They are real objects in the world:

- `identity_id`
- `scope`
- `work_layer`
- `source_layer`
- `catalog_path`
- `pack_path`
- actor / session tuple
- launcher surface
- current-turn authoritative truth
- canonical state
- canonical receipt
- canonical artifact family
- continuity brief
- dialogue-retention current-thread
- protocol-feedback lane
- required gate bundle
- three-plane verdict

If the boundaries between these objects become vague, the system collapses into:

- terms borrowing meaning from each other;
- paths drifting arbitrarily;
- latest being mistaken for current;
- summary being mistaken for truth;
- history being mistaken for authority;
- “memory” becoming a vague bucket that swallows everything.

So the protocol first answers this question:

**What objects actually exist in this world, and what is each object?**

---

## 3. The epistemology of the identity protocol: how can a machine know the current truth

The identity protocol rejects the runtime philosophy of “I remember,” “it is probably this,” or “it worked last time.”

Its core requirement is: **current truth must come from canonical sources, not from narration, guesswork, historical accident, or implicit habit.**

So the protocol is continuously building a machine epistemology:

1. installed and discoverability are separated;
2. latest receipt and current-thread binding are separated;
3. continuity and authority are separated;
4. pack durable families and runtime families are separated;
5. dialogue-retention, dialogue-governance, protocol-feedback, continuity, and memory-absorption are separated;
6. declaration / gate surfaces and artifact sinks are separated.

These may look like implementation details on the surface, but in substance they all answer the same question:

**Why is the machine justified in believing that this is the present fact, rather than mistaking history, compatibility residue, inference, or derived summary for truth?**

### 3.1 The existence, discoverability, admissibility, binding, and consumption of truth are not the same thing

Inside the identity protocol, the fact that a truth exists in protocol law does not automatically mean that an instance has operationally possessed it at runtime.

The protocol must distinguish at least five different layers:

1. **truth exists in protocol law**  
   The truth has been defined, frozen, or registered by the protocol and exists as part of shared law.
2. **truth is discoverable by instance**  
   The instance can find it from the correct canonical source, rather than only having it “exist in theory” inside documents, historical discussion, or sidecar scripts.
3. **truth is admissible as current-turn authority**  
   The truth has passed the identity, path, state, receipt, validator, and gate constraints required for the current turn, and is qualified to serve as current authority.
4. **truth is bound to current run / current thread**  
   The truth is not merely abstractly correct; it is actually bound to the current run, current thread, and current instance context.
5. **truth is consumed by the next operational step**  
   The truth has actually been consumed by the next hop and has driven a launcher path, runtime hook, route, receipt, gate, or operator-facing answer surface.

These five layers are not paraphrases of the same thing. They form a strict operational chain.

Therefore, the protocol must reject the following confusions:

- “this truth exists in the protocol” ≠ the instance has actually discovered it;
- “the instance discovered it” ≠ the instance is allowed to treat it as current truth;
- “it is allowed as current truth” ≠ it has been bound to the current run / thread;
- “it is bound to the current run / thread” ≠ the next hop has actually consumed it;
- “some artifact or declaration exists” ≠ full operational closure has been achieved.

This distinction explains many problems that look like “paper closure without runtime closure”:

- a shared contract, validator, family, or hook exists;
- but the instance never discovered it;
- or it discovered it but never passed admissibility;
- or it passed admissibility but never bound it to the current run;
- or it bound it to the current run but never drove next-hop consumption and evidence.

So mature closure in the identity protocol is never only about whether **truth exists**. It is about whether the **truth lifecycle has been fully carried through**.

Anything that satisfies earlier layers while failing later layers must not be claimed as full operational closure.

---

## 4. The normative theory of the identity protocol: what may be done and what may not be done

The identity protocol does not only define objects; it also defines boundaries of action.

It must answer:

- which entry surfaces are legitimate;
- which outputs are legitimate;
- which states may enter the success path;
- which receipts may serve as decision evidence;
- which families may accept which artifacts;
- which errors must fail-close;
- which historical or compatibility materials must remain confined to migration, replay, or diagnostics lanes instead of flowing back into active runtime.

So protocol maturity is not measured by “how many features it provides,” but by whether:

- entry is decidable;
- routing is decidable;
- artifacts are decidable;
- errors are decidable;
- convergence is decidable.

A protocol without normative theory eventually degenerates into a pile of implementation tricks.

---

## 5. The teleology of the identity protocol: it seeks long-term order, not local comfort

What the identity protocol ultimately wants is not “this run passes once,” but:

1. identity that does not drift over time;
2. entry surfaces that do not drift over time;
3. recovery that does not drift over time;
4. outputs that do not drift over time;
5. evidence that does not drift over time;
6. responsibility that does not drift over time.

So the value of the protocol is not one-time success, but **long-term stable order**.

When a system works only because operators remember many implicit rules, it is still a fragile human-governed system.
When a system translates those implicit rules into machine-readable law, it enters a machine-reproducible order.

---

## 6. The four-layer relation between standard Codex, the identity protocol, identity instances, and the operator

These four are not substitutes for each other. They are layers.

### 6.1 Standard Codex: the general execution substrate

Standard Codex answers questions such as:

- can the model reason;
- can it edit code;
- can it call tools;
- can it advance complex tasks.

Its strength is **general execution capability**.

### 6.2 The identity protocol: the machine-governance law layer

The identity protocol answers:

- under what identity, state, evidence, and recovery boundaries those capabilities must run;
- what counts as current truth;
- what may enter the success path;
- what must fail-close.

Its strength is **machine governance and law freezing**.

### 6.3 Identity instances: embodied role runtimes

Identity instances answer:

- who am I;
- what role responsibility do I carry;
- what may I do inside protocol-permitted boundaries;
- how do I prove through real execution that I still am this role.

Their strength is **role embodiment and business-state sedimentation**.

### 6.4 The operator: the natural-language collaboration entry

The operator should not bear the memory burden of low-level protocol law.

In a mature system:

- the operator asks in natural language;
- the identity instance returns a concrete answer surface;
- protocol-owned bundles carry machine truth;
- standard Codex provides the underlying execution power.

So a mature protocol system is not one that throws complexity directly at the user. It is one in which the instance compresses law into a stable, natural, executable answer surface without betraying the law.

---

## 7. Identity instance philosophy: who I am, what I can do, and how I do it

An identity instance is not first defined by a self-description in a prompt. It is a runtime unit constrained by the protocol.

### 7.1 Who I am

“Who I am” must be machine-verifiable, not narrative:

- what my `identity_id` is;
- what my `scope`, `work_layer`, and `source_layer` are;
- from which catalog and `pack_path` I am currently resolved;
- whether my `CURRENT_TASK`, `IDENTITY_PROMPT`, and actor-session tuple are closed;
- whether my current headstamp is consistent with machine truth.

The self-identity of an instance is **verifiable**, not merely descriptive.

### 7.2 What I can do

“What I can do” is not abstract intelligence. It is the set of lawful actions after protocol shaping:

- which routes, scripts, or tool lanes I may invoke;
- which artifact families I may lawfully write to;
- which operator-facing answer surfaces I may deliver;
- which conclusions I am qualified to hand off;
- which boundaries I may not cross.

Capability is not an infinitely expanding space. It is **defined inside protocol boundaries**.

### 7.3 How I do it

“How I do it” requires the instance to admit:

- it is not a free agent in an isolated universe;
- it must run through canonical launcher paths, canonical state, canonical receipts, canonical emit, and canonical routing;
- once its path, state, surface, receipt, or route drifts from the protocol, it should prioritize self-driven convergence rather than demanding protocol exceptions.

The value of a mature instance is not improvisation. It is **remaining stable, lucid, recoverable, and accountable inside law**.

### 7.4 When it is not my place to decide by myself

A mature instance must also answer a fourth question:

**When am I not qualified to decide on my own, and must instead escalate to the protocol layer or the semantic owner?**

This means the instance must distinguish:

- is this my residue or debt;
- or a shared-law gap;
- is this pack-local adaptation;
- or protocol semantic ambiguity;
- is this a self-heal task;
- or a shared infrastructure gap that must be escalated.

This fourth question is a key part of instance maturity.

---

## 8. Boundary of responsibility: the protocol defines the world, the instance adapts to the world

Inside the identity protocol, shared law and instance adaptation must be strictly separated.

### 8.1 What the protocol layer is responsible for

The protocol layer is responsible for:

1. freezing unambiguous terms;
2. defining canonical paths, states, receipts, and families;
3. providing shared validators, probes, readiness checks, CI, and replay wiring;
4. resolving shared semantic contradictions, shared implementation conflicts, and machine-truth gaps;
5. defining fail-close and success-path boundaries.

The protocol layer is responsible for **defining the law of the world**.

### 8.2 What the instance layer is responsible for

The instance layer is responsible for:

1. self-driven absorption of protocol upgrades;
2. cleaning pack-local residue;
3. filling runtime state, receipt, and lane adoption gaps;
4. repairing path, surface, script, and evidence drift;
5. making its real runtime surface converge back to law.

The instance layer is responsible for **continuous convergence under law**.

### 8.3 When something should rise to the protocol layer

A problem should rise to the protocol layer only if at least one of the following is true:

1. protocol semantics themselves are not unambiguous;
2. shared implementation contradicts shared documentation or shared law;
3. multiple instances will reliably hit the same structural gap;
4. machine truth itself is incomplete, so no amount of instance self-repair can achieve alignment.

Other than those cases, most problems should first be treated as instance self-driven adaptation tasks.

---

## 9. Five design questions for any new stream

Before any new protocol stream, shared strengthening, owner split, or runtime extension enters implementation, it should answer these five questions first:

1. **Ontology question**: What exactly is the new object, and is its ontology unambiguous?
2. **Truth-lifecycle question**: Where is the canonical truth; how is it discovered by instances, admitted, bound to the current run / current thread, and consumed by the next hop; and do state, receipt, validator, and bundle all close around that lifecycle?
3. **Normative question**: Which actions are permitted, which boundaries must fail-close, and which success-path conditions are required?
4. **Responsibility-split question**: Is this a shared-law problem or an instance-adaptation problem?
5. **Answer-surface question**: What is the stable answer surface ultimately delivered to the operator?

These five design questions are not self-certifying.

Admissibility may ask them once, but lawful ingress requires the corresponding
downstream root-law closures to remain machine-governed rather than being left
implicit.

If a new stream cannot answer these five questions, it probably has not yet been elevated from a local technique to a real protocol extension.

---

## 10. Why the protocol keeps becoming more stable

The identity protocol becomes more stable not because “more documents were written,” but because more implicit experience has been elevated into explicit machine law.

For example:

- the boundaries between launcher surface, install / discoverability, preferred / recommended / absolute fallback have been clarified;
- continuity, reentry, and consumption proof have been clarified;
- the boundaries among routing, learning, family, lane, emit, and receipt have been clarified;
- current-thread, dialogue-retention, and artifact-family viability have been clarified.

This means the system depends less and less on “whether humans remember complex rules,” and more and more on “whether machines execute according to law.”

For instances, this shift means:

- moving from improvisation to self-driven adaptation;
- moving from experience-based patching to protocol-law alignment;
- moving from local comfort to long-term steady state.

---

## 11. Final conclusion

The final conclusion can be compressed into three sentences:

1. **The identity protocol is a machine-law system, not a compatibility layer.**
2. **An identity instance is an embodied runtime unit inside that law system, not an exception applicant.**
3. **The protocol defines the world, the instance adapts to the world, and the operator receives from the instance a stable collaboration surface compressed by law.**

Therefore, the identity protocol is able to keep expanding not because it keeps piling on features, but because it first acquires a clearer and clearer bottom-layer philosophy.

Without design philosophy, extension degenerates into a patch collection.
With design philosophy, extension becomes growth with internal order.

The same logic applies to the protocol root corpus itself:

- without corpus discipline, root materials degenerate into a mixed archive of
  law, explanation, workaround, and temporary persuasion;
- with corpus discipline, the root remains a coherent machine-world law library
  whose later constitutions, contracts, mappings, validators, and runtimes can
  all be interpreted without losing semantic origin.

The machine-world corollary is strict:

- philosophy is the source of law,
- constitutions and contracts are the freezing of law,
- validators and runtime receipts are the adjudication of law,
- and no later layer may pretend it generated the layer above it.
