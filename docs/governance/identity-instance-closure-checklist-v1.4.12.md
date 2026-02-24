# Identity Instance Closure Checklist (v1.4.12)

Date: 2026-02-24  
Type: Operations closure checklist (runtime instance governance)  
Status: Actionable / command-ready  
Owner: Base-repo architect

---

## 0) Purpose

This checklist defines the **mandatory closure sequence** after identity instance migration, repair, or self-driven upgrade attempts.

It is designed to answer one practical question:

> After moving to a writable runtime root, what exactly must be done to reach a release-safe, auditable success state?

---

## 1) Scope and assumptions

This checklist applies to runtime identities (example: `base-repo-audit-expert-v3`) resolved from:

- selected runtime catalog: `$IDENTITY_CATALOG`
- USER scope runtime instance path

Protocol repo example root:

- `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local`

---

## 1.1) Runtime mode selection (mandatory first step)

Before running any heal/update command, select one runtime path mode explicitly:

1. **Project-runtime mode (recommended, external root)**  
   set `IDENTITY_HOME` to a writable path **outside protocol repo**
2. **Global mode (direct explicit opt-in)**  
   `source ./scripts/use_local_identity_env.sh`

Reference policy:

- `docs/governance/identity-runtime-path-selection-governance-v1.4.12.md`

No implicit mode selection is allowed for release-bound runs.

---

## 2) Required final state (must all be true)

A run is considered **business-success closed** only if all conditions hold:

1. `all_ok = true`
2. `writeback_status = WRITTEN`
3. `permission_state = WRITEBACK_WRITTEN`
4. release workspace cleanliness validation passes
5. e2e smoke validation passes

If any condition fails, keep release posture at `Conditional Go`.

---

## 3) Execution sequence (strict order)

> Run commands from protocol root (example shown with `identity-protocol-local`).

### Step 1 — Pin runtime env

```bash
# project-runtime mode (recommended, external root):
export IDENTITY_PROTOCOL_HOME="$(pwd)"
export IDENTITY_HOME="/tmp/codex-identity-runtime/${USER}/$(basename "$(pwd)")"
export IDENTITY_CATALOG="${IDENTITY_HOME}/catalog.local.yaml"
mkdir -p "${IDENTITY_HOME}"

# OR global runtime (explicit opt-in):
# source ./scripts/use_local_identity_env.sh

echo "IDENTITY_HOME=$IDENTITY_HOME"
echo "IDENTITY_CATALOG=$IDENTITY_CATALOG"
echo "IDENTITY_PROTOCOL_HOME=$IDENTITY_PROTOCOL_HOME"
```

### Step 2 — Resolve target identity deterministically

```bash
python3 scripts/resolve_identity_context.py resolve \
  --identity-id base-repo-audit-expert-v3 \
  --repo-catalog identity/catalog/identities.yaml \
  --local-catalog "$IDENTITY_CATALOG"
```

Must verify:

- `source_layer=local`
- `resolved_scope=USER`
- `conflict_detected=false` (or explicit justified arbitration if true)

### Step 3 — Heal dry-run (scan/adopt/lock/repair plan)

```bash
python3 scripts/identity_creator.py heal \
  --identity-id base-repo-audit-expert-v3 \
  --repo-catalog identity/catalog/identities.yaml \
  --catalog "$IDENTITY_CATALOG" \
  --scope USER
```

### Step 4 — Heal apply (perform fixes)

```bash
python3 scripts/identity_creator.py heal \
  --identity-id base-repo-audit-expert-v3 \
  --repo-catalog identity/catalog/identities.yaml \
  --catalog "$IDENTITY_CATALOG" \
  --scope USER \
  --apply
```

### Step 5 — Validate before update

```bash
python3 scripts/identity_creator.py validate \
  --identity-id base-repo-audit-expert-v3 \
  --catalog "$IDENTITY_CATALOG" \
  --scope USER
```

### Step 6 — Upgrade in review-required mode

```bash
python3 scripts/identity_creator.py update \
  --identity-id base-repo-audit-expert-v3 \
  --mode review-required \
  --catalog "$IDENTITY_CATALOG" \
  --scope USER

# resolve latest execution report path from known runtime roots
REPORT=$(python3 - <<'PY'
import glob, os
identity_id="base-repo-audit-expert-v3"
roots=["/tmp/identity-runtime","/tmp/identity-upgrade-reports"]
ih=os.environ.get("IDENTITY_HOME","").strip()
if ih:
    roots.append(ih)
cands=[]
for r in roots:
    cands.extend(glob.glob(os.path.join(r,"**",f"identity-upgrade-exec-{identity_id}-*.json"), recursive=True))
cands=[p for p in cands if not p.endswith("-patch-plan.json")]
cands.sort(key=os.path.getmtime)
print(cands[-1] if cands else "")
PY
)
echo "$REPORT"
```

### Step 7 — Verify writeback contract

```bash
python3 scripts/validate_identity_experience_writeback.py \
  --identity-id base-repo-audit-expert-v3 \
  --repo-catalog identity/catalog/identities.yaml \
  --local-catalog "$IDENTITY_CATALOG" \
  --report "$REPORT"
```

### Step 8 — Verify permission-state contract (require WRITTEN)

```bash
python3 scripts/validate_identity_permission_state.py \
  --identity-id base-repo-audit-expert-v3 \
  --report "$REPORT" \
  --require-written \
  --ci
```

### Step 9 — Final release-oriented regressions

```bash
python3 scripts/validate_release_workspace_cleanliness.py
bash scripts/e2e_smoke_test.sh
```

---

## 4) Sandboxed/deferred writeback handling

If update result contains:

- `writeback_status=DEFERRED_PERMISSION_BLOCKED`
- `permission_state=NEEDS_ESCALATION` (or escalation denied)

Then this means:

- governance detection worked,
- but business closure is **not complete**.

Required follow-up:

1. rerun with approved escalation or
2. migrate to writable runtime root and rerun full sequence from Step 1

No partial pass accepted for release.

---

## 5) Common failure triage

If Step 7/8 fails, check in order:

1. catalog still points to old/non-writable path
2. scope mismatch (`USER` expected but another scope used)
3. RULEBOOK/TASK_HISTORY paths still bind to old location
4. report file path passed to validators is not the latest run artifact
5. runtime root accidentally points into protocol root (blocked by `IP-PATH-001`)

---

## 6) Audit evidence to retain

For each closure run, preserve:

1. resolve output JSON
2. heal report JSON (dry-run + apply)
3. update execution report JSON
4. writeback validator output
5. permission-state validator output
6. readiness/e2e command outcomes

Retention recommendation: keep at least the latest 7 days for rapid arbitration.

---

## 7) Non-goals

1. This checklist does not redefine identity protocol policy.
2. This checklist does not replace existing release gates.
3. This checklist does not permit soft-pass on deferred writeback.
