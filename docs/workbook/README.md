# Protocol Workbook Control Plane

Status: Active guidance
Layer: protocol
Scope: canonical `docs/workbook/` directory contract for cross-stream issue governance

## Current control-plane alias refs

- `identity/protocol/mappings/workbook-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`

## Fixed role

1. `docs/workbook/` is the only canonical directory for protocol-side cross-stream issue governance.
2. Workbook documents are minor-family scoped:
   - `protocol-issue-register-v1.6.md`
   - `protocol-deep-audit-workbook-v1.6.md`
3. Stream-owner governance and review remain patch-scoped under:
   - `docs/governance/*-v1.6.x.md`
   - `docs/review/*-v1.6.x.md`

## Migration note

1. The current `v1.6` workbook pair migrates the earlier issue-routing material that previously lived outside the protocol base repo.
2. Those older outer-workspace files are no longer authoritative for protocol truth.
3. If mirrors are still kept for audit export, they are projection-only and must not be used by validators as default inputs.

## Total contract

1. The workbook control plane is the governed bundle of:
   - `docs/governance/identity-workbook-governance-v1.6.md`,
   - `identity/protocol/mappings/workbook-registry.current.yaml`,
   - `identity/protocol/mappings/workbook-registry.v1.6.yaml`,
   - `docs/workbook/templates/README.md`,
   - `docs/workbook/templates/protocol-issue-register.template.md`,
   - `docs/workbook/templates/protocol-deep-audit-workbook.template.md`,
   - `docs/workbook/protocol-issue-register-v1.6.md`,
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`,
   - `scripts/validate_issue_register_consistency.py`,
   - `scripts/scaffold_workbook_family.py`,
   - `scripts/validate_workbook_family_contract.py`,
   - `scripts/render_active_workbook_projections.py`.
2. `identity/protocol/mappings/workbook-registry.v1.6.yaml` selects the authority pair and declares any optional workspace projection exports.
3. External projections may exist for operator convenience, but current status authority remains inside `identity-protocol-local/docs/workbook/`.
4. If an external projection is kept, regenerate it through `scripts/render_active_workbook_projections.py`; do not hand-edit projection mirrors.
5. The active `v1.6` family keeps those projections in boundary-only mode, so stale outer mirror counts do not decide protocol release gates.

## Template lane

1. `docs/workbook/templates/` freezes the workbook-family scaffold source for future minors.
2. `scripts/scaffold_workbook_family.py` renders future family docs and registry files without switching the active current pointer by default.
3. `scripts/validate_workbook_family_contract.py` is the scaffold validator for non-active families and complements the active-family validator.

## Minor-vs-patch rule

1. `workbook = X.X`
2. `governance/review = X.X.X`
3. Do not mix these layers by attaching workbook control-plane meaning to one specific patch lane such as `v1.6.14`.
