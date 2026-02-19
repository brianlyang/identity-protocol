# Identity Rollback Drill (Operational)

## Objective

Practice a safe rollback from a newer protocol pin to a known-good pin.

## Preconditions

- Consumer repo has `identity/PROTOCOL_PIN.yaml`
- Consumer has local verification scripts
- A known-good previous pin exists (tag+commit)

## Drill steps

### 1) Capture current state

```bash
cat identity/PROTOCOL_PIN.yaml
bash scripts/identity/upgrade_and_verify_v1.sh
```

Archive outputs:
- verification console log
- `/tmp/identity_discovery_contract.latest.json`

### 2) Simulate incident

Common trigger examples:
- manifest semantic validator fails
- discovery contract returns errors
- runtime compile drift after protocol update

### 3) Rollback pin

Edit `identity/PROTOCOL_PIN.yaml` to previous known-good tag+commit.

### 4) Re-verify

```bash
bash scripts/identity/upgrade_and_verify_v1.sh
```

Pass criteria:
- all checks green
- no missing required keys/files

### 5) Incident record

Record in incident log:
- failed target tag
- rollback target tag
- root cause summary
- preventive action

## Decision policy

- If failure affects required contract keys/files: immediate rollback.
- If failure only affects optional v1.1 features and operations are not blocked:
  allow temporary degraded mode with explicit risk note.

