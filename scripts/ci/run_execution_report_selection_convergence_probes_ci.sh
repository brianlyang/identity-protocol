#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/exec-report-selection-convergence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${TMP_ROOT}" "${REPO_ROOT}" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from execution_report_selection_common import collect_reports
from full_identity_protocol_scan import _latest_runtime_report as full_scan_latest_runtime_report
from primary_execution_report_common import latest_primary_execution_report_from_roots
from report_three_plane_status import _latest_report as three_plane_latest_report


def _run_json(cmd: list[str], *, cwd: Path) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise AssertionError(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )
    try:
        return json.loads(proc.stdout.strip())
    except Exception as exc:
        raise AssertionError({"cmd": cmd, "stdout": proc.stdout, "stderr": proc.stderr, "error": str(exc)})


def _run_ok(cmd: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise AssertionError(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )
    return proc.stdout.strip()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


tmp_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
workspace_root = (tmp_root / "workspace").resolve()
identity_id = "probe-identity"
run_id = f"identity-upgrade-exec-{identity_id}-100"
report_name = f"{run_id}.json"

repo_catalog = (workspace_root / "identity" / "catalog" / "identities.yaml").resolve()
local_catalog = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
pack_root = (workspace_root / ".identity" / identity_id).resolve()
prompt_path = (pack_root / "IDENTITY_PROMPT.md").resolve()
task_path = (pack_root / "CURRENT_TASK.json").resolve()
report_path = (pack_root / "runtime" / "reports" / report_name).resolve()
alternate_report_path = (pack_root / "runtime" / "reports" / f"identity-upgrade-exec-{identity_id}-101.json").resolve()
derivative_receipt_path = (
    pack_root / "runtime" / "reports" / "postexec" / f"{run_id}-postexec-receipt.json"
).resolve()
foreign_upgrade_path = (workspace_root / "resource" / "reports" / "foreign-upgrade-history.json").resolve()

prompt_path.parent.mkdir(parents=True, exist_ok=True)
prompt_path.write_text("# Probe Identity\n", encoding="utf-8")
task_path.write_text(json.dumps({"agent_identity": {"id": identity_id}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

catalog_payload = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_root),
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
    ]
}
_write_json(repo_catalog, catalog_payload)
_write_json(local_catalog, catalog_payload)

os.environ["PROJECT_ROOT"] = str(workspace_root)
os.environ["CODEX_HOME"] = str(workspace_root)
os.environ["IDENTITY_HOME"] = str((workspace_root / ".identity").resolve())
os.environ["IDENTITY_PROTOCOL_HOME"] = str(repo_root)
os.environ["IDENTITY_CATALOG"] = str(local_catalog)
os.environ["IDENTITY_SCOPE"] = "USER"

head_sha = subprocess.run(
    ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip().lower()

report_payload = {
    "run_id": run_id,
    "identity_id": identity_id,
    "catalog_path": str(local_catalog),
    "resolved_pack_path": str(pack_root),
    "identity_prompt_path": str(prompt_path),
    "identity_prompt_sha256": _sha256(prompt_path),
    "identity_prompt_bytes": int(prompt_path.stat().st_size),
    "identity_prompt_activated_at": "2026-03-28T00:00:00Z",
    "identity_prompt_source_layer": "global",
    "identity_prompt_scope": "USER",
    "identity_prompt_status": "ACTIVATED",
    "upgrade_required": False,
    "prompt_change_required": False,
    "prompt_change_applied": False,
    "identity_prompt_hash_before": _sha256(prompt_path),
    "identity_prompt_hash_after": _sha256(prompt_path),
    "identity_prompt_change_note": "no_prompt_change_required",
    "prompt_policy_hash": _sha256(prompt_path),
    "runtime_state_artifact_path": "runtime/state/prompt-runtime-state.json",
    "runtime_state_artifact_hash": "",
    "prompt_runtime_state_binding_status": "PASS_REQUIRED",
    "prompt_runtime_state_externalization_status": "PASS_REQUIRED",
    "permission_state": "WRITEBACK_WRITTEN",
    "permission_error_code": "",
    "writeback_status": "WRITTEN",
    "writeback_precheck": {"all_writable": True},
    "protocol_root": str(repo_root),
    "protocol_commit_sha": head_sha,
    "protocol_head_sha_at_run_start": head_sha,
    "baseline_reference_mode": "run_pinned",
}
runtime_state_path = (pack_root / "runtime" / "state" / "prompt-runtime-state.json").resolve()
_write_json(
    runtime_state_path,
    {
        "prompt_policy_hash": report_payload["prompt_policy_hash"],
        "prompt_state": "externalized",
    },
)
report_payload["runtime_state_artifact_hash"] = _sha256(runtime_state_path)
_write_json(report_path, report_payload)
_write_json(
    derivative_receipt_path,
    {
        **report_payload,
        "run_id": run_id,
        "postexec_status": "PASS_REQUIRED",
    },
)
_write_json(
    foreign_upgrade_path,
    {
        **report_payload,
        "identity_id": "foreign-identity",
        "resolved_pack_path": str((workspace_root / ".identity" / "foreign-identity").resolve()),
    },
)

os.utime(prompt_path, (100.0, 100.0))
os.utime(task_path, (100.0, 100.0))
os.utime(report_path, (200.0, 200.0))
os.utime(derivative_receipt_path, (300.0, 300.0))
os.utime(foreign_upgrade_path, (400.0, 400.0))

collected = collect_reports(pack_root, identity_id, include_generic_upgrade_json=True)
assert derivative_receipt_path not in collected, {
    "case": "derivative_receipt_excluded_from_primary_report_candidates",
    "collected": [str(p) for p in collected],
    "forbidden": str(derivative_receipt_path),
}

freshness_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_execution_report_freshness.py"),
        "--identity-id",
        identity_id,
        "--catalog",
        str(local_catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--json-only",
    ],
    cwd=repo_root,
)
baseline_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_protocol_baseline_freshness.py"),
        "--identity-id",
        identity_id,
        "--catalog",
        str(local_catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--json-only",
    ],
    cwd=repo_root,
)
run_id_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_run_id_report_selection.py"),
        "--identity-id",
        identity_id,
        "--catalog",
        str(local_catalog),
        "--run-id",
        run_id,
        "--json-only",
    ],
    cwd=repo_root,
)
locator_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "resolve_latest_identity_upgrade_report.py"),
        "--identity-id",
        identity_id,
        "--search-root",
        str((pack_root / "runtime" / "reports").resolve()),
        "--json-only",
    ],
    cwd=repo_root,
)
prompt_activation_stdout = _run_ok(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_prompt_activation.py"),
        "--identity-id",
        identity_id,
        "--catalog",
        str(local_catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--report-dir",
        str((pack_root / "runtime" / "reports").resolve()),
    ],
    cwd=repo_root,
)
prompt_lifecycle_stdout = _run_ok(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_prompt_lifecycle.py"),
        "--identity-id",
        identity_id,
        "--report-dir",
        str((pack_root / "runtime" / "reports").resolve()),
    ],
    cwd=repo_root,
)
permission_stdout = _run_ok(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_permission_state.py"),
        "--identity-id",
        identity_id,
        "--report-dir",
        str((pack_root / "runtime" / "reports").resolve()),
    ],
    cwd=repo_root,
)
experience_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_experience_writeback.py"),
        "--identity-id",
        identity_id,
        "--repo-catalog",
        str(repo_catalog),
        "--local-catalog",
        str(local_catalog),
        "--json-only",
    ],
    cwd=repo_root,
)
three_plane_selected_report = str(
    three_plane_latest_report(
        identity_id,
        str((workspace_root / ".identity").resolve()),
        str(pack_root),
    )
    or ""
).strip()
full_scan_selected_report = str(
    full_scan_latest_runtime_report(identity_id, (pack_root / "runtime" / "reports").resolve()) or ""
).strip()

