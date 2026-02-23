# Local-instance persistence boundary (v1.4.6)

Status: **enforced (code-plane)**  
Last updated: **2026-02-23**

---

## 1. Incident summary (the severe bug)

Before v1.4.6 hardening, runtime identities could be created/registered under repository paths
(`identity/packs/...` + `identity/catalog/identities.yaml`).

This created a critical failure mode:

1. A maintainer syncs/pulls/re-clones the base repo.
2. Runtime identity instances are overwritten, drifted, or lost.
3. `identity-creator`/`identity-installer` continue operating against demo/repo fixtures instead of stable local runtime assets.
4. Upgrade evidence exists, but local instance continuity is broken.

This violated the expected operating model:

- base repo should host protocol + demo fixtures
- runtime instances should persist independently from base repo lifecycle

---

## 2. Governance decision

### 2.1 Layer split (MUST)

- **repo layer**: protocol + fixture/demo identities
- **local layer**: runtime/operational identities

Resolution precedence is **local > repo** for runtime operations.

### 2.2 Fixture/runtime semantics (MUST)

- `profile=fixture` + `runtime_mode=demo_only`: can exist in repo and serve as demo/test baseline.
- `profile=runtime` + `runtime_mode=local_only`: must live in local catalog + local instance root.

`store-manager` is explicitly fixture/demo in base catalog.

### 2.3 Persistence boundary (MUST)

Non-fixture runtime identities **must not** point to repo paths.

If a runtime identity resolves to repo path, validation fails.

---

## 3. Enforcement points

## 3.1 Context resolution

- Script: `scripts/resolve_identity_context.py`
- Local defaults:
  - `IDENTITY_HOME` resolution order:
    1. use explicit env `IDENTITY_HOME` if set
    2. else if `CODEX_HOME` is set, use `${CODEX_HOME}/identity`
    3. else use default `~/.codex/identity`
    4. if home path create fails, fallback to `./.codex/identity`
  - local catalog: `${IDENTITY_HOME}/catalog.local.yaml`
  - local identity root: `${IDENTITY_HOME}` (skills-style root convention)
    (legacy `${IDENTITY_HOME}/identity`, `${IDENTITY_HOME}/identities`, and `${IDENTITY_HOME}/instances` allowed for compatibility)
- Behavior:
  - merged catalog view (local overrides repo)
  - resolved identity includes source layer + effective pack path

## 3.2 Creator boundary

- Script: `scripts/create_identity_pack.py`
- Default target:
  - `--pack-root ${IDENTITY_HOME}`
  - `--catalog ${IDENTITY_HOME}/catalog.local.yaml`
- Repo-path write is blocked unless `--repo-fixture` is explicitly set.

## 3.3 Installer boundary

- Script: `scripts/identity_installer.py`
- Default target/catalog are local.
- Repo target writes are blocked unless `--allow-repo-target` is explicitly set.

## 3.4 Runtime persistence validator

- Script: `scripts/validate_identity_local_persistence.py`
- Gate:
  - runtime identity in repo path => fail
  - runtime identity with `demo_only` => fail
  - runtime-mode without local catalog => fail

## 3.5 Experience writeback gate

- Script: `scripts/execute_identity_upgrade.py`
  - review-required success must write back to RULEBOOK + TASK_HISTORY
- Script: `scripts/validate_identity_experience_writeback.py`
  - validates execution report ↔ writeback chain
- `scripts/release_readiness_check.py`
  - now auto-generates execution report if absent
  - always enforces writeback validation

---

## 4. Operational model (skill-like)

Runtime identities are now handled like isolated skill instances:

1. create/register to local catalog
2. activate/switch within local catalog transaction
3. update via creator against resolved local pack
4. install via installer to local target root
5. replay/writeback evidence retained on instance assets

Base repo sync does not mutate these local instance assets by default.

---

## 5. Migration

For legacy runtime identities living under repo paths:

```bash
python3 scripts/migrate_repo_instances_to_local.py --apply
```

Outputs:

- local catalog update
- migration report
- rollback map

---

## 6. Verification checklist

```bash
# local boundary
python3 scripts/validate_identity_local_persistence.py --runtime-mode

# create + register local runtime identity
python3 scripts/create_identity_pack.py \
  --id base-repo-audit-expert-local \
  --title "Base Repo Audit Expert" \
  --description "Local runtime identity" \
  --register

# creator mainline
python3 scripts/identity_creator.py validate --identity-id base-repo-audit-expert-local
python3 scripts/identity_creator.py activate --identity-id base-repo-audit-expert-local
python3 scripts/identity_creator.py update --identity-id base-repo-audit-expert-local --mode review-required --out-dir /tmp/upgrade-reports

# writeback closure
python3 scripts/validate_identity_experience_writeback.py \
  --identity-id base-repo-audit-expert-local \
  --report /tmp/upgrade-reports/identity-upgrade-exec-base-repo-audit-expert-local-*.json
```

---

## 7. Release-plane caveat

If workflow file updates are blocked by token scope, code-plane hardening can be merged first,
but Full-Go release statement requires workflow-side required-check proof to be green.
