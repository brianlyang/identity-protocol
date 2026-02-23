#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

HIGH_IMPACT = {"CURRENT_TASK.json", "IDENTITY_PROMPT.md", "RULEBOOK.jsonl"}


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip()


def _changed(base: str, head: str) -> list[str]:
    rc, out = _run(["git", "diff", "--name-only", f"{base}..{head}"])
    if rc != 0:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]


def _latest_report(identity_id: str) -> Path | None:
    p = Path("identity/runtime/reports")
    if not p.exists():
        return None
    rows = sorted(p.glob(f"identity-upgrade-exec-{identity_id}-*.json"), key=lambda x: x.stat().st_mtime)
    rows = [x for x in rows if not x.name.endswith("-patch-plan.json")]
    return rows[-1] if rows else None


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_high_impact(identity_id: str, files: list[str]) -> bool:
    prefixes = [f"identity/{identity_id}/", f"identity/packs/{identity_id}/"]
    for f in files:
        for pref in prefixes:
            if f.startswith(pref) and Path(f).name in HIGH_IMPACT:
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate mode-B promotion arbitration for high-impact identity changes")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--report", default="", help="optional explicit upgrade execution report")
    args = ap.parse_args()

    base = args.base.strip()
    if not base:
        rc, out = _run(["git", "rev-parse", "HEAD~1"])
        if rc != 0:
            print("[WARN] cannot resolve base; skip promotion arbitration check")
            return 0
        base = out

    files = _changed(base, args.head)
    if not files:
        print("[OK] no changed files; promotion arbitration skipped")
        return 0

    if not _is_high_impact(args.identity_id, files):
        print("[OK] no high-impact identity-core changes; mode promotion arbitration pass")
        return 0

    report = Path(args.report) if args.report else _latest_report(args.identity_id)
    if not report or not report.exists():
        print("[FAIL] high-impact changes require upgrade execution report evidence")
        return 1

    row = _load(report)
    mode = str(row.get("protocol_mode", "")).strip()
    all_ok = bool(row.get("all_ok"))

    if mode == "mode_a_shared":
        if not all_ok:
            print(f"[FAIL] mode_a_shared report must be all_ok=true for promotion: {report}")
            return 1
        print(f"[OK] high-impact changes covered by mode_a_shared replay PASS: {report}")
        return 0

    if mode != "mode_b_standalone":
        print(f"[FAIL] invalid protocol_mode for promotion evidence: {mode!r}")
        return 1

    note = str(row.get("arbitration_note_id", "")).strip()
    mode_a_replay = str(row.get("mode_a_replay_report", "")).strip()
    if not note:
        print("[FAIL] mode_b promotion requires arbitration_note_id")
        return 1
    if not mode_a_replay:
        print("[FAIL] mode_b promotion requires mode_a_replay_report")
        return 1
    rp = Path(mode_a_replay)
    if not rp.exists():
        print(f"[FAIL] mode_a_replay_report not found: {rp}")
        return 1
    replay = _load(rp)
    if str(replay.get("protocol_mode", "")).strip() != "mode_a_shared" or not bool(replay.get("all_ok")):
        print("[FAIL] mode_a_replay_report must be mode_a_shared with all_ok=true")
        return 1

    print("[OK] mode_b promotion arbitration validated with mode_a replay evidence")
    print(f"     arbitration_note_id={note}")
    print(f"     mode_a_replay_report={rp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
