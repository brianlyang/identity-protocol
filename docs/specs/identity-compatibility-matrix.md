# Identity Protocol Compatibility Matrix (v1.1)

## Purpose

Define compatibility guarantees between protocol versions, creator tooling, and consumer repos.

## Versioning model

- `MAJOR`: breaking contract changes in required files/keys
- `MINOR`: backward-compatible protocol additions (new optional blocks, new validators)
- `PATCH`: documentation/tooling fixes without contract break

## Matrix

| Producer (identity-protocol) | Consumer pin target | Expected result | Notes |
|---|---|---|---|
| v1.0.x | v1.0.x | ✅ Stable | Base protocol contract only |
| v1.1.x | v1.0.x | ✅ Stable | Consumer keeps old pin; new features not consumed |
| v1.1.x | v1.1.x | ✅ Stable | Includes manifest/discovery validations |
| v2.x | v1.x | ⚠️ Review required | Major upgrade requires migration playbook |

## Contract levels

### Level A (required, stable in v1.x)
- `identity/catalog/identities.yaml`
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`
- `identity/runtime/IDENTITY_COMPILED.md`
- `CURRENT_TASK.json` keys:
  - `objective`
  - `state_machine`
  - `gates`
  - `source_of_truth`
  - `escalation_policy`

### Level B (optional in v1.1+, recommended)
- `identity/protocol/IDENTITY_DISCOVERY.md`
- identity catalog optional blocks:
  - `interface`
  - `policy`
  - `dependencies`
  - `observability`

## Consumer upgrade checklist

1. Update `identity/PROTOCOL_PIN.yaml` tag+commit.
2. Run `scripts/identity/upgrade_and_verify_v1.sh`.
3. Confirm discovery artifact generated:
   - `/tmp/identity_discovery_contract.latest.json`
4. If fail:
   - rollback pin
   - rerun validation

