#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <identity-id> <title> <description> [pack-root]"
  exit 1
fi

IDENTITY_ID="$1"
TITLE="$2"
DESCRIPTION="$3"
PACK_ROOT="${4:-identity/packs}"
PACK_DIR="${PACK_ROOT}/${IDENTITY_ID}"

mkdir -p "${PACK_DIR}"
mkdir -p "${PACK_DIR}/agents"
mkdir -p "identity/runtime/examples"

cat > "${PACK_DIR}/META.yaml" <<META
id: "${IDENTITY_ID}"
title: "${TITLE}"
description: "${DESCRIPTION}"
status: "active"
methodology_version: "v1.2.3"
META

cat > "${PACK_DIR}/IDENTITY_PROMPT.md" <<'PROMPT'
# Identity Prompt

Define role cognition, principles, and decision rules.
PROMPT

cat > "${PACK_DIR}/CURRENT_TASK.json" <<JSON
{
  "task_id": "${IDENTITY_ID}_bootstrap",
  "objective": {
    "title": "${DESCRIPTION}",
    "priority": "HIGH",
    "status": "pending"
  },
  "state_machine": {
    "current_state": "intake",
    "allowed_states": ["intake", "analyze", "execute", "verify", "done", "blocked"],
    "transition_rules": [
      "intake -> analyze",
      "analyze -> execute",
      "execute -> verify",
      "verify -> done",
      "verify -> analyze",
      "analyze -> blocked"
    ]
  },
  "gates": {
    "document_gate": "required",
    "media_gate": "required",
    "category_compliance_gate": "required",
    "reject_memory_gate": "required",
    "protocol_baseline_review_gate": "required",
    "payload_evidence_gate": "required",
    "multimodal_consistency_gate": "required",
    "reasoning_loop_gate": "required",
    "routing_gate": "required",
    "rulebook_gate": "required"
  },
  "protocol_review_contract": {
    "required_before": [
      "identity_capability_upgrade",
      "identity_architecture_decision"
    ],
    "must_review_sources": [
      {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "identity/protocol/IDENTITY_PROTOCOL.md"
      },
      {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md"
      },
      {
        "type": "official_doc",
        "url": "https://developers.openai.com/codex/skills/"
      },
      {
        "type": "official_doc",
        "url": "https://agentskills.io/specification"
      },
      {
        "type": "official_doc",
        "url": "https://modelcontextprotocol.io/specification/latest"
      }
    ],
    "required_evidence_fields": [
      "review_id",
      "reviewed_at",
      "reviewer_identity",
      "purpose",
      "sources_reviewed",
      "findings",
      "decision"
    ],
    "evidence_report_path_pattern": "identity/runtime/examples/protocol-baseline-review-*.json",
    "max_review_age_days": 7
  },
  "evaluation_contract": {
    "required_evidence_triplet": ["api_evidence", "event_evidence", "ui_evidence"],
    "consistency_required": true,
    "consistency_fail_action": "block_done_and_trigger_recheck",
    "run_report_path_pattern": "resource/reports/*run*.json"
  },
  "reasoning_loop_contract": {
    "max_attempts_before_escalation": 3,
    "mandatory_fields_per_attempt": ["attempt", "hypothesis", "patch", "expected_effect", "result"],
    "failure_requires_next_action": true
  },
  "routing_contract": {
    "auto_route_enabled": true,
    "fallback_switch_after_failures": 2,
    "problem_type_routes": {
      "unknown": ["identity-creator"]
    }
  },
  "rulebook_contract": {
    "append_only": true,
    "required_rule_types": ["negative", "positive"],
    "required_fields": [
      "rule_id",
      "type",
      "trigger",
      "action",
      "evidence_run_id",
      "scope",
      "confidence",
      "updated_at"
    ],
    "rulebook_path": "${PACK_DIR}/RULEBOOK.jsonl"
  },
  "source_of_truth": {
    "local_docs_roots": [],
    "local_project_evidence_roots": ["resource/reports", "resource/preflight", "resource/reject-archive"]
  },
  "escalation_policy": {
    "email_for_offline_only": true,
    "offline_blockers": [],
    "do_not_email_for": ["routine_status_update", "normal_progress_report", "non_blocking_warning"]
  },
  "required_artifacts": ["resource/reports/*.json", "resource/reports/*.md"],
  "post_execution_mandatory": [
    "append task outcome into ${PACK_DIR}/TASK_HISTORY.md",
    "update objective.status",
    "update state_machine.current_state"
  ]
}
JSON

cat > "${PACK_DIR}/TASK_HISTORY.md" <<'HISTORY'
# Task History

## Entries
HISTORY

python3 - <<PY
import json, datetime
path = "${PACK_DIR}/RULEBOOK.jsonl"
row = {
  "rule_id": "${IDENTITY_ID}-bootstrap-positive-rule",
  "type": "positive",
  "trigger": "identity_pack_initialized",
  "action": "enforce_protocol_baseline_review_before_identity_upgrades",
  "evidence_run_id": "bootstrap",
  "scope": "identity_runtime",
  "confidence": "high",
  "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with open(path, "w", encoding="utf-8") as f:
  f.write(json.dumps(row, ensure_ascii=False) + "\\n")
PY

cat > "${PACK_DIR}/agents/identity.yaml" <<META
interface:
  display_name: "${TITLE}"
  short_description: "${DESCRIPTION}"
  default_prompt: "Operate as ${IDENTITY_ID} and satisfy runtime gates."

policy:
  allow_implicit_activation: true
  activation_priority: 50
  conflict_resolution: "priority_then_objective"

dependencies:
  tools: []

observability:
  event_topics: []
  required_artifacts:
    - "resource/reports/*.json"
META

cat > "identity/runtime/examples/protocol-baseline-review-${IDENTITY_ID}-sample.json" <<JSON
{
  "review_id": "protocol-baseline-review-${IDENTITY_ID}-sample",
  "reviewed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "reviewer_identity": "${IDENTITY_ID}",
  "purpose": "sample protocol baseline review evidence generated by identity-creator scaffold",
  "sources_reviewed": [
    {
      "type": "github_repo_file",
      "repo": "brianlyang/identity-protocol",
      "path": "identity/protocol/IDENTITY_PROTOCOL.md"
    },
    {
      "type": "github_repo_file",
      "repo": "brianlyang/identity-protocol",
      "path": "docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md"
    },
    {
      "type": "official_doc",
      "url": "https://developers.openai.com/codex/skills/"
    },
    {
      "type": "official_doc",
      "url": "https://agentskills.io/specification"
    },
    {
      "type": "official_doc",
      "url": "https://modelcontextprotocol.io/specification/latest"
    }
  ],
  "findings": [
    "Identity-upgrade conclusions must be source-backed.",
    "Protocol baseline review gate must pass before architecture decisions."
  ],
  "decision": {
    "result": "approved",
    "notes": "sample artifact; replace with real review for production upgrades"
  }
}
JSON

echo "Initialized identity pack at ${PACK_DIR}"
echo "Created protocol baseline review sample at identity/runtime/examples/protocol-baseline-review-${IDENTITY_ID}-sample.json"
echo "Next: register this pack in identity/catalog/identities.yaml"
