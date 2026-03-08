#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"

BUNDLE_CONTRACT_ID = "hotfix_p0_007_ucg_control_plane_freeze_contract_v1"
BUNDLE_KEY = "required_gate_bundle_runner"

# Order is deterministic for replay and log comparison.
BUNDLE_REQUIREMENT_ORDER: tuple[str, ...] = (
    "asb16-rq-017",
    "asb16-rq-030",
    "asb16-rq-021",
    "asb16-rq-022",
    "asb16-rq-018",
    "asb16-rq-019",
    "asb16-rq-020",
    "asb16-rq-033",
    "asb16-rq-034",
)

TARGET_NAME_BY_REQUIREMENT: dict[str, str] = {
    "asb16-rq-017": "cross_verification_tracks",
    "asb16-rq-030": "intake_evidence_quorum",
    "asb16-rq-021": "route_version_pinning",
    "asb16-rq-022": "fallback_taxonomy_normalization",
    "asb16-rq-018": "dedup_monotonicity",
    "asb16-rq-019": "cross_workflow_schema",
    "asb16-rq-020": "skill_path_integrity",
    "asb16-rq-033": "execution_target_tuple_isolation",
    "asb16-rq-034": "multimodal_plugin_enforcement",
}
REQUIREMENT_BY_TARGET: dict[str, str] = {v: k for k, v in TARGET_NAME_BY_REQUIREMENT.items()}

STATUS_FIELD_BY_TARGET: dict[str, str] = {
    "cross_verification_tracks": "cross_verification_tracks_status",
    "intake_evidence_quorum": "intake_evidence_quorum_status",
    "route_version_pinning": "pin_status",
    "fallback_taxonomy_normalization": "fallback_taxonomy_normalization_status",
    "dedup_monotonicity": "monotonicity_status",
    "cross_workflow_schema": "cross_workflow_schema_status",
    "skill_path_integrity": "path_integrity_status",
    "execution_target_tuple_isolation": "execution_target_tuple_isolation_status",
    "multimodal_plugin_enforcement": "multimodal_plugin_enforcement_status",
}

ERROR_FIELD_CANDIDATES: tuple[str, ...] = (
    "error_code",
    "pin_error_code",
    "normalization_error_code",
    "path_integrity_error_code",
    "route_conflict_error_code",
)

TRUTHY_VALUES: tuple[str, ...] = ("1", "true", "yes", "y", "on")
FALSY_VALUES: tuple[str, ...] = ("0", "false", "no", "n", "off", "")


@dataclass(frozen=True)
class ValidatorSpec:
    requirement_key: str
    target_name: str
    script_path: str
    fixed_args: tuple[str, ...] = ()


def _resolve_default_contract_mapping(repo_root: Path) -> Path:
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    fallback = mapping_dir / "contract-binding.yaml"
    return fallback


def _parse_validator_entry(raw_entry: str) -> tuple[str, tuple[str, ...]]:
    # Example raw entries:
    # - scripts/validate_v16_intake_evidence_core.py::mode=intake_contract
    # - scripts/validate_v16_cross_verification_tracks.py::wrapper_only_optional
    raw = str(raw_entry or "").strip()
    if not raw:
        return "", ()
    if "::" not in raw:
        return raw, ()
    script_part, suffix = raw.split("::", 1)
    suffix = suffix.strip()
    if not suffix:
        return script_part.strip(), ()
    if suffix.startswith("mode="):
        mode_value = suffix.split("=", 1)[1].strip()
        if mode_value:
            return script_part.strip(), ("--mode", mode_value)
    # wrapper/optional annotations are metadata only and do not map to CLI flags.
    return script_part.strip(), ()


