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

from actor_session_common import actor_session_path, write_actor_binding_store
from execution_report_selection_common import collect_reports
from primary_execution_report_common import (
    latest_primary_execution_report_from_roots,
    report_logical_identity_key,
)


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


def _run_json_with_rc(cmd: list[str], *, cwd: Path) -> tuple[int, dict[str, object]]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
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


def _three_plane_report_selected_path(payload: dict[str, object]) -> str:
    instance_plane = payload.get("instance_plane_detail") or {}
    if not isinstance(instance_plane, dict):
        return ""
    freshness = instance_plane.get("execution_report_freshness") or {}
    if not isinstance(freshness, dict):
        return ""
    return str(freshness.get("report_selected_path", "")).strip()


def _scan_report_selected_path(payload: dict[str, object], identity_id: str) -> str:
    identity_rows: list[dict[str, object]] = []
    direct_identities = payload.get("identities") or []
    if isinstance(direct_identities, dict):
        for key, value in direct_identities.items():
            if isinstance(value, dict):
                row = dict(value)
                row.setdefault("identity_id", key)
                identity_rows.append(row)
    elif isinstance(direct_identities, list):
        identity_rows.extend([item for item in direct_identities if isinstance(item, dict)])

    catalogs = payload.get("catalogs") or []
    if isinstance(catalogs, list):
        for catalog in catalogs:
            if not isinstance(catalog, dict):
                continue
            catalog_identities = catalog.get("identities") or []
            if isinstance(catalog_identities, list):
                identity_rows.extend([item for item in catalog_identities if isinstance(item, dict)])

    target = next(
        (
            item for item in identity_rows
            if str(item.get("identity_id", "")).strip() == identity_id
        ),
        {},
    )
    checks = target.get("checks") if isinstance(target, dict) else {}
    if not isinstance(checks, dict):
        return ""
    freshness = checks.get("execution_report_freshness") or {}
    if not isinstance(freshness, dict):
        return ""
    return str(freshness.get("report_selected_path", "")).strip()


