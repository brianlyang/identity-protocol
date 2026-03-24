#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from feedback_current_run_binding_common import derive_feedback_current_run_binding_projection

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_FEEDBACK_TO_JUDGEMENT_LOOPBACK_INVALID = "IP-RLSTR-002"

EXPECTED_ACCURATE_JUDGEMENT_CONTRACT_REF = "rq_034_multimodal_plugin_enforcement_contract_v1"
EXPECTED_ACCURATE_JUDGEMENT_VALIDATOR = "scripts/validate_multimodal_plugin_enforcement.py"
EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_CONTRACT_REF = "feedback_operational_prompt_contract_v1"
EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_VALIDATOR = "scripts/validate_identity_experience_feedback_governance.py"
EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_SUPPORTING_VALIDATORS: tuple[str, ...] = (
    "scripts/validate_identity_experience_feedback.py",
)

LOOPBACK_ARTIFACT_KIND_OPERATIONAL_PROMPT = "operational_prompt"
LOOPBACK_SCOPE_NEXT_ROUND_PREFLIGHT_ONLY = "next_round_preflight_only"
JUDGEMENT_REENTRY_STATUS_FIRST_LOOP_REVALIDATION_REQUIRED = "first_loop_revalidation_required"
ADOPTION_DECISION_FIRST_LOOP_REVALIDATE_BEFORE_ADOPT = "first_loop_revalidate_before_adopt"
CONFLICT_WITH_CURRENT_EVIDENCE_DEMOTE_OR_ROLLBACK_REQUIRED = "demote_or_rollback_required"
DEMOTION_OR_ROLLBACK_ACTION_ROLLBACK_PROMPT_REF_AND_NEGATIVE_FEEDBACK_WRITEBACK = (
    "rollback_prompt_ref_and_negative_feedback_writeback"
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = _clean_str(item)
        if token:
            out.append(token)
    return out


def _dotted_ref(*parts: str) -> str:
    tokens = [token for token in (_clean_str(part) for part in parts) if token]
    return ".".join(tokens)


def _normalize_status(value: Any, *, default: str = STATUS_SKIPPED_NOT_REQUIRED) -> str:
    token = _clean_str(value).upper()
    if token in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED}:
        return token
    return default


def derive_live_roundtrip_projection(
    *,
    third_loop_exploration_status: str,
    loopback_projection: dict[str, Any],
) -> dict[str, str]:
    overall_loopback_status = _normalize_status(
        loopback_projection.get("feedback_to_judgement_loopback_status"),
        default=STATUS_SKIPPED_NOT_REQUIRED,
    )
    third_status = _normalize_status(third_loop_exploration_status)
    fourth_status = _normalize_status(
        loopback_projection.get("fourth_loop_promotion_status"),
        default=overall_loopback_status,
    )
    first_status = _normalize_status(
        loopback_projection.get("first_loop_revalidation_status"),
        default=_normalize_status(loopback_projection.get("loop_back_to_first_loop_status"), default=overall_loopback_status),
    )
    conflict_status = _normalize_status(
        loopback_projection.get("conflict_demotion_status"),
        default=overall_loopback_status,
    )
    negative_feedback_status = _normalize_status(
        loopback_projection.get("negative_feedback_writeback_status"),
        default=overall_loopback_status,
    )
    loopback_roundtrip_status = _normalize_status(
        loopback_projection.get("loopback_roundtrip_status"),
        default=overall_loopback_status,
    )
    roundtrip_components = (
        third_status,
        fourth_status,
        first_status,
        conflict_status,
        negative_feedback_status,
        loopback_roundtrip_status,
    )
    if any(status == STATUS_FAIL_REQUIRED for status in roundtrip_components):
        live_roundtrip_proof_status = STATUS_FAIL_REQUIRED
    elif any(status == STATUS_PASS_REQUIRED for status in roundtrip_components):
        live_roundtrip_proof_status = STATUS_PASS_REQUIRED
    else:
        live_roundtrip_proof_status = STATUS_SKIPPED_NOT_REQUIRED

    return {
        "third_loop_exploration_status": third_status,
        "fourth_loop_promotion_status": fourth_status,
        "first_loop_revalidation_status": first_status,
        "conflict_demotion_status": conflict_status,
        "negative_feedback_writeback_status": negative_feedback_status,
        "loopback_roundtrip_status": loopback_roundtrip_status,
        "live_roundtrip_proof_status": live_roundtrip_proof_status,
    }


