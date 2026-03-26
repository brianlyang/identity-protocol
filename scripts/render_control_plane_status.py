#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from reference_visual_atlas_governance_common import (
    load_reference_visual_atlas_registry,
    reference_visual_atlas_control_plane_checks,
)
from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_PASS_WITH_BLOCKERS = "PASS_WITH_BLOCKERS"

STATUS_ARTIFACT_PAYLOAD_DROP_TOKENS = (
    "forbidden_default_literals",
    "forbidden_default_hits",
)
DEFAULT_STATUS_ENTRY = "identity/protocol/mappings/control-plane-status.current.yaml"


@dataclass(frozen=True)
class CheckSpec:
    name: str
    command: tuple[str, ...]
    status_key: str | None


BASE_CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec(
        name="control_plane_budget",
        command=("python3", "scripts/validate_control_plane_budget.py", "--json-only"),
        status_key="control_plane_budget_status",
    ),
    CheckSpec(
        name="control_plane_budget_sync",
        command=("python3", "scripts/validate_control_plane_budget_sync.py", "--json-only"),
        status_key="control_plane_budget_sync_status",
    ),
    CheckSpec(
        name="control_plane_invariants",
        command=("python3", "scripts/validate_control_plane_invariants.py", "--json-only"),
        status_key="control_plane_invariants_status",
    ),
    CheckSpec(
        name="contract_binding_reference_integrity",
        command=("python3", "scripts/validate_contract_binding_reference_integrity.py", "--json-only"),
        status_key="contract_binding_reference_integrity_status",
    ),
    CheckSpec(
        name="layer_targeted_gate_profile",
        command=("python3", "scripts/validate_layer_targeted_gate_profile.py", "--json-only"),
        status_key="layer_targeted_gate_profile_status",
    ),
    CheckSpec(
        name="required_gate_surface_drift",
        command=("python3", "scripts/validate_required_gate_surface_drift.py", "--json-only"),
        status_key="required_gate_surface_drift_status",
    ),
    CheckSpec(
        name="executable_surface_runtime_literal_lock",
        command=("python3", "scripts/validate_executable_surface_runtime_literal_lock.py", "--json-only"),
        status_key="executable_surface_runtime_literal_lock_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_governance",
        command=("python3", "scripts/validate_protocol_root_corpus_governance.py", "--json-only"),
        status_key="protocol_root_corpus_governance_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_ordering",
        command=("python3", "scripts/validate_protocol_root_corpus_ordering.py", "--json-only"),
        status_key="protocol_root_corpus_ordering_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_authority",
        command=("python3", "scripts/validate_protocol_root_corpus_authority.py", "--json-only"),
        status_key="protocol_root_corpus_authority_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_derivation",
        command=("python3", "scripts/validate_protocol_root_corpus_derivation.py", "--json-only"),
        status_key="protocol_root_corpus_derivation_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_transition",
        command=("python3", "scripts/validate_protocol_root_corpus_transition.py", "--json-only"),
        status_key="protocol_root_corpus_transition_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_gateway_admissibility",
        command=("python3", "scripts/validate_protocol_root_corpus_gateway_admissibility.py", "--json-only"),
        status_key="protocol_root_corpus_gateway_admissibility_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_precedence",
        command=("python3", "scripts/validate_protocol_root_corpus_precedence.py", "--json-only"),
        status_key="protocol_root_corpus_precedence_status",
    ),
    CheckSpec(
        name="protocol_root_corpus_question_routing",
        command=("python3", "scripts/validate_protocol_root_corpus_question_routing.py", "--json-only"),
        status_key="protocol_root_corpus_question_routing_status",
    ),
    CheckSpec(
        name="protocol_broadcast_doc_control",
        command=("python3", "scripts/validate_protocol_broadcast_doc_control.py", "--json-only"),
        status_key="protocol_broadcast_doc_control_status",
    ),
    CheckSpec(
        name="protocol_governed_subdomain_doc_control_registry",
        command=("python3", "scripts/validate_protocol_governed_subdomain_doc_control_registry.py", "--json-only"),
        status_key="protocol_governed_subdomain_doc_control_registry_status",
    ),
    CheckSpec(
        name="release_doc_surface_governance",
        command=("python3", "scripts/validate_release_doc_surface_governance.py", "--json-only"),
        status_key="release_doc_surface_governance_status",
    ),
    CheckSpec(
        name="v16x_release_closure_boundary",
        command=("python3", "scripts/validate_v16x_release_closure_boundary.py", "--json-only"),
        status_key="v16x_release_closure_boundary_status",
    ),
    CheckSpec(
        name="v16x_release_closure_summary",
        command=("python3", "scripts/validate_v16x_release_closure_summary.py", "--json-only"),
        status_key="v16x_release_closure_summary_status",
    ),
    CheckSpec(
        name="doc_command_surface_registry",
        command=("python3", "scripts/validate_doc_command_surface_registry.py", "--json-only"),
        status_key="doc_command_surface_registry_status",
    ),
    CheckSpec(
        name="docs_command_contract",
        command=("python3", "scripts/docs_command_contract_check.py"),
        status_key=None,
    ),
    CheckSpec(
        name="protocol_ssot_source",
        command=("python3", "scripts/validate_protocol_ssot_source.py"),
        status_key=None,
    ),
    CheckSpec(
        name="reference_visual_atlas_inventory",
        command=("python3", "scripts/validate_reference_visual_atlas_inventory.py", "--json-only"),
        status_key="reference_visual_atlas_inventory_status",
    ),
)


