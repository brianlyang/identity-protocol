# Identity × Skill × MCP Cross-Vendor Governance Guide v1.0

Status: draft  
Scope: OpenAI + Anthropic + Google Gemini + MCP Specification 2025-11-25  
Last updated: 2026-02-21

## 1) Purpose

This guide is a governance and architecture reference for `identity-protocol` as a base repository.

It targets one concrete goal:
- achieve **continuous maintenance + multi-scenario reuse + auditable execution + clean handoff** under multi-agent operation.

This document does **not** introduce a parallel protocol. It maps external protocol capabilities onto your existing control-plane contracts in:
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `docs/specs/identity-control-loop-v1.4.0.md`

## 2) Hard Positioning (No Ambiguity)

Use this layer split as a non-negotiable rule:
- `identity`: direction, constraints, arbitration, closure criteria.
- `skill`: reusable strategy/workflow package.
- `mcp`: capability transport and tool exposure protocol.
- `tool runtime`: concrete execution side effects.

Failure triage must be layered. Do not patch all layers at once.

## 3) Cross-Vendor Facts That Matter for Design

### 3.1 OpenAI (Responses + Tools + Remote MCP)

Key operational facts:
- Tool/function calling is explicitly multi-step and requires app-side execution + result return.
- OpenAI supports built-in tools and remote MCP via `tools` in Responses API.
- Remote MCP has explicit approval flow options and server trust warnings.

Design implication for this repo:
- your `capability_orchestration_contract` must treat `require_approval` and trust tiers as policy input, not runtime afterthought.

### 3.2 Anthropic (Tool use + Tool runner + MCP connector)

Key operational facts:
- Tool definitions rely heavily on detailed descriptions and JSON Schema.
- `tool_choice` modes (`auto` / `any` / `tool` / `none`) materially change behavior.
- MCP connector allows remote MCP from Messages API, but with explicit limitations (not full MCP feature set; tool calls focus).

Design implication for this repo:
- your `knowledge_acquisition_contract` should encode model/vendor-specific tool-choice constraints and "must explain" fallback policy.

### 3.3 Google Gemini (Function calling + MCP in SDK)

Key operational facts:
- Function calling is explicit app-managed loop.
- Gemini SDKs document MCP support and automatic tool call loops when using MCP client sessions.
- Parallel/compositional function calling exists and can change route/latency tradeoffs.

Design implication for this repo:
- your `capability_arbitration_contract` must explicitly resolve reasoning-depth vs latency vs parallel-calling risk.

### 3.4 MCP Spec 2025-11-25

Key protocol facts:
- MCP defines tool/resource/prompt capabilities and negotiation semantics.
- Security guidance emphasizes input validation, access controls, rate limiting, user confirmation for sensitive ops, and audit logs.
- HTTP auth spec is separate from STDIO env-based credential patterns.

Design implication for this repo:
- your `ci_enforcement_contract` must verify capability declarations, transport/auth assumptions, and audit evidence completeness per run.

## 4) Mapping External Protocols to Existing Identity Contracts

Map every external capability request into one of your existing contracts.

| External concern | Identity contract (existing) | Required evidence |
| --- | --- | --- |
| Choosing skills/tools under uncertainty | `capability_orchestration_contract` | route decision record + fallback chain + budget bound |
| On-demand retrieval / fresh docs learning | `knowledge_acquisition_contract` | source tier, freshness stamp, citation list |
| Success/failure feedback becoming durable rule | `experience_feedback_contract` | hypothesis/patch/result + replay result + rulebook delta |
| Gate and CI enforcement consistency | `ci_enforcement_contract` | required checks inventory + workflow binding |
| Tension between speed, correctness, learning | `capability_arbitration_contract` | arbitration decision record + threshold trigger |

If a new feature cannot map to this table, reject the change until contract mapping is explicit.

## 5) Four Core Capability Conflict: Practical Arbitration Policy

Your repo already has four-core arbitration semantics. The recommended practical precedence for high-risk production use is:

1. judgement integrity (evidence consistency)
2. reasoning closure (traceability)
3. routing efficiency (cost/latency)
4. rule learning speed (promotion cadence)

Use this only as default precedence. Permit override only with explicit arbitration records.

Minimum arbitration record fields:
- `task_id`
- `identity_id`
- `conflict_type`
- `options_considered`
- `selected_option`
- `why_not_others`
- `expected_risk`
- `rollback_condition`
- `validator_evidence`

## 6) Multi-Agent (Master/Sub) Anti-Drift Runtime Pattern

Use one canonical control pattern:
- Master owns objective decomposition, routing, gate decisions, acceptance.
- Sub owns bounded execution and structured evidence output.
- Sub cannot mutate top-level identity contracts.

