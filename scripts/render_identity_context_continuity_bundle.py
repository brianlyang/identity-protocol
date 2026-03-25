#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from identity_context_continuity_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    clean_string,
    continuity_report_root,
    continuity_state_root,
    reentry_brief_path,
    resolve_pack_task,
)

SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLE_CONTRACT_ID = "identity_context_continuity_bundle_v1"
BUNDLE_ROLE = "launcher_and_instance_internal_support"
LAUNCHER_OWNER_STREAM = "v1.6.14"

VALIDATOR_SPECS: dict[str, dict[str, str]] = {
    "continuity_artifact": {
        "script": str((SCRIPT_DIR / "validate_identity_context_continuity.py").resolve()),
        "status_field": "identity_context_continuity_status",
    },
    "reentry_brief": {
        "script": str((SCRIPT_DIR / "validate_identity_reentry_brief.py").resolve()),
        "status_field": "identity_reentry_brief_status",
    },
    "reentry_consumption": {
        "script": str((SCRIPT_DIR / "validate_identity_reentry_consumption.py").resolve()),
        "status_field": "identity_reentry_consumption_status",
    },
    "receipt_family": {
        "script": str((SCRIPT_DIR / "validate_identity_context_continuity_receipts.py").resolve()),
        "status_field": "identity_context_continuity_receipt_family_status",
    },
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _run_validator_json(cmd: list[str]) -> tuple[dict[str, Any], int]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "validator_surface_status": STATUS_FAIL_REQUIRED,
            "render_error": "validator_stdout_not_json",
            "raw_stdout": stdout,
            "raw_stderr": stderr,
            "returncode": proc.returncode,
        }
    if not isinstance(payload, dict):
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "validator_surface_status": STATUS_FAIL_REQUIRED,
            "render_error": "validator_root_not_object",
            "raw_stdout": stdout,
            "raw_stderr": stderr,
            "returncode": proc.returncode,
        }
    payload.setdefault("returncode", proc.returncode)
    if stderr:
        payload.setdefault("raw_stderr", stderr)
    return payload, proc.returncode


def _status_from_payload(name: str, payload: dict[str, Any]) -> str:
    spec = VALIDATOR_SPECS[name]
    token = clean_string(payload.get(spec["status_field"]))
    if token:
        return token
    token = clean_string(payload.get("status"))
    return token or STATUS_FAIL_REQUIRED


def _validator_cmd(
    *,
    name: str,
    identity_id: str,
    catalog: str,
    current_task: str,
    artifact: str,
    artifact_kind: str,
    brief: str,
    receipt: str,
) -> list[str]:
    spec = VALIDATOR_SPECS[name]
    cmd = [sys.executable, spec["script"], "--identity-id", identity_id, "--json-only"]
    if clean_string(catalog):
        cmd.extend(["--catalog", clean_string(catalog)])
    if clean_string(current_task):
        cmd.extend(["--current-task", clean_string(current_task)])
    if name == "continuity_artifact":
        if clean_string(artifact):
            cmd.extend(["--artifact", clean_string(artifact)])
        if clean_string(artifact_kind):
            cmd.extend(["--artifact-kind", clean_string(artifact_kind)])
    elif name == "reentry_brief":
        if clean_string(brief):
            cmd.extend(["--brief", clean_string(brief)])
    elif name == "reentry_consumption":
        if clean_string(brief):
            cmd.extend(["--brief", clean_string(brief)])
        if clean_string(receipt):
            cmd.extend(["--receipt", clean_string(receipt)])
    return cmd


def _bundle_status(
    *,
    startup_readiness_status: str,
    reentry_contract_required: bool,
    continuity_contract_required: bool,
) -> str:
    if startup_readiness_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED
    if startup_readiness_status == STATUS_SKIPPED_NOT_REQUIRED and not reentry_contract_required and not continuity_contract_required:
        return STATUS_SKIPPED_NOT_REQUIRED
    return STATUS_FAIL_REQUIRED


def _launcher_recommendation(startup_readiness_status: str) -> str:
    if startup_readiness_status == STATUS_PASS_REQUIRED:
        return "consume_governed_reentry_brief"
    if startup_readiness_status == STATUS_SKIPPED_NOT_REQUIRED:
        return "fresh_start_without_continuity_contract"
    return "fresh_start_without_governed_reentry_claim"


