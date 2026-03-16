# Identity Runtime Path Residue Governance v1.6.11

## Scope

This governance closes a recurring attribution gap:

1. Historical evidence trees (`runtime/reports`, `sanitization-backups`) were sometimes scanned as live control-plane inputs.
2. Legacy literals like `.agents/identity` inside archival files triggered false P0 classification.
3. Teams then mixed protocol-side and instance-side ownership.

This document defines a fail-close triage baseline that is control-plane only.

## Canonical Scanner

Use `scripts/scan_identity_path_residue.py`.

### Included Control-Plane Surfaces

1. `catalog.local.yaml`
2. `CURRENT_TASK.json`
3. `IDENTITY_PROMPT.md`
4. `META.yaml`
5. `runtime/state/**/*`
6. `runtime/plugins/**/*`
7. `runtime/gate/**/*`

### Excluded Non-Normative Surfaces

1. `runtime/reports/**/*`
2. `**/sanitization-backups/**/*`
3. `**/*.bak*`

## Classification Contract

1. `path_residue_status=PASS_REQUIRED` on scoped control-plane files means no active runtime residue.
2. Residues found only in excluded surfaces are informational, not protocol blocker.
3. P0 protocol ownership requires proof on included control-plane surfaces or transport gate failures.
4. If scoped scan passes and headstamp still drops, classify as instance-governance issue by default.

## Required Metrics

Every triage batch must persist:

1. `scanned_file_count`
2. `hit_count`
3. `total_match_count`
4. `path_residue_status`
5. `identity_home`

## Operational Examples

```bash
python3 scripts/scan_identity_path_residue.py \
  --repo-root /path/to/repo \
  --identity-id feiqiao-guard-delivery-lead \
  --json-only
```

```bash
python3 scripts/scan_identity_path_residue.py \
  --repo-root /path/to/repo \
  --identity-id feiqiao-guard-delivery-lead \
  --apply \
  --json-only
```

## Ownership Boundary

1. Protocol-side: maintain scanner contract and exclusion rules.
2. Instance-side: fix runtime bridge/emitter behavior when scoped scanner passes but live headstamp fails.
3. Protocol will not claim instance-side bridge regressions as protocol-base defects without cross-instance proof.
