# Identity Core Capability Verification Matrix

Status: Active
Updated: 2026-02-20

This matrix turns the 4 core capabilities into protocol-level review checks.

## Capability 1: Accurate result judgement (multi-modal cross-check)

**Intent**: prevent false success signals.

Protocol requirements:
- `gates.multimodal_consistency_gate = required`
- `evaluation_contract.required_evidence_triplet` includes:
  - `api_evidence`
  - `event_evidence`
  - `ui_evidence`
- `evaluation_contract.consistency_required = true`

Validation:
- `python3 scripts/validate_identity_runtime_contract.py`

Review checklist:
- [ ] run artifact includes all 3 evidence types
- [ ] consistency decision recorded
- [ ] inconsistent runs are blocked from `done`

---

## Capability 2: Strong reasoning loop until target reached

**Intent**: no guess-based one-shot retries.

Protocol requirements:
- `gates.reasoning_loop_gate = required`
- `reasoning_loop_contract.mandatory_fields_per_attempt` includes:
  - `attempt`, `hypothesis`, `patch`, `expected_effect`, `result`
- `learning_verification_contract.reasoning_trace_required = true`

Validation:
- `python3 scripts/validate_identity_learning_loop.py --run-report <run.json>`

Review checklist:
- [ ] reasoning_attempts exists and non-empty
- [ ] each attempt has mandatory fields
- [ ] failed attempts include next action

---

## Capability 3: Automatic routing to identity/skill/tool

**Intent**: avoid route dead-ends and capability lock-in.

Protocol requirements:
- `gates.routing_gate = required`
- `routing_contract.auto_route_enabled = true`
- `routing_contract.problem_type_routes` is non-empty

Validation:
- runtime contract validator for structural presence
- consumer-side route resolvability checks (path + enabled) are recommended

Review checklist:
- [ ] each critical problem_type has route chain
- [ ] fallback switching threshold is configured
- [ ] route components are discoverable in target runtime

---

## Capability 4: Rule strength (error/success rule completion)

**Intent**: convert outcomes into durable operational memory.

Protocol requirements:
- `gates.rulebook_gate = required`
- `rulebook_contract.append_only = true`
- `rulebook_contract.required_rule_types` includes `negative` and `positive`
- `learning_verification_contract.rulebook_update_required = true`

Validation:
- `python3 scripts/validate_identity_runtime_contract.py`
- `python3 scripts/validate_identity_learning_loop.py --run-report <run.json>`

Review checklist:
- [ ] rulebook exists and has schema-complete rows
- [ ] rule records linked to run_id (`evidence_run_id` by default)
- [ ] both negative and positive rules are represented over time

---

## Acceptance baseline

A release cannot claim “self-driven learning” unless all 4 capabilities are validated and review checklist items are satisfied.
