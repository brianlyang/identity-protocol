#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/protocol-feedback-path-residue-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${ROOT_DIR}"

echo "[info] protocol-feedback path residue probes temp dir: ${TMP_DIR}"

python3 - "${TMP_DIR}" <<'PY'
import json
import sys
from pathlib import Path

tmp_dir = Path(sys.argv[1]).resolve()
repo_root = Path.cwd().resolve()
sys.path.insert(0, str(repo_root / "scripts"))

from protocol_feedback_archival_common import materialize_feedback_channel_artifacts

feedback_root = (tmp_dir / "materialize-pack" / "runtime" / "protocol-feedback").resolve()
bad_channel_dir = (feedback_root / "runtime" / "protocol-feedback" / "inbox-from-protocol").resolve()
bad_index_path = (feedback_root / "runtime" / "protocol-feedback" / "evidence-index" / "INDEX.md").resolve()

result = materialize_feedback_channel_artifacts(
    feedback_root=feedback_root,
    channel_dir=bad_channel_dir,
    index_path=bad_index_path,
    identity_id="probe-identity",
    catalog_path=str(tmp_dir / "catalog.local.yaml"),
    body="hello protocol feedback",
    title="Protocol feedback inbox helper smoke",
    slug="protocol-feedback-inbox-helper-smoke",
    lane="inbox",
)

batch_path = Path(result["batch_path"]).resolve()
receipt_path = Path(result["receipt_path"]).resolve()
expected_root = (feedback_root / "inbox-from-protocol").resolve()
assert batch_path.parent == expected_root, result
assert receipt_path.parent == expected_root, result
assert not (feedback_root / "runtime" / "protocol-feedback" / "inbox-from-protocol").exists(), result
print("[PASS] materialize feedback channel artifacts canonicalized nested inbox helper path")
PY

mkdir -p "${TMP_DIR}/repair-pack/runtime/protocol-feedback/runtime/protocol-feedback/inbox-from-protocol"
cat > "${TMP_DIR}/catalog.local.yaml" <<YAML
identities:
  - id: probe-identity
    pack_path: ${TMP_DIR}/repair-pack
YAML
cat > "${TMP_DIR}/repair-pack/CURRENT_TASK.json" <<'JSON'
{}
JSON
cat > "${TMP_DIR}/repair-pack/runtime/protocol-feedback/runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_probe.md" <<'EOF_MD'
# Probe inbox

nested root residue
EOF_MD
cat > "${TMP_DIR}/repair-pack/runtime/protocol-feedback/runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_RECEIPT_probe.json" <<'EOF_JSON'
{"status":"ok"}
EOF_JSON

if python3 scripts/repair_protocol_feedback_path_residue.py \
  --catalog "${TMP_DIR}/catalog.local.yaml" \
  --identity-id probe-identity \
  --feedback-root runtime/protocol-feedback \
  --json-only > "${TMP_DIR}/preview.json"; then
  echo "[FAIL] expected preview residue scan to fail before apply"
  exit 1
fi

python3 - "${TMP_DIR}/preview.json" <<'PY'
import json
import sys
payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
assert payload["protocol_feedback_path_residue_status"] == "FAIL_REQUIRED", payload
assert payload["hit_count_before"] == 2, payload
print("[PASS] protocol-feedback residue preview blocked")
PY

python3 scripts/repair_protocol_feedback_path_residue.py \
  --catalog "${TMP_DIR}/catalog.local.yaml" \
  --identity-id probe-identity \
  --feedback-root runtime/protocol-feedback \
  --apply \
  --json-only > "${TMP_DIR}/apply.json"

python3 - "${TMP_DIR}/apply.json" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
assert payload["protocol_feedback_path_residue_status"] == "PASS_REQUIRED", payload
assert payload["hit_count_after"] == 0, payload
assert payload["moved_count"] == 2, payload
feedback_root = Path(payload["feedback_root"]).resolve()
assert (feedback_root / "inbox-from-protocol" / "PROTOCOL_INBOX_probe.md").exists(), payload
assert (feedback_root / "inbox-from-protocol" / "PROTOCOL_INBOX_RECEIPT_probe.json").exists(), payload
assert not (feedback_root / "runtime" / "protocol-feedback" / "inbox-from-protocol").exists(), payload
print("[PASS] protocol-feedback residue repair canonicalized nested files")
PY

echo "[PASS] protocol-feedback path residue probes passed"
