#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from governed_runtime_summary_checkpoint_common import (
    SUMMARY_LIFECYCLE_FINALIZED,
    SUMMARY_LIFECYCLE_IN_PROGRESS,
    load_governed_runtime_summary_doc,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
RELEASE_READINESS_REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_READINESS_SCRIPT_PATH = (RELEASE_READINESS_REPO_ROOT / "scripts" / "release_readiness_check.py").resolve()
FORBIDDEN_FORWARD_FLAGS = {
    "--summary-out",
    "--resume-from-summary",
    "--max-command-sequence-checks",
}


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _load_progress(summary_doc: dict[str, Any]) -> dict[str, Any]:
    progress = summary_doc.get("summary_progress") or {}
    return progress if isinstance(progress, dict) else {}


def _progress_fingerprint(summary_doc: dict[str, Any]) -> tuple[Any, ...]:
    progress = _load_progress(summary_doc)
    return (
        _clean_str(summary_doc.get("summary_lifecycle_status")),
        _safe_int(progress.get("checkpoint_sequence")),
        _safe_int(progress.get("executed_command_count")),
        _clean_str(progress.get("current_check_name")),
        _clean_str(progress.get("last_completed_check_name")),
        _clean_str(progress.get("current_check_state")),
    )


def _write_json(path_text: str, payload: dict[str, Any]) -> str:
    target = Path(path_text).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    else:
        target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target)


def _build_round_cmd(
    *,
    forwarded_args: list[str],
    summary_out: str,
    batch_size: int,
    resume_from_summary: str = "",
) -> list[str]:
    cmd = [
        sys.executable,
        str(RELEASE_READINESS_SCRIPT_PATH),
        *forwarded_args,
        "--summary-out",
        summary_out,
        "--max-command-sequence-checks",
        str(batch_size),
    ]
    if resume_from_summary:
        cmd.extend(["--resume-from-summary", resume_from_summary])
    return cmd


