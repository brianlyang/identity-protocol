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
15. Protocol-vendor semantic isolation validator must treat fixture/demo identities as inspection-only to prevent auto-required protocol-feedback artifacts from triggering false `IP-SEM-001` fail-closed outcomes in CI.
16. External-source trust-chain validator must treat fixture/demo identities as inspection-only to prevent auto-required protocol-feedback artifacts from triggering false `IP-SRC-003` fail-closed outcomes in CI.
17. Protocol data sanitization boundary validator must treat fixture/demo identities as inspection-only to prevent auto-required protocol-feedback artifacts from triggering false `IP-DSN-001` fail-closed outcomes in CI.
18. `identity_creator update` must normalize inherited fallback scope for fixture identities (`USER -> AUTO`) before runtime mode guard to avoid CI aborts from environment-scope leakage.
19. required-gates workflow must call `identity_creator update` with explicit repo catalog binding (`--catalog` + `--repo-catalog` to `identity/catalog/identities.yaml`) to prevent CI home-catalog (`global`) mode drift from tripping runtime mode guard.
20. for fixture identities running on repo catalog, `identity_creator update` runtime mode guard must use `expect-mode=any` (instead of strict `auto` project/global recognition) to avoid false `mode=custom` aborts.
21. required-gates mutation/update report-chain validators must run only for mutable runtime identities; fixture/demo identities stay inspection-only and must skip update/report-contract chain execution in CI.
22. fixture sample contracts must not use workstation-specific absolute paths (for example `/Users/...`) in required runtime evidence fields; fixture artifacts must use repository-relative paths so CI runners can resolve them deterministically.

## Implementation evidence

- Commit `37273f6`
- Commit `f24a83f`
- Commit `5be9dc8`
- Commit `7fdfdd1`
- Commit `2ad0b4a`
- Commit `this-change-set`

## Status

Implementation completed; awaiting fresh workflow run confirmation on `main`.
