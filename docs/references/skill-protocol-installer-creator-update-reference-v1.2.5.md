# Skill Protocol Reference: Trigger / Create / Update / Validate (v1.2.5)

This document is the long-form reference for identity-protocol reviewers.

It captures the complete operational model for skill behavior under Codex-like AGENTS governance, including:
- trigger/discovery behavior
- installer vs creator boundaries
- update flow and distribution flow
- post-update validation and continuous trigger stability

---

## 0) Unified runtime model (very important)

Skill behavior is layered:

1. **Resident layer**: only `name + description` metadata is always considered.
2. **Trigger layer**: once a request matches a skill, load `SKILL.md` body.
3. **Execution layer**: load `scripts/`, `references/`, `assets/` only when needed.
4. **Turn continuity layer**: no automatic cross-turn persistence unless re-mentioned/re-matched.

Operational implication:
- trigger quality depends more on metadata quality than on long body text.

---

## 1) Skill trigger mechanism

### 1.1 Discovery stage

- runtime first discovers available skills from injected environment rules (e.g. AGENTS skill list)
- discovery is based on current session skill registry, not implicit historical memory

### 1.2 Trigger decision rules

- explicit trigger: user names skill directly (`$skill-name` or literal mention)
- semantic trigger: user request strongly matches description intent
- multi-skill cases: choose minimal covering set and declare order

### 1.3 Non-trigger scenarios

- if no registered skill matches, fallback to generic toolchain (shell/MCP/code edits)

### 1.4 Governance constraints

- if matched, skill should be used (cannot silently skip)
- no cross-turn carry unless re-matched/re-mentioned
- if path/resource unreadable: report + fallback

---

## 2) Skill creation mechanism (creator plane)

### 2.1 Minimal structure

- `<skill>/SKILL.md` (required)
- `<skill>/scripts/*` (optional, recommended)
- `<skill>/references/*` (optional)
- `<skill>/assets/*` (optional)

### 2.2 SKILL.md content contract

Should include:
- use scope and non-scope
- input contract
- executable/reproducible workflow steps
- output contract and quality criteria
- fallback behavior
- validation steps

### 2.3 Creation principles

- prefer scripts/templates over long hand-written chat logic
- resolve relative paths from skill root first
- load only necessary references (progressive disclosure)

### 2.4 Registration reality

- creating files alone is not enough
- skill must be discoverable by session registry to trigger in future turns

---

## 3) Installer vs Creator (boundary contract)

### 3.1 skill-installer responsibilities

- list installable skills (curated/experimental/remote)
- install existing skills into local skill directory
- install from GitHub repo/path/url (public/private depending on auth)
- remind runtime reload/restart requirement where applicable

Not responsible for:
- authoring semantics
- quality policy design

### 3.2 skill-creator responsibilities

- define/update skill semantics and resources
- maintain trigger wording quality
- enforce update validation and regression discipline

Not responsible for:
- distribution to all runtime targets

### 3.3 Operational rule

- content changes => creator plane
- distribution/reinstallation => installer plane

---

## 4) Skill update mechanism (existing skill)

Skill update has two linked operations:

1. update skill content
2. distribute updated version to target runtimes

### 4.1 Update triggers

- explicit user request to update skill
- observed mis-trigger/under-trigger
- workflow failures or repeated manual patches
- new scenario coverage need

### 4.2 Patch priority order (recommended)

1. trigger mismatch -> patch `description`
2. execution mismatch -> patch `SKILL.md` body
3. fragile ops -> patch/add `scripts/`
4. context overload -> move details to `references/`
5. template/output drift -> patch `assets/`
6. UI metadata drift -> patch `agents/openai.yaml` (if used)

### 4.3 Update hygiene

- avoid pseudo-updates (docs changed but runtime behavior unchanged)
- keep changes atomic and reversible
- maintain backward compatibility where possible

---

## 5) Post-update validation (4 layers)

### 5.1 Static/structure validation

- required files exist
- SKILL references resolve
- command/parameter docs match scripts

### 5.2 Dynamic/resource validation

- run changed scripts at least once
- verify expected output fields/artifacts
- verify failure branches produce explicit diagnostics

### 5.3 Trigger regression validation

Must include three suites:
- positive cases (must trigger)
- boundary cases (must route deterministically)
- negative cases (must not trigger)

### 5.4 Real-task smoke validation

- run one representative real task
- verify stability and output quality improvements

Success criteria:
- validation passes
- trigger behavior is correct
- real task is more stable than before

---

## 6) Continuous trigger stability

### 6.1 Mechanism layer

- explicit mention has top priority
- semantic match acts as fallback trigger
- multi-skill routing should minimize scope and overlap

### 6.2 Prompting layer

- keep action phrases stable
- include real operator synonyms in description
- state boundary conditions clearly to reduce false positives

### 6.3 Engineering layer

- maintain a regression prompt set (positive/boundary/negative)
- log trigger misses and periodically patch metadata
- run trigger regression after each meaningful update

---

## 7) Frequent failure patterns

- only patching body, not description => trigger issue remains
- overloading SKILL body with references => noisy execution
- missing negative regression tests => false trigger spikes
- updating content but skipping runtime reinstallation/reload => stale behavior in target runtime

---

## 8) Practical SOP (from trigger to report)

1. detect trigger target
2. declare selected skill(s) + execution order
3. load minimal context (`SKILL.md` + required scripts)
4. execute workflow
5. validate (static + dynamic + trigger regression + smoke)
6. report artifacts/paths/results/residual risk

---

## 9) Maintainer checklist

- [ ] installer and creator boundaries remain clear
- [ ] update follows trigger -> patch -> validate -> replay
- [ ] post-update 4-layer validation evidence exists
- [ ] trigger regression includes positive/boundary/negative suites
- [ ] runtime distribution/reinstall step is completed where needed
- [ ] review references are accessible from canonical entry and README
