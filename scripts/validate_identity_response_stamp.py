#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from response_stamp_common import (
    blocker_receipt,
    render_external_stamp,
    resolve_stamp_context,
)
from tool_vendor_governance_common import contract_required, load_json

ERR_STAMP_MISMATCH = "IP-ASB-STAMP-001"
ERR_STAMP_SOURCE = "IP-ASB-STAMP-002"
ERR_STAMP_HARDCODED = "IP-ASB-STAMP-003"
ERR_STAMP_HARD_GATE = "IP-ASB-STAMP-004"
ALLOWED_SOURCES = {"project", "global", "auto", "env"}
PLACEHOLDER_RE = re.compile(r"<[^>]+>")


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "identity_response_stamp_contract",
        "response_stamp_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _resolve_pack_and_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    import yaml

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    pack = Path(pack_raw).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def _parse_stamp_line(stamp_line: str) -> dict[str, str]:
    raw = (stamp_line or "").strip()
    if not raw.startswith("Identity-Context:"):
        return {}
    body = raw.split(":", 1)[1].strip()
    pairs = [x.strip() for x in body.split(";") if x.strip()]
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _looks_redacted(token: str) -> bool:
    t = str(token or "").strip()
    if not t:
        return False
    if t.startswith("/"):
        return False
    if t.startswith("~"):
        return False
    if ":" in t and len(t) > 1 and t[1] == ":":
        return False
    return "/" not in t and "\\" not in t


def _emit_blocker(receipt_path: Path, payload: dict[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dynamic identity response stamp contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--stamp-line", default="")
    ap.add_argument("--stamp-file", default="")
    ap.add_argument("--stamp-json", default="", help="render payload json file containing external_stamp field")
    ap.add_argument("--require-dynamic", action="store_true")
    ap.add_argument("--require-redacted-external", action="store_true")
    ap.add_argument("--require-lock-match", action="store_true")
    ap.add_argument(
        "--enforce-user-visible-gate",
        action="store_true",
        help="hard gate for user-visible reply channel; disables contract-not-required skip path",
    )
    ap.add_argument("--force-check", action="store_true", help="run checks even when contract.required is false")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        _, task_path = _resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    force_required = bool(args.force_check or args.enforce_user_visible_gate)
    if not force_required and not contract_required(contract):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "stamp_status": "SKIPPED_NOT_REQUIRED",
            "error_code": "",
            "stale_reasons": ["contract_not_required"],
            "required_contract": False,
        }
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"[OK] response stamp contract not required for identity={args.identity_id}; skipped")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        ctx = resolve_stamp_context(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            actor_id=args.actor_id,
            explicit_catalog=bool(args.catalog.strip()),
        )
    except Exception as exc:
        print(f"[FAIL] unable to resolve stamp context: {exc}")
        return 1

    if args.stamp_line.strip():
        stamp_line = args.stamp_line.strip()
    elif args.stamp_file.strip():
        stamp_path = Path(args.stamp_file).expanduser().resolve()
        if not stamp_path.exists():
            print(f"[FAIL] stamp file not found: {stamp_path}")
            return 1
        lines = [x.strip() for x in stamp_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        stamp_line = lines[0] if lines else ""
    elif args.stamp_json.strip():
        stamp_json_path = Path(args.stamp_json).expanduser().resolve()
        if not stamp_json_path.exists():
            print(f"[FAIL] stamp json file not found: {stamp_json_path}")
            return 1
        try:
            stamp_json_payload = json.loads(stamp_json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] stamp json invalid: {stamp_json_path} ({exc})")
            return 1
        if not isinstance(stamp_json_payload, dict):
            print(f"[FAIL] stamp json payload must be object: {stamp_json_path}")
            return 1
        stamp_line = str(stamp_json_payload.get("external_stamp", "")).strip()
    else:
        if args.enforce_user_visible_gate:
            stamp_line = ""
        else:
            stamp_line = render_external_stamp(ctx)

    parsed = _parse_stamp_line(stamp_line)
    stale_reasons: list[str] = []
    error_code = ""

    if args.enforce_user_visible_gate and not stamp_line:
        stale_reasons.append("missing_user_visible_identity_context_stamp")
        error_code = ERR_STAMP_HARD_GATE

    required_keys = ("actor_id", "identity_id", "catalog_ref", "pack_ref", "scope", "lock", "lease", "source")
    if not error_code:
        missing = [k for k in required_keys if not parsed.get(k)]
        if missing:
            stale_reasons.append(f"missing_fields:{','.join(missing)}")
            error_code = ERR_STAMP_HARDCODED

    if not error_code and (PLACEHOLDER_RE.search(stamp_line) or "identity_id=<" in stamp_line):
        stale_reasons.append("placeholder_leakage_detected")
        error_code = ERR_STAMP_HARDCODED

    actual_identity = parsed.get("identity_id", "")
    require_dynamic = bool(args.require_dynamic or args.enforce_user_visible_gate)
    require_redacted_external = bool(args.require_redacted_external or args.enforce_user_visible_gate)
    require_lock_match = bool(args.require_lock_match or args.enforce_user_visible_gate)

    if not error_code and require_dynamic:
        if actual_identity != ctx.identity_id:
            stale_reasons.append("identity_id_mismatch")
            error_code = ERR_STAMP_MISMATCH

    if not error_code and require_redacted_external:
        if not _looks_redacted(parsed.get("catalog_ref", "")) or not _looks_redacted(parsed.get("pack_ref", "")):
            stale_reasons.append("external_ref_not_redacted")
            error_code = ERR_STAMP_HARDCODED

    source = parsed.get("source", "")
    if not error_code:
        if source not in ALLOWED_SOURCES:
            stale_reasons.append("source_domain_invalid")
            error_code = ERR_STAMP_SOURCE
        elif source != ctx.source_domain:
            stale_reasons.append("source_domain_mismatch")
            error_code = ERR_STAMP_SOURCE

    if not error_code and require_lock_match:
        if parsed.get("lock", "") != ctx.lock_state:
            stale_reasons.append("lock_state_mismatch")
            error_code = ERR_STAMP_MISMATCH

    ok = error_code == ""
    receipt_path = (
        Path(args.blocker_receipt_out).expanduser().resolve()
        if args.blocker_receipt_out.strip()
        else Path(f"/tmp/identity-stamp-blocker-receipt-{args.identity_id}.json").resolve()
    )

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "stamp_line": stamp_line,
        "parsed_fields": parsed,
        "expected_context": {
            "identity_id": ctx.identity_id,
            "lock_state": ctx.lock_state,
            "source_domain": ctx.source_domain,
            "catalog_ref": ctx.catalog_ref,
            "pack_ref": ctx.pack_ref,
        },
        "stamp_status": "PASS" if ok else "FAIL",
        "error_code": error_code,
        "stale_reasons": stale_reasons,
        "blocker_receipt_path": str(receipt_path) if not ok else "",
    }

    if not ok:
        receipt = blocker_receipt(
            error_code=error_code,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=actual_identity,
            source_domain=source or ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/active_identity.json",
            next_action="refresh_identity_binding_then_retry",
        )
        _emit_blocker(receipt_path, receipt)
        payload["blocker_receipt"] = receipt

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if ok:
            print(f"[OK] response stamp validated for identity={args.identity_id}")
            print("validate_identity_response_stamp PASSED")
        else:
            print(f"[FAIL] {error_code} response stamp validation failed for identity={args.identity_id}")
            print(f"blocker_receipt={receipt_path}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
