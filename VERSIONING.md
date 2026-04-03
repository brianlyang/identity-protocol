# Versioning Policy

This repository uses semantic versioning for protocol releases:
- MAJOR: breaking protocol contract changes
- MINOR: backward-compatible additions
- PATCH: fixes and clarifications

## Stable baseline

- `v1.0.0` is the first stable baseline.
- `v1.x` must preserve the frozen required contract in:
  - `docs/specs/identity-protocol-contract-v1.0.0.md`

## Compatibility

Consumer repositories should pin a release tag and upgrade intentionally.

### Required compatibility promises in v1.x

- Required catalog fields stay backward compatible.
- Required runtime keys in `CURRENT_TASK.json` stay backward compatible.
- Core compile/validate scripts remain functionally available.

### Breaking changes

Any breaking change to required contract must bump MAJOR (`v2.0.0`).

## Stream-number discipline for `v1.x.y` governance/review lanes

Patch-numbered governance/review documents are not freeform “documentation
supplement” buckets. In this repository, a `v1.x.y` stream number denotes a
bounded protocol-owner stream.

Opening a new `v1.x.y` stream therefore requires, at minimum:

1. one bounded protocol problem statement or strengthening target,
2. one canonical governance doc plus one canonical review ledger,
3. one stream-doc-registry entry,
4. one workbook issue row or equivalent owner-scope traceability surface,
5. explicit non-goal boundaries, and
6. an explicit statement of whether the stream is:
   - docs-first / governance-first and awaiting later machine landing, or
   - already machine-consumed through validators / probes / gates.

This rule exists to prevent misuse of patch stream numbers as:

- ad hoc doc补充 / documentation supplements,
- loose commentary bundles,
- unscoped truth-sync notes,
- or retrospective narrative dumps with no bounded owner lane.

If the work is only explanatory, reference-atlas, release-summary, or truth-sync
inside an already-open stream, it must land under the existing stream/workbook/
reference surfaces rather than minting a new `v1.x.y` number.

## Non-versioned protocol-root interpretive documents

This repository also allows a second, separate document class:

- non-versioned protocol-root interpretive sources under `identity/protocol/*.md`

These are **not** `v1.x.y` stream docs. They exist to anchor bottom-layer
protocol philosophy, meta-principles, or root explanatory semantics that sit
above individual stream-owner lanes.

To be valid, a protocol-root interpretive doc must:

1. live under `identity/protocol/`,
2. be explicitly anchored from `IDENTITY_PROTOCOL.md` and/or
   `IDENTITY_RUNTIME.md`,
3. declare that it is interpretive / explanatory rather than a direct
   machine-consumed contract row,
4. avoid masquerading as a validator schema, gate profile, mapping row, or
   runtime success-path artifact sink, and
5. avoid minting a fake `v1.x.y` stream number unless it truly opens a bounded
   new protocol-owner stream.

In short:

- `v1.x.y` = bounded stream-owner governance/review lane
- `identity/protocol/*.md` (non-versioned) = protocol-root interpretive source

## Minimum release checklist

- protocol docs updated
- registry/schema compatibility reviewed
- creator scripts validated
- dependency baseline reviewed (`requirements-dev.txt`)
- migration note included if behavior changes
- changelog updated
- changelog gate passed in CI (`validate_changelog_updated.py`)
- release tag created

## Release metadata synchronization (v1.6.14+)

To avoid “code merged but release metadata stale”, every protocol-impacting
change must keep the following files aligned:

1. `CHANGELOG.md` (what changed)
2. `VERSIONING.md` (how release policy applies)
3. `requirements-dev.txt` (whether dependency baseline changed)

If dependency set is unchanged, keep `requirements-dev.txt` intact but treat it
as explicitly reviewed during release closure.

### Enforcement note

Release closure is considered incomplete when any of the three synchronization
files is stale, even if feature code is already merged.

The draft head marker tracks the current protocol execution baseline and may be
newer than the latest tagged release snapshot recorded below.

## Current formal release snapshot (v1.5.1)

- Current production-facing release tag: `v1.5.1`
- Release target branch: `main`
- Release-aligned commit: `5d562a0ae1f785102f2d4001583545969ff215c1`
- Required cloud gate closure evidence:
  - workflow: `identity-protocol-ci`
  - run-id: `22708478725`
  - required check: `required-gates / validate-identity = success`

## Full-Go declaration rule (mandatory)

For v1.5.x and later:

- If cloud `required-gates` has no latest green run-id for the release head,
  status must remain **Conditional Go**.
- `Full Go` is allowed only when:
  1) local acceptance chain passes, and
  2) cloud `required-gates` passes on the same release head.
