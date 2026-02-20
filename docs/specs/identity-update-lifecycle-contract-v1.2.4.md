# Identity Update Lifecycle Contract v1.2.4 (draft)

## Purpose

Bring identity evolution to the same operational standard as skill updates.

Skill updates are effective because they define four deterministic phases:
1. trigger
2. patch surface
3. validation
4. replay

This contract applies the same four-phase chain to identity updates.

## Four-phase contract

### 1) Trigger contract (when update is mandatory)

An identity update MUST be triggered when any of the following is true:

- `operational_failure`: online item is technically successful but operationally failing (e.g. image/price/semantic mismatch)
- `repeat_failure`: same class of failure repeats beyond threshold
- `route_exhausted`: existing identity+skill+tool routes fail to converge within configured attempts
- `new_domain_gap`: required problem domain has no valid route

Runtime key:
- `identity_update_lifecycle_contract.trigger_contract`

### 2) Patch surface contract (what must be updated)

Identity updates MUST patch explicit local surfaces, not only narrative output.

Required surfaces:
- `CURRENT_TASK.json` (gates/routes/state contracts)
- `IDENTITY_PROMPT.md` (decision policy)
- `RULEBOOK.jsonl` (negative/positive learning rules)
- `TASK_HISTORY.md` (change ledger)

Runtime key:
- `identity_update_lifecycle_contract.patch_surface_contract`

### 3) Validation contract (prove update correctness)

Identity update is invalid unless required validators pass.

Minimum required checks:
- `scripts/validate_identity_runtime_contract.py`
- `scripts/validate_identity_upgrade_prereq.py --identity-id <id>`
- route resolvability check for updated problem types

Runtime key:
- `identity_update_lifecycle_contract.validation_contract`

### 4) Replay contract (prove real improvement)

After update, replay the original failing case. No replay = no learning completion.

Required:
- replay on same case/sample
- compare before vs after evidence
- fail replay => re-enter update loop

Runtime key:
- `identity_update_lifecycle_contract.replay_contract`

## Done criteria

For identity-evolution tasks, `done` is allowed only when all four phases are satisfied.

Technical success alone is insufficient.

## Alignment

- Skill alignment: mirrors skill update chain (trigger -> edit -> validate -> regression replay)
- MCP alignment: deterministic contracts, explicit failure semantics, testable execution gates
