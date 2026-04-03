#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
DEFAULT_TEMPLATE = "identity/protocol/plugins/templates/agent-relay-final-answer.contract_v1.json"
DEFAULT_RECEIPT_SCHEMA_VERSION = "agent_relay_final_answer_receipt_v1"
DEFAULT_RELAY_SURFACE = "agent_relay_final_answer"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def resolve_path(raw: str, *, repo_root: Path) -> Path:
    candidate = Path(str(raw or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def first_nonempty_line(text: str) -> str:
    for line in str(text or "").splitlines():
        token = str(line or "").strip()
        if token:
            return token
    return ""


def normalize_source_text(text: str) -> str:
    return str(text or "").replace("\r\n", "\n").strip()


def parse_identity_context_fields(line: str) -> dict[str, str]:
    raw = str(line or "").strip()
    prefix = "Identity-Context:"
    if not raw.startswith(prefix):
        return {}
    payload = raw[len(prefix) :].strip().replace("|", ";")
    parsed: dict[str, str] = {}
    for chunk in payload.split(";"):
        piece = str(chunk or "").strip()
        if not piece or "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            parsed[key] = value
    return parsed


def extract_source_text_from_json(doc: dict[str, Any], *, target_identity_id: str) -> tuple[str, str, str, str]:
    generated_at = str(doc.get("generated_at", "")).strip()
    identity_id = str(doc.get("identity_id", "")).strip()
    if str(doc.get("last_agent_message", "")).strip():
        return (
            normalize_source_text(str(doc.get("last_agent_message", ""))),
            identity_id,
            generated_at,
            "leader_snapshot_item",
        )
    if str(doc.get("final_answer", "")).strip():
        return (
            normalize_source_text(str(doc.get("final_answer", ""))),
            identity_id,
            generated_at,
            "final_report_json",
        )
    if str(doc.get("FINAL_ANSWER", "")).strip():
        return (
            normalize_source_text(str(doc.get("FINAL_ANSWER", ""))),
            identity_id,
            generated_at,
            "final_report_json",
        )
    items = doc.get("items")
    if isinstance(items, list):
        selected: dict[str, Any] | None = None
        if target_identity_id:
            selected = next(
                (
                    item
                    for item in items
                    if isinstance(item, dict)
                    and str(item.get("identity_id", "")).strip() == target_identity_id
                    and str(item.get("last_agent_message", "")).strip()
                ),
                None,
            )
        if selected is None:
            selected = next(
                (
                    item
                    for item in items
                    if isinstance(item, dict) and str(item.get("last_agent_message", "")).strip()
                ),
                None,
            )
        if isinstance(selected, dict):
            return (
                normalize_source_text(str(selected.get("last_agent_message", ""))),
                str(selected.get("identity_id", "")).strip(),
                generated_at,
                "leader_snapshot_payload",
            )
    return "", "", generated_at, ""


def extract_source_text(path: Path, *, target_identity_id: str) -> tuple[str, str, str, str]:
    if not path.exists():
        return "", "", "", ""
    if path.suffix.lower() == ".json":
        try:
            doc = load_json(path)
        except Exception:
            return "", "", "", ""
        text, identity_id, generated_at, source_kind = extract_source_text_from_json(
            doc,
            target_identity_id=target_identity_id,
        )
        if text:
            return text, identity_id, generated_at, source_kind
    return normalize_source_text(path.read_text(encoding="utf-8")), "", "", "plain_text_final_answer"


def infer_source_snapshot_ts(path: Path, *, target_identity_id: str) -> str:
    text, _identity_id, generated_at, _source_kind = extract_source_text(
        path,
        target_identity_id=target_identity_id,
    )
    if text:
        return generated_at
    return ""


def default_delivery_authority(relay_mode: str) -> str:
    mode = str(relay_mode or "").strip().lower()
    if mode == "exact":
        return "identity_instance_output"
    if mode == "summary":
        return "ungoverned_operator_summary"
    return ""


def build_receipt(
    *,
    target_identity_id: str,
    question_tag: str,
    source_artifact: Path,
    relay_text: str,
    relay_mode: str = "exact",
    relay_surface: str = DEFAULT_RELAY_SURFACE,
    delivery_authority: str = "",
    source_snapshot_ts: str = "",
) -> dict[str, Any]:
    mode = str(relay_mode or "").strip()
    authority = str(delivery_authority or "").strip() or default_delivery_authority(mode)
    snapshot_ts = str(source_snapshot_ts or "").strip() or infer_source_snapshot_ts(
        source_artifact,
        target_identity_id=str(target_identity_id or "").strip(),
    )
    return {
        "schema_version": DEFAULT_RECEIPT_SCHEMA_VERSION,
        "relay_surface": str(relay_surface or "").strip() or DEFAULT_RELAY_SURFACE,
        "relay_mode": mode,
        "target_identity_id": str(target_identity_id or "").strip(),
        "question_tag": str(question_tag or "").strip(),
        "source_artifact": str(source_artifact),
        "source_snapshot_ts": snapshot_ts,
        "relay_text": str(relay_text or ""),
        "delivery_authority": authority,
    }


def preview(text: str, *, lines: int = 3) -> list[str]:
    return [str(line).strip() for line in normalize_source_text(text).splitlines()[:lines] if str(line).strip()]
