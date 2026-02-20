# Skill Installer / Skill Creator / Skill Update Lifecycle (Canonical Reference)

> This file is the canonical reference name for review and audit.
> Detailed content is kept aligned with:
> `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`

## Purpose

Provide a stable, explicit, non-ambiguous reference path for the three core skill mechanisms:

1. installation (`skill-installer`)
2. creation/authoring (`skill-creator`)
3. update lifecycle (trigger -> patch -> validate -> replay)

## Required review points

- installer and creator responsibilities must remain separated
- update must follow trigger/patch/validate/replay
- trigger regression must include positive/boundary/negative suites
- updated skill must pass structure + resource + trigger + smoke validation
- when multi-runtime distribution is needed, installer path must complete re-install/reload

## Operational rule

For reviewers and identity-upgrade maintainers, read this file first, then the detailed versioned reference file.
