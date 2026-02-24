#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path

from resolve_identity_context import resolve_identity

REQ_FIELDS = [
    "identity_prompt_path",
    "identity_prompt_sha256",
    "identity_prompt_activated_at",
    "identity_prompt_source_layer",
    "identity_prompt_status",
]

ALLOWED_STATUS = {"ACTIVATED", "PRESENT", "STALE", "TEMPLATE_ONLY", "MISSING", "READ_ERROR", "PLACEHOLDER_OR_TOO_SHORT"}


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report root must be object")
    return data


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _auto_report(identity_id: str, catalog: str) -> Path:
    ctx = resolve_identity(
        identity_id,
        Path("identity/catalog/identities.yaml").resolve(),
        Path(catalog).expanduser().resolve(),
        preferred_scope="",
        allow_conflict=True,
    )
    pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    runtime_reports = pack / "runtime" / "reports"
    matched = sorted(runtime_reports.glob(f"identity-upgrade-exec-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    matched = [p for p in matched if not p.name.endswith("-patch-plan.json")]
    if not matched:
        raise FileNotFoundError(f"no execution report found under {runtime_reports}")
    return matched[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity prompt activation evidence in upgrade execution report")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="", help="runtime catalog path (required when --report is not provided)")
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    if args.report:
        report_path = Path(args.report).expanduser().resolve()
    else:
        if not args.catalog:
            print("[FAIL] --catalog is required when --report is omitted")
            return 2
        try:
            report_path = _auto_report(args.identity_id, args.catalog)
        except Exception as exc:
            print(f"[FAIL] {exc}")
            return 2

    if not report_path.exists():
        print(f"[FAIL] report not found: {report_path}")
        return 1

    try:
        report = _load_json(report_path)
    except Exception as exc:
        print(f"[FAIL] invalid report json: {exc}")
        return 1

    missing = [k for k in REQ_FIELDS if not str(report.get(k, "")).strip()]
    if missing:
        print(f"[FAIL] prompt activation fields missing/empty: {missing}")
        return 1

    status = str(report.get("identity_prompt_status") or "")
    if status not in ALLOWED_STATUS:
        print(f"[FAIL] identity_prompt_status invalid: {status}")
        return 1

    prompt_path = Path(str(report.get("identity_prompt_path") or "")).expanduser().resolve()
    if not prompt_path.exists():
        print(f"[FAIL] identity prompt file missing on disk: {prompt_path}")
        return 1

    disk_hash = _sha256_text(prompt_path.read_text(encoding="utf-8", errors="ignore"))
    report_hash = str(report.get("identity_prompt_sha256") or "")
    if disk_hash != report_hash:
        print("[FAIL] identity prompt hash mismatch between report and disk")
        print(f"       report={report_hash}")
        print(f"       disk={disk_hash}")
        return 1

    source_layer = str(report.get("identity_prompt_source_layer") or "")
    if source_layer not in {"project", "global"}:
        print(f"[FAIL] identity_prompt_source_layer must be project|global, got={source_layer}")
        return 1

    print(f"[OK] prompt activation validated: {report_path}")
    print(f"     identity_prompt_status={status} source_layer={source_layer}")
    print(f"     identity_prompt_path={prompt_path}")
    print(f"     identity_prompt_sha256={report_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
