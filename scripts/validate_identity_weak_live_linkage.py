#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from identity_weak_live_linkage_common import (
    ALLOWED_VERDICT_CLASSES,
    PRIMARY_FALSE_GREEN_FAMILIES,
    SECONDARY_FALSE_GREEN_FAMILIES,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    WEAK_LIVE_LINKAGE_CONTRACT_ID,
    WEAK_LIVE_LINKAGE_VALIDATOR_ID,
    bool_to_status,
    clean_string,
    derive_operational_closure_class,
    overall_linkage_status_from_class,
    resolve_pack_task,
    resolve_weak_live_linkage_contract,
    weak_live_linkage_contract_issues,
)
from tool_vendor_governance_common import ACTIVE_EXECUTION_POINTER_REL, resolve_report_path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ERR_CONTRACT = "IP-WLL-001"
ERR_RUNTIME = "IP-WLL-002"

PROMPT_CONTRACT_KEYS: tuple[str, ...] = (
    "prompt_bootstrap_capability_contract_v1",
    "prompt_capability_matrix_fail_closed_contract_v1",
    "derived_prompt_conformance_contract_v1",
)
PROMPT_LIVE_BINDING_FIELDS: tuple[str, ...] = (
    "driver_receipt_refs",
    "driver_run_id",
    "driver_projection_digest",
    "current_run_driver_binding_status",
)
SAMPLE_CONTRACT_KEYS: tuple[str, ...] = (
    "capability_arbitration_contract",
    "experience_feedback_contract",
    "knowledge_acquisition_contract",
    "trigger_regression_contract",
)
SAMPLE_VALIDATOR_SPECS: tuple[tuple[str, str, str], ...] = (
    ("capability_arbitration", "scripts/validate_identity_capability_arbitration.py", "capability_arbitration_status"),
    ("experience_feedback", "scripts/validate_identity_experience_feedback.py", "experience_feedback_status"),
    ("knowledge_acquisition", "scripts/validate_identity_knowledge_acquisition.py", "knowledge_acquisition_status"),
    ("trigger_regression", "scripts/validate_identity_trigger_regression.py", "trigger_regression_status"),
)
SAMPLE_STRICT_PROJECTION_FIELDS: tuple[str, ...] = (
    "evidence_origin",
    "report_freshness_status",
    "run_id_binding_status",
    "strict_live_proof_status",
    "strict_live_operational_status",
    "operational_closure_class",
    "live_binding_strength",
    "next_hop_consumption_status",
    "report_selection_mode",
)
TRIO_CONTRACT_KEYS: tuple[str, ...] = (
    "tool_installation_contract",
    "vendor_api_discovery_contract",
    "vendor_api_solution_contract",
)
LOOP_ROUTE_FIELDS: tuple[str, ...] = (
    "selected_candidate_receipt_ref",
    "roundtable_receipt_ref",
    "route_live_binding_status",
)
LOOPBACK_FIELDS: tuple[str, ...] = (
    "operational_prompt_receipt_ref",
    "feedback_run_id",
    "preflight_reentry_receipt_ref",
    "loopback_live_binding_status",
)

def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = clean_string(raw)
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


