#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${ROOT}/scripts/shell_strict_entry_common.sh"
source "${ROOT}/scripts/runtime_temp_path_common.sh"

CATALOG_ARG=""
IDENTITY_ID="${IDENTITY_ID:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --catalog)
      CATALOG_ARG="${2:-}"
      shift 2
      ;;
    --identity-id)
      IDENTITY_ID="${2:-}"
      shift 2
      ;;
    *)
      echo "[FAIL] unknown argument: $1"
      exit 1
      ;;
  esac
done

CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_ARG}")"
export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-${ROOT}/.tmp}"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "feedback-to-judgement-loopback-probes" "run")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

eval "$(
  ROOT="${ROOT}" CATALOG_PATH="${CATALOG_PATH}" IDENTITY_ID="${IDENTITY_ID}" python3 - <<'PY'
import json
import os
import shlex
import sys
from pathlib import Path

import yaml

root = Path(os.environ["ROOT"]).resolve()
sys.path.insert(0, str(root / "scripts"))

from tool_vendor_governance_common import load_json, resolve_pack_and_task  # noqa: E402

catalog_path = Path(os.environ["CATALOG_PATH"]).resolve()
requested_identity = str(os.environ.get("IDENTITY_ID", "")).strip()
catalog_doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]

candidate_ids = [requested_identity] if requested_identity else [str(row.get("id", "")).strip() for row in rows if str(row.get("id", "")).strip()]
selected = None
for identity_id in candidate_ids:
    try:
        _pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    except Exception:
        continue
    task_doc = load_json(task_path)
    arbitration = task_doc.get("capability_arbitration_contract") or {}
    feedback = task_doc.get("experience_feedback_contract") or {}
    if not (isinstance(arbitration, dict) and arbitration.get("required") is True):
        continue
    if not (isinstance(feedback, dict) and feedback.get("required") is True):
        continue
    if not isinstance(arbitration.get("accurate_judgement_enforcement"), dict):
        continue
    if not isinstance(arbitration.get("feedback_operational_prompt_enforcement"), dict):
        continue
    selected = {
        "identity_id": identity_id,
        "task_path": str(task_path),
    }
    break

if selected is None:
    raise SystemExit("no loopback-ready identity found for probes")

for key, value in selected.items():
    print(f"{key.upper()}={shlex.quote(str(value))}")
PY
)"

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_MISSING_RULEBOOK_TASK="${TMP_ROOT}/negative-missing-rulebook.json"
NEGATIVE_MISSING_RULEBOOK_JSON="${TMP_ROOT}/negative-missing-rulebook.out.json"
NEGATIVE_JUDGEMENT_TASK="${TMP_ROOT}/negative-judgement-gate.json"
NEGATIVE_JUDGEMENT_JSON="${TMP_ROOT}/negative-judgement-gate.out.json"

python3 "${ROOT}/scripts/validate_feedback_to_judgement_loopback.py" \
  --catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --json-only > "${POSITIVE_JSON}"

python3 - "${TASK_PATH}" "${NEGATIVE_MISSING_RULEBOOK_TASK}" <<'PY'
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
doc = json.loads(src.read_text(encoding="utf-8"))
contract = doc.get("experience_feedback_contract") or {}
contract["negative_rulebook_path"] = ""
doc["experience_feedback_contract"] = contract
dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

set +e
python3 "${ROOT}/scripts/validate_feedback_to_judgement_loopback.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${NEGATIVE_MISSING_RULEBOOK_TASK}" \
  --json-only > "${NEGATIVE_MISSING_RULEBOOK_JSON}"
NEGATIVE_RULEBOOK_RC=$?
set -e
if [ "${NEGATIVE_RULEBOOK_RC}" -eq 0 ]; then
  echo "[FAIL] negative missing-rulebook probe unexpectedly passed"
  exit 1
fi

python3 - "${TASK_PATH}" "${NEGATIVE_JUDGEMENT_TASK}" <<'PY'
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
doc = json.loads(src.read_text(encoding="utf-8"))
arbitration = doc.get("capability_arbitration_contract") or {}
judgement = arbitration.get("accurate_judgement_enforcement") or {}
judgement["requires_multimodal_evidence_consistency"] = False
arbitration["accurate_judgement_enforcement"] = judgement
doc["capability_arbitration_contract"] = arbitration
dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

set +e
python3 "${ROOT}/scripts/validate_feedback_to_judgement_loopback.py" \
  --identity-id "${IDENTITY_ID}" \
  --current-task "${NEGATIVE_JUDGEMENT_TASK}" \
  --json-only > "${NEGATIVE_JUDGEMENT_JSON}"
NEGATIVE_JUDGEMENT_RC=$?
set -e
if [ "${NEGATIVE_JUDGEMENT_RC}" -eq 0 ]; then
  echo "[FAIL] negative judgement-gate probe unexpectedly passed"
  exit 1
fi

python3 - "${POSITIVE_JSON}" "${NEGATIVE_MISSING_RULEBOOK_JSON}" "${NEGATIVE_JUDGEMENT_JSON}" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative_rulebook = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
negative_judgement = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))

if positive.get("feedback_to_judgement_loopback_status") != "PASS_REQUIRED":
    raise SystemExit("positive loopback probe must PASS_REQUIRED")
if positive.get("loop_back_to_first_loop_status") != "PASS_REQUIRED":
    raise SystemExit("positive loopback routeback status must PASS_REQUIRED")
if positive.get("adoption_decision") != "first_loop_revalidate_before_adopt":
    raise SystemExit("positive loopback adoption_decision mismatch")
if positive.get("conflict_with_current_evidence") != "demote_or_rollback_required":
    raise SystemExit("positive loopback conflict policy mismatch")

rulebook_reasons = [str(x).strip() for x in (negative_rulebook.get("stale_reasons") or []) if str(x).strip()]
if negative_rulebook.get("feedback_to_judgement_loopback_status") != "FAIL_REQUIRED":
    raise SystemExit("negative missing-rulebook probe must FAIL_REQUIRED")
if "experience_feedback_contract_negative_rulebook_path_missing" not in rulebook_reasons:
    raise SystemExit("negative missing-rulebook probe missing expected stale reason")

judgement_reasons = [str(x).strip() for x in (negative_judgement.get("stale_reasons") or []) if str(x).strip()]
if negative_judgement.get("feedback_to_judgement_loopback_status") != "FAIL_REQUIRED":
    raise SystemExit("negative judgement probe must FAIL_REQUIRED")
if "accurate_judgement_enforcement_requires_multimodal_evidence_consistency_false" not in judgement_reasons:
    raise SystemExit("negative judgement probe missing expected stale reason")

summary = {
    "feedback_to_judgement_loopback_probe_status": "PASS_REQUIRED",
    "positive_loopback_status": positive.get("feedback_to_judgement_loopback_status"),
    "negative_missing_rulebook_failure": "experience_feedback_contract_negative_rulebook_path_missing",
    "negative_judgement_gate_failure": "accurate_judgement_enforcement_requires_multimodal_evidence_consistency_false",
    "identity_id": positive.get("identity_id"),
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
