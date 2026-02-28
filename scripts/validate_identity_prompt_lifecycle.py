#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _latest(identity_id: str, report_dir: Path) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    rows = [p for p in rows if not p.name.endswith("-patch-plan.json")]
    return rows[-1] if rows else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate IDENTITY_PROMPT lifecycle contract in upgrade reports.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="/tmp/identity-upgrade-reports")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser().resolve() if args.report else _latest(
        args.identity_id, Path(args.report_dir).expanduser().resolve()
    )
    if report_path is None or not report_path.exists():
        print(f"[FAIL] execution report not found for identity={args.identity_id}")
        return 1
    data = json.loads(report_path.read_text(encoding="utf-8"))

    required = [
        "upgrade_required",
        "prompt_change_required",
        "prompt_change_applied",
        "identity_prompt_hash_before",
        "identity_prompt_hash_after",
        "identity_prompt_change_note",
        "identity_prompt_status",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"[FAIL] prompt lifecycle fields missing: {missing}")
        return 1

    upgrade_required = bool(data.get("upgrade_required"))
    change_required = bool(data.get("prompt_change_required"))
    change_applied = bool(data.get("prompt_change_applied"))
    h_before = str(data.get("identity_prompt_hash_before", "")).strip()
    h_after = str(data.get("identity_prompt_hash_after", "")).strip()
    status = str(data.get("identity_prompt_status", "")).strip().upper()
    note = str(data.get("identity_prompt_change_note", "")).strip()
    permission_error_code = str(data.get("permission_error_code", "")).strip()
    next_action = str(data.get("next_action", "")).strip()
    failure_reason = str(data.get("failure_reason", "")).strip()
    writeback_status = str(data.get("writeback_status", "")).strip().upper()
    all_ok = bool(data.get("all_ok", False))
    deferred_blocked = (not all_ok) and (
        permission_error_code in {"IP-UPG-001", "IP-PERM-001"}
        or next_action
        in {
            "blocked_by_safe_auto_path_policy",
            "resolve_capability_activation_then_rerun_update",
            "review_required_create_pr_from_patch_plan",
        }
        or failure_reason in {"safe_auto_path_policy_violation", "permission_precheck_blocked"}
        or note == "prompt_change_deferred_due_to_failed_validators"
        or writeback_status.startswith("DEFERRED")
    )

    if upgrade_required and not change_required and not deferred_blocked:
        print("[FAIL] upgrade_required=true requires prompt_change_required=true")
        return 1
    if not upgrade_required and change_required:
        print("[FAIL] prompt_change_required=true while upgrade_required=false")
        return 1
    if change_required and not change_applied and not deferred_blocked:
        print(f"[FAIL] prompt_change_required=true but prompt_change_applied=false note={note}")
        return 1
    if change_applied and (not h_before or not h_after):
        print("[FAIL] prompt_change_applied=true requires hash_before/hash_after")
        return 1
    if change_applied and h_before == h_after:
        print("[FAIL] prompt_change_applied=true but hash_before == hash_after")
        return 1
    if status != "ACTIVATED":
        print(f"[FAIL] identity_prompt_status must be ACTIVATED, got: {status}")
        return 1

    prompt_path = Path(str(data.get("identity_prompt_path", ""))).expanduser().resolve()
    if not prompt_path.exists():
        print(f"[FAIL] prompt path missing: {prompt_path}")
        return 1
    text = prompt_path.read_text(encoding="utf-8", errors="ignore")
    if "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:BEGIN -->" not in text or "<!-- IDENTITY_PROMPT_RUNTIME_CONTRACT:END -->" not in text:
        print("[FAIL] prompt runtime contract block markers missing in IDENTITY_PROMPT.md")
        return 1

    print(f"[OK] prompt lifecycle validated: {report_path}")
    print(f"     change_required={change_required} change_applied={change_applied}")
    print(f"     hash_before={h_before}")
    print(f"     hash_after={h_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