def _run_json_validator(cmd: list[str], status_field: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    payload = _parse_json_payload(proc.stdout or "") or {}
    status = clean_string(payload.get(status_field)).upper()
    if not status:
        status = STATUS_PASS_REQUIRED if proc.returncode == 0 else STATUS_FAIL_REQUIRED
    return {
        "cmd": cmd,
        "rc": proc.returncode,
        "status": status,
        "payload": payload,
        "stdout_tail": (proc.stdout or "")[-400:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }


def _current_run_pointer(pack_root: Path) -> Path | None:
    pointer_path = (pack_root / ACTIVE_EXECUTION_POINTER_REL).resolve()
    if not pointer_path.exists():
        return None
    try:
        doc = json.loads(pointer_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(doc, dict):
        return None
    for key in ("report_path", "execution_report", "selected_report_path"):
        raw = clean_string(doc.get(key))
        if not raw:
            continue
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (pack_root / raw).resolve()
        else:
            p = p.resolve()
        if p.exists():
            return p
    return None


def _resolve_contract_paths(pack_root: Path, contract_doc: dict[str, Any]) -> list[Path]:
    rows: list[Path] = []
    report_pattern = clean_string(contract_doc.get("report_path_pattern"))
    sample_pattern = clean_string(contract_doc.get("sample_report_path_pattern"))
    feedback_pattern = clean_string(contract_doc.get("feedback_log_path_pattern"))
    for pattern in (report_pattern, sample_pattern, feedback_pattern):
        if not pattern:
            continue
        selected = resolve_report_path(report="", pattern=pattern, pack_root=pack_root)
        if selected is not None and selected.exists() and selected not in rows:
            rows.append(selected)
    for field in (
        "positive_rulebook_path",
        "negative_rulebook_path",
        "operational_prompt_ref_field",
    ):
        raw = clean_string(contract_doc.get(field))
        if not raw:
            continue
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (pack_root / raw).resolve()
        else:
            p = p.resolve()
        if p.exists() and p not in rows:
            rows.append(p)
    return rows


def _path_origin(path: Path, *, pack_root: Path, current_run_pointer: Path | None) -> str:
    try:
        if current_run_pointer is not None and path.resolve() == current_run_pointer.resolve():
            return "live"
    except Exception:
        pass
    text = path.as_posix()
    if "/runtime/examples/" in text:
        return "sample"
    if "/runtime/reports/" in text or "/runtime/logs/" in text:
        return "history"
    if path.name == "IDENTITY_PROMPT.md":
        return "prompt_presence"
    return "governed_artifact"


def _first_existing_contract(task_doc: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in keys:
        node = task_doc.get(key)
        if isinstance(node, dict):
            rows.append(node)
    return rows


def _all_fields_present(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    if not rows:
        return False
    for row in rows:
        if all(clean_string(row.get(field)) for field in fields):
            return True
    return False


def _family_result(
    *,
    family: str,
    applicable: bool,
    contract_status: str,
    artifact_status: str,
    run_binding_status: str,
    consumption_status: str,
    evidence_origin: str,
    reasons: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    closure_class = derive_operational_closure_class(
        contract_layer_status=contract_status,
        artifact_layer_status=artifact_status,
        run_binding_layer_status=run_binding_status,
        consumption_layer_status=consumption_status,
    )
    payload: dict[str, Any] = {
        "family": family,
        "applicable": bool(applicable),
        "contract_status": contract_status,
        "artifact_status": artifact_status,
        "run_binding_status": run_binding_status,
        "consumption_status": consumption_status,
        "closure_class": closure_class,
        "evidence_origin": evidence_origin,
        "reasons": reasons,
    }
    if extra:
        payload.update(extra)
    return payload


def _prompt_family(
    *,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    pack_root: Path,
    task_doc: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    prompt_path = (pack_root / "IDENTITY_PROMPT.md").resolve()
    contracts = _first_existing_contract(task_doc, PROMPT_CONTRACT_KEYS)
    applicable = bool(contracts or prompt_path.exists())
    prompt_bootstrap = _run_json_validator(
        [
            "python3",
            "scripts/validate_prompt_bootstrap_capability.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "prompt_bootstrap_contract_status",
    )
    prompt_matrix = _run_json_validator(
        [
            "python3",
            "scripts/validate_prompt_capability_matrix.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "prompt_capability_matrix_status",
    )
    prompt_derivation = _run_json_validator(
        [
            "python3",
            "scripts/validate_prompt_derivation_conformance.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "prompt_derivation_conformance_status",
    )
    if not applicable:
        return (
            _family_result(
                family="prompt_presence_only",
                applicable=False,
                contract_status=STATUS_SKIPPED_NOT_REQUIRED,
                artifact_status=STATUS_SKIPPED_NOT_REQUIRED,
                run_binding_status=STATUS_SKIPPED_NOT_REQUIRED,
                consumption_status=STATUS_SKIPPED_NOT_REQUIRED,
                evidence_origin="not_applicable",
                reasons=["prompt_family_not_required"],
            ),
            prompt_bootstrap,
            prompt_matrix,
            [prompt_derivation],
        )

    contract_status = STATUS_PASS_REQUIRED if contracts else STATUS_FAIL_REQUIRED
    artifact_status = STATUS_PASS_REQUIRED if prompt_path.exists() else STATUS_FAIL_REQUIRED
    prompt_payloads = [prompt_bootstrap.get("payload", {}), prompt_matrix.get("payload", {}), prompt_derivation.get("payload", {})]
    prompt_projection_present = all(
        isinstance(payload, dict) and all(field in payload for field in PROMPT_LIVE_BINDING_FIELDS)
        for payload in prompt_payloads
    )
    live_binding_present = prompt_projection_present and all(
        clean_string(payload.get("current_run_driver_binding_status")).upper() == STATUS_PASS_REQUIRED
        for payload in prompt_payloads
        if isinstance(payload, dict)
    )
    run_binding_status = STATUS_PASS_REQUIRED if live_binding_present else STATUS_FAIL_REQUIRED
    next_hop_absorbed = live_binding_present and all(
        clean_string(payload.get("requiredization_current_round_linked")).lower() in {"true", "1"}
        for payload in prompt_payloads
        if isinstance(payload, dict)
    )
    consumption_status = STATUS_PASS_REQUIRED if next_hop_absorbed else STATUS_FAIL_REQUIRED
    reasons: list[str] = []
    if artifact_status != STATUS_PASS_REQUIRED:
        reasons.append("identity_prompt_missing")
    if not prompt_projection_present:
        reasons.append("prompt_live_driver_projection_missing")
    elif run_binding_status != STATUS_PASS_REQUIRED:
        reasons.append("prompt_live_driver_binding_unproven")
    if any(row.get("status") == STATUS_PASS_REQUIRED for row in (prompt_bootstrap, prompt_matrix, prompt_derivation)) and run_binding_status != STATUS_PASS_REQUIRED:
        reasons.append("prompt_green_survives_without_live_driver_binding")
    evidence_origin = next(
        (
            clean_string(payload.get("evidence_origin"))
            for payload in prompt_payloads
            if isinstance(payload, dict) and clean_string(payload.get("evidence_origin"))
        ),
        "prompt_presence" if prompt_path.exists() else "missing",
    )
    return (
        _family_result(
            family="prompt_presence_only",
            applicable=True,
            contract_status=contract_status,
            artifact_status=artifact_status,
            run_binding_status=run_binding_status,
            consumption_status=consumption_status,
            evidence_origin=evidence_origin,
            reasons=reasons,
            extra={
                "prompt_path": str(prompt_path),
            },
        ),
        prompt_bootstrap,
        prompt_matrix,
        [prompt_derivation],
    )


def _sample_family(
    *,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    pack_root: Path,
    task_doc: dict[str, Any],
    current_run_pointer: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contracts = _first_existing_contract(task_doc, SAMPLE_CONTRACT_KEYS + TRIO_CONTRACT_KEYS)
    applicable = bool(contracts)
    sample_validator_rows: dict[str, Any] = {}
    for family_name, script_path, status_field in SAMPLE_VALIDATOR_SPECS:
        sample_validator_rows[family_name] = _run_json_validator(
            [
                "python3",
                script_path,
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--json-only",
            ],
            status_field,
        )
    if not applicable:
        return (
            _family_result(
                family="sample_report_only",
                applicable=False,
                contract_status=STATUS_SKIPPED_NOT_REQUIRED,
                artifact_status=STATUS_SKIPPED_NOT_REQUIRED,
                run_binding_status=STATUS_SKIPPED_NOT_REQUIRED,
                consumption_status=STATUS_SKIPPED_NOT_REQUIRED,
                evidence_origin="not_applicable",
                reasons=["sample_history_family_not_required"],
            ),
            sample_validator_rows,
        )

    selected_paths: list[Path] = []
    origins: list[str] = []
    for contract in contracts:
        for path in _resolve_contract_paths(pack_root, contract):
            if path not in selected_paths:
                selected_paths.append(path)
                origins.append(_path_origin(path, pack_root=pack_root, current_run_pointer=current_run_pointer))

    sample_payloads = [
        row.get("payload")
        for row in sample_validator_rows.values()
        if isinstance(row, dict) and isinstance(row.get("payload"), dict)
    ]
    for payload in sample_payloads:
        sample_path = clean_string(payload.get("selected_report_path"))
        if sample_path:
            p = Path(sample_path).expanduser().resolve()
            if p.exists() and p not in selected_paths:
                selected_paths.append(p)
                origins.append(clean_string(payload.get("evidence_origin")) or _path_origin(p, pack_root=pack_root, current_run_pointer=current_run_pointer))

    artifact_status = STATUS_PASS_REQUIRED if selected_paths or sample_payloads else STATUS_FAIL_REQUIRED
    history_or_sample = next(
        (origin for origin in origins if origin in {"sample", "history", "live"}),
        "missing",
    )
    live_binding_present = _all_fields_present(contracts, ("report_freshness_status", "run_id_binding_status", "strict_live_proof_status"))
    downstream_projection_present = all(
        all(clean_string(payload.get(field)) for field in SAMPLE_STRICT_PROJECTION_FIELDS)
        for payload in sample_payloads
    )
    downstream_all_live_proof = bool(sample_payloads) and all(
        clean_string(payload.get("strict_live_operational_status")).upper() == STATUS_PASS_REQUIRED
        for payload in sample_payloads
    )
    run_binding_status = (
        STATUS_PASS_REQUIRED
        if downstream_all_live_proof or (live_binding_present and origins and all(origin == "live" for origin in origins))
        else STATUS_FAIL_REQUIRED
    )
    downstream_next_hop_absorbed = bool(sample_payloads) and all(
        clean_string(payload.get("next_hop_consumption_status")).upper() == STATUS_PASS_REQUIRED
        for payload in sample_payloads
    )
    consumption_status = (
        STATUS_PASS_REQUIRED
        if downstream_projection_present and (downstream_next_hop_absorbed or run_binding_status == STATUS_PASS_REQUIRED)
        else STATUS_FAIL_REQUIRED
    )
    reasons: list[str] = []
    if artifact_status != STATUS_PASS_REQUIRED:
        reasons.append("sample_or_history_artifact_missing")
    if any(origin in {"sample", "history"} for origin in origins):
        reasons.append("sample_or_history_artifact_selected_on_strict_lane")
    if run_binding_status != STATUS_PASS_REQUIRED:
        reasons.append("sample_or_history_live_run_binding_unproven")
    if not downstream_projection_present:
        reasons.append("downstream_sample_validator_projection_missing")
    for family_name, row in sample_validator_rows.items():
        payload = row.get("payload") if isinstance(row, dict) and isinstance(row.get("payload"), dict) else {}
        if clean_string(payload.get("strict_live_operational_status")).upper() != STATUS_PASS_REQUIRED:
            reasons.append(f"{family_name}_strict_live_operational_status_unproven")
    return (
        _family_result(
            family="sample_report_only",
            applicable=True,
            contract_status=STATUS_PASS_REQUIRED,
            artifact_status=artifact_status,
            run_binding_status=run_binding_status,
            consumption_status=consumption_status,
            evidence_origin=history_or_sample,
            reasons=sorted(set(reasons)),
            extra={
                "selected_paths": [str(path) for path in selected_paths],
                "downstream_projection_present": downstream_projection_present,
            },
        ),
        sample_validator_rows,
    )


def _loop_family(
    *,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    task_doc: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    arbitration = task_doc.get("capability_arbitration_contract") if isinstance(task_doc.get("capability_arbitration_contract"), dict) else {}
    route_enforcement = arbitration.get("route_discovery_enforcement") if isinstance(arbitration, dict) else {}
    feedback_enforcement = arbitration.get("feedback_operational_prompt_enforcement") if isinstance(arbitration, dict) else {}
    applicable = isinstance(route_enforcement, dict) or isinstance(feedback_enforcement, dict)
    routing = _run_json_validator(
        [
            "python3",
            "scripts/validate_identity_routing_learning_strengthening.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "routing_learning_strengthening_status",
    )
    loopback = _run_json_validator(
        [
            "python3",
            "scripts/validate_feedback_to_judgement_loopback.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "feedback_to_judgement_loopback_status",
    )
    roundtable = _run_json_validator(
        [
            "python3",
            "scripts/validate_capability_fit_roundtable_evidence.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--operation",
            operation,
            "--json-only",
        ],
        "capability_fit_roundtable_status",
    )
    if not applicable:
        return (
            _family_result(
                family="loop_meta_only",
                applicable=False,
                contract_status=STATUS_SKIPPED_NOT_REQUIRED,
                artifact_status=STATUS_SKIPPED_NOT_REQUIRED,
                run_binding_status=STATUS_SKIPPED_NOT_REQUIRED,
                consumption_status=STATUS_SKIPPED_NOT_REQUIRED,
                evidence_origin="not_applicable",
                reasons=["loop_family_not_required"],
            ),
            routing,
            loopback,
            roundtable,
        )
    routing_payload = routing.get("payload", {})
    loopback_payload = loopback.get("payload", {})
    selected_candidate_id = clean_string(routing_payload.get("selected_candidate_id"))
    selection_basis = clean_string(routing_payload.get("selection_basis"))
    placeholder_projection = selected_candidate_id == "selected_candidate_id" or selection_basis == "selection_basis"
    semantic_center_status = (
        STATUS_PASS_REQUIRED
        if routing.get("status") == STATUS_PASS_REQUIRED and loopback.get("status") == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    roundtable_alignment_status = (
        clean_string(routing_payload.get("capability_fit_roundtable_status")).upper()
        or clean_string(roundtable.get("status")).upper()
        or STATUS_SKIPPED_NOT_REQUIRED
    )
    route_live_binding_status = clean_string(routing_payload.get("route_live_binding_status")).upper() or STATUS_FAIL_REQUIRED
    loopback_live_binding_status = clean_string(loopback_payload.get("loopback_live_binding_status")).upper() or STATUS_FAIL_REQUIRED
    live_bridge_status = (
        STATUS_PASS_REQUIRED
        if route_live_binding_status == STATUS_PASS_REQUIRED and loopback_live_binding_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    reasons: list[str] = []
    if placeholder_projection:
        reasons.append("route_projection_reuses_field_name_placeholders")
    if roundtable_alignment_status == STATUS_FAIL_REQUIRED:
        reasons.append("roundtable_live_evidence_not_consumed")
    reasons.extend(
        clean_string(reason)
        for reason in (routing_payload.get("route_live_binding_reasons") or [])
        if clean_string(reason)
    )
    reasons.extend(
        clean_string(reason)
        for reason in (loopback_payload.get("loopback_live_binding_reasons") or [])
        if clean_string(reason)
    )
    if semantic_center_status == STATUS_PASS_REQUIRED and live_bridge_status != STATUS_PASS_REQUIRED:
        reasons.append("semantic_center_green_without_live_bridge_consumption")
    return (
        _family_result(
            family="loop_meta_only",
            applicable=True,
            contract_status=STATUS_PASS_REQUIRED,
            artifact_status=semantic_center_status,
            run_binding_status=live_bridge_status,
            consumption_status=STATUS_FAIL_REQUIRED if live_bridge_status != STATUS_PASS_REQUIRED else STATUS_PASS_REQUIRED,
            evidence_origin="loop_meta",
            reasons=reasons,
            extra={
                "semantic_center_status": semantic_center_status,
                "live_bridge_status": live_bridge_status,
                "roundtable_alignment_status": roundtable_alignment_status,
                "selected_candidate_id": selected_candidate_id,
                "selection_basis": selection_basis,
                "selected_candidate_receipt_ref": clean_string(routing_payload.get("selected_candidate_receipt_ref")),
                "roundtable_receipt_ref": clean_string(routing_payload.get("roundtable_receipt_ref")),
                "route_live_binding_status": route_live_binding_status,
                "operational_prompt_receipt_ref": clean_string(loopback_payload.get("operational_prompt_receipt_ref")),
                "feedback_run_id": clean_string(loopback_payload.get("feedback_run_id")),
                "preflight_reentry_receipt_ref": clean_string(loopback_payload.get("preflight_reentry_receipt_ref")),
                "loopback_live_binding_status": loopback_live_binding_status,
            },
        ),
        routing,
        loopback,
        roundtable,
    )


def _latest_log_family(
    *,
    catalog_path: Path,
    identity_id: str,
    operation: str,
    pack_root: Path,
    task_doc: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    feedback_contract = task_doc.get("experience_feedback_contract")
    if not isinstance(feedback_contract, dict):
        return (
            _family_result(
                family="latest_log_no_run_binding",
                applicable=False,
                contract_status=STATUS_SKIPPED_NOT_REQUIRED,
                artifact_status=STATUS_SKIPPED_NOT_REQUIRED,
                run_binding_status=STATUS_SKIPPED_NOT_REQUIRED,
                consumption_status=STATUS_SKIPPED_NOT_REQUIRED,
                evidence_origin="not_applicable",
                reasons=["experience_feedback_contract_missing"],
            ),
            {},
        )

    governance = _run_json_validator(
        [
            "python3",
            "scripts/validate_identity_experience_feedback_governance.py",
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--report",
            "",
            "--json-only",
        ],
        "experience_feedback_governance_status",
    )
    governance_payload = governance.get("payload", {}) if isinstance(governance.get("payload"), dict) else {}
    latest_feedback_log = clean_string(governance_payload.get("latest_feedback_log"))
    artifact_status = STATUS_PASS_REQUIRED if latest_feedback_log else STATUS_FAIL_REQUIRED
    freshness_status = clean_string(governance_payload.get("report_freshness_status")).upper() or STATUS_FAIL_REQUIRED
    latest_feedback_run_id_match_status = (
        clean_string(governance_payload.get("latest_feedback_run_id_match_status")).upper() or STATUS_FAIL_REQUIRED
    )
    operational_prompt_run_join_status = (
        clean_string(governance_payload.get("operational_prompt_run_join_status")).upper() or STATUS_FAIL_REQUIRED
    )
    run_binding_status = (
        STATUS_PASS_REQUIRED
        if freshness_status == STATUS_PASS_REQUIRED
        and latest_feedback_run_id_match_status == STATUS_PASS_REQUIRED
        and operational_prompt_run_join_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    reasons: list[str] = []
    if artifact_status != STATUS_PASS_REQUIRED:
        reasons.append("latest_feedback_log_missing")
    if freshness_status != STATUS_PASS_REQUIRED:
        reasons.append("latest_feedback_log_not_fresh_enough")
    if latest_feedback_run_id_match_status != STATUS_PASS_REQUIRED:
        reasons.append("latest_feedback_run_id_not_matched_to_current_run")
    if operational_prompt_run_join_status != STATUS_PASS_REQUIRED:
        reasons.append("operational_prompt_not_joined_to_current_run")
    reasons.extend(
        clean_string(reason)
        for reason in (governance_payload.get("stale_reasons") or [])
        if clean_string(reason)
    )
    return (
        _family_result(
            family="latest_log_no_run_binding",
            applicable=True,
            contract_status=STATUS_PASS_REQUIRED,
            artifact_status=artifact_status,
            run_binding_status=run_binding_status,
            consumption_status=STATUS_FAIL_REQUIRED if run_binding_status != STATUS_PASS_REQUIRED else STATUS_PASS_REQUIRED,
            evidence_origin=clean_string(governance_payload.get("evidence_origin")) or ("live_log" if latest_feedback_log else "missing"),
            reasons=sorted(set(reasons)),
            extra={
                "latest_feedback_log": latest_feedback_log,
                "latest_feedback_log_age_days": governance_payload.get("latest_feedback_log_age_days"),
                "report_freshness_status": freshness_status,
                "required_run_id": clean_string(governance_payload.get("required_run_id")),
                "latest_feedback_run_id_match_status": latest_feedback_run_id_match_status,
                "operational_prompt_run_join_status": operational_prompt_run_join_status,
                "operational_prompt_receipt_ref": clean_string(governance_payload.get("operational_prompt_receipt_ref")),
                "feedback_run_id": clean_string(governance_payload.get("feedback_run_id")),
                "preflight_reentry_receipt_ref": clean_string(governance_payload.get("preflight_reentry_receipt_ref")),
                "loopback_live_binding_status": clean_string(governance_payload.get("loopback_live_binding_status")).upper()
                or STATUS_FAIL_REQUIRED,
            },
        ),
        governance,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the v1.6.19 weak-live-linkage differential-audit contract.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = clean_string(args.catalog)
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None
    try:
        pack_root, task_path, task_doc = resolve_pack_task(
            catalog_path=catalog_path,
            current_task=clean_string(args.current_task),
            identity_id=args.identity_id,
        )
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "operation": args.operation,
            "identity_weak_live_linkage_status": STATUS_FAIL_REQUIRED,
            "weak_live_linkage_contract_status": STATUS_FAIL_REQUIRED,
            "contract_layer_status": STATUS_FAIL_REQUIRED,
            "artifact_layer_status": STATUS_FAIL_REQUIRED,
            "run_binding_layer_status": STATUS_FAIL_REQUIRED,
            "consumption_layer_status": STATUS_FAIL_REQUIRED,
            "overall_linkage_status": STATUS_FAIL_REQUIRED,
            "operational_closure_class": "structure_green",
            "false_green_family": "",
            "evidence_origin": "missing",
            "live_binding_strength": "absent",
            "next_hop_consumption_status": STATUS_FAIL_REQUIRED,
            "semantic_center_status": STATUS_FAIL_REQUIRED,
            "live_bridge_status": STATUS_FAIL_REQUIRED,
            "roundtable_alignment_status": STATUS_FAIL_REQUIRED,
            "philosophy_truth_lifecycle_status": STATUS_FAIL_REQUIRED,
            "stale_reasons": [f"runtime_resolution_failed:{exc}"],
            "error_code": ERR_RUNTIME,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    required, contract_doc, contract_key = resolve_weak_live_linkage_contract(task_doc)
    contract_issues = weak_live_linkage_contract_issues(contract_doc if isinstance(contract_doc, dict) else {}) if required else ["required_contract_disabled_or_missing"]
    philosophy_truth_lifecycle_status = STATUS_PASS_REQUIRED if required and not any(issue.endswith("mismatch") and issue.startswith("truth_") for issue in contract_issues) and "philosophy_anchor_refs_mismatch" not in contract_issues else STATUS_FAIL_REQUIRED
    contract_status = STATUS_PASS_REQUIRED if required and not contract_issues else STATUS_FAIL_REQUIRED
    current_run_pointer = _current_run_pointer(pack_root)

    prompt_family, prompt_bootstrap, prompt_matrix, prompt_derivation_rows = _prompt_family(
        catalog_path=catalog_path or Path(""),
        identity_id=args.identity_id,
        operation=args.operation,
        pack_root=pack_root,
        task_doc=task_doc,
    )
    sample_family, sample_validator_rows = _sample_family(
        catalog_path=catalog_path or Path(""),
        identity_id=args.identity_id,
        operation=args.operation,
        pack_root=pack_root,
        task_doc=task_doc,
        current_run_pointer=current_run_pointer,
    )
    loop_family, routing_validator, loopback_validator, roundtable_validator = _loop_family(
        catalog_path=catalog_path or Path(""),
        identity_id=args.identity_id,
        operation=args.operation,
        task_doc=task_doc,
    )
    latest_log_family, experience_feedback_governance = _latest_log_family(
        catalog_path=catalog_path or Path(""),
        identity_id=args.identity_id,
        operation=args.operation,
        pack_root=pack_root,
        task_doc=task_doc,
    )

    family_rows = [prompt_family, sample_family, loop_family, latest_log_family]
    applicable_rows = [row for row in family_rows if bool(row.get("applicable"))]
    detected_primary = [
        row["family"]
        for row in applicable_rows
        if row["family"] in PRIMARY_FALSE_GREEN_FAMILIES
        and clean_string(row.get("run_binding_status")).upper() != STATUS_PASS_REQUIRED
        and clean_string(row.get("artifact_status")).upper() == STATUS_PASS_REQUIRED
    ]
    detected_secondary = [
        row["family"]
        for row in applicable_rows
        if row["family"] in SECONDARY_FALSE_GREEN_FAMILIES
        and clean_string(row.get("run_binding_status")).upper() != STATUS_PASS_REQUIRED
        and clean_string(row.get("artifact_status")).upper() == STATUS_PASS_REQUIRED
    ]
    false_green_family = (detected_primary + detected_secondary + [""])[0]

    artifact_any = any(clean_string(row.get("artifact_status")).upper() == STATUS_PASS_REQUIRED for row in applicable_rows)
    binding_any = any(clean_string(row.get("run_binding_status")).upper() == STATUS_PASS_REQUIRED for row in applicable_rows)
    consumption_any = any(clean_string(row.get("consumption_status")).upper() == STATUS_PASS_REQUIRED for row in applicable_rows)

    contract_layer_status = contract_status
    artifact_layer_status = STATUS_PASS_REQUIRED if contract_status == STATUS_PASS_REQUIRED and artifact_any else STATUS_FAIL_REQUIRED
    run_binding_layer_status = STATUS_PASS_REQUIRED if contract_status == STATUS_PASS_REQUIRED and binding_any and not false_green_family else STATUS_FAIL_REQUIRED
    consumption_layer_status = STATUS_PASS_REQUIRED if contract_status == STATUS_PASS_REQUIRED and consumption_any and not false_green_family else STATUS_FAIL_REQUIRED
    operational_closure_class = derive_operational_closure_class(
        contract_layer_status=contract_layer_status,
        artifact_layer_status=artifact_layer_status,
        run_binding_layer_status=run_binding_layer_status,
        consumption_layer_status=consumption_layer_status,
    )
    if operational_closure_class not in ALLOWED_VERDICT_CLASSES:
        operational_closure_class = "structure_green"
    overall_linkage_status = overall_linkage_status_from_class(operational_closure_class)
    evidence_origin = next((clean_string(row.get("evidence_origin")) for row in applicable_rows if clean_string(row.get("evidence_origin")) and clean_string(row.get("evidence_origin")) != "missing"), "missing")
    live_binding_strength = (
        "strong"
        if run_binding_layer_status == STATUS_PASS_REQUIRED and consumption_layer_status == STATUS_PASS_REQUIRED
        else ("weak" if artifact_layer_status == STATUS_PASS_REQUIRED else "absent")
    )
    next_hop_consumption_status = consumption_layer_status
    semantic_center_status = clean_string(loop_family.get("semantic_center_status")).upper() or STATUS_SKIPPED_NOT_REQUIRED
    live_bridge_status = clean_string(loop_family.get("live_bridge_status")).upper() or STATUS_SKIPPED_NOT_REQUIRED
    roundtable_alignment_status = clean_string(loop_family.get("roundtable_alignment_status")).upper() or STATUS_SKIPPED_NOT_REQUIRED

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "contract_key": contract_key,
        "contract_id": clean_string(contract_doc.get("contract_id")) if isinstance(contract_doc, dict) else "",
        "validator": clean_string(contract_doc.get("validator")) if isinstance(contract_doc, dict) else "",
        "probe_runner": clean_string(contract_doc.get("probe_runner")) if isinstance(contract_doc, dict) else "",
        "identity_weak_live_linkage_status": contract_status,
        "weak_live_linkage_contract_status": contract_status,
        "contract_layer_status": contract_layer_status,
        "artifact_layer_status": artifact_layer_status,
        "run_binding_layer_status": run_binding_layer_status,
        "consumption_layer_status": consumption_layer_status,
        "overall_linkage_status": overall_linkage_status,
        "operational_closure_class": operational_closure_class,
        "false_green_family": false_green_family,
        "evidence_origin": evidence_origin,
        "live_binding_strength": live_binding_strength,
        "next_hop_consumption_status": next_hop_consumption_status,
        "semantic_center_status": semantic_center_status,
        "live_bridge_status": live_bridge_status,
        "roundtable_alignment_status": roundtable_alignment_status,
        "selected_candidate_receipt_ref": clean_string(loop_family.get("selected_candidate_receipt_ref")),
        "roundtable_receipt_ref": clean_string(loop_family.get("roundtable_receipt_ref")),
        "route_live_binding_status": clean_string(loop_family.get("route_live_binding_status")).upper(),
        "operational_prompt_receipt_ref": clean_string(loop_family.get("operational_prompt_receipt_ref")),
        "feedback_run_id": clean_string(loop_family.get("feedback_run_id")),
        "preflight_reentry_receipt_ref": clean_string(loop_family.get("preflight_reentry_receipt_ref")),
        "loopback_live_binding_status": clean_string(loop_family.get("loopback_live_binding_status")).upper(),
        "required_run_id": clean_string(latest_log_family.get("required_run_id")),
        "latest_feedback_run_id_match_status": clean_string(
            latest_log_family.get("latest_feedback_run_id_match_status")
        ).upper(),
        "operational_prompt_run_join_status": clean_string(
            latest_log_family.get("operational_prompt_run_join_status")
        ).upper(),
        "philosophy_truth_lifecycle_status": philosophy_truth_lifecycle_status,
        "current_run_pointer": str(current_run_pointer) if current_run_pointer else "",
        "contract_issues": contract_issues,
        "family_rows": family_rows,
        "component_validator_rows": {
            "prompt_bootstrap": prompt_bootstrap,
            "prompt_capability_matrix": prompt_matrix,
            "prompt_derivation_conformance": prompt_derivation_rows[0] if prompt_derivation_rows else {},
            "sample_family_consumers": sample_validator_rows,
            "routing_learning_strengthening": routing_validator,
            "feedback_to_judgement_loopback": loopback_validator,
            "capability_fit_roundtable_evidence": roundtable_validator,
            "experience_feedback_governance": experience_feedback_governance,
        },
        "stale_reasons": contract_issues
        + [
            f"weak_live_linkage_detected:{family}"
            for family in detected_primary + detected_secondary
        ],
        "error_code": "" if contract_status == STATUS_PASS_REQUIRED else ERR_CONTRACT,
        "kernel_contract_id": WEAK_LIVE_LINKAGE_CONTRACT_ID,
        "validator_id": WEAK_LIVE_LINKAGE_VALIDATOR_ID,
    }

    _emit(payload, json_only=args.json_only)
    return 0 if contract_status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
