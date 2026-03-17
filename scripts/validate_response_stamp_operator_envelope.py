#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from response_stamp_common import (
    DEFAULT_RESPONSE_STAMP_TEMPLATE_REF,
    normalize_response_stamp_profile,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_machine_line(line: str) -> dict[str, str]:
    prefix = "Machine-Verification: "
    if not str(line).startswith(prefix):
        return {}
    payload = str(line)[len(prefix) :].strip()
    if not payload:
        return {}
    out: dict[str, str] = {}
    for item in payload.split(";"):
        token = str(item).strip()
        if not token or "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[str(key).strip()] = str(value).strip()
    return out


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate shared operator response-stamp envelope.")
    ap.add_argument("--stamp-json", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    stamp_path = Path(args.stamp_json).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not stamp_path.exists():
        print(f"[FAIL] stamp json not found: {stamp_path}")
        return 2

    payload = _load_json(stamp_path)
    if not isinstance(payload, dict):
        print("[FAIL] stamp json must decode to an object")
        return 2

    response_stamp_profile = normalize_response_stamp_profile(payload.get("response_stamp_profile"))
    template_ref = str(response_stamp_profile.get("template_ref", "")).strip() or DEFAULT_RESPONSE_STAMP_TEMPLATE_REF
    template_path = (repo_root / template_ref).resolve() if not Path(template_ref).is_absolute() else Path(template_ref)
    stale_reasons: list[str] = []

    template_doc: dict[str, Any] = {}
    if not template_path.exists():
        stale_reasons.append("operator_template_missing")
    else:
        doc = _load_json(template_path)
        template_doc = doc if isinstance(doc, dict) else {}

    operator_lines = payload.get("operator_envelope_lines")
    if not isinstance(operator_lines, list):
        operator_lines = []
    operator_lines = [str(line).strip() for line in operator_lines if str(line).strip()]
    if not operator_lines:
        display_line = str(payload.get("display_headstamp_line", "")).strip()
        machine_line = str(payload.get("machine_verification_line", "")).strip()
        if display_line:
            operator_lines.append(display_line)
        if machine_line:
            operator_lines.append(machine_line)

    display_line = operator_lines[0] if len(operator_lines) >= 1 else ""
    machine_line = operator_lines[1] if len(operator_lines) >= 2 else ""
    external_stamp = str(payload.get("external_stamp", "")).strip()
    expected_display_line = f"Display-Headstamp: {external_stamp}" if external_stamp else ""

    if not response_stamp_profile.get("enabled", False):
        stale_reasons.append("response_stamp_profile_disabled")
    if str(response_stamp_profile.get("format", "")).strip() != "structured_block":
        stale_reasons.append("response_stamp_profile_format_not_structured_block")
    if display_line != expected_display_line:
        stale_reasons.append("display_headstamp_line_mismatch")
    if not machine_line.startswith("Machine-Verification: "):
        stale_reasons.append("machine_verification_line_missing")

    machine_fields = _parse_machine_line(machine_line)
    template_required_fields = []
    if template_doc:
        template_required_fields = list(((template_doc.get("machine_segment") or {}).get("required_fields") or []))
    if not template_required_fields:
        template_required_fields = [
            "verification_source",
            "display_headstamp_identity_id",
            "authoritative_identity_id",
            "headstamp_consistency_status",
        ]
    missing_machine_fields = [field for field in template_required_fields if not str(machine_fields.get(field, "")).strip()]
    if missing_machine_fields:
        stale_reasons.extend(f"machine_verification_field_missing:{field}" for field in missing_machine_fields)

    expected_machine_payload = payload.get("machine_verification")
    if not isinstance(expected_machine_payload, dict):
        expected_machine_payload = {}
    for field in template_required_fields:
        expected_value = _stringify(
            expected_machine_payload.get(field, payload.get(field, ""))
        )
        actual_value = str(machine_fields.get(field, "")).strip()
        if expected_value and actual_value and expected_value != actual_value:
            stale_reasons.append(f"machine_verification_field_mismatch:{field}")

    if (
        str(machine_fields.get("display_headstamp_identity_id", "")).strip()
        and str(machine_fields.get("authoritative_identity_id", "")).strip()
        and str(machine_fields.get("display_headstamp_identity_id", "")).strip()
        == str(machine_fields.get("authoritative_identity_id", "")).strip()
        and str(machine_fields.get("headstamp_consistency_status", "")).strip() != STATUS_PASS_REQUIRED
    ):
        stale_reasons.append("machine_verification_consistency_projection_invalid")

    status = STATUS_FAIL_REQUIRED if stale_reasons else STATUS_PASS_REQUIRED
    out = {
        "operator_headstamp_envelope_status": status,
        "response_stamp_profile_status": STATUS_PASS_REQUIRED if response_stamp_profile.get("enabled", False) else STATUS_FAIL_REQUIRED,
        "response_stamp_profile": response_stamp_profile,
        "operator_template_ref": template_ref,
        "operator_template_path": str(template_path),
        "operator_template_status": STATUS_PASS_REQUIRED if template_doc else STATUS_FAIL_REQUIRED,
        "operator_envelope_line_count": len(operator_lines),
        "display_headstamp_line": display_line,
        "machine_verification_line": machine_line,
        "parsed_machine_verification": machine_fields,
        "missing_machine_fields": missing_machine_fields,
        "stale_reasons": stale_reasons,
    }
    if args.json_only:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