def _validate_forwarded_args(forwarded_args: list[str]) -> str:
    for token in forwarded_args:
        if token in FORBIDDEN_FORWARD_FLAGS:
            return token
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Continue release_readiness_check.py in bounded command-sequence batches until the summary finalizes "
            "or a fail-close condition is reached."
        )
    )
    ap.add_argument("--summary-out", required=True, help="shared summary checkpoint path used across continuation rounds")
    ap.add_argument("--batch-size", type=int, default=25, help="max command-sequence checks to execute per round")
    ap.add_argument("--max-rounds", type=int, default=8, help="maximum continuation rounds before fail-close")
    ap.add_argument("--report-out", default="", help="optional continuation report JSON path")
    ap.add_argument("--json-only", action="store_true", help="print only the final continuation JSON")
    args, forwarded_args = ap.parse_known_args()
    if forwarded_args[:1] == ["--"]:
        forwarded_args = forwarded_args[1:]

    forbidden = _validate_forwarded_args(forwarded_args)
    if forbidden:
        print(
            json.dumps(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "error_code": "IP-RR-CONT-001",
                    "reason": f"forwarded_flag_forbidden:{forbidden}",
                },
                ensure_ascii=False,
            )
        )
        return 2

    if args.batch_size <= 0:
        print(
            json.dumps(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "error_code": "IP-RR-CONT-002",
                    "reason": "batch_size_must_be_positive",
                },
                ensure_ascii=False,
            )
        )
        return 2
    if args.max_rounds <= 0:
        print(
            json.dumps(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "error_code": "IP-RR-CONT-003",
                    "reason": "max_rounds_must_be_positive",
                },
                ensure_ascii=False,
            )
        )
        return 2

    summary_out = str(Path(args.summary_out).expanduser().resolve())
    report: dict[str, Any] = {
        "continuation_status": STATUS_FAIL_REQUIRED,
        "summary_out": summary_out,
        "batch_size": int(args.batch_size),
        "max_rounds": int(args.max_rounds),
        "runner_repo_root": str(RELEASE_READINESS_REPO_ROOT),
        "release_readiness_script_path": str(RELEASE_READINESS_SCRIPT_PATH),
        "rounds": [],
    }

    initial_doc = load_governed_runtime_summary_doc(summary_out)
    if _clean_str(initial_doc.get("summary_lifecycle_status")) == SUMMARY_LIFECYCLE_FINALIZED:
        report.update(
            {
                "continuation_status": STATUS_PASS_REQUIRED,
                "continuation_reason": "summary_already_finalized",
                "summary_lifecycle_status": SUMMARY_LIFECYCLE_FINALIZED,
                "round_count": 0,
                "final_summary": initial_doc,
            }
        )
        if args.report_out:
            report["report_out"] = _write_json(args.report_out, report)
        print(json.dumps(report, ensure_ascii=False, indent=None if args.json_only else 2))
        return 0

    previous_fingerprint: tuple[Any, ...] | None = _progress_fingerprint(initial_doc) if initial_doc else None
    previous_summary_path = summary_out if initial_doc else ""

    for round_index in range(1, int(args.max_rounds) + 1):
        cmd = _build_round_cmd(
            forwarded_args=forwarded_args,
            summary_out=summary_out,
            batch_size=int(args.batch_size),
            resume_from_summary=previous_summary_path,
        )
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(RELEASE_READINESS_REPO_ROOT),
        )
        summary_doc = load_governed_runtime_summary_doc(summary_out)
        lifecycle_status = _clean_str(summary_doc.get("summary_lifecycle_status"))
        progress = _load_progress(summary_doc)
        round_row = {
            "round_index": round_index,
            "command": cmd,
            "round_workdir": str(RELEASE_READINESS_REPO_ROOT),
            "returncode": int(proc.returncode),
            "summary_lifecycle_status": lifecycle_status,
            "current_check_name": _clean_str(progress.get("current_check_name")),
            "current_check_state": _clean_str(progress.get("current_check_state")),
            "last_completed_check_name": _clean_str(progress.get("last_completed_check_name")),
            "checkpoint_sequence": _safe_int(progress.get("checkpoint_sequence")),
            "executed_command_count": _safe_int(progress.get("executed_command_count")),
            "stdout_tail": proc.stdout.splitlines()[-20:],
            "stderr_tail": proc.stderr.splitlines()[-20:],
        }
        report["rounds"].append(round_row)

        if proc.returncode != 0:
            report.update(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "continuation_reason": "release_readiness_round_failed",
                    "failed_round_index": round_index,
                    "summary_lifecycle_status": lifecycle_status or SUMMARY_LIFECYCLE_IN_PROGRESS,
                    "final_summary": summary_doc,
                }
            )
            break

        if not summary_doc:
            report.update(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "continuation_reason": "summary_missing_after_successful_round",
                    "failed_round_index": round_index,
                    "summary_lifecycle_status": "",
                }
            )
            break

        if lifecycle_status == SUMMARY_LIFECYCLE_FINALIZED:
            report.update(
                {
                    "continuation_status": STATUS_PASS_REQUIRED,
                    "continuation_reason": "summary_finalized",
                    "summary_lifecycle_status": lifecycle_status,
                    "round_count": round_index,
                    "final_summary": summary_doc,
                }
            )
            break

        if lifecycle_status != SUMMARY_LIFECYCLE_IN_PROGRESS:
            report.update(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "continuation_reason": "summary_lifecycle_status_invalid_after_round",
                    "failed_round_index": round_index,
                    "summary_lifecycle_status": lifecycle_status,
                    "final_summary": summary_doc,
                }
            )
            break

        fingerprint = _progress_fingerprint(summary_doc)
        if previous_fingerprint is not None and fingerprint == previous_fingerprint:
            report.update(
                {
                    "continuation_status": STATUS_FAIL_REQUIRED,
                    "continuation_reason": "summary_progress_stalled",
                    "failed_round_index": round_index,
                    "summary_lifecycle_status": lifecycle_status,
                    "final_summary": summary_doc,
                }
            )
            break

        previous_fingerprint = fingerprint
        previous_summary_path = summary_out
    else:
        final_doc = load_governed_runtime_summary_doc(summary_out)
        report.update(
            {
                "continuation_status": STATUS_FAIL_REQUIRED,
                "continuation_reason": "max_rounds_exhausted_without_finalization",
                "failed_round_index": int(args.max_rounds),
                "summary_lifecycle_status": _clean_str(final_doc.get("summary_lifecycle_status")),
                "final_summary": final_doc,
            }
        )

    if "round_count" not in report:
        report["round_count"] = len(report.get("rounds", []))
    if args.report_out:
        report["report_out"] = _write_json(args.report_out, report)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0 if report.get("continuation_status") == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
