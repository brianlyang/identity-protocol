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


def _message_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif isinstance(item.get("content"), str):
                    parts.append(str(item.get("content")))
        return "\n".join([x for x in parts if x]).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return str(value.get("text"))
        if isinstance(value.get("content"), str):
            return str(value.get("content"))
    return ""


def _extract_reply_samples(reply_log_path: Path) -> list[str]:
    text = reply_log_path.read_text(encoding="utf-8", errors="ignore")
    suffix = reply_log_path.suffix.lower()

    if suffix == ".jsonl":
        out: list[str] = []
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            role = str(row.get("role", "")).strip().lower()
            if role and role not in {"assistant", "ai", "model"}:
                continue
            msg = _message_to_text(row.get("content"))
            if not msg:
                msg = _message_to_text(row.get("message"))
            if not msg:
                msg = _message_to_text(row.get("output"))
            if msg:
                out.append(msg)
        return out

    if suffix == ".json":
        try:
            doc = json.loads(text)
        except Exception:
            doc = None
        out: list[str] = []
        if isinstance(doc, dict):
            replies = doc.get("replies")
            if isinstance(replies, list):
                for item in replies:
                    msg = _message_to_text(item)
                    if msg:
                        out.append(msg)
            messages = doc.get("messages")
            if isinstance(messages, list):
                for row in messages:
                    if not isinstance(row, dict):
                        continue
                    role = str(row.get("role", "")).strip().lower()
                    if role and role not in {"assistant", "ai", "model"}:
                        continue
                    msg = _message_to_text(row.get("content"))
                    if msg:
                        out.append(msg)
            if not out:
                msg = _message_to_text(doc.get("content"))
                if msg:
                    out.append(msg)
        elif isinstance(doc, list):
            for item in doc:
                msg = _message_to_text(item)
                if msg:
                    out.append(msg)
        return out

    chunks = [x.strip() for x in text.split("\n---\n") if x.strip()]
    if chunks:
        return chunks
    return [x.strip() for x in text.splitlines() if x.strip()]


def _first_nonempty_line(text: str) -> str:
    for line in str(text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dynamic identity response stamp contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--stamp-line", default="")
    ap.add_argument("--stamp-file", default="")
    ap.add_argument("--stamp-json", default="", help="render payload json file containing external_stamp field")
    ap.add_argument(
        "--reply-log",
        default="",
        help=(
            "optional reply evidence file (.json/.jsonl/.txt). "
            "when provided, each assistant reply is checked for first-line Identity-Context stamp."
        ),
    )
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

    reply_samples: list[str] = []
    if args.reply_log.strip():
        reply_log_path = Path(args.reply_log).expanduser().resolve()
        if not reply_log_path.exists():
            print(f"[FAIL] reply log file not found: {reply_log_path}")
            return 1
        reply_samples = _extract_reply_samples(reply_log_path)
        stamp_line = _first_nonempty_line(reply_samples[0]) if reply_samples else ""
    elif args.stamp_line.strip():
        stamp_line = args.stamp_line.strip()
        reply_samples = [stamp_line]
    elif args.stamp_file.strip():
        stamp_path = Path(args.stamp_file).expanduser().resolve()
        if not stamp_path.exists():
            print(f"[FAIL] stamp file not found: {stamp_path}")
            return 1
        lines = [x.strip() for x in stamp_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        stamp_line = lines[0] if lines else ""
        reply_samples = [stamp_line] if stamp_line else []
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
        reply_samples = [stamp_line] if stamp_line else []
    else:
        if args.enforce_user_visible_gate:
            stamp_line = ""
            reply_samples = []
        else:
            stamp_line = render_external_stamp(ctx)
            reply_samples = [stamp_line]

    sample_first_lines = [_first_nonempty_line(x) for x in reply_samples]
    sample_first_lines = [x for x in sample_first_lines if x]
    reply_stamp_missing_refs = [
        idx for idx, line in enumerate(sample_first_lines, start=1) if not line.startswith("Identity-Context:")
    ]
    reply_stamp_missing_count = len(reply_stamp_missing_refs)
    reply_sample_count = len(sample_first_lines)

    if not stamp_line and sample_first_lines:
        stamp_line = sample_first_lines[0]

    parsed = _parse_stamp_line(stamp_line)
    stale_reasons: list[str] = []
    error_code = ""

    if args.enforce_user_visible_gate and (reply_sample_count == 0 or not stamp_line):
        stale_reasons.append("missing_user_visible_identity_context_stamp")
        error_code = ERR_STAMP_HARD_GATE
    if args.enforce_user_visible_gate and reply_stamp_missing_count > 0 and not error_code:
        stale_reasons.append("reply_stamp_missing_in_replay_window")
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
        "reply_sample_count": reply_sample_count,
        "reply_stamp_missing_count": reply_stamp_missing_count,
        "reply_stamp_missing_refs": reply_stamp_missing_refs,
        "blocker_receipt_path": str(receipt_path) if not ok else "",
    }

    if not ok:
        actual_identity_for_receipt = actual_identity or "MISSING_STAMP"
        receipt = blocker_receipt(
            error_code=error_code,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=actual_identity_for_receipt,
            source_domain=source or ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/active_identity.json",
            next_action="refresh_identity_binding_then_retry",
        )
        _emit_blocker(receipt_path, receipt)
        payload["blocker_receipt"] = receipt
    else:
        # Ensure deterministic behavior for follow-up blocker-receipt validation:
        # a previous failed run may have left a stale blocker receipt at the same path.
        if receipt_path.exists():
            try:
                receipt_path.unlink()
            except Exception:
                pass

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
