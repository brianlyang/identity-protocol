# Workbook Family Templates

Status: Active template control plane
Layer: protocol
Scope: template and scaffold contract for future workbook families under `docs/workbook/`

## Current control-plane alias refs

- `identity/protocol/mappings/workbook-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`

## Fixed role

1. These template files are part of the `v1.6` workbook control plane and remain protocol-owned infrastructure, not ad hoc operator notes.
2. `protocol-issue-register.template.md` defines the canonical scaffold shape for future `protocol-issue-register-<minor>.md` families.
3. `protocol-deep-audit-workbook.template.md` defines the canonical scaffold shape for future `protocol-deep-audit-workbook-<minor>.md` families.
4. `scripts/scaffold_workbook_family.py` is the only supported generator for new workbook families.
5. `scripts/validate_workbook_family_contract.py` is the machine contract for generated family scaffolds before activation.

## Activation boundary

1. Template files are never current-status authority by themselves.
2. Generated workbook families remain scaffold-only until `identity/protocol/mappings/workbook-registry.current.yaml` is switched explicitly.
3. External projection stubs generated from these templates remain projection-only and do not participate in status authority before activation/backfill.
