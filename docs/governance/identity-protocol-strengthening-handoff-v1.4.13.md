# Identity Protocol Strengthening Handoff (v1.4.13)

Status: Canonical handoff summary (protocol-layer only)
Governance layer: protocol
Applies to: identity protocol base-repo architecture decisions only

This handoff note exists to keep index links stable and provide a concise execution bridge
between audit findings and implementation tasks in v1.4.13.

Execution directive (mandatory):

1. Execute protocol-strengthening items based on this handoff document only.
2. Any `artifacts/` mirror is evidence-only and must not be treated as normative source.
3. Core-change coupling scope is maintained in:
   - `docs/governance/templates/protocol-core-change-map.yaml`
   - update this map when protocol-core scope changes.

## Layered governance boundary (mandatory)

Protocol layer governance (this document scope):

1. Canonical SSOT/governance docs and templates under `docs/governance/`
2. Protocol validators under `scripts/validate_protocol_*` and protocol gate wiring in workflow/readiness/e2e/three-plane
3. Protocol-safe defaults and boundary contracts (no business-scene coupling)

Identity instance governance (explicitly out of scope here):

1. Runtime instance behavior in `CURRENT_TASK.json`, `IDENTITY_PROMPT.md`, `RULEBOOK.jsonl`
2. Roundtable/collaboration style, vendor-specific operation style, and per-instance execution routing preferences
3. Business-task artifacts and instance-local retros

Cross-layer interface rule:

1. Protocol layer defines machine-checkable contracts and gates.
2. Instance layer implements behavior within those contracts.
3. Instance-specific policy must not be promoted into protocol mandatory gates without explicit protocol review.

## Scope guardrails

1. Protocol layer only (no business-scene coupling)
2. No user-specific absolute path as normative requirement
3. No default-identity hardcoding in protocol-critical gates
4. Recoverable blocked states remain fail-operational; hard boundaries remain fail-closed

## Repository path governance matrix (mandatory)

This section normalizes the repository paths highlighted in protocol audits and defines their governance layer and coupling mode.

1. `identity/`
   - `identity/catalog/**` and `identity/protocol/**` are protocol-governed assets.
   - `identity/store-manager/**` and `identity/packs/**` are protocol baseline/example identities; changes must preserve protocol-level non-hardcoded semantics.
   - `identity/runtime/**` is runtime evidence/artifact surface and remains non-normative.
2. `skills/`
   - Protocol-adjacent capability packs; changes are allowed but must not introduce protocol hard requirements unless promoted through protocol review.
3. `README.md`
   - Operator-facing protocol entry; contract-level changes must stay aligned with canonical handoff and validator command set.
4. `CHANGELOG.md`
   - Release traceability ledger; significant protocol-core changes require changelog linkage, but changelog edits alone do not define protocol contract.
5. `VERSIONING.md`
   - Version/governance semantics for protocol release policy; edits are protocol governance changes and must remain consistent with canonical handoff.
6. `requirements-dev.txt`
   - Toolchain dependency baseline for local audit parity; updates require preflight/readiness replay evidence.

## Canonical references

- `docs/governance/identity-base-protocol-runtime-retro-and-governance-feedback-v1.4.13.md`
- `docs/governance/identity-environment-path-deep-audit-and-self-drive-upgrade-v1.4.13.md`
- `docs/governance/identity-token-efficiency-and-skill-parity-governance-v1.4.13.md`
- `docs/governance/identity-token-governance-audit-checklist-v1.4.13.md`
- `docs/governance/templates/protocol-p1-followup-issue-pack-v1.4.13.md` (copy-ready architect issue templates for P1 hardening)

## Architect execution bundle (single-send)

Use this bundle in order to avoid interpretation drift:

1. Canonical directive: this handoff (`identity-protocol-strengthening-handoff-v1.4.13.md`)
2. P1 copy-ready templates: `docs/governance/templates/protocol-p1-followup-issue-pack-v1.4.13.md`
3. Core-change coupling scope: `docs/governance/templates/protocol-core-change-map.yaml`
4. Validation replay commands: "Required validation command set" section below

Required architect reply format:

1. commit sha list
2. changed file list
3. acceptance command outputs (per issue / per gate)
4. residual risks + next milestone

## Document lifecycle governance (mandatory)

Operational axiom:

`SSOT + gate binding + periodic archive`

Lifecycle rules:

1. Each protocol topic has one canonical governance entry document.
2. New governance docs must bind to at least one gate or validator; otherwise classify as evidence-only/archive.
3. Template docs stay under `docs/governance/templates/` and must be referenced by canonical documents.
4. Keep active governance set lean; periodically archive outdated snapshots to avoid protocol-doc sprawl.

## v1.4.13 implementation highlights (landed)

1. capability blocked/arbitration/report linkage hardening
2. canonical session pointer consistency + activation rollback semantics
3. repo/runtime path boundary hardening and fallback explicitization
4. dialogue governance validator chain (contract-first, optional, warn/enforce)
5. required-gates / e2e / readiness / three-plane integration

## Required validation command set

Run environment preflight first (toolchain + auth readiness visibility):

```bash
bash scripts/preflight_protocol_audit_env.sh
```

For release-grade strict profiles that require GitHub capability auth readiness:

```bash
bash scripts/preflight_protocol_audit_env.sh --require-gh-auth
```

Notes:

1. If `gh auth` is not ready, strict-union readiness may fail with `IP-CAP-003`.
2. This is an environment-auth state, not a protocol-regression signal.
3. Local protocol-gate replay can still proceed without `--require-gh-auth`.

```bash
python3 scripts/validate_identity_protocol.py
python3 scripts/validate_identity_local_persistence.py
python3 scripts/validate_identity_creation_boundary.py
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_release_workspace_cleanliness.py
python3 scripts/validate_protocol_ssot_source.py
python3 scripts/validate_protocol_handoff_coupling.py --base HEAD~1 --head HEAD
```
