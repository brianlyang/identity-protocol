#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${ROOT}/scripts/runtime_temp_path_common.sh"

export IDENTITY_RUNTIME_TMP_ROOT="${IDENTITY_RUNTIME_TMP_ROOT:-${ROOT}/.tmp}"
TMP_ROOT="$(identity_runtime_mktemp_dir_sh "workbook-family-scaffold-probes" "run")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

python3 - "${ROOT}" "${TMP_ROOT}" <<'PY'
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str((Path(sys.argv[1]).resolve() / "scripts")))

from workbook_control_plane_common import derive_probe_minor_from_active, load_active_workbook_registry  # noqa: E402


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def ensure_materialized_dir(probe_root: Path, source_root: Path, rel_dir: Path) -> None:
    if str(rel_dir) in {"", "."}:
        return
    parent = rel_dir.parent
    if str(parent) != ".":
        ensure_materialized_dir(probe_root, source_root, parent)
    target = probe_root / rel_dir
    source = source_root / rel_dir
    if target.exists():
        if target.is_symlink():
            target.unlink()
        elif target.is_dir():
            return
        else:
            raise SystemExit(f"cannot materialize directory over file: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        child_target = target / child.name
        if child_target.exists():
            continue
        child_target.symlink_to(child, target_is_directory=child.is_dir())


def build_shadow_repo(source_root: Path, shadow_workspace: Path) -> Path:
    shadow_repo = shadow_workspace / source_root.name
    shadow_workspace.mkdir(parents=True, exist_ok=True)
    shadow_repo.mkdir(parents=True, exist_ok=True)
    for child in source_root.iterdir():
        if child.name in {".git", ".tmp", "__pycache__"}:
            continue
        target = shadow_repo / child.name
        if target.exists():
            continue
        target.symlink_to(child, target_is_directory=child.is_dir())
    ensure_materialized_dir(shadow_repo, source_root, Path("docs/workbook"))
    ensure_materialized_dir(shadow_repo, source_root, Path("identity/protocol/mappings"))
    return shadow_repo


def run_json(cmd: list[str], *, cwd: Path) -> tuple[int, dict]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if not stdout:
        raise SystemExit(f"command produced no stdout: {' '.join(cmd)} stderr={stderr}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"command did not emit JSON: {' '.join(cmd)} stdout={stdout!r} stderr={stderr!r}") from exc
    return proc.returncode, payload


source_root = Path(sys.argv[1]).resolve()
tmp_root = Path(sys.argv[2]).resolve()
bundle = load_active_workbook_registry(source_root)
active_minor = str(bundle.active_family_doc.get("workbook_family", "")).strip()
probe_minor = derive_probe_minor_from_active(active_minor)

shadow_workspace = tmp_root / "workspace"
shadow_repo = build_shadow_repo(source_root, shadow_workspace)

scaffold_cmd = [
    "python3",
    str(shadow_repo / "scripts/scaffold_workbook_family.py"),
    "--minor",
    probe_minor,
    "--repo-root",
    str(shadow_repo),
    "--workspace-root",
    str(shadow_workspace),
    "--json-only",
]
scaffold_rc, scaffold_payload = run_json(scaffold_cmd, cwd=shadow_repo)
if scaffold_rc != 0 or scaffold_payload.get("status") != STATUS_PASS_REQUIRED:
    raise SystemExit(f"scaffold probe failed: {scaffold_payload}")
if scaffold_payload.get("current_pointer_updated"):
    raise SystemExit(f"scaffold probe unexpectedly updated current pointer: {scaffold_payload}")

validator_cmd = [
    "python3",
    str(shadow_repo / "scripts/validate_workbook_family_contract.py"),
    "--minor",
    probe_minor,
    "--repo-root",
    str(shadow_repo),
    "--workspace-root",
    str(shadow_workspace),
    "--json-only",
]
validator_rc, validator_payload = run_json(validator_cmd, cwd=shadow_repo)
if validator_rc != 0 or validator_payload.get("status") != STATUS_PASS_REQUIRED:
    raise SystemExit(f"scaffold contract validator failed: {validator_payload}")

negative_cmd = [
    "python3",
    str(shadow_repo / "scripts/scaffold_workbook_family.py"),
    "--minor",
    probe_minor,
    "--repo-root",
    str(shadow_repo),
    "--workspace-root",
    str(shadow_workspace),
    "--activate-current",
    "--activation-consent-token",
    "wrong-token",
    "--overwrite",
    "--json-only",
]
negative_rc, negative_payload = run_json(negative_cmd, cwd=shadow_repo)
if negative_rc == 0:
    raise SystemExit(f"activation consent negative probe unexpectedly passed: {negative_payload}")
if negative_payload.get("error_code") != "IP-WFSC-003":
    raise SystemExit(f"activation consent negative probe returned wrong error code: {negative_payload}")

print(
    json.dumps(
        {
            "workbook_family_scaffold_probe_status": STATUS_PASS_REQUIRED,
            "active_minor": active_minor,
            "probe_minor": probe_minor,
            "scaffold_status": scaffold_payload.get("status"),
            "validator_status": validator_payload.get("status"),
            "activation_consent_negative_status": STATUS_FAIL_REQUIRED,
            "tmp_root": str(tmp_root),
        },
        ensure_ascii=False,
    )
)
PY
