#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

required_files=(
  "identity/catalog/identities.yaml"
  "identity/protocol/IDENTITY_PROTOCOL.md"
  "identity/protocol/IDENTITY_RUNTIME.md"
  "identity/runtime/IDENTITY_COMPILED.md"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "${ROOT}/${f}" ]]; then
    echo "[FAIL] missing ${f}"
    FAIL=1
  else
    echo "[OK]   ${f}"
  fi
done

TASK_JSON="${ROOT}/identity/store-manager/CURRENT_TASK.json"
if [[ -f "${TASK_JSON}" ]]; then
  for key in objective state_machine gates source_of_truth escalation_policy; do
    if ! jq -e ".${key}" "${TASK_JSON}" >/dev/null 2>&1; then
      echo "[FAIL] ${TASK_JSON} missing key: ${key}"
      FAIL=1
    else
      echo "[OK]   ${TASK_JSON} has key: ${key}"
    fi
  done
else
  echo "[WARN] ${TASK_JSON} not found (legacy/non-store-manager project?)"
fi

if [[ ${FAIL} -ne 0 ]]; then
  echo "Identity protocol validation FAILED"
  exit 1
fi

echo "Identity protocol validation PASSED"
