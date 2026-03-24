# Identity Discovery Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes deterministic discovery law for identity packs and identity
selection surfaces.

It is not:

1. a product/domain catalog example sheet;
2. a business-facing identity showcase;
3. a substitute for current runtime resolver truth or machine adjudication.

## Purpose

Define a deterministic discovery contract for identity packs, similar to skill discovery.

- Input: working directories + optional extra roots.
- Output: active/available identities with policy/dependency metadata and load errors.

## Foundational design philosophy anchor

This discovery contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why discovery must prefer canonical truth, semantic singularity, and fail-close determinism over convenience heuristics;
2. this file freezes the concrete discovery law: request/response shapes, precedence, activation policy, error reporting, and minimal implementation requirements;
3. this file is authoritative for root-domain discovery law, but current-turn discovery legality still depends on machine-consumed resolver, catalog, validator, and runtime truth surfaces;
4. philosophical grounding does not replace the contract authority of this discovery specification.

## Method: `identity/list`

### Request shape

```json
{
  "method": "identity/list",
  "id": 2001,
  "params": {
    "cwds": ["/Users/me/project"],
    "extraRoots": ["/Users/me/shared-identities"],
    "forceReload": true
  }
}
```

### Response shape

```json
{
  "id": 2001,
  "result": {
    "data": [
      {
        "cwd": "/Users/me/project",
        "defaultIdentity": "store-manager",
        "identities": [
          {
            "id": "identity-alpha",
            "title": "Identity Alpha",
            "description": "Autonomous governed runtime identity",
            "status": "active",
            "packPath": "identity/identity-alpha",
            "enabled": true,
            "policy": {
              "allowImplicitActivation": true,
              "activationPriority": 90,
              "conflictResolution": "priority_then_objective"
            },
            "dependencies": {
              "tools": [
                { "type": "mcp", "value": "n8n-mcp" }
              ]
            },
            "interface": {
              "displayName": "Identity Alpha",
              "shortDescription": "Autonomous governed runtime identity"
            }
          }
        ],
        "errors": []
      }
    ]
  }
}
```

## Discovery precedence

1. Explicit project root (`cwd`)
2. Parent repository roots (if configured)
3. `extraRoots`

Conflict policy:
- same `id` across roots: prefer nearest `cwd` root unless explicit pin overrides.

## Activation policy contract

Activation priority order:
1. explicit identity selection
2. runtime pin (`identity/PROTOCOL_PIN.yaml` and project defaults)
3. implicit policy match (`allow_implicit_activation=true` + objective similarity)

## Required error reporting

Each `errors[]` item must include:
- `code`: machine-readable error code
- `path`: file path if applicable
- `message`: concise human-readable description
- `severity`: `warn` or `error`

## Minimal local implementation requirements

A compliant local implementation must:
1. Resolve `identity/catalog/identities.yaml`
2. Resolve `default_identity`
3. Verify each `pack_path` exists
4. Return normalized metadata + errors

Discovery law remains root-domain law only; runtime authority for any concrete
current-turn discovery result still belongs to the governed resolver and its
machine-consumed outputs.
