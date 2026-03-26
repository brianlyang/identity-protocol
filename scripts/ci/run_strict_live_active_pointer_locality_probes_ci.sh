#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/strict-live-active-pointer-locality.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

python3 - <<'PY' "${TMP_ROOT}"
import json
import sys
from pathlib import Path

sys.path.insert(0, str((Path.cwd() / "scripts").resolve()))
from strict_live_evidence_resolution_common import resolve_active_execution_context

base = Path(sys.argv[1]).resolve()
identity_id = "strict-live-pointer-probe"

source_pack = base / "source/.identity" / identity_id
clone_pack = base / "clone/.identity" / identity_id
workspace_pack = base / "workspace/.identity" / identity_id
workspace_root = workspace_pack.parent.parent

for pack in (source_pack, clone_pack, workspace_pack):
    (pack / "runtime/reports").mkdir(parents=True, exist_ok=True)
    (pack / "runtime/state").mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.resolve()


def make_report(path: Path, *, run_id: str, resolved_pack_path: Path) -> Path:
    return write_json(
        path,
        {
            "run_id": run_id,
            "session_id": f"run:{run_id}",
            "resolved_pack_path": str(resolved_pack_path.resolve()),
            "report_path": str(path.resolve()),
        },
    )


external_report = make_report(
    source_pack / "runtime/reports" / f"identity-upgrade-exec-{identity_id}-runA.json",
    run_id="runA",
    resolved_pack_path=source_pack,
)
write_json(
    clone_pack / "runtime/state/active_execution_report.json",
    {
        "run_id": "runA",
        "report_path": str(external_report),
    },
)
rejected = resolve_active_execution_context(clone_pack)
assert rejected["report_path"] == "", rejected
assert rejected["report_doc"] == {}, rejected
assert rejected["run_id"] == "runA", rejected
assert rejected["report_resolution_mode"] == "external_pointer_report_rejected", rejected

clone_local_report = make_report(
    clone_pack / "runtime/reports" / external_report.name,
    run_id="runA",
    resolved_pack_path=clone_pack,
)
rehomed = resolve_active_execution_context(clone_pack)
assert rehomed["report_path"] == str(clone_local_report), rehomed
assert rehomed["run_id"] == "runA", rehomed
assert rehomed["report_doc"].get("resolved_pack_path") == str(clone_pack.resolve()), rehomed
assert rehomed["report_resolution_mode"] == "pointer_report_name_rehomed_candidate_root", rehomed

workspace_report = make_report(
    workspace_root / "resource/reports" / f"identity-upgrade-exec-{identity_id}-runB.json",
    run_id="runB",
    resolved_pack_path=workspace_pack,
)
write_json(
    workspace_pack / "runtime/state/active_execution_report.json",
    {
        "run_id": "runB",
        "report_path": str(workspace_report),
    },
)
candidate_root_bound = resolve_active_execution_context(workspace_pack)
assert candidate_root_bound["report_path"] == str(workspace_report), candidate_root_bound
assert candidate_root_bound["run_id"] == "runB", candidate_root_bound
assert candidate_root_bound["report_resolution_mode"] == "pointer_candidate_root_report", candidate_root_bound

print(
    json.dumps(
        {
            "strict_live_active_pointer_locality_probe_status": "PASS_REQUIRED",
            "external_pointer_rejection_status": "PASS_REQUIRED",
            "report_name_rehome_status": "PASS_REQUIRED",
            "candidate_root_binding_status": "PASS_REQUIRED",
            "external_pointer_resolution_mode": rejected["report_resolution_mode"],
            "rehome_resolution_mode": rehomed["report_resolution_mode"],
            "candidate_root_resolution_mode": candidate_root_bound["report_resolution_mode"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] strict-live active pointer locality probes passed"