def inspect_feedback_to_judgement_loopback(
    *,
    task_doc: dict[str, Any],
    identity_id: str,
    task_path: str = "",
) -> dict[str, Any]:
    arbitration = task_doc.get("capability_arbitration_contract") or {}
    feedback = task_doc.get("experience_feedback_contract") or {}
    judgement = arbitration.get("accurate_judgement_enforcement") if isinstance(arbitration, dict) else {}
    prompt = arbitration.get("feedback_operational_prompt_enforcement") if isinstance(arbitration, dict) else {}

    required_contract = (
        isinstance(arbitration, dict)
        and arbitration.get("required") is True
        and isinstance(feedback, dict)
        and feedback.get("required") is True
    )

    base_payload = {
        "identity_id": _clean_str(identity_id),
        "task_path": _clean_str(task_path),
        "required_contract": bool(required_contract),
        "loopback_artifact_ref": "",
        "loopback_artifact_kind": "",
        "preflight_context_injection_ref": "",
        "loopback_scope": "",
        "loopback_ttl_rounds": "",
        "first_loop_revalidation_required": False,
        "judgement_reentry_status": "",
        "adoption_decision": "",
        "conflict_with_current_evidence": "",
        "demotion_or_rollback_action": "",
        "negative_feedback_ref": "",
        "loop_back_to_first_loop_status": STATUS_SKIPPED_NOT_REQUIRED,
        "stale_reasons": [],
        "error_code": "",
    }
    if not required_contract:
        return {
            "feedback_to_judgement_loopback_status": STATUS_SKIPPED_NOT_REQUIRED,
            **base_payload,
        }

    stale_reasons: list[str] = []
    promotion_reasons: list[str] = []
    revalidation_reasons: list[str] = []
    conflict_reasons: list[str] = []
    negative_feedback_reasons: list[str] = []

    if not isinstance(judgement, dict) or not judgement:
        stale_reasons.append("accurate_judgement_enforcement_missing")
        revalidation_reasons.append("accurate_judgement_enforcement_missing")
    else:
        if _clean_str(judgement.get("contract_ref")) != EXPECTED_ACCURATE_JUDGEMENT_CONTRACT_REF:
            stale_reasons.append("accurate_judgement_enforcement_contract_ref_mismatch")
            revalidation_reasons.append("accurate_judgement_enforcement_contract_ref_mismatch")
        if _clean_str(judgement.get("validator")) != EXPECTED_ACCURATE_JUDGEMENT_VALIDATOR:
            stale_reasons.append("accurate_judgement_enforcement_validator_mismatch")
            revalidation_reasons.append("accurate_judgement_enforcement_validator_mismatch")
        if judgement.get("requires_multimodal_evidence_consistency") is not True:
            stale_reasons.append("accurate_judgement_enforcement_requires_multimodal_evidence_consistency_false")
            revalidation_reasons.append("accurate_judgement_enforcement_requires_multimodal_evidence_consistency_false")
        if _clean_str(judgement.get("inconsistent_evidence_transition")) != "block_done":
            stale_reasons.append("accurate_judgement_enforcement_inconsistent_evidence_transition_invalid")
            revalidation_reasons.append("accurate_judgement_enforcement_inconsistent_evidence_transition_invalid")

    if not isinstance(prompt, dict) or not prompt:
        stale_reasons.append("feedback_operational_prompt_enforcement_missing")
        promotion_reasons.append("feedback_operational_prompt_enforcement_missing")
        operational_prompt_field = ""
        prompt_injection_field = ""
        replay_status_field = ""
    else:
        if _clean_str(prompt.get("contract_ref")) != EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_CONTRACT_REF:
            stale_reasons.append("feedback_operational_prompt_enforcement_contract_ref_mismatch")
            promotion_reasons.append("feedback_operational_prompt_enforcement_contract_ref_mismatch")
        if _clean_str(prompt.get("validator")) != EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_VALIDATOR:
            stale_reasons.append("feedback_operational_prompt_enforcement_validator_mismatch")
            promotion_reasons.append("feedback_operational_prompt_enforcement_validator_mismatch")
        supporting = set(_as_list(prompt.get("supporting_validators")))
        missing_supporting = set(EXPECTED_FEEDBACK_OPERATIONAL_PROMPT_SUPPORTING_VALIDATORS) - supporting
        if missing_supporting:
            stale_reasons.append("feedback_operational_prompt_enforcement_supporting_validators_missing")
            promotion_reasons.append("feedback_operational_prompt_enforcement_supporting_validators_missing")
        if prompt.get("rulebook_delta_required") is not True:
            stale_reasons.append("feedback_operational_prompt_enforcement_rulebook_delta_required_false")
            promotion_reasons.append("feedback_operational_prompt_enforcement_rulebook_delta_required_false")
        if prompt.get("rollback_prompt_ref_required") is not True:
            stale_reasons.append("feedback_operational_prompt_enforcement_rollback_prompt_ref_required_false")
            promotion_reasons.append("feedback_operational_prompt_enforcement_rollback_prompt_ref_required_false")
        if prompt.get("ttl_rounds_required") is not True:
            stale_reasons.append("feedback_operational_prompt_enforcement_ttl_rounds_required_false")
            promotion_reasons.append("feedback_operational_prompt_enforcement_ttl_rounds_required_false")
        operational_prompt_field = _clean_str(prompt.get("operational_prompt_ref_field"))
        prompt_injection_field = _clean_str(prompt.get("prompt_injection_status_field"))
        replay_status_field = _clean_str(prompt.get("replay_status_field"))
        if not operational_prompt_field:
            stale_reasons.append("feedback_operational_prompt_enforcement_operational_prompt_ref_field_missing")
            promotion_reasons.append("feedback_operational_prompt_ref_missing")
        if not prompt_injection_field:
            stale_reasons.append("feedback_operational_prompt_enforcement_prompt_injection_status_field_missing")
            promotion_reasons.append("feedback_prompt_injection_status_field_missing")
        if not replay_status_field:
            stale_reasons.append("feedback_operational_prompt_enforcement_replay_status_field_missing")
            promotion_reasons.append("feedback_replay_status_field_missing")

    if not isinstance(feedback, dict) or not feedback:
        stale_reasons.append("experience_feedback_contract_missing")
        promotion_reasons.append("experience_feedback_contract_missing")
        negative_feedback_reasons.append("experience_feedback_contract_missing")
    else:
        replay_gate = feedback.get("promote_requires_replay_pass")
        if replay_gate is None:
            replay_gate = feedback.get("promotion_requires_replay_pass")
        if replay_gate is not True:
            stale_reasons.append("experience_feedback_contract_replay_gate_false")
            promotion_reasons.append("experience_feedback_contract_replay_gate_false")

        negative_rulebook_path = _clean_str(feedback.get("negative_rulebook_path"))
        if not negative_rulebook_path:
            stale_reasons.append("experience_feedback_contract_negative_rulebook_path_missing")
            negative_feedback_reasons.append("experience_feedback_contract_negative_rulebook_path_missing")

        cross_layer_feedback_targets = set(_as_list(feedback.get("cross_layer_feedback_targets")))
        if "gates" not in cross_layer_feedback_targets:
            stale_reasons.append("experience_feedback_contract_cross_layer_feedback_targets_missing_gates")
            negative_feedback_reasons.append("experience_feedback_contract_cross_layer_feedback_targets_missing_gates")

        required_fields = set(_as_list(feedback.get("required_fields")))
        if "replay_status" not in required_fields:
            stale_reasons.append("experience_feedback_contract_required_fields_missing_replay_status")
            negative_feedback_reasons.append("experience_feedback_contract_required_fields_missing_replay_status")

    overall_status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    loopback_artifact_ref = _dotted_ref("experience_feedback_contract", operational_prompt_field)
    loopback_ttl_rounds = _dotted_ref("experience_feedback_contract", "ttl_rounds")
    negative_feedback_ref = _clean_str((feedback or {}).get("negative_rulebook_path"))
    if not loopback_artifact_ref:
        promotion_reasons.append("loopback_artifact_ref_missing")
    if not loopback_ttl_rounds:
        promotion_reasons.append("loopback_ttl_rounds_missing")
    first_loop_revalidation_required = True
    judgement_reentry_status = JUDGEMENT_REENTRY_STATUS_FIRST_LOOP_REVALIDATION_REQUIRED
    adoption_decision = ADOPTION_DECISION_FIRST_LOOP_REVALIDATE_BEFORE_ADOPT
    conflict_with_current_evidence = CONFLICT_WITH_CURRENT_EVIDENCE_DEMOTE_OR_ROLLBACK_REQUIRED
    demotion_or_rollback_action = DEMOTION_OR_ROLLBACK_ACTION_ROLLBACK_PROMPT_REF_AND_NEGATIVE_FEEDBACK_WRITEBACK
    if not first_loop_revalidation_required:
        revalidation_reasons.append("first_loop_revalidation_required_false")
    if judgement_reentry_status != JUDGEMENT_REENTRY_STATUS_FIRST_LOOP_REVALIDATION_REQUIRED:
        revalidation_reasons.append("judgement_reentry_status_invalid")
    if adoption_decision != ADOPTION_DECISION_FIRST_LOOP_REVALIDATE_BEFORE_ADOPT:
        revalidation_reasons.append("adoption_decision_invalid")
    if conflict_with_current_evidence != CONFLICT_WITH_CURRENT_EVIDENCE_DEMOTE_OR_ROLLBACK_REQUIRED:
        conflict_reasons.append("conflict_with_current_evidence_invalid")
    if demotion_or_rollback_action != DEMOTION_OR_ROLLBACK_ACTION_ROLLBACK_PROMPT_REF_AND_NEGATIVE_FEEDBACK_WRITEBACK:
        conflict_reasons.append("demotion_or_rollback_action_invalid")

    fourth_loop_promotion_status = STATUS_PASS_REQUIRED if not promotion_reasons else STATUS_FAIL_REQUIRED
    first_loop_revalidation_status = STATUS_PASS_REQUIRED if not revalidation_reasons else STATUS_FAIL_REQUIRED
    conflict_demotion_status = STATUS_PASS_REQUIRED if not conflict_reasons else STATUS_FAIL_REQUIRED
    negative_feedback_writeback_status = (
        STATUS_PASS_REQUIRED if not negative_feedback_reasons else STATUS_FAIL_REQUIRED
    )
    loopback_roundtrip_status = (
        STATUS_PASS_REQUIRED
        if all(
            status == STATUS_PASS_REQUIRED
            for status in (
                fourth_loop_promotion_status,
                first_loop_revalidation_status,
                conflict_demotion_status,
                negative_feedback_writeback_status,
            )
        )
        else STATUS_FAIL_REQUIRED
    )
    payload = {
        "feedback_to_judgement_loopback_status": overall_status,
        **base_payload,
        "loopback_artifact_ref": loopback_artifact_ref,
        "loopback_artifact_kind": LOOPBACK_ARTIFACT_KIND_OPERATIONAL_PROMPT,
        "preflight_context_injection_ref": loopback_artifact_ref,
        "loopback_scope": LOOPBACK_SCOPE_NEXT_ROUND_PREFLIGHT_ONLY,
        "loopback_ttl_rounds": loopback_ttl_rounds,
        "first_loop_revalidation_required": first_loop_revalidation_required,
        "judgement_reentry_status": judgement_reentry_status,
        "adoption_decision": adoption_decision,
        "conflict_with_current_evidence": conflict_with_current_evidence,
        "demotion_or_rollback_action": demotion_or_rollback_action,
        "negative_feedback_ref": negative_feedback_ref,
        "fourth_loop_promotion_status": fourth_loop_promotion_status,
        "fourth_loop_promotion_reasons": promotion_reasons,
        "first_loop_revalidation_status": first_loop_revalidation_status,
        "first_loop_revalidation_reasons": revalidation_reasons,
        "conflict_demotion_status": conflict_demotion_status,
        "conflict_demotion_reasons": conflict_reasons,
        "negative_feedback_writeback_status": negative_feedback_writeback_status,
        "negative_feedback_writeback_reasons": negative_feedback_reasons,
        "loopback_roundtrip_status": loopback_roundtrip_status,
        "loop_back_to_first_loop_status": overall_status,
        "stale_reasons": stale_reasons,
        "error_code": "" if overall_status != STATUS_FAIL_REQUIRED else ERR_FEEDBACK_TO_JUDGEMENT_LOOPBACK_INVALID,
    }
    feedback_live_projection: dict[str, Any] = {}
    task_token = _clean_str(task_path)
    if task_token:
        feedback_live_projection = derive_feedback_current_run_binding_projection(
            pack_root=Path(task_token).expanduser().resolve().parent,
            identity_id=_clean_str(identity_id),
            contract_doc=feedback if isinstance(feedback, dict) else {},
        )
    else:
        feedback_live_projection = {
            "required_run_id": "",
            "current_run_pointer": "",
            "current_run_report_path": "",
            "latest_feedback_log": "",
            "latest_feedback_log_age_days": None,
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_run_id": "",
            "latest_feedback_run_id_match_status": STATUS_FAIL_REQUIRED,
            "latest_feedback_same_run_binding_status": STATUS_FAIL_REQUIRED,
            "operational_prompt_receipt_ref": "",
            "operational_prompt_run_join_status": STATUS_FAIL_REQUIRED,
            "feedback_run_id": "",
            "preflight_reentry_receipt_ref": "",
            "loopback_live_binding_status": STATUS_FAIL_REQUIRED,
            "feedback_replay_status": "",
            "evidence_origin": "missing",
            "stale_reasons": ["task_path_missing_for_feedback_live_projection"],
        }
    payload.update(
        {
            "operational_prompt_receipt_ref": _clean_str(feedback_live_projection.get("operational_prompt_receipt_ref")),
            "feedback_run_id": _clean_str(feedback_live_projection.get("feedback_run_id")),
            "preflight_reentry_receipt_ref": _clean_str(feedback_live_projection.get("preflight_reentry_receipt_ref")),
            "loopback_live_binding_status": _normalize_status(
                feedback_live_projection.get("loopback_live_binding_status"),
                default=STATUS_FAIL_REQUIRED,
            ),
            "latest_feedback_run_id_match_status": _normalize_status(
                feedback_live_projection.get("latest_feedback_run_id_match_status"),
                default=STATUS_FAIL_REQUIRED,
            ),
            "operational_prompt_run_join_status": _normalize_status(
                feedback_live_projection.get("operational_prompt_run_join_status"),
                default=STATUS_FAIL_REQUIRED,
            ),
            "loopback_live_binding_reasons": [
                _clean_str(reason)
                for reason in (feedback_live_projection.get("stale_reasons") or [])
                if _clean_str(reason)
            ],
        }
    )
    return payload
