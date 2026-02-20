#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> dict[str, Any]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "code": p.returncode,
        "ok": p.returncode == 0,
        "stdout": p.stdout[-6000:],
        "stderr": p.stderr[-6000:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run identity update cycle checks (skill-style: trigger/patch/validate/replay)")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--replay-command", default="", help="optional replay command for the original failing case")
    ap.add_argument("--out-dir", default="identity/runtime/reports")
    args = ap.parse_args()

    checks = []
    checks.append(_run(["python3", "scripts/validate_identity_upgrade_prereq.py", "--identity-id", args.identity_id]))
    checks.append(_run(["python3", "scripts/validate_identity_runtime_contract.py"]))
    checks.append(_run(["python3", "scripts/validate_identity_update_lifecycle.py", "--identity-id", args.identity_id]))

    replay = None
    if args.replay_command.strip():
        replay = _run(["bash", "-lc", args.replay_command.strip()])

    all_ok = all(c["ok"] for c in checks) and (replay is None or replay["ok"])

    report = {
        "run_id": f"identity-update-cycle-{args.identity_id}-{int(time.time())}",
        "identity_id": args.identity_id,
        "checks": checks,
        "replay": replay,
        "all_ok": all_ok,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"identity-update-cycle-{args.identity_id}-{int(time.time())}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"report={out_path}")
    print(f"all_ok={all_ok}")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
