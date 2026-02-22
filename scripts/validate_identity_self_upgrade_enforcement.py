#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _changed_files(base: str, head: str) -> list[str]:
    rc, out, err = _run(["git", "diff", "--name-only", f"{base}..{head}"])
    if rc != 0:
        raise RuntimeError(f"git diff failed: {err or out}")
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Enforce that identity-core updates include self-upgrade execution evidence."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    if not args.base:
        rc, out, _ = _run(["git", "rev-parse", "HEAD~1"])
        if rc != 0:
            print("[WARN] fallback base resolution failed; skip enforcement on first commit context")
            return 0
        args.base = out.strip()

    try:
        changed = _changed_files(args.base, args.head)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    if not changed:
        print("[OK] no changed files in range; enforcement skipped")
        return 0

    identity_prefixes = [
        f"identity/{args.identity_id}/",
        f"identity/packs/{args.identity_id}/",
    ]
    core_targets = {
        "CURRENT_TASK.json",
        "IDENTITY_PROMPT.md",
        "RULEBOOK.jsonl",
    }
    touched_core = []
    for f in changed:
        for pref in identity_prefixes:
            if f.startswith(pref):
                name = Path(f).name
                if name in core_targets:
                    touched_core.append(f)

    if not touched_core:
        print("[OK] no identity-core contract files changed; enforcement pass")
        return 0

    evidence_changed = [
        f
        for f in changed
        if f.startswith("identity/runtime/reports/")
        and Path(f).name.startswith(f"identity-upgrade-exec-{args.identity_id}-")
        and f.endswith(".json")
    ]

    if not evidence_changed:
        print("[FAIL] identity-core files changed without self-upgrade evidence report change.")
        print("       touched core files:")
        for f in touched_core:
            print(f"       - {f}")
        print(
            "       require at least one changed file under "
            f"identity/runtime/reports/identity-upgrade-exec-{args.identity_id}-*.json"
        )
        return 1

    report_candidates = [f for f in evidence_changed if not f.endswith("-patch-plan.json")]
    if not report_candidates:
        print("[FAIL] self-upgrade evidence exists but no execution report JSON found.")
        print("       expected file pattern: identity-upgrade-exec-<identity-id>-<ts>.json")
        return 1

    required_check_tokens = [
        "validate_identity_upgrade_prereq.py",
        "validate_identity_runtime_contract.py",
        "validate_identity_update_lifecycle.py",
        "validate_identity_capability_arbitration.py",
    ]
    valid_reports = 0
    for rel in report_candidates:
        path = Path(rel)
        try:
            report = _load_json(path)
        except Exception as e:
            print(f"[FAIL] cannot parse evidence report {rel}: {e}")
            continue

        if str(report.get("identity_id", "")).strip() != args.identity_id:
            print(f"[FAIL] evidence report identity mismatch in {rel}")
            continue
        mode = str(report.get("mode", "")).strip()
        if mode not in {"review-required", "safe-auto"}:
            print(f"[FAIL] invalid mode in {rel}: {mode!r}")
            continue
        checks = report.get("checks")
        if not isinstance(checks, list) or not checks:
            print(f"[FAIL] report.checks must be non-empty list in {rel}")
            continue
        cmds = [str(x.get("cmd", "")) for x in checks if isinstance(x, dict)]
        missing_tokens = [tok for tok in required_check_tokens if not any(tok in c for c in cmds)]
        if missing_tokens:
            print(f"[FAIL] evidence report missing required checks in {rel}: {missing_tokens}")
            continue
        run_id = str(report.get("run_id", "")).strip()
        if not run_id:
            print(f"[FAIL] report.run_id missing in {rel}")
            continue
        patch_plan_name = f"{run_id}-patch-plan.json"
        if f"identity/runtime/reports/{patch_plan_name}" not in evidence_changed:
            print(
                f"[FAIL] evidence report {rel} missing matching patch plan diff change: "
                f"identity/runtime/reports/{patch_plan_name}"
            )
            continue
        valid_reports += 1

    if valid_reports == 0:
        print("[FAIL] no valid self-upgrade execution evidence report found.")
        return 1

    print("[OK] self-upgrade enforcement passed")
    print("     touched core files:")
    for f in touched_core:
        print(f"     - {f}")
    print("     evidence files:")
    for f in evidence_changed:
        print(f"     - {f}")
    print(f"     valid_execution_reports={valid_reports}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
