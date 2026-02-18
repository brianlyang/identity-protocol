# Identity Catalog Change Audit Template

Use this template for every change to `identity/catalog/identities.yaml`.

## Change metadata
- Date:
- Author:
- Reviewer:
- Change ticket / issue:
- Target release tag:

## Scope
- Changed field(s):
- Affected identity id(s):
- default_identity changed? (yes/no):

## Rationale
- Why this change is needed:
- Business and operational impact:
- Risk level (low/medium/high):

## Contract impact
- Schema compatibility impact (none/additive/breaking):
- Runtime behavior impact:
- Guardrail impact:
- Escalation policy impact:

## Verification evidence
- [ ] `python scripts/validate_identity_protocol.py` passed
- [ ] `python scripts/compile_identity_runtime.py` passed
- [ ] runtime brief diff reviewed
- [ ] consumer integration checklist reviewed

Evidence paths/links:
- validation output:
- compile output:
- runtime brief diff:

## Rollback plan
- Revert commit/tag:
- Rollback command:
- Rollback validation steps:
