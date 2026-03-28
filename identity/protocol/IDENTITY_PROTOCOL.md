# Identity Protocol

## Normative source map (current governed execution)

This file is kept as protocol overview/baseline context.  
For active governed execution, normative sources are:

1. Historical motherline baseline:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. Active stream registry (current-state routing SSOT):
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. Current review/audit baseline:
   - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
4. Global protocol handoff baseline:
   - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
5. Foundational protocol design philosophy (interpretive / bottom-layer source):
   - `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Philosophical-order rule:

1. In philosophical order, identity protocol law exists because the bottom theory in `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` exists first.
2. This file is therefore a protocol-law constitution derived from that bottom theory, not an unrelated document set that later gained a philosophy appendix.

Governance rule:

1. Script updates under `scripts/` are implementation surfaces only.
2. Any P0/P1 contract change must first land in governance/review docs, then code/wiring/replay.
3. Script-only semantic changes without governance/review delta are non-compliant.

## Governance execution stack (how work is controlled)

1. **Contract layer** (`docs/governance/...v1.6.0.md` + active stream docs resolved by `stream-doc-registry.current.yaml`)
   - fields, enums, error-codes, fail-closed semantics, acceptance commands.
2. **Review layer** (`docs/review/...v1.6.md` + active stream review ledgers)
   - intake, replay verdict, non-merge stage status, residual risks.
3. **Implementation layer** (`scripts/*.py`, `scripts/*.sh`)
   - validators/writers/parsers and strict gate logic.
4. **Wiring layer** (creator/readiness/e2e/full-scan/three-plane/CI)
   - six-surface + required-gates wiring.
5. **Replay evidence layer** (reports + machine-readable payloads)
   - deterministic pass/fail with error-code families.

Status transitions are controlled by governance/review, not by script commit alone:
`SPEC_READY -> IMPL_READY -> GATE_READY -> VERIFIED -> DONE`.


## Foundational design philosophy boundary

1. `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` is the protocol-root bottom theory and interpretive source for why identity protocol law exists at all.
2. It explains why identity protocol is treated as a machine-law system, how protocol / instance / operator responsibilities split, and how new streams should be evaluated before implementation.
3. This file operationalizes and freezes those bottom-theory commitments into protocol-law structure, governance execution, contract boundaries, and runtime-facing constitutions.
4. The design philosophy document is therefore philosophically prior, but it is **not** a direct machine-consumed contract row, validator schema, or runtime success-path artifact sink.
5. Machine-consumed truth remains frozen in governance/review docs, mappings, validators, probes, runtime state, and receipts; the design philosophy document explains why those laws exist and how they should be interpreted, but does not replace them.
6. The root-domain machine-law primacy and compatibility-shelter boundary is frozen separately in `identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md`.
7. The root-domain machine-world ontology law for what objects may exist and how they remain semantically separate is frozen separately in `identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md`.
8. The root-domain current-truth epistemology law for how a machine justifies believing present fact is frozen separately in `identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md`.
9. The root-domain decision-evidence admissibility law for what may motivate, support, or terminally justify a machine decision is frozen separately in `identity/protocol/DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md`.
10. The root-domain success-path state admissibility law for which state classes may enter active execution, stay optional, or redirect into governed recovery is frozen separately in `identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md`.
11. The root-domain entry-surface legitimacy law for which entry surfaces are lawful, which may drive active execution, and which must remain helper-only, recovery-only, or demoted is frozen separately in `identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md`.
12. The root-domain error terminality law for which errors must fail-close, redirect into governed recovery, or remain explicitly non-blocking is frozen separately in `identity/protocol/ERROR_TERMINALITY_CONTRACT.md`.
13. The root-domain artifact-family admissibility law for which governed families may accept which artifacts, which artifacts remain merely compatible, and which must redirect or stay demoted is frozen separately in `identity/protocol/ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md`.
14. The root-domain prompt-bootstrap law for lawful identity prompt activation and bootstrap discipline is frozen separately in `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`.
15. The root-domain identity-discovery law for how lawful identity surfaces are discovered and bound is frozen separately in `identity/protocol/IDENTITY_DISCOVERY.md`.
16. The root-domain agent-handoff law for lawful cross-agent responsibility transfer and closure is frozen separately in `identity/protocol/AGENT_HANDOFF_CONTRACT.md`.
17. The root-domain instance self-judgement law for who I am, what I can do, how I do it, and when I must not decide alone is frozen separately in `identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md`.
18. The root-domain responsibility and escalation boundary between protocol law and instance adaptation is frozen separately in `identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md`.
19. The root-domain admissibility law for new protocol streams and shared strengthenings is frozen separately in `identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md`.
20. The root-domain truth lifecycle law for existence, discoverability, admissibility, run-binding, and next-hop consumption is frozen separately in `identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md`.
21. The root-domain operator answer-surface and law-preserving compression boundary is frozen separately in `identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md`.
22. The manual root-contract enumeration carried by this constitution is an explanatory projection and must remain congruent with the admitted `reading_order` root-contract sequence rather than becoming an independently authored alternate root index.

## Constitutional derivation discipline

1. This constitution may derive only from bottom theory, and from properly governed constitutional/contract strengthening that has been refrozen into protocol law.
2. Current stream, checker, or verdict state must not be reverse-projected into constitutional source law.
3. Governance evidence, review evidence, runtime evidence, or current-turn enforcement may expose incompleteness in constitutional law, but they do not become the semantic parent of that law merely by exposing the gap.
4. Operational evidence may justify constitutional strengthening, but it becomes law only after governed refreezing at constitutional or contract layers.

## Root constitutional-spine boundary

1. The root constitutional spine is governed as separate constitutional-entry and spine-bridge row families rather than as one narrative claim.
2. Constitutional-entry rows bind root index, bottom theory, protocol constitution, and runtime constitution as the lawful entry sequence of the root corpus.
3. Spine-bridge rows bind lawful derivation and authority-split continuity between those entry surfaces.
4. Protocol legality must keep expected row-family total and emitted row-family total congruent under machine-readable coverage completeness rather than relying on one aggregate spine count.
5. Protocol legality must also keep expected entry rel-path identities and expected bridge ids explicit rather than collapsing them into generic structure failure.
6. Protocol legality must not finalize constitutional-spine truth while missing or unexpected entry rel-paths or bridge ids remain known only inside validator machinery.

## Root-law promotion and re-entry boundary

1. Outer governance/review/workbook/reference/evidence/runtime/receipt/implementation surfaces may motivate strengthening, but they do not directly promote themselves into protocol-root law.
2. Root navigation and demoted support surfaces remain non-authoring surfaces; they may project or preserve context, but they do not silently regain constitutional or contract authority.
3. Governed re-entry for non-origin surfaces must terminate at an allowed root gateway:
   - constitutional law
   - runtime constitutional law
   - root contract law
   - machine-registry law
   - governed re-entry chain: constitution -> runtime constitution -> root contract -> machine-registry
4. Machine-registry or governed-extension surfaces may reveal a need for upstream strengthening, but that revelation does not reverse-author bottom theory, constitution, or runtime constitution.
5. Promotion into root law without governed refreezing is non-compliant, even if the motivating surface contains true evidence.

## Root gateway-admissibility boundary

1. Gateway admission is narrower than general motivation to strengthen.
2. Non-origin surfaces may enter only the root gateways explicitly admitted by governed gateway-admissibility law.
3. Gateway effect remains bounded by gateway class:
   - constitution gateway refreezes constitutional law;
   - runtime constitution gateway refreezes runtime law;
   - root contract gateway refreezes root-contract law;
   - machine-registry gateway projects machine-consumed registry truth.
4. Gateway effect target is fixed by gateway class itself; gateway admission cannot directly emit a different root target class than the one governed for that gateway.
5. Gateway effect target also retains the question class governed for that target layer rather than inheriting a new answer class from incoming motivation.
6. Gateway admission does not transfer authorship from an incoming surface to the gateway output.
7. Machine-registry gateway may terminate current-turn legality, but that does not let incoming motivation surfaces author upstream law.

## Root adjudication-surface boundary

1. Current-turn legality uses a phase-governed machine chain rather than a flat set of interchangeable enforcement surfaces.
2. mappings admit machine-consumed law and registry truth into current-turn legality;
3. validators evaluate legality against that admitted law rather than authoring new source law;
4. probes fail-close hidden drift instead of softening legality expectations;
5. runtime state binds live truth only after prior legality phases remain satisfied;
6. receipts close the adjudicated verdict and do not replace the earlier legality phases they report.
7. A later adjudication surface may summarize or close earlier legality work, but it may not back-author the law-bearing role of an earlier phase.
8. Bound runtime evidence and adjudicated verdict closure evidence are therefore different admissibility strata and must not be collapsed.
9. Operator answer compression must preserve those distinct backing strata rather than flattening all answer claims into one generic proof source.
10. Operator answer compression must also preserve distinct epistemic postures rather than flattening law-grounded, source-resolution, admissibility, live-bound, and realized-effect claims into one generic current-truth posture.
11. Current-truth commitments must preserve their own proof strata rather than flattening source grounding, governed resolution, present-turn authority, derivational provenance, and fail-close justification into one generic epistemic proof layer.
12. Success-path state classes must preserve their own admission-proof strata rather than flattening defined, admissible, bound, optional, recovery, and demoted-support state classes into one generic state proof layer.
13. Decision-evidence classes must preserve their own proof strata rather than flattening frozen-law, registry, validator-verdict, bound-runtime, closure, and demoted-support evidence classes into one generic decision-evidence proof layer.

## Root conflict-precedence boundary

1. Semantic-meaning conflict resolves by source-order law:
   - bottom theory
   - protocol constitution
   - runtime constitution
   - root contract law
2. Current-turn legality conflict resolves by machine-consumed enforcement terminals, with machine-registry law as the only terminal root gateway.
3. Gateway-authorship conflict resolves by gateway effect scope, preserved target question class, preserved answer mode, and preserved source order, not by incoming motivating surface identity.
4. Demotion-status conflict resolves by governed reclassification, not by later reuse, copying, or convenience.
5. No layer may use local recency, vividness, or implementation familiarity to seize precedence that belongs to another layer.

## Root machine-registry completeness boundary

1. Law-bearing root mapping families under `identity/protocol/mappings/` become canonical only when admitted by the machine-registry directory child set.
2. On-disk presence without registry admission does not authorize current-turn consumption, legal ingress, or bundle membership.
3. A governed root mapping family must remain explicit as a current/version pair rather than hiding behind an unregistered file.
4. Registry-completeness drift is a root-law failure, not a convenience-layer warning.
5. Registry admission without discoverable validator/probe/common/status-key/error-code surfaces is still incomplete.
5a. Registry admission without discoverable validator root-doc-anchor and row-projection contract surfaces is still incomplete.
5b. Registry admission without discoverable probe shadow-bootstrap contract surfaces is still incomplete.
6. Repo-relative descriptor surfaces disclosed by an admitted family must remain repo-root relative and repo-contained; absolute-path or parent-escape capture is non-compliant.
7. Repo-relative descriptor surfaces disclosed by an admitted family must also stay role-typed; validator, probe, and shared-common path classes are not interchangeable.
8. Role-typed repo-relative descriptor surfaces disclosed by an admitted family must also stay cross-role coherent; validator/probe/common may not silently bind to different root surface stems.
9. Cross-role coherent descriptor surfaces disclosed by an admitted family must also stay family-congruent; borrowing another family's descriptor stem requires explicit registry-completeness declaration rather than silent impersonation.

Machine-registry completeness must also keep admitted family and emitted
status disclosure explicit as separate row families; registered-complete
root-mapping-family total must remain congruent with family-status-row
total rather than being left implicit.

Machine-registry completeness must also keep admitted family identity
projection explicit; the registered complete family set may not be
collapsed into the emitted family-status-row subset.

Registry-completeness truth may not finalize on partial family-status-row
coverage while the registered complete family set remains known.

Machine-registry completeness must also keep violation projection
explicit; structure, completeness, and anchor violations must be
projected into stale reasons before final status.

Projected violation-reason total must remain congruent with
structure/completeness/anchor violation-row total rather than being left
implicit.

## Root governance completeness boundary

1. Governance law must remain machine-readable as separate registered-top-level-entry, corpus-class-profile, and forbidden-content-class row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each governance family must also remain explicit; rel-path, corpus-class, or forbidden-content-class identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize governance legality while missing or unexpected rel-path, corpus-class, or forbidden-content-class identities remain known only inside validator logic.
5. Fail-close governance output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root gateway-admissibility completeness boundary

1. Gateway-admissibility law must remain machine-readable as separate gateway-order, gateway-effect-target, and gateway-profile row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each gateway-admissibility family must also remain explicit; gateway identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize gateway-admissibility legality while missing or unexpected gateway identities remain known only inside validator logic.
5. Fail-close gateway-admissibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root derivation completeness boundary

1. Derivation law must remain machine-readable as a separate derivation-class-profile row family.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for the derivation family must also remain explicit; corpus-class identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize derivation legality while missing or unexpected corpus-class identities remain known only inside validator logic.
5. Fail-close derivation output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root transition completeness boundary

1. Transition law must remain machine-readable as separate surface-class-profile, direct-root-target-edge, and strengthening-gateway-edge row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each transition family must also remain explicit; surface, promotion-edge, or re-entry-gateway identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize transition legality while missing or unexpected surface, promotion-edge, or re-entry-gateway identities remain known only inside validator logic.
5. Fail-close transition output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root authority completeness boundary

1. Authority law must remain machine-readable as separate authority-class-profile and entry-authority-projection row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each authority family must also remain explicit; corpus-class or entry identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize authority legality while missing or unexpected corpus-class or entry identities remain known only inside validator logic.
5. Fail-close authority output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root conflict-precedence completeness boundary

1. Conflict-precedence law must remain machine-readable as separate precedence-profile and gateway-authorship-projection row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each conflict-precedence family must also remain explicit; conflict-class or gateway identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize conflict-precedence legality while missing or unexpected conflict-class or gateway identities remain known only inside validator logic.
5. Fail-close conflict-precedence output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root ordering completeness boundary

1. Ordering law must remain machine-readable as separate source-order, reading-order, README-root-contract-index, protocol-boundary-root-contract-index, adjudication-order, and adjudication-surface-profile row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each ordering family must also remain explicit; source, entry, manual-root-contract, or adjudication-surface identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize ordering legality while missing or unexpected source, entry, manual-root-contract, or adjudication-surface identities remain known only inside validator logic.
5. Fail-close ordering output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.
6. Explanatory root-contract indices rendered in root docs must remain congruent with admitted `reading_order` root-contract entries rather than silently authoring an alternate order.

## Root question-routing completeness boundary

1. Question-routing law must remain machine-readable as separate question-class-profile, root-entry-question-projection, and gateway-question-projection row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each question-routing family must also remain explicit; question-class or route identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize question-routing legality while missing or unexpected question-class or route identities remain known only inside validator logic.
5. Fail-close question-routing output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root design-question closure completeness boundary

1. Design-question closure law must remain machine-readable as separate required-question-closure and emitted-question-status row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each design-question closure family must also remain explicit; question identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize design-question closure legality while missing or unexpected question identities remain known only inside validator logic.
5. Fail-close design-question closure output must preserve missing/unexpected question identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root machine-law primacy completeness boundary

1. Machine-law primacy law must remain machine-readable as separate commitment, anchor, primacy-proof, primacy-limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each machine-law primacy family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize machine-law primacy legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close machine-law primacy output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root machine-world ontology completeness boundary

1. Machine-world ontology law must remain machine-readable as separate strata, object, ontology-proof, ontology-limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each machine-world ontology family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize machine-world ontology legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close machine-world ontology output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root stream-design admissibility completeness boundary

1. Stream-design admissibility law must remain machine-readable as separate question, admissibility-proof, admissibility-limit, outcome-class, and projection-surface row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each stream-design admissibility family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close stream-design admissibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root prompt-bootstrap completeness boundary

1. Prompt-bootstrap law must remain machine-readable as separate anchor, output-field, binding-field, proof, limit, and native-literal row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each prompt-bootstrap family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize prompt-bootstrap truth while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close prompt-bootstrap output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root entry-surface legitimacy completeness boundary

1. Entry-surface legitimacy law must remain machine-readable as separate entry-class, differentiation, proof, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each entry-surface legitimacy family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize entry-surface legitimacy truth while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close entry-surface legitimacy output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root identity-discovery completeness boundary

1. Identity-discovery law must remain machine-readable as separate section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each identity-discovery family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize identity-discovery truth while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close identity-discovery output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root agent-handoff completeness boundary

1. Agent-handoff law must remain machine-readable as separate role, payload, anchor, handoff-proof, handoff-limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each agent-handoff family must also remain explicit; role, payload, anchor, proof, limit, or collapse drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize agent-handoff legality while missing or unexpected handoff row identities remain known only inside validator logic.
5. Fail-close agent-handoff output must preserve missing/unexpected role, payload, anchor, proof, limit, and collapse row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root error-terminality completeness boundary

1. Error-terminality law must remain machine-readable as separate error-class, differentiation, proof, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each error-terminality family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize error-terminality truth while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close error-terminality output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root truth-lifecycle completeness boundary

1. Truth-lifecycle law must remain machine-readable as separate lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each truth-lifecycle family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize truth-lifecycle legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close truth-lifecycle output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root artifact-family admissibility completeness boundary

1. Artifact-family admissibility law must remain machine-readable as separate family-admission-class, differentiation, proof, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each artifact-family admissibility family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize artifact-family admissibility while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close artifact-family admissibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root current-truth epistemology completeness boundary

1. Current-truth epistemology law must remain machine-readable as separate commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each current-truth epistemology family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize current-truth epistemology while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close current-truth epistemology output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root success-path state admissibility completeness boundary

1. Success-path state admissibility law must remain machine-readable as separate state-class, differentiation, proof, state-class-proof-alignment, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each success-path state admissibility family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize success-path state admissibility while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close success-path state admissibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root decision-evidence admissibility completeness boundary

1. Decision-evidence admissibility law must remain machine-readable as separate evidence-class, differentiation, adjudication-phase-alignment, decision-evidence-proof, evidence-class-proof-alignment, limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each decision-evidence admissibility family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize decision-evidence admissibility while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close decision-evidence admissibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root operator answer-surface completeness boundary

1. Operator answer-surface law must remain machine-readable as separate surface, support-memory, support-limit, answer-claim-alignment, answer-claim-epistemic-alignment, answer-surface-proof, answer-surface-limit, boundary, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each operator answer-surface family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize operator answer-surface legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close operator answer-surface output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root protocol-instance responsibility completeness boundary

1. Protocol-instance responsibility law must remain machine-readable as separate layer, responsibility, escalation-trigger, escalation-proof, escalation-limit, and boundary-collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each protocol-instance responsibility family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize protocol-instance responsibility legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close protocol-instance responsibility output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root identity-instance self-judgement completeness boundary

1. Identity-instance self-judgement law must remain machine-readable as separate question, anchor, self-judgement-proof, self-judgement-limit, and collapse row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each identity-instance self-judgement family must also remain explicit; identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only inside validator logic.
5. Fail-close identity-instance self-judgement output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root law-bundle component-row completeness boundary

1. Root-law bundle coherence must remain machine-readable as separate component-row and component-status-row families.
2. Aggregate row-family counts are insufficient on their own; expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness.
3. Expected row identity set and emitted row identity set for each law-bundle family must also remain explicit; component identity drift may not be collapsed into summary-only counts.
4. Protocol legality must not finalize root-law bundle legality while missing or unexpected component identities remain known only inside validator logic.
5. Fail-close root-law bundle output must preserve missing/unexpected row identity projection rather than hiding drift behind aggregate-count shorthand or generic structure failure.

## Root-law bundle boundary

The protocol constitution depends on a governed root-law bundle across:

1. constitutional spine;
2. root admission/governance;
3. ordering;
4. authority;
5. question-routing;
6. derivation;
7. transition;
8. gateway-admissibility;
9. machine-registry completeness;
10. conflict precedence.

These are separate machine-law slices so that origin, navigation, authorship,
promotion, admissibility, and terminal legality do not collapse into one
informal rule.

Strengthening one slice must not silently weaken or bypass another; any
protocol-root change that alters the bundle requires governed updates in the
matching mapping, validator, and negative-probe surfaces.

Root-law bundle rows must also remain descriptor-concordant with the active
component families they bind; bundle metadata may not override or hide a
component family's own disclosed validator/probe/common/status-key/error-code
surfaces.

Root-law bundle rows must also preserve each bound component family's
disclosed probe shadow-bootstrap contract; bundle metadata may not suppress
bootstrap/mirror binding law or demote it into shell convention.

Local waiver of descriptor concordance must remain forbidden inside the
bundle.

Root-law bundle rows must also preserve descriptor-field mode; a repo-relative
path field may not be reinterpreted as validator-emitted metadata, and
validator-emitted status-key/error-code fields may not be reinterpreted as
ordinary path strings.

The bundle must not locally reauthor the self-describing descriptor schema
used by law-bearing root mapping families; its descriptor field set and
descriptor-field modes must remain aligned with root machine-registry
completeness law.

The bundle's descriptor schema must stay source-singular: one admitted source
component/current mapping pair, no substitute source, and no fallback source.

Local reauthoring of descriptor schema governance must remain forbidden
inside the bundle.

If that admitted source is unavailable or invalid, protocol legality must
fail-close rather than locally reconstructing descriptor schema.

The bundle must also inherit machine-registry completeness
self-describing-family requirement law; the admitted requirement that
law-bearing root mapping families stay self-describing may not be silently
redeclared, weakened, or guessed inside the bundle.

If the admitted source does not disclose that self-describing-family
requirement law, protocol legality must fail-close rather than locally
reconstructing self-describing-family legality.

Local redeclaration of self-describing-family requirement governance must
remain forbidden inside the bundle.

The bundle must also inherit machine-registry completeness family-surface
binding law; explicit cross-family descriptor-stem bindings declared there may
not be silently reauthored, suppressed, or replaced by local bundle convenience.

If the admitted source does not disclose that family-surface binding law,
protocol legality must fail-close rather than locally reconstructing
descriptor-family binding legality.

Local redeclaration of family-surface binding governance must remain
forbidden inside the bundle.

The bundle must also inherit machine-registry completeness repo-relative
descriptor path-pattern law; descriptor-stem capture patterns for validator,
probe, and shared-common surfaces may not be silently redeclared, loosened, or
guessed from bundle convention.

If the admitted source does not disclose those patterns, protocol legality
must fail-close rather than locally reconstructing descriptor-surface pattern
law.

The bundle must also inherit machine-registry completeness repo-relative
descriptor discipline law; repo-root-relative scope, parent-escape rejection,
role-typed path classes, and cross-role surface-stem coherence may not be
silently redeclared, weakened, or guessed inside the bundle.

Local redeclaration of repo-relative discipline governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that repo-relative discipline,
protocol legality must fail-close rather than locally reconstructing
descriptor-path legality law.

The bundle must also inherit machine-registry completeness current/version
naming law; root family prefix, current-entry suffix, active-version regex,
and current/version pair requirement may not be silently redeclared,
weakened, or guessed inside the bundle.

Local redeclaration of current/version naming governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that naming law, protocol legality
must fail-close rather than locally reconstructing current/version mediation
law.

The bundle must also inherit machine-registry completeness registry-child
admission law; canonical registry directory, admitted registry-current entry,
and registered child-set membership for component current/version files may
not be silently redeclared, weakened, or guessed inside the bundle.

Local redeclaration of registry-child admission governance must remain
forbidden inside the bundle.

If the admitted source does not disclose that registry-child admission law,
protocol legality must fail-close rather than locally reconstructing
component-admission law.

Bundle component descriptors must also stay current-entry mediated; bundle
rows bind through admitted component current mappings, not direct version-file
pinning.

If a component current row is absent or invalid, protocol legality must
fail-close rather than bypassing current mediation.

Root-law bundle rows must also remain validator-live; each bound component
validator must execute through its disclosed validator surface and emit
`PASS_REQUIRED` through its disclosed status key.

Descriptor concordance or file presence may not override a non-passing
component validator verdict.

Root-law bundle rows must also keep component validator execution-failure
policy fail-closed; missing execution, nonzero exit, invalid machine output,
or missing disclosed status key may not be downgraded into advisory noise.

Root-law bundle rows must also keep component validator returncode-observation
contract explicit; nonzero returncode is observed without host exception
overlay inside the bundle.

Local substitution of host-language exception raising for governed nonzero
returncode handling is forbidden inside the bundle.

Root-law bundle rows must also keep component validator machine-output
contract explicit; bundle legality consumes structured machine output carrying
the disclosed status key, not human-readable logs or incidental shell text.

Root-law bundle rows must also keep component validator invocation contract
explicit; bundle legality invokes the disclosed validator surface as `python3
<validator_script> --repo-root <repo_root> --json-only`.

Local substitution of interpreter, repo-root binding, or compact
machine-output mode is forbidden inside the bundle.

Root-law bundle rows must also keep component validator output-channel
contract explicit; the disclosed validator verdict is consumed from stdout
only.

stderr diagnostics must not be promoted into an alternate status-bearing
verdict channel inside the bundle.

Root-law bundle rows must also keep component validator stderr-isolation
contract explicit; stderr remains separately captured from verdict-bearing
stdout.

Local merging of stderr into stdout or admission of a mixed stream is
forbidden inside the bundle.

Root-law bundle rows must also keep component validator stdio text-decoding
contract explicit; bound component validators execute with utf-8 strict text
decode and no locale overlay.

Local substitution of codec, locale-shaped decoder choice, or replacement
policy is forbidden inside the bundle.

Root-law bundle rows must also keep component validator stdout-normalization
contract explicit; only outer-whitespace trim may occur before JSON decode
inside the bundle.

Local line selection, inner-content trimming, or JSON reconstruction from
mixed stdout is forbidden inside the bundle.

Root-law bundle rows must also keep component validator stdout-presence
contract explicit; bound component validator stdout must remain nonempty after
outer-whitespace trim.

Local treatment of empty or whitespace-only stdout as implicit success, an
invented empty object, or advisory silence is forbidden inside the bundle.

Root-law bundle rows must also keep component validator stdout-framing
contract explicit; bound component validator verdict is consumed only when
whole stdout is a single JSON object carrying the disclosed status key.

Local extraction of a JSON fragment from mixed stdout preamble, trailer, or
incidental shell text is forbidden inside the bundle.

Root-law bundle rows must also keep component validator status-key
resolution contract explicit; the disclosed status key is resolved only as a
direct top-level member of the admitted verdict object.

Local search across nested objects, alias keys, pointer paths, or other
convenience structures is forbidden inside the bundle.

Root-law bundle rows must also keep component validator status-literal
contract explicit; the disclosed status value is admitted only as the exact
canonical string literal.

Local trimming, case-folding, non-string coercion, or alternate-literal
mapping is forbidden inside the bundle.

Root-law bundle rows must also keep component validator execution-input
contract explicit; bound component validators execute with devnull-backed
noninteractive stdin.

Local inheritance of ambient stdin or dependence on operator keystrokes is
forbidden inside the bundle.

Root-law bundle rows must also keep component validator verdict-admission
timing contract explicit; bound component validator verdict is admitted only
after completed process exit.

Local streaming of partial stdout, pre-exit parsing, or background-process
substitution is forbidden inside the bundle.

Root-law bundle rows must also keep component validator execution-timeout
contract explicit; bound component validators execute with no local timeout
overlay inside the bundle.

Local injection of deadlines, kill-after policies, or timeout overlays is
forbidden inside the bundle.

Root-law bundle rows must also keep component validator working-directory
contract explicit; bound component validators execute with repo_root as the
governed working directory.

Local substitution of arbitrary cwd or ambient shell location is forbidden
inside the bundle.

Root-law bundle rows must also keep component validator execution-environment
contract explicit; bound component validators execute with inherited
parent-process environment and no local overlay.

Local injection of env maps, scrubbing of inherited variables, or shadow
environment overlay is forbidden inside the bundle.

Root-law bundle rows must also keep component validator execution-transport
contract explicit; bound component validators execute through local direct
subprocess vector transport.

Local substitution of shell mediation, remote hop, or other ambient transport
is forbidden inside the bundle.

Root-law bundle rows must also keep component validator contract-drift
execution policy explicit; bound component validators execute under canonical
contract and fail-closed on drift.

Local obedience to a drifted disclosed contract row or admission of
drift-shaped execution is forbidden inside the bundle.

Root-law bundle rows must also keep component validator contract-surface
projection policy explicit; bundle summary discloses declared contract rows
while component rows disclose effective canonical execution surface.

Local collapse of disclosed drift and effective execution or projection of
one as the other is forbidden inside the bundle.

Root-law bundle rows must also keep component validator observation-continuity
policy explicit; once bound component surfaces resolve, component observation
continues under canonical surface before final fail-close.

Local short-circuit that suppresses bound component observation merely
because a bundle contract row drifted is forbidden inside the bundle.

Root-law bundle rows must also keep component status-row coverage policy
explicit; every bound component must emit one status row before final
status.

Root-law bundle rows must also keep machine-readable coverage
completeness explicit; bound component total must remain congruent with
component-status-row total rather than being left implicit.

Local finalization on partial component-row coverage is forbidden inside
the bundle.

Root-law bundle rows must also keep violation-projection policy explicit;
all structure, bundle, and anchor violations must be projected into stale
reasons before final status.

Local final verdict must not withhold stale-reason projection for known
violation rows.

Root-law bundle rows must also keep machine-readable projection
completeness explicit; projected stale-reason total must remain congruent
with violation-row total rather than being left implicit.

Root-law bundle rows must also keep final-status derivation policy explicit;
final status is `PASS_REQUIRED` if and only if stale reasons remain empty
after violation projection; otherwise final status is `FAIL_REQUIRED`.

Local verdict path must not bypass stale-reason-adjudicated final status.

Root-law bundle rows must also keep error-code precedence policy explicit;
registry-class failure preempts structure-class failure, structure-class
failure preempts bundle-class failure, and pass-state emits empty error
code.

Local error-code derivation must not bypass precedence-adjudicated failure
classification.

Root-law bundle rows must also keep failure-classification policy explicit;
registry class derives from direct stale reasons present before violation
projection, structure class derives from structure violations, bundle class
derives from bundle and anchor violations, and otherwise failure class is
pass.

Local classification path must not invent an anchor-only failure class or
bypass direct stale reasons.

Root-law bundle rows must also keep registry-class admission policy
explicit; only direct stale reasons already present before violation
projection may admit registry failure class.

Projected violation reasons must not be reclassified as registry failure
basis.

Root-law bundle rows must also keep registry direct-stale-reason origin
policy explicit; admitted direct origins are alias error, document
invalidity, canonical contract-row invalidity, and required-surface
absence before violation projection.

Root-law bundle rows must also keep registry direct-stale-reason alias
origin policy explicit; admitted alias direct reasons are rows
containing the `_alias_error:` marker before document, required-surface,
and contract-row classification.

Root-law bundle rows must also keep registry direct-stale-reason
document origin policy explicit; admitted document direct reasons are
rows ending with `_empty_or_invalid` after alias exclusion and before
required-surface and contract-row classification.

Root-law bundle rows must also keep registry direct-stale-reason
required-surface origin policy explicit; admitted required-surface
direct reasons are required-component-descriptor-fields missing,
surface-missing rows, anchor-checks missing, and components missing
before violation projection.

Root-law bundle rows must also keep registry direct-stale-reason
contract-row origin policy explicit; admitted contract-row direct
reasons are root-corpus-law-bundle prefixed rows and
root-machine-registry-completeness prefixed rows that remain after
alias, document, and required-surface classification.

Root-law bundle rows must also keep registry direct-stale-reason source
policy explicit; direct stale-reason source is local stale reasons
already present before violation projection.

Projected structure, bundle, and anchor stale reasons must not be
reinterpreted as direct stale-reason source.

Root-law bundle rows must also keep machine-readable source completeness
explicit; direct-stale source total must remain congruent with local
stale-reason total rather than being left implicit.

Root-law bundle rows must also preserve any pre-fail completeness
mismatch as machine-readable evidence rather than normalizing totals
first and only surfacing a derived failure flag.

Root-law bundle rows must also keep registry direct-stale-reason
partition policy explicit; each local stale reason present before
violation projection classifies exactly once as alias, document,
contract-row, required-surface, or unknown ontology drift.

Root-law bundle rows must also keep registry direct-stale-reason
origin-classifier precedence policy explicit; alias classification
preempts document, document preempts required-surface, required-surface
preempts contract-row, and otherwise origin remains unknown.

Root-law bundle rows must also keep registry direct-stale-reason
residual-unknown policy explicit; only local stale reasons that remain
non-alias, non-document, non-required-surface, and non-contract-row
after alias, document, required-surface, and contract-row resolution
may remain unknown.

Root-law bundle rows must also keep registry direct-stale-reason
unclassified policy explicit; unclassified direct stale-reason origin
must remain fail-closed.

Local direct stale-reason ontology must not silently expand beyond those
admitted origins.

Root-law bundle rows must also keep component-validator observation-reason
policy explicit; admitted observation reasons are parse/status failure,
nonzero returncode after admitted parse/status resolution, and non-pass
component status before bundle-violation projection.

Root-law bundle rows must also keep component-validator parse/status
origin policy explicit; admitted parse/status reasons are
validator-output missing, validator-output invalid-json,
validator-output not-json-object, validator-status-key missing, and
validator-status-literal not-string before nonzero returncode, non-pass
component status, explicit non-execution exclusion, and
bundle-violation projection.

Root-law bundle rows must also keep component-validator nonzero-returncode
origin policy explicit; admitted nonzero-returncode reason is
component-validator nonzero returncode only, after admitted parse/status
resolution and before non-pass component status, explicit
non-execution exclusion, and bundle-violation projection.

Root-law bundle rows must also keep component-validator non-pass-status
origin policy explicit; admitted non-pass-status reason is
component-status not-pass-required only, after admitted parse/status and
nonzero returncode resolution and before explicit non-execution
exclusion and bundle-violation projection.

Root-law bundle rows must also keep component-validator prefixed
ontology-drift origin policy explicit; admitted prefixed
ontology-drift rows are validator-output, validator-status,
component-status, and component-validator prefixed rows only, after
admitted parse/status, nonzero returncode, non-pass-status, and
exclusion-origin resolution and before not-applicable classification.

Root-law bundle rows must also keep component-validator residual
not-applicable policy explicit; admitted residual not-applicable rows
are only nonprefixed, nonadmitted, nonexcluded rows after parse-status,
nonzero returncode, non-pass-status, exclusion-origin, and prefixed
ontology-drift resolution.

Root-law bundle rows must also keep component-validator observation-reason
classifier precedence policy explicit; parse/status classification
preempts nonzero returncode, nonzero returncode preempts non-pass
component status, non-pass component status preempts explicit
non-execution exclusion, explicit non-execution exclusion preempts
prefixed observation-family ontology drift, and otherwise classification
remains not-applicable.

Root-law bundle rows must also keep component-validator observation-reason
exclusion-origin policy explicit; admitted excluded non-observation rows
are component-validator missing, component-status-row coverage
incomplete, component-validator contract-surface reasons, and
component-probe surface-contract reasons before bundle-violation
projection.

Local bundle law must not silently re-bucket admitted observation
reasons or prefixed observation-family ontology drift as excluded
non-observation rows.

Local bundle law must keep non-execution bundle rows outside
component-validator observation ontology.

Root-law bundle rows must also keep component-validator observation-reason
source policy explicit; observation source is bundle-violation rows only
before violation projection.

Direct stale reasons, structure violations, anchor violations, and
projected stale-reason strings must not be reinterpreted as observation
source.

Root-law bundle rows must also keep machine-readable source completeness
explicit; observation-source total must remain congruent with
bundle-violation total rather than being left implicit.

Root-law bundle rows must also preserve any pre-fail completeness
mismatch as machine-readable evidence rather than normalizing totals
first and only surfacing a derived failure flag.

Root-law bundle rows must also keep component-validator observation-reason
partition policy explicit; each bundle-violation row classifies exactly
once as admitted observation reason, excluded non-observation row, or
unknown ontology drift before violation projection.

Root-law bundle rows must also keep component-validator observation-reason
unclassified policy explicit; unclassified observation reason must
remain fail-closed.

Local bundle observation ontology must not silently expand beyond those
admitted component-validator observation reasons.

## Goal

Define identity as a first-class control-plane protocol, parallel to skills and MCP.

- **Skills**: capability packaging and reusable procedures.
- **MCP**: tool transport and execution surface.
- **Identity**: role cognition, governance boundaries, decision loop, and learning closure.

This protocol is scenario-agnostic by design.

## Core ownership and escalation contract (v1.6.10 additive)

1. `identity protocol` is the shared contract and upgrade framework; it does **not** backstop instance-owned technical debt.
2. `identity instance` is an autonomous optimization unit and must absorb protocol upgrades, complete self-heal, and clear its own technical debt.
3. `instance_owned_technical_debt` includes missing instance-local skills/config/transport/install/replay hygiene and other local recovery obligations.
4. `instance_clean_proof` is required before any remaining issue may be escalated as `protocol_residual_issue`.
5. `No instance-clean proof, no protocol escalation.`
6. `protocol_residual_issue` means a shared contract / wiring / validator / CI / governance defect that still remains **after** `instance_clean_proof`.
7. Host/runtime entry gaps remain a separate boundary and must not be relabeled as either `instance_owned_technical_debt` or `protocol_residual_issue`.
8. Closed protocol layers must not be reopened by unresolved instance-owned technical debt.

## Bottom-layer no-downgrade / no-backstop / no backward-compatibility contract (motherline freeze)

1. `identity protocol` is a standard and upgrade target, not a compatibility shelter for lagging instances, workspaces, or one-off scenes.
2. Active protocol surfaces must not downgrade themselves or provide downward/backward compatibility in order to keep historical residue, partial adoption, or instance-local debt alive.
3. Instances and workspaces must self-upgrade to the current protocol contract; unresolved lagging adoption remains `instance_owned_technical_debt` until closed through governed upgrade/migration work.
4. Compatibility, fallback, bridge, and legacy-overlay behavior may survive only inside governed migration, replay, and diagnostics surfaces; they must not re-enter active defaults, validator green paths, current-turn runtime truth, active execution entry, or protocol-owned success paths.
5. Explicit fixture/import lanes may preserve historical literals only as non-runtime test/import material; they do not create backward-compatibility rights and must not be cited as active-runtime precedent.
6. When authoritative current-turn truth is missing, the protocol fail-closes; it does not rebuild live truth from compatibility projection, literal actor fallback, legacy alias bridges, or workspace-local backstops.
7. Kernel anchor: `rq_047_protocol_no_downgrade_motherline_contract_v1`.

## Layer contract

1. Canon layer (hard governance)
2. Identity prompt layer (role cognition + decision principles)
3. Runtime task layer (single source of truth state)

### Protocol-side prompt bootstrap source (v1.6 additive)

1. Runtime `IDENTITY_PROMPT.md` is a pack-level artifact and must remain under identity pack paths.
2. Protocol layer must not add same-name runtime artifact file `identity/protocol/IDENTITY_PROMPT.md`.
3. Prompt baseline source for protocol-side capability evolution is tracked in:
   - `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
4. Any update to the bootstrap source must close mapping + validator + replay chain before promotion-grade claims.

## Required identity pack files

For each identity id `<id>`:
- `identity/packs/<id>/IDENTITY_PROMPT.md`
- `identity/packs/<id>/CURRENT_TASK.json`
- `identity/packs/<id>/TASK_HISTORY.md`
- `identity/packs/<id>/META.yaml`
- `identity/packs/<id>/agents/identity.yaml`
- `identity/packs/<id>/scripts/README.md`

Compatibility note: legacy packs under `identity/<id>/` are migration-only locations; active runtime truth must resolve through catalog `pack_path` and must not treat the legacy tree as an open-ended default runtime backstop.

### Canonical identity instance pack topology (v1.6.13 additive)

1. Governed identity packs must keep the canonical root topology: `agents/`, `runtime/`, `scripts/`.
2. Pack-root `scripts/` is the only canonical identity-instance executable source surface.
3. `runtime/` remains reserved for runtime/autonomy/state/report/downsink assets; `runtime/scripts/` is forbidden.
4. Instance-local helper automation belongs in the instance pack, not in a workspace-global shared patch directory.
5. Required validator: `scripts/validate_identity_instance_pack_topology.py`.
6. Directory drift is fail-close; unregistered additional directories are non-compliant until promoted by governance.

### Canonical identity-Codex launcher boundary (v1.6.14 additive)

1. `v1.6.14` freezes the identity-bound Codex launcher model; it does not mutate Codex product semantics.
2. Canonical generic launcher command:
   - `identity-codex --identity-id <identity-id> -- <codex args>`
3. Canonical per-identity shortcut command:
   - `id-<identity-id> <codex args>`
4. Bare identity command names are non-canonical, and overriding the product command `codex` is forbidden.
5. Canonical pack-local launcher assets belong under pack-root `scripts/launchers/`, building on the `v1.6.13` pack topology freeze.
6. Canonical installed launcher shims belong under `${CODEX_HOME}/bin/`.
7. Workspace helper paths such as `scripts/codex_native_chat/` are migration/evidence helpers only until the protocol-owned launcher installer lands; they must not survive as active default entry surfaces or compatibility backstops after closure.
8. Launcher/install governance is separate from MCP provider health, business-tool availability, and host-final visible-surface promotion work.
9. Active runtime identities may not remain in launcher `SKIPPED_NOT_REQUIRED(contract_not_required)` state inside governed lifecycle surfaces; migration closure is now machine-enforced through launcher closure checks plus contract-backfill / launcher-rollout wiring.

### Canonical identity-instance script orchestration boundary (v1.6.15 additive)

1. `v1.6.15` freezes how governed routes bind to pack-local instance scripts; it does not create a new pack-root directory or reopen `v1.6.13` / `v1.6.14`.
2. Canonical pack-local script catalog path:
   - `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`
3. Canonical additive route fields under `capability_orchestration_contract.task_type_routes.<route>`:
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
   - `script_receipt_pattern`
4. Instance scripts become a first-class orchestration unit between `CURRENT_TASK.json` routing and lower capability execution, and a single route may bind multiple role-distinct script ids when probe/render/emit responsibilities are intentionally separated.
5. Lower capability dependencies remain explicit through `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields; script ids do not bypass those layers.
6. `script_preconditions` may reference inherited gateway/headstamp/host-visible/relay contracts, but those references do not reopen ownership of `v1.6.11`-`v1.6.14` streams.
7. Route-scoped lower-capability admission must remain machine-attributable; unrelated routes do not silently block a declared route unless a stronger activation policy explicitly says so.
8. Canonical receipt-family roles are route admission, execution, emit, and recovery, and they remain runtime-owned artifacts rather than source files under `scripts/`.
9. Receipt-family projections remain compatible with route provenance fields such as `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`, including layered execution-then-emit patterns.
10. If a governed route produces user-visible final text, that route must bind to a pack-local emitter script and declare an emit-family receipt.
11. Protocol-owned validators, continuity probe lane, and pack-lifecycle rollout wiring are now landed shared surfaces; launcher live-consumption proof and pilot adoption remain the follow-on targets.

### Canonical identity context continuity boundary (v1.6.16 additive)

1. `v1.6.16` freezes governed continuity checkpoints and startup-consumable re-entry briefing; it does not reopen `v1.6.13` / `v1.6.14` / `v1.6.15`.
2. Canonical continuity roles are:
   - `rolling_checkpoint`
   - `stage_checkpoint`
   - `migration_checkpoint`
   - `reentry_brief`
3. Continuity artifacts are derived continuity assets, not authority sources; authority remains in `IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, active governance/review docs, workbook surfaces, and governed runtime receipts.
4. The frozen default trigger profile is `default_turns_15_30_60`, with forced trigger classes such as clear/reset, compaction boundary, launcher restart/recover, resume migration, major commit, major gate flip, lane switch, and root-cause turns.
5. Continuity producers remain pack-local scripts under pack-root `scripts/`, inheriting `v1.6.13`; continuity outputs remain runtime-owned artifacts rather than source files.
6. Canonical target runtime continuity families are:
   - `runtime/reports/context-continuity/`
   - `runtime/state/context-continuity/`
7. `reentry_brief` is the canonical startup-consumable artifact and must stay compact enough for re-entry rather than becoming a long-history replacement.
8. Raw transcript persistence and vendor session history remain non-authoritative by default; when protocol mirrors them into governed runtime sinks, that ownership belongs to `v1.6.18` dialogue retention rather than continuity.
9. Launcher/startup/resume/recover entry remains owned by `v1.6.14`; `v1.6.16` owns only the continuity artifact model and safe consumption boundary.
10. No pack may claim `v1.6.16` adoption until continuity target paths are backfilled through the relevant topology and path-governance contracts.
11. The implementation-facing contract family for this stream is anchored by:
   - `rq_044_identity_context_continuity_artifact_contract_v1`
   - `rq_045_identity_reentry_brief_consumption_contract_v1`
   - `rq_046_identity_context_continuity_receipt_family_contract_v1`
12. The canonical task contract keys are `context_continuity_contract_v1` and `reentry_brief_consumption_contract_v1`; runtime receipt-family roles remain runtime-owned evidence families rather than task keys.
13. Day-1 implementation strategy is `flat-script-first`; new continuity-specific script subtrees are non-canonical until a later governed topology revision explicitly legalizes them.

### Canonical artifact-family routing boundary (v1.6.18 additive)

1. `v1.6.18` freezes the protocol-scoped routing matrix for persisted artifact families inside governed identity packs/runtime.
2. `memory` is not a canonical protocol artifact-family name; every persisted protocol artifact must resolve to an exact governed family.
3. The frozen protocol-scoped families are:
   - pack rulebook family -> `RULEBOOK.jsonl`
   - pack task-history family -> `TASK_HISTORY.md`
   - runtime dialogue-retention family -> `runtime/reports/dialogue-retention/**` + `runtime/state/dialogue-retention/**`
   - runtime dialogue-governance family -> `runtime/reports/dialogue-*.json`
   - runtime experience-feedback family -> `runtime/rulebooks/*.jsonl`, `runtime/examples/*experience-feedback*.json`, `runtime/logs/feedback/*.json`
   - runtime protocol-feedback family -> `runtime/protocol-feedback/**`
   - runtime continuity/reentry family -> `runtime/reports/context-continuity/**` + `runtime/state/context-continuity/**`
   - runtime memory-absorption family -> `runtime/memory-absorption/**`
4. `RULEBOOK.jsonl` and `runtime/rulebooks/*.jsonl` are distinct semantic objects and must not be collapsed into one “rule memory” bucket.
5. `TASK_HISTORY.md` is chronological pack history and must not be misused as continuity/reentry state.
6. `runtime/protocol-feedback/**` is governed protocol communication, not a generic learning or continuity sink.
7. `runtime/memory-absorption/**` is quarantine/re-materialization only and cannot satisfy active continuity, dialogue, learning, or protocol-feedback obligations.
8. Declaration keys and gates such as `reject_memory_gate`, `dialogue_retention_contract_v1`, `dialogue_governance_contract`, `experience_feedback_contract`, `context_continuity_contract_v1`, and `reentry_brief_consumption_contract_v1` are control-plane declarations, not artifact families.
9. The first family-specific machine consumer for this stream remains `rq_051_identity_dialogue_retention_contract_v1`; it mirrors product-sidecar session truth into governed runtime sinks without reclassifying that mirror as continuity or authority.
10. The whole-matrix routing machine consumer for this stream is now `rq_052_identity_artifact_family_routing_contract_v1`; it fail-closes on generic `memory` sink drift, missing routing contract coverage, cross-family path collisions, protocol-feedback root drift, continuity/reentry anchor drift, and memory-absorption active-path leakage while leaving each family’s deeper semantics with its inherited owner validator lane.
11. Semantic ownership for family names, canonical roots, canonical producer/consumer roles, and frozen non-goals remains with the `v1.6.18` governance stream plus its inherited owner streams; execution closeout may extend validators, probes, readiness wiring, replay breadth, and truth-sync only inside that frozen routing matrix.
12. Any future protocol-owned persisted family must be introduced by a later governed stream rather than silently added under generic “memory” wording.
13. Any change that adds/renames a family, repoints a canonical root, changes canonical producer/consumer roles, relaxes the `memory` anti-pollution boundary, promotes `runtime/memory-absorption/**` onto an active success path, or uses compatibility/backstop shortcuts to hide inherited-family failures must reopen governed semantic-owner review.
14. A routed red caused by an inherited family-owner validator is inherited-family execution/evidence debt unless the proposed fix crosses one of the semantic-owner boundaries above; that residual does not by itself reopen `v1.6.18` routing semantics.
15. Protocol interpretation of memory-like persisted artifacts is layered: language ban on generic `memory`, exact family identity, fixed path, canonical producer/consumer roles, declaration/gate separation, and runtime viability proof.
16. A family is considered viable only when semantic owner, canonical root, shared producer method, shared consumer/validator lane, and live replay on active identities all remain aligned; docs-only or path-only presence is insufficient.
17. Upgrade safety is three-state: required/adopted family must remain `PASS_REQUIRED`, optional/not-required family may remain `SKIPPED_NOT_REQUIRED` without dragging the outer routing lane red, and quarantine-only family must never be promoted to active success-path truth.
18. Future protocol-owned visual atlas growth for this boundary must use the shared reference onboarding path (`docs/references/README.md` plus `python3 scripts/generate_reference_visual_atlas_scaffold.py --help`) rather than freehand atlas sprawl; generator output is preview-only until registry/index/backlink/validator truth-sync is landed.

### Canonical weak-live-linkage differential-audit boundary (v1.6.19 additive)

1. `v1.6.19` freezes `weak_live_linkage` as a protocol-owned differential-audit lane across trio, prompt, sample/self-test, and loop-consumer surfaces; it does not reopen `v1.6.17`, `v1.6.18`, or invent a new artifact family.
2. The stream inherits the root philosophy truth lifecycle: truth exists, truth is discoverable, truth is admissible, truth is bound, and truth is consumed. Presence alone does not satisfy possession, and possession alone does not satisfy current-run consumption.
3. The machine-consumed intake row for this stream is `rq_055_identity_weak_live_linkage_differential_audit_contract_v1`.
4. `rq_055` green means the differential-audit law is installed, machine-consumed, and able to classify weak live-linkage patterns; it does **not** by itself claim that every affected consumer already reached `full_operational_closure`.
5. The frozen four-layer audit model is:
   - `contract_layer`
   - `artifact_layer`
   - `run_binding_layer`
   - `consumption_layer`
6. The frozen verdict classes are:
   - `structure_green`
   - `sample_or_history_green`
   - `unabsorbed_green`
   - `full_operational_closure`
7. The shared `roundtable_four_track_cross_validation_contract_v1` primitive may be reused as cross-validation intake for route/loop evidence discrimination, but it does not become a new loop, a new artifact family, or the semantic owner of weak-live-linkage law.
8. History/sample/meta artifacts may remain valid for sample/self-test, review, or semantic-center proof; they must not silently satisfy strict current-run success once the stream requires live-binding and next-hop-consumption interpretation.

### Canonical terminal-truth cleanliness boundary (v1.6.21 additive)

1. `v1.6.21` freezes one higher-order protocol boundary above inherited execution-closure law:
   - execution closure truth,
   - clean terminal truth,
   - canonical publishability
   must remain distinct machine interpretations.
2. The stream does **not** reopen the inherited legality of review-required execution closure. Instead, it freezes that review-required closure may remain execution-closed while still being vetoed from clean terminal truth and canonical publishability.
3. The machine-consumed intake row for this stream is `rq_056_identity_terminal_truth_cleanliness_contract_v1`.
4. Governed negative feedback may veto:
   - `clean_terminal_truth`
   - `canonical_publishability`
   without automatically invalidating the lower execution-closure truth.
5. Dirty signals such as degraded writeback, deferred writeback status, `all_ok=false`, `next_recovery_action`, placeholder outputs, unresolved contradictions, and confidence-below-floor must fail-close on the clean-terminal / publishable lane.
6. Canonical publishability requires clean terminal truth. Execution closure alone is insufficient.
7. Instance/runtime projections must not emit `is_terminal_clean=true`, `publishable=true`, or `canonical_result_eligible=true` while dirty signals remain active; the shared adoption probe must fail-close such drift.
8. The same lane also emits an explicit terminal-state equivalence projection (`terminal_state_class`, `terminal_state_machine_status`, `requires_review`, `retry_required`, `revalidation_required`, `repair_required`, `quarantine_required`, `requires_human`, `terminal_failure`) so downstream consumers do not collapse every non-clean state into one ambiguous failure bucket. Review-pending, revalidation-pending, repair-pending, retry-pending, quarantine, and failed-terminal semantics must remain machine-distinct.
9. Generic clean-completion alias surfaces such as top-level `overall_status` / `final_status` / `status` / `result` / `outcome` plus `done` / `completed` booleans must not claim clean completion while the higher-order lane remains non-clean; alias drift is part of the shared adoption fail-close boundary rather than a pack-local interpretation detail.

## Runtime source-of-truth boundary (v1.4.x hardening)

Identity runtime must distinguish demo fixtures from local runtime instances:

- **fixture/demo identity**: repository-local references for examples and protocol fixtures.
- **runtime identity**: local instance under `IDENTITY_HOME`, resolved from local catalog.

Runtime decisions (validate/activate/update/install/writeback) must use local runtime context.
Repository fixture files must not be treated as live runtime state.

### Scope resolution contract (v1.4.12 uplift)

Identity resolution must be deterministic and auditable across layered scopes:

1. CLI explicit parameters (`--catalog`, `--target-root`, `--scope`)
2. Environment/config (`IDENTITY_HOME`, `runtime-paths.env`)
3. Project runtime scope (`<project>/.identity`)
4. Global runtime scope (`${CODEX_HOME:-~/.codex}/.identity`)

Legacy labels/paths (`local`, `repo`, `env`, `auto`, `.agents/identity`, `~/.codex/.identity`) are migration metadata only and must not enter strict runtime gate semantics.

If one `identity_id` resolves to multiple pack paths across scopes, tooling MUST fail unless explicit arbitration (`--scope`) is provided.

Mandatory validator:
- `scripts/validate_identity_scope_resolution.py`
- `scripts/validate_identity_scope_isolation.py`
- `scripts/validate_identity_scope_persistence.py`

Operational remediation entrypoint:
- `python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog> [--apply]`

Health diagnostics contract (CI-gated):
- `python3 scripts/collect_identity_health_report.py --identity-id <id> --catalog <catalog> --out-dir <dir> --enforce-pass`
- `python3 scripts/validate_identity_health_contract.py --identity-id <id> --report-dir <dir> --require-pass`

Protocol requirement:
- Health report must include failed-check recommendations.
- Required-gates/release/e2e MUST run health collection + contract validation.

Permission-state contract (CI-gated):
- `scripts/validate_identity_permission_state.py`
- upgrade report MUST include:
  - `permission_state`
  - `permission_error_code`
  - `writeback_precheck`
- CI/release requires `writeback_status=WRITTEN`; deferred permission status is not release-pass eligible.

### Cross-actor isolation scope semantics (v1.6.8 additive)

`IP-ASB-203` enforcement must distinguish current-actor closure from global hygiene telemetry.

1. Canonical validator:
   - `scripts/validate_cross_actor_isolation.py`
2. Supported scope modes:
   - `catalog_all`: fail-close on any actor binding anomaly in catalog scope.
   - `actor_primary`: fail-close on current actor scope, keep non-target actor anomalies as warning telemetry.
   - `actor_only`: fail-close on current actor scope only.
3. Strict runtime orchestrators (full-scan/three-plane/readiness/e2e/ci) must pass:
   - `--actor-id <resolved_actor_id>`
   - `--scope-mode actor_primary`
4. Telemetry contract (machine-readable):
   - `cross_actor_isolation_status` remains blocking status for current actor scope.
   - `global_observation_status` + `global_observation_stale_reasons` expose non-target actor contamination.
5. Fail-close boundary:
   - current actor scope anomalies remain `FAIL_REQUIRED` (`IP-ASB-203`);
   - unrelated actor-file anomalies are visible warnings and must not hard-block current actor closure by default.

## Registry contract

`identity/catalog/identities.yaml` must include:
- id
- title
- description
- status
- methodology_version
- pack_path

`default_identity` must reference a valid id.

Optional metadata blocks per identity:
- `interface` (display_name, short_description, default_prompt)
- `policy` (allow_implicit_activation, activation_priority, conflict_resolution)
- `dependencies` (tool/env/network/filesystem requirements)
- `observability` (event_topics, required_artifacts)

See discovery draft: `identity/protocol/IDENTITY_DISCOVERY.md`.

### Identity-scoped evidence rule (mandatory)

For runtime identities, evidence/sample/log path patterns must be identity-scoped:

- path fields must include target `identity_id`
- cross-identity hits (including `store-manager` for non-store identities) are invalid
- global fallback to unrelated identity samples is forbidden

Mandatory validator:
- `scripts/validate_identity_instance_isolation.py`

### State-source strategy (mandatory, v1.6 semantic freeze)

To avoid catalog/META drift, protocol adopts **dual-write + strong consistency**:

- single decision source: runtime catalog status (`catalog.local.yaml` for runtime identities)
- mirrored audit field: `META.status` is required and must equal catalog status
- activation/switch operation must update both layers transactionally
- any mismatch is a protocol violation
- `catalog_multi_active` is allowed for actor-scoped parallelism
- `session_primary_binding` is mandatory in strict lanes (same actor/session tuple must not drift across identities)

Mandatory validator:
- `scripts/validate_identity_state_consistency.py`

## Four core capability contracts

Identity protocol must be verifiable against four capability contracts:

1. **Accurate judgement contract**
   - Requires multimodal evidence consistency checks.
   - Inconsistent evidence cannot transition to `done`.

2. **Reasoning loop contract**
   - Requires hypothesis/patch/result trace per attempt.
   - "No-target-reached" cannot be treated as completion.

3. **Auto-routing contract**
   - Requires problem-type routing map and route-switch policy.
   - When uncertainty persists, route discovery must execute (identity/skill/tool).

4. **Rule learning contract**
   - Requires append-only rulebook linkage to run evidence.
   - Requires both negative and positive rule accumulation over time.

### Accurate judgement canonical binding (v1.6.2 multimodal stream)

To avoid “statement-only” drift, the accurate judgement contract is hard-bound to protocol plugin governance:

1. Contract ID: `rq_034_multimodal_plugin_enforcement_contract_v1`
2. Requirement key: `asb16-rq-034`
3. Canonical validator: `scripts/validate_multimodal_plugin_enforcement.py`
4. Canonical plugin root: `identity/protocol/plugins/`
5. Canonical registries:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - `identity/protocol/plugins/PROVIDER_PROFILES.current.yaml`
6. Mandatory done-transition gate:
   - `requires_multimodal_evidence_consistency=true`
   - `inconsistent_evidence_transition=block_done`
7. Any non-canonical plugin contract/profile source in strict lane must fail-close (`IP-MM-REG-001`).

### Reasoning loop canonical binding (v1.6.2 fail-close stream)

To avoid “trace-present but semantic-invalid” drift, the reasoning loop contract is hard-bound to protocol fail-close plugin governance:

1. Contract ID: `rq_035_reasoning_loop_failclose_contract_v1`
2. Requirement key: `asb16-rq-035`
3. Canonical validator: `scripts/validate_reasoning_loop_failclose.py`
4. Canonical plugin root:
   - `identity/protocol/plugins/reasoning-loop-enforcement/`
5. Mandatory semantic gate:
   - done/pass completion block is controlled by `no_target_completion_mode`:
     - default `terminal_attempt_only`: terminal unresolved attempt cannot transition to done/pass.
     - optional `any_attempt`: any historical `no_target_reached=true` blocks done/pass.
   - `done_requires_terminal_target_reached=true` preserves strict closure for unresolved terminal completion.
   - failed attempt without `next_action` is fail-close.
   - escalation threshold is controlled by `escalation_requirement_mode` (default `at_or_exceed`).
   - once escalation threshold is hit, missing escalation signal is fail-close.
   - escalation signal accepts boolean/token markers and configurable non-empty reference fields when enabled; generic retry text is not escalation by default.
   - strict operations use `strict_run_id_binding=true`: when `run_id` is provided, any selected runtime proof source (including fallback sources) must bind to the same run id or fail-close with `IP-RL-RUN-006`.
   - runtime proof source selection is configuration-driven via `runtime_report_selection_mode` (default `prefer_run_id`) to reduce strict-lane volatility without requiring explicit `report_selected_path`.
6. Enforcement-level policy is configuration-driven (no validator hardcoding):
   - `L1`: attempt trace integrity
   - `L2`: `L1` + four-track evidence refs
   - `L3`: `L2` + external freshness/reconciliation constraints
7. Any registry/profile/contract mismatch for reasoning plugin in strict lane must fail-close (`IP-RL-REG-001` / `IP-RL-CONF-001`).

## Protocol baseline review contract (v1.2.3+)

To avoid identity-level drift and unsupported architectural conclusions, identity upgrades MUST include baseline protocol review evidence.

When task intent involves identity-capability upgrades or architecture decisions:

- `gates.protocol_baseline_review_gate` MUST be `required`.
- `protocol_review_contract` MUST exist in CURRENT_TASK and include:
  - `must_review_sources` (required canonical references)
  - `required_evidence_fields`
  - `evidence_report_path_pattern`

A valid review evidence record MUST include, at minimum:
- review id/time/reviewer
- purpose
- reviewed source list
- findings
- decision

## Identity update lifecycle contract (v1.2.4+)

To match skill update discipline (`trigger -> patch -> validate -> replay`), identity updates MUST define and pass an explicit lifecycle contract.

When runtime detects operational failure or capability gap:

- `gates.identity_update_gate` MUST be `required`.
- `identity_update_lifecycle_contract` MUST exist in CURRENT_TASK and include:
  - `trigger_contract` (when update is mandatory)
  - `patch_surface_contract` (what files/contracts must be changed)
  - `validation_contract` (which checks must pass)
  - `replay_contract` (same-case regression requirements)

Mandatory patch surfaces:
- `CURRENT_TASK.json`
- `IDENTITY_PROMPT.md`
- `RULEBOOK.jsonl`
- `TASK_HISTORY.md`

Mandatory validators:
- `scripts/validate_identity_runtime_contract.py`
- `scripts/validate_identity_upgrade_prereq.py`
- `scripts/validate_identity_update_lifecycle.py`

No replay pass -> no identity learning completion.

## Identity trigger regression contract (v1.2.5+)

To mirror mature skill trigger stability practice, identity route/update changes MUST pass trigger regression.

When routing, trigger conditions, or update gates are modified:

- `trigger_regression_contract` MUST exist in CURRENT_TASK.
- Required suites:
  - `positive_cases`
  - `boundary_cases`
  - `negative_cases`
- Each suite requires deterministic expected/observed route + trigger result.

Mandatory validator:
- `scripts/validate_identity_trigger_regression.py`

No trigger-regression pass -> no identity update completion/merge.

## Agent handoff contract (v1.2.7+)

To prevent master/sub execution drift, identity updates with delegated sub-agent execution MUST pass handoff contract validation.

When handoff is used:

- `gates.agent_handoff_gate` MUST be `required`.
- `agent_handoff_contract` MUST exist in CURRENT_TASK and include:
  - required handoff fields
  - forbidden mutation list
  - handoff log pattern
  - allowed result enum

Mandatory validator:
- `scripts/validate_agent_handoff_contract.py`

No handoff pass -> no merge.

Contract reference:
- `identity/protocol/AGENT_HANDOFF_CONTRACT.md`

## Human-collaboration trigger contract (v1.3.0+)

To avoid silent stalls when runtime is blocked by human-only interactions, identity runtime MUST carry explicit collaboration-trigger controls.

When collaboration blockers are possible:

- `gates.collaboration_trigger_gate` MUST be `required`.
- `blocker_taxonomy_contract` MUST exist in CURRENT_TASK and include mandatory blocker types:
  - `login_required`
  - `captcha_required`
  - `session_expired`
  - `manual_verification_required`
- `collaboration_trigger_contract` MUST exist in CURRENT_TASK and include:
  - hard rule and trigger conditions
  - immediate notify policy (`notify_policy` + `notify_timing=immediate`)
  - `notify_channel` (default: `ops-notification-router`)
  - dedupe controls (`dedupe_window_hours` + `state_change_bypass_dedupe`)
  - `must_emit_receipt_in_chat=true`
  - evidence log path + freshness window

Mandatory validator:
- `scripts/validate_identity_collab_trigger.py`

No collaboration-trigger pass -> no merge/no release for affected identity update.

## Control-loop extension contracts (v1.4.0+)

To keep identity as an auditable control-plane (not a prompt-only layer), runtime MUST enforce the closed-loop extension contracts:

`Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update`

Required runtime contracts:

- `capability_orchestration_contract`
  - defines skill orchestration strategy, MCP/tool selection constraints, and routing budget/risk boundaries.
- `knowledge_acquisition_contract`
  - defines when retrieval is mandatory, source tiers, evidence format, and refresh policy.
- `experience_feedback_contract`
  - defines positive/negative experience feedback, rulebook impact, and replay promotion rules.
- `install_safety_contract`
  - defines non-destructive local-instance install defaults, idempotent reinstall behavior, and backup/rollback requirements for replace operations.
- `ci_enforcement_contract`
  - defines required validator/check inventory and CI gate alignment.

Mandatory validators:

- `scripts/validate_identity_orchestration_contract.py`
- `scripts/validate_identity_knowledge_contract.py`
- `scripts/validate_identity_experience_feedback.py`
- `scripts/validate_identity_install_safety.py`
- `scripts/validate_identity_experience_feedback_governance.py`
- `scripts/validate_identity_ci_enforcement.py`

No control-loop contract pass -> no identity update completion/merge.

## Capability arbitration contract (v1.4.2+)

To keep four core capabilities aligned under runtime tension, identity MUST define conflict arbitration rather than implicit trade-offs.

When routing/latency/learning priorities conflict:

- `gates.arbitration_gate` MUST be `required`.
- `capability_arbitration_contract` MUST exist in CURRENT_TASK and include:
  - `priority_order`
  - `conflict_rules` (judgement_vs_routing / reasoning_vs_latency / routing_vs_learning / learning_vs_hotfix)
  - `trigger_thresholds`
  - `decision_record_required_fields`
  - `sample_report_path_pattern`

Mandatory validator:
- `scripts/validate_identity_capability_arbitration.py`

No arbitration pass -> no merge for affected route/update changes.

## Skill + MCP + Tool collaboration contract (new baseline in v1.2.5)

Identity capability decisions MUST align with collaboration boundaries:

- skill = strategy constraints (sequence/validation/fallback)
- MCP = capability access surface (registered tools)
- tool = concrete execution action

Identity must never assume:
- skill automatically grants external permissions
- skill trigger implies MCP/tools are necessarily available

Collaboration baseline reference:
- `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

## Dual-track governance model

### Track A: hard guardrails

Non-bypassable constraints:
- compliance and legal boundaries
- rejection memory constraints
- media integrity constraints
- escalation triggers
- collaboration trigger gate for human-collab blockers
- protocol baseline review gate for identity-upgrade decisions
- identity update lifecycle gate for runtime evolution decisions
- trigger regression gate for route/update changes
- agent handoff gate for delegated execution changes
- orchestration gate for capability composition decisions
- knowledge acquisition gate for source-grounded decisions
- experience feedback gate for rule learning closure
- ci enforcement gate for required-check integrity
- arbitration gate for four-core conflict resolution integrity

## Release-plane declaration rule

- `Conditional Go`: allowed when local acceptance chain passes but cloud required-gates is not yet green on release head.
- `Full Go`: allowed only when both local acceptance and cloud required-gates pass on same release head.
- install safety gate for local-instance preservation integrity

### Track B: adaptive growth

Continuously updated strategy:
- failed-case pattern extraction
- hypothesis -> experiment -> replay
- skill and prompt tuning proposals

## Runtime state requirements (CURRENT_TASK.json)

Minimum required blocks:
- `objective`
- `state_machine`
- `gates`
- `source_of_truth`
- `escalation_policy`
- `required_artifacts`
- `post_execution_mandatory`
- `evaluation_contract`
- `reasoning_loop_contract`
- `routing_contract`
- `rulebook_contract`
- `blocker_taxonomy_contract`
- `collaboration_trigger_contract`
- `capability_orchestration_contract`
- `knowledge_acquisition_contract`
- `experience_feedback_contract`
- `install_safety_contract`
- `ci_enforcement_contract`
- `capability_arbitration_contract`

Conditional required blocks:
- `protocol_review_contract` (identity upgrade tasks)
- `identity_update_lifecycle_contract` (runtime evolution / update tasks)
- `trigger_regression_contract` (routing/trigger/update gate changes)
- `agent_handoff_contract` (master/sub delegated execution)
- `blocker_taxonomy_contract` + `collaboration_trigger_contract` (human-collab blockers)

## Conflict resolution

Priority order:
1. Canon/hard guardrails
2. CURRENT_TASK runtime contract
3. Skill instructions
4. MCP/tool preference

## Alignment with skill and MCP protocol patterns

To reduce protocol drift and avoid ad-hoc logic:
- Identity must remain declarative and schema-verifiable (like skill metadata discipline).
- Runtime decisions must be contract-driven and testable (like MCP interface determinism).
- Discovery, validation, and release gates must be explicit and automated.
- Identity conclusions for protocol upgrades must be source-cited and evidence-backed.
- Identity updates must follow explicit trigger/patch/validate/replay lifecycle, mirroring skill update discipline.
- Identity route/update behavior must pass positive/boundary/negative trigger regression.
- Identity review must include skill+mcp+tool collaboration boundary checks.
- Identity delegation must pass master/sub handoff payload and mutation-safety checks.
- Identity human-collab blockers must pass taxonomy + immediate auto-notify + receipt constraints.

## Email escalation policy

Email is only for offline blocking actions. Non-blocking updates are routed to logs or dashboards.

## Batch-1 anchor placeholders (v1.6 intake, non-promotional)

The following sections provide stable kernel anchors for v1.6 Batch-1 mapping rows.
Execution closure remains governed by v1.6 governance/review and must stay
`SPEC_READY / PENDING_INTAKE` until validator + replay closure is complete.

### rq_001_unlock_formula_contract_v1

Required receipt fields:

- `unlock_allowed`
- `decision_gates`
- `p0_total`
- `p0_done`
- `p0_not_done_refs`
- `audit_signoff_status`
- `env_blockers`
- `protocol_blockers`
- `evidence_refs`

Hard constraints:

1. `D6` is derived output only (`D1..D5` + `P0` ledger are the only formula inputs).
2. Same governance/review inputs must produce stable `formula_input_digest`.

### rq_002_capability_boundary_contract_v1

Required receipt fields:

- `boundary_classification`
- `classification_source`
- `capability_activation_status`
- `capability_activation_error_code`

Hard constraints:

1. `IP-CAP-*` must classify to `env_auth_blocker` by default.
2. Classification must keep env/auth blockers separate from protocol-code blockers.

### rq_003_promotion_evidence_pipeline_contract_v1

Required receipt fields:

- `decision_hash`
- `input_hash`
- `reviewer_role`
- `reviewer_signature_ref`
- `evidence_bundle_refs`

Hard constraints:

1. Promotion evidence must be non-repudiable and deterministic for same inputs.
2. Narrative-only promotion without receipt fields is invalid.

### rq_004_outlet_matrix_contract_v1

Required receipt fields:

- `outlet_matrix_status`
- `matrix_positive_status`
- `matrix_negative_status`
- `cross_cwd_parity_status`
- `send_time_gate_status`
- `governed_outlet_enforced`
- `outlet_channel_id`
- `outlet_bypass_detected`

Hard constraints:

1. Positive + negative paths are both mandatory.
2. Bypass/manual/direct outlet drift must be fail-closed.

### rq_005_sidecar_cwd_invariance_contract_v1

Required receipt fields:

- `cwd_parity_status`
- `passthrough_digest`
- `sidecar_contract_status`
- `sidecar_error_code`

Hard constraints:

1. Root and temp execution must produce identical normalized passthrough digest.
2. CWD-only noise cannot change sidecar verdict semantics.

### rq_006_release_plane_cloud_evidence_contract_v1

Required receipt fields:

- `target_branch`
- `release_head_sha`
- `required_gates_run_id`
- `run_url`
- `workflow_file_sha`
- `run_head_sha`
- `run_workflow_file_sha`
- `conditions`
- `release_plane_status`

Hard constraints:

1. Release-plane evidence must bind to one run tuple (`run_id + head + workflow_file_sha`).
2. Missing cloud evidence under strict lanes must fail-close.

### rq_007_cross_cwd_absolute_input_contract_v1

Required receipt fields:

- `repo_catalog_input`
- `repo_catalog_is_absolute`
- `repo_cwd_resolved_repo_catalog`
- `tmp_cwd_resolved_repo_catalog`
- `cwd_parity_status`

Hard constraints:

1. Non-absolute `repo_catalog` must fail-close in strict lanes.
2. Root-cwd and temp-cwd resolution must converge to the same canonical path.

### rq_008_docs_bridge_consistency_contract_v1

Required receipt fields:

- `bridge_consistency_status`
- `contradiction_pairs`
- `governance_anchor_refs`
- `review_anchor_refs`

Hard constraints:

1. Contradiction tuples must be deterministic for unchanged docs inputs.
2. Bridge checker output must be machine-replayable.

### rq_009_run_id_anchored_report_selection_contract_v1

Required receipt fields:

- `run_id`
- `selection_strategy`
- `report_selected_path`
- `candidate_count`

Hard constraints:

1. If run-id is present, selection must be run-id anchored before mtime fallback.
2. Same run-id + candidate set must produce stable selected report path.

### rq_010_phase_a_bootstrap_before_strict_contract_v1

Required receipt fields:

- `phase_a_refresh_applied`
- `phase_b_strict_revalidate_status`
- `phase_trace_status`

Hard constraints:

1. Strict revalidate must preserve phase-A bootstrap traceability.
2. Update/readiness/aggregation lanes must consume the same phase tuple semantics.

### rq_011_tmp_collision_safe_allocator_contract_v1

Required receipt fields:

- `tmp_root`
- `generated_paths`
- `collision_count`
- `unique_path_count`
- `path_scope_guard_status`

Hard constraints:

1. Runtime temp allocation must be run-scoped and collision-safe.
2. Temp artifacts must remain within runtime temp root (no path escape).

### rq_012_handoff_collab_freshness_autorotation_contract_v1

Required receipt fields:

- `rotation_applied`
- `freshness_age_days`
- `rotation_receipt_ref`
- `freshness_status`

Hard constraints:

1. Freshness decisions must be receipted and replayable.
2. Stale freshness without rotation closure must fail-close in strict lanes.

### rq_013_protocol_feedback_atomic_emit_contract_v1

Required receipt fields:

- `transaction_id`
- `batch_ref`
- `index_ref`
- `receipt_ref`

Hard constraints:

1. Feedback emit must be atomic across batch/index/receipt.
2. Partial-write failure must rollback and emit deterministic failure code.

### rq_016_refresh_strict_business_interference_matrix_contract_v1

Required receipt fields:

- `refresh_receipt_ref`
- `strict_receipt_ref`
- `interference_row_count_refresh`
- `interference_row_count_strict`

Hard constraints:

1. Refresh and strict modes must both emit interference matrix receipts.
2. Missing either replay side invalidates closure.

### rq_023_discovery_dual_track_requiredization_activation_contract_v1

Required receipt fields:

- `requiredization_triggered`
- `trigger_classes`
- `required_contract_declared`
- `required_contract`
- `discovery_requiredization_status`

Hard constraints:

1. Requiredization must be trigger-conditioned (`not_triggered -> optional`, `triggered_no_apply -> fail-close`).
2. Trigger classification and requiredization status must be deterministic for same inputs.

### rq_024_discovery_apply_coverage_fail_closed_contract_v1

Required receipt fields:

- `discovery_required_total`
- `discovery_required_passed`
- `discovery_required_coverage_rate`
- `discovery_requiredization_status`
- `error_code`

Hard constraints:

1. Apply-time requiredization cannot pass with partial coverage.
2. Coverage mismatch must fail-close with canonical discovery error semantics.

### rq_025_kernel_canonical_source_contract_v1

Required receipt fields:

- `canonical_source_paths`
- `missing_source_paths`
- `kernel_ssot_source_status`
- `ssot_validator_rc`

Hard constraints:

1. Canonical kernel source set is fixed to protocol/runtime/mapping artifacts.
2. Any canonical source drift or missing path is fail-close.

### rq_026_kernel_contract_mapping_projection_contract_v1

Required receipt fields:

- `total_requirements`
- `p0_total`
- `p0_mapped`
- `p0_coverage_rate`
- `orphan_count`
- `unmapped_p0_requirements`

Hard constraints:

1. P0 mapping coverage target is `100%`.
2. Orphan mapping rows must be `0`.

### rq_028_instance_write_boundary_lock_contract_v1

Required receipt fields:

- `base_repo_write_boundary_status`
- `error_code`
- `violation_path`
- `normalized_violation_path`
- `evidence_ref`

Hard constraints:

1. Instance lanes must fail-close on protocol/governance/review write attempts.
2. Canonical boundary classification must stay deterministic across lanes.

### rq_029_semantic_single_source_convergence_contract_v1

Required receipt fields:

- `semantic_tuple_update`
- `semantic_tuple_three_plane`
- `semantic_tuple_full_scan`
- `mismatch_count`
- `mismatch_fields`

Hard constraints:

1. Same lineage must converge to identical semantic tuple across lanes.
2. Tuple mismatch is deterministic fail-close with canonical convergence error code.

### rq_032_headstamp_pre_send_hard_gate_contract_v1

Required receipt fields:

- `headstamp_status`
- `error_code`
- `evidence_ref`
- `actor_binding_ref`
- `reply_first_line_surface_mode`

Hard constraints:

1. Missing/malformed/mismatched headstamp must block outbound send.
2. Governed and direct/manual send paths must share canonical pre-send verdict semantics.
3. Raw canonical artifact validation must accept only a literal first line beginning with `Identity-Context:` and must classify that surface as `reply_first_line_surface_mode=raw_canonical`.
4. Governed host-visible validation MAY accept a first line beginning with `Display-Headstamp: Identity-Context: ... | Layer-Context: ...`, but only as `reply_first_line_surface_mode=visible_projection`; validators must canonicalize that visible projection back to the same underlying `Identity-Context` stamp before verdict.
5. Any other first-line surface is `reply_first_line_surface_mode=invalid` and is deterministic fail-close.
6. Visible-projection acceptance is additive only: it must not weaken raw canonical strictness and must not create a second authority source.

### rq_036_host_visible_post_check_next_hop_block_contract_v1

Required receipt/state fields:

- `host_transport_post_check_closure_state_file`
- `host_transport_post_check_state_write_status`
- `host_transport_post_check_block_on_active`
- `host_transport_post_check_blocker_active`
- `host_transport_post_check_closure_status`
- `host_transport_post_check_error_code`
- `reply_first_line_gate_executed`
- `send_time_block_stage`
- `reply_first_line_blocked_reason`

Hard constraints:

1. Host-visible transport attestation MUST persist a post-check closure state on every run.
2. Any write failure on closure state MUST fail-close with escalation-required semantics (`IP-PRIV-ESC-001` family).
3. In strict operations, send-time gate MUST read the post-check closure state before release.
4. If post-check closure state is missing/invalid/unreadable in strict operations, send-time MUST hard-block next hop (`FAIL_REQUIRED`).
5. If `block_on_active=true` and `blocker_active=true`, send-time MUST hard-block next hop (`FAIL_REQUIRED`).
6. This contract is control-plane level only: instance-local manual prefixing is not a valid substitute.
7. When strict send-time is blocked before first-line validator execution, payload MUST mark:
   - `reply_first_line_gate_executed=false`
   - `reply_first_line_status=SKIPPED_NOT_REQUIRED`
   - `send_time_block_stage=pre_first_line_post_check_*`
   and MUST NOT report synthetic first-line-missing evidence (`reply_first_line_missing_count=0`).
8. In strict scan orchestration, same-turn ordering MUST run host transport attestation before send-time gate evaluation when both are required.
9. In strict scan orchestration, tuple-bound post-check recovery MUST execute before host/send gates when blocker-active risk is present.

Operational recovery path (control-plane only):

1. If `host_transport_post_check_blocker_active=true` due stale/mismatched live receipts, recovery MUST use protocol toolchain, not manual state edits:
   - `scripts/recover_host_visible_post_check_state.py`
2. Recovery tool MUST:
   - reseed required host-visible channel receipts with explicit tuple (`actor_id/session_id/run_id`)
   - rewrite runtime state using same tuple
   - immediately rerun `validate_host_transport_wiring_attestation.py --require-live-receipts`
3. If live attestation does not return `PASS_REQUIRED`, recovery remains failed and next-hop strict block stays active.

Metrics (release gate thresholds):

1. `pre_send_gate_pass_rate >= 0.95`
2. `post_check_detectability_rate = 1.00` for injected negative probes.
3. `next_hop_block_rate = 1.00` after post-check blocker activation.
4. `false_green_rate = 0.00` for strict run-bound host-visible attestation.

Machine projection (required in strict scans):

1. `host_visible_post_check_metrics.host_visible_post_check_metrics_status`
2. `host_visible_post_check_metrics.metrics.*`
3. `host_visible_post_check_metrics.metric_statuses.*`

### rq_047_protocol_no_downgrade_motherline_contract_v1

Required receipt/state fields:

- `compatibility_legacy_boundary_status`
- `strict_actor_entry_semantics_status`
- `identity_switch_closure_status`
- `pointer_consistency`
- `compatibility_pointer_identity_authority`
- `violation_count`
- `violations`
- `stale_reasons`
- `error_code`

Hard constraints:

1. Active protocol surfaces must not downgrade themselves or provide downward/backward compatibility for lagging instances, historical residue, or scene-specific exceptions.
2. Compatibility, fallback, bridge, and legacy-overlay surfaces are forbidden on active defaults, active execution entry, validator green paths, current-turn runtime truth, and protocol-owned success paths.
3. Instance/workspace adoption debt must be closed by instance-owned upgrade, governed migration, or explicit repair; protocol success surfaces must not act as backstops.
4. When authoritative current-turn truth is missing or drifted, the only valid result is fail-close plus repair guidance; literal actor fallback, compatibility projection, legacy alias bridges, and workspace-local backstops must not reconstitute live truth.
5. Historical fixture/import material is allowed only as explicit non-runtime test/migration input and must not be promoted into green-path runtime semantics.
6. Any attempt to normalize downgrade/backstop behavior on active protocol surfaces is a deterministic protocol violation.

## Batch-6/7 anchor placeholders (v1.6 intake, non-promotional)

The following sections are **kernel anchor placeholders** for v1.6 Batch-6/7 mapping survivability.
They are intentionally non-promotional until corresponding runtime validators and replay evidence are
fully wired. Governance/review authority remains in:

- `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` (`8.10`, `8.11`)
- `docs/review/protocol-remediation-audit-ledger-v1.6.md` (`FIX16-035`, `FIX16-036`)

### rq_017_multi_track_cross_verification_contract_v1

Required receipt fields:

- `t1_status`, `t2_status`, `t3_status`, `t4_status`
- `cross_verification_bundle_id`
- `source_url_set`
- `reference_timestamp_utc`
- `conflict_reconciliation_note`

### rq_022_fallback_taxonomy_normalization_contract_v1

Required receipt fields:

- `fallback_reason_raw`
- `fallback_taxonomy_class`
- `taxonomy_version`
- `normalization_status`
- `normalization_error_code`

### rq_030_intake_evidence_quorum_contract_v1

Required receipt fields:

- `t1_roundtable_status`
- `t2_vendor_status`
- `t3_openai_context_status`
- `t4_protocol_spec_status`
- `cross_verification_bundle_id`
- `source_url_set`
- `reference_timestamp_utc`
- `conflict_reconciliation_note`
