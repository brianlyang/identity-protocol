# Identity Protocol Broadcast

This directory is the governed broadcast extension pack for the identity protocol machine world.

## Foundational philosophy inheritance

1. This extension inherits `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` as the bottom-theory source for semantic singularity, fail-close preference, and lifecycle closure.
2. It inherits `identity/protocol/IDENTITY_RUNTIME.md` as the runtime constitution for delivery, acknowledgment, migration closure, and current-turn authority boundaries.
3. Broadcast truth in protocol law does not automatically equal broadcast possession in an instance runtime.

## Extension authority boundary

1. `identity/protocol/broadcast/index.json` is the canonical item index for protocol broadcast source material.
2. `identity/protocol/broadcast/schema/broadcast-item.v1.json` freezes the broadcast item schema.
3. `identity/protocol/broadcast/items/*.json` freeze protocol broadcast source documents for governed dissemination.
4. This pack defines governed extension law for broadcast source material; it does not silently acknowledge broadcasts, replace host-gateway ownership, or collapse broadcast into continuity or memory sinks.

## Runtime adjudication boundary

1. This README, the index, and the schema are frozen extension surfaces; they are not terminal surfaces for current-turn legality.
2. Current-turn legality for broadcast delivery must resolve from machine-consumed enforcement surfaces such as:
   - `scripts/validate_identity_broadcast_delivery.py`
   - `scripts/run_identity_broadcast_delivery.py`
   - `scripts/check_identity_broadcast_migration_closure.py`
   - validators
   - probes
   - runtime state
   - receipts
3. The active governance and review surfaces for this extension remain:
   - `docs/governance/identity-broadcast-communication-convergence-governance-v1.6.20.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.20-broadcast-communication-convergence.md`

## Truth lifecycle discipline

1. Broadcast source existence is not operational closure.
2. The lifecycle must remain explicit and ordered:
   - `truth_exists`
   - `truth_discoverable`
   - `truth_admissible`
   - `truth_bound`
   - `truth_consumed`
3. A broadcast item may exist in protocol law while still failing operational closure if the instance has not discovered it, admitted it as current authority, bound it to the current run, or consumed it in the next operational step.

## Canonical files

1. `index.json`
2. `schema/broadcast-item.v1.json`
3. `items/*.json`
4. `BROADCAST_DOC_CONTROL.current.yaml`
5. `identity/protocol/mappings/governed-subdomain-doc-control.current.yaml`

## Readability and governance control

1. `BROADCAST_DOC_CONTROL.current.yaml` is the stable doc-control entry for this subdomain.
2. `identity/protocol/mappings/governed-subdomain-doc-control.current.yaml` is the machine-consumed registry that binds `broadcast` to its active doc-control carrier.
3. `scripts/validate_protocol_broadcast_doc_control.py` fail-closes when broadcast extension-law readability drifts.
4. `scripts/ci/run_protocol_broadcast_doc_control_probes_ci.sh` proves positive and negative doc-control paths.
