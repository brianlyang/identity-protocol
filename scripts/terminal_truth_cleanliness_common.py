#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"

TERMINAL_TRUTH_CLEANLINESS_CONTRACT_KEY = "identity_terminal_truth_cleanliness_contract_v1"
TERMINAL_TRUTH_CLEANLINESS_CONTRACT_ID = "rq_056_identity_terminal_truth_cleanliness_contract_v1"
TERMINAL_TRUTH_CLEANLINESS_VALIDATOR_ID = "scripts/validate_terminal_truth_cleanliness.py"
TERMINAL_TRUTH_CLEANLINESS_PROBE_RUNNER_ID = "scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh"

NEGATIVE_FEEDBACK_TERMINAL_VETO_CONTRACT_ID = "negative_feedback_terminal_veto_contract_v1"
CANONICAL_PUBLISHABLE_RESULT_GATE_CONTRACT_ID = "canonical_publishable_result_gate_contract_v1"
INSTANCE_ADOPTION_TERMINAL_TRUTH_PROBE_CONTRACT_ID = "instance_adoption_terminal_truth_probe_contract_v1"

TERMINAL_VETO_SCOPE: tuple[str, ...] = (
    "clean_terminal_truth",
    "canonical_publishability",
)

TERMINAL_TRUTH_CLASSES: tuple[str, ...] = (
    "clean_terminal_truth",
    "review_required_execution_closure",
    "dirty_terminal_execution_closure",
    "non_terminal_or_failed_execution",
)

TERMINAL_STATE_CLASSES: tuple[str, ...] = (
    "completed_clean",
    "review_pending",
    "revalidation_pending",
    "repair_pending",
    "retry_pending",
    "quarantined",
    "failed_terminal",
    "non_terminal_pending",
)

NEGATIVE_FEEDBACK_CLASSES: tuple[str, ...] = (
    "none",
    "review_required",
    "degraded_execution",
    "placeholder_result",
    "unresolved_contradiction",
    "confidence_below_floor",
)

DIRTY_SIGNAL_FIELDS: tuple[str, ...] = (
    "all_ok",
    "writeback_mode",
    "writeback_status",
    "degrade_reason",
    "next_action",
    "next_recovery_action",
    "failure_reason",
    "prompt_change_required",
    "prompt_change_applied",
)

PLACEHOLDER_SCAN_FIELDS: tuple[str, ...] = (
    "title",
    "report_title",
    "report_payload",
    "final_payload",
    "final_report",
    "canonical_result",
    "publishable_result",
    "response_text",
    "output_title",
    "output_payload",
)

REQUIRED_REPORT_FIELDS: tuple[str, ...] = (
    "identity_terminal_truth_cleanliness_status",
    "terminal_truth_contract_status",
    "terminal_state_machine_status",
    "terminal_state_class",
    "terminal_state_basis",
    "terminal_state_conflict_status",
    "requires_review",
    "retry_required",
    "revalidation_required",
    "repair_required",
    "quarantine_required",
    "requires_human",
    "terminal_failure",
    "state_transition_required",
    "state_machine_blockers",
    "execution_closure_status",
    "terminal_truth_cleanliness_status",
    "terminal_truth_class",
    "is_terminal_clean",
    "is_terminal_dirty",
    "terminal_truth_basis",
    "terminal_truth_blockers",
    "negative_feedback_terminal_veto_status",
    "negative_feedback_class",
    "feedback_severity",
    "terminal_veto_required",
    "terminal_veto_scope",
    "loopback_required",
    "loopback_target_stage",
    "loopback_reason",
    "pre_terminal_veto_applied",
    "next_state_after_veto",
    "canonical_publishable_result_status",
    "publishable",
    "publish_blockers",
    "canonical_result_eligible",
    "canonical_result_basis",
    "requires_repair_before_publish",
    "instance_adoption_terminal_truth_probe_status",
    "stale_reasons",
    "error_code",
)