Required handoff payload (enforce as schema, not convention):
- `task_id`
- `input_scope`
- `actions_taken`
- `artifacts`
- `result`
- `next_action`
- `rulebook_update`

This aligns with your current hardening path:
- `identity/protocol/AGENT_HANDOFF_CONTRACT.md`
- `scripts/validate_agent_handoff_contract.py`

## 7) CI as Control-Plane Enforcement (Not Just Build Check)

CI in this repo should be interpreted as protocol law execution.

A PR is governance-valid only when all are true:
- required gates pass in reusable workflow.
- trigger regression includes semantic validation, not field-presence only.
- update lifecycle includes replay evidence and required check coverage.
- handoff logs pass freshness + task/identity consistency checks.
- route quality metrics are generated and archived.

Recommended required check set (aligned with current direction):
- `validate_identity_runtime_contract.py`
- `validate_identity_update_lifecycle.py`
- `validate_identity_trigger_regression.py`
- `validate_identity_learning_loop.py`
- `validate_agent_handoff_contract.py`
- `validate_identity_orchestration_contract.py`
- `validate_identity_knowledge_contract.py`
- `validate_identity_experience_feedback.py`
- `validate_identity_ci_enforcement.py`
- `validate_identity_capability_arbitration.py`

## 8) Pre-Change Cross-Validation Protocol (Before Any Upgrade)

Before changing identity/skill/mcp integration logic, run this fixed preflight:

1. Source review
2. Contract mapping
3. Risk declaration
4. Patch surface declaration
5. Validator set freeze
6. Replay case selection

### 8.1 Source review

Collect authoritative references for each affected layer and include links in PR body.

### 8.2 Contract mapping

State exactly which contract blocks are touched in `CURRENT_TASK.json`.

### 8.3 Risk declaration

At minimum classify:
- route wrong
- gate miss
- tool auth
- skill mismatch
- evidence missing

### 8.4 Patch surface declaration

List required files before coding. Reject hidden scope expansion.

### 8.5 Validator set freeze

Lock required validators before first patch commit.

### 8.6 Replay case selection

Pick at least one historical failure case and one boundary case.

## 9) Knowledge Acquisition: Make Fast Learning Auditable

To satisfy "fast learning without drift", enforce a retrieval policy contract:
- source tiers: official docs > primary spec > curated examples > community notes.
- freshness policy by domain volatility.
- mandatory citation capture for high-impact decisions.
- explicit "inference vs fact" tagging in review notes.

Suggested evidence fields:
- `source_url`
- `source_type`
- `retrieved_at`
- `claim`
- `evidence_excerpt`
- `inference_note`

## 10) Skill/MCP Growth Without Chaos: Registry Discipline

When many skills and MCP servers coexist, use two registries plus one arbitration table.

Required registries:
- `skill registry`: intent domain, trigger conditions, fallback policy, owner.
- `mcp registry`: server trust tier, auth mode, allowed tools, risk class.

Arbitration table key:
- `(task_type, risk_level, latency_budget, data_sensitivity) -> (skill_set, mcp_server_set, approval_mode)`

Operational rule:
- route decisions must be reproducible from registry + task features, not individual agent preference.

## 11) What to Add Next in This Repository

Priority P0:
- add one canonical cross-vendor decision matrix artifact in `identity/runtime/examples/`.
- add one validator that checks every route decision references a registry key.
- add one CI check that rejects missing source citation for high-impact protocol changes.

Priority P1:
- add weekly drift report generation from route metrics + replay pass rate.
- add audit snapshot section that tracks unresolved cross-vendor behavior mismatches.

Priority P2:
- add simulation tests for arbitration conflict types under synthetic workload.

## 12) Review Checklist (Use in PR Template)

Use this in every protocol-impacting PR:
- does change map to existing contract names only?
- is arbitration behavior explicit for new latency/accuracy tradeoffs?
- are trust and approval semantics explicit for remote MCP tools?
- is failure replay evidence attached?
- are branch protection required checks aligned with current gate inventory?
- is audit snapshot updated with residual risks?

## 13) Source Links (Official + Spec)

OpenAI:
- https://platform.openai.com/docs/guides/function-calling
- https://platform.openai.com/docs/guides/tools
- https://platform.openai.com/docs/guides/tools-remote-mcp
- https://developers.openai.com/codex/guides/agents-sdk

Anthropic:
- https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector

Google Gemini:
- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/gemini-api/docs/function-calling/tutorial
- https://ai.google.dev/gemini-api/docs/url-context

MCP specification:
- https://modelcontextprotocol.io/specification/2025-11-25
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization

## 14) Note on "Roundtable" Framing

This document is a synthesized architecture position built from official vendor/spec documents and your current repository contracts.

It is not a transcript of direct human roundtable participation from OpenAI/Anthropic/Google architects. It is intended as an auditable engineering synthesis for protocol review use.
