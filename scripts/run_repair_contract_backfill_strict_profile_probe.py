#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repair_contract_backfill_strict_profile_probe_common import (
    run_repair_contract_backfill_strict_profile_probe,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STRICT_PROFILE_PROBE_FAILED = "IP-RCBK-SP-001"


def _emit(payload: dict[str, object], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Seed a generic current-run projection failure and prove repair_contract_backfill strict_full still fail-closes."
    )
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--workspace-root", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report-path", required=True)
    ap.add_argument("--codex-home", required=True)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, object] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_STRICT_PROFILE_PROBE_FAILED,
        "repo_root": str(Path(args.repo_root).expanduser().resolve()),
        "workspace_root": str(Path(args.workspace_root).expanduser().resolve()),
        "catalog": str(args.catalog),
        "identity_id": str(args.identity_id).strip(),
        "report_path": str(Path(args.report_path).expanduser().resolve()),
        "codex_home": str(Path(args.codex_home).expanduser().resolve()),
    }
    try:
        result = run_repair_contract_backfill_strict_profile_probe(
            repo_root=Path(args.repo_root),
            workspace_root=Path(args.workspace_root),
            catalog_arg=str(args.catalog),
            identity_id=str(args.identity_id),
            report_path=Path(args.report_path),
            codex_home=Path(args.codex_home),
        )
        payload.update(result)
        payload["status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        payload["stale_reasons"] = [f"strict_profile_probe_failed:{type(exc).__name__}:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
