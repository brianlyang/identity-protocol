#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

IDS="${1:-${IDS:-}}"
if [ -z "${IDS}" ]; then
  echo "[FAIL] IDS is empty"
  exit 1
fi

CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH:-}")"
REPO_CATALOG_PATH="$(protocol_shell_entry_repo_catalog_path "${REPO_CATALOG_PATH:-}")"
HEADSTAMP_ACTOR_ID="$(protocol_shell_entry_require_actor_id "${HEADSTAMP_ACTOR_ID:-}")"
HEADSTAMP_SESSION_ID="${HEADSTAMP_SESSION_ID:-run:${GITHUB_RUN_ID:-ci-local}}"

for ID in ${IDS}; do
  IS_FIXTURE_ID="$(ID="$ID" CATALOG_PATH="$CATALOG_PATH" python3 -c 'import os,yaml,pathlib; identity_id=os.environ.get("ID","").strip(); catalog_path=os.environ["CATALOG_PATH"]; doc=yaml.safe_load(pathlib.Path(catalog_path).read_text(encoding="utf-8")) or {}; rows=[x for x in (doc.get("identities") or []) if isinstance(x,dict)]; row=next((x for x in rows if str(x.get("id","")).strip()==identity_id), {}); profile=str(row.get("profile","")).strip().lower(); runtime_mode=str(row.get("runtime_mode","")).strip().lower(); print("1" if (profile=="fixture" or runtime_mode=="demo_only") else "0")')"
  SESSION_PER_ID="${HEADSTAMP_SESSION_ID}-${ID}"
  if [ "${IS_FIXTURE_ID}" = "1" ]; then
    python3 scripts/validate_full_scan_target_regression.py \
      --identity-id "${ID}" \
      --project-catalog "${CATALOG_PATH}" \
      --repo-catalog "${REPO_CATALOG_PATH}" \
      --target-source-layer project \
      --actor-id "${HEADSTAMP_ACTOR_ID}" \
      --session-id "${SESSION_PER_ID}" \
      --expected-work-layer protocol \
      --expected-source-layer project \
      --allow-fixture-session-skip \
      --json-only
  else
    python3 scripts/validate_full_scan_target_regression.py \
      --identity-id "${ID}" \
      --project-catalog "${CATALOG_PATH}" \
      --repo-catalog "${REPO_CATALOG_PATH}" \
      --target-source-layer project \
      --actor-id "${HEADSTAMP_ACTOR_ID}" \
      --session-id "${SESSION_PER_ID}" \
      --expected-work-layer protocol \
      --expected-source-layer project \
      --enforce-m2m-pass \
      --json-only
  fi
done