def _atlas_check_specs(repo_root: Path) -> tuple[CheckSpec, ...]:
    registry_doc, _registry_entry, _registry_active, _registry_alias_error = load_reference_visual_atlas_registry(
        repo_root
    )
    checks: list[CheckSpec] = []
    for row in reference_visual_atlas_control_plane_checks(registry_doc):
        validator_script = str(row.get("validator_script") or "").strip()
        status_key = str(row.get("status_key") or "").strip() or None
        name = str(row.get("name") or "").strip()
        if not validator_script or not name:
            continue
        checks.append(
            CheckSpec(
                name=name,
                command=("python3", validator_script, "--json-only"),
                status_key=status_key,
            )
        )
    return tuple(checks)


def _ordered_specs(repo_root: Path) -> tuple[CheckSpec, ...]:
    return (*BASE_CHECKS[:-1], *_atlas_check_specs(repo_root), BASE_CHECKS[-1])


def _select_specs(
    repo_root: Path,
    *,
    include_check_names: tuple[str, ...] = (),
) -> tuple[CheckSpec, ...]:
    ordered_specs = _ordered_specs(repo_root)
    if not include_check_names:
        return ordered_specs
    available_names = {spec.name for spec in ordered_specs}
    missing = [name for name in include_check_names if name not in available_names]
    if missing:
        raise ValueError(f"unknown_control_plane_check_names:{','.join(sorted(set(missing)))}")
    include_set = set(include_check_names)
    return tuple(spec for spec in ordered_specs if spec.name in include_set)


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_json_blob(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        obj = json.loads(raw[start : end + 1])
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _sanitize_status_artifact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, node in value.items():
            key_str = str(key)
            lowered = key_str.strip().lower()
            if any(token in lowered for token in STATUS_ARTIFACT_PAYLOAD_DROP_TOKENS):
                continue
            sanitized[key_str] = _sanitize_status_artifact_payload(node)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_status_artifact_payload(item) for item in value]
    return value


