# Audit Snapshot — 2026-02-25 — Protocol/Runtime Boundary Closure (v1.4.12)

## Scope

This snapshot closes the residual P0 raised by roundtable audit feedback:

1. runtime writes could still drift into protocol repository paths via fallback branches
2. protocol-root identities could enter update flow without explicit fixture intent
3. dirty-worktree drift repeated due to missing ignore patterns for runtime replay/learning samples

## What was changed

### 1) Hard boundary enforcement (protocol root vs runtime root)

- `scripts/execute_identity_upgrade.py`
  - added protocol/runtime separation gate (`IP-PATH-001`)
  - default behavior now **blocks** upgrade execution when `pack_path` resolves under `protocol_root`
  - repo fallback `<protocol_root>/.codex/identity/runtime/...` removed from runtime output root resolver
  - explicit fixture/debug override remains available:
    - `--allow-protocol-root-pack`

- `scripts/identity_creator.py`
  - `update` command now enforces protocol-root separation before invoking upgrade executor
  - explicit fixture/debug override:
    - `--allow-protocol-root-pack`
  - scope alignment check now uses resolver-provided `resolved_scope` (avoids false mismatch for fixture identities)

- `scripts/resolve_identity_context.py`
  - fallback identity home changed from repo-local `.codex` to:
    - `/tmp/codex-identity-runtime/<user>`
  - this prevents fallback writes from entering protocol repo tree in sandboxed environments

### 2) Clean-workspace isolation refinement

- `.gitignore` expanded to include:
  - `identity/runtime/examples/*-learning-*.json`
  - `identity/runtime/examples/*-update-replay-*.json`
  - `.codex/`

This closes common runtime drift files observed in audit runs.

### 3) Legacy role-binding evidence path normalization

- `scripts/identity_creator.py`
  - role-binding evidence writes now normalize legacy patterns:
    - `identity/runtime/**`
    - `identity/runtime/local/<identity-id>/**`
  - both are redirected into `<pack_path>/runtime/**` for runtime identities

- `scripts/validate_identity_role_binding.py`
  - role-binding evidence lookup now resolves the same legacy patterns against pack runtime root

- `scripts/repair_identity_baseline_evidence.py`
  - role-binding repair now emits evidence to identity-scoped runtime root instead of repo-relative legacy paths

## Verification evidence (local)

1. **workspace cleanliness gate**
   - command:
     - `python3 scripts/validate_release_workspace_cleanliness.py`
   - result:
     - `[OK] release workspace cleanliness check passed`

2. **protocol-root hard block**
   - command:
     - `python3 scripts/execute_identity_upgrade.py --catalog identity/catalog/identities.yaml --identity-id store-manager ...`
   - result:
     - `[FAIL] IP-PATH-001 pack_path is inside protocol_root ...`

3. **runtime output root no longer repo-local**
   - command:
     - `python3 scripts/identity_creator.py update --identity-id office-ops-expert --scope USER ...`
   - observed report root:
     - `/tmp/identity-runtime/office-ops-expert/...`
   - no runtime output written to `<protocol_root>/.codex/identity/runtime/...`

4. **role-binding repair uses identity runtime root**
   - command:
     - `python3 scripts/repair_identity_baseline_evidence.py --identity-id base-repo-audit-expert-v3 --catalog ~/.codex/identity/catalog.local.yaml --repair-role-binding --apply`
   - observed output:
     - `/Users/yangxi/.codex/identity/base-repo-audit-expert-v3/runtime/examples/identity-role-binding-...json`
   - follow-up validator:
     - `python3 scripts/validate_identity_role_binding.py ...` -> `PASSED`

## Residual posture

- **Code-plane**: Go (local hardening and guardrails active)
- **Release-plane**: Conditional Go (requires latest cloud required-gates run-id evidence closure)

## Notes for reviewers

- Fixture identities under protocol repo are intentionally blocked by default for update path.
- If fixture/debug replay is explicitly required, use `--allow-protocol-root-pack` and attach rationale in audit notes.
- CI/release posture remains strict (`validate_identity_permission_state --require-written` unchanged).