_write_json(
    alternate_report_path,
    {
        **report_payload,
        "run_id": f"identity-upgrade-exec-{identity_id}-101",
        "identity_prompt_sha256": "mismatched-prompt-sha",
        "prompt_policy_hash": "mismatched-prompt-sha",
    },
)
os.utime(alternate_report_path, (250.0, 250.0))
preferred_selected = latest_primary_execution_report_from_roots(
    [(pack_root / "runtime" / "reports").resolve()],
    identity_id,
    preferred_prompt_sha=str(report_payload["identity_prompt_sha256"]),
)

selected_freshness = str(freshness_payload.get("report_selected_path", "")).strip()
selected_baseline = str(baseline_payload.get("report_selected_path", "")).strip()
selected_run_id = str(run_id_payload.get("report_selected_path", "")).strip()
selected_locator = str(locator_payload.get("selected_report_path", "")).strip()
selected_experience = str(experience_payload.get("report_selected_path", "")).strip()
expected = str(report_path)

assert selected_freshness == expected, {
    "case": "freshness_selects_primary_execution_report",
    "selected": selected_freshness,
    "expected": expected,
}
assert selected_baseline == expected, {
    "case": "baseline_selects_same_primary_execution_report",
    "selected": selected_baseline,
    "expected": expected,
}
assert selected_run_id == expected, {
    "case": "run_id_selection_ignores_derivative_receipt",
    "selected": selected_run_id,
    "expected": expected,
}
assert selected_locator == expected, {
    "case": "locator_selects_primary_execution_report",
    "selected": selected_locator,
    "expected": expected,
    "payload": locator_payload,
}
assert selected_experience == expected, {
    "case": "experience_writeback_selects_primary_execution_report",
    "selected": selected_experience,
    "expected": expected,
    "payload": experience_payload,
}
assert three_plane_selected_report == expected, {
    "case": "three_plane_selects_primary_execution_report",
    "selected": three_plane_selected_report,
    "expected": expected,
    "preferred_pack": str(pack_root),
}
assert full_scan_selected_report == expected, {
    "case": "full_scan_selects_primary_execution_report",
    "selected": full_scan_selected_report,
    "expected": expected,
    "report_dir": str((pack_root / "runtime" / "reports").resolve()),
}
assert preferred_selected == report_path, {
    "case": "shared_primitive_prefers_prompt_matching_report",
    "selected": str(preferred_selected) if preferred_selected is not None else "",
    "expected": expected,
    "alternate_report": str(alternate_report_path),
}
assert "[OK] identity prompt activation validated:" in prompt_activation_stdout, prompt_activation_stdout
assert "[OK] prompt lifecycle validated:" in prompt_lifecycle_stdout, prompt_lifecycle_stdout
assert "[OK] permission state validated:" in permission_stdout, permission_stdout
assert selected_freshness == selected_baseline == selected_run_id == selected_locator == selected_experience == three_plane_selected_report == full_scan_selected_report, {
    "case": "selection_convergence",
    "freshness": selected_freshness,
    "baseline": selected_baseline,
    "run_id": selected_run_id,
    "locator": selected_locator,
    "experience_writeback": selected_experience,
    "three_plane": three_plane_selected_report,
    "full_scan": full_scan_selected_report,
}

print(
    json.dumps(
        {
            "execution_report_selection_convergence_probe_status": "PASS_REQUIRED",
            "selected_report_path": expected,
            "candidate_count": len(collected),
            "freshness_status": freshness_payload.get("freshness_status", ""),
            "baseline_status": baseline_payload.get("baseline_status", ""),
            "run_id_selection_strategy": run_id_payload.get("selection_strategy", ""),
            "primary_report_locator_selection_mode": locator_payload.get("selection_mode", ""),
            "prompt_activation_selected_report": expected,
            "prompt_lifecycle_selected_report": expected,
            "permission_state_selected_report": expected,
            "experience_writeback_selected_report": expected,
            "three_plane_selected_report": expected,
            "full_scan_selected_report": expected,
            "prompt_sha_preferred_selected_report": str(preferred_selected) if preferred_selected is not None else "",
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] execution report selection convergence probes passed"
