#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from response_stamp_common import blocker_receipt, resolve_stamp_context
from tool_vendor_governance_common import contract_required, load_json

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPLY_FIRST_LINE = "IP-ASB-STAMP-SESSION-001"
STRICT_LOCK_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "validate"}


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    # Reuse response stamp contract, while allowing explicit first-line contract key.
    for key in (
        "reply_identity_context_first_line_contract_v1",
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


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _emit_blocker(receipt_path: Path, payload: dict[str, Any]) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate that user-visible assistant replies start with Identity-Context first line.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--reply-log", default="", help="assistant reply evidence (.json/.jsonl/.txt)")
    ap.add_argument("--reply-file", default="", help="single reply text file")
    ap.add_argument("--reply-text", default="", help="inline single reply text")
    ap.add_argument("--stamp-json", default="", help="optional rendered stamp payload json (external_stamp field)")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-first-line-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "mutation", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
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
    force_required = bool(args.force_check or args.enforce_first_line_gate)
    if not force_required and not contract_required(contract):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "required_contract": False,
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "reply_sample_count": 0,
            "blocker_receipt_path": "",
            "stale_reasons": ["contract_not_required"],
        }
        _emit(payload, json_only=args.json_only)
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
    evidence_ref = ""
    if args.reply_log.strip():
        p = Path(args.reply_log).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] reply log file not found: {p}")
            return 1
        reply_samples = _extract_reply_samples(p)
        evidence_ref = str(p)
    elif args.reply_file.strip():
        p = Path(args.reply_file).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] reply file not found: {p}")
            return 1
        reply_samples = [p.read_text(encoding="utf-8", errors="ignore")]
        evidence_ref = str(p)
    elif args.reply_text.strip():
        reply_samples = [args.reply_text]
        evidence_ref = "inline:reply_text"
    elif args.stamp_json.strip():
        p = Path(args.stamp_json).expanduser().resolve()
        if not p.exists():
            print(f"[FAIL] stamp json not found: {p}")
            return 1
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FAIL] invalid stamp json: {p} ({exc})")
            return 1
        if not isinstance(doc, dict):
            print(f"[FAIL] stamp json payload must be object: {p}")
            return 1
        stamp_line = str(doc.get("external_stamp", "")).strip()
        reply_samples = [stamp_line] if stamp_line else []
        evidence_ref = str(p)

    first_lines = [_first_nonempty_line(x) for x in reply_samples]
    first_lines = [x for x in first_lines if x]

    missing_refs: list[str] = []
    for idx, line in enumerate(first_lines, start=1):
        if not line.startswith("Identity-Context:"):
            missing_refs.append(f"sample:{idx}")

    stale_reasons: list[str] = []
    error_code = ""

    if args.enforce_first_line_gate and len(first_lines) == 0:
        stale_reasons.append("reply_evidence_missing")
        error_code = ERR_REPLY_FIRST_LINE

    if len(missing_refs) > 0:
        stale_reasons.append("reply_first_line_identity_context_missing")
        if not error_code:
            error_code = ERR_REPLY_FIRST_LINE

    # Optional identity mismatch signal if first line exists and parsable.
    if not error_code and first_lines:
        parsed = _parse_stamp_line(first_lines[0])
        actual_identity = str(parsed.get("identity_id", "")).strip()
        if actual_identity and actual_identity != ctx.identity_id:
            stale_reasons.append("reply_first_line_identity_mismatch")
            error_code = ERR_REPLY_FIRST_LINE

    lock_boundary_enforced = bool(args.enforce_first_line_gate and args.operation in STRICT_LOCK_OPERATIONS)
    parsed_lock_state = ""
    if not error_code and first_lines:
        parsed_lock_state = str(_parse_stamp_line(first_lines[0]).get("lock", "")).strip()
    if not error_code and lock_boundary_enforced:
        if ctx.lock_state != "LOCK_MATCH":
            stale_reasons.append("actor_binding_lock_not_match")
            error_code = ERR_REPLY_FIRST_LINE
        elif parsed_lock_state and parsed_lock_state != "LOCK_MATCH":
            stale_reasons.append("reply_first_line_lock_not_match")
            error_code = ERR_REPLY_FIRST_LINE

    ok = error_code == ""
    receipt_path = (
        Path(args.blocker_receipt_out).expanduser().resolve()
        if args.blocker_receipt_out.strip()
        else Path(f"/tmp/identity-reply-first-line-blocker-receipt-{args.identity_id}.json").resolve()
    )

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": bool(force_required or contract_required(contract)),
        "reply_first_line_status": STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED,
        "error_code": error_code,
        "lock_boundary_enforced": lock_boundary_enforced,
        "expected_lock_state": ctx.lock_state,
        "reply_first_line_lock_state": parsed_lock_state,
        "reply_first_line_missing_count": len(missing_refs),
        "reply_first_line_missing_refs": missing_refs,
        "reply_sample_count": len(first_lines),
        "reply_evidence_ref": evidence_ref,
        "expected_identity_id": ctx.identity_id,
        "blocker_receipt_path": str(receipt_path) if not ok else "",
        "stale_reasons": stale_reasons,
    }

    if not ok:
        first_line_identity = ""
        if first_lines:
            parsed = _parse_stamp_line(first_lines[0])
            first_line_identity = str(parsed.get("identity_id", "")).strip()
        receipt = blocker_receipt(
            error_code=ERR_REPLY_FIRST_LINE,
            expected_identity_id=ctx.identity_id,
            actual_identity_id=first_line_identity or "MISSING_STAMP",
            source_domain=ctx.source_domain,
            resolver_ref=f"{catalog_path.parent}/session/actors",
            next_action="emit_identity_context_first_line_then_retry",
        )
        _emit_blocker(receipt_path, receipt)
        payload["blocker_receipt"] = receipt
    else:
        if receipt_path.exists():
            try:
                receipt_path.unlink()
            except Exception:
                pass

    _emit(payload, json_only=args.json_only)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