def _select_validator_spec(requirement_key: str, row: dict[str, Any]) -> ValidatorSpec | None:
    target_name = TARGET_NAME_BY_REQUIREMENT.get(requirement_key, requirement_key)
    validator_ids = list(row.get("validator_ids") or [])
    parsed: list[tuple[str, tuple[str, ...]]] = [
        _parse_validator_entry(entry) for entry in validator_ids if str(entry or "").strip()
    ]
    if not parsed:
        return None

    # Prefer validate_* scripts for gate execution (emit/normalize helpers are non-gating helpers).
    preferred: tuple[str, tuple[str, ...]] | None = None
    for script_path, fixed_args in parsed:
        base = Path(script_path).name
        if base.startswith("validate_"):
            preferred = (script_path, fixed_args)
            break
    if preferred is None:
        preferred = parsed[0]
    return ValidatorSpec(
        requirement_key=requirement_key,
        target_name=target_name,
        script_path=preferred[0],
        fixed_args=preferred[1],
    )


def _load_validator_specs(mapping_path: Path, requirement_keys: tuple[str, ...]) -> tuple[list[ValidatorSpec], list[str]]:
    if not mapping_path.exists():
        return [], [f"contract_mapping_missing:{mapping_path}"]

    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    specs: list[ValidatorSpec] = []
    for requirement_key in requirement_keys:
        row = data.get(requirement_key)
        if not isinstance(row, dict):
            errors.append(f"mapping_row_missing:{requirement_key}")
            continue
        spec = _select_validator_spec(requirement_key, row)
        if spec is None:
            errors.append(f"validator_ids_missing:{requirement_key}")
            continue
        specs.append(spec)
    return specs, errors


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return int(proc.returncode), proc.stdout, proc.stderr


