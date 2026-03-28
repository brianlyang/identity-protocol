#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from primary_execution_report_common import latest_prompt_bound_primary_execution_report_from_roots
from runtime_temp_path_common import runtime_temp_root

ALLOWED_STATES = {
    "BLOCKED",
    "PRECHECK",
    "RUN_READONLY",
    "NEEDS_ESCALATION",
    "ESCALATION_GRANTED",
    "ESCALATION_DENIED",
    "WRITEBACK_ATTEMPT",
    "WRITEBACK_WRITTEN",
    "WRITEBACK_DEFERRED",
    "WRITEBACK_FAILED",
    "DONE",
}
ALLOWED_CODE_PREFIXES = (
    "",
    "IP-PERM-",
    "IP-PATH-",
    "IP-CI-",
    "IP-REC-",
    "IP-UPG-",
    "IP-EXEC-ORDER-",
    "IP-SAFEAUTO-",
)


def _is_allowed_code(code: str) -> bool:
    if not code:
        return True
    return any(code.startswith(prefix) for prefix in ALLOWED_CODE_PREFIXES if prefix)


def _state_matches_writeback(state: str, writeback_status: str) -> bool:
    if writeback_status == "WRITTEN":
        return state == "WRITEBACK_WRITTEN"
    if writeback_status.startswith("DEFERRED_"):
        return state in {"PRECHECK", "BLOCKED", "WRITEBACK_DEFERRED", "ESCALATION_DENIED"}
    if writeback_status == "NOT_REQUIRED":
        return state in {"PRECHECK", "DONE", "WRITEBACK_WRITTEN"}
    if writeback_status == "MISSING":
        return state in {"PRECHECK", "BLOCKED"}
    return True


def _writeback_code_matches(writeback_status: str, code: str) -> bool:
    if writeback_status == "DEFERRED_PERMISSION_BLOCKED":
        return code.startswith("IP-PERM-")
    if writeback_status == "DEFERRED_POLICY_BLOCKED":
        return code.startswith("IP-UPG-") or code.startswith("IP-SAFEAUTO-")
    if writeback_status == "DEFERRED_VALIDATION_FAILED":
        return (not code) or code.startswith("IP-UPG-") or code.startswith("IP-EXEC-ORDER-")
    return True


def _latest(identity_id: str, report_dir: Path) -> Path | None:
    return latest_prompt_bound_primary_execution_report_from_roots([report_dir], identity_id)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate permission-state contract in identity upgrade report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default=str(runtime_temp_root() / "identity-upgrade-reports"))
    ap.add_argument("--require-written", action="store_true")
    ap.add_argument("--ci", action="store_true")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser().resolve() if args.report else _latest(args.identity_id, Path(args.report_dir).expanduser().resolve())
    if report_path is None or not report_path.exists():
        print(f"[FAIL] execution report not found for identity={args.identity_id}")
        return 1

    data = json.loads(report_path.read_text(encoding="utf-8"))
    state = str(data.get("permission_state", "")).strip()
    code = str(data.get("permission_error_code", "")).strip()
    wb = str(data.get("writeback_status", "")).strip()
    pre = data.get("writeback_precheck") or {}

    if not state:
        print("[FAIL] permission_state missing")
        return 1
    if state not in ALLOWED_STATES:
        print(f"[FAIL] invalid permission_state: {state}")
        return 1
    if not _is_allowed_code(code):
        print(f"[FAIL] invalid permission_error_code: {code}")
        return 1
    if not isinstance(pre, dict) or "all_writable" not in pre:
        print("[FAIL] writeback_precheck missing required fields")
        return 1

    if not _state_matches_writeback(state, wb):
        print(f"[FAIL] permission_state/writeback_status mismatch: {state} vs {wb}")
        return 1

    if not _writeback_code_matches(wb, code):
        print(f"[FAIL] writeback_status/code mismatch: {wb} vs {code}")
        return 1

    if args.ci and wb == "DEFERRED_PERMISSION_BLOCKED":
        print("[FAIL] CI cannot accept deferred permission writeback")
        return 2

    if args.require_written and wb != "WRITTEN":
        print(f"[FAIL] writeback_status must be WRITTEN, got {wb}")
        return 2

    print(f"[OK] permission state validated: {report_path}")
    print(f"     permission_state={state} writeback_status={wb} error_code={code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
