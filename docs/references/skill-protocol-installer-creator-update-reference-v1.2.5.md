# Skill Protocol Reference: Installer vs Creator vs Update Lifecycle (v1.2.5)

This reference is added as a **review baseline artifact** for identity protocol maintainers.

It translates proven skill mechanics into identity-governance language so identity evolution can stay deterministic and auditable.

## 1) Responsibility split (must not mix)

### skill-installer (distribution plane)

Responsibilities:
- list installable skills from curated/remote sources
- install a selected skill into local skill directory
- support install from GitHub path/repo

Non-responsibilities:
- does not define skill quality
- does not define skill workflow correctness
- does not define business policy

### skill-creator (authoring plane)

Responsibilities:
- create/update skill package structure (`SKILL.md`, `scripts/`, `references/`, `assets/`)
- define trigger semantics and usage boundaries
- maintain quality gates and post-update validation

Non-responsibilities:
- does not act as package installer
- does not bypass runtime governance constraints

## 2) Skill update lifecycle (canonical chain)

A stable skill update follows this chain:

1. trigger (why update is required)
2. patch surface (what files are changed)
3. validation (what checks must pass)
4. replay/regression (original failing prompt/task must be rerun)

This exact chain is now mirrored by identity update contract (`v1.2.4+`).

## 3) Trigger stability model (must test explicitly)

For every update, run trigger regression in three buckets:

- positive: should trigger
- boundary: context-dependent/adjacent cases, should route deterministically
- negative: should not trigger

Why this matters:
- prevents silent over-triggering
- prevents under-triggering after refactors
- keeps behavior stable across wording variations

## 4) Mapping from skill mechanics to identity protocol

- skill metadata trigger discipline -> identity routing + trigger regression contract
- skill update chain -> identity update lifecycle contract
- skill validation + replay -> identity validators + same-case replay requirement
- skill creator/operator clarity -> identity-creator update-operation contract

## 5) Required review checkpoints before identity capability decisions

When changing identity capability/routing/governance:

1. review `identity/protocol/IDENTITY_PROTOCOL.md`
2. review this reference file
3. review OpenAI Codex skills docs
4. review Agent Skills specification
5. review MCP specification

Review evidence must be recorded per `protocol_review_contract`.

## 6) Maintainer checklist

- [ ] update trigger condition is explicit
- [ ] patch surface includes runtime/prompt/rulebook/history
- [ ] validators are wired in CI/e2e
- [ ] positive/boundary/negative trigger suites are present
- [ ] replay of original failing case is executed and recorded
- [ ] review evidence cites baseline protocol sources
