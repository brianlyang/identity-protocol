#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import (
    contract_required,
    latest_identity_upgrade_report,
    load_json,
    resolve_pack_and_task,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REGISTRY = "IP-RL-REG-001"
ERR_CONFIG = "IP-RL-CONF-001"
ERR_RUNTIME_MISSING = "IP-RL-RUN-001"
ERR_ATTEMPT_FIELDS = "IP-RL-RUN-002"
ERR_NO_TARGET_DONE = "IP-RL-RUN-003"
ERR_NEXT_ACTION = "IP-RL-RUN-004"
ERR_ESCALATION = "IP-RL-RUN-005"
ERR_RUN_ID_MISMATCH = "IP-RL-RUN-006"
ERR_FOUR_TRACK = "IP-RL-RUN-007"
ERR_EXTERNAL = "IP-RL-RUN-008"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}
RUNTIME_PROOF_REQUIRED_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
    "mutation",
}
LEVELS = {"L0", "L1", "L2", "L3"}
DEFAULT_ATTEMPT_FIELDS: dict[str, tuple[str, ...]] = {
    "L0": (),
    "L1": ("attempt", "hypothesis", "patch", "expected_effect", "result"),
    "L2": (
        "attempt",
        "hypothesis",
        "patch",
        "expected_effect",
        "result",
        "result_code",
        "target_reached",
        "no_target_reached",
        "next_action",
        "evidence_refs",
    ),
    "L3": (
        "attempt",
        "hypothesis",
        "patch",
        "expected_effect",
        "result",
        "result_code",
        "target_reached",
        "no_target_reached",
        "next_action",
        "evidence_refs",
    ),
}
DEFAULT_LEVEL_RUN_FIELDS: dict[str, tuple[str, ...]] = {
    "L0": (),
    "L1": (),
    "L2": ("roundtable_evidence_refs", "vendor_evidence_refs", "network_evidence_refs", "reference_evidence_refs"),
    "L3": ("roundtable_evidence_refs", "vendor_evidence_refs", "network_evidence_refs", "reference_evidence_refs"),
}
DEFAULT_LEVEL_EXTERNAL_FIELDS: dict[str, tuple[str, ...]] = {
    "L0": (),
    "L1": (),
    "L2": (),
    "L3": ("external_source_freshness_status", "conflict_reconciliation_note", "source_url_set"),
}
DEFAULT_COMPLETION_STATES = {"done", "pass", "passed", "success", "completed", "closed"}
DEFAULT_NO_TARGET_TOKENS = {"no_target_reached", "not_reached", "target_not_reached"}
DEFAULT_FAIL_TOKENS = {"fail", "failed", "error", "blocked", "no_target_reached", "not_reached", "target_not_reached"}
DEFAULT_PASS_TOKENS = {"pass", "passed", "success", "done", "resolved", "target_reached"}
DEFAULT_ESCALATION_SIGNAL_FIELDS = (
    "route_switch_triggered",
    "human_collaboration_triggered",
    "escalation_triggered",
    "route_switch_ref",
    "human_collaboration_ref",
    "escalation_ref",
    "next_action",
)
DEFAULT_ESCALATION_SIGNAL_VALUES = {
    "true",
    "1",
    "yes",
    "triggered",
    "escalate",
    "handoff",
    "route_switch",
    "human_collaboration",
}
DEFAULT_NO_TARGET_COMPLETION_MODE = "terminal_attempt_only"
NO_TARGET_COMPLETION_MODE_ANY = {"any_attempt", "historical_any", "any"}
NO_TARGET_COMPLETION_MODE_TERMINAL = {
    "terminal_attempt_only",
    "terminal_attempt",
    "terminal",
    "final_attempt",
}
DEFAULT_ESCALATION_NONEMPTY_FIELDS = {"next_action"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _emit_with_status(payload: dict[str, Any], *, json_only: bool) -> None:
    payload["status"] = str(payload.get("reasoning_loop_failclose_status", "")).strip().upper()
    _emit(payload, json_only=json_only)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    return [str(x).strip() for x in _as_list(value) if str(x).strip()]


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "reasoning_loop_failclose_contract_v1",
        "reasoning_loop_failclose_contract",
        "rq_035_reasoning_loop_failclose_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _resolve_report_candidates(
    *,
    identity_id: str,
    pack_path: Path,
    report_selected_path: str,
    learning_pattern: str,
) -> tuple[list[Path], list[Path]]:
    runtime_candidates: list[Path] = []
    selected = str(report_selected_path or "").strip()
    if selected:
        p = Path(selected).expanduser().resolve()
        if p.exists() and p.is_file():
            runtime_candidates.append(p)

    latest = latest_identity_upgrade_report(identity_id, pack_path)
    if latest is not None:
        runtime_candidates.append(latest.resolve())

    learning_candidates: list[Path] = []
    raw_pattern = str(learning_pattern or "").strip()
    if raw_pattern:
        p = Path(raw_pattern).expanduser()
        has_magic = any(ch in raw_pattern for ch in ["*", "?", "["])
        if p.is_absolute():
            if has_magic:
                learning_candidates.extend(
                    Path(x).expanduser().resolve() for x in glob.glob(str(p)) if Path(x).is_file()
                )
            elif p.exists() and p.is_file():
                learning_candidates.append(p.resolve())
        else:
            preferred = sorted(pack_path.glob(raw_pattern))
            if preferred:
                learning_candidates.extend(x.resolve() for x in preferred if x.is_file())
            else:
                learning_candidates.extend(x.resolve() for x in Path(".").glob(raw_pattern) if x.is_file())

    fallback_pack = (pack_path / "runtime" / "examples" / f"{identity_id}-learning-sample.json").resolve()
    if fallback_pack.exists() and fallback_pack.is_file():
        learning_candidates.append(fallback_pack)
    fallback_repo = (Path("identity") / "runtime" / "examples" / f"{identity_id}-learning-sample.json").resolve()
    if fallback_repo.exists() and fallback_repo.is_file():
        learning_candidates.append(fallback_repo)

    uniq_runtime: list[Path] = []
    seen_runtime: set[str] = set()
    for path in runtime_candidates:
        key = str(path.resolve())
        if key not in seen_runtime:
            seen_runtime.add(key)
            uniq_runtime.append(path.resolve())

    uniq_learning: list[Path] = []
    seen_learning: set[str] = set()
    for path in learning_candidates:
        key = str(path.resolve())
        if key not in seen_learning:
            seen_learning.add(key)
            uniq_learning.append(path.resolve())
    return uniq_runtime, uniq_learning


