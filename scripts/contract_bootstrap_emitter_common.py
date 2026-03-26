#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}

STATUS_TOKENS = {
    STATUS_PASS_REQUIRED,
    STATUS_FAIL_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
}

EMITTER_ROLE_SPECS: dict[str, dict[str, Any]] = {
    "bootstrap_emitter": {
        "auto_materializable": True,
        "receipt_pattern_keys": ("rotation_receipt_pattern",),
        "invocations": (
            {
                "invocation_id": "bootstrap",
                "label": "bootstrap",
                "extra_args": (),
                "supports_apply": True,
            },
        ),
    },
    "atomic_emitter": {
        "auto_materializable": True,
        "receipt_pattern_keys": ("receipt_path_pattern",),
        "invocations": (
            {
                "invocation_id": "atomic",
                "label": "atomic",
                "extra_args": (),
                "supports_apply": False,
            },
        ),
    },
    "matrix_emitter": {
        "auto_materializable": True,
        "receipt_pattern_keys": ("refresh_receipt_pattern", "strict_receipt_pattern"),
        "required_task_list_fields": ("required_validators",),
        "invocations": (
            {
                "invocation_id": "refresh",
                "label": "refresh",
                "extra_args": ("--mode", "refresh"),
                "supports_apply": False,
            },
            {
                "invocation_id": "strict",
                "label": "strict",
                "extra_args": ("--mode", "strict"),
                "supports_apply": False,
            },
        ),
    },
    "receipt_emitter": {
        "auto_materializable": False,
        "receipt_pattern_keys": ("receipt_path_pattern",),
        "invocations": (
            {
                "invocation_id": "receipt",
                "label": "receipt",
                "extra_args": (),
                "supports_apply": False,
            },
        ),
    },
}


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = _clean_str(raw)
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _resolve_status_token(payload: dict[str, Any] | None, *, rc: int) -> str:
    if isinstance(payload, dict):
        preferred_fields = (
            "freshness_status",
            "atomic_emit_status",
            "interference_matrix_status",
            "pin_status",
            "status",
        )
        for key in preferred_fields:
            candidate = _clean_str(payload.get(key)).upper()
            if candidate in STATUS_TOKENS:
                return candidate
        for key, value in payload.items():
            if not str(key).endswith("_status"):
                continue
            candidate = _clean_str(value).upper()
            if candidate in STATUS_TOKENS:
                return candidate
    return STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED


def _role_preconditions_satisfied(*, task_doc: dict[str, Any], role_spec: dict[str, Any]) -> bool:
    required_task_list_fields = tuple(role_spec.get("required_task_list_fields") or ())
    if not required_task_list_fields:
        return True
    for field in required_task_list_fields:
        values = task_doc.get(field)
        if isinstance(values, (list, tuple)) and any(_clean_str(item) for item in values):
            continue
        return False
    return True


