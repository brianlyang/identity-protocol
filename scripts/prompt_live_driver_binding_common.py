#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from strict_live_evidence_resolution_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    clean_string,
    resolve_active_execution_context,
)
from tool_vendor_governance_common import ACTIVE_EXECUTION_POINTER_REL

STRICT_CURRENT_RUN_REQUIRED_FIELD = "strict_current_run_required"
ACTIVE_EXECUTION_POINTER_REL_FIELD = "active_execution_pointer_rel"
PROMPT_RUNTIME_STATE_REL_FIELD = "prompt_runtime_state_rel"
PROMPT_REPORT_PATH_FIELD_FIELD = "prompt_report_prompt_path_field"
PROMPT_REPORT_HASH_FIELDS_FIELD = "prompt_report_hash_field_candidates"
PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD = "prompt_report_runtime_state_path_field"
PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD = "prompt_report_runtime_state_binding_status_field"
PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD = "prompt_report_runtime_state_externalization_status_field"
PROMPT_RUNTIME_STATE_PATH_FIELD = "prompt_runtime_state_prompt_path_field"
PROMPT_RUNTIME_STATE_HASH_FIELD = "prompt_runtime_state_hash_field"

DEFAULT_PROMPT_RUNTIME_STATE_REL = "runtime/state/prompt_contract.json"
DEFAULT_PROMPT_REPORT_PATH_FIELD = "identity_prompt_path"
DEFAULT_PROMPT_REPORT_HASH_FIELDS: tuple[str, ...] = (
    "identity_prompt_hash_after",
    "prompt_policy_hash",
)
DEFAULT_PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD = "runtime_state_artifact_path"
DEFAULT_PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD = "prompt_runtime_state_binding_status"
DEFAULT_PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD = "prompt_runtime_state_externalization_status"
DEFAULT_PROMPT_RUNTIME_STATE_PATH_FIELD = "identity_prompt_path"
DEFAULT_PROMPT_RUNTIME_STATE_HASH_FIELD = "prompt_policy_hash"


def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def prompt_live_driver_binding_contract_defaults() -> dict[str, Any]:
    return {
        STRICT_CURRENT_RUN_REQUIRED_FIELD: True,
        ACTIVE_EXECUTION_POINTER_REL_FIELD: ACTIVE_EXECUTION_POINTER_REL.as_posix(),
        PROMPT_RUNTIME_STATE_REL_FIELD: DEFAULT_PROMPT_RUNTIME_STATE_REL,
        PROMPT_REPORT_PATH_FIELD_FIELD: DEFAULT_PROMPT_REPORT_PATH_FIELD,
        PROMPT_REPORT_HASH_FIELDS_FIELD: list(DEFAULT_PROMPT_REPORT_HASH_FIELDS),
        PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD: DEFAULT_PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD,
        PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD: DEFAULT_PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD,
        PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD: DEFAULT_PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD,
        PROMPT_RUNTIME_STATE_PATH_FIELD: DEFAULT_PROMPT_RUNTIME_STATE_PATH_FIELD,
        PROMPT_RUNTIME_STATE_HASH_FIELD: DEFAULT_PROMPT_RUNTIME_STATE_HASH_FIELD,
    }


def merge_prompt_live_driver_binding_contract_defaults(contract_doc: dict[str, Any] | None) -> dict[str, Any]:
    merged = _clone_json(contract_doc if isinstance(contract_doc, dict) else {})
    defaults = prompt_live_driver_binding_contract_defaults()
    if merged.get(STRICT_CURRENT_RUN_REQUIRED_FIELD) is not True:
        merged[STRICT_CURRENT_RUN_REQUIRED_FIELD] = True
    for key, value in defaults.items():
        if key == STRICT_CURRENT_RUN_REQUIRED_FIELD:
            continue
        if key not in merged:
            merged[key] = _clone_json(value)
            continue
        if isinstance(value, list):
            rows = [clean_string(item) for item in (merged.get(key) or []) if clean_string(item)]
            if not rows:
                rows = list(value)
            else:
                for token in value:
                    if token not in rows:
                        rows.append(token)
            merged[key] = rows
            continue
        if not clean_string(merged.get(key)):
            merged[key] = _clone_json(value)
    return merged


