#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

GOVERNED_ANSWER_BRIDGE_ADMISSION_CONTRACT_ID = "governed_answer_bridge_admission_contract_v1"


def clean_bridge_token(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def build_governed_answer_bridge_admission_contract(
    *,
    consumer_stream: str,
    owner_stream: str,
    question_family: str,
) -> dict[str, Any]:
    return {
        "contract_id": GOVERNED_ANSWER_BRIDGE_ADMISSION_CONTRACT_ID,
        "consumer_stream": clean_bridge_token(consumer_stream),
        "owner_stream": clean_bridge_token(owner_stream),
        "question_family": clean_bridge_token(question_family),
        "owner_bundle_status_pass_required_for_bridge_integrity": True,
        "owner_stream_exact_match_required": True,
        "question_family_exact_match_required": True,
        "consumer_default_injection_forbidden": True,
        "bridge_integrity_not_equal_owner_answer_status": True,
        "owner_answer_status_not_equal_operator_projection": True,
    }


def evaluate_governed_answer_bridge_admission(
    bundle: dict[str, Any],
    *,
    expected_consumer_stream: str,
    expected_owner_stream: str,
    expected_question_family: str,
    bundle_status_key: str = "identity_context_reentry_answer_bundle_status",
    owner_stream_key: str = "continuity_owner_stream",
    question_family_key: str = "question_family",
    contract_key: str = "bridge_admission_contract",
) -> dict[str, Any]:
    owner_bundle_status_value = clean_bridge_token(bundle.get(bundle_status_key)) or STATUS_FAIL_REQUIRED
    owner_stream_value = clean_bridge_token(bundle.get(owner_stream_key))
    question_family_value = clean_bridge_token(bundle.get(question_family_key))

    owner_bundle_status = (
        STATUS_PASS_REQUIRED
        if owner_bundle_status_value == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    owner_stream_status = (
        STATUS_PASS_REQUIRED
        if owner_stream_value == clean_bridge_token(expected_owner_stream)
        else STATUS_FAIL_REQUIRED
    )
    question_family_status = (
        STATUS_PASS_REQUIRED
        if question_family_value == clean_bridge_token(expected_question_family)
        else STATUS_FAIL_REQUIRED
    )

    contract = bundle.get(contract_key)
    contract_status = STATUS_FAIL_REQUIRED
    contract_reason = "continuity_intent_bridge_contract_missing"
    if isinstance(contract, dict):
        expected_contract = build_governed_answer_bridge_admission_contract(
            consumer_stream=expected_consumer_stream,
            owner_stream=expected_owner_stream,
            question_family=expected_question_family,
        )
        mismatched_fields = [
            key
            for key, expected_value in expected_contract.items()
            if contract.get(key) != expected_value
        ]
        if mismatched_fields:
            contract_reason = (
                "continuity_intent_bridge_contract_mismatch:" + ",".join(sorted(mismatched_fields))
            )
        else:
            contract_status = STATUS_PASS_REQUIRED
            contract_reason = "continuity_intent_bridge_contract_admitted"

    if owner_bundle_status != STATUS_PASS_REQUIRED:
        bridge_status = STATUS_FAIL_REQUIRED
        bridge_reason = "continuity_intent_owner_bundle_status_not_pass_required"
    elif owner_stream_status != STATUS_PASS_REQUIRED:
        bridge_status = STATUS_FAIL_REQUIRED
        bridge_reason = "continuity_intent_owner_stream_mismatch"
    elif question_family_status != STATUS_PASS_REQUIRED:
        bridge_status = STATUS_FAIL_REQUIRED
        bridge_reason = "continuity_intent_question_family_mismatch"
    elif contract_status != STATUS_PASS_REQUIRED:
        bridge_status = STATUS_FAIL_REQUIRED
        bridge_reason = contract_reason
    else:
        bridge_status = STATUS_PASS_REQUIRED
        bridge_reason = "continuity_intent_bridge_contract_admitted"

    return {
        "owner_bundle_status_value": owner_bundle_status_value,
        "owner_bundle_status": owner_bundle_status,
        "owner_stream_value": owner_stream_value,
        "owner_stream_status": owner_stream_status,
        "question_family_value": question_family_value,
        "question_family_status": question_family_status,
        "bridge_contract": contract if isinstance(contract, dict) else {},
        "bridge_contract_status": contract_status,
        "bridge_contract_reason": contract_reason,
        "bridge_status": bridge_status,
        "bridge_reason": bridge_reason,
    }
