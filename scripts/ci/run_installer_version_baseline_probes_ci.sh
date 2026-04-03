#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${INSTALLER_BASELINE_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-installer-version-baseline-probes}"
FIXTURE_ROOT="${WORK_ROOT}/fixtures"
RESULT_ROOT="${WORK_ROOT}/results"
REPORT_DIR="${WORK_ROOT}/reports"
BACKUP_DIR="${WORK_ROOT}/backups"
MANIFEST_PATH="${WORK_ROOT}/manifest.installer_version_baseline_probes.json"
PROBE_RUNNER="${WORK_ROOT}/installer_probe_runner.py"

mkdir -p "${FIXTURE_ROOT}" "${RESULT_ROOT}" "${REPORT_DIR}" "${BACKUP_DIR}"

SOURCE_PACK="${FIXTURE_ROOT}/source/probe-install-baseline"
TARGET_ROOT="${FIXTURE_ROOT}/instances"
CATALOG_PATH="${FIXTURE_ROOT}/catalog.local.yaml"
REPO_CATALOG_PATH="${FIXTURE_ROOT}/repo-catalog.yaml"
IDENTITY_ID="probe-install-baseline"

python3 - <<'PY' "${SOURCE_PACK}" "${CATALOG_PATH}" "${REPO_CATALOG_PATH}" "${IDENTITY_ID}"
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

source_pack = Path(sys.argv[1]).resolve()
catalog_path = Path(sys.argv[2]).resolve()
repo_catalog_path = Path(sys.argv[3]).resolve()
identity_id = sys.argv[4]

(source_pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)

task = {
    "agent_identity": {
        "id": identity_id,
        "methodology_version": "v1.5",
        "prompt_version": "v1.5",
        "json_version": "v1.5",
    },
    "scaffold_metadata": {
        "protocol_contract_version": "v1.5.0",
        "required_version_stream": "v1.5",
        "required_gate_bundle_contract_version": "v1.6.6",
        "identity_protocol_version": "v1.5",
    },
}

meta = {
    "id": identity_id,
    "methodology_version": "v1.5",
}

