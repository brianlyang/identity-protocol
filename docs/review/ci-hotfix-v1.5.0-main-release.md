# CI Hotfix Receipt (v1.5.0 main release)

Date: 2026-03-04

## Problem

`identity-protocol-ci / required-gates / validate-identity` failed on main release pushes.

## Root causes

1. Workflow used non-existent action reference `rhysd/actionlint@v1`.
2. After pinning actionlint, shellcheck rule `SC2012` failed due `ls`-based file selection in `.github/workflows/_identity-required-gates.yml`.
3. Changelog gate required `CHANGELOG.md` update for significant workflow changes.

## Fixes applied

- `37273f6` — pin actionlint to `rhysd/actionlint@v1.7.11`.
- `f24a83f` — replace `ls` usage with `find + sort` and fail-closed empty-report guard.
- `5be9dc8` — add changelog entry for the CI hotfix.

## Failing run references

- 22662666987
- 22663308352
- 22663774209

## Release note

This receipt is documentation-only and does not alter protocol semantics.
