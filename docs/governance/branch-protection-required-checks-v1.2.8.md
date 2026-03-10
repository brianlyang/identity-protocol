# Branch protection required checks (v1.2.8)

> Migration notice (v1.6.3 stream): this file is an operator checklist mirror.
> During GitHub-native control-plane migration, normative policy source is:
> 1) repository rulesets (platform state), and
> 2) `identity/protocol/mappings/github-control-plane-offload.current.yaml` (protocol migration SSOT).
> If checklist wording conflicts with ruleset+mapping state, treat this file as stale and follow ruleset+mapping.

## Purpose

Ensure identity protocol gates cannot be bypassed by merge settings drift.

## Required checks to enforce on `main`

In GitHub repository settings:

- Settings -> Branches -> Branch protection rules -> `main`
- Enable **Require status checks to pass before merging**
- Add required checks:
  - `protocol-ci / required-gates`
  - `identity-protocol-ci / required-gates`

> Note: exact check display names come from workflow + job names. If GitHub UI displays variants, select both CI workflows' `required-gates` job entries.

## Why both checks

- `protocol-ci` covers full-repo changes.
- `identity-protocol-ci` is scoped by identity-related paths for fast feedback and anti-drift isolation.

Keeping both as required blocks accidental merges when one workflow is skipped.

## Audit checklist

For every governance audit:

1. Open branch protection settings for `main`
2. Confirm required checks list includes both entries
3. Confirm **Require branches to be up to date before merging** is enabled
4. Confirm direct pushes to `main` are restricted as policy requires

If any check is missing, treat as `HIGH` risk and remediate before merge window opens.
