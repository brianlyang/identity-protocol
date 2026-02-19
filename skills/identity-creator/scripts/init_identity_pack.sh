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

cat > "${PACK_DIR}/META.yaml" <<META
id: "${IDENTITY_ID}"
title: "${TITLE}"
description: "${DESCRIPTION}"
status: "active"
methodology_version: "v1.0"
META

cat > "${PACK_DIR}/IDENTITY_PROMPT.md" <<'PROMPT'
# Identity Prompt

Define role cognition, principles, and decision rules.
PROMPT

cat > "${PACK_DIR}/CURRENT_TASK.json" <<'JSON'
{
  "objective": {
    "title": "",
    "priority": "HIGH",
    "status": "pending"
  },
  "state_machine": {
    "current_state": "intake",
    "allowed_states": ["intake"]
  },
  "gates": {},
  "source_of_truth": {},
  "escalation_policy": {},
  "required_artifacts": [],
  "post_execution_mandatory": []
}
JSON

cat > "${PACK_DIR}/TASK_HISTORY.md" <<'HISTORY'
# Task History

## Entries
HISTORY

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
  required_artifacts: []
META

echo "Initialized identity pack at ${PACK_DIR}"
echo "Next: register this pack in identity/catalog/identities.yaml"
