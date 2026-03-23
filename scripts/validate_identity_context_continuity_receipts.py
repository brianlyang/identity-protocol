#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from identity_context_continuity_common import (
    CHECKPOINT_ARTIFACT_KINDS,
    CONTINUITY_AUXILIARY_RECEIPT_KINDS,
    CONTINUITY_RECEIPT_KINDS,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    clean_string,
    continuity_report_location_status,
    continuity_report_root,
    discover_continuity_report_doc,
    load_json,
    resolve_pack_task,
)

ERR_MEMBER_MISSING = "IP-ICREC-001"
ERR_MEMBER_INVALID = "IP-ICREC-002"
ERR_JOIN_INVALID = "IP-ICREC-003"
ERR_UNKNOWN_KIND = "IP-ICREC-004"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = REPO_ROOT.parent

ROLE_ORDER: tuple[str, ...] = (
    "checkpoint",
    "migration_handoff",
    "reentry_brief",
    "reentry_consumption",
)
ROLE_STATUS_FIELDS: dict[str, str] = {
    "checkpoint": "checkpoint_receipt_status",
    "migration_handoff": "migration_handoff_receipt_status",
    "reentry_brief": "reentry_brief_receipt_status",
    "reentry_consumption": "reentry_consumption_receipt_status",
}
ROLE_ARG_FIELDS: dict[str, str] = {
    "checkpoint": "checkpoint_receipt",
    "migration_handoff": "migration_receipt",
    "reentry_brief": "reentry_brief_receipt",
    "reentry_consumption": "reentry_consumption_receipt",
}
RECEIPT_SCOPE_KEYS: tuple[str, ...] = (
    "route_or_entry_scope",
    "entry_scope",
    "startup_scope",
    "scope",
    "consumption_scope",
)
FORBIDDEN_CROSS_STREAM_KEYS: tuple[str, ...] = (
    "thread_uuid",
    "thread_id",
    "session_id",
    "launcher_install_receipt",
    "launcher_install_receipt_ref",
    "tuple_receipt_ref",
    "actor_session_receipt_ref",
    "route_selected",
    "script_id",
)
ALLOWED_CONTINUITY_RECEIPT_KINDS = frozenset(CONTINUITY_RECEIPT_KINDS.values())
ROLE_DISCOVERY_FIELDS: dict[str, tuple[str, ...]] = {
    "checkpoint": ("receipt_kind",),
    "migration_handoff": ("receipt_kind",),
    "reentry_brief": ("receipt_kind",),
    "reentry_consumption": ("receipt_kind", "reentry_brief_ref", "continuity_lineage_ref"),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_local_reference(token: str, *, pack_root: Path) -> Path | None:
    text = clean_string(token)
    if not text:
        return None
    candidate = Path(text).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        return resolved if resolved.exists() else None
    for base in (pack_root, REPO_ROOT, WORKSPACE_ROOT):
        resolved = (base / candidate).resolve()
        if resolved.exists():
            return resolved
    return None


def _run_json_validator(cmd: list[str]) -> tuple[int, dict[str, Any], str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    stdout = proc.stdout.strip()
    if stdout:
        try:
            return proc.returncode, json.loads(stdout), stdout
        except Exception:
            return proc.returncode, {}, stdout
    return proc.returncode, {}, stdout


def _extract_first(doc: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        token = clean_string(doc.get(key))
        if token:
            return token
    return ""


def _extract_scope(doc: dict[str, Any]) -> str:
    return _extract_first(doc, RECEIPT_SCOPE_KEYS)


def _discover_role_receipt(*, pack_root: Path, explicit_receipt: str, role: str) -> tuple[Path | None, str]:
    return discover_continuity_report_doc(
        pack_root=pack_root,
        explicit_report=explicit_receipt,
        required_fields=ROLE_DISCOVERY_FIELDS[role],
        preferred_receipt_kind=CONTINUITY_RECEIPT_KINDS[role],
        selection_requires_fields=False,
    )


def _read_receipt_doc(path: Path) -> dict[str, Any]:
    return load_json(path)


def _forbidden_key_issues(doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in FORBIDDEN_CROSS_STREAM_KEYS:
        if key in doc and doc.get(key) not in (None, "", [], {}):
            issues.append(f"forbidden_cross_stream_key_present:{key}")
    return issues


def _scan_unknown_continuity_receipt_kinds(report_root: Path) -> list[str]:
    if not report_root.exists():
        return []
    issues: list[str] = []
    for path in sorted(report_root.glob("*.json")):
        if not path.is_file():
            continue
        try:
            doc = load_json(path)
        except Exception:
            continue
        kind = clean_string(doc.get("receipt_kind") or doc.get("receipt_family"))
        if not kind:
            continue
        if kind in ALLOWED_CONTINUITY_RECEIPT_KINDS:
            continue
        if kind in CONTINUITY_AUXILIARY_RECEIPT_KINDS:
            continue
        lowered = kind.lower()
        if any(token in lowered for token in ("continuity", "reentry", "migration")):
            issues.append(f"unknown_continuity_receipt_kind:{kind}:{path.name}")
    return issues


def _validate_artifact_backed_receipt(
    *,
    role: str,
    receipt_doc: dict[str, Any],
    receipt_path: Path,
    pack_root: Path,
    identity_id: str,
    current_task: str,
) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    payload: dict[str, Any] = {
        "receipt_path": str(receipt_path),
        "receipt_kind": clean_string(receipt_doc.get("receipt_kind") or receipt_doc.get("receipt_family")),
        "artifact_ref": "",
        "artifact_path": "",
        "artifact_kind": "",
        "current_continuity_id": "",
        "parent_continuity_ref": "",
        "scope": _extract_scope(receipt_doc),
        "validator_status": STATUS_FAIL_REQUIRED,
    }

    location_status, location_issues = continuity_report_location_status(pack_root=pack_root, report_path=receipt_path)
    if location_status != STATUS_PASS_REQUIRED:
        issues.extend(location_issues)

    expected_kind = CONTINUITY_RECEIPT_KINDS[role]
    receipt_kind = payload["receipt_kind"]
    if not receipt_kind:
        issues.append("receipt_kind_missing")
    elif receipt_kind != expected_kind:
        issues.append(f"receipt_kind_mismatch:{receipt_kind}")

    issues.extend(_forbidden_key_issues(receipt_doc))

    artifact_ref_token = _extract_first(receipt_doc, ("artifact_ref", "continuity_artifact_ref", "checkpoint_ref", "migration_checkpoint_ref"))
    payload["artifact_ref"] = artifact_ref_token
    if not artifact_ref_token:
        issues.append("artifact_ref_missing")
        return payload, issues

    artifact_path = _resolve_local_reference(artifact_ref_token, pack_root=pack_root)
    if artifact_path is None:
        issues.append("artifact_ref_unresolved")
        return payload, issues
    payload["artifact_path"] = str(artifact_path)

    artifact_kind = _extract_first(receipt_doc, ("artifact_kind", "continuity_artifact_kind"))
    payload["artifact_kind"] = artifact_kind
    allowed_artifact_kinds = ("migration_checkpoint",) if role == "migration_handoff" else tuple(
        kind for kind in CHECKPOINT_ARTIFACT_KINDS if kind != "migration_checkpoint"
    )
    if not artifact_kind:
        issues.append("artifact_kind_missing")
    elif artifact_kind not in allowed_artifact_kinds:
        issues.append(f"artifact_kind_invalid:{artifact_kind}")

    cmd = [
        "python3",
        str(SCRIPT_DIR / "validate_identity_context_continuity.py"),
        "--identity-id",
        identity_id,
        "--current-task",
        current_task,
        "--artifact",
        str(artifact_path),
        "--artifact-kind",
        artifact_kind,
        "--json-only",
    ]
    rc, validator_payload, _ = _run_json_validator(cmd)
    payload["validator_status"] = clean_string(validator_payload.get("identity_context_continuity_status")) or (
        STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    )
    if payload["validator_status"] != STATUS_PASS_REQUIRED:
        issues.append(
            f"artifact_validator_failed:{clean_string(validator_payload.get('error_code')) or 'continuity_validator_failed'}"
        )
        payload["current_continuity_id"] = clean_string(validator_payload.get("continuity_id"))
        payload["parent_continuity_ref"] = clean_string(validator_payload.get("supersedes_ref"))
        return payload, issues

    payload["current_continuity_id"] = clean_string(validator_payload.get("continuity_id")) or _extract_first(
        receipt_doc,
        ("continuity_id", "continuity_lineage_ref", "continuity_ref", "lineage_ref"),
    )
    payload["parent_continuity_ref"] = clean_string(validator_payload.get("supersedes_ref")) or _extract_first(
        receipt_doc,
        ("parent_continuity_ref", "supersedes_ref", "continuity_lineage_ref", "continuity_ref", "lineage_ref"),
    )
    if not payload["current_continuity_id"]:
        issues.append("continuity_id_missing")
    if role == "migration_handoff" and not payload["parent_continuity_ref"]:
        issues.append("migration_parent_lineage_missing")
    return payload, issues


def _validate_reentry_brief_receipt(
    *,
    receipt_doc: dict[str, Any],
    receipt_path: Path,
    pack_root: Path,
    identity_id: str,
    current_task: str,
) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    payload: dict[str, Any] = {
        "receipt_path": str(receipt_path),
        "receipt_kind": clean_string(receipt_doc.get("receipt_kind") or receipt_doc.get("receipt_family")),
        "brief_ref": "",
        "brief_resolved_path": "",
        "continuity_lineage_ref": "",
        "current_continuity_id": "",
        "scope": _extract_scope(receipt_doc),
        "validator_status": STATUS_FAIL_REQUIRED,
    }

    location_status, location_issues = continuity_report_location_status(pack_root=pack_root, report_path=receipt_path)
    if location_status != STATUS_PASS_REQUIRED:
        issues.extend(location_issues)

    if not payload["receipt_kind"]:
        issues.append("receipt_kind_missing")
    elif payload["receipt_kind"] != CONTINUITY_RECEIPT_KINDS["reentry_brief"]:
        issues.append(f"receipt_kind_mismatch:{payload['receipt_kind']}")

    issues.extend(_forbidden_key_issues(receipt_doc))

    brief_ref_token = _extract_first(receipt_doc, ("reentry_brief_ref", "brief_ref", "artifact_ref"))
    payload["brief_ref"] = brief_ref_token
    if not brief_ref_token:
        issues.append("reentry_brief_ref_missing")
        return payload, issues

    brief_path = _resolve_local_reference(brief_ref_token, pack_root=pack_root)
    if brief_path is None:
        issues.append("reentry_brief_ref_unresolved")
        return payload, issues
    payload["brief_resolved_path"] = str(brief_path)

    cmd = [
        "python3",
        str(SCRIPT_DIR / "validate_identity_reentry_brief.py"),
        "--identity-id",
        identity_id,
        "--current-task",
        current_task,
        "--brief",
        str(brief_path),
        "--json-only",
    ]
    rc, validator_payload, _ = _run_json_validator(cmd)
    payload["validator_status"] = clean_string(validator_payload.get("identity_reentry_brief_status")) or (
        STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    )
    payload["continuity_lineage_ref"] = clean_string(validator_payload.get("continuity_lineage_ref")) or _extract_first(
        receipt_doc,
        ("continuity_lineage_ref", "lineage_ref", "continuity_ref"),
    )
    payload["current_continuity_id"] = clean_string(validator_payload.get("continuity_id"))
    if payload["validator_status"] != STATUS_PASS_REQUIRED:
        issues.append(f"reentry_brief_validator_failed:{clean_string(validator_payload.get('error_code')) or 'brief_validator_failed'}")
        return payload, issues

    if not payload["continuity_lineage_ref"]:
        issues.append("continuity_lineage_ref_missing")
    return payload, issues


def _validate_reentry_consumption_receipt(
    *,
    receipt_doc: dict[str, Any],
    receipt_path: Path,
    pack_root: Path,
    identity_id: str,
    current_task: str,
    brief_hint: str,
) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    payload: dict[str, Any] = {
        "receipt_path": str(receipt_path),
        "receipt_kind": clean_string(receipt_doc.get("receipt_kind") or receipt_doc.get("receipt_family")),
        "brief_ref": clean_string(receipt_doc.get("reentry_brief_ref")),
        "brief_resolved_path": "",
        "continuity_lineage_ref": clean_string(receipt_doc.get("continuity_lineage_ref")),
        "scope": _extract_scope(receipt_doc),
        "validator_status": STATUS_FAIL_REQUIRED,
    }

    location_status, location_issues = continuity_report_location_status(pack_root=pack_root, report_path=receipt_path)
    if location_status != STATUS_PASS_REQUIRED:
        issues.extend(location_issues)

    if not payload["receipt_kind"]:
        issues.append("receipt_kind_missing")
    elif payload["receipt_kind"] != CONTINUITY_RECEIPT_KINDS["reentry_consumption"]:
        issues.append(f"receipt_kind_mismatch:{payload['receipt_kind']}")

    issues.extend(_forbidden_key_issues(receipt_doc))

    cmd = [
        "python3",
        str(SCRIPT_DIR / "validate_identity_reentry_consumption.py"),
        "--identity-id",
        identity_id,
        "--current-task",
        current_task,
        "--receipt",
        str(receipt_path),
        "--json-only",
    ]
    if brief_hint:
        cmd.extend(["--brief", brief_hint])
    rc, validator_payload, _ = _run_json_validator(cmd)
    payload["validator_status"] = clean_string(validator_payload.get("identity_reentry_consumption_status")) or (
        STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    )
    payload["brief_ref"] = clean_string(validator_payload.get("reentry_brief_ref")) or payload["brief_ref"]
    resolved_brief = _resolve_local_reference(payload["brief_ref"], pack_root=pack_root) if payload["brief_ref"] else None
    if resolved_brief is not None:
        payload["brief_resolved_path"] = str(resolved_brief)
    payload["continuity_lineage_ref"] = clean_string(validator_payload.get("continuity_lineage_ref")) or payload["continuity_lineage_ref"]
    payload["scope"] = clean_string(validator_payload.get("route_or_entry_scope")) or payload["scope"]
    if payload["validator_status"] != STATUS_PASS_REQUIRED:
        issues.append(
            f"reentry_consumption_validator_failed:{clean_string(validator_payload.get('error_code')) or 'consumption_validator_failed'}"
        )
        return payload, issues

    if not payload["brief_ref"]:
        issues.append("reentry_brief_ref_missing")
    if not payload["continuity_lineage_ref"]:
        issues.append("continuity_lineage_ref_missing")
    return payload, issues


def _join_family(role_rows: dict[str, dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    distinct_paths = [clean_string(role_rows[role].get("receipt_path")) for role in ROLE_ORDER]
    if len(set(distinct_paths)) != len(distinct_paths):
        issues.append("receipt_role_paths_collapsed")

    checkpoint_current = clean_string(role_rows["checkpoint"].get("current_continuity_id"))
    if not checkpoint_current:
        issues.append("checkpoint_continuity_id_missing")
        return issues

    allowed_lineage = {checkpoint_current}
    migration_parent = clean_string(role_rows["migration_handoff"].get("parent_continuity_ref"))
    migration_current = clean_string(role_rows["migration_handoff"].get("current_continuity_id"))
    if not migration_parent:
        issues.append("migration_parent_lineage_missing")
    elif migration_parent not in allowed_lineage:
        issues.append(f"migration_parent_not_joinable:{migration_parent}")
    if migration_current:
        allowed_lineage.add(migration_current)

    brief_lineage = clean_string(role_rows["reentry_brief"].get("continuity_lineage_ref"))
    if not brief_lineage:
        issues.append("reentry_brief_lineage_missing")
    elif brief_lineage not in allowed_lineage:
        issues.append(f"reentry_brief_lineage_not_joinable:{brief_lineage}")
    brief_current = clean_string(role_rows["reentry_brief"].get("current_continuity_id"))
    if brief_current:
        allowed_lineage.add(brief_current)

    consumption_lineage = clean_string(role_rows["reentry_consumption"].get("continuity_lineage_ref"))
    if not consumption_lineage:
        issues.append("reentry_consumption_lineage_missing")
    elif consumption_lineage not in allowed_lineage:
        issues.append(f"reentry_consumption_lineage_not_joinable:{consumption_lineage}")

    brief_ref = clean_string(role_rows["reentry_brief"].get("brief_resolved_path")) or clean_string(role_rows["reentry_brief"].get("brief_ref"))
    consumption_brief_ref = clean_string(role_rows["reentry_consumption"].get("brief_resolved_path")) or clean_string(role_rows["reentry_consumption"].get("brief_ref"))
    if brief_ref and consumption_brief_ref and brief_ref != consumption_brief_ref:
        issues.append("reentry_consumption_brief_ref_mismatch")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity continuity receipt-family closure for v1.6.16.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--checkpoint-receipt", default="")
    ap.add_argument("--migration-receipt", default="")
    ap.add_argument("--reentry-brief-receipt", default="")
    ap.add_argument("--reentry-consumption-receipt", default="")
    ap.add_argument("--route-or-entry-scope", default="")
    ap.add_argument("--require-observed", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None

    try:
        pack_root, task_path, _task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "identity_context_continuity_receipt_family_status": STATUS_SKIPPED_NOT_REQUIRED,
        "checkpoint_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "migration_handoff_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reentry_brief_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reentry_consumption_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "receipt_join_status": STATUS_SKIPPED_NOT_REQUIRED,
        "route_or_entry_scope": clean_string(args.route_or_entry_scope),
        "receipt_observed_count": 0,
        "report_root": str(continuity_report_root(pack_root)),
        "checkpoint_receipt_path": "",
        "migration_handoff_receipt_path": "",
        "reentry_brief_receipt_path": "",
        "reentry_consumption_receipt_path": "",
        "checkpoint_receipt_discovery_mode": "",
        "migration_handoff_receipt_discovery_mode": "",
        "reentry_brief_receipt_discovery_mode": "",
        "reentry_consumption_receipt_discovery_mode": "",
        "stale_reasons": [],
        "error_code": "",
        "evidence_ref": str(task_path),
    }

    discovered: dict[str, tuple[Path | None, str]] = {}
    explicit_inputs = {
        role: clean_string(getattr(args, ROLE_ARG_FIELDS[role]))
        for role in ROLE_ORDER
    }
    for role in ROLE_ORDER:
        receipt_path, mode = _discover_role_receipt(
            pack_root=pack_root,
            explicit_receipt=explicit_inputs[role],
            role=role,
        )
        discovered[role] = (receipt_path, mode)
        payload[f"{role}_receipt_path"] = str(receipt_path) if receipt_path is not None else ""
        payload[f"{role}_receipt_discovery_mode"] = mode

    observed_count = sum(1 for path, _mode in discovered.values() if path is not None)
    payload["receipt_observed_count"] = observed_count

    if observed_count == 0 and not args.require_observed:
        payload["stale_reasons"] = ["continuity_receipt_family_not_observed"]
        _emit(payload, json_only=args.json_only)
        return 0

    role_rows: dict[str, dict[str, Any]] = {}
    missing_roles = [role for role in ROLE_ORDER if discovered[role][0] is None]
    for role in missing_roles:
        payload[ROLE_STATUS_FIELDS[role]] = STATUS_FAIL_REQUIRED
    if missing_roles:
        payload["identity_context_continuity_receipt_family_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MEMBER_MISSING
        payload["stale_reasons"] = [f"missing_receipt_role:{role}" for role in missing_roles]
        _emit(payload, json_only=args.json_only)
        return 1

    unknown_kind_issues = _scan_unknown_continuity_receipt_kinds(continuity_report_root(pack_root))
    if unknown_kind_issues:
        for role in ROLE_ORDER:
            payload[ROLE_STATUS_FIELDS[role]] = STATUS_FAIL_REQUIRED
        payload["identity_context_continuity_receipt_family_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_UNKNOWN_KIND
        payload["stale_reasons"] = unknown_kind_issues
        payload["evidence_ref"] = str(continuity_report_root(pack_root))
        _emit(payload, json_only=args.json_only)
        return 1

    member_invalid_issues: list[str] = []
    for role in ROLE_ORDER:
        receipt_path = discovered[role][0]
        assert receipt_path is not None
        try:
            receipt_doc = _read_receipt_doc(receipt_path)
            if not isinstance(receipt_doc, dict):
                raise ValueError("receipt_root_not_object")
        except Exception as exc:
            payload[ROLE_STATUS_FIELDS[role]] = STATUS_FAIL_REQUIRED
            member_invalid_issues.append(f"{role}_receipt_invalid:{exc}")
            continue

        if role in {"checkpoint", "migration_handoff"}:
            row, issues = _validate_artifact_backed_receipt(
                role=role,
                receipt_doc=receipt_doc,
                receipt_path=receipt_path,
                pack_root=pack_root,
                identity_id=args.identity_id,
                current_task=str(task_path),
            )
        elif role == "reentry_brief":
            row, issues = _validate_reentry_brief_receipt(
                receipt_doc=receipt_doc,
                receipt_path=receipt_path,
                pack_root=pack_root,
                identity_id=args.identity_id,
                current_task=str(task_path),
            )
        else:
            brief_row = role_rows.get("reentry_brief", {})
            brief_hint = clean_string(brief_row.get("brief_resolved_path")) or clean_string(brief_row.get("brief_ref"))
            row, issues = _validate_reentry_consumption_receipt(
                receipt_doc=receipt_doc,
                receipt_path=receipt_path,
                pack_root=pack_root,
                identity_id=args.identity_id,
                current_task=str(task_path),
                brief_hint=brief_hint,
            )
        role_rows[role] = row
        payload[ROLE_STATUS_FIELDS[role]] = STATUS_FAIL_REQUIRED if issues else STATUS_PASS_REQUIRED
        if issues:
            member_invalid_issues.extend(f"{role}:{issue}" for issue in issues)
        scope = clean_string(row.get("scope"))
        if scope and not payload["route_or_entry_scope"]:
            payload["route_or_entry_scope"] = scope

    if member_invalid_issues:
        payload["identity_context_continuity_receipt_family_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MEMBER_INVALID
        payload["stale_reasons"] = member_invalid_issues
        for role in ROLE_ORDER:
            row = role_rows.get(role)
            if row and clean_string(row.get("receipt_path")):
                payload[f"{role}_receipt_path"] = clean_string(row.get("receipt_path"))
        payload["evidence_ref"] = str(continuity_report_root(pack_root))
        _emit(payload, json_only=args.json_only)
        return 1

    if not payload["route_or_entry_scope"]:
        payload["route_or_entry_scope"] = "startup_resume_recover"

    join_issues = _join_family(role_rows)
    if join_issues:
        payload["identity_context_continuity_receipt_family_status"] = STATUS_FAIL_REQUIRED
        payload["receipt_join_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_JOIN_INVALID
        payload["stale_reasons"] = join_issues
        payload["evidence_ref"] = str(continuity_report_root(pack_root))
        _emit(payload, json_only=args.json_only)
        return 1

    payload["identity_context_continuity_receipt_family_status"] = STATUS_PASS_REQUIRED
    payload["receipt_join_status"] = STATUS_PASS_REQUIRED
    payload["evidence_ref"] = str(continuity_report_root(pack_root))
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
