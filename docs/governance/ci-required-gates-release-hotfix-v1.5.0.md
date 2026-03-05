# Governance Addendum: required-gates CI release hotfix (v1.5.0)

Date: 2026-03-04
Scope: main release lane

## Governance intent

Ensure release lane CI remains fail-closed for protocol changes while avoiding setup-time false failures caused by invalid external action references or shell lint anti-patterns.

## Enforced corrections

1. Workflow lint action must reference an existing immutable upstream tag.
2. Shell command snippets in CI workflows must satisfy actionlint/shellcheck (including SC2012 avoidance).
3. Significant CI workflow changes must be reflected in `CHANGELOG.md`.
4. Fixture identities in CI must remain inspection-only for actor/session binding gates.
5. Required runtime contract validators must support both pack-local and repository-relative fixture evidence/rulebook paths.
6. Protocol-core script/workflow changes must co-change canonical handoff in the same diff range.
7. Cross-actor isolation gate must skip strict enforcement when the catalog has no active identities.

## Implementation evidence

- Commit `37273f6`
- Commit `f24a83f`
- Commit `5be9dc8`
- Commit `7fdfdd1`
- Commit `2ad0b4a`

## Status

Implementation completed; awaiting fresh workflow run confirmation on `main`.
