#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

import host_visible_native_attestation_projection_common as common


def _check_file_tokens(label: str, relative_path: str, tokens: tuple[str, ...], env_var: str | None = None) -> list[str]:
    try:
        text = common.read_text(relative_path, env_var=env_var)
    except FileNotFoundError:
        return [f"{label}_missing:{relative_path}"]
    missing = common.contains_all_tokens(text, tokens)
    return [f"{label}_missing_token:{token}" for token in missing]


def _check_evidence_log() -> list[str]:
    try:
        text = common.read_text(common.EVIDENCE_LOG, env_var="HVNAP_EVIDENCE_PATH")
    except FileNotFoundError:
        return [f"evidence_log_missing:{common.EVIDENCE_LOG}"]

    failures: list[str] = []
    for alternatives in common.EVIDENCE_LOG_ANCHOR_GROUPS:
        if not any(token in text for token in alternatives):
            failures.append(f"evidence_log_missing_token:{alternatives[0]}")
    return failures


def validate() -> dict:
    failures: list[str] = []
    checks: list[str] = []

    for relative_path in common.FIXED_WRITE_SET:
        path = common.repo_path(relative_path)
        if not path.exists():
            failures.append(f"fixed_write_set_missing:{relative_path}")
        else:
            checks.append(f"fixed_write_set_present:{relative_path}")

    failures.extend(
        _check_file_tokens(
            "governance",
            common.FIXED_WRITE_SET[0],
            common.governance_required_tokens(),
            env_var="HVNAP_GOVERNANCE_PATH",
        )
    )
    if not any(item.startswith("governance_missing") for item in failures):
        checks.append("governance_tokens_aligned")

    failures.extend(
        _check_file_tokens(
            "review",
            common.FIXED_WRITE_SET[1],
            common.review_required_tokens(),
            env_var="HVNAP_REVIEW_PATH",
        )
    )
    if not any(item.startswith("review_missing") for item in failures):
        checks.append("review_tokens_aligned")

    for relative_path, tokens in common.READ_ONLY_MINIMUM_TOKENS.items():
        failures.extend(_check_file_tokens("read_only_surface", relative_path, tokens))
    if not any(item.startswith("read_only_surface_missing") for item in failures):
        checks.append("read_only_surface_projection_tokens_present")

    failures.extend(_check_evidence_log())
    if not any(item.startswith("evidence_log_missing") for item in failures):
        checks.append("evidence_log_anchors_present")

    failures = sorted(set(failures))
    status = "PASS" if not failures else "FAIL"
    return {
        "family_id": common.FAMILY_ID,
        "classification": common.CLASSIFICATION,
        "status": status,
        "checks": checks,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    result = validate()
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True)
    if args.json_only:
        print(payload)
    else:
        print(payload)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
