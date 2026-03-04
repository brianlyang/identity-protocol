#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from resolve_identity_context import resolve_identity

ERR_REPORT_PATH_CONTRACT = "IP-PATH-002"


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _canonical(path_raw: str) -> tuple[Path | None, list[str]]:
    reasons: list[str] = []
    raw = str(path_raw or "").strip()
    if not raw:
        return None, ["report_resolved_pack_path_missing"]
    if raw in {".", ".."}:
        return None, ["report_resolved_pack_path_relative_token"]
    p = Path(raw).expanduser()
    if not p.is_absolute():
        reasons.append("report_resolved_pack_path_not_absolute")
    resolved = p.resolve()
    if str(p) != str(resolved):
        reasons.append("report_resolved_pack_path_not_canonical")
    if not resolved.exists():
        reasons.append("report_resolved_pack_path_not_found")
    return resolved, reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate execution report resolved_pack_path contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()

    stale_reasons: list[str] = []
    report_data: dict[str, Any] = {}
    expected_pack_path = ""
    expected_catalog_path = ""

    if not catalog_path.exists():
        stale_reasons.append("catalog_not_found")
    if not repo_catalog_path.exists():
        stale_reasons.append("repo_catalog_not_found")
    if not report_path.exists():
        stale_reasons.append("report_not_found")
    else:
        report_data = _safe_json(report_path)
        if not report_data:
            stale_reasons.append("report_invalid_json")

    if not stale_reasons:
        try:
            resolved = resolve_identity(
                args.identity_id,
                repo_catalog_path,
                catalog_path,
                allow_conflict=True,
            )
            expected_pack_path = str(Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve())
            expected_catalog_path = str(Path(str(resolved.get("catalog_path", "")).strip()).expanduser().resolve())
        except Exception as exc:
            stale_reasons.append(f"identity_resolution_failed:{exc}")

    report_pack_raw = str(report_data.get("resolved_pack_path", "")).strip()
    report_catalog_raw = str(report_data.get("catalog_path", "")).strip()
    report_pack_path = None
    if not stale_reasons:
        report_pack_path, pack_reasons = _canonical(report_pack_raw)
        stale_reasons.extend(pack_reasons)

    if not stale_reasons and report_pack_path is not None and expected_pack_path:
        if str(report_pack_path) != expected_pack_path:
            stale_reasons.append("report_resolved_pack_path_mismatch_identity_pack")

    if not stale_reasons and report_catalog_raw:
        report_catalog_path = Path(report_catalog_raw).expanduser().resolve()
        if str(report_catalog_path) != str(catalog_path):
            stale_reasons.append("report_catalog_path_mismatch_requested_catalog")
        if expected_catalog_path and str(report_catalog_path) != expected_catalog_path:
            stale_reasons.append("report_catalog_path_mismatch_resolved_catalog")

    ok = len(stale_reasons) == 0
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "report_path": str(report_path),
        "report_resolved_pack_path": report_pack_raw,
        "report_catalog_path": report_catalog_raw,
        "resolved_pack_path": expected_pack_path,
        "resolved_catalog_path": expected_catalog_path,
        "path_scope": "runtime_report",
        "path_governance_status": "PASS_REQUIRED" if ok else "FAIL_REQUIRED",
        "path_error_codes": [] if ok else [ERR_REPORT_PATH_CONTRACT],
        "stale_reasons": stale_reasons,
        "canonicalization_ref": "Path.resolve(strict=False)",
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print(
                "[OK] execution report path contract passed: "
                f"identity={args.identity_id} report={report_path}"
            )
        else:
            print(
                f"[FAIL] {ERR_REPORT_PATH_CONTRACT} execution report path contract failed: "
                f"identity={args.identity_id} report={report_path}"
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
