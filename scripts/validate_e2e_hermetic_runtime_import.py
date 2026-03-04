#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_HERMETIC_IMPORT = "IP-E2E-HERM-001"

STRICT_OPERATIONS = {"activate", "update", "readiness", "e2e", "ci", "validate", "mutation"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate hermetic runtime import preflight for e2e/replay operations.")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--pythonpath-bootstrap-mode", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    strict = str(args.operation or "validate").strip().lower() in STRICT_OPERATIONS
    bootstrap_mode = str(args.pythonpath_bootstrap_mode or "").strip() or "auto"

    stale_reasons: list[str] = []
    missing_modules: list[str] = []
    for mod in ("response_stamp_common", "resolve_identity_context"):
        if not _has_module(mod):
            missing_modules.append(mod)
            stale_reasons.append(f"module_not_importable:{mod}")

    error_code = ""
    if missing_modules:
        error_code = ERR_HERMETIC_IMPORT
        status = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        import_status = STATUS_FAIL_REQUIRED if strict else STATUS_WARN_NON_BLOCKING
        rc = 1 if strict else 0
    else:
        status = STATUS_PASS_REQUIRED
        import_status = STATUS_PASS_REQUIRED
        rc = 0

    payload = {
        "operation": args.operation,
        "strict_operation": strict,
        "e2e_hermetic_runtime_status": status,
        "pythonpath_bootstrap_mode": bootstrap_mode,
        "import_preflight_status": import_status,
        "import_preflight_error_code": error_code,
        "missing_modules": missing_modules,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

