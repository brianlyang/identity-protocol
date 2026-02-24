# Identity Runtime Path Selection Governance (v1.4.12)

Date: 2026-02-24  
Type: Runtime operations governance baseline (path strategy)  
Status: Proposal-ready -> merge as required operations policy  
Owner: Base-repo architect + Audit expert

---

## 0. Why this document exists

Repeated upgrade loops showed the same root issue:

- operators do not make runtime path mode explicit before running identity commands;
- identity may run against global runtime by accident (`~/.codex/identity`);
- in sandboxed sessions this often triggers deferred writeback / escalation;
- teams then retry ad hoc, causing governance churn.

This policy closes the loop by making runtime path mode an explicit first decision.

---

## 1. Mandatory runtime path modes (only two allowed)

### Mode P (Project-runtime, recommended default)

- `IDENTITY_HOME` is project-associated **but outside protocol_root** (example: `/tmp/codex-identity-runtime/<project>/<id-home>`)
- `IDENTITY_CATALOG=$IDENTITY_HOME/catalog.local.yaml`
- writeback remains in a writable runtime root without polluting protocol repository
- preferred for sandboxed development and deterministic local regression

### Mode G (Global runtime, explicit opt-in)

- `IDENTITY_HOME=~/.codex/identity`
- `IDENTITY_CATALOG=~/.codex/identity/catalog.local.yaml`
- allowed for long-lived personal runtime ops
- may require escalation in restricted sandbox sessions

### Forbidden mode

- implicit/no-mode execution where runtime root is inferred from incidental shell/env leftovers.

---

## 2. Required operator decision step (before any update/heal/install)

Every operation session MUST begin with explicit mode selection.

### Select Mode P (project-local)

```bash
# NOTE: protocol/runtime hard boundary requires runtime root outside protocol repo.
export IDENTITY_PROTOCOL_HOME="$(pwd)"
export IDENTITY_HOME="/tmp/codex-identity-runtime/${USER}/$(basename "$(pwd)")"
export IDENTITY_CATALOG="${IDENTITY_HOME}/catalog.local.yaml"
mkdir -p "${IDENTITY_HOME}"
```

### Select Mode G (global)

```bash
source ./scripts/use_local_identity_env.sh
```

Then resolve identity and confirm path tuple:

```bash
python3 "$IDENTITY_PROTOCOL_HOME/scripts/resolve_identity_context.py" resolve \
  --identity-id <identity-id> \
  --repo-catalog "$IDENTITY_PROTOCOL_HOME/identity/catalog/identities.yaml" \
  --local-catalog "$IDENTITY_CATALOG"
```

Required check:

1. `catalog_path == $IDENTITY_CATALOG`
2. `source_layer == local`
3. `resolved_scope` matches intended scope (usually `USER`)

---

## 3. Sandbox behavior contract (hard rule)

If Mode G is selected and writeback is blocked by sandbox permissions:

- result may become `DEFERRED_PERMISSION_BLOCKED`;
- this is governance-detected state, **not** release-pass state.

Allowed recovery paths:

1. approve escalation and rerun same chain, or
2. switch to Mode P and rerun full closure chain.

Release policy:

- no release green if final report is not:
  - `all_ok=true`
  - `writeback_status=WRITTEN`
  - `permission_state=WRITEBACK_WRITTEN`

---

## 4. Installation governance alignment (skill-style parity)

For identity installer actions, runtime target MUST be explicit:

- project-runtime install: `--target-root <external-runtime-root>`
- global install: `--target-root ~/.codex/identity`

No implicit target fallback for release-bound runs.

This mirrors skill governance ergonomics:

- skill path mode is explicit in project config;
- identity runtime mode must be explicit in operator bootstrap.

---

## 5. Required gates mapping (path-governance layer)

Minimum gate chain for release-bound identity runs:

1. scope resolution / isolation / persistence
2. runtime contract + role binding
3. writeback validator
4. permission state validator with `--require-written --ci`
5. workspace cleanliness
6. readiness + e2e

If any gate fails, status remains `Conditional Go`.

---

## 6. Anti-drift controls

1. do not run identity update before path mode selection.
2. do not mix Mode P and Mode G reports in one promotion set without arbitration note.
3. do not claim closure with deferred permission status.
4. do not write runtime artifacts into protocol repository runtime folders (fixture/debug exceptions require explicit bypass flags and audit notes).

---

## 7. Acceptance criteria (this policy considered closed when all pass)

1. Operators can choose path mode in one command at session start.
2. Path tuple in reports is deterministic and auditable.
3. In sandboxed default flow, Mode P achieves non-escalated WRITTEN closure.
4. Mode G escalation path is documented and treated as exception path.
5. Release gate evidence shows required checks tied to selected mode.

---

## 8. Implementation note (v1.4.12 hard boundary alignment)

`execute_identity_upgrade.py` now enforces protocol/runtime separation (`IP-PATH-001`):

- runtime pack paths under `protocol_root` are blocked by default in update flow
- explicit fixture/debug bypass requires `--allow-protocol-root-pack`

Therefore, any documented project mode that points to `<repo>/.agents/identity` is considered legacy guidance and must not be used for release-bound update/writeback runs.
