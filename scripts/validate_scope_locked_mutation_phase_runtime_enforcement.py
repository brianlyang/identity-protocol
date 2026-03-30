#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scope_locked_mutation_phase_runtime_enforcement_contract_common import (
    ALLOWED_NEXT_ACTIONS,
    BRIDGED_GUARD_FIELDS,
    DOC_EXPECTATIONS,
    FAIL_CLOSE_REASON,
    FAIL_CLOSE_REASON_FAMILY,
    FAIL_REQUIRED,
    FIXED_WRITE_SET,
    ISSUE_ID,
    LANE_ID,
    PASS_REQUIRED,
    REQUIRED_MACHINE_FIELDS,
    SCRIPT_EXPECTATIONS,
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

    for relative_path, tokens in DOC_EXPECTATIONS.items():
        path = root / relative_path
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            if token == "reply-envelope gate":
                stale_reasons.append("reply_envelope_not_admitted")
            elif token in FAIL_CLOSE_REASON_FAMILY:
                stale_reasons.append(token)
            elif token == "emit_fail_close_token":
                stale_reasons.append("mutation_required_but_not_entered")
            else:
                stale_reasons.append(f"missing_token:{relative_path}:{token}")

    for relative_path, tokens in SCRIPT_EXPECTATIONS.items():
        path = root / relative_path
        if not path.exists():
            continue
        for token in _missing_tokens(path, tokens):
            if token in FAIL_CLOSE_REASON_FAMILY:
                stale_reasons.append(token)
            elif token == "reply_envelope_not_admitted":
                stale_reasons.append("reply_envelope_not_admitted")
            else:
                stale_reasons.append(f"missing_token:{relative_path}:{token}")

    payload = canonical_payload()
    if payload.get("fixed_write_set") != list(FIXED_WRITE_SET):
        stale_reasons.append("tool_use_outside_fixed_write_set_after_lock")
    if payload.get("allowed_next_actions") != list(ALLOWED_NEXT_ACTIONS):
        stale_reasons.append("mutation_required_but_not_entered")

    machine_state = default_machine_state()
    for field in REQUIRED_MACHINE_FIELDS:
        if field not in machine_state:
            stale_reasons.append(f"missing_machine_field:{field}")
    for field in BRIDGED_GUARD_FIELDS:
        if field not in machine_state:
            stale_reasons.append(f"missing_guard_field:{field}")
    if machine_state.get("allowed_next_actions") != list(ALLOWED_NEXT_ACTIONS):
        stale_reasons.append("mutation_required_but_not_entered")
    if machine_state.get("reply_envelope_status") != "LOCKED_TO_RUNTIME_RECEIPTS":
        stale_reasons.append("reply_envelope_not_admitted")
    if machine_state.get("runtime_guard_status") != "ENFORCED":
        stale_reasons.append("scope_locked_reread_not_admitted")
    if machine_state.get("forced_fail_close_reason") != FAIL_CLOSE_REASON:
        stale_reasons.append("execution_loop_not_entering_mutation_phase")

    ok = not stale_reasons
    result = {
        "ok": ok,
        "status": PASS_REQUIRED if ok else FAIL_REQUIRED,
        "issue": ISSUE_ID,
        "lane_id": LANE_ID,
        "mode": "continuous_scope_locked_mutation_phase_runtime_enforcement_ready" if ok else FAIL_CLOSE_REASON,
        "checked_file_count": len(FIXED_WRITE_SET),
        "allowed_next_actions": list(ALLOWED_NEXT_ACTIONS),
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "bridged_guard_fields": list(BRIDGED_GUARD_FIELDS),
        "fail_close_reason_family": list(FAIL_CLOSE_REASON_FAMILY),
        "stale_reasons": stale_reasons,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    result = validate(args.root)
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
