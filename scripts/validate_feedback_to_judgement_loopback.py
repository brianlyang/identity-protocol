#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from feedback_to_judgement_loopback_common import (
    ERR_FEEDBACK_TO_JUDGEMENT_LOOPBACK_INVALID,
    STATUS_FAIL_REQUIRED,
    inspect_feedback_to_judgement_loopback,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _emit(payload: dict, *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the v1.6.17 feedback-to-judgement loopback bridge.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--current-task", default="", help="optional CURRENT_TASK.json path for probe/fixture validation")
    ap.add_argument("--operation", default="", help="accepted for gate-runner compatibility")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    identity_id = str(args.identity_id or "").strip()
    current_task = str(args.current_task or "").strip()
    try:
        if current_task:
            task_path = Path(current_task).expanduser().resolve()
            if not task_path.exists():
                raise FileNotFoundError(f"current_task not found: {task_path}")
            task_doc = load_json(task_path)
            if not identity_id:
                identity_id = str(task_doc.get("identity_id") or task_path.parent.name).strip()
        else:
            if not identity_id:
                raise ValueError("identity_id required unless --current-task is provided")
            catalog_path = Path(str(args.catalog or "")).expanduser().resolve()
            _pack_root, task_path = resolve_pack_and_task(catalog_path, identity_id)
            task_doc = load_json(task_path)
    except Exception as exc:
        payload = {
            "feedback_to_judgement_loopback_status": STATUS_FAIL_REQUIRED,
            "loop_back_to_first_loop_status": STATUS_FAIL_REQUIRED,
            "required_contract": True,
            "identity_id": identity_id,
            "task_path": str(Path(current_task).expanduser().resolve()) if current_task else "",
            "stale_reasons": [f"current_task_resolve_failed:{type(exc).__name__}"],
            "error_code": ERR_FEEDBACK_TO_JUDGEMENT_LOOPBACK_INVALID,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    payload = inspect_feedback_to_judgement_loopback(
        task_doc=task_doc,
        identity_id=identity_id,
        task_path=str(task_path),
    )
    _emit(payload, json_only=args.json_only)
    return 0 if str(payload.get("feedback_to_judgement_loopback_status", "")).strip().upper() != STATUS_FAIL_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
