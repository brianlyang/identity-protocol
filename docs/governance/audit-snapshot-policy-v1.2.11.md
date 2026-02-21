# Audit Snapshot Policy (v1.2.11)

## Purpose

Make audit closure and post-audit optimization traceable, replayable, and review-efficient.

Audit snapshot is now a **fixed governance action** after every major audit cycle.

---

## Mandatory rule

After each audit cycle (including follow-up fixes), maintainers MUST add one snapshot file:

- `docs/governance/audit-snapshot-YYYY-MM-DD.md`

A cycle is considered complete only when:

1. findings are mapped to concrete PRs/commits
2. status is updated per finding (closed / partially mitigated / open)
3. residual risk and next actions are recorded

In addition, for **every protocol version upgrade** (including minor/patch upgrades):

4. one extension cross-validation archive is added/updated under `docs/references/`
5. non-conflict mapping to `IDENTITY_PROTOCOL.md` four-core capabilities is documented
6. review evidence explicitly cites both skill and MCP collaboration references

---

## Required content (minimum)

Each snapshot MUST include:

1. scope and audit date
2. baseline source references (protocol + skill + mcp/tool boundaries)
3. findings register (severity, owner, status)
4. remediation mapping table (finding -> PR -> commit -> validator/workflow evidence)
5. residual risks and compensating controls
6. branch protection status check (manual UI confirmation)
7. operational SLA status (e.g., fresh handoff logs)
8. route-quality metrics trend (hit/misroute/fallback)
9. next audit window and trigger conditions
10. extension non-conflict statement (core capability invariant preserved)
11. cross-validation evidence links:
   - skill protocol lifecycle reference
   - skill/MCP/tool collaboration reference
   - identity protocol/runtime baseline files

---

## Update cadence

- Mandatory on each major audit closure
- Recommended weekly light snapshot when active hardening is ongoing

---

## Review efficiency goal

A new reviewer should be able to restore context in under 10 minutes by reading:

1. `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
2. latest `audit-snapshot-*.md`
3. linked PRs and validators

---

## Non-compliance handling

If snapshot is missing for a completed hardening cycle:

- mark governance status as incomplete
- block final closure announcement
- require backfill snapshot before next release window

If version upgrade is merged without cross-validation archive and non-conflict mapping:

- mark release governance as drift-risk
- require immediate follow-up PR to add missing evidence
- treat missing cross-validation as blocker for next upgrade window
