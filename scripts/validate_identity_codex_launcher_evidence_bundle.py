#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_codex_launcher_evidence_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    inspect_launcher_convergence_payload_bundle,
    inspect_launcher_convergence_receipt_bundle,
    load_json,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate identity-codex launcher evidence bundle refs, manifest kinds, and mirror digests."
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--payload-json", default="")
    mode.add_argument("--receipt-path", default="")
    ap.add_argument("--require-ref-field", action="append", default=[])
    ap.add_argument("--expected-kind", action="append", default=[])
    ap.add_argument("--require-summary-ref", action="store_true")
    ap.add_argument("--require-self-evidence-ref-match", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "status": STATUS_FAIL_REQUIRED,
        "mode": "receipt" if str(args.receipt_path).strip() else "payload",
        "payload_json": str(Path(args.payload_json).expanduser().resolve()) if str(args.payload_json).strip() else "",
        "receipt_path": str(Path(args.receipt_path).expanduser().resolve()) if str(args.receipt_path).strip() else "",
        "required_ref_fields": [str(field).strip() for field in args.require_ref_field if str(field).strip()],
        "expected_kinds": [str(kind).strip() for kind in args.expected_kind if str(kind).strip()],
        "require_summary_ref": bool(args.require_summary_ref),
        "require_self_evidence_ref_match": bool(args.require_self_evidence_ref_match),
    }
    try:
        if str(args.payload_json).strip():
            payload_doc = load_json(Path(args.payload_json))
            inspection = inspect_launcher_convergence_payload_bundle(
                payload=payload_doc,
                required_ref_fields=args.require_ref_field,
                expected_kinds=args.expected_kind,
                require_summary_ref=bool(args.require_summary_ref),
            )
            payload["inspected_payload_status"] = str(payload_doc.get("status", "")).strip()
        else:
            inspection = inspect_launcher_convergence_receipt_bundle(
                receipt_path=Path(args.receipt_path),
                expected_kinds=args.expected_kind,
                require_summary_ref=bool(args.require_summary_ref),
                require_self_evidence_ref_match=bool(args.require_self_evidence_ref_match),
            )
        payload.update(inspection)
        payload["status"] = str(inspection.get("status", "")).strip() or STATUS_FAIL_REQUIRED
        _emit(payload, json_only=bool(args.json_only))
        return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1
    except Exception as exc:
        payload["errors"] = [f"{type(exc).__name__}:{exc}"]
        _emit(payload, json_only=bool(args.json_only))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
