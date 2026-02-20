# Skill Protocol Reference: Installer vs Creator vs Update Lifecycle (v1.2.5)

This reference is a **baseline review artifact** for identity protocol maintainers.

It captures skill protocol mechanics in a way identity maintainers can reuse directly, instead of inventing ad-hoc naming or ad-hoc flows.

---

## 1) Strict role split: installer vs creator

### 1.1 skill-installer (distribution plane)

Use when the task is:
- list installable skills
- install/reinstall a skill to local runtime
- install from curated source or GitHub path/repo

Responsibilities:
- fetch/install package into local skills directory
- handle installation source selection
- support re-install in target runtime

Non-responsibilities:
- no authoring of skill semantics
- no business workflow design
- no quality policy definition

### 1.2 skill-creator (authoring plane)

Use when the task is:
- create a new skill
- update existing skill behavior/structure/trigger semantics
- add scripts/references/assets and validate quality

Responsibilities:
- maintain `SKILL.md` trigger + execution semantics
- maintain `scripts/`, `references/`, `assets/`, optional UI metadata files
- define post-update validation and replay tests

Non-responsibilities:
- no package distribution/install orchestration
- no bypass of runtime governance contracts

**Operational summary**:
- content changes: creator path
- distribution to target runtime: installer path

---

## 2) Skill update mechanism (canonical)

Skill update is a two-part operation:

1. update skill content (creator plane)
2. distribute updated version (installer plane)

This is the baseline chain:

1. trigger (why update is needed)
2. patch surface (what changed)
3. validation (which checks must pass)
4. replay/regression (rerun original failing case)

Identity update lifecycle mirrors this same chain.

---

## 3) Patch surface priority (when updating a skill)

Patch in this order to reduce drift:

1. trigger instability -> patch `SKILL.md` description first
2. workflow instability -> patch `SKILL.md` body steps
3. repetitive/error-prone actions -> patch/add `scripts/`
4. overloaded domain details -> move to `references/`
5. output/template drift -> patch `assets/`
6. UI metadata drift -> patch `agents/openai.yaml` (if used)

Keep patches atomic and evidence-backed.

---

## 4) Post-update validation (mandatory)

A skill update is not complete until all four checks pass.

### 4.1 Structure validation
- run a structural validator (e.g., quick validate script)
- ensure required files resolve

### 4.2 Resource validation
- run changed scripts at least once
- verify references linked from `SKILL.md` are reachable

### 4.3 Trigger regression validation (must include 3 suites)
- positive cases (should trigger)
- boundary cases (should route deterministically)
- negative cases (should not trigger)

### 4.4 Real task smoke test
- run one real/representative task
- confirm stability and quality improvement

---

## 5) Continuous triggering strategy

### 5.1 Mechanism layer
- trigger by metadata + request semantics
- explicit skill mention must strongly trigger
- non-matching tasks must not trigger

### 5.2 Prompt layer
- include stable action phrases in metadata
- include common synonyms used by operators

### 5.3 Engineering layer
- maintain prompt regression set
- record trigger failures and patch metadata regularly

---

## 6) Identity protocol mapping (direct reuse)

- skill metadata trigger discipline -> identity routing + trigger regression contract
- skill update chain -> identity update lifecycle contract
- skill validator/replay discipline -> identity validator chain + replay requirement
- installer/creator separation -> identity routing between runtime updater and capability builder

---

## 7) Required review baseline before identity capability decisions

For identity capability/routing/governance changes, reviewers must check:

1. `identity/protocol/IDENTITY_PROTOCOL.md`
2. this reference file
3. OpenAI Codex Skills official docs
4. Agent Skills specification
5. MCP specification

Review evidence is mandatory per `protocol_review_contract`.

---

## 8) Maintainer checklist

- [ ] updater trigger condition is explicit
- [ ] patch surface is explicit and minimal
- [ ] structural + resource + regression + smoke validations are all run
- [ ] positive/boundary/negative suites all exist and pass
- [ ] original failing case replay evidence is recorded
- [ ] distribution path (installer plane) is completed where required
- [ ] baseline review evidence cites protocol sources
