# CI Hotfix Receipt (v1.5.0 main release)

Date: 2026-03-04

## Problem

`identity-protocol-ci / required-gates / validate-identity` failed on main release pushes.

## Root causes

1. Workflow used non-existent action reference `rhysd/actionlint@v1`.
2. After pinning actionlint, shellcheck rule `SC2012` failed due `ls`-based file selection in `.github/workflows/_identity-required-gates.yml`.
3. Changelog gate required `CHANGELOG.md` update for significant workflow changes.
4. Fixture identities regressed under required runtime gates due pack-local-only path resolution and strict USER-scope assumptions.
5. Actor-session strict gates treated fixture identities as mutable runtime identities in CI.
6. Cross-actor isolation strict gate rejected fixture-only catalogs with no active identities.
7. Protocol handoff coupling gate required canonical handoff update whenever protocol-core scripts/workflow changed.
8. Session refresh strict gate flagged fixture identities with false `IP-ASB-RFS-002` failures in CI.

## Fixes applied

- `37273f6` — pin actionlint to `rhysd/actionlint@v1.7.11`.
- `f24a83f` — replace `ls` usage with `find + sort` and fail-closed empty-report guard.
- `5be9dc8` — add changelog entry for the CI hotfix.
- `7fdfdd1` — restore fixture compatibility in required runtime gates:
  - runtime contract evidence/rulebook fallback resolution
  - prompt quality scope auto arbitration
  - role-binding evidence fallback and fixture sample freshness alignment
  - fixture blocker taxonomy alias bridge normalization
- `2ad0b4a` — canonical handoff addendum to satisfy protocol-core coupling.

## Failing run references

- 22662666987
- 22663308352
- 22663774209
- 22664039042
- 22664484023
- 22700873854

## Release note

This receipt is documentation-only and does not alter protocol semantics.
