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
    "protocol_root": str(repo_root),
    "protocol_commit_sha": head_sha,
    "protocol_head_sha_at_run_start": head_sha,
    "baseline_reference_mode": "run_pinned",
}
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

selected_freshness = str(freshness_payload.get("report_selected_path", "")).strip()
selected_baseline = str(baseline_payload.get("report_selected_path", "")).strip()
selected_run_id = str(run_id_payload.get("report_selected_path", "")).strip()
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
assert selected_freshness == selected_baseline == selected_run_id, {
    "case": "selection_convergence",
    "freshness": selected_freshness,
    "baseline": selected_baseline,
    "run_id": selected_run_id,
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
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] execution report selection convergence probes passed"
