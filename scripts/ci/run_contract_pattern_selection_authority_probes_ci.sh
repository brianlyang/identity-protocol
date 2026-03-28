#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/contract-pattern-selection-authority-ci.XXXXXX")"
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


def _run_json(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> tuple[int, dict[str, object]]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(proc.stdout.strip())
    except Exception as exc:
        raise AssertionError(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "error": str(exc),
            }
        )
    if not isinstance(payload, dict):
        raise AssertionError(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "error": "json payload must be object",
            }
        )
    return proc.returncode, payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


tmp_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
workspace_root = (tmp_root / "workspace").resolve()
identity_id = "probe-identity"
repo_catalog = (workspace_root / "identity" / "catalog" / "identities.yaml").resolve()
local_catalog = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
pack_root = (workspace_root / ".identity" / identity_id).resolve()
prompt_path = (pack_root / "IDENTITY_PROMPT.md").resolve()
task_path = (pack_root / "CURRENT_TASK.json").resolve()
report_path = (pack_root / "runtime" / "reports" / f"identity-upgrade-exec-{identity_id}-100.json").resolve()

prompt_path.parent.mkdir(parents=True, exist_ok=True)
prompt_path.write_text("# Probe Identity\n", encoding="utf-8")
prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

task_payload = {
    "agent_identity": {"id": identity_id},
    "instance_base_repo_mutation_policy_v1": {
        "required": False,
        "report_glob": f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
    },
    "cross_workflow_evidence_schema_contract_v1": {
        "required": True,
        "evidence_path_pattern": f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
    },
}
task_path.write_text(json.dumps(task_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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

report_payload = {
    "run_id": f"identity-upgrade-exec-{identity_id}-100",
    "identity_id": identity_id,
    "catalog_path": str(local_catalog),
    "resolved_pack_path": str(pack_root),
    "identity_prompt_path": str(prompt_path),
    "identity_prompt_sha256": prompt_sha,
    "identity_prompt_bytes": int(prompt_path.stat().st_size),
    "identity_prompt_activated_at": "2026-03-28T00:00:00Z",
    "identity_prompt_source_layer": "project",
    "identity_prompt_scope": "USER",
    "identity_prompt_status": "ACTIVATED",
    "route_action": "route-approved",
    "quality_meta_state": "governed-pass",
    "dedup_state": "dedup-ok",
    "schema_version": "v1",
}
_write_json(report_path, report_payload)

env = os.environ.copy()
env.update(
    {
        "PROJECT_ROOT": str(workspace_root),
        "CODEX_HOME": str(workspace_root),
        "IDENTITY_HOME": str((workspace_root / ".identity").resolve()),
        "IDENTITY_CATALOG": str(local_catalog),
        "IDENTITY_PROTOCOL_HOME": str(repo_root),
        "PYTHONPATH": str((repo_root / "scripts").resolve()),
    }
)

_, base_repo_write_boundary_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_instance_base_repo_write_boundary.py"),
        "--catalog",
        str(local_catalog),
        "--identity-id",
        identity_id,
        "--json-only",
    ],
    cwd=repo_root,
    env=env,
)
_, cross_workflow_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "normalize_cross_workflow_evidence.py"),
        "--catalog",
        str(local_catalog),
        "--identity-id",
        identity_id,
        "--json-only",
    ],
    cwd=repo_root,
    env=env,
)
coverage_rc, required_contract_coverage_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_required_contract_coverage.py"),
        "--catalog",
        str(local_catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--identity-id",
        identity_id,
        "--json-only",
    ],
    cwd=repo_root,
    env=env,
)

contracts = required_contract_coverage_payload.get("contracts") or []
if not isinstance(contracts, list):
    contracts = []
cross_workflow_schema_row = next(
    (
        row for row in contracts
        if isinstance(row, dict) and str(row.get("name", "")).strip() == "cross_workflow_schema"
    ),
    {},
)

expected_path = str(report_path)
expected_mode = "pattern_primary_execution_report_family_prompt_bound"

assert str(base_repo_write_boundary_payload.get("base_repo_write_boundary_status", "")).strip() == "PASS_REQUIRED", {
    "case": "base_repo_write_boundary_returns_pass",
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("report_selected_path", "")).strip() == expected_path, {
    "case": "base_repo_write_boundary_selects_prompt_bound_report",
    "payload": base_repo_write_boundary_payload,
    "expected": expected_path,
}
assert str(base_repo_write_boundary_payload.get("report_selection_mode", "")).strip() == expected_mode, {
    "case": "base_repo_write_boundary_projects_selection_mode",
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("report_selected_authority_class", "")).strip() == expected_mode, {
    "case": "base_repo_write_boundary_projects_authority_class",
    "payload": base_repo_write_boundary_payload,
}

assert str(cross_workflow_payload.get("cross_workflow_evidence_normalization_status", "")).strip() == "PASS_REQUIRED", {
    "case": "cross_workflow_normalization_returns_pass",
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("evidence_ref", "")).strip() == expected_path, {
    "case": "cross_workflow_normalization_selects_prompt_bound_report",
    "payload": cross_workflow_payload,
    "expected": expected_path,
}
assert str(cross_workflow_payload.get("evidence_selection_mode", "")).strip() == expected_mode, {
    "case": "cross_workflow_normalization_projects_selection_mode",
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("evidence_selected_authority_class", "")).strip() == expected_mode, {
    "case": "cross_workflow_normalization_projects_authority_class",
    "payload": cross_workflow_payload,
}

assert isinstance(cross_workflow_schema_row, dict) and cross_workflow_schema_row, {
    "case": "required_contract_coverage_emits_cross_workflow_schema_row",
    "payload": required_contract_coverage_payload,
}
assert str(cross_workflow_schema_row.get("evidence_ref", "")).strip() == expected_path, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_evidence_ref",
    "row": cross_workflow_schema_row,
    "expected": expected_path,
}
assert str(cross_workflow_schema_row.get("evidence_selection_mode", "")).strip() == expected_mode, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_selection_mode",
    "row": cross_workflow_schema_row,
}
assert str(cross_workflow_schema_row.get("evidence_selected_authority_class", "")).strip() == expected_mode, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_authority_class",
    "row": cross_workflow_schema_row,
}

print(
    json.dumps(
        {
            "contract_pattern_selection_authority_probe_status": "PASS_REQUIRED",
            "coverage_validator_rc": coverage_rc,
            "report_path": expected_path,
            "base_repo_write_boundary_report_selection_mode": str(
                base_repo_write_boundary_payload.get("report_selection_mode", "")
            ).strip(),
            "cross_workflow_evidence_selection_mode": str(
                cross_workflow_payload.get("evidence_selection_mode", "")
            ).strip(),
            "required_contract_coverage_cross_workflow_schema_selection_mode": str(
                cross_workflow_schema_row.get("evidence_selection_mode", "")
            ).strip(),
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] contract-pattern selection authority probes passed"