def _parse_payload(stdout_text: str) -> dict[str, Any]:
    text = (stdout_text or "").strip()
    if not text:
        return {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in reversed(lines):
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _extract_error_code(payload: dict[str, Any], stderr_text: str) -> str:
    for key in ERROR_FIELD_CANDIDATES:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    err = str(stderr_text or "").strip()
    if "IP-" in err:
        # keep tail concise for replay readability
        tail = err.splitlines()[-1] if err.splitlines() else err
        return tail.strip()
    return ""


def _classify_status(*, target_name: str, rc: int, payload: dict[str, Any]) -> tuple[str, str]:
    status_field = STATUS_FIELD_BY_TARGET[target_name]
    status_value = str(payload.get(status_field, "")).strip().upper()
    if status_value in {
        STATUS_PASS_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_FAIL_REQUIRED,
    }:
        return status_value, status_field
    if status_value == STATUS_FAIL_OPTIONAL:
        return STATUS_FAIL_REQUIRED, status_field

    if rc != 0:
        return STATUS_FAIL_REQUIRED, status_field
    if status_field not in payload:
        return STATUS_FAIL_REQUIRED, status_field
    required_contract = bool(payload.get("required_contract", False))
    return (STATUS_PASS_REQUIRED if required_contract else STATUS_SKIPPED_NOT_REQUIRED), status_field


def _validate_row_payload_contract(*, payload: dict[str, Any], status_field: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict) or not payload:
        issues.append("payload_missing_or_not_object")
        return issues
    if status_field not in payload:
        issues.append("status_field_missing")
    if "required_contract" not in payload:
        issues.append("required_contract_missing")
    return issues


def _write_payload_out(out_path: str, payload: dict[str, Any]) -> None:
    target = Path(out_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_bool_token(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    text = str(raw or "").strip().lower()
    if text in TRUTHY_VALUES:
        return True
    if text in FALSY_VALUES:
        return False
    return False


def _derive_parity_operation_scope(*, operation: str, surface_label: str) -> str:
    op = str(operation or "").strip().lower()
    label = str(surface_label or "").strip().lower()
    if op in {"scan", "inspection"} and label.endswith("_scan_probe"):
        return "scan_probe"
    if op:
        return f"operation:{op}"
    if label:
        return f"surface:{label}"
    return "default"


def _derive_required_contract_reason(
    *,
    required_contract: bool,
    operation: str,
    surface_label: str,
) -> str:
    if bool(required_contract):
        return "required_contract_detected"
    op = str(operation or "").strip().lower()
    label = str(surface_label or "").strip().lower()
    if op in {"scan", "inspection"} and label.endswith("_scan_probe"):
        return "scan_probe_optional_not_required"
    return "no_required_contract_detected"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run required gate bundle from mapping single-source registry.")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--identity-id", required=True)
    parser.add_argument("--operation", default="validate")
    parser.add_argument("--repo-catalog", default="")
    parser.add_argument("--contract-mapping", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--report-selected-path", default="")
    parser.add_argument("--send-time-gate-status", default="")
    parser.add_argument(
        "--outlet-bypass-detected",
        nargs="?",
        const="true",
        default="",
        help="explicit outlet bypass flag (true/false). bare flag implies true.",
    )
    parser.add_argument("--surface-label", default="")
    parser.add_argument("--target-name", default="", help="optional single target probe via bundle registry lineage")
    parser.add_argument("--out", default="", help="optional path to persist JSON receipt")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--actor-id", default="")
    parser.add_argument("--resolved-work-layer", default="")
    parser.add_argument("--resolved-source-layer", default="")
    parser.add_argument("--lock-state", default="")
    parser.add_argument("--final-emit-contract-status", default="")
    parser.add_argument("--final-emit-policy-mode", default="")
    parser.add_argument("--final-emit-schema-status", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    mapping_path = Path(args.contract_mapping).expanduser().resolve() if str(args.contract_mapping or "").strip() else _resolve_default_contract_mapping(repo_root)
    target_name = str(args.target_name or "").strip()
    requirement_keys = BUNDLE_REQUIREMENT_ORDER
    mapping_errors: list[str] = []
    if target_name:
        target_key = REQUIREMENT_BY_TARGET.get(target_name, "")
        if not target_key:
            mapping_errors.append(f"unknown_target_name:{target_name}")
            requirement_keys = ()
        else:
            requirement_keys = (target_key,)

    specs, spec_errors = _load_validator_specs(mapping_path, requirement_keys)
    mapping_errors.extend(spec_errors)
    result_rows: list[dict[str, Any]] = []
    failure_count = 0
    row_contract_error_count = 0
    surface_label = str(args.surface_label or "").strip() or str(args.operation or "").strip().replace("-", "_") or "unknown_surface"

    if mapping_errors:
        failure_count += len(mapping_errors)
    if not str(args.run_id or "").strip():
        mapping_errors.append("run_id_binding_missing")
        failure_count += 1

    for spec in specs:
        cmd = [
            sys.executable,
            spec.script_path,
            "--catalog",
            str(args.catalog),
            "--identity-id",
            str(args.identity_id),
            "--operation",
            str(args.operation),
            "--json-only",
        ]
        cmd.extend(spec.fixed_args)
        rc, out, err = _run(cmd)
        payload = _parse_payload(out)
        status_value, status_field = _classify_status(target_name=spec.target_name, rc=rc, payload=payload)
        payload_contract_issues = _validate_row_payload_contract(payload=payload, status_field=status_field)
        if rc != 0:
            payload_contract_issues.append("validator_rc_nonzero")
        if payload_contract_issues:
            status_value = STATUS_FAIL_REQUIRED
            row_contract_error_count += 1
        error_code = _extract_error_code(payload, err)
        if payload_contract_issues and not error_code:
            error_code = "IP-GATE-ENTRY-002"

        required_contract = bool(payload.get("required_contract", False))
        if status_value == STATUS_FAIL_REQUIRED:
            failure_count += 1
        elif status_value == STATUS_FAIL_OPTIONAL and required_contract:
            failure_count += 1

        result_rows.append(
            {
                "requirement_key": spec.requirement_key,
                "target_name": spec.target_name,
                "validator": spec.script_path,
                "fixed_args": list(spec.fixed_args),
                "validator_rc": rc,
                "status_field": status_field,
                "status": status_value,
                "error_code": error_code,
                "required_contract": required_contract,
                "auto_required_signal": bool(payload.get("auto_required_signal", False)),
                "surface_label": surface_label,
                "stale_reasons": list(payload.get("stale_reasons") or []),
                "evidence_ref": str(payload.get("evidence_ref", "")).strip(),
                "payload_contract_issues": payload_contract_issues,
                "payload": payload,
                "stderr_tail": (err.splitlines()[-1] if err else ""),
            }
        )

    missing_targets = [
        TARGET_NAME_BY_REQUIREMENT[key]
        for key in requirement_keys
        if TARGET_NAME_BY_REQUIREMENT.get(key) not in {row.get("target_name") for row in result_rows}
    ]
    if missing_targets:
        failure_count += len(missing_targets)

    run_id_binding = str(args.run_id or "").strip()
    report_selected_path = str(args.report_selected_path or "").strip()
    required_contract_any = any(bool(row.get("required_contract", False)) for row in result_rows)
    failed_required_contract_count = sum(
        1
        for row in result_rows
        if str(row.get("status", "")).upper() == STATUS_FAIL_REQUIRED
    )

    if mapping_errors or missing_targets or row_contract_error_count > 0:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-001"
    elif failed_required_contract_count > 0:
        bundle_status = STATUS_FAIL_REQUIRED
        error_code = "IP-GATE-ENTRY-002"
    else:
        bundle_status = STATUS_PASS_REQUIRED
        error_code = ""

    parity_operation_scope = _derive_parity_operation_scope(
        operation=str(args.operation or "").strip(),
        surface_label=surface_label,
    )
    required_contract_reason = _derive_required_contract_reason(
        required_contract=required_contract_any,
        operation=str(args.operation or "").strip(),
        surface_label=surface_label,
    )

    payload: dict[str, Any] = {
        "bundle_contract_id": BUNDLE_CONTRACT_ID,
        "bundle_key": BUNDLE_KEY,
        "bundle_status": bundle_status,
        "error_code": error_code,
        "identity_id": str(args.identity_id),
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "operation": str(args.operation),
        "contract_mapping": str(mapping_path),
        "mapping_errors": mapping_errors,
        "missing_targets": missing_targets,
        "results": result_rows,
        "surface_label": surface_label,
        "run_id_binding": run_id_binding,
        "report_selected_path": report_selected_path,
        "actor_id": str(args.actor_id or "").strip(),
        "resolved_work_layer": str(args.resolved_work_layer or "").strip(),
        "resolved_source_layer": str(args.resolved_source_layer or "").strip(),
        "lock_state": str(args.lock_state or "").strip(),
        "required_contract": required_contract_any,
        "required_contract_reason": required_contract_reason,
        "failed_required_contract_count": failed_required_contract_count,
        "parity_operation_scope": parity_operation_scope,
        "send_time_gate_status": str(args.send_time_gate_status or "").strip().upper(),
        "outlet_bypass_detected": _parse_bool_token(args.outlet_bypass_detected),
        "final_emit_contract_status": str(args.final_emit_contract_status or "").strip().upper(),
        "final_emit_policy_mode": str(args.final_emit_policy_mode or "").strip(),
        "final_emit_schema_status": str(args.final_emit_schema_status or "").strip().upper(),
        "row_contract_error_count": row_contract_error_count,
    }

    if target_name:
        target_row = next((row for row in result_rows if row.get("target_name") == target_name), None)
        if not target_row:
            target_status_field = STATUS_FIELD_BY_TARGET.get(target_name, "status")
            target_payload = {
                target_status_field: STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-ENTRY-001",
                "stale_reasons": ["bundle_target_missing"],
                "bundle_contract_id": BUNDLE_CONTRACT_ID,
                "bundle_key": BUNDLE_KEY,
                "bundle_target_name": target_name,
                "actor_id": str(args.actor_id or "").strip(),
                "resolved_work_layer": str(args.resolved_work_layer or "").strip(),
                "resolved_source_layer": str(args.resolved_source_layer or "").strip(),
                "lock_state": str(args.lock_state or "").strip(),
            }
            if args.json_only:
                print(json.dumps(target_payload, ensure_ascii=False))
            else:
                print(json.dumps(target_payload, ensure_ascii=False, indent=2))
            return 1

        target_payload = dict(
            target_row.get("payload") if isinstance(target_row.get("payload"), dict) else {}
        )
        target_status_field = STATUS_FIELD_BY_TARGET[target_name]
        target_payload.setdefault(target_status_field, target_row.get("status", STATUS_FAIL_REQUIRED))
        target_payload.setdefault("required_contract", bool(target_row.get("required_contract", False)))
        target_payload.setdefault("auto_required_signal", bool(target_row.get("auto_required_signal", False)))
        target_payload.setdefault("stale_reasons", list(target_row.get("stale_reasons") or []))
        target_payload.setdefault("evidence_ref", str(target_row.get("evidence_ref", "")))
        if not str(target_payload.get("error_code", "")).strip() and str(target_row.get("error_code", "")).strip():
            target_payload["error_code"] = target_row.get("error_code", "")
        target_payload.setdefault("bundle_contract_id", BUNDLE_CONTRACT_ID)
        target_payload.setdefault("bundle_key", BUNDLE_KEY)
        target_payload.setdefault("bundle_target_name", target_name)
        target_payload.setdefault("surface_label", surface_label)
        target_payload.setdefault("run_id_binding", run_id_binding)
        target_payload.setdefault("report_selected_path", report_selected_path)
        target_payload.setdefault("actor_id", str(args.actor_id or "").strip())
        target_payload.setdefault("resolved_work_layer", str(args.resolved_work_layer or "").strip())
        target_payload.setdefault("resolved_source_layer", str(args.resolved_source_layer or "").strip())
        target_payload.setdefault("lock_state", str(args.lock_state or "").strip())
        target_payload.setdefault("parity_operation_scope", parity_operation_scope)
        target_payload.setdefault(
            "required_contract_reason",
            _derive_required_contract_reason(
                required_contract=bool(target_payload.get("required_contract", False)),
                operation=str(args.operation or "").strip(),
                surface_label=surface_label,
            ),
        )
        target_payload.setdefault("send_time_gate_status", str(args.send_time_gate_status or "").strip().upper())
        target_payload.setdefault("outlet_bypass_detected", _parse_bool_token(args.outlet_bypass_detected))
        target_payload.setdefault("final_emit_contract_status", str(args.final_emit_contract_status or "").strip().upper())
        target_payload.setdefault("final_emit_policy_mode", str(args.final_emit_policy_mode or "").strip())
        target_payload.setdefault("final_emit_schema_status", str(args.final_emit_schema_status or "").strip().upper())
        if bundle_status == STATUS_FAIL_REQUIRED:
            target_payload[target_status_field] = STATUS_FAIL_REQUIRED
            if not str(target_payload.get("error_code", "")).strip():
                target_payload["error_code"] = error_code or "IP-GATE-ENTRY-001"
            stale = list(target_payload.get("stale_reasons") or [])
            if "bundle_entry_contract_failed" not in stale:
                stale.append("bundle_entry_contract_failed")
            target_payload["stale_reasons"] = stale
        if str(args.out or "").strip():
            _write_payload_out(str(args.out), target_payload)
        if args.json_only:
            print(json.dumps(target_payload, ensure_ascii=False))
        else:
            print(json.dumps(target_payload, ensure_ascii=False, indent=2))
        return 1 if str(target_payload.get(target_status_field, "")).upper() == STATUS_FAIL_REQUIRED else 0

    if str(args.out or "").strip():
        _write_payload_out(str(args.out), payload)
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[BUNDLE] {BUNDLE_KEY} status={bundle_status} failed_required_contract_count={failed_required_contract_count} "
            f"mapping_errors={len(mapping_errors)} missing_targets={len(missing_targets)}"
        )
        for row in result_rows:
            print(
                f"[BUNDLE] {row['target_name']}: status={row['status']} rc={row['validator_rc']} "
                f"required_contract={row['required_contract']} error_code={row['error_code'] or '-'}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if bundle_status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