def _git_head_short(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _run_check(spec: CheckSpec, repo_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        list(spec.command),
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        check=False,
    )
    payload = _extract_json_blob(proc.stdout)
    status = ""
    error_code = ""
    if spec.status_key:
        status = str(payload.get(spec.status_key, "")).strip()
        error_code = str(payload.get("error_code", "")).strip()
    else:
        status = STATUS_PASS_REQUIRED if proc.returncode == 0 else STATUS_FAIL_REQUIRED
    if not status:
        status = STATUS_PASS_REQUIRED if proc.returncode == 0 else STATUS_FAIL_REQUIRED
    return {
        "name": spec.name,
        "command": list(spec.command),
        "rc": int(proc.returncode),
        "status": status,
        "error_code": error_code,
        "stdout_tail": [],
        "stderr_tail": [],
        "payload": _sanitize_status_artifact_payload(payload),
    }


def _derive_overall_status(checks: list[dict[str, Any]]) -> tuple[str, bool, list[str]]:
    statuses = [str(item.get("status", "")).strip() for item in checks]
    reasons: list[str] = []
    if any(s == STATUS_FAIL_REQUIRED for s in statuses):
        for item in checks:
            if item.get("status") == STATUS_FAIL_REQUIRED:
                reasons.append(f"{item.get('name')}:FAIL_REQUIRED")
        return STATUS_FAIL_REQUIRED, False, reasons
    if any(s == STATUS_WARN_NON_BLOCKING for s in statuses):
        for item in checks:
            if item.get("status") == STATUS_WARN_NON_BLOCKING:
                reasons.append(f"{item.get('name')}:WARN_NON_BLOCKING")
        return STATUS_PASS_WITH_BLOCKERS, False, reasons
    return STATUS_PASS_REQUIRED, True, reasons


def build_status(
    repo_root: Path,
    *,
    include_check_names: tuple[str, ...] = (),
) -> dict[str, Any]:
    ordered_specs = _select_specs(repo_root, include_check_names=include_check_names)
    checks = [_run_check(spec, repo_root) for spec in ordered_specs]
    overall_status, promotion_ready, reasons = _derive_overall_status(checks)
    status = {
        "schema_version": 1,
        "status_version": "v1.6",
        "generated_at_utc": _utc_now(),
        "git_head_short": _git_head_short(repo_root),
        "machine_promotion_policy": {
            "promotion_ready_requires": [STATUS_PASS_REQUIRED],
            "blocked_by": [STATUS_FAIL_REQUIRED, STATUS_PASS_WITH_BLOCKERS],
            "warnings_non_promotional": [STATUS_WARN_NON_BLOCKING],
        },
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "fail_count": sum(1 for c in checks if c.get("status") == STATUS_FAIL_REQUIRED),
            "warn_count": sum(1 for c in checks if c.get("status") == STATUS_WARN_NON_BLOCKING),
            "pass_count": sum(1 for c in checks if c.get("status") == STATUS_PASS_REQUIRED),
        },
        "surface_governance": build_governed_runtime_summary_surface_payload("control_plane_status_artifact"),
        "control_plane_status": overall_status,
        "promotion_ready": promotion_ready,
        "promotion_block_reasons": reasons,
        "selected_check_names": list(include_check_names),
    }
    return status


def resolve_status_target(
    repo_root: Path,
    *,
    status_file: str = DEFAULT_STATUS_ENTRY,
) -> tuple[Path, str, str]:
    return _resolve_current_yaml_alias(repo_root, str(status_file))


def persist_status_payload(status_file: Path, payload: dict[str, Any]) -> Path:
    target = Path(status_file).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Render machine-generated control-plane status artifact.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument(
        "--status-file",
        default=DEFAULT_STATUS_ENTRY,
    )
    parser.add_argument("--check-name", action="append", default=[])
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    status_entry_file = (repo_root / str(args.status_file)).resolve()
    status_file, status_active_file, status_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.status_file)
    )
    if not status_entry_file.exists():
        print(f"[FAIL] control-plane status entry missing: {status_entry_file}")
        return 1
    if status_alias_error:
        print(f"[FAIL] control-plane status alias resolution failed: {status_alias_error} ({status_active_file})")
        return 1
    try:
        payload = build_status(
            repo_root,
            include_check_names=tuple(str(name).strip() for name in (args.check_name or []) if str(name).strip()),
        )
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 1
    payload["status_file_entry"] = str(status_entry_file)
    payload["status_file"] = str(status_file)
    payload["status_file_active_file"] = status_active_file
    payload["status_file_alias_error"] = status_alias_error

    if args.write:
        persist_status_payload(status_file, payload)

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-STATUS] status={payload.get('control_plane_status')} "
            f"promotion_ready={payload.get('promotion_ready')} "
            f"fails={payload.get('summary', {}).get('fail_count', 0)} "
            f"warns={payload.get('summary', {}).get('warn_count', 0)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("control_plane_status") != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
