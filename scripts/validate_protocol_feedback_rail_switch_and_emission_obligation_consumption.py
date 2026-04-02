#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common import (
    FIXED_WRITE_SET,
    ISSUE_ID,
    LANE_ID,
    REQUIRED_MACHINE_VISIBLE_FIELDS,
    RUNTIME_STALE_REASON_FAMILY,
    SAMPLE_EXPLICIT_REQUEST,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    VALIDATION_BUNDLE,
    WORKBOOK_REL_PATHS,
    render_json,
    validate_contract_documents,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_ROOT = SCRIPT_DIR.parent


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _run_json(cmd: list[str], *, cwd: Path) -> dict[str, Any]:
    rc, stdout, stderr = _run(cmd, cwd=cwd)
    payload = _parse_json_payload(stdout) or {}
    return {
        "rc": rc,
        "stdout": stdout,
        "stderr": stderr,
        "payload": payload,
        "command": cmd,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        token = str(item or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _tmp_base(repo_root: Path) -> Path:
    raw = str(os.environ.get("TMPDIR", "")).strip()
    base = Path(raw).expanduser().resolve() if raw else (repo_root / ".tmp").resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base


def _validate_workbook_closure(repo_root: Path) -> list[str]:
    errors: list[str] = []
    issue_register_path = repo_root / WORKBOOK_REL_PATHS["issue_register"]
    deep_audit_path = repo_root / WORKBOOK_REL_PATHS["deep_audit_workbook"]

    if not issue_register_path.exists():
        errors.append(f"missing_workbook:{WORKBOOK_REL_PATHS['issue_register']}")
    else:
        issue_register_text = issue_register_path.read_text(encoding="utf-8")
        row_re = re.compile(
            rf"^\|\s*ISSUE-049\b.*?\|\s*CLOSED\s*\|\s*`{re.escape(LANE_ID)}`\s*\|",
            re.MULTILINE,
        )
        if not row_re.search(issue_register_text):
            errors.append("issue_049_row_not_closed")
        for token in (
            "scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py",
            "scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh",
        ):
            if token not in issue_register_text:
                errors.append(f"issue_register_missing_token:{token}")

    if not deep_audit_path.exists():
        errors.append(f"missing_workbook:{WORKBOOK_REL_PATHS['deep_audit_workbook']}")
    else:
        deep_audit_text = deep_audit_path.read_text(encoding="utf-8")
        section_match = re.search(
            r"^### ISSUE-049\b.*?(?=^##\s+\d+\)|\Z)",
            deep_audit_text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not section_match:
            errors.append("issue_049_deep_audit_section_missing")
        else:
            section = section_match.group(0)
            for token in (
                "- `status`: CLOSED",
                "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
                "scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py",
                "scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py",
                "scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh",
                "`PASS_REQUIRED`",
                "`PASS`",
            ):
                if token not in section:
                    errors.append(f"deep_audit_missing_token:{token}")
            if "is opened" in section or "remains open" in section:
                errors.append("deep_audit_retains_open_language")
    return errors


def _create_fixture(tmp_root: Path) -> tuple[str, Path, Path]:
    identity_id = "issue-049-fixture"
    pack_path = (tmp_root / "identity" / "packs" / identity_id).resolve()
    pack_path.mkdir(parents=True, exist_ok=True)
    task_payload = {
        "task_id": "issue_049_fixture",
        "identity_id": identity_id,
        "task_state": "fixture",
    }
    _write_json(pack_path / "CURRENT_TASK.json", task_payload)
    catalog_path = (tmp_root / "identity" / "catalog" / "identities.yaml").resolve()
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        "\n".join(
            [
                'version: "1.0"',
                'updated_at: "2026-04-02"',
                'default_identity: ""',
                'identities:',
                f'  - id: "{identity_id}"',
                f'    pack_path: "{pack_path.as_posix()}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return identity_id, pack_path, catalog_path


def _path_exists(token: str) -> bool:
    raw = str(token or "").strip()
    return bool(raw) and Path(raw).expanduser().exists()


def _runtime_composition(*, skip_atomic_emit: bool, skip_outbox_sync: bool, repo_root: Path) -> dict[str, Any]:
    tmp_base = _tmp_base(repo_root)
    with tempfile.TemporaryDirectory(prefix="issue049-protocol-feedback.", dir=str(tmp_base)) as td:
        tmp_root = Path(td).resolve()
        identity_id, pack_path, catalog_path = _create_fixture(tmp_root)

        bootstrap_cmd = [
            "python3",
            str((EXECUTION_ROOT / "scripts" / "validate_protocol_feedback_bootstrap_ready.py").resolve()),
            "--catalog",
            str(catalog_path),
            "--repo-catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--expected-work-layer",
            "protocol",
            "--source-layer",
            "project",
            "--layer-intent-text",
            SAMPLE_EXPLICIT_REQUEST,
            "--force-check",
            "--auto-bootstrap",
            "--operation",
            "validate",
            "--json-only",
        ]
        bootstrap = _run_json(bootstrap_cmd, cwd=EXECUTION_ROOT)
        bootstrap_payload = bootstrap["payload"]
        bootstrap_status = str(bootstrap_payload.get("protocol_feedback_bootstrap_status", "")).strip() or (
            STATUS_PASS_REQUIRED if bootstrap["rc"] == 0 else STATUS_FAIL_REQUIRED
        )

        request_detected = True
        rule_known = True
        rail_selected = bool(bootstrap_payload.get("protocol_lane_selected", False))
        emission_obligation_status = (
            STATUS_PASS_REQUIRED
            if request_detected and rule_known and rail_selected and bootstrap_status == STATUS_PASS_REQUIRED
            else STATUS_FAIL_REQUIRED
        )

        emit_invoked = False
        channel_entered = False
        artifact_materialized = False
        atomic_emit_status = "SKIPPED_NOT_REQUIRED"
        atomic_validation_status = "SKIPPED_NOT_REQUIRED"
        outbox_sync_status = "SKIPPED_NOT_REQUIRED"
        transaction_id = ""
        evidence_refs: dict[str, str] = {
            "bootstrap_receipt_path": str(bootstrap_payload.get("bootstrap_receipt_path", "")).strip(),
            "batch_ref": "",
            "index_ref": "",
            "receipt_ref": "",
            "channel_receipt_path": "",
        }
        emit = {"rc": 0, "payload": {}, "stdout": "", "stderr": "", "command": []}
        atomic_validate = {"rc": 0, "payload": {}, "stdout": "", "stderr": "", "command": []}

        if emission_obligation_status == STATUS_PASS_REQUIRED and not skip_atomic_emit:
            transaction_id = f"issue049-{uuid.uuid4().hex[:12]}"
            payload_path = (tmp_root / "explicit-request.json").resolve()
            _write_json(
                payload_path,
                {
                    "issue_id": ISSUE_ID,
                    "lane_id": LANE_ID,
                    "explicit_protocol_feedback_request": SAMPLE_EXPLICIT_REQUEST,
                    "protocol_feedback_request_detected": True,
                },
            )
            emit_cmd = [
                "python3",
                str((EXECUTION_ROOT / "scripts" / "emit_protocol_feedback_atomic.py").resolve()),
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--operation",
                "validate",
                "--transaction-id",
                transaction_id,
                "--payload-json",
                str(payload_path),
                "--json-only",
            ]
            if skip_outbox_sync:
                emit_cmd.append("--skip-outbox-sync")
            else:
                emit_cmd.append("--force-outbox-sync")
            emit = _run_json(emit_cmd, cwd=EXECUTION_ROOT)
            emit_payload = emit["payload"]
            atomic_emit_status = str(emit_payload.get("atomic_emit_status", "")).strip() or (
                STATUS_PASS_REQUIRED if emit["rc"] == 0 else STATUS_FAIL_REQUIRED
            )
            outbox_sync_status = str(emit_payload.get("outbox_sync_status", "")).strip() or outbox_sync_status
            emit_invoked = emit["rc"] == 0 and atomic_emit_status == STATUS_PASS_REQUIRED
            evidence_refs["batch_ref"] = str(emit_payload.get("batch_ref", "")).strip()
            evidence_refs["index_ref"] = str(emit_payload.get("index_ref", "")).strip()
            evidence_refs["receipt_ref"] = str(emit_payload.get("receipt_ref", "")).strip()

            outbox_sync_payload = emit_payload.get("outbox_sync_payload")
            if not isinstance(outbox_sync_payload, dict):
                outbox_sync_payload = {}
            evidence_refs["channel_receipt_path"] = str(outbox_sync_payload.get("receipt_path", "")).strip()
            channel_entered = (
                emit_invoked
                and outbox_sync_status == STATUS_PASS_REQUIRED
                and bool(str(outbox_sync_payload.get("receipt_ref", "")).strip())
            )

            if emit_invoked:
                atomic_cmd = [
                    "python3",
                    str((EXECUTION_ROOT / "scripts" / "validate_protocol_feedback_atomic_emit.py").resolve()),
                    "--catalog",
                    str(catalog_path),
                    "--identity-id",
                    identity_id,
                    "--receipt",
                    evidence_refs["receipt_ref"],
                    "--transaction-id",
                    transaction_id,
                    "--force-required",
                    "--operation",
                    "validate",
                    "--json-only",
                ]
                atomic_validate = _run_json(atomic_cmd, cwd=EXECUTION_ROOT)
                atomic_payload = atomic_validate["payload"]
                atomic_validation_status = str(atomic_payload.get("protocol_feedback_atomic_emit_status", "")).strip() or (
                    STATUS_PASS_REQUIRED if atomic_validate["rc"] == 0 else STATUS_FAIL_REQUIRED
                )

            artifact_paths = [
                evidence_refs["batch_ref"],
                evidence_refs["index_ref"],
                evidence_refs["receipt_ref"],
            ]
            if outbox_sync_status == STATUS_PASS_REQUIRED:
                artifact_paths.append(evidence_refs["channel_receipt_path"])
            artifact_materialized = emit_invoked and all(_path_exists(token) for token in artifact_paths)
        elif skip_atomic_emit:
            outbox_sync_status = "SKIPPED_BY_TEST_MODE"
            atomic_emit_status = "SKIPPED_BY_TEST_MODE"
            atomic_validation_status = "SKIPPED_BY_TEST_MODE"

        rule_consumption_status = (
            STATUS_PASS_REQUIRED
            if emission_obligation_status == STATUS_PASS_REQUIRED
            and emit_invoked
            and channel_entered
            and artifact_materialized
            and atomic_validation_status == STATUS_PASS_REQUIRED
            else STATUS_FAIL_REQUIRED
        )

        stale_reasons: list[str] = []
        if not request_detected:
            stale_reasons.append("explicit_request_not_detected")
        if not rule_known:
            stale_reasons.append("protocol_feedback_rule_unknown")
        if not rail_selected:
            stale_reasons.append("protocol_feedback_rail_not_selected")
        if emission_obligation_status != STATUS_PASS_REQUIRED:
            stale_reasons.append("protocol_feedback_emission_obligation_unmet")
        if not channel_entered:
            stale_reasons.append("protocol_feedback_channel_not_entered")
        if not emit_invoked:
            stale_reasons.append("protocol_feedback_emit_not_invoked")
        if not artifact_materialized:
            stale_reasons.append("protocol_feedback_artifact_not_materialized")
        if rule_consumption_status != STATUS_PASS_REQUIRED:
            stale_reasons.append("protocol_feedback_rule_not_consumed")

        return {
            "fixture_pack_path": str(pack_path),
            "fixture_catalog_path": str(catalog_path),
            "transaction_id": transaction_id,
            "protocol_feedback_request_detected": request_detected,
            "protocol_feedback_rule_known": rule_known,
            "protocol_feedback_rail_selected": rail_selected,
            "protocol_feedback_emission_obligation_status": emission_obligation_status,
            "protocol_feedback_channel_entered": channel_entered,
            "protocol_feedback_emit_invoked": emit_invoked,
            "protocol_feedback_artifact_materialized": artifact_materialized,
            "protocol_feedback_rule_consumption_status": rule_consumption_status,
            "bootstrap_status": bootstrap_status,
            "bootstrap_result": bootstrap,
            "atomic_emit_status": atomic_emit_status,
            "atomic_emit_result": emit,
            "atomic_validation_status": atomic_validation_status,
            "atomic_validation_result": atomic_validate,
            "outbox_sync_status": outbox_sync_status,
            "evidence_refs": evidence_refs,
            "stale_reasons": _dedupe(stale_reasons),
        }


def validate(repo_root: Path, *, skip_atomic_emit: bool, skip_outbox_sync: bool) -> dict[str, Any]:
    docs_result = validate_contract_documents(repo_root)
    workbook_errors = _validate_workbook_closure(repo_root)
    runtime_result = _runtime_composition(
        skip_atomic_emit=skip_atomic_emit,
        skip_outbox_sync=skip_outbox_sync,
        repo_root=repo_root,
    )

    stale_reasons: list[str] = []
    if docs_result["status"] != STATUS_PASS_REQUIRED:
        stale_reasons.append("documentation_contract_drift")
    if workbook_errors:
        stale_reasons.append("workbook_closure_drift")
    stale_reasons.extend(runtime_result["stale_reasons"])
    stale_reasons = _dedupe(stale_reasons)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    mode = (
        "explicit_request_consumed_into_protocol_feedback_emit"
        if status == STATUS_PASS_REQUIRED
        else stale_reasons[0]
    )

    return {
        "status": status,
        "issue_id": ISSUE_ID,
        "lane_id": LANE_ID,
        "mode": mode,
        "documentation_contract_status": docs_result["status"],
        "documentation_errors": docs_result["errors"],
        "workbook_closure_status": STATUS_PASS_REQUIRED if not workbook_errors else STATUS_FAIL_REQUIRED,
        "workbook_errors": workbook_errors,
        "protocol_feedback_request_detected": runtime_result["protocol_feedback_request_detected"],
        "protocol_feedback_rule_known": runtime_result["protocol_feedback_rule_known"],
        "protocol_feedback_rail_selected": runtime_result["protocol_feedback_rail_selected"],
        "protocol_feedback_emission_obligation_status": runtime_result["protocol_feedback_emission_obligation_status"],
        "protocol_feedback_channel_entered": runtime_result["protocol_feedback_channel_entered"],
        "protocol_feedback_emit_invoked": runtime_result["protocol_feedback_emit_invoked"],
        "protocol_feedback_artifact_materialized": runtime_result["protocol_feedback_artifact_materialized"],
        "protocol_feedback_rule_consumption_status": runtime_result["protocol_feedback_rule_consumption_status"],
        "required_machine_visible_fields": list(REQUIRED_MACHINE_VISIBLE_FIELDS),
        "runtime_stale_reason_family": list(RUNTIME_STALE_REASON_FAMILY),
        "bootstrap_status": runtime_result["bootstrap_status"],
        "atomic_emit_status": runtime_result["atomic_emit_status"],
        "atomic_validation_status": runtime_result["atomic_validation_status"],
        "outbox_sync_status": runtime_result["outbox_sync_status"],
        "evidence_refs": runtime_result["evidence_refs"],
        "validation_bundle": list(VALIDATION_BUNDLE),
        "checked_fixed_write_count": len(FIXED_WRITE_SET),
        "stale_reasons": stale_reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ISSUE-049 protocol-feedback rail switch and canonical emission / receipt consumption."
    )
    parser.add_argument("--repo-root", default=None, help="Override repository root for fixed-write-set and workbook validation.")
    parser.add_argument("--skip-atomic-emit", action="store_true", help="Probe-only negative mode: detect explicit request but skip atomic emit.")
    parser.add_argument("--skip-outbox-sync", action="store_true", help="Probe-only negative mode: emit atomic receipt but skip outbox channel entry.")
    parser.add_argument("--json-only", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else EXECUTION_ROOT
    result = validate(
        repo_root,
        skip_atomic_emit=bool(args.skip_atomic_emit),
        skip_outbox_sync=bool(args.skip_outbox_sync),
    )
    print(render_json(result) if not args.json_only else json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
