#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from launcher_convergence_probe_context_common import (
    ERR_DISCOVERY_FAILED,
    ERR_MATERIALIZATION_FAILED,
    materialize_launcher_convergence_probe_context,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _emit(payload: dict[str, object], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Materialize a single-identity launcher convergence probe workspace from a runtime catalog."
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--target-workspace-root", required=True)
    ap.add_argument("--preserve-launcher-assets", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, object] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_DISCOVERY_FAILED,
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "identity_id": str(args.identity_id).strip(),
        "target_workspace_root": str(Path(args.target_workspace_root).expanduser().resolve()),
        "preserve_launcher_assets": bool(args.preserve_launcher_assets),
    }
    try:
        result = materialize_launcher_convergence_probe_context(
            catalog_path=Path(args.catalog),
            identity_id=str(args.identity_id).strip(),
            target_workspace_root=Path(args.target_workspace_root),
            preserve_launcher_assets=bool(args.preserve_launcher_assets),
        )
        payload.update(result)
        payload["status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        message = str(exc)
        if "missing_identity_row" in message or "missing_source_pack" in message:
            payload["error_code"] = ERR_DISCOVERY_FAILED
        else:
            payload["error_code"] = ERR_MATERIALIZATION_FAILED
        payload["stale_reasons"] = [message] if message else ["launcher_convergence_probe_context_failed"]
        _emit(payload, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