def _selected_report_path_from_ok_stdout(stdout: str, prefix: str) -> str:
    token = str(prefix or "").strip()
    for line in str(stdout or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(token):
            return stripped.removeprefix(token).strip()
    return ""


def _logical_identity_key_from_path(path_text: str) -> str:
    token = str(path_text or "").strip()
    if not token:
        return ""
    path = Path(token).expanduser().resolve()
    if not path.exists() or not path.is_file():
        return ""
    return report_logical_identity_key(path)


tmp_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
workspace_root = (tmp_root / "workspace").resolve()
identity_id = "probe-identity"
actor_id = "assistant:codex"
session_id = "run:probe-exec-report-selection"
run_id = f"identity-upgrade-exec-{identity_id}-100"
report_name = f"{run_id}.json"

repo_catalog = (workspace_root / "identity" / "catalog" / "identities.yaml").resolve()
local_catalog = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
global_catalog = (workspace_root / ".identity" / "global-catalog.local.yaml").resolve()
pack_root = (workspace_root / ".identity" / identity_id).resolve()
prompt_path = (pack_root / "IDENTITY_PROMPT.md").resolve()
task_path = (pack_root / "CURRENT_TASK.json").resolve()
report_path = (pack_root / "runtime" / "reports" / report_name).resolve()
alternate_report_path = (pack_root / "runtime" / "reports" / f"identity-upgrade-exec-{identity_id}-101.json").resolve()
detached_search_root = (workspace_root / "detached-upgrade-reports").resolve()
detached_report_path = (detached_search_root / report_name).resolve()
detached_alternate_report_path = (detached_search_root / f"identity-upgrade-exec-{identity_id}-101.json").resolve()
detached_foreign_prompt_match_path = (
    detached_search_root / f"identity-upgrade-exec-{identity_id}-102.json"
).resolve()
derivative_receipt_path = (
    pack_root / "runtime" / "reports" / "postexec" / f"{run_id}-postexec-receipt.json"
).resolve()
foreign_upgrade_path = (workspace_root / "resource" / "reports" / "foreign-upgrade-history.json").resolve()
foreign_pack_root = (workspace_root / ".identity" / f"{identity_id}-foreign-pack").resolve()
foreign_prompt_path = (foreign_pack_root / "IDENTITY_PROMPT.md").resolve()
foreign_catalog_path = (workspace_root / ".identity" / "foreign-catalog.local.yaml").resolve()

prompt_path.parent.mkdir(parents=True, exist_ok=True)
prompt_path.write_text("# Probe Identity\n", encoding="utf-8")
task_path.write_text(
    json.dumps(
        {
            "agent_identity": {"id": identity_id},
            "instance_base_repo_mutation_policy_v1": {
                "required": False,
                "report_glob": f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
            },
            "cross_workflow_evidence_schema_contract_v1": {
                "required": True,
                "evidence_path_pattern": f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

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
_write_json(global_catalog, {"identities": []})

os.environ["PROJECT_ROOT"] = str(workspace_root)
os.environ["CODEX_HOME"] = str(workspace_root)
os.environ["IDENTITY_HOME"] = str((workspace_root / ".identity").resolve())
os.environ["IDENTITY_RUNTIME_TMP_ROOT"] = str((workspace_root / ".tmp").resolve())
os.environ["IDENTITY_PROTOCOL_HOME"] = str(repo_root)
os.environ["IDENTITY_CATALOG"] = str(local_catalog)
os.environ["IDENTITY_SCOPE"] = "USER"
os.environ["CODEX_ACTOR_ID"] = actor_id
os.environ["CODEX_SESSION_ID"] = session_id

write_actor_binding_store(
    actor_session_path(local_catalog, actor_id),
    {
        "actor_id": actor_id,
        "catalog_path": str(local_catalog),
        "binding_version": 1,
        "compare_token": "1",
        "bindings": [
            {
                "actor_id": actor_id,
                "catalog_path": str(local_catalog),
                "identity_id": identity_id,
                "session_id": session_id,
                "run_id": session_id.removeprefix("run:"),
                "binding_ref": f"{actor_id}:{identity_id}:{session_id}:v1",
                "binding_version": 1,
                "mutation_lane": "activate",
                "bound_at": "2026-03-28T00:00:00Z",
                "updated_at": "2026-03-28T00:00:00Z",
            }
        ],
    },
)

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
    "route_action": "route-approved",
    "quality_meta_state": "governed-pass",
    "dedup_state": "dedup-ok",
    "schema_version": "v1",
    "protocol_mode": "mode_a_shared",
    "all_ok": True,
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
_write_json(detached_report_path, report_payload)
_write_json(
    detached_alternate_report_path,
    {
        **report_payload,
        "run_id": f"identity-upgrade-exec-{identity_id}-101",
        "identity_prompt_sha256": "mismatched-prompt-sha",
        "prompt_policy_hash": "mismatched-prompt-sha",
    },
)
_write_json(
    detached_foreign_prompt_match_path,
    {
        **report_payload,
        "run_id": f"identity-upgrade-exec-{identity_id}-102",
        "catalog_path": str(foreign_catalog_path),
        "resolved_pack_path": str(foreign_pack_root),
        "identity_prompt_path": str(foreign_prompt_path),
    },
)

os.utime(prompt_path, (100.0, 100.0))
os.utime(task_path, (100.0, 100.0))
os.utime(report_path, (200.0, 200.0))
os.utime(derivative_receipt_path, (300.0, 300.0))
os.utime(foreign_upgrade_path, (400.0, 400.0))
os.utime(detached_report_path, (200.0, 200.0))
os.utime(detached_alternate_report_path, (250.0, 250.0))
os.utime(detached_foreign_prompt_match_path, (275.0, 275.0))

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
prompt_activation_cmd = [
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
]
prompt_activation_stdout = _run_ok(prompt_activation_cmd, cwd=repo_root)
prompt_lifecycle_cmd = [
    sys.executable,
    str(repo_root / "scripts" / "validate_identity_prompt_lifecycle.py"),
    "--identity-id",
    identity_id,
    "--report-dir",
    str((pack_root / "runtime" / "reports").resolve()),
]
prompt_lifecycle_stdout = _run_ok(prompt_lifecycle_cmd, cwd=repo_root)
permission_cmd = [
    sys.executable,
    str(repo_root / "scripts" / "validate_identity_permission_state.py"),
    "--identity-id",
    identity_id,
    "--report-dir",
    str((pack_root / "runtime" / "reports").resolve()),
]
permission_stdout = _run_ok(permission_cmd, cwd=repo_root)
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
three_plane_out = (workspace_root / "three-plane.json").resolve()
three_plane_cmd = [
    sys.executable,
    str(repo_root / "scripts" / "report_three_plane_status.py"),
    "--identity-id",
    identity_id,
    "--actor-id",
    actor_id,
    "--session-id",
    session_id,
    "--catalog",
    str(local_catalog),
    "--repo-catalog",
    str(repo_catalog),
    "--out",
    str(three_plane_out),
]
_run_ok(three_plane_cmd, cwd=repo_root)
three_plane_payload = json.loads(three_plane_out.read_text(encoding="utf-8"))
scan_out = (workspace_root / "full-scan.json").resolve()
scan_cmd = [
    sys.executable,
    str(repo_root / "scripts" / "full_identity_protocol_scan.py"),
    "--scan-mode",
    "target",
    "--identity-ids",
    identity_id,
    "--actor-id",
    actor_id,
    "--session-id",
    session_id,
    "--project-catalog",
    str(local_catalog),
    "--global-catalog",
    str(global_catalog),
    "--out",
    str(scan_out),
]
_run_ok(scan_cmd, cwd=repo_root)
scan_payload = json.loads(scan_out.read_text(encoding="utf-8"))

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
three_plane_after_out = (workspace_root / "three-plane-after.json").resolve()
three_plane_after_cmd = list(three_plane_cmd)
three_plane_after_cmd[-1] = str(three_plane_after_out)
_run_ok(three_plane_after_cmd, cwd=repo_root)
three_plane_after_payload = json.loads(three_plane_after_out.read_text(encoding="utf-8"))
scan_after_out = (workspace_root / "full-scan-after.json").resolve()
scan_after_cmd = list(scan_cmd)
scan_after_cmd[-1] = str(scan_after_out)
_run_ok(scan_after_cmd, cwd=repo_root)
scan_after_payload = json.loads(scan_after_out.read_text(encoding="utf-8"))
search_root_locator_after_payload = _run_json(
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
pack_locator_after_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "resolve_latest_identity_upgrade_report.py"),
        "--identity-id",
        identity_id,
        "--pack-root",
        str(pack_root),
        "--json-only",
    ],
    cwd=repo_root,
)
detached_locator_without_catalog_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "resolve_latest_identity_upgrade_report.py"),
        "--identity-id",
        identity_id,
        "--search-root",
        str(detached_search_root),
        "--json-only",
    ],
    cwd=repo_root,
)
catalog_detached_locator_after_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "resolve_latest_identity_upgrade_report.py"),
        "--identity-id",
        identity_id,
        "--catalog",
        str(local_catalog),
        "--search-root",
        str(detached_search_root),
        "--json-only",
    ],
    cwd=repo_root,
)
repair_prompt_rc, repair_prompt_payload = _run_json_with_rc(
    [
        sys.executable,
        str(repo_root / "scripts" / "repair_identity_prompt_runtime_state.py"),
        "--catalog",
        str(local_catalog),
        "--identity-id",
        identity_id,
        "--json-only",
    ],
    cwd=repo_root,
)
repair_postexec_rc, repair_postexec_payload = _run_json_with_rc(
    [
        sys.executable,
        str(repo_root / "scripts" / "repair_identity_post_execution_mandatory.py"),
        "--catalog",
        str(local_catalog),
        "--repo-catalog",
        str(repo_catalog),
        "--identity-id",
        identity_id,
        "--json-only",
    ],
    cwd=repo_root,
)
prompt_activation_after_stdout = _run_ok(prompt_activation_cmd, cwd=repo_root)
prompt_lifecycle_after_stdout = _run_ok(prompt_lifecycle_cmd, cwd=repo_root)
permission_after_stdout = _run_ok(permission_cmd, cwd=repo_root)
mode_promotion_payload = _run_json(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_identity_mode_promotion_arbitration.py"),
        "--identity-id",
        identity_id,
        "--repo-catalog",
        str(repo_catalog),
        "--local-catalog",
        str(local_catalog),
        "--changed-file",
        f"identity/{identity_id}/CURRENT_TASK.json",
        "--json-only",
    ],
    cwd=repo_root,
)
base_repo_write_boundary_payload = _run_json(
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
)
cross_workflow_payload = _run_json(
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
)
required_contract_coverage_rc, required_contract_coverage_payload = _run_json_with_rc(
    [
        sys.executable,
        str(repo_root / "scripts" / "validate_required_contract_coverage.py"),
        "--catalog",
        str(local_catalog),
        "--identity-id",
        identity_id,
        "--report-selected-path",
        str(report_path),
        "--json-only",
    ],
    cwd=repo_root,
)
assert required_contract_coverage_rc in {0, 1}, {
    "case": "required_contract_coverage_returns_machine_readable_status",
    "rc": required_contract_coverage_rc,
    "payload": required_contract_coverage_payload,
}

