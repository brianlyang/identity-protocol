# Identity Discovery Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It freezes deterministic discovery law for identity packs and identity
selection surfaces.

It is not:

1. a product/domain catalog example sheet;
2. a business-facing identity showcase;
3. a substitute for current runtime resolver truth or machine adjudication.

## Root-law scope and non-goals

1. This file freezes deterministic discovery law for root-domain identity discovery surfaces.
2. It is not a runtime resolver output, cached catalogue snapshot, or operator convenience note.
3. It is not a substitute for constitutional law in `IDENTITY_PROTOCOL.md` / `IDENTITY_RUNTIME.md`.
4. It must not be treated as a shortcut that bypasses canonical resolver outputs, validation, or current-run binding.

## Purpose

Define deterministic identity discovery law for governed identity-pack selection, including request/response shapes, precedence, activation policy, required error reporting, minimal implementation requirements, and fail-close discovery collapses.

This file remains the authoritative root-domain contract for deterministic identity discovery law.

## Foundational design philosophy anchor

This discovery contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why discovery must prefer canonical truth, semantic singularity, and fail-close determinism over convenience heuristics;
2. this file freezes the concrete discovery law: request/response shapes, precedence, activation policy, error reporting, minimal implementation requirements, and fail-close collapses;
3. this file is authoritative for root-domain discovery law, but current-turn discovery legality still depends on machine-consumed resolver, catalog, validator, and runtime truth surfaces;
4. philosophical grounding does not replace the contract authority of this discovery specification.

## Constitutional inheritance and authority boundary

This root-domain discovery contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the protocol-law boundaries for identity objects, source-of-truth discipline, and governed selection semantics that discovery must preserve.
2. `IDENTITY_RUNTIME.md` freezes how discovery becomes embodied in runtime startup, active identity resolution, and operational guard checks.
3. this file freezes the root-domain discovery contract that must be obeyed by resolvers and discovery validators without inventing local compatibility semantics.
4. root-contract authority must not be mistaken for either bottom-theory primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- identity instances and launchers performing governed discovery;
- resolvers, validators, and probes that adjudicate discovery legality;
- protocol maintainers strengthening discovery law without reopening local convenience heuristics.

It is not optimized as a business-facing catalogue or operator browsing aid.

## Runtime adjudication boundary

This file does not itself decide which identity is legal for the present turn.

Current-turn discovery legality must still resolve from machine-consumed enforcement surfaces such as:

1. the governed resolver and canonical catalog outputs;
2. identity context resolution, scope/path validation, and active-runtime checks;
3. validators, probes, runtime state, and receipts bound to the current run.

So this file freezes discovery law, while runtime adjudication determines whether discovery has actually been executed lawfully in the present turn.

## Deterministic identity discovery law

Governed identity discovery is not convenience browsing. It is a lawful process
for discovering candidate identity packs and governed selection surfaces from
canonical roots under explicit precedence and error-reporting discipline.

Discovery is lawful only when request shape, response shape, precedence,
activation ordering, error reporting, and minimal implementation requirements
remain explicit rather than inferred from local habit, cache residue, or path
similarity.

Cached snapshots, loose path guesses, and operator convenience notes may assist
human understanding, but they must not silently replace governed discovery
truth for the present turn.

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

Required request fields:

1. `method`
2. `id`
3. `cwds`
4. `extraRoots`
5. `forceReload`

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

Required response fields:

1. `defaultIdentity`
2. `identities`
3. `errors`
4. `packPath`
5. `allowImplicitActivation`
6. `activationPriority`
7. `conflictResolution`

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

When a discovery claim relies on governed proof, the proof stratum behind that
claim must match the discovery claim being made.

## Discovery-proof discipline

Deterministic discovery may be supported only by proof whose stratum matches
the discovery claim being asserted.

### 1. Request-shape proof

Supports claims that discovery input shape is lawful before resolver execution
begins.

Proof role: `request_shape_governed_discovery_proof`.

### 2. Response-shape proof

Supports claims that governed discovery output shape remains complete and
machine-consumable after resolver execution.

Proof role: `response_shape_governed_discovery_proof`.

### 3. Precedence-resolution proof

Supports claims that candidate identity roots were resolved under governed
precedence rather than local path convenience.

Proof role: `precedence_resolution_governed_discovery_proof`.

### 4. Activation-resolution proof

Supports claims that activation ordering was resolved under explicit selection,
pinning, and governed implicit policy order.

Proof role: `activation_resolution_governed_discovery_proof`.

### 5. Error-reporting proof

Supports claims that discovery errors remain explicit, structured, and
fail-close rather than silently absorbed.

Proof role: `error_reporting_governed_discovery_proof`.

### 6. Implementation-compliance proof

Supports claims that the local discovery implementation still resolves the
canonical catalog, default identity, pack paths, and normalized metadata shape.

Proof role: `implementation_compliance_governed_discovery_proof`.

## Discovery-proof limits

The protocol must preserve these discovery-proof limits:

1. request-shape proof is not proof of response-shape compliance;
2. response-shape proof is not proof of governed precedence resolution;
3. precedence-resolution proof is not proof of governed activation resolution;
4. activation-resolution proof is not proof of required error reporting;
5. error-reporting proof is not proof of implementation compliance;
6. implementation-compliance proof is not proof of current-turn resolver legality.

## Non-compliant discovery collapses

The following are non-compliant:

1. `cached_catalogue_as_current_turn_truth`: a cached catalogue snapshot is treated as current-turn governed discovery truth.
2. `path_presence_as_discovery_legality`: visible path presence or a nearby folder is treated as sufficient discovery legality.
3. `local_convenience_as_conflict_resolution`: same-id conflicts are resolved by local convenience rather than governed precedence and explicit pinning.
4. `missing_error_fields_as_valid_discovery`: discovery output is treated as valid even though required `errors[]` fields are missing.
5. `operator_note_as_resolver_truth`: an operator-facing note or summary is treated as if it were the governed resolver output.

## Validation

Use:

- `python3 scripts/validate_protocol_root_identity_discovery.py --json-only`
- `bash scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh`
- `python3 scripts/validate_discovery_requiredization.py`

These checks validate:

1. the root-domain discovery law, machine-consumed discovery mapping, and root-corpus integration;
2. deterministic discovery structure, precedence, and required reporting fields;
3. runtime discovery requiredization checks where present-turn discovery claims are made.

Discovery law remains root-domain law only; runtime authority for any concrete
current-turn discovery result still belongs to the governed resolver and its
machine-consumed outputs.