def _resolve_path(raw: str, *, base: Path) -> Path | None:
    token = clean_string(raw)
    if not token:
        return None
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _sha256(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _status_is_pass(value: Any) -> bool:
    return clean_string(value).upper() in {STATUS_PASS_REQUIRED, "PASS"}


def _collect_receipt_refs(*raw_values: str) -> list[str]:
    rows: list[str] = []
    for value in raw_values:
        token = clean_string(value)
        if token and token not in rows:
            rows.append(token)
    return rows


def derive_prompt_live_driver_binding_projection(
    *,
    pack_root: Path,
    contract_doc: dict[str, Any] | None,
    prompt_path: Path,
) -> dict[str, Any]:
    contract = merge_prompt_live_driver_binding_contract_defaults(contract_doc)
    active_context = resolve_active_execution_context(pack_root)
    current_run_id = clean_string(active_context.get("run_id"))
    report_path = _resolve_path(clean_string(active_context.get("report_path")), base=pack_root)
    report_doc = _load_json(report_path)
    prompt_runtime_state_rel = clean_string(contract.get(PROMPT_RUNTIME_STATE_REL_FIELD)) or DEFAULT_PROMPT_RUNTIME_STATE_REL
    prompt_state_path = _resolve_path(prompt_runtime_state_rel, base=pack_root)
    prompt_state_doc = _load_json(prompt_state_path)
    prompt_sha = _sha256(prompt_path)
    prompt_exists = prompt_path.exists()

    stale_reasons: list[str] = []
    if not clean_string(active_context.get("pointer_path")):
        stale_reasons.append("active_execution_pointer_missing")
    if report_path is None or not report_path.exists():
        stale_reasons.append("current_run_report_missing")
    if not current_run_id:
        stale_reasons.append("current_run_id_missing")
    if not prompt_exists:
        stale_reasons.append("identity_prompt_missing")

    if report_doc:
        report_run_id = clean_string(report_doc.get("run_id"))
        if current_run_id and report_run_id != current_run_id:
            stale_reasons.append("current_run_report_run_id_mismatch")
    elif report_path is not None and report_path.exists():
        stale_reasons.append("current_run_report_unreadable")

    report_prompt_path_field = clean_string(contract.get(PROMPT_REPORT_PATH_FIELD_FIELD)) or DEFAULT_PROMPT_REPORT_PATH_FIELD
    report_prompt_path = _resolve_path(clean_string(report_doc.get(report_prompt_path_field)), base=pack_root)
    if prompt_exists:
        if report_prompt_path is None:
            stale_reasons.append("current_run_prompt_path_missing")
        elif report_prompt_path != prompt_path.resolve():
            stale_reasons.append("current_run_prompt_path_mismatch")

    report_hash_fields = [
        clean_string(item)
        for item in (contract.get(PROMPT_REPORT_HASH_FIELDS_FIELD) or [])
        if clean_string(item)
    ] or list(DEFAULT_PROMPT_REPORT_HASH_FIELDS)
    report_hash_values = [
        clean_string(report_doc.get(field))
        for field in report_hash_fields
        if clean_string(report_doc.get(field))
    ]
    if prompt_sha:
        if not report_hash_values:
            stale_reasons.append("current_run_prompt_digest_missing")
        elif prompt_sha not in report_hash_values:
            stale_reasons.append("current_run_prompt_digest_mismatch")

    report_runtime_state_path_field = clean_string(contract.get(PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD)) or DEFAULT_PROMPT_REPORT_RUNTIME_STATE_PATH_FIELD
    report_runtime_state_path = _resolve_path(clean_string(report_doc.get(report_runtime_state_path_field)), base=pack_root)
    if prompt_state_path is None or not prompt_state_path.exists():
        stale_reasons.append("prompt_runtime_state_missing")
    elif report_runtime_state_path is not None and report_runtime_state_path != prompt_state_path.resolve():
        stale_reasons.append("prompt_runtime_state_path_mismatch")

    prompt_state_path_field = clean_string(contract.get(PROMPT_RUNTIME_STATE_PATH_FIELD)) or DEFAULT_PROMPT_RUNTIME_STATE_PATH_FIELD
    prompt_state_prompt_path = _resolve_path(clean_string(prompt_state_doc.get(prompt_state_path_field)), base=pack_root)
    if prompt_exists and prompt_state_doc:
        if prompt_state_prompt_path is None:
            stale_reasons.append("prompt_runtime_state_prompt_path_missing")
        elif prompt_state_prompt_path != prompt_path.resolve():
            stale_reasons.append("prompt_runtime_state_prompt_path_mismatch")

    prompt_state_hash_field = clean_string(contract.get(PROMPT_RUNTIME_STATE_HASH_FIELD)) or DEFAULT_PROMPT_RUNTIME_STATE_HASH_FIELD
    prompt_state_hash = clean_string(prompt_state_doc.get(prompt_state_hash_field))
    if prompt_sha:
        if not prompt_state_hash:
            stale_reasons.append("prompt_runtime_state_digest_missing")
        elif prompt_state_hash != prompt_sha:
            stale_reasons.append("prompt_runtime_state_digest_mismatch")

    runtime_state_binding_field = clean_string(contract.get(PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD)) or DEFAULT_PROMPT_REPORT_RUNTIME_STATE_BINDING_STATUS_FIELD
    runtime_state_externalization_field = (
        clean_string(contract.get(PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD))
        or DEFAULT_PROMPT_REPORT_RUNTIME_STATE_EXTERNALIZATION_STATUS_FIELD
    )
    runtime_state_binding_status = clean_string(report_doc.get(runtime_state_binding_field))
    runtime_state_externalization_status = clean_string(report_doc.get(runtime_state_externalization_field))
    if report_doc:
        if not _status_is_pass(runtime_state_binding_status):
            stale_reasons.append("prompt_runtime_state_binding_not_green")
        if not _status_is_pass(runtime_state_externalization_status):
            stale_reasons.append("prompt_runtime_state_externalization_not_green")

    current_run_driver_binding_status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    evidence_origin = "live" if current_run_driver_binding_status == STATUS_PASS_REQUIRED else ("prompt_presence" if prompt_exists else "missing")
    driver_projection_digest = prompt_sha or (report_hash_values[0] if report_hash_values else "") or prompt_state_hash

    return {
        "driver_receipt_refs": _collect_receipt_refs(
            clean_string(active_context.get("pointer_path")),
            str(report_path) if report_path is not None and report_path.exists() else clean_string(active_context.get("report_path")),
            str(prompt_state_path) if prompt_state_path is not None and prompt_state_path.exists() else prompt_runtime_state_rel,
        ),
        "driver_run_id": current_run_id,
        "driver_projection_digest": driver_projection_digest,
        "current_run_driver_binding_status": current_run_driver_binding_status,
        "requiredization_current_round_linked": current_run_driver_binding_status == STATUS_PASS_REQUIRED,
        "current_run_report_path": str(report_path) if report_path is not None and report_path.exists() else "",
        "prompt_runtime_state_path": str(prompt_state_path) if prompt_state_path is not None and prompt_state_path.exists() else "",
        "evidence_origin": evidence_origin,
        "stale_reasons": stale_reasons,
    }
