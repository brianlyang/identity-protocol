#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import ensure_index_linkage, normalize_feedback_path_under_root, rel_to_feedback_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def utc_now_z() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_compact_token() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def safe_feedback_slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip("-._")
    return token or "batch"


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = str(text or "")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8")
    return path


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _path_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def ensure_markdown_title(*, title: str, body: str) -> str:
    title_text = str(title or "").strip()
    normalized = str(body or "")
    if title_text and not normalized.lstrip().startswith("#"):
        return f"# {title_text}\n\n{normalized}"
    return normalized


def collect_feedback_outbox_seed_refs(outbox_dir: Path, feedback_root: Path, *, max_refs: int = 24) -> list[str]:
    refs: list[str] = []
    if not outbox_dir.exists():
        return refs
    for path in sorted(outbox_dir.glob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("FEEDBACK_BATCH_"):
            continue
        refs.append(rel_to_feedback_root(path, feedback_root))
        if len(refs) >= max_refs:
            break
    return refs


def collect_feedback_atomic_seed_refs(feedback_root: Path, *, max_refs: int = 24) -> list[str]:
    atomic_dir = (feedback_root / "atomic").resolve()
    refs: list[str] = []
    if not atomic_dir.exists():
        return refs
    for pattern in ("*.batch.json", "*.index.json", "*.receipt.json"):
        for path in sorted(atomic_dir.glob(pattern)):
            if not path.is_file():
                continue
            refs.append(rel_to_feedback_root(path, feedback_root))
            if len(refs) >= max_refs:
                return refs
    return refs


def render_protocol_feedback_ssot_archival_bootstrap_body(
    *,
    identity_id: str,
    generated_at_utc: str,
    feedback_root: Path,
    outbox_seed_refs: list[str],
    atomic_seed_refs: list[str],
    source_file_count: int,
    source_mode: str,
) -> str:
    lines = [
        "identity_id: " + str(identity_id or "").strip(),
        "archival_mode: ssot_bootstrap",
        "source_mode: " + str(source_mode or "").strip(),
        "generated_at_utc: " + str(generated_at_utc or "").strip(),
        "feedback_root: " + feedback_root.as_posix(),
        "source_file_count: " + str(int(source_file_count)),
        "canonical_outbox_ref_count: " + str(len(outbox_seed_refs)),
        "atomic_ref_count: " + str(len(atomic_seed_refs)),
        "",
        "## Canonical outbox refs",
    ]
    if outbox_seed_refs:
        lines.extend(f"- {ref}" for ref in outbox_seed_refs)
    else:
        lines.append("- none")
    lines.extend(["", "## Atomic transaction refs"])
    if atomic_seed_refs:
        lines.extend(f"- {ref}" for ref in atomic_seed_refs)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def materialize_feedback_channel_artifacts(
    *,
    feedback_root: Path,
    channel_dir: Path,
    index_path: Path,
    identity_id: str,
    catalog_path: str,
    body: str,
    title: str,
    slug: str,
    lane: str = "outbox",
    summary_payload: dict[str, Any] | None = None,
    section_title: str = "Protocol feedback linkage auto",
    extra_receipt_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    token = utc_compact_token()
    slug_token = safe_feedback_slug(slug or title or "batch")
    normalized_lane = str(lane or "outbox").strip().lower()
    if normalized_lane == "outbox":
        batch_name = f"FEEDBACK_BATCH_{token}_{slug_token}.md"
        receipt_name = f"PROTOCOL_FEEDBACK_RECEIPT_{token}_{slug_token}.json"
        summary_name = f"SUMMARY_{token}_{slug_token}.json"
    elif normalized_lane == "inbox":
        batch_name = f"PROTOCOL_INBOX_{token}_{slug_token}.md"
        receipt_name = f"PROTOCOL_INBOX_RECEIPT_{token}_{slug_token}.json"
        summary_name = f"INBOX_SUMMARY_{token}_{slug_token}.json"
    else:
        raise ValueError(f"unsupported feedback lane: {normalized_lane}")

    expected_leaf = "outbox-to-protocol" if normalized_lane == "outbox" else "inbox-from-protocol"
    channel_dir = normalize_feedback_path_under_root(
        feedback_root,
        channel_dir,
        default_leaf=expected_leaf,
    )
    index_path = normalize_feedback_path_under_root(
        feedback_root,
        index_path,
        default_leaf="evidence-index/INDEX.md",
    )
    if not _path_under(feedback_root, channel_dir):
        raise ValueError(f"channel_dir_not_under_feedback_root:{channel_dir}")
    if not _path_under(feedback_root, index_path):
        raise ValueError(f"index_path_not_under_feedback_root:{index_path}")

    batch_path = (channel_dir / batch_name).resolve()
    receipt_path = (channel_dir / receipt_name).resolve()
    batch_rel = rel_to_feedback_root(batch_path, feedback_root)
    receipt_rel = rel_to_feedback_root(receipt_path, feedback_root)
    summary_ref = ""

    write_text(batch_path, ensure_markdown_title(title=title, body=body))

    if isinstance(summary_payload, dict):
        summary_path = (channel_dir / summary_name).resolve()
        write_json(summary_path, summary_payload)
        summary_ref = rel_to_feedback_root(summary_path, feedback_root)

    generated_at_utc = utc_now_z()
    receipt_payload: dict[str, Any] = {
        "identity_id": str(identity_id or "").strip(),
        "catalog_path": str(catalog_path or "").strip(),
        "feedback_root": str(feedback_root),
        "lane": normalized_lane,
        "channel_dir": str(channel_dir),
        "batch_path": str(batch_path),
        "batch_ref": batch_rel,
        "summary_ref": summary_ref,
        "receipt_ref": receipt_rel,
        "generated_at_utc": generated_at_utc,
        "protocol_feedback_emit_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }
    if isinstance(extra_receipt_fields, dict) and extra_receipt_fields:
        receipt_payload.update(extra_receipt_fields)
    write_json(receipt_path, receipt_payload)

    refs = [batch_rel, receipt_rel] + ([summary_ref] if summary_ref else [])
    _, linked = ensure_index_linkage(index_path, refs=refs, section_title=section_title)

    receipt_payload["protocol_feedback_emit_status"] = STATUS_PASS_REQUIRED if linked else STATUS_FAIL_REQUIRED
    receipt_payload["error_code"] = "" if linked else "IP-GOV-FEEDBACK-002"
    receipt_payload["stale_reasons"] = [] if linked else ["feedback_index_linkage_missing"]
    receipt_payload["index_linked"] = bool(linked)
    write_json(receipt_path, receipt_payload)

    return {
        "batch_path": str(batch_path),
        "batch_ref": batch_rel,
        "receipt_path": str(receipt_path),
        "receipt_ref": receipt_rel,
        "summary_ref": summary_ref,
        "index_path": str(index_path),
        "index_linked": bool(linked),
        "protocol_feedback_emit_status": STATUS_PASS_REQUIRED if linked else STATUS_FAIL_REQUIRED,
        "error_code": "" if linked else "IP-GOV-FEEDBACK-002",
        "stale_reasons": [] if linked else ["feedback_index_linkage_missing"],
    }


def materialize_feedback_outbox_batch(
    *,
    feedback_root: Path,
    outbox_dir: Path,
    index_path: Path,
    identity_id: str,
    catalog_path: str,
    body: str,
    title: str,
    slug: str,
    summary_payload: dict[str, Any] | None = None,
    section_title: str = "Protocol feedback linkage auto",
    extra_receipt_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return materialize_feedback_channel_artifacts(
        feedback_root=feedback_root,
        channel_dir=outbox_dir,
        index_path=index_path,
        identity_id=identity_id,
        catalog_path=catalog_path,
        body=body,
        title=title,
        slug=slug,
        lane="outbox",
        summary_payload=summary_payload,
        section_title=section_title,
        extra_receipt_fields=extra_receipt_fields,
    )
