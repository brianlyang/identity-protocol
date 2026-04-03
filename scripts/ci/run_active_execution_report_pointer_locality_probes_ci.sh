#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/active-report-pointer-locality-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${TMP_ROOT}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from tool_vendor_governance_common import (
    IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_ACTIVE_EXECUTION_POINTER,
    IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_CANDIDATE_ROOT_LATEST,
    IDENTITY_UPGRADE_REPORT_SELECTION_MODE_ACTIVE_EXECUTION_POINTER,
    IDENTITY_UPGRADE_REPORT_SELECTION_MODE_CANDIDATE_ROOT_LATEST,
    resolve_latest_identity_upgrade_report,
)

tmp_root = Path(sys.argv[1]).resolve()
identity_id = "probe-identity"
run_id = f"identity-upgrade-exec-{identity_id}-probe"
report_name = f"{run_id}.json"

source_pack = (tmp_root / "source-pack").resolve()
clone_pack = (tmp_root / "clone-pack").resolve()
for pack in (source_pack, clone_pack):
    (pack / "runtime" / "reports").mkdir(parents=True, exist_ok=True)
    (pack / "runtime" / "state").mkdir(parents=True, exist_ok=True)

source_report = (source_pack / "runtime" / "reports" / report_name).resolve()
clone_report = (clone_pack / "runtime" / "reports" / report_name).resolve()

for report_path, pack_path, catalog_name in (
    (source_report, source_pack, "source.catalog.yaml"),
    (clone_report, clone_pack, "clone.catalog.yaml"),
):
    report_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "identity_id": identity_id,
                "catalog_path": str((tmp_root / catalog_name).resolve()),
                "resolved_pack_path": str(pack_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

pointer_path = (clone_pack / "runtime" / "state" / "active_execution_report.json").resolve()
pointer_path.write_text(
    json.dumps(
        {
            "run_id": run_id,
            "report_path": str(source_report),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

external_pointer_resolution = resolve_latest_identity_upgrade_report(identity_id, clone_pack)
assert external_pointer_resolution.selected_report == clone_report, {
    "case": "external_pointer_rejected_fallbacks_to_pack_local_report",
    "selected_report": str(external_pointer_resolution.selected_report)
    if external_pointer_resolution.selected_report
    else "",
    "expected_report": str(clone_report),
    "forbidden_external_report": str(source_report),
}
assert external_pointer_resolution.pointer_resolution_mode == "external_pointer_report_rejected", (
    external_pointer_resolution
)
assert (
    external_pointer_resolution.selection_mode
    == IDENTITY_UPGRADE_REPORT_SELECTION_MODE_CANDIDATE_ROOT_LATEST
), external_pointer_resolution
assert (
    external_pointer_resolution.selected_report_authority_class
    == IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_CANDIDATE_ROOT_LATEST
), external_pointer_resolution

pointer_path.write_text(
    json.dumps(
        {
            "run_id": run_id,
            "report_path": str(clone_report),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

pack_local_resolution = resolve_latest_identity_upgrade_report(identity_id, clone_pack)
assert pack_local_resolution.selected_report == clone_report, {
    "case": "pack_local_pointer_remains_authoritative",
    "selected_report": str(pack_local_resolution.selected_report)
    if pack_local_resolution.selected_report
    else "",
    "expected_report": str(clone_report),
}
assert pack_local_resolution.pointer_resolution_mode == "pointer_candidate_root_report", (
    pack_local_resolution
)
assert (
    pack_local_resolution.selection_mode
    == IDENTITY_UPGRADE_REPORT_SELECTION_MODE_ACTIVE_EXECUTION_POINTER
), pack_local_resolution
assert (
    pack_local_resolution.selected_report_authority_class
    == IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_ACTIVE_EXECUTION_POINTER
), pack_local_resolution

print(
    json.dumps(
        {
            "active_execution_report_pointer_locality_probe_status": "PASS_REQUIRED",
            "external_pointer_rejection_status": "PASS_REQUIRED",
            "external_pointer_resolution_mode": external_pointer_resolution.pointer_resolution_mode,
            "external_pointer_selection_mode": external_pointer_resolution.selection_mode,
            "external_pointer_selected_report_authority_class": (
                external_pointer_resolution.selected_report_authority_class
            ),
            "external_pointer_rejected_selected_report": (
                str(external_pointer_resolution.selected_report)
                if external_pointer_resolution.selected_report
                else ""
            ),
            "pack_local_pointer_authority_status": "PASS_REQUIRED",
            "pack_local_pointer_resolution_mode": pack_local_resolution.pointer_resolution_mode,
            "pack_local_pointer_selection_mode": pack_local_resolution.selection_mode,
            "pack_local_pointer_selected_report_authority_class": (
                pack_local_resolution.selected_report_authority_class
            ),
            "pack_local_pointer_selected_report": (
                str(pack_local_resolution.selected_report)
                if pack_local_resolution.selected_report
                else ""
            ),
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] active execution report pointer locality probes passed"