selected_freshness = str(freshness_payload.get("report_selected_path", "")).strip()
selected_baseline = str(baseline_payload.get("report_selected_path", "")).strip()
selected_run_id = str(run_id_payload.get("report_selected_path", "")).strip()
selected_locator = str(locator_payload.get("selected_report_path", "")).strip()
selected_experience = str(experience_payload.get("report_selected_path", "")).strip()
selected_three_plane = _three_plane_report_selected_path(three_plane_payload)
selected_three_plane_after = _three_plane_report_selected_path(three_plane_after_payload)
selected_scan = _scan_report_selected_path(scan_payload, identity_id)
selected_scan_after = _scan_report_selected_path(scan_after_payload, identity_id)
selected_search_root_locator_after = str(search_root_locator_after_payload.get("selected_report_path", "")).strip()
selected_pack_locator_after = str(pack_locator_after_payload.get("selected_report_path", "")).strip()
selected_detached_locator_without_catalog = str(detached_locator_without_catalog_payload.get("selected_report_path", "")).strip()
selected_catalog_detached_locator_after = str(catalog_detached_locator_after_payload.get("selected_report_path", "")).strip()
selected_repair_prompt = str(repair_prompt_payload.get("report_selected_path", "")).strip()
selected_repair_postexec = str(repair_postexec_payload.get("report_selected_path", "")).strip()
selected_prompt_activation_after = _selected_report_path_from_ok_stdout(
    prompt_activation_after_stdout,
    "[OK] identity prompt activation validated:",
)
selected_prompt_lifecycle_after = _selected_report_path_from_ok_stdout(
    prompt_lifecycle_after_stdout,
    "[OK] prompt lifecycle validated:",
)
selected_permission_after = _selected_report_path_from_ok_stdout(
    permission_after_stdout,
    "[OK] permission state validated:",
)
selected_mode_promotion = str(mode_promotion_payload.get("report_selected_path", "")).strip()
selected_base_repo_write_boundary = str(base_repo_write_boundary_payload.get("report_selected_path", "")).strip()
selected_cross_workflow_evidence = str(cross_workflow_payload.get("evidence_ref", "")).strip()
required_contract_coverage_rows = required_contract_coverage_payload.get("contracts") or []
if not isinstance(required_contract_coverage_rows, list):
    required_contract_coverage_rows = []
