#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_LIVE,
    HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_SHADOW,
    HOST_VISIBLE_SURFACE_STATE_FILE,
)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def resolve_pack_runtime_path(pack_path: Path, raw_path: str, fallback_rel: str) -> Path:
    token = _normalize_text(raw_path) or _normalize_text(fallback_rel)
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def mirror_pack_runtime_path_under_shadow_root(
    *,
    pack_path: Path,
    resolved_path: Path,
    shadow_root: Path,
) -> Path:
    pack_root = pack_path.expanduser().resolve()
    target = resolved_path.expanduser().resolve()
    shadow = shadow_root.expanduser().resolve()
    try:
        relative = target.relative_to(pack_root)
    except ValueError:
        relative = Path(target.name)
    return (shadow / relative).resolve()


def resolve_host_visible_surface_runtime_paths(
    *,
    pack_path: Path,
    contract: dict[str, Any] | None,
    shadow_root: str = "",
) -> dict[str, Any]:
    contract_doc = contract if isinstance(contract, dict) else {}
    live_state_path = resolve_pack_runtime_path(
        pack_path,
        _normalize_text(contract_doc.get("runtime_state_file", "")),
        HOST_VISIBLE_SURFACE_STATE_FILE,
    )
    live_receipt_pattern_path = resolve_pack_runtime_path(
        pack_path,
        _normalize_text(contract_doc.get("runtime_receipt_pattern", "")),
        HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    )
    live_post_check_closure_state_path = resolve_pack_runtime_path(
        pack_path,
        _normalize_text(contract_doc.get("post_check_closure_state_file", "")),
        HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    )

    shadow_root_token = _normalize_text(shadow_root)
    if not shadow_root_token:
        return {
            "runtime_scope": HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_LIVE,
            "runtime_shadow_root": "",
            "live_runtime_state_path": str(live_state_path),
            "live_runtime_receipt_pattern_path": str(live_receipt_pattern_path),
            "live_post_check_closure_state_path": str(live_post_check_closure_state_path),
            "runtime_state_path": str(live_state_path),
            "runtime_receipt_pattern_path": str(live_receipt_pattern_path),
            "post_check_closure_state_path": str(live_post_check_closure_state_path),
        }

    shadow_root_path = Path(shadow_root_token).expanduser().resolve()
    runtime_state_path = mirror_pack_runtime_path_under_shadow_root(
        pack_path=pack_path,
        resolved_path=live_state_path,
        shadow_root=shadow_root_path,
    )
    runtime_receipt_pattern_path = mirror_pack_runtime_path_under_shadow_root(
        pack_path=pack_path,
        resolved_path=live_receipt_pattern_path,
        shadow_root=shadow_root_path,
    )
    post_check_closure_state_path = mirror_pack_runtime_path_under_shadow_root(
        pack_path=pack_path,
        resolved_path=live_post_check_closure_state_path,
        shadow_root=shadow_root_path,
    )
    return {
        "runtime_scope": HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_SHADOW,
        "runtime_shadow_root": str(shadow_root_path),
        "live_runtime_state_path": str(live_state_path),
        "live_runtime_receipt_pattern_path": str(live_receipt_pattern_path),
        "live_post_check_closure_state_path": str(live_post_check_closure_state_path),
        "runtime_state_path": str(runtime_state_path),
        "runtime_receipt_pattern_path": str(runtime_receipt_pattern_path),
        "post_check_closure_state_path": str(post_check_closure_state_path),
    }


def enumerate_runtime_receipt_paths(receipt_pattern_path: Path) -> list[Path]:
    resolved = receipt_pattern_path.expanduser().resolve()
    if resolved.is_file():
        return [resolved]
    parent = resolved.parent
    if not parent.exists():
        return []
    try:
        return sorted(parent.glob(resolved.name), key=lambda item: str(item))
    except Exception:
        return []


def build_runtime_file_fingerprint(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    fingerprint: dict[str, Any] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "is_file": resolved.is_file(),
        "size_bytes": 0,
        "mtime_ns": None,
        "sha256": "",
    }
    if not resolved.exists():
        return fingerprint
    try:
        stat = resolved.stat()
        fingerprint["size_bytes"] = int(stat.st_size)
        fingerprint["mtime_ns"] = int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)))
    except Exception:
        pass
    if not resolved.is_file():
        return fingerprint
    digest = hashlib.sha256()
    with resolved.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    fingerprint["sha256"] = digest.hexdigest()
    return fingerprint


def snapshot_host_visible_surface_runtime(
    *,
    runtime_state_path: Path,
    runtime_receipt_pattern_path: Path,
    post_check_closure_state_path: Path,
) -> dict[str, Any]:
    receipt_pattern = runtime_receipt_pattern_path.expanduser().resolve()
    receipt_entries = [
        build_runtime_file_fingerprint(path)
        for path in enumerate_runtime_receipt_paths(receipt_pattern)
    ]
    return {
        "runtime_state": build_runtime_file_fingerprint(runtime_state_path),
        "runtime_receipt_pattern": str(receipt_pattern),
        "runtime_receipt_count": len(receipt_entries),
        "runtime_receipts": receipt_entries,
        "post_check_closure_state": build_runtime_file_fingerprint(post_check_closure_state_path),
    }


def host_visible_surface_runtime_snapshot_unchanged(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> bool:
    return json.dumps(before or {}, ensure_ascii=False, sort_keys=True) == json.dumps(
        after or {},
        ensure_ascii=False,
        sort_keys=True,
    )


def host_visible_surface_runtime_snapshot_changed_sections(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> list[str]:
    before_doc = before if isinstance(before, dict) else {}
    after_doc = after if isinstance(after, dict) else {}
    changed: list[str] = []
    for key in (
        "runtime_state",
        "runtime_receipt_pattern",
        "runtime_receipt_count",
        "runtime_receipts",
        "post_check_closure_state",
    ):
        if json.dumps(before_doc.get(key), ensure_ascii=False, sort_keys=True) != json.dumps(
            after_doc.get(key),
            ensure_ascii=False,
            sort_keys=True,
        ):
            changed.append(key)
    return changed
