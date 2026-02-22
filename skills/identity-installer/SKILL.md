# Identity Installer Skill

Use this skill when the request is about **installing / reinstalling / verifying / rolling back identity packs** in local runtime.

## Scope
- installer-plane only (distribution & install safety)
- non-destructive local upgrades by default
- generate install provenance reports for audit

## Must-follow flow
1. `plan` (or `dry-run`) first
2. evaluate conflict type:
   - `same_signature` -> `no_op_with_report`
   - `compatible_upgrade` -> `abort_and_explain` (default non-destructive policy)
   - `destructive_replace` -> backup + rollback ref required
3. run `install` only after dry-run is acceptable
4. run `verify`
5. ensure reports exist under:
   - `identity/runtime/reports/install/identity-install-<identity-id>-*.json`
   - mirror sample: `identity/runtime/examples/install/install-report-*-<identity-id>.json`

## Commands
- `python3 scripts/identity_installer.py plan --identity-id <id>`
- `python3 scripts/identity_installer.py dry-run --identity-id <id>`
- `python3 scripts/identity_installer.py install --identity-id <id> --register --activate`
- `python3 scripts/identity_installer.py verify --identity-id <id>`
- `python3 scripts/identity_installer.py rollback --identity-id <id> --rollback-ref restore_from:<backup_path>`

## Output contract
- Always return:
  - report path
  - conflict_type
  - action
  - preserved_paths
  - backup_ref/rollback_ref (if replace path touched)
