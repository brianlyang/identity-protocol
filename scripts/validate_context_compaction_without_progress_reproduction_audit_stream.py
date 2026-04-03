#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context_compaction_without_progress_reproduction_audit_stream_contract_common import (
    ALLOWED_AUDIT_OUTCOMES,
    CLASSIFICATION,
    DOC_EXPECTATIONS,
    FAIL_CLOSE_REASON,
    FAIL_REQUIRED,
    FIXED_WRITE_SET,
    READ_ONLY_INPUT_EXPECTATIONS,
    READ_ONLY_INPUT_SURFACES,
    REQUIRED_MACHINE_FIELDS,
    STREAM_ID,
    PASS_REQUIRED,
    canonical_payload,
    default_machine_state,
    repo_root,
)


def _missing_tokens(path: Path, tokens: tuple[str, ...]) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [token for token in tokens if token not in content]


def validate(root: Path) -> dict[str, object]:
    stale_reasons: list[str] = []

    for relative_path in FIXED_WRITE_SET:
        path = root / relative_path
        if not path.exists():
            stale_reasons.append(f"missing_fixed_write_path:{relative_path}")

    for relative_path in READ_ONLY_INPUT_SURFACES:
        path = root / relative_path
        if not path.exists():
            stale_reasons.append(f"missing_read_only_input:{relative_path}")

    for relative_path, tokens in DOC_EXPECTATIONS.items():
        path = root / relative_path
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            stale_reasons.append(f"missing_token:{relative_path}:{token}")

    for relative_path, tokens in READ_ONLY_INPUT_EXPECTATIONS.items():
        path = root / relative_path
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            stale_reasons.append(f"missing_read_only_token:{relative_path}:{token}")

    payload = canonical_payload()
    if payload.get("stream_id") != STREAM_ID:
        stale_reasons.append("stream_id_drift")
    if payload.get("classification") != CLASSIFICATION:
        stale_reasons.append("classification_drift")
    if payload.get("fixed_write_set") != list(FIXED_WRITE_SET):
        stale_reasons.append("fixed_write_set_drift")
    if payload.get("read_only_input_surfaces") != list(READ_ONLY_INPUT_SURFACES):
        stale_reasons.append("read_only_input_surface_drift")
    if payload.get("allowed_audit_outcomes") != list(ALLOWED_AUDIT_OUTCOMES):
        stale_reasons.append("allowed_audit_outcomes_drift")

    machine_state = default_machine_state()
    for field in REQUIRED_MACHINE_FIELDS:
        if field not in machine_state:
            stale_reasons.append(f"missing_machine_field:{field}")
    if machine_state.get("stream_mode") != "READ_ONLY":
        stale_reasons.append("stream_mode_drift")
    if machine_state.get("coverage_classification_status") != "CURRENTLY_COVERED_BY_ISSUE_045_AND_046":
        stale_reasons.append("coverage_classification_drift")
    if machine_state.get("protocol_feedback_mixing_status") != "NOT_ADMITTED":
        stale_reasons.append("protocol_feedback_mixing_drift")
    if machine_state.get("identity_binding_mixing_status") != "NOT_ADMITTED":
        stale_reasons.append("identity_binding_mixing_drift")

    ok = not stale_reasons
    return {
        "ok": ok,
        "status": PASS_REQUIRED if ok else FAIL_REQUIRED,
        "stream_id": STREAM_ID,
        "classification": CLASSIFICATION,
        "mode": "read_only_residual_reproduction_audit_stream_ready" if ok else FAIL_CLOSE_REASON,
        "checked_file_count": len(FIXED_WRITE_SET),
        "read_only_input_surface_count": len(READ_ONLY_INPUT_SURFACES),
        "allowed_audit_outcomes": list(ALLOWED_AUDIT_OUTCOMES),
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "stale_reasons": stale_reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    result = validate(repo_root(args.root))
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
