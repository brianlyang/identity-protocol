# Runtime Preflight Checklist (v1.2.13)

## Purpose

Ensure live business tests never run with stale local identity protocol rules.

## Mandatory step 0: local protocol sync gate

Before any runtime test (e.g. item-level remediation), run:

```bash
bash scripts/preflight_identity_runtime_sync.sh <local-identity-protocol-path> [branch]
```

Example:

```bash
bash scripts/preflight_identity_runtime_sync.sh /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local main
```

### Pass criteria

- command returns `[OK]`
- prints `sync_sha=<sha>`
- sha equals remote `origin/main`

### Fail behavior

If stale:
1. `git checkout main`
2. `git pull --ff-only`
3. rerun preflight sync script

No pass -> no business runtime execution.

---

## Remaining preflight steps

1. Validate protocol basics:
   - `python3 scripts/validate_identity_protocol.py`
2. Validate governance snapshot index:
   - `python3 scripts/validate_audit_snapshot_index.py`
3. Validate handoff contract and self-test:
   - `python3 scripts/validate_agent_handoff_contract.py --identity-id store-manager --self-test`
4. Export route quality metrics baseline:
   - `python3 scripts/export_route_quality_metrics.py --identity-id store-manager`

---

## Operator note

This checklist externalizes memory into executable gates. Do not rely on chat memory for critical preflight actions.