cross_workflow_schema_row = next(
    (
        row for row in required_contract_coverage_rows
        if isinstance(row, dict) and str(row.get("name", "")).strip() == "cross_workflow_schema"
    ),
    {},
)
expected = str(report_path)
expected_detached = str(detached_report_path)
expected_detached_unanchored = str(detached_foreign_prompt_match_path)
expected_logical_identity_key = report_logical_identity_key(report_path)
selected_catalog_detached_logical_identity_key = _logical_identity_key_from_path(selected_catalog_detached_locator_after)

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
assert selected_three_plane == expected, {
    "case": "three_plane_selects_primary_execution_report",
    "selected": selected_three_plane,
    "expected": expected,
    "payload": three_plane_payload,
}
assert selected_three_plane_after == expected, {
    "case": "three_plane_preserves_prompt_sha_preference",
    "selected": selected_three_plane_after,
    "expected": expected,
    "payload": three_plane_after_payload,
}
assert selected_scan == expected, {
    "case": "full_scan_selects_primary_execution_report",
    "selected": selected_scan,
    "expected": expected,
    "payload": scan_payload,
}
assert selected_scan_after == expected, {
    "case": "full_scan_preserves_prompt_sha_preference",
    "selected": selected_scan_after,
    "expected": expected,
    "payload": scan_after_payload,
}
assert selected_search_root_locator_after == expected, {
    "case": "search_root_locator_preserves_prompt_sha_preference",
    "selected": selected_search_root_locator_after,
    "expected": expected,
    "payload": search_root_locator_after_payload,
}
assert str(search_root_locator_after_payload.get("selection_mode", "")).strip() == "search_root_latest_primary_execution_report", {
    "case": "search_root_locator_projects_prompt_bound_selection_mode",
    "payload": search_root_locator_after_payload,
}
assert str(search_root_locator_after_payload.get("selected_report_authority_class", "")).strip() == "search_root_latest_primary_execution_report", {
    "case": "search_root_locator_projects_prompt_bound_authority_class",
    "payload": search_root_locator_after_payload,
}
assert selected_pack_locator_after == expected, {
    "case": "pack_root_locator_preserves_prompt_sha_preference",
    "selected": selected_pack_locator_after,
    "expected": expected,
    "payload": pack_locator_after_payload,
}
assert selected_detached_locator_without_catalog == expected_detached_unanchored, {
    "case": "detached_search_root_without_catalog_degrades_to_mtime_surface",
    "selected": selected_detached_locator_without_catalog,
    "expected": expected_detached_unanchored,
    "payload": detached_locator_without_catalog_payload,
}
assert selected_catalog_detached_locator_after == expected_detached, {
    "case": "catalog_anchored_detached_search_root_prefers_matching_pack_projection",
    "selected": selected_catalog_detached_locator_after,
    "expected": expected_detached,
    "payload": catalog_detached_locator_after_payload,
}
assert selected_catalog_detached_logical_identity_key == expected_logical_identity_key, {
    "case": "catalog_anchored_detached_search_root_preserves_logical_report_identity",
    "selected": selected_catalog_detached_logical_identity_key,
    "expected": expected_logical_identity_key,
    "payload": catalog_detached_locator_after_payload,
}
assert str(catalog_detached_locator_after_payload.get("selection_mode", "")).strip() == "search_root_latest_primary_execution_report", {
    "case": "catalog_anchored_detached_search_root_projects_prompt_bound_selection_mode",
    "payload": catalog_detached_locator_after_payload,
}
assert str(catalog_detached_locator_after_payload.get("selected_report_authority_class", "")).strip() == "search_root_latest_primary_execution_report", {
    "case": "catalog_anchored_detached_search_root_projects_prompt_bound_authority_class",
    "payload": catalog_detached_locator_after_payload,
}
assert selected_prompt_activation_after == expected, {
    "case": "prompt_activation_preserves_prompt_sha_preference",
    "selected": selected_prompt_activation_after,
    "expected": expected,
    "stdout": prompt_activation_after_stdout,
}
assert selected_prompt_lifecycle_after == expected, {
    "case": "prompt_lifecycle_preserves_prompt_sha_preference",
    "selected": selected_prompt_lifecycle_after,
    "expected": expected,
    "stdout": prompt_lifecycle_after_stdout,
}
assert selected_permission_after == expected, {
    "case": "permission_state_preserves_prompt_sha_preference",
    "selected": selected_permission_after,
    "expected": expected,
    "stdout": permission_after_stdout,
}
assert selected_mode_promotion == expected, {
    "case": "mode_promotion_arbitration_preserves_prompt_sha_preference",
    "selected": selected_mode_promotion,
    "expected": expected,
    "payload": mode_promotion_payload,
}
assert selected_base_repo_write_boundary == expected, {
    "case": "base_repo_write_boundary_contract_pattern_preserves_prompt_sha_preference",
    "selected": selected_base_repo_write_boundary,
    "expected": expected,
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("base_repo_write_boundary_status", "")).strip() == "PASS_REQUIRED", {
    "case": "base_repo_write_boundary_contract_pattern_returns_machine_pass_status",
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("report_selection_mode", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "base_repo_write_boundary_contract_pattern_projects_selection_mode",
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("report_selected_authority_class", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "base_repo_write_boundary_contract_pattern_projects_authority_class",
    "payload": base_repo_write_boundary_payload,
}
assert str(base_repo_write_boundary_payload.get("report_logical_identity_key", "")).strip() == expected_logical_identity_key, {
    "case": "base_repo_write_boundary_contract_pattern_projects_logical_identity_key",
    "payload": base_repo_write_boundary_payload,
    "expected": expected_logical_identity_key,
}
assert selected_cross_workflow_evidence == expected, {
    "case": "cross_workflow_contract_pattern_preserves_prompt_sha_preference",
    "selected": selected_cross_workflow_evidence,
    "expected": expected,
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("cross_workflow_evidence_normalization_status", "")).strip() == "PASS_REQUIRED", {
    "case": "cross_workflow_contract_pattern_returns_machine_pass_status",
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("evidence_selection_mode", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "cross_workflow_contract_pattern_projects_selection_mode",
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("evidence_selected_authority_class", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "cross_workflow_contract_pattern_projects_authority_class",
    "payload": cross_workflow_payload,
}
assert str(cross_workflow_payload.get("evidence_logical_identity_key", "")).strip() == expected_logical_identity_key, {
    "case": "cross_workflow_contract_pattern_projects_logical_identity_key",
    "payload": cross_workflow_payload,
    "expected": expected_logical_identity_key,
}
assert isinstance(cross_workflow_schema_row, dict) and cross_workflow_schema_row, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_row",
    "payload": required_contract_coverage_payload,
}
assert str(cross_workflow_schema_row.get("evidence_ref", "")).strip() == expected, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_evidence_ref",
    "row": cross_workflow_schema_row,
    "expected": expected,
}
assert str(cross_workflow_schema_row.get("evidence_selection_mode", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "required_contract_coverage_projects_cross_workflow_schema_selection_mode",
    "row": cross_workflow_schema_row,
}
assert str(cross_workflow_schema_row.get("evidence_selected_authority_class", "")).strip() == "pattern_primary_execution_report_family_prompt_bound", {
    "case": "required_contract_coverage_projects_cross_workflow_schema_authority_class",
    "row": cross_workflow_schema_row,
}
assert str(cross_workflow_schema_row.get("evidence_logical_identity_key", "")).strip() == expected_logical_identity_key, {
    "case": "required_contract_coverage_projects_cross_workflow_schema_logical_identity_key",
    "row": cross_workflow_schema_row,
    "expected": expected_logical_identity_key,
}
assert str(mode_promotion_payload.get("mode_promotion_arbitration_status", "")).strip() == "PASS_REQUIRED", {
    "case": "mode_promotion_arbitration_returns_machine_pass_status",
    "payload": mode_promotion_payload,
}
assert preferred_selected == report_path, {
    "case": "shared_primitive_prefers_prompt_matching_report",
    "selected": str(preferred_selected) if preferred_selected is not None else "",
    "expected": expected,
    "alternate_report": str(alternate_report_path),
}
assert selected_repair_prompt == expected, {
    "case": "prompt_runtime_repair_selects_prompt_bound_primary_execution_report",
    "selected": selected_repair_prompt,
    "expected": expected,
    "payload": repair_prompt_payload,
}
assert repair_prompt_rc in {0, 1}, {
    "case": "prompt_runtime_repair_returns_machine_readable_status",
    "rc": repair_prompt_rc,
}
assert selected_repair_postexec == expected, {
    "case": "post_execution_repair_selects_prompt_bound_primary_execution_report",
    "selected": selected_repair_postexec,
    "expected": expected,
    "payload": repair_postexec_payload,
}
assert repair_postexec_rc in {0, 1}, {
    "case": "post_execution_repair_returns_machine_readable_status",
    "rc": repair_postexec_rc,
}
assert "[OK] identity prompt activation validated:" in prompt_activation_stdout, prompt_activation_stdout
assert "[OK] prompt lifecycle validated:" in prompt_lifecycle_stdout, prompt_lifecycle_stdout
assert "[OK] permission state validated:" in permission_stdout, permission_stdout
assert selected_freshness == selected_baseline == selected_run_id == selected_locator == selected_experience == selected_three_plane == selected_three_plane_after == selected_scan == selected_scan_after == selected_search_root_locator_after == selected_pack_locator_after == selected_prompt_activation_after == selected_prompt_lifecycle_after == selected_permission_after == selected_mode_promotion == selected_base_repo_write_boundary == selected_cross_workflow_evidence == selected_repair_prompt == selected_repair_postexec, {
    "case": "selection_convergence",
    "freshness": selected_freshness,
    "baseline": selected_baseline,
    "run_id": selected_run_id,
    "locator": selected_locator,
    "experience_writeback": selected_experience,
    "three_plane": selected_three_plane,
    "three_plane_after": selected_three_plane_after,
    "full_scan": selected_scan,
    "full_scan_after": selected_scan_after,
    "search_root_locator_after": selected_search_root_locator_after,
    "pack_locator_after": selected_pack_locator_after,
    "prompt_activation_after": selected_prompt_activation_after,
    "prompt_lifecycle_after": selected_prompt_lifecycle_after,
    "permission_after": selected_permission_after,
    "mode_promotion_after": selected_mode_promotion,
    "base_repo_write_boundary": selected_base_repo_write_boundary,
    "cross_workflow_evidence": selected_cross_workflow_evidence,
    "repair_prompt_runtime_state": selected_repair_prompt,
    "repair_post_execution_mandatory": selected_repair_postexec,
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
            "three_plane_prompt_sha_selected_report": selected_three_plane_after,
            "full_scan_selected_report": expected,
            "full_scan_prompt_sha_selected_report": selected_scan_after,
            "search_root_locator_prompt_sha_selected_report": selected_search_root_locator_after,
            "pack_root_locator_selected_report": selected_pack_locator_after,
            "detached_search_root_unanchored_selected_report": selected_detached_locator_without_catalog,
            "catalog_anchored_detached_search_root_selected_report": selected_catalog_detached_locator_after,
            "catalog_anchored_detached_search_root_logical_identity_key": selected_catalog_detached_logical_identity_key,
            "expected_logical_identity_key": expected_logical_identity_key,
            "prompt_activation_prompt_sha_selected_report": selected_prompt_activation_after,
            "prompt_lifecycle_prompt_sha_selected_report": selected_prompt_lifecycle_after,
            "permission_state_prompt_sha_selected_report": selected_permission_after,
            "mode_promotion_prompt_sha_selected_report": selected_mode_promotion,
            "base_repo_write_boundary_prompt_sha_selected_report": selected_base_repo_write_boundary,
            "cross_workflow_contract_prompt_sha_selected_report": selected_cross_workflow_evidence,
            "mode_promotion_arbitration_status": mode_promotion_payload.get("mode_promotion_arbitration_status", ""),
            "base_repo_write_boundary_status": base_repo_write_boundary_payload.get("base_repo_write_boundary_status", ""),
            "cross_workflow_evidence_normalization_status": cross_workflow_payload.get("cross_workflow_evidence_normalization_status", ""),
            "repair_prompt_runtime_state_selected_report": selected_repair_prompt,
            "repair_prompt_runtime_state_rc": repair_prompt_rc,
            "repair_post_execution_mandatory_selected_report": selected_repair_postexec,
            "repair_post_execution_mandatory_rc": repair_postexec_rc,
            "prompt_sha_preferred_selected_report": str(preferred_selected) if preferred_selected is not None else "",
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] execution report selection convergence probes passed"
