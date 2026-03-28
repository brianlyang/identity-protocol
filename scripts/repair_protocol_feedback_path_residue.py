#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    PROTOCOL_FEEDBACK_ROOT,
    extract_feedback_relative_suffix,
    normalize_feedback_path_under_root,
    rel_to_feedback_root,
    resolve_feedback_root,
)
from tool_vendor_governance_common import resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_bytes(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    if left.stat().st_size != right.stat().st_size:
        return False
    return _sha256(left) == _sha256(right)


def _cleanup_empty_parents(path: Path, *, stop_root: Path) -> None:
    node = path.resolve()
    root = stop_root.resolve()
    while node != root:
        try:
            node.rmdir()
        except OSError:
            break
        node = node.parent


def _scan_residue(feedback_root: Path) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if not feedback_root.exists():
        return hits
    for candidate in sorted(feedback_root.rglob("*")):
        if not candidate.is_file():
            continue
        rel = rel_to_feedback_root(candidate, feedback_root)
        if rel == PROTOCOL_FEEDBACK_ROOT or rel.startswith(f"{PROTOCOL_FEEDBACK_ROOT}/"):
            suffix = extract_feedback_relative_suffix(rel)
            target = normalize_feedback_path_under_root(feedback_root, suffix or "")
            if candidate.resolve() == target.resolve():
                continue
            hits.append(
                {
                    "source_path": str(candidate.resolve()),
                    "source_ref": rel,
                    "target_path": str(target),
                    "target_ref": rel_to_feedback_root(target, feedback_root),
                }
            )
    return hits


def _apply_residue(feedback_root: Path, hits: list[dict[str, str]]) -> dict[str, int]:
    moved_count = 0
    pruned_duplicate_count = 0
    conflict_count = 0
    for hit in hits:
        source = Path(hit["source_path"]).resolve()
        target = Path(hit["target_path"]).resolve()
        if not source.exists():
            continue
        if target.exists():
            if _same_bytes(source, target):
                source.unlink()
                _cleanup_empty_parents(source.parent, stop_root=feedback_root)
                pruned_duplicate_count += 1
                continue
            conflict_count += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        _cleanup_empty_parents(source.parent, stop_root=feedback_root)
        moved_count += 1
    return {
        "moved_count": moved_count,
        "pruned_duplicate_count": pruned_duplicate_count,
        "conflict_count": conflict_count,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair nested protocol-feedback root residue by canonicalizing duplicate runtime/protocol-feedback prefixes.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    hits_before = _scan_residue(feedback_root)
    apply_stats = {
        "moved_count": 0,
        "pruned_duplicate_count": 0,
        "conflict_count": 0,
    }
    if args.apply and hits_before:
        apply_stats = _apply_residue(feedback_root, hits_before)
    hits_after = _scan_residue(feedback_root)
    status = STATUS_PASS_REQUIRED if not hits_after else STATUS_FAIL_REQUIRED

    payload = {
        "identity_id": str(args.identity_id).strip(),
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "feedback_root": str(feedback_root),
        "apply_enabled": bool(args.apply),
        "protocol_feedback_path_residue_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else "IP-DSPATH-004",
        "hit_count_before": len(hits_before),
        "hit_count_after": len(hits_after),
        "hits_before": hits_before,
        "hits_after": hits_after,
        **apply_stats,
        "stale_reasons": [] if status == STATUS_PASS_REQUIRED else ["nested_protocol_feedback_root_residue_detected"],
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