def render_continuity_bundle_payload(
    *,
    identity_id: str,
    catalog: str = "",
    current_task: str = "",
    artifact: str = "",
    artifact_kind: str = "",
    brief: str = "",
    receipt: str = "",
) -> dict[str, Any]:
    catalog_raw = clean_string(catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None

    try:
        pack_root, task_path, _task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(current_task),
            identity_id=identity_id,
        )
    except Exception as exc:
        return {
            "status": STATUS_FAIL_REQUIRED,
            "identity_context_continuity_bundle_status": STATUS_FAIL_REQUIRED,
            "bundle_contract_id": BUNDLE_CONTRACT_ID,
            "bundle_role": BUNDLE_ROLE,
            "identity_id": identity_id,
            "error": str(exc),
        }

    validator_payloads: dict[str, dict[str, Any]] = {}
    validator_statuses: dict[str, str] = {}
    validator_evidence_refs: dict[str, str] = {}
    validator_stale_reasons: dict[str, list[str]] = {}
    any_render_error = False

    for name in VALIDATOR_SPECS:
        cmd = _validator_cmd(
            name=name,
            identity_id=identity_id,
            catalog=str(catalog_path) if catalog_path is not None else "",
            current_task=clean_string(current_task),
            artifact=clean_string(artifact),
            artifact_kind=clean_string(artifact_kind),
            brief=clean_string(brief),
            receipt=clean_string(receipt),
        )
        payload, _rc = _run_validator_json(cmd)
        if clean_string(payload.get("render_error")):
            any_render_error = True
        validator_payloads[name] = payload
        validator_statuses[name] = _status_from_payload(name, payload)
        validator_evidence_refs[name] = clean_string(payload.get("evidence_ref"))
        stale = payload.get("stale_reasons")
        validator_stale_reasons[name] = list(stale) if isinstance(stale, list) else []

    artifact_payload = validator_payloads["continuity_artifact"]
    brief_payload = validator_payloads["reentry_brief"]
    consumption_payload = validator_payloads["reentry_consumption"]
    receipt_payload = validator_payloads["receipt_family"]

    startup_readiness_status = validator_statuses["reentry_brief"]
    live_consumption_proof_status = validator_statuses["reentry_consumption"]
    receipt_family_status = validator_statuses["receipt_family"]
    continuity_contract_required = bool(artifact_payload.get("required_contract"))
    reentry_contract_required = bool(brief_payload.get("required_contract") or consumption_payload.get("required_contract"))

    bundle_status = _bundle_status(
        startup_readiness_status=startup_readiness_status,
        reentry_contract_required=reentry_contract_required,
        continuity_contract_required=continuity_contract_required,
    )
    if any_render_error:
        bundle_status = STATUS_FAIL_REQUIRED

    continuity_lineage_ref = (
        clean_string(consumption_payload.get("continuity_lineage_ref"))
        or clean_string(brief_payload.get("continuity_lineage_ref"))
        or clean_string(artifact_payload.get("supersedes_ref"))
    )
    continuity_id = (
        clean_string(brief_payload.get("continuity_id"))
        or clean_string(artifact_payload.get("continuity_id"))
    )
    current_reentry_brief_ref = (
        clean_string(consumption_payload.get("reentry_brief_ref"))
        or clean_string(brief_payload.get("reentry_brief_ref"))
        or str(reentry_brief_path(pack_root))
    )

    payload = {
        "status": bundle_status,
        "identity_context_continuity_bundle_status": bundle_status,
        "bundle_contract_id": BUNDLE_CONTRACT_ID,
        "bundle_role": BUNDLE_ROLE,
        "identity_id": identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "canonical_report_root": str(continuity_report_root(pack_root)),
        "canonical_state_root": str(continuity_state_root(pack_root)),
        "canonical_reentry_brief_path": str(reentry_brief_path(pack_root)),
        "launcher_entry_owner_stream": LAUNCHER_OWNER_STREAM,
        "surface_governance": build_governed_runtime_summary_surface_payload(
            "identity_context_continuity_bundle_surface"
        ),
        "operator_surface_contract": {
            "new_user_facing_continuity_command_family_forbidden": True,
            "continuity_discovery_is_internal_support_only": True,
            "launcher_entry_owner_stream": LAUNCHER_OWNER_STREAM,
            "protocol_guides_instance_answers": True,
        },
        "continuity_contract_required": continuity_contract_required,
        "reentry_contract_required": reentry_contract_required,
        "startup_reentry_readiness_status": startup_readiness_status,
        "live_reentry_consumption_proof_status": live_consumption_proof_status,
        "receipt_family_observation_status": receipt_family_status,
        "recommended_launcher_bind_mode": _launcher_recommendation(startup_readiness_status),
        "continuity_id": continuity_id,
        "current_reentry_brief_ref": current_reentry_brief_ref,
        "continuity_lineage_ref": continuity_lineage_ref,
        "validator_statuses": validator_statuses,
        "validator_evidence_refs": validator_evidence_refs,
        "validator_stale_reasons": validator_stale_reasons,
        "validator_payloads": validator_payloads,
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render a protocol-owned continuity bundle for launcher/internal consumers without creating a new operator command family."
    )
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--artifact", default="")
    ap.add_argument("--artifact-kind", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--receipt", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = render_continuity_bundle_payload(
        identity_id=args.identity_id,
        catalog=args.catalog,
        current_task=args.current_task,
        artifact=args.artifact,
        artifact_kind=args.artifact_kind,
        brief=args.brief,
        receipt=args.receipt,
    )
    _emit(payload, json_only=args.json_only)
    return 0 if clean_string(payload.get("status")) != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
