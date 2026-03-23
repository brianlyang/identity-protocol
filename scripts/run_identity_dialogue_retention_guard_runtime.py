#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from identity_dialogue_retention_common import (
    STATUS_FAIL_REQUIRED,
    resolve_dialogue_retention_pack_context,
    sync_dialogue_retention,
)


def _emit(payload: dict, *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Shared runtime driver for protocol-owned dialogue retention sync.")
    ap.add_argument("--guard-script", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("action", choices=("sync",))
    ap.add_argument("--thread-id", default="")
    ap.add_argument("--source-session-file", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        ctx = resolve_dialogue_retention_pack_context(script_file=args.guard_script, explicit_catalog=args.catalog)
        payload = sync_dialogue_retention(
            ctx,
            thread_id=args.thread_id,
            source_session_file=args.source_session_file,
            reply_file=args.reply_file,
            apply=True,
        )
    except Exception as exc:
        payload = {
            "status": STATUS_FAIL_REQUIRED,
            "action": str(getattr(args, "action", "")).strip(),
            "error": str(exc),
        }
        _emit(payload, json_only=args.json_only)
        return 1

    payload["action"] = "sync"
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
