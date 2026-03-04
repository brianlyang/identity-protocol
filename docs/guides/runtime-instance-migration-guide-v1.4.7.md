# Runtime instance migration guide (v1.4.7)

Status: **recommended for all teams upgrading from repo-internal runtime identities**  
Updated: **2026-02-23**

---

## Why this migration is required

From v1.4.6+, runtime identities are designed to be **local-only** by default:

- local catalog: `${IDENTITY_HOME}/catalog.local.yaml`
- local identity instances: `${IDENTITY_HOME}/<identity-id>` (skills-style root convention)
  (legacy `${IDENTITY_HOME}/identity/<identity-id>`, `${IDENTITY_HOME}/identities/<identity-id>`, and `${IDENTITY_HOME}/instances/<identity-id>` remain readable)

This prevents the severe failure mode where pulling/re-cloning the base repo overwrites runtime instances.

If your runtime identities are still under repository paths (`identity/packs/...`), migrate them now.

---

## Scope

This guide migrates **non-fixture runtime identities** from repo paths to local paths.

Fixture/demo identities (for example `store-manager`) remain in repo and should keep:

- `profile=fixture`
- `runtime_mode=demo_only`

---

## Prerequisites

1. On latest main:

```bash
git checkout main
git pull --ff-only
```

2. Set local runtime home (recommended explicit):

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export IDENTITY_HOME="${IDENTITY_HOME:-$CODEX_HOME/identity}"
```

3. Optional backup (strongly recommended):

```bash
mkdir -p /tmp/identity-migration-backup
cp identity/catalog/identities.yaml /tmp/identity-migration-backup/repo-identities.yaml.bak
```

---

## Migration steps

### Step 1) Preview (dry-run)

```bash
python3 scripts/migrate_repo_instances_to_local.py
```

This prints:

- candidate identities to move
- source/target mapping
- expected local catalog updates

### Step 2) Apply

```bash
python3 scripts/migrate_repo_instances_to_local.py --apply
```

Outputs are written under `${IDENTITY_HOME}/reports/`:

- `migration-report-<timestamp>.json`
- `migration-rollback-map-<timestamp>.json`

### Step 3) Validate persistence boundary

```bash
python3 scripts/validate_identity_local_persistence.py --runtime-mode
```

Expected: pass (`[OK] local persistence boundary validation passed`)

### Step 4) Validate runtime identity behavior

Replace `<runtime-id>` with your migrated identity id.

```bash
python3 scripts/identity_creator.py validate --identity-id <runtime-id>
python3 scripts/identity_creator.py activate --identity-id <runtime-id>
python3 scripts/identity_creator.py update --identity-id <runtime-id> --mode review-required --out-dir /tmp/upgrade-reports
python3 scripts/validate_identity_experience_writeback.py --identity-id <runtime-id> --report /tmp/upgrade-reports/identity-upgrade-exec-<runtime-id>-*.json
```

---

## Installer-plane verification (recommended)

```bash
python3 scripts/identity_installer.py plan --identity-id <runtime-id>
python3 scripts/identity_installer.py dry-run --identity-id <runtime-id>
python3 scripts/identity_installer.py install --identity-id <runtime-id>
python3 scripts/identity_installer.py verify --identity-id <runtime-id>
```

To confirm boundary hardening, this should fail without explicit override:

```bash
python3 scripts/identity_installer.py plan --identity-id <runtime-id> --target-root identity/packs
# expected: blocked unless --allow-repo-target + confirm token + purpose
```

---

## Rollback strategy

If migration must be reverted:

1. Read `${IDENTITY_HOME}/reports/migration-rollback-map-*.json`
2. Restore repo catalog backup if needed
3. Copy instance directories back using the map (`to -> from`)

Note: rollback should be treated as emergency only; preserve migration evidence for audit.

---

## FAQ

### Q1: Does base repo pull still affect my runtime identity after migration?

No, not by default. Runtime identities are local-only and resolved from local catalog first.

### Q2: Can I still create repo fixture identities?

Yes, but only explicitly:

```bash
python3 scripts/create_identity_pack.py ... --repo-fixture --repo-fixture-confirm "I_UNDERSTAND_REPO_FIXTURE_WRITE" --repo-fixture-purpose "demo fixture only" --pack-root identity/packs --catalog identity/catalog/identities.yaml
```

### Q3: Why is writeback validation required in migration checklist?

Because migration is not only storage relocation; it must prove update loop continuity:
`update(report) -> RULEBOOK/TASK_HISTORY writeback -> validator pass`.