CANONICAL_STRICT_FIELDS: tuple[str, ...] = (
    "required",
    "contract_id",
    "validator",
    "probe_runner",
    "fail_mode",
    "negative_feedback_terminal_veto_contract_id",
    "canonical_publishable_result_gate_contract_id",
    "instance_adoption_probe_contract_id",
    "dirty_signal_fields",
    "placeholder_result_scan_fields",
    "terminal_veto_scope",
    "required_report_fields",
    "review_required_execution_closure_allowed",
    "preserve_execution_closure_distinction",
    "canonical_publishability_requires_clean_terminal_truth",
    "philosophy_anchor_refs",
)

PLACEHOLDER_TOKENS: tuple[str, ...] = (
    "placeholder",
    "todo",
    "tbd",
    "dummy",
    "stub",
)

CONTRADICTION_FIELDS: tuple[str, ...] = (
    "multimodal_inconsistency_status",
    "contradiction_status",
    "consistency_status",
)

CONFIDENCE_FIELDS: tuple[str, ...] = (
    "confidence_status",
    "confidence_floor_status",
)


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return clean_string(value).lower() in {"1", "true", "yes", "y", "on"}


def status_is_pass(value: Any) -> bool:
    return clean_string(value).upper() == STATUS_PASS_REQUIRED


def _bool_or_false(value: Any) -> bool:
    return as_bool(value)


def terminal_truth_cleanliness_contract_skeleton() -> dict[str, Any]:
    return {
        "required": True,
        "contract_id": TERMINAL_TRUTH_CLEANLINESS_CONTRACT_ID,
        "validator": TERMINAL_TRUTH_CLEANLINESS_VALIDATOR_ID,
        "probe_runner": TERMINAL_TRUTH_CLEANLINESS_PROBE_RUNNER_ID,
        "fail_mode": "fail_required",
        "negative_feedback_terminal_veto_contract_id": NEGATIVE_FEEDBACK_TERMINAL_VETO_CONTRACT_ID,
        "canonical_publishable_result_gate_contract_id": CANONICAL_PUBLISHABLE_RESULT_GATE_CONTRACT_ID,
        "instance_adoption_probe_contract_id": INSTANCE_ADOPTION_TERMINAL_TRUTH_PROBE_CONTRACT_ID,
        "dirty_signal_fields": list(DIRTY_SIGNAL_FIELDS),
        "placeholder_result_scan_fields": list(PLACEHOLDER_SCAN_FIELDS),
        "terminal_veto_scope": list(TERMINAL_VETO_SCOPE),
        "required_report_fields": list(REQUIRED_REPORT_FIELDS),
        "review_required_execution_closure_allowed": True,
        "preserve_execution_closure_distinction": True,
        "canonical_publishability_requires_clean_terminal_truth": True,
        "philosophy_anchor_refs": [
            "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
            "identity/protocol/README.md",
        ],
    }


def canonicalize_terminal_truth_cleanliness_contract_doc(contract_doc: dict[str, Any] | None) -> dict[str, Any]:
    default = terminal_truth_cleanliness_contract_skeleton()
    current = clone_json(contract_doc) if isinstance(contract_doc, dict) else {}
    for key, value in default.items():
        if key not in current:
            current[key] = clone_json(value)
    for key in CANONICAL_STRICT_FIELDS:
        current[key] = clone_json(default[key])
    return current


def resolve_pack_task(
    *,
    catalog_path: Path | None,
    current_task: str,
    identity_id: str,
) -> tuple[Path, Path, dict[str, Any]]:
    if clean_string(current_task):
        task_path = Path(clean_string(current_task)).expanduser().resolve()
        if not task_path.is_file():
            raise FileNotFoundError(f"current_task_not_found:{task_path}")
        task_doc = load_json(task_path)
        return task_path.parent.resolve(), task_path.resolve(), task_doc
    if catalog_path is None or not catalog_path.exists():
        missing_catalog = catalog_path if catalog_path is not None else "<missing>"
        raise FileNotFoundError(f"catalog not found: {missing_catalog}")
    pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
    task_doc = load_json(task_path)
    return pack_root.resolve(), task_path.resolve(), task_doc


