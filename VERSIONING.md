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

## Minimum release checklist

- protocol docs updated
- registry/schema compatibility reviewed
- creator scripts validated
- dependency baseline reviewed (`requirements-dev.txt`)
- migration note included if behavior changes
- changelog updated
- changelog gate passed in CI (`validate_changelog_updated.py`)
- release tag created

## Release metadata synchronization (v1.4.3+)

To avoid “code merged but release metadata stale”, every protocol-impacting
change must keep the following files aligned:

1. `CHANGELOG.md` (what changed)
2. `VERSIONING.md` (how release policy applies)
3. `requirements-dev.txt` (whether dependency baseline changed)

If dependency set is unchanged, keep `requirements-dev.txt` intact but treat it
as explicitly reviewed during release closure.
