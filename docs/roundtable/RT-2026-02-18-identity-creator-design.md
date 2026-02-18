# Roundtable Record: Identity-Creator Design

Date: 2026-02-18

## Participants (role simulation)
- Architecture lead
- Reliability lead
- Ops lead
- Standards lead

## Decisions
1. Identity remains first-class control plane parallel to skills/MCP.
2. Keep native-vs-extension boundary explicit.
3. Add deterministic compile and validate scripts.
4. Preserve historical discussions for auditability.

## Risks and controls
- Path resolution breakage -> path check script in consumer repo.
- Runtime drift -> compile + diff guard.
- Layer confusion -> explicit conflict priority in protocol docs.
