#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from identity_dialogue_retention_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    clean_string,
    resolve_dialogue_retention_pack_context,
)
from identity_context_continuity_common import REENTRY_BRIEF_REL

CONTEXT_CONSUMPTION_RECEIPT_REL = Path("runtime/reports/context-continuity/reentry-consumption-receipt.json")
CONTEXT_GUARD_SCRIPT_REL = Path("scripts/run_identity_context_continuity_guard.sh")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_json(cmd: list[str], *, cwd: Path) -> tuple[int, dict[str, Any], str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload: dict[str, Any] = {}
    if stdout:
        try:
            raw = json.loads(stdout)
            if isinstance(raw, dict):
                payload = raw
        except Exception:
            payload = {}
    if not payload and stderr:
        try:
            raw = json.loads(stderr)
            if isinstance(raw, dict):
                payload = raw
        except Exception:
            payload = {}
    return proc.returncode, payload, stdout, stderr


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json_root_not_object:{path}")
    return payload


def _pending_reentry_consumption(pack_root: Path) -> tuple[bool, str, str]:
    brief_path = (pack_root / REENTRY_BRIEF_REL).resolve()
    if not brief_path.is_file():
        return False, "", ""
    try:
        brief_doc = _load_json(brief_path)
    except Exception:
        return True, "", "brief_invalid_json"
    brief_continuity_id = clean_string(brief_doc.get("continuity_id"))
    receipt_path = (pack_root / CONTEXT_CONSUMPTION_RECEIPT_REL).resolve()
    if not receipt_path.is_file():
        return True, brief_continuity_id, "receipt_missing"
    try:
        receipt_doc = _load_json(receipt_path)
    except Exception:
        return True, brief_continuity_id, "receipt_invalid_json"
    consumed_lineage = clean_string(receipt_doc.get("continuity_lineage_ref"))
    if not brief_continuity_id:
        return False, "", ""
    return brief_continuity_id != consumed_lineage, brief_continuity_id, consumed_lineage


def main() -> int:
    ap = argparse.ArgumentParser(description="Run shared post-delivery runtime hooks for dialogue retention and continuity.")
    ap.add_argument("--emitter-script", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--thread-id", default="")
    ap.add_argument("--source-session-file", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        ctx = resolve_dialogue_retention_pack_context(script_file=args.emitter_script, explicit_catalog=args.catalog)
        actions_taken: list[str] = []
        artifacts: dict[str, Any] = {}

        dialogue_cmd = [
            sys.executable,
            str((ctx.protocol_home / "scripts" / "run_identity_dialogue_retention_guard_runtime.py").resolve()),
            "--guard-script",
            str(Path(args.emitter_script).expanduser().resolve()),
            "--catalog",
            str(ctx.catalog_path),
            "sync",
            "--json-only",
        ]
        if clean_string(args.thread_id):
            dialogue_cmd.extend(["--thread-id", clean_string(args.thread_id)])
        if clean_string(args.source_session_file):
            dialogue_cmd.extend(["--source-session-file", clean_string(args.source_session_file)])
        if clean_string(args.reply_file):
            dialogue_cmd.extend(["--reply-file", clean_string(args.reply_file)])
        rc_dialogue, dialogue_payload, dialogue_stdout, dialogue_stderr = _run_json(dialogue_cmd, cwd=ctx.workspace_root)
        artifacts["dialogue_retention"] = {
            "returncode": rc_dialogue,
            "payload": dialogue_payload,
            "stdout": dialogue_stdout,
            "stderr": dialogue_stderr,
        }
        if rc_dialogue != 0 or clean_string(dialogue_payload.get("status")) != STATUS_PASS_REQUIRED:
            raise RuntimeError(clean_string(dialogue_payload.get("error")) or "dialogue_retention_sync_failed")
        actions_taken.append("dialogue_retention_sync")

        guard_script = (ctx.pack_root / CONTEXT_GUARD_SCRIPT_REL).resolve()
        if not guard_script.is_file():
            raise RuntimeError(f"context_continuity_guard_missing:{guard_script}")

        tick_cmd = [
            str(guard_script),
            "--catalog",
            str(ctx.catalog_path),
            "tick",
            "--turn-increment",
            "1",
            "--json-only",
        ]
        rc_tick, tick_payload, tick_stdout, tick_stderr = _run_json(tick_cmd, cwd=ctx.workspace_root)
        artifacts["context_continuity_tick"] = {
            "returncode": rc_tick,
            "payload": tick_payload,
            "stdout": tick_stdout,
            "stderr": tick_stderr,
        }
        if rc_tick != 0 or clean_string(tick_payload.get("status")) != STATUS_PASS_REQUIRED:
            raise RuntimeError(clean_string(tick_payload.get("error")) or "context_continuity_tick_failed")
        actions_taken.append("context_continuity_tick")

        pending_reentry, active_brief_continuity_id, consumed_lineage = _pending_reentry_consumption(ctx.pack_root)
        post_recover_payload: dict[str, Any] = {}
        if pending_reentry:
            post_cmd = [
                str(guard_script),
                "--catalog",
                str(ctx.catalog_path),
                "post-recover",
                "--json-only",
            ]
            rc_post, post_recover_payload, post_stdout, post_stderr = _run_json(post_cmd, cwd=ctx.workspace_root)
            artifacts["context_continuity_post_recover"] = {
                "returncode": rc_post,
                "payload": post_recover_payload,
                "stdout": post_stdout,
                "stderr": post_stderr,
            }
            if rc_post != 0 or clean_string(post_recover_payload.get("status")) != STATUS_PASS_REQUIRED:
                raise RuntimeError(clean_string(post_recover_payload.get("error")) or "context_continuity_post_recover_failed")
            actions_taken.append("context_continuity_post_recover")

        payload = {
            "status": STATUS_PASS_REQUIRED,
            "identity_id": ctx.identity_id,
            "catalog_path": str(ctx.catalog_path),
            "dialogue_retention_status": STATUS_PASS_REQUIRED,
            "context_continuity_status": STATUS_PASS_REQUIRED,
            "pending_reentry_consumption_detected": bool(pending_reentry),
            "active_reentry_brief_continuity_id": clean_string(active_brief_continuity_id),
            "consumed_reentry_lineage": clean_string(consumed_lineage),
            "actions_taken": actions_taken,
            "artifacts": artifacts,
        }
    except Exception as exc:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "error": str(exc),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
