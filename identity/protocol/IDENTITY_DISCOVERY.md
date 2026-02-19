# Identity Discovery Contract (v1.1 draft)

## Purpose

Define a deterministic discovery contract for identity packs, similar to skill discovery.

- Input: working directories + optional extra roots.
- Output: active/available identities with policy/dependency metadata and load errors.

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
            "id": "store-manager",
            "title": "WeChat Shop Store Manager",
            "description": "Revenue-oriented autonomous operator",
            "status": "active",
            "packPath": "identity/store-manager",
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
              "displayName": "Store Manager",
              "shortDescription": "Autonomous WeChat Shop operator"
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

