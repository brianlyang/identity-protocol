#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/exec-surface-literal-lock.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

run_expect() {
  local name="$1"
  local expected_rc="$2"
  shift 2
  local out_json="${TMP_ROOT}/${name}.json"
  set +e
  "$@" >"${out_json}"
  local rc=$?
  set -e
  if [ "$rc" -ne "$expected_rc" ]; then
    echo "[FAIL] ${name}: expected rc=${expected_rc}, got rc=${rc}"
    cat "${out_json}"
    exit 1
  fi
  echo "${out_json}"
}

assert_json_field() {
  local json_path="$1"
  local python_expr="$2"
  python3 - "$json_path" "$python_expr" <<'PY'
import json
import sys
path = sys.argv[1]
expr = sys.argv[2]
obj = json.load(open(path, encoding="utf-8"))
if not eval(expr, {"obj": obj}):
    raise SystemExit(f"assertion_failed: {expr}\njson={obj}")
PY
}

echo "[INFO] executable surface runtime literal lock: positive repo lane"
POSITIVE_JSON="$(run_expect positive_repo 0 python3 "${REPO_ROOT}/scripts/validate_executable_surface_runtime_literal_lock.py" --repo-root "${REPO_ROOT}" --json-only)"
assert_json_field "${POSITIVE_JSON}" 'obj.get("executable_surface_runtime_literal_lock_status") == "PASS_REQUIRED"'
assert_json_field "${POSITIVE_JSON}" 'obj.get("violation_count") == 0'

echo "[INFO] executable surface runtime literal lock: negative fixed uuid lane"
NEG_UUID_ROOT="${TMP_ROOT}/neg-uuid-repo"
mkdir -p "${NEG_UUID_ROOT}/scripts"
python3 - "${NEG_UUID_ROOT}" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
uuid_token = "-".join(["0" * 8, "1" * 4, "2" * 4, "3" * 4, "4" * 12])
(root / "scripts" / "bad_uuid.sh").write_text(
    "#!/usr/bin/env bash\n"
    f'CODEX_THREAD_ID="{uuid_token}"\n',
    encoding="utf-8",
)
PY
NEG_UUID_JSON="$(run_expect negative_uuid 1 python3 "${REPO_ROOT}/scripts/validate_executable_surface_runtime_literal_lock.py" --repo-root "${NEG_UUID_ROOT}" --json-only)"
assert_json_field "${NEG_UUID_JSON}" 'obj.get("executable_surface_runtime_literal_lock_status") == "FAIL_REQUIRED"'
assert_json_field "${NEG_UUID_JSON}" 'any(v.get("kind") == "fixed_uuid_literal" for v in (obj.get("violations") or []))'

echo "[INFO] executable surface runtime literal lock: negative rollout path lane"
NEG_ROLLOUT_ROOT="${TMP_ROOT}/neg-rollout-repo"
mkdir -p "${NEG_ROLLOUT_ROOT}/scripts"
python3 - "${NEG_ROLLOUT_ROOT}" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
rollout_token = "".join(["rollout-", "20", "26", "-03", "-24", "T01", "-59", "-34"])
(root / "scripts" / "bad_rollout.sh").write_text(
    "#!/usr/bin/env bash\n"
    f'SIDECAR_PATH="sessions/probe/{rollout_token}.jsonl"\n',
    encoding="utf-8",
)
PY
NEG_ROLLOUT_JSON="$(run_expect negative_rollout 1 python3 "${REPO_ROOT}/scripts/validate_executable_surface_runtime_literal_lock.py" --repo-root "${NEG_ROLLOUT_ROOT}" --json-only)"
assert_json_field "${NEG_ROLLOUT_JSON}" 'obj.get("executable_surface_runtime_literal_lock_status") == "FAIL_REQUIRED"'
assert_json_field "${NEG_ROLLOUT_JSON}" 'any(v.get("kind") == "fixed_rollout_path_literal" for v in (obj.get("violations") or []))'

echo "[INFO] executable surface runtime literal lock: docs boundary lane"
DOCS_BOUNDARY_ROOT="${TMP_ROOT}/docs-boundary-repo"
mkdir -p "${DOCS_BOUNDARY_ROOT}/scripts" "${DOCS_BOUNDARY_ROOT}/docs/review"
python3 - "${DOCS_BOUNDARY_ROOT}" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
uuid_token = "-".join(["a" * 8, "b" * 4, "c" * 4, "d" * 4, "e" * 12])
rollout_token = "".join(["rollout-", "20", "26", "-03", "-24", "T07", "-08", "-09"])
(root / "scripts" / "good_dynamic.sh").write_text(
    "#!/usr/bin/env bash\n"
    'THREAD_ID="${THREAD_ID:-runtime-generated}"\n'
    'STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"\n',
    encoding="utf-8",
)
(root / "docs" / "review" / "evidence.md").write_text(
    f"evidence_path=sessions/probe/{rollout_token}-{uuid_token}.jsonl\n",
    encoding="utf-8",
)
PY
DOCS_BOUNDARY_JSON="$(run_expect docs_boundary 0 python3 "${REPO_ROOT}/scripts/validate_executable_surface_runtime_literal_lock.py" --repo-root "${DOCS_BOUNDARY_ROOT}" --json-only)"
assert_json_field "${DOCS_BOUNDARY_JSON}" 'obj.get("executable_surface_runtime_literal_lock_status") == "PASS_REQUIRED"'
assert_json_field "${DOCS_BOUNDARY_JSON}" 'all("docs/" not in path for path in (obj.get("scan_files") or []))'

echo "[INFO] executable surface runtime literal lock: active pack script lane"
PACK_BOUNDARY_ROOT="${TMP_ROOT}/pack-boundary"
mkdir -p "${PACK_BOUNDARY_ROOT}/repo/scripts" "${PACK_BOUNDARY_ROOT}/identity/alpha/scripts"
python3 - "${PACK_BOUNDARY_ROOT}" <<'PY'
from pathlib import Path
import sys
import yaml
root = Path(sys.argv[1]).resolve()
uuid_token = "-".join(["9" * 8, "8" * 4, "7" * 4, "6" * 4, "5" * 12])
(root / "repo" / "scripts" / "good.sh").write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
(root / "identity" / "alpha" / "scripts" / "bad_pack.py").write_text(
    "THREAD_ID = \"" + uuid_token + "\"\n",
    encoding="utf-8",
)
catalog = {
    "default_identity": "alpha",
    "identities": [
        {
            "id": "alpha",
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
            "pack_path": str((root / "identity" / "alpha").resolve()),
        }
    ],
}
(root / "catalog.local.yaml").write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY
PACK_BOUNDARY_JSON="$(run_expect active_pack_negative 1 python3 "${REPO_ROOT}/scripts/validate_executable_surface_runtime_literal_lock.py" --repo-root "${PACK_BOUNDARY_ROOT}/repo" --catalog "${PACK_BOUNDARY_ROOT}/catalog.local.yaml" --include-active-pack-scripts --json-only)"
assert_json_field "${PACK_BOUNDARY_JSON}" 'obj.get("executable_surface_runtime_literal_lock_status") == "FAIL_REQUIRED"'
assert_json_field "${PACK_BOUNDARY_JSON}" 'any(v.get("origin") == "active_pack" for v in (obj.get("violations") or []))'

echo "[PASS] executable surface runtime literal lock probes passed"