source_pack.joinpath("CURRENT_TASK.json").write_text(
    json.dumps(task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
source_pack.joinpath("META.yaml").write_text(
    yaml.safe_dump(meta, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
source_pack.joinpath("IDENTITY_PROMPT.md").write_text(
    "# Probe Identity Prompt\n\nIdentity-Context first line probe.\n",
    encoding="utf-8",
)

catalog = {
    "version": "1.0",
    "default_identity": "",
    "identities": [],
}
catalog_path.write_text(
    yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)

repo_catalog = {
    "version": "1.0",
    "default_identity": "",
    "identities": [],
}
repo_catalog_path.write_text(
    yaml.safe_dump(repo_catalog, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
PY

cat > "${PROBE_RUNNER}" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _resolve_baseline(repo_root: Path) -> dict[str, Any]:
    entry = repo_root / "identity/protocol/mappings/version-baseline.current.yaml"
    entry_doc = _load_yaml(entry)
    active_file = str(entry_doc.get("active_file", "")).strip()
    if not active_file:
        raise RuntimeError("version_baseline_active_file_missing")
    baseline = _load_yaml((repo_root / active_file).resolve())
    return baseline


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _latest_report(report_dir: Path, identity_id: str) -> Path:
    rows = sorted(report_dir.glob(f"identity-install-{identity_id}-install-*.json"), key=lambda p: p.stat().st_mtime)
    if not rows:
        raise RuntimeError("install_report_missing")
    return rows[-1]


def _catalog_row(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    return next((x for x in rows if str(x.get("id", "")).strip() == identity_id), {})


def _check_baseline_alignment(
    *,
    baseline: dict[str, Any],
    task_doc: dict[str, Any],
    meta_doc: dict[str, Any],
    catalog_row: dict[str, Any],
) -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    agent = task_doc.get("agent_identity") if isinstance(task_doc.get("agent_identity"), dict) else {}
    scaffold = task_doc.get("scaffold_metadata") if isinstance(task_doc.get("scaffold_metadata"), dict) else {}
    for field, expected in (baseline.get("agent_identity") or {}).items():
        expected_text = str(expected or "").strip()
        observed = str(agent.get(field, "")).strip()
        if expected_text and observed != expected_text:
            mismatches.append({"field": f"task.agent_identity.{field}", "expected": expected_text, "observed": observed})
    for field, expected in (baseline.get("scaffold_metadata") or {}).items():
        expected_text = str(expected or "").strip()
        observed = str(scaffold.get(field, "")).strip()
        if expected_text and observed != expected_text:
            mismatches.append(
                {"field": f"task.scaffold_metadata.{field}", "expected": expected_text, "observed": observed}
            )
    expected_meta = str(((baseline.get("meta") or {}).get("methodology_version") or "")).strip()
    observed_meta = str(meta_doc.get("methodology_version", "")).strip()
    if expected_meta and observed_meta != expected_meta:
        mismatches.append({"field": "meta.methodology_version", "expected": expected_meta, "observed": observed_meta})
    expected_catalog = str(((baseline.get("catalog") or {}).get("methodology_version") or "")).strip()
    observed_catalog = str(catalog_row.get("methodology_version", "")).strip()
    if expected_catalog and observed_catalog != expected_catalog:
        mismatches.append(
            {"field": "catalog.methodology_version", "expected": expected_catalog, "observed": observed_catalog}
        )
    return mismatches


def _case_install_legacy_pack_version_drift_blocked(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    target_pack = (Path(args.target_root).resolve() / args.identity_id).resolve()
    report_dir = Path(args.report_dir).resolve()
    cmd = [
        "python3",
        "scripts/identity_installer.py",
        "install",
        "--identity-id",
        args.identity_id,
        "--source-pack",
        str(Path(args.source_pack).resolve()),
        "--target-root",
        str(Path(args.target_root).resolve()),
        "--pack-root",
        str(Path(args.target_root).resolve()),
        "--catalog",
        str(Path(args.catalog).resolve()),
        "--repo-catalog",
        str(Path(args.repo_catalog).resolve()),
        "--scope",
        "USER",
        "--register",
        "--activate",
        "--report-dir",
        str(report_dir),
        "--backup-dir",
        str(Path(args.backup_dir).resolve()),
    ]
    installer_rc, installer_stdout, installer_stderr = _run(cmd, cwd=repo_root)

    report_path = None
    report_doc: dict[str, Any] = {}
    report_error = ""
    try:
        report_path = _latest_report(report_dir, args.identity_id)
        report_doc = _load_json(report_path)
    except Exception as exc:  # pragma: no cover
        report_error = str(exc)

    baseline = _resolve_baseline(repo_root)
    task_doc = _load_json(target_pack / "CURRENT_TASK.json") if (target_pack / "CURRENT_TASK.json").exists() else {}
    meta_doc = _load_yaml(target_pack / "META.yaml") if (target_pack / "META.yaml").exists() else {}
    catalog_row = _catalog_row(Path(args.catalog).resolve(), args.identity_id)
    mismatches = _check_baseline_alignment(
        baseline=baseline,
        task_doc=task_doc,
        meta_doc=meta_doc,
        catalog_row=catalog_row,
    )

    report_checks = {
        "version_baseline_apply_status": str(report_doc.get("version_baseline_apply_status", "")).strip(),
        "version_baseline_verify_status": str(report_doc.get("version_baseline_verify_status", "")).strip(),
        "host_gateway_downsink_status": str(report_doc.get("host_gateway_downsink_status", "")).strip(),
        "install_block_reasons": list(report_doc.get("install_block_reasons") or []),
    }
    report_ok = (
        report_checks["version_baseline_apply_status"] == "PASS_REQUIRED"
        and report_checks["version_baseline_verify_status"] == "PASS_REQUIRED"
        and report_checks["host_gateway_downsink_status"] == "PASS_REQUIRED"
        and len(report_checks["install_block_reasons"]) == 0
    )
    overall_ok = installer_rc == 0 and not report_error and report_ok and len(mismatches) == 0

    payload = {
        "probe": "install_legacy_pack_version_drift_blocked",
        "probe_status": "PASS_REQUIRED" if overall_ok else "FAIL_REQUIRED",
        "installer_rc": installer_rc,
        "installer_stdout_tail": installer_stdout.strip().splitlines()[-12:],
        "installer_stderr_tail": installer_stderr.strip().splitlines()[-12:],
        "report_path": str(report_path) if report_path else "",
        "report_load_error": report_error,
        "report_checks": report_checks,
        "baseline_mismatch_count": len(mismatches),
        "baseline_mismatches": mismatches,
        "target_pack_path": str(target_pack),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if overall_ok else 1


def _case_install_then_migration_closure_pass(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    cmd = [
        "python3",
        "scripts/check_version_baseline_migration_closure.py",
        "--repo-catalog",
        str(Path(args.repo_catalog).resolve()),
        "--catalog",
        str(Path(args.catalog).resolve()),
        "--json-only",
    ]
    rc, out, err = _run(cmd, cwd=repo_root)
    payload = {}
    try:
        payload = json.loads(out) if out.strip() else {}
    except Exception:
        payload = {}
    status = str(payload.get("version_baseline_migration_closure_status", "")).strip().upper()
    violations = int(payload.get("violation_count", 0) or 0)
    overall_ok = rc == 0 and status == "PASS_REQUIRED" and violations == 0
    doc = {
        "probe": "install_then_migration_closure_pass",
        "probe_status": "PASS_REQUIRED" if overall_ok else "FAIL_REQUIRED",
        "checker_rc": rc,
        "checker_status": status,
        "checker_violation_count": violations,
        "checker_stdout_tail": out.strip().splitlines()[-10:],
        "checker_stderr_tail": err.strip().splitlines()[-10:],
    }
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if overall_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=["install_legacy_pack_version_drift_blocked", "install_then_migration_closure_pass"])
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--source-pack", required=True)
    ap.add_argument("--target-root", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report-dir", required=True)
    ap.add_argument("--backup-dir", required=True)
    args = ap.parse_args()

    if args.case == "install_legacy_pack_version_drift_blocked":
        return _case_install_legacy_pack_version_drift_blocked(args)
    if args.case == "install_then_migration_closure_pass":
        return _case_install_then_migration_closure_pass(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "${PROBE_RUNNER}"

run_probe() {
  local name="$1"
  shift
  local cmd=("$@")

  local stdout_path="${RESULT_ROOT}/${name}.stdout.json"
  local stderr_path="${RESULT_ROOT}/${name}.stderr.log"
  local meta_path="${RESULT_ROOT}/${name}.meta.json"
  local timestamp_utc
  timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local cmd_string
  cmd_string="$(printf '%q ' "${cmd[@]}")"
  cmd_string="${cmd_string% }"

  set +e
  "${cmd[@]}" >"${stdout_path}" 2>"${stderr_path}"
  local rc=$?
  set -e

  if [ ! -s "${stderr_path}" ]; then
    rm -f "${stderr_path}"
  fi

  python3 - <<'PY' "${name}" "${rc}" "${stdout_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

name = sys.argv[1]
rc = int(sys.argv[2])
stdout_path = Path(sys.argv[3]).resolve()
doc = json.loads(stdout_path.read_text(encoding="utf-8"))

status = str(doc.get("probe_status", "")).strip().upper()
if name == "install_legacy_pack_version_drift_blocked":
    if rc != 0:
        raise SystemExit("install_legacy_pack_version_drift_blocked: expected zero rc")
    if status != "PASS_REQUIRED":
        raise SystemExit("install_legacy_pack_version_drift_blocked: expected PASS_REQUIRED")
    if int(doc.get("baseline_mismatch_count", 0) or 0) != 0:
        raise SystemExit("install_legacy_pack_version_drift_blocked: baseline mismatches detected")
elif name == "install_then_migration_closure_pass":
    if rc != 0:
        raise SystemExit("install_then_migration_closure_pass: expected zero rc")
    if status != "PASS_REQUIRED":
        raise SystemExit("install_then_migration_closure_pass: expected PASS_REQUIRED")
    if int(doc.get("checker_violation_count", 0) or 0) != 0:
        raise SystemExit("install_then_migration_closure_pass: expected zero violations")
else:
    raise SystemExit(f"unknown probe: {name}")
PY

  local sha256
  sha256="$(python3 - <<'PY' "${stdout_path}"
from __future__ import annotations
import hashlib, sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

  python3 - <<'PY' "${meta_path}" "${name}" "${stdout_path}" "${sha256}" "${cmd_string}" "${rc}" "${timestamp_utc}"
from __future__ import annotations
import json, sys
from pathlib import Path

meta_path = Path(sys.argv[1]).resolve()
payload = {
    "name": sys.argv[2],
    "file": str(Path(sys.argv[3]).resolve()),
    "sha256": sys.argv[4],
    "command": sys.argv[5],
    "rc": int(sys.argv[6]),
    "timestamp_utc": sys.argv[7],
}
meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  echo "[INSTALLER][PROBE] ${name} rc=${rc} file=${stdout_path}"
}

cd "${REPO_ROOT}"

run_probe install_legacy_pack_version_drift_blocked \
  python3 "${PROBE_RUNNER}" \
  --case install_legacy_pack_version_drift_blocked \
  --repo-root "${REPO_ROOT}" \
  --source-pack "${SOURCE_PACK}" \
  --target-root "${TARGET_ROOT}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report-dir "${REPORT_DIR}" \
  --backup-dir "${BACKUP_DIR}"

run_probe install_then_migration_closure_pass \
  python3 "${PROBE_RUNNER}" \
  --case install_then_migration_closure_pass \
  --repo-root "${REPO_ROOT}" \
  --source-pack "${SOURCE_PACK}" \
  --target-root "${TARGET_ROOT}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report-dir "${REPORT_DIR}" \
  --backup-dir "${BACKUP_DIR}"

python3 - <<'PY' "${MANIFEST_PATH}" "${RESULT_ROOT}"
from __future__ import annotations

import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1]).resolve()
result_root = Path(sys.argv[2]).resolve()
items = []
for meta_path in sorted(result_root.glob("*.meta.json")):
    doc = json.loads(meta_path.read_text(encoding="utf-8"))
    items.append(doc)

manifest = {
    "suite": "installer_version_baseline_probes_ci",
    "count": len(items),
    "items": items,
}
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[INSTALLER][MANIFEST] {manifest_path}")
PY

