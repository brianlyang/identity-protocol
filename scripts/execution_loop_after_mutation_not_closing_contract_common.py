from __future__ import annotations

from copy import deepcopy


CANDIDATE_ID = "execution_loop_after_mutation_not_closing_candidate"
FAIL_CLOSE_REASON = "execution_loop_after_mutation_not_closing"
GOVERNING_LAW = (
    "once mutation_phase_entry_status=ENTERED, staged paths are present, or "
    "validator/probe/targeted-regression evidence exists, allowed_next_actions "
    "collapse exactly to {run_validator, run_probe, stage_and_commit, "
    "emit_blocker_receipt, emit_fail_close_token}; reread/recap/re-anchor/"
    "whole-family reinspection/reassurance browsing are not admitted and must "
    "fail-close as execution_loop_after_mutation_not_closing"
)
ALLOWED_NEXT_ACTIONS = (
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token",
)
FORBIDDEN_POST_MUTATION_ACTIONS = (
    "reread",
    "recap",
    "re-anchor",
    "whole-family reinspection",
    "reassurance browsing",
)
REQUIRED_FIELDS = (
    "candidate_id",
    "governing_law",
    "mutation_phase_entry_status",
    "staged_paths_status",
    "validation_evidence_status",
    "allowed_next_actions",
    "forbidden_post_mutation_actions",
    "fail_close_reason",
)


def build_contract_payload() -> dict:
    return {
        "candidate_id": CANDIDATE_ID,
        "governing_law": GOVERNING_LAW,
        "mutation_phase_entry_status": "ENTERED",
        "staged_paths_status": "ABSENT",
        "validation_evidence_status": "ABSENT",
        "allowed_next_actions": list(ALLOWED_NEXT_ACTIONS),
        "forbidden_post_mutation_actions": list(FORBIDDEN_POST_MUTATION_ACTIONS),
        "attempted_post_mutation_action": None,
        "fail_close_reason": FAIL_CLOSE_REASON,
    }


def build_targeted_regression_payload(name: str) -> dict:
    payload = build_contract_payload()
    if name == "mutation_entered_closeout_only":
        payload["mutation_phase_entry_status"] = "ENTERED"
        payload["staged_paths_status"] = "ABSENT"
        payload["validation_evidence_status"] = "ABSENT"
        return payload
    raise ValueError(f"unsupported targeted regression: {name}")


def _has_required_post_mutation_trigger(payload: dict) -> bool:
    return any(
        (
            payload.get("mutation_phase_entry_status") == "ENTERED",
            payload.get("staged_paths_status") == "PRESENT",
            payload.get("validation_evidence_status") == "PRESENT",
        )
    )


def validate_contract_payload(payload: dict) -> list[str]:
    stale_reasons: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in payload:
            stale_reasons.append(f"missing_required_field:{field}")

    if stale_reasons:
        return stale_reasons

    if payload.get("candidate_id") != CANDIDATE_ID:
        stale_reasons.append("candidate_id_not_canonical")
    if payload.get("governing_law") != GOVERNING_LAW:
        stale_reasons.append("governing_law_not_canonical")
    if payload.get("fail_close_reason") != FAIL_CLOSE_REASON:
        stale_reasons.append("fail_close_reason_not_canonical")

    if not _has_required_post_mutation_trigger(payload):
        stale_reasons.append("post_mutation_trigger_not_materialized")

    if list(payload.get("allowed_next_actions", [])) != list(ALLOWED_NEXT_ACTIONS):
        stale_reasons.append("allowed_next_actions_not_collapsed_after_mutation")

    if list(payload.get("forbidden_post_mutation_actions", [])) != list(
        FORBIDDEN_POST_MUTATION_ACTIONS
    ):
        stale_reasons.append("forbidden_post_mutation_actions_not_canonical")

    attempted = payload.get("attempted_post_mutation_action")
    if attempted in FORBIDDEN_POST_MUTATION_ACTIONS:
        stale_reasons.append(FAIL_CLOSE_REASON)

    return stale_reasons


def build_validation_result(payload: dict, mode: str) -> dict:
    result = deepcopy(payload)
    stale_reasons = validate_contract_payload(payload)
    result.update(
        {
            "mode": mode,
            "status": "PASS_REQUIRED" if not stale_reasons else "FAIL_REQUIRED",
            "stale_reasons": stale_reasons,
            "allowed_next_actions": list(ALLOWED_NEXT_ACTIONS),
            "forbidden_post_mutation_actions": list(FORBIDDEN_POST_MUTATION_ACTIONS),
            "fail_close_reason": FAIL_CLOSE_REASON,
        }
    )
    return result