def iter_bootstrap_emitter_contracts(
    task_doc: dict[str, Any],
    *,
    force_required: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_key, node in (task_doc or {}).items():
        if not isinstance(node, dict):
            continue
        for emitter_role, role_spec in EMITTER_ROLE_SPECS.items():
            if role_spec.get("auto_materializable") is False:
                continue
            if not _role_preconditions_satisfied(task_doc=task_doc, role_spec=role_spec):
                continue
            emitter_rel = _clean_str(node.get(emitter_role))
            if not emitter_rel:
                continue
            receipt_patterns = {
                key: _clean_str(node.get(key))
                for key in role_spec.get("receipt_pattern_keys", ())
                if _clean_str(node.get(key))
            }
            rows.append(
                {
                    "task_key": _clean_str(task_key),
                    "contract": node,
                    "required": bool(force_required or contract_required(node)),
                    "emitter_role": emitter_role,
                    "bootstrap_emitter": emitter_rel,
                    "validator": _clean_str(node.get("validator")),
                    "required_fields": [
                        _clean_str(item)
                        for item in (node.get("required_fields") or [])
                        if _clean_str(item)
                    ],
                    "receipt_pattern": next(iter(receipt_patterns.values()), ""),
                    "receipt_patterns": receipt_patterns,
                    "fail_action": _clean_str(node.get("fail_action")),
                    "invocations": [
                        {
                            "invocation_id": _clean_str(invocation.get("invocation_id")),
                            "label": _clean_str(invocation.get("label")),
                            "extra_args": [
                                _clean_str(arg)
                                for arg in (invocation.get("extra_args") or ())
                                if _clean_str(arg)
                            ],
                            "supports_apply": bool(invocation.get("supports_apply", False)),
                        }
                        for invocation in (role_spec.get("invocations") or ())
                    ],
                }
            )
    return rows


def resolve_bootstrap_emitter_path(*, repo_root: Path, emitter_rel: str) -> Path:
    emitter_path = (repo_root / emitter_rel).resolve()
    try:
        emitter_path.relative_to(repo_root.resolve())
    except Exception as exc:
        raise ValueError(f"bootstrap_emitter_outside_repo:{emitter_rel}") from exc
    if not emitter_path.exists() or not emitter_path.is_file():
        raise FileNotFoundError(f"bootstrap_emitter_missing:{emitter_rel}")
    return emitter_path


def build_bootstrap_emitter_cmd(
    *,
    repo_root: Path,
    emitter_rel: str,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    apply: bool,
    invocation: dict[str, Any] | None = None,
) -> list[str]:
    emitter_path = resolve_bootstrap_emitter_path(repo_root=repo_root, emitter_rel=emitter_rel)
    invocation = invocation or {}
    cmd = [
        "python3",
        str(emitter_path),
        "--catalog",
        str(catalog_path.resolve()),
        "--identity-id",
        _clean_str(identity_id),
        "--operation",
        _clean_str(operation) or "validate",
        "--json-only",
    ]
    if apply and bool(invocation.get("supports_apply", False)):
        cmd.append("--apply")
    for arg in invocation.get("extra_args") or ():
        token = _clean_str(arg)
        if token:
            cmd.append(token)
    return cmd


def run_bootstrap_emitter(
    *,
    repo_root: Path,
    emitter_rel: str,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    apply: bool,
    invocation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cmd = build_bootstrap_emitter_cmd(
        repo_root=repo_root,
        emitter_rel=emitter_rel,
        catalog_path=catalog_path,
        identity_id=identity_id,
        operation=operation,
        apply=apply,
        invocation=invocation,
    )
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root.resolve()),
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _parse_json_payload(proc.stdout or "") or {}
    row_status = _resolve_status_token(payload, rc=proc.returncode)
    return {
        "cmd": cmd,
        "rc": int(proc.returncode),
        "status": row_status,
        "payload": payload,
        "stdout_tail": (proc.stdout or "")[-400:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }


def materialize_required_bootstrap_emitters(
    *,
    repo_root: Path,
    catalog_path: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    operation: str,
    apply: bool,
    force_required: bool = False,
) -> dict[str, Any]:
    all_rows = iter_bootstrap_emitter_contracts(task_doc, force_required=force_required)
    required_rows = [row for row in all_rows if bool(row.get("required"))]
    effective_apply = bool(apply or operation in STRICT_OPERATIONS)
    payload: dict[str, Any] = {
        "apply": effective_apply,
        "contract_bootstrap_emitter_count": len(all_rows),
        "required_bootstrap_emitter_count": len(required_rows),
        "materialized_bootstrap_emitter_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "rows": [],
        "stale_reasons": [],
    }
    if not required_rows:
        payload["stale_reasons"] = ["no_required_contract_bootstrap_emitters_declared"]
        return payload

    stale_reasons: list[str] = []
    rows_out: list[dict[str, Any]] = []
    for row in required_rows:
        invocation_results: list[dict[str, Any]] = []
        row_status = STATUS_PASS_REQUIRED
        row_rc = 0
        for invocation in (row.get("invocations") or ({"invocation_id": "default", "label": "default", "extra_args": [], "supports_apply": True},)):
            invocation_id = _clean_str(invocation.get("invocation_id")) or "default"
            try:
                result = run_bootstrap_emitter(
                    repo_root=repo_root,
                    emitter_rel=str(row.get("bootstrap_emitter", "")).strip(),
                    catalog_path=catalog_path,
                    identity_id=identity_id,
                    operation=operation,
                    apply=effective_apply,
                    invocation=invocation,
                )
            except Exception as exc:
                result = {
                    "cmd": [],
                    "rc": 1,
                    "status": STATUS_FAIL_REQUIRED,
                    "payload": {},
                    "stdout_tail": "",
                    "stderr_tail": "",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                }
            result_with_invocation = {
                "invocation_id": invocation_id,
                "label": _clean_str(invocation.get("label")) or invocation_id,
                "supports_apply": bool(invocation.get("supports_apply", False)),
                "extra_args": list(invocation.get("extra_args") or []),
                **result,
            }
            invocation_results.append(result_with_invocation)
            row_rc = max(row_rc, int(result.get("rc", 0)))
            if str(result.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
                row_status = STATUS_FAIL_REQUIRED
                stale_reasons.append(
                    f"bootstrap_emitter_not_green:{str(row.get('task_key', '')).strip()}:{invocation_id}:{str(result.get('status', '')).strip() or 'UNKNOWN'}"
                )
            if str(result.get("exception_type", "")).strip():
                stale_reasons.append(
                    f"bootstrap_emitter_exception:{str(row.get('task_key', '')).strip()}:{invocation_id}:{str(result.get('exception_type', '')).strip()}"
                )
            if int(result.get("rc", 1)) != 0:
                stale_reasons.append(
                    f"bootstrap_emitter_rc_nonzero:{str(row.get('task_key', '')).strip()}:{invocation_id}"
                )

        representative = invocation_results[0] if invocation_results else {
            "cmd": [],
            "rc": 1,
            "status": STATUS_FAIL_REQUIRED,
            "payload": {},
            "stdout_tail": "",
            "stderr_tail": "",
        }
        aggregate_payload: dict[str, Any]
        if len(invocation_results) == 1:
            aggregate_payload = dict(representative.get("payload") or {})
        else:
            aggregate_payload = {
                "multi_invocation": True,
                "invocation_count": len(invocation_results),
                "invocation_ids": [str(item.get("invocation_id", "")).strip() for item in invocation_results],
                "payloads_by_invocation": {
                    str(item.get("invocation_id", "")).strip(): dict(item.get("payload") or {})
                    for item in invocation_results
                    if str(item.get("invocation_id", "")).strip()
                },
                "evidence_refs": [
                    str((item.get("payload") or {}).get("evidence_ref", "")).strip()
                    for item in invocation_results
                    if str((item.get("payload") or {}).get("evidence_ref", "")).strip()
                ],
            }

        result_row = {
            "task_key": str(row.get("task_key", "")).strip(),
            "emitter_role": str(row.get("emitter_role", "")).strip(),
            "bootstrap_emitter": str(row.get("bootstrap_emitter", "")).strip(),
            "validator": str(row.get("validator", "")).strip(),
            "receipt_pattern": str(row.get("receipt_pattern", "")).strip(),
            "receipt_patterns": dict(row.get("receipt_patterns") or {}),
            "fail_action": str(row.get("fail_action", "")).strip(),
            "required_fields": list(row.get("required_fields") or []),
            "invocation_count": len(invocation_results),
            "invocations": invocation_results,
            "cmd": representative.get("cmd", []),
            "rc": row_rc,
            "status": row_status,
            "payload": aggregate_payload,
            "stdout_tail": representative.get("stdout_tail", ""),
            "stderr_tail": representative.get("stderr_tail", ""),
        }
        if str(representative.get("exception_type", "")).strip():
            result_row["exception_type"] = str(representative.get("exception_type", "")).strip()
        if str(representative.get("exception_message", "")).strip():
            result_row["exception_message"] = str(representative.get("exception_message", "")).strip()
        rows_out.append(result_row)

    payload["rows"] = rows_out
    payload["stale_reasons"] = sorted(set(reason for reason in stale_reasons if reason))
    payload["materialized_bootstrap_emitter_status"] = (
        STATUS_PASS_REQUIRED if not payload["stale_reasons"] else STATUS_FAIL_REQUIRED
    )
    if payload["materialized_bootstrap_emitter_status"] != STATUS_PASS_REQUIRED:
        payload["error_code"] = "IP-CBE-001"
    return payload
