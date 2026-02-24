# Audit Snapshot — 2026-02-24 — Release Documentation Governance Closure (v1.4.12)

## Snapshot type
- Governance closure snapshot (documentation-first release control)
- Scope: release review entrypoints, audit evidence routing, repository source-of-truth boundary

## Unified verdict
- Code-plane: **Go (local)**
- Release-plane: **Conditional Go** (requires cloud required-gates run-id closure on the same release head)

## Why this snapshot exists
This release cycle introduced many runtime/scope/self-heal/permission-state changes.
Without a strict documentation closure set, teams can pass local tests but still diverge in release understanding.
This snapshot locks the **mandatory governance document set** and the **single audit repository boundary**.

## Mandatory documentation set for release closure (must be updated in same batch)
1. `README.md`
2. `CHANGELOG.md`
3. `VERSIONING.md`
4. `requirements-dev.txt`
5. `identity/protocol/IDENTITY_PROTOCOL.md`
6. `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
7. this snapshot file

## Repository source-of-truth boundary
- Release/audit source-of-truth repository:
  - `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local`
- Non-release working repositories (for experiments/regression scratch) must not be used as release evidence source.
- Reviewers must verify current working directory before running any release-gate command:

```bash
cd /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local
pwd
git rev-parse --abbrev-ref HEAD
```

## Required review sequence (documentation-centered)
1. Read `README.md` release posture + minimum acceptance commands.
2. Read `CHANGELOG.md` Unreleased section for implemented gates and deferred items.
3. Read `identity/protocol/IDENTITY_PROTOCOL.md` for enforceable contract language.
4. Read latest audit snapshot entries from `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
5. Run release-readiness/e2e commands and attach outputs to audit record.

## Release command evidence (minimum)
```bash
python3 scripts/identity_creator.py validate --identity-id office-ops-expert --catalog "${IDENTITY_HOME}/catalog.local.yaml"
python3 scripts/validate_identity_local_persistence.py --runtime-mode
python3 scripts/release_readiness_check.py --identity-id office-ops-expert --base HEAD~1 --head HEAD
IDENTITY_IDS=office-ops-expert bash scripts/e2e_smoke_test.sh
python3 scripts/validate_identity_instance_isolation.py --catalog "${IDENTITY_HOME}/catalog.local.yaml" --identity-id office-ops-expert
```

## Governance hard constraints
1. Before all minimum commands PASS and cloud required-gates are green on release head:
   - status must remain `Conditional Go`.
2. `DEFERRED_PERMISSION_BLOCKED` is recovery-only and cannot satisfy release gate.
3. Runtime evidence/sample/log paths must remain identity-scoped; cross-identity hits are fail conditions.

## Auditor handoff note
This snapshot is intended as the anchor document for roundtable review, postmortem, and release sign-off.
All closure claims should reference this file plus concrete command outputs and run-id URLs.