def _extract_attempts(report_doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("reasoning_attempts", "attempts"):
        value = report_doc.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _result_token(attempt: dict[str, Any]) -> str:
    for key in ("result_code", "result", "status"):
        token = str(attempt.get(key, "")).strip().lower()
        if token:
            return token
    return ""


def _completion_token(report_doc: dict[str, Any]) -> str:
    for key in ("overall_status", "final_status", "status", "result", "outcome"):
        token = str(report_doc.get(key, "")).strip().lower()
        if token:
            return token
    return ""


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _has_escalation_signal(
    *,
    report_doc: dict[str, Any],
    attempts: list[dict[str, Any]],
    fields: list[str],
    values: set[str],
    accept_nonempty_ref: bool,
    accept_nonempty_fields: set[str],
) -> bool:
    sources: list[dict[str, Any]] = [report_doc] + [row for row in attempts if isinstance(row, dict)]
    normalized_nonempty_fields = {str(x).strip().lower() for x in accept_nonempty_fields if str(x).strip()}
    for source in sources:
        for field in fields:
            key = str(field or "").strip()
            if not key:
                continue
            raw = source.get(key)
            if isinstance(raw, bool) and raw:
                return True
            norm_key = key.lower()
            if _nonempty(raw):
                if norm_key in normalized_nonempty_fields:
                    return True
                if accept_nonempty_ref and (
                    norm_key.endswith("_ref")
                    or norm_key.endswith("_refs")
                ):
                    return True
            text = str(raw or "").strip().lower()
            if text in values:
                return True
    return False


def _normalize_no_target_completion_mode(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value in NO_TARGET_COMPLETION_MODE_ANY:
        return "any_attempt"
    if value in NO_TARGET_COMPLETION_MODE_TERMINAL or not value:
        return "terminal_attempt_only"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate reasoning-loop fail-close contract (RQ-035).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=[
            "activate",
            "update",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "scan",
            "three-plane",
            "inspection",
            "mutation",
        ],
        default="validate",
    )
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report-selected-path", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    repo_root = Path(__file__).resolve().parents[1]
    registry_path = (
        repo_root
        / str(contract.get("plugin_registry_path", "identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml"))
    ).resolve()
    required = contract_required(contract)
    auto_required_signal = registry_path.exists()
    if auto_required_signal:
        required = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required and args.operation in STRICT_OPERATIONS),
        "reasoning_loop_failclose_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_runtime_evidence_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_attempt_trace_status": STATUS_SKIPPED_NOT_REQUIRED,
        "no_target_done_block_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_next_action_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_escalation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_four_track_status": STATUS_SKIPPED_NOT_REQUIRED,
        "external_source_freshness_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reasoning_enforcement_level": "",
        "plugin_registry_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_report_path": "",
        "runtime_report_run_id": "",
        "runtime_report_source": "",
        "report_selected_path": str(args.report_selected_path or "").strip(),
        "reasoning_attempt_count": 0,
        "reasoning_failed_attempt_count": 0,
        "no_target_reached_detected": False,
        "terminal_attempt_index": 0,
        "terminal_attempt_target_reached": False,
        "terminal_attempt_no_target_reached": False,
        "no_target_completion_mode": "",
        "done_requires_terminal_target_reached": True,
        "escalation_signal_accept_nonempty_ref": True,
        "escalation_signal_nonempty_fields": [],
        "reasoning_runtime_evidence_refs": [],
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit_with_status(payload, json_only=args.json_only)
        return 0

    payload["producer_readiness"] = True

    if not registry_path.exists() or not registry_path.is_file():
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REGISTRY
        payload["stale_reasons"] = [f"plugin_registry_missing:{registry_path}"]
        payload["evidence_ref"] = str(task_path)
        _emit_with_status(payload, json_only=args.json_only)
        return 1

    registry = _load_yaml(registry_path)
    plugins = _as_list(registry.get("plugins"))
    plugin_id = str(contract.get("plugin_id", "reasoning-loop-enforcement")).strip() or "reasoning-loop-enforcement"
    expected_validator = str(
        contract.get("validator", "scripts/validate_reasoning_loop_failclose.py")
    ).strip()
    row = next(
        (
            item
            for item in plugins
            if isinstance(item, dict) and str(item.get("plugin_id", "")).strip() == plugin_id
        ),
        None,
    )
    if not isinstance(row, dict):
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REGISTRY
        payload["stale_reasons"] = [f"plugin_registry_row_missing:{plugin_id}"]
        payload["evidence_ref"] = str(registry_path)
        _emit_with_status(payload, json_only=args.json_only)
        return 1

    if str(row.get("validator_script", "")).strip() != expected_validator:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REGISTRY
        payload["stale_reasons"] = ["plugin_registry_validator_mismatch"]
        payload["evidence_ref"] = str(registry_path)
        _emit_with_status(payload, json_only=args.json_only)
        return 1
    payload["plugin_registry_status"] = STATUS_PASS_REQUIRED

    level = str(contract.get("reasoning_enforcement_level", "L1")).strip().upper() or "L1"
    if level not in LEVELS:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONFIG
        payload["stale_reasons"] = [f"invalid_reasoning_enforcement_level:{level}"]
        payload["evidence_ref"] = str(task_path)
        _emit_with_status(payload, json_only=args.json_only)
        return 1
    payload["reasoning_enforcement_level"] = level

    no_target_completion_mode = _normalize_no_target_completion_mode(
        str(
            contract.get(
                "no_target_completion_mode",
                contract.get("no_target_completion_scope", DEFAULT_NO_TARGET_COMPLETION_MODE),
            )
        )
    )
    if not no_target_completion_mode:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONFIG
        payload["stale_reasons"] = ["invalid_no_target_completion_mode"]
        payload["evidence_ref"] = str(task_path)
        _emit_with_status(payload, json_only=args.json_only)
        return 1
    payload["no_target_completion_mode"] = no_target_completion_mode
    done_requires_terminal_target_reached = _boolish(
        contract.get("done_requires_terminal_target_reached", True)
    )
    payload["done_requires_terminal_target_reached"] = done_requires_terminal_target_reached

    escalation_signal_accept_nonempty_ref = _boolish(
        contract.get("escalation_signal_accept_nonempty_ref", True)
    )
    escalation_signal_nonempty_fields = {
        token.strip().lower()
        for token in _as_str_list(contract.get("escalation_signal_nonempty_fields"))
        if token.strip()
    } or set(DEFAULT_ESCALATION_NONEMPTY_FIELDS)
    payload["escalation_signal_accept_nonempty_ref"] = escalation_signal_accept_nonempty_ref
    payload["escalation_signal_nonempty_fields"] = sorted(escalation_signal_nonempty_fields)

    level_attempt_fields_cfg = contract.get("level_required_attempt_fields")
    level_run_fields_cfg = contract.get("level_required_run_fields")
    level_external_fields_cfg = contract.get("level_required_external_fields")
    attempt_fields = set(
        _as_str_list(level_attempt_fields_cfg.get(level))
        if isinstance(level_attempt_fields_cfg, dict)
        else list(DEFAULT_ATTEMPT_FIELDS[level])
    )
    run_fields = set(
        _as_str_list(level_run_fields_cfg.get(level))
        if isinstance(level_run_fields_cfg, dict)
        else list(DEFAULT_LEVEL_RUN_FIELDS[level])
    )
    external_fields = set(
        _as_str_list(level_external_fields_cfg.get(level))
        if isinstance(level_external_fields_cfg, dict)
        else list(DEFAULT_LEVEL_EXTERNAL_FIELDS[level])
    )

    runtime_candidates, learning_candidates = _resolve_report_candidates(
        identity_id=args.identity_id,
        pack_path=pack_path,
        report_selected_path=str(args.report_selected_path or "").strip(),
        learning_pattern=str(contract.get("learning_report_path_pattern", "runtime/examples/*-learning-sample.json")),
    )

    report_doc: dict[str, Any] = {}
    report_path: Path | None = None
    report_source = ""
    for candidate in runtime_candidates:
        try:
            doc = load_json(candidate)
        except Exception:
            continue
        attempts = _extract_attempts(doc)
        if attempts:
            report_doc = doc
            report_path = candidate
            report_source = "runtime_report"
            break
    if report_path is None:
        for candidate in learning_candidates:
            try:
                doc = load_json(candidate)
            except Exception:
                continue
            attempts = _extract_attempts(doc)
            if attempts:
                report_doc = doc
                report_path = candidate
                report_source = "learning_sample_fallback"
                break

    if report_path is None:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_attempt_trace_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RUNTIME_MISSING
        payload["stale_reasons"] = ["reasoning_report_missing_or_no_attempts"]
        payload["reasoning_runtime_evidence_refs"] = [str(p) for p in runtime_candidates[:2] + learning_candidates[:2]]
        payload["evidence_ref"] = str(task_path)
        _emit(payload, json_only=args.json_only)
        return 1

    payload["runtime_report_path"] = str(report_path)
    payload["runtime_report_source"] = report_source
    payload["runtime_report_run_id"] = str(report_doc.get("run_id", "")).strip()
    payload["reasoning_runtime_evidence_refs"] = [str(report_path)]
    payload["evidence_ref"] = str(report_path)

    run_id_binding = str(args.run_id or "").strip()
    if run_id_binding and payload["runtime_report_run_id"] and payload["runtime_report_run_id"] != run_id_binding:
        if report_source == "runtime_report":
            payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
            payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_RUN_ID_MISMATCH
            payload["stale_reasons"] = [
                f"runtime_report_run_id_mismatch:{payload['runtime_report_run_id']}!={run_id_binding}"
            ]
            _emit_with_status(payload, json_only=args.json_only)
            return 1
        payload["stale_reasons"].append(
            f"run_id_mismatch_accepted_by_learning_fallback:{payload['runtime_report_run_id']}!={run_id_binding}"
        )

    attempts = _extract_attempts(report_doc)
    payload["reasoning_attempt_count"] = len(attempts)
    if not attempts:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_attempt_trace_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RUNTIME_MISSING
        payload["stale_reasons"].append("reasoning_attempts_empty")
        _emit_with_status(payload, json_only=args.json_only)
        return 1

    missing_attempt_fields: list[str] = []
    failed_attempt_count = 0
    failed_without_next_action_count = 0
    no_target_detected = False
    terminal_attempt_target_reached = False
    terminal_attempt_no_target_reached = False
    terminal_attempt_index = len(attempts)
    no_target_tokens = {
        token.strip().lower()
        for token in _as_str_list(contract.get("no_target_result_tokens"))
    } or DEFAULT_NO_TARGET_TOKENS
    fail_tokens = {
        token.strip().lower()
        for token in _as_str_list(contract.get("failed_result_tokens"))
    } or DEFAULT_FAIL_TOKENS
    pass_tokens = {
        token.strip().lower()
        for token in _as_str_list(contract.get("pass_result_tokens"))
    } or DEFAULT_PASS_TOKENS

    for idx, attempt in enumerate(attempts, start=1):
        missing = sorted(field for field in attempt_fields if field not in attempt)
        if missing:
            missing_attempt_fields.extend(f"attempt[{idx}]:{field}" for field in missing)

        result_token = _result_token(attempt)
        no_target = _boolish(attempt.get("no_target_reached")) or (result_token in no_target_tokens)
        no_target_detected = no_target_detected or no_target
        target_reached = _boolish(attempt.get("target_reached")) or (result_token in pass_tokens)
        attempt_failed = no_target or (result_token in fail_tokens) or (not target_reached and result_token != "")
        if attempt_failed:
            failed_attempt_count += 1
            if _boolish(contract.get("failure_requires_next_action", True)):
                if not _nonempty(attempt.get("next_action")):
                    failed_without_next_action_count += 1
        terminal_attempt_index = idx
        terminal_attempt_target_reached = target_reached
        terminal_attempt_no_target_reached = no_target

    payload["reasoning_failed_attempt_count"] = failed_attempt_count
    payload["no_target_reached_detected"] = no_target_detected
    payload["terminal_attempt_index"] = terminal_attempt_index
    payload["terminal_attempt_target_reached"] = terminal_attempt_target_reached
    payload["terminal_attempt_no_target_reached"] = terminal_attempt_no_target_reached

    completion_states = {
        token.strip().lower()
        for token in _as_str_list(contract.get("completion_states_done"))
    } or DEFAULT_COMPLETION_STATES
    completion_token = _completion_token(report_doc)
    completion_is_done = completion_token in completion_states

    max_attempts_before_escalation = int(
        contract.get(
            "max_attempts_before_escalation",
            (task.get("reasoning_loop_contract") or {}).get("max_attempts_before_escalation", 3),
        )
    )
    escalation_signal_fields = _as_str_list(contract.get("escalation_signal_fields")) or list(
        DEFAULT_ESCALATION_SIGNAL_FIELDS
    )
    escalation_signal_values = {
        token.strip().lower() for token in _as_str_list(contract.get("escalation_signal_values"))
    } or DEFAULT_ESCALATION_SIGNAL_VALUES
    escalation_required = failed_attempt_count > max_attempts_before_escalation
    escalation_detected = _has_escalation_signal(
        report_doc=report_doc,
        attempts=attempts,
        fields=escalation_signal_fields,
        values=escalation_signal_values,
        accept_nonempty_ref=escalation_signal_accept_nonempty_ref,
        accept_nonempty_fields=escalation_signal_nonempty_fields,
    )

    run_field_missing = sorted(field for field in run_fields if not _nonempty(report_doc.get(field)))
    external_field_missing = sorted(field for field in external_fields if not _nonempty(report_doc.get(field)))

    external_freshness_ok = True
    if level == "L3":
        freshness = str(report_doc.get("external_source_freshness_status", "")).strip().upper()
        external_freshness_ok = freshness in {"PASS_REQUIRED", "PASS"}

    no_target_done_violation = False
    if completion_is_done:
        if no_target_completion_mode == "any_attempt":
            no_target_done_violation = no_target_detected
        else:
            no_target_done_violation = terminal_attempt_no_target_reached
        if done_requires_terminal_target_reached and not terminal_attempt_target_reached:
            no_target_done_violation = True

    fail_code = ""
    if missing_attempt_fields:
        fail_code = ERR_ATTEMPT_FIELDS
    elif no_target_done_violation:
        fail_code = ERR_NO_TARGET_DONE
    elif failed_without_next_action_count > 0:
        fail_code = ERR_NEXT_ACTION
    elif escalation_required and not escalation_detected:
        fail_code = ERR_ESCALATION
    elif run_field_missing:
        fail_code = ERR_FOUR_TRACK
    elif external_field_missing or not external_freshness_ok:
        fail_code = ERR_EXTERNAL

    payload["reasoning_attempt_trace_status"] = (
        STATUS_PASS_REQUIRED if not missing_attempt_fields else STATUS_FAIL_REQUIRED
    )
    payload["no_target_done_block_status"] = (
        STATUS_FAIL_REQUIRED if no_target_done_violation else STATUS_PASS_REQUIRED
    )
    payload["reasoning_next_action_status"] = (
        STATUS_FAIL_REQUIRED if failed_without_next_action_count > 0 else STATUS_PASS_REQUIRED
    )
    payload["reasoning_escalation_status"] = (
        STATUS_FAIL_REQUIRED if (escalation_required and not escalation_detected) else STATUS_PASS_REQUIRED
    )
    if level in {"L2", "L3"}:
        payload["reasoning_four_track_status"] = (
            STATUS_PASS_REQUIRED if not run_field_missing else STATUS_FAIL_REQUIRED
        )
    else:
        payload["reasoning_four_track_status"] = STATUS_SKIPPED_NOT_REQUIRED
    if level == "L3":
        payload["external_source_freshness_status"] = (
            STATUS_PASS_REQUIRED if (not external_field_missing and external_freshness_ok) else STATUS_FAIL_REQUIRED
        )
    else:
        payload["external_source_freshness_status"] = STATUS_SKIPPED_NOT_REQUIRED

    if fail_code:
        payload["reasoning_loop_failclose_status"] = STATUS_FAIL_REQUIRED
        payload["reasoning_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = fail_code
        if missing_attempt_fields:
            payload["stale_reasons"].append(f"missing_attempt_fields:{len(missing_attempt_fields)}")
        if fail_code == ERR_NO_TARGET_DONE:
            payload["stale_reasons"].append(
                "done_transition_violation:"
                + f"mode={no_target_completion_mode},terminal_target_reached={terminal_attempt_target_reached},"
                + f"terminal_no_target={terminal_attempt_no_target_reached}"
            )
        if run_field_missing:
            payload["stale_reasons"].append(f"missing_level_run_fields:{','.join(run_field_missing)}")
        if external_field_missing:
            payload["stale_reasons"].append(f"missing_external_fields:{','.join(external_field_missing)}")
        if level == "L3" and not external_freshness_ok:
            payload["stale_reasons"].append("external_source_freshness_status_not_pass")
        _emit_with_status(payload, json_only=args.json_only)
        return 1

    payload["reasoning_loop_failclose_status"] = STATUS_PASS_REQUIRED
    payload["reasoning_runtime_evidence_status"] = (
        STATUS_PASS_REQUIRED if args.operation in RUNTIME_PROOF_REQUIRED_OPERATIONS else STATUS_SKIPPED_NOT_REQUIRED
    )
    payload["error_code"] = ""
    _emit_with_status(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