def resolve_terminal_truth_cleanliness_contract(task_doc: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    contract_doc = task_doc.get(TERMINAL_TRUTH_CLEANLINESS_CONTRACT_KEY)
    if not isinstance(contract_doc, dict):
        contract_doc = {}
    return contract_required(contract_doc), contract_doc, TERMINAL_TRUTH_CLEANLINESS_CONTRACT_KEY


def terminal_truth_cleanliness_contract_issues(contract_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if clean_string(contract_doc.get("contract_id")) != TERMINAL_TRUTH_CLEANLINESS_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if clean_string(contract_doc.get("validator")) != TERMINAL_TRUTH_CLEANLINESS_VALIDATOR_ID:
        issues.append("validator_mismatch")
    if clean_string(contract_doc.get("probe_runner")) != TERMINAL_TRUTH_CLEANLINESS_PROBE_RUNNER_ID:
        issues.append("probe_runner_mismatch")
    if bool(contract_doc.get("required")) is not True:
        issues.append("required_flag_not_true")
    if clean_string(contract_doc.get("fail_mode")).lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")
    if clean_string(contract_doc.get("negative_feedback_terminal_veto_contract_id")) != NEGATIVE_FEEDBACK_TERMINAL_VETO_CONTRACT_ID:
        issues.append("negative_feedback_veto_contract_id_mismatch")
    if clean_string(contract_doc.get("canonical_publishable_result_gate_contract_id")) != CANONICAL_PUBLISHABLE_RESULT_GATE_CONTRACT_ID:
        issues.append("publishable_result_gate_contract_id_mismatch")
    if clean_string(contract_doc.get("instance_adoption_probe_contract_id")) != INSTANCE_ADOPTION_TERMINAL_TRUTH_PROBE_CONTRACT_ID:
        issues.append("instance_adoption_probe_contract_id_mismatch")

    dirty_fields = [clean_string(item) for item in (contract_doc.get("dirty_signal_fields") or []) if clean_string(item)]
    if dirty_fields != list(DIRTY_SIGNAL_FIELDS):
        issues.append("dirty_signal_fields_mismatch")

    placeholder_fields = [clean_string(item) for item in (contract_doc.get("placeholder_result_scan_fields") or []) if clean_string(item)]
    if placeholder_fields != list(PLACEHOLDER_SCAN_FIELDS):
        issues.append("placeholder_result_scan_fields_mismatch")

    veto_scope = [clean_string(item) for item in (contract_doc.get("terminal_veto_scope") or []) if clean_string(item)]
    if veto_scope != list(TERMINAL_VETO_SCOPE):
        issues.append("terminal_veto_scope_mismatch")

    report_fields = [clean_string(item) for item in (contract_doc.get("required_report_fields") or []) if clean_string(item)]
    if report_fields != list(REQUIRED_REPORT_FIELDS):
        issues.append("required_report_fields_mismatch")

    philosophy_refs = [clean_string(item) for item in (contract_doc.get("philosophy_anchor_refs") or []) if clean_string(item)]
    if philosophy_refs != [
        "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
        "identity/protocol/README.md",
    ]:
        issues.append("philosophy_anchor_refs_mismatch")

    if bool(contract_doc.get("review_required_execution_closure_allowed")) is not True:
        issues.append("review_required_execution_closure_allowed_not_true")
    if bool(contract_doc.get("preserve_execution_closure_distinction")) is not True:
        issues.append("preserve_execution_closure_distinction_not_true")
    if bool(contract_doc.get("canonical_publishability_requires_clean_terminal_truth")) is not True:
        issues.append("canonical_publishability_requires_clean_terminal_truth_not_true")
    return issues


def _collect_placeholder_hits(report_doc: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for field in PLACEHOLDER_SCAN_FIELDS:
        raw = report_doc.get(field)
        if not isinstance(raw, str):
            continue
        text = raw.strip().lower()
        if text and any(token in text for token in PLACEHOLDER_TOKENS):
            hits.append(field)
    return hits


def _collect_contradiction_hits(report_doc: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for field in CONTRADICTION_FIELDS:
        value = clean_string(report_doc.get(field)).upper()
        if value == STATUS_FAIL_REQUIRED:
            hits.append(field)
    if as_bool(report_doc.get("contradiction_unresolved")):
        hits.append("contradiction_unresolved")
    return hits


def _collect_confidence_hits(report_doc: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for field in CONFIDENCE_FIELDS:
        value = clean_string(report_doc.get(field)).upper()
        if value and value != STATUS_PASS_REQUIRED:
            hits.append(field)
    if as_bool(report_doc.get("confidence_below_floor")):
        hits.append("confidence_below_floor")
    score = report_doc.get("confidence_score")
    floor = report_doc.get("required_confidence_floor")
    try:
        if score is not None and floor is not None and float(score) < float(floor):
            hits.append("confidence_score_below_floor")
    except Exception:
        pass
    return sorted(set(hits))


def _execution_closure_basis(report_doc: dict[str, Any]) -> tuple[str, bool]:
    all_ok = as_bool(report_doc.get("all_ok"))
    upgrade_required = as_bool(report_doc.get("upgrade_required"))
    writeback_mode = clean_string(report_doc.get("writeback_mode")).upper()
    writeback_status = clean_string(report_doc.get("writeback_status")).upper()
    strict_non_upgrade_closed = (
        (not upgrade_required)
        and all_ok
        and writeback_mode == "STRICT_WRITEBACK"
        and writeback_status in {"WRITTEN", "NOT_REQUIRED"}
    )
    strict_upgrade_closed = upgrade_required and all_ok and writeback_status == "WRITTEN"
    if strict_non_upgrade_closed:
        return "strict_non_upgrade_closed", True
    if strict_upgrade_closed:
        return "strict_upgrade_closed", True
    return "execution_closure_not_reached", False


def _contains_transition_token(*values: str, tokens: tuple[str, ...]) -> bool:
    haystack = " ".join(clean_string(value).lower() for value in values if clean_string(value))
    return any(token in haystack for token in tokens)


def derive_terminal_state_projection(
    report_doc: dict[str, Any],
    *,
    terminal_truth_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report_doc = report_doc if isinstance(report_doc, dict) else {}
    truth = terminal_truth_projection if isinstance(terminal_truth_projection, dict) else derive_terminal_truth_projection(report_doc)

    next_action = clean_string(report_doc.get("next_action"))
    next_recovery_action = clean_string(report_doc.get("next_recovery_action"))
    failure_reason = clean_string(report_doc.get("failure_reason"))

    is_terminal_clean = bool(truth.get("is_terminal_clean", False))
    publishable = bool(truth.get("publishable", False))
    negative_feedback_class = clean_string(truth.get("negative_feedback_class"))
    next_state_after_veto = clean_string(truth.get("next_state_after_veto"))
    loopback_required = bool(truth.get("loopback_required", False))

    explicit_quarantine = as_bool(report_doc.get("quarantine_required"))
    explicit_retry = as_bool(report_doc.get("retry_required"))
    explicit_requires_human = as_bool(report_doc.get("requires_human"))
    explicit_terminal_failure = as_bool(report_doc.get("terminal_failure")) or as_bool(report_doc.get("failed_terminal"))

    requires_review = negative_feedback_class == "review_required" or next_state_after_veto == "review_pending"
    revalidation_required = next_state_after_veto == "revalidation_pending"
    repair_required = next_state_after_veto == "repair_pending"
    quarantine_required = explicit_quarantine or _contains_transition_token(
        next_action, next_recovery_action, failure_reason, tokens=("quarantine", "quarantined")
    )
    retry_required = explicit_retry or revalidation_required or repair_required or _contains_transition_token(
        next_action, next_recovery_action, failure_reason, tokens=("retry", "rerun", "replay")
    )
    requires_human = explicit_requires_human or requires_review or _contains_transition_token(
        next_action, next_recovery_action, failure_reason, tokens=("human", "manual_review", "approval")
    )
    terminal_failure = explicit_terminal_failure or _contains_transition_token(
        next_action, next_recovery_action, failure_reason, tokens=("failed_terminal", "terminal_failure", "abort_terminal", "fatal")
    )

    terminal_state_basis = clean_string(truth.get("terminal_truth_class")) or clean_string(truth.get("terminal_truth_basis"))

    if is_terminal_clean and publishable:
        terminal_state_class = "completed_clean"
    elif terminal_failure:
        terminal_state_class = "failed_terminal"
    elif quarantine_required:
        terminal_state_class = "quarantined"
    elif requires_review:
        terminal_state_class = "review_pending"
    elif repair_required:
        terminal_state_class = "repair_pending"
    elif revalidation_required:
        terminal_state_class = "revalidation_pending"
    elif retry_required:
        terminal_state_class = "retry_pending"
    else:
        terminal_state_class = "non_terminal_pending"

    state_transition_required = terminal_state_class not in {"completed_clean", "failed_terminal"}

    primary_specific_flags = {
        "requires_review": requires_review,
        "revalidation_required": revalidation_required,
        "repair_required": repair_required,
        "quarantine_required": quarantine_required,
        "terminal_failure": terminal_failure,
    }
    specific_true = [name for name, enabled in primary_specific_flags.items() if enabled]

    conflict_reasons: list[str] = []
    if len(specific_true) > 1:
        conflict_reasons.append("multiple_primary_terminal_state_markers")

    if terminal_state_class == "completed_clean":
        if not (is_terminal_clean and publishable):
            conflict_reasons.append("completed_clean_without_clean_publishable_truth")
        if specific_true:
            conflict_reasons.append("completed_clean_with_pending_or_failure_markers")
        if state_transition_required:
            conflict_reasons.append("completed_clean_state_transition_required_true")
    elif terminal_state_class == "review_pending":
        if not requires_review:
            conflict_reasons.append("review_pending_without_requires_review")
        if not requires_human:
            conflict_reasons.append("review_pending_without_requires_human")
        if is_terminal_clean or publishable:
            conflict_reasons.append("review_pending_marked_clean_or_publishable")
    elif terminal_state_class == "revalidation_pending":
        if not revalidation_required:
            conflict_reasons.append("revalidation_pending_without_revalidation_required")
        if not loopback_required:
            conflict_reasons.append("revalidation_pending_without_loopback_required")
        if is_terminal_clean or publishable:
            conflict_reasons.append("revalidation_pending_marked_clean_or_publishable")
    elif terminal_state_class == "repair_pending":
        if not repair_required:
            conflict_reasons.append("repair_pending_without_repair_required")
        if is_terminal_clean or publishable:
            conflict_reasons.append("repair_pending_marked_clean_or_publishable")
    elif terminal_state_class == "retry_pending":
        if not retry_required:
            conflict_reasons.append("retry_pending_without_retry_required")
        if is_terminal_clean or publishable:
            conflict_reasons.append("retry_pending_marked_clean_or_publishable")
    elif terminal_state_class == "quarantined":
        if not quarantine_required:
            conflict_reasons.append("quarantined_without_quarantine_required")
        if is_terminal_clean or publishable:
            conflict_reasons.append("quarantined_marked_clean_or_publishable")
    elif terminal_state_class == "failed_terminal":
        if not terminal_failure:
            conflict_reasons.append("failed_terminal_without_terminal_failure")
        if is_terminal_clean or publishable:
            conflict_reasons.append("failed_terminal_marked_clean_or_publishable")
        if state_transition_required:
            conflict_reasons.append("failed_terminal_state_transition_required_true")
    elif terminal_state_class == "non_terminal_pending":
        if is_terminal_clean or publishable:
            conflict_reasons.append("non_terminal_pending_marked_clean_or_publishable")
        if specific_true:
            conflict_reasons.append("non_terminal_pending_with_primary_specific_markers")

    adoption_probe_reasons: list[str] = []
    adoption_fields = {
        "terminal_state_class": terminal_state_class,
        "requires_review": requires_review,
        "retry_required": retry_required,
        "revalidation_required": revalidation_required,
        "repair_required": repair_required,
        "quarantine_required": quarantine_required,
        "requires_human": requires_human,
        "terminal_failure": terminal_failure,
        "state_transition_required": state_transition_required,
    }
    for field, expected in adoption_fields.items():
        if field not in report_doc:
            continue
        current = report_doc.get(field)
        if isinstance(expected, bool):
            if _bool_or_false(current) != expected:
                adoption_probe_reasons.append(f"report_{field}_projection_mismatch")
        elif clean_string(current) != clean_string(expected):
            adoption_probe_reasons.append(f"report_{field}_projection_mismatch")

    terminal_state_conflict_status = STATUS_FAIL_REQUIRED if conflict_reasons else STATUS_PASS_REQUIRED
    terminal_state_machine_status = (
        STATUS_FAIL_REQUIRED if conflict_reasons or adoption_probe_reasons else STATUS_PASS_REQUIRED
    )
    state_machine_blockers = sorted(set(conflict_reasons + adoption_probe_reasons))

    return {
        "terminal_state_machine_status": terminal_state_machine_status,
        "terminal_state_class": terminal_state_class,
        "terminal_state_basis": terminal_state_basis or terminal_state_class,
        "terminal_state_conflict_status": terminal_state_conflict_status,
        "requires_review": requires_review,
        "retry_required": retry_required,
        "revalidation_required": revalidation_required,
        "repair_required": repair_required,
        "quarantine_required": quarantine_required,
        "requires_human": requires_human,
        "terminal_failure": terminal_failure,
        "state_transition_required": state_transition_required,
        "state_machine_blockers": state_machine_blockers,
    }


def derive_terminal_truth_projection(
    report_doc: dict[str, Any],
    *,
    post_execution_status: str = "",
    writeback_continuity_status: str = "",
) -> dict[str, Any]:
    report_doc = report_doc if isinstance(report_doc, dict) else {}
    basis, execution_from_report = _execution_closure_basis(report_doc)
    support_statuses = [clean_string(post_execution_status).upper(), clean_string(writeback_continuity_status).upper()]
    support_statuses = [status for status in support_statuses if status]
    support_ok = all(status == STATUS_PASS_REQUIRED for status in support_statuses) if support_statuses else True
    execution_closure_status = STATUS_PASS_REQUIRED if execution_from_report and support_ok else STATUS_FAIL_REQUIRED

    next_action = clean_string(report_doc.get("next_action"))
    next_recovery_action = clean_string(report_doc.get("next_recovery_action"))
    writeback_mode = clean_string(report_doc.get("writeback_mode")).upper()
    writeback_status = clean_string(report_doc.get("writeback_status")).upper()
    degrade_reason = clean_string(report_doc.get("degrade_reason"))
    all_ok = as_bool(report_doc.get("all_ok"))
    prompt_change_required = as_bool(report_doc.get("prompt_change_required"))
    prompt_change_applied = as_bool(report_doc.get("prompt_change_applied"))

    review_required = next_action.startswith("review_required")
    placeholder_hits = _collect_placeholder_hits(report_doc)
    contradiction_hits = _collect_contradiction_hits(report_doc)
    confidence_hits = _collect_confidence_hits(report_doc)

    dirty_signals: list[str] = []
    if review_required:
        dirty_signals.append("review_required_next_action")
    if writeback_mode == "DEGRADED_WRITEBACK":
        dirty_signals.append("degraded_writeback_mode")
    if writeback_status.startswith("DEFERRED_"):
        dirty_signals.append(f"writeback_status:{writeback_status}")
    if not all_ok:
        dirty_signals.append("all_ok_false")
    if next_recovery_action:
        dirty_signals.append("next_recovery_action_present")
    if degrade_reason:
        dirty_signals.append("degrade_reason_present")
    if prompt_change_required and not prompt_change_applied:
        dirty_signals.append("prompt_change_pending")
    if placeholder_hits:
        dirty_signals.append("placeholder_result_present")
    if contradiction_hits:
        dirty_signals.append("unresolved_contradiction")
    if confidence_hits:
        dirty_signals.append("confidence_below_floor")

    negative_feedback_class = "none"
    feedback_severity = "none"
    loopback_required = False
    loopback_target_stage = ""
    loopback_reason = ""
    next_state_after_veto = ""

    if review_required:
        negative_feedback_class = "review_required"
        feedback_severity = "medium"
        loopback_required = False
        loopback_target_stage = "human_review"
        loopback_reason = next_action or "review_required"
        next_state_after_veto = "review_pending"
    elif writeback_mode == "DEGRADED_WRITEBACK" or writeback_status.startswith("DEFERRED_") or next_recovery_action or not all_ok or degrade_reason:
        negative_feedback_class = "degraded_execution"
        feedback_severity = "high"
        loopback_required = True
        loopback_target_stage = "first_loop_revalidation"
        loopback_reason = next_recovery_action or degrade_reason or writeback_status or "degraded_execution"
        next_state_after_veto = "revalidation_pending"
    elif contradiction_hits:
        negative_feedback_class = "unresolved_contradiction"
        feedback_severity = "high"
        loopback_required = True
        loopback_target_stage = "first_loop_revalidation"
        loopback_reason = "unresolved_contradiction"
        next_state_after_veto = "revalidation_pending"
    elif confidence_hits:
        negative_feedback_class = "confidence_below_floor"
        feedback_severity = "medium"
        loopback_required = True
        loopback_target_stage = "first_loop_revalidation"
        loopback_reason = "confidence_below_floor"
        next_state_after_veto = "revalidation_pending"
    elif placeholder_hits:
        negative_feedback_class = "placeholder_result"
        feedback_severity = "medium"
        loopback_required = True
        loopback_target_stage = "repair_before_publish"
        loopback_reason = "placeholder_result"
        next_state_after_veto = "repair_pending"

    terminal_veto_required = execution_closure_status == STATUS_PASS_REQUIRED and negative_feedback_class != "none"
    terminal_veto_scope = list(TERMINAL_VETO_SCOPE) if terminal_veto_required else []
    pre_terminal_veto_applied = terminal_veto_required
    is_terminal_clean = execution_closure_status == STATUS_PASS_REQUIRED and not terminal_veto_required
    is_terminal_dirty = execution_closure_status == STATUS_PASS_REQUIRED and terminal_veto_required

    if is_terminal_clean:
        terminal_truth_class = "clean_terminal_truth"
    elif execution_closure_status == STATUS_PASS_REQUIRED and review_required:
        terminal_truth_class = "review_required_execution_closure"
    elif execution_closure_status == STATUS_PASS_REQUIRED:
        terminal_truth_class = "dirty_terminal_execution_closure"
    else:
        terminal_truth_class = "non_terminal_or_failed_execution"
        if not next_state_after_veto:
            next_state_after_veto = "non_terminal_pending"

    terminal_truth_cleanliness_status = STATUS_PASS_REQUIRED if is_terminal_clean else STATUS_FAIL_REQUIRED
    canonical_result_eligible = is_terminal_clean
    publishable = canonical_result_eligible
    canonical_publishable_result_status = STATUS_PASS_REQUIRED if publishable else STATUS_FAIL_REQUIRED
    publish_blockers = sorted(set(dirty_signals + (["execution_closure_not_reached"] if execution_closure_status != STATUS_PASS_REQUIRED else [])))

    terminal_truth_candidate = execution_closure_status == STATUS_PASS_REQUIRED
    veto_ok = False
    if negative_feedback_class == "none":
        veto_ok = (
            not terminal_veto_required
            and not terminal_veto_scope
            and not pre_terminal_veto_applied
            and not loopback_required
        )
    elif negative_feedback_class == "review_required":
        if terminal_truth_candidate:
            veto_ok = (
                terminal_veto_required
                and terminal_veto_scope == list(TERMINAL_VETO_SCOPE)
                and pre_terminal_veto_applied is True
                and loopback_required is False
                and bool(clean_string(loopback_reason))
                and next_state_after_veto == "review_pending"
            )
        else:
            veto_ok = (
                not terminal_veto_required
                and not terminal_veto_scope
                and pre_terminal_veto_applied is False
                and loopback_required is False
                and bool(clean_string(loopback_reason))
                and next_state_after_veto == "review_pending"
            )
    else:
        if terminal_truth_candidate:
            veto_ok = (
                terminal_veto_required
                and terminal_veto_scope == list(TERMINAL_VETO_SCOPE)
                and pre_terminal_veto_applied is True
                and loopback_required is True
                and bool(clean_string(loopback_reason))
                and next_state_after_veto in {"revalidation_pending", "repair_pending"}
            )
        else:
            veto_ok = (
                not terminal_veto_required
                and not terminal_veto_scope
                and pre_terminal_veto_applied is False
                and loopback_required is True
                and bool(clean_string(loopback_reason))
                and next_state_after_veto in {"revalidation_pending", "repair_pending"}
            )
    negative_feedback_terminal_veto_status = STATUS_PASS_REQUIRED if veto_ok else STATUS_FAIL_REQUIRED

    adoption_probe_reasons: list[str] = []
    if "is_terminal_clean" in report_doc and _bool_or_false(report_doc.get("is_terminal_clean")) != is_terminal_clean:
        adoption_probe_reasons.append("report_is_terminal_clean_projection_mismatch")
    if "is_terminal_dirty" in report_doc and _bool_or_false(report_doc.get("is_terminal_dirty")) != is_terminal_dirty:
        adoption_probe_reasons.append("report_is_terminal_dirty_projection_mismatch")
    if "publishable" in report_doc and _bool_or_false(report_doc.get("publishable")) != publishable:
        adoption_probe_reasons.append("report_publishable_projection_mismatch")
    if "canonical_result_eligible" in report_doc and _bool_or_false(report_doc.get("canonical_result_eligible")) != canonical_result_eligible:
        adoption_probe_reasons.append("report_canonical_result_projection_mismatch")
    if clean_string(report_doc.get("terminal_truth_class")) and clean_string(report_doc.get("terminal_truth_class")) != terminal_truth_class:
        adoption_probe_reasons.append("report_terminal_truth_class_mismatch")

    instance_adoption_terminal_truth_probe_status = (
        STATUS_FAIL_REQUIRED if adoption_probe_reasons else STATUS_PASS_REQUIRED
    )

    top_level_ok = (
        execution_closure_status == STATUS_PASS_REQUIRED
        and terminal_truth_cleanliness_status == STATUS_PASS_REQUIRED
        and negative_feedback_terminal_veto_status == STATUS_PASS_REQUIRED
        and canonical_publishable_result_status == STATUS_PASS_REQUIRED
        and instance_adoption_terminal_truth_probe_status == STATUS_PASS_REQUIRED
    )

    stale_reasons: list[str] = []
    if execution_closure_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("execution_closure_not_reached_or_supporting_validator_red")
    if negative_feedback_terminal_veto_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("negative_feedback_veto_projection_invalid")
    if terminal_truth_cleanliness_status != STATUS_PASS_REQUIRED:
        stale_reasons.extend(publish_blockers)
    stale_reasons.extend(adoption_probe_reasons)

    return {
        "identity_terminal_truth_cleanliness_status": STATUS_PASS_REQUIRED if top_level_ok else STATUS_FAIL_REQUIRED,
        "execution_closure_status": execution_closure_status,
        "terminal_truth_cleanliness_status": terminal_truth_cleanliness_status,
        "terminal_truth_class": terminal_truth_class,
        "is_terminal_clean": is_terminal_clean,
        "is_terminal_dirty": is_terminal_dirty,
        "terminal_truth_basis": basis,
        "terminal_truth_blockers": publish_blockers,
        "negative_feedback_terminal_veto_status": negative_feedback_terminal_veto_status,
        "negative_feedback_class": negative_feedback_class,
        "feedback_severity": feedback_severity,
        "terminal_veto_required": terminal_veto_required,
        "terminal_veto_scope": terminal_veto_scope,
        "loopback_required": loopback_required,
        "loopback_target_stage": loopback_target_stage,
        "loopback_reason": loopback_reason,
        "pre_terminal_veto_applied": pre_terminal_veto_applied,
        "next_state_after_veto": next_state_after_veto,
        "canonical_publishable_result_status": canonical_publishable_result_status,
        "publishable": publishable,
        "publish_blockers": publish_blockers,
        "canonical_result_eligible": canonical_result_eligible,
        "canonical_result_basis": "clean_terminal_truth_required_for_publishability",
        "requires_repair_before_publish": not publishable,
        "instance_adoption_terminal_truth_probe_status": instance_adoption_terminal_truth_probe_status,
        "stale_reasons": sorted(set(stale_reasons)),
        "placeholder_result_fields": placeholder_hits,
        "contradiction_fields": contradiction_hits,
        "confidence_blocker_fields": confidence_hits,
        "dirty_signals": dirty_signals,
    }


def project_terminal_truth_fields(
    report_doc: dict[str, Any],
    *,
    post_execution_status: str = "",
    writeback_continuity_status: str = "",
) -> dict[str, Any]:
    projected = derive_terminal_truth_projection(
        report_doc,
        post_execution_status=post_execution_status,
        writeback_continuity_status=writeback_continuity_status,
    )
    merged = dict(report_doc or {})
    merged.update(projected)
    merged.update(derive_terminal_state_projection(merged, terminal_truth_projection=projected))
    return merged
