# Skill Installer / Skill Creator / Skill Update Lifecycle (Canonical Reference)

This is the **canonical review entry** for skill mechanism alignment in identity-protocol.

It standardizes four things reviewers must check:

1. trigger/discovery model
2. installer vs creator responsibilities
3. update lifecycle and distribution lifecycle
4. post-update validation + continuous trigger stability

> Detailed long-form SOP is in:
> `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`

---

## A) Core model (Codex runtime perspective)

Skill loading is layered:

1. **resident metadata layer**: `name + description`
2. **trigger layer**: skill selected only when request matches metadata
3. **execution layer**: after trigger, load `SKILL.md` body and then needed resources (`scripts/`, `references/`, `assets/`)
4. **turn layer**: by default no automatic cross-turn inheritance unless explicitly re-mentioned or re-matched

Implication: metadata quality controls trigger quality.

---

## B) Installer vs Creator (strict separation)

### skill-installer

Purpose: distribution/installation of existing skills.

Typical operations:
- list curated/experimental skills
- install by repo/path/url
- reinstall updated version in target environment

Not responsible for:
- authoring skill semantics
- workflow quality design

### skill-creator

Purpose: authoring/updating skill definition and resources.

Typical operations:
- create/update `SKILL.md`
- maintain `scripts/`, `references/`, `assets/`
- enforce validation and trigger regression discipline

Not responsible for:
- package distribution to runtime targets

---

## C) Skill update = two coupled operations

1. **content update** (creator-plane)
2. **runtime distribution** (installer-plane)

Canonical update chain:
1. trigger
2. patch surface
3. validation
4. replay/regression

---

## D) Patch priority for existing skills

1. trigger mismatch -> patch `description` first
2. execution instability -> patch `SKILL.md` workflow body
3. repetitive/fragile ops -> patch `scripts/`
4. overlong domain details -> move to `references/`
5. output drift -> patch `assets/`
6. UI metadata drift -> patch `agents/openai.yaml` (if present)

---

## E) Post-update validation (must include all)

1. structure validation
2. resource/script validation
3. trigger regression (positive/boundary/negative)
4. real-task smoke run

Success condition:
- valid structure
- correct trigger behavior
- improved real-task stability

---

## F) Continuous trigger strategy

- mechanism: explicit mention > strong semantic match > minimal-scope route set
- prompting: use stable command prefixes and synonyms in descriptions
- engineering: maintain regression prompt set and periodic metadata tuning

---

## G) Reviewer checklist

- [ ] installer/creator boundaries are not mixed
- [ ] update chain follows trigger/patch/validate/replay
- [ ] creator-plane changes and installer-plane distribution are both completed
- [ ] 3-suite trigger regression evidence exists
- [ ] post-update smoke run evidence exists
- [ ] references are easy to locate from README and runtime review contracts
