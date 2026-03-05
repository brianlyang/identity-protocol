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
8. Session refresh gate must skip strict enforcement for fixture/demo-only identities.
9. Send-time reply gate must skip strict synthetic-evidence enforcement for fixture/demo-only identities.
10. Trigger-regression report discovery must support fixture repository-runtime fallback when pack-local samples are absent.
11. Learning-loop validator must support fixture repository-runtime fallback for run-report and rulebook references.
12. Collaboration-trigger validator must avoid cross-identity glob contamination and skip fixture stale-age enforcement.
13. Agent-handoff validator must scope evidence logs to target identity and treat fixture log freshness as inspection-only to avoid stale fixture false failures in CI.
14. `identity_creator update` must not hard-code `USER` scope in CI paths; default scope must allow catalog-driven arbitration (`${IDENTITY_SCOPE:-""}`) to avoid fixture/system scope false blocks.

## Implementation evidence

- Commit `37273f6`
- Commit `f24a83f`
- Commit `5be9dc8`
- Commit `7fdfdd1`
- Commit `2ad0b4a`
- Commit `this-change-set`

## Status

Implementation completed; awaiting fresh workflow run confirmation on `main`.
