#!/usr/bin/env python3
from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task

CROSS_VERIFICATION_CONTRACT_KEYS: tuple[str, ...] = (
    "multi_track_cross_verification_contract_v1",
    "multi_track_cross_verification_contract",
    "intake_evidence_quorum_contract_v1",
    "intake_evidence_quorum_contract",
)

UMBRELLA_CONTRACT_KEYS: tuple[str, ...] = (
    "cross_verification_intake_contract_v1",
    "cross_verification_intake_contract",
    "intake_evidence_contract_v1",
    "intake_evidence_contract",
)

BUNDLE_PATTERN_KEYS: tuple[str, ...] = (
    "evidence_bundle_path_pattern",
    "bundle_path_pattern",
    "cross_verification_bundle_pattern",
    "intake_bundle_pattern",
)


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _extract_bundle_id_from_text(raw: str) -> str:
    patterns = (
        r"cross_verification_bundle_id\s*[:=]\s*([^\s,;]+)",
        r"bundle_id\s*[:=]\s*([^\s,;]+)",
        r"evidence_bundle_id\s*[:=]\s*([^\s,;]+)",
    )
    for pat in patterns:
        match = re.search(pat, raw, flags=re.IGNORECASE)
        if match:
            return _clean_string(match.group(1))
    return ""


def _file_contains_token(path: Path, token: str, *, max_chars: int = 400_000) -> bool:
    target = _clean_string(token)
    if not target:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return target in text[:max_chars]


def _collect_contract_patterns(task_doc: dict[str, Any]) -> list[str]:
    patterns: list[str] = []

    def _append_from_contract(contract_doc: Any) -> None:
        if not isinstance(contract_doc, dict):
            return
        for key in BUNDLE_PATTERN_KEYS:
            token = _clean_string(contract_doc.get(key))
            if token:
                patterns.append(token)

    for key in CROSS_VERIFICATION_CONTRACT_KEYS:
        _append_from_contract(task_doc.get(key))

    for umbrella_key in UMBRELLA_CONTRACT_KEYS:
        umbrella_doc = task_doc.get(umbrella_key)
        if not isinstance(umbrella_doc, dict):
            continue
        _append_from_contract(umbrella_doc)
        for key in CROSS_VERIFICATION_CONTRACT_KEYS:
            _append_from_contract(umbrella_doc.get(key))

    dedup: list[str] = []
    seen: set[str] = set()
    for item in patterns:
        token = _clean_string(item)
        if not token or token in seen:
            continue
        seen.add(token)
        dedup.append(token)
    return dedup


def _resolve_pattern(pack_path: Path, pattern: str) -> list[Path]:
    raw = _clean_string(pattern)
    if not raw:
        return []
    candidate = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ("*", "?", "["))
    hits: list[Path] = []
    if candidate.is_absolute():
        if has_magic:
            hits = [Path(item).expanduser().resolve() for item in glob.glob(str(candidate))]
        elif candidate.exists():
            hits = [candidate.resolve()]
    else:
        preferred = [item.resolve() for item in pack_path.glob(raw)]
        fallback = [item.resolve() for item in Path(".").glob(raw)]
        hits = preferred if preferred else fallback
    return [item for item in hits if item.exists() and item.is_file()]


def resolve_cross_verification_bundle_context(
    *,
    catalog_path: str | Path,
    identity_id: str,
    run_id: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "bundle_path": "",
        "bundle_id": "",
        "selection_status": "",
        "selection_source": "",
        "selection_error": "",
        "candidate_count": 0,
        "candidate_paths": [],
        "pack_path": "",
        "task_path": "",
    }
    try:
        pack_path, task_path = resolve_pack_and_task(Path(catalog_path).expanduser().resolve(), identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        result["selection_error"] = f"cross_verification_bundle_context_resolve_failed:{exc}"
        return result

    result["pack_path"] = str(pack_path)
    result["task_path"] = str(task_path)
    feedback_root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not feedback_root.exists():
        result["selection_status"] = "feedback_root_missing"
        return result

    patterns = _collect_contract_patterns(task_doc)
    if not patterns:
        result["selection_status"] = "contract_bundle_patterns_missing"
        return result
    result["selection_source"] = "task_contract_bundle_patterns"

    candidates: list[Path] = []
    seen: set[str] = set()
    for pattern in patterns:
        for hit in _resolve_pattern(pack_path, pattern):
            key = str(hit)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(hit)

    candidates.sort(key=lambda path: path.stat().st_mtime)
    result["candidate_count"] = len(candidates)
    result["candidate_paths"] = [str(path) for path in candidates[-10:]]
    if not candidates:
        result["selection_status"] = "bundle_candidates_missing"
        return result

    selected = candidates[-1]
    run_token = _clean_string(run_id)
    if run_token:
        run_hits = [path for path in candidates if run_token in path.name or _file_contains_token(path, run_token)]
        if not run_hits:
            result["selection_status"] = "bundle_current_round_unresolved"
            return result
        selected = run_hits[-1]
        result["selection_status"] = "run_bound_bundle"
    else:
        result["selection_status"] = "latest_bundle"

    result["bundle_path"] = str(selected)
    try:
        raw = selected.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raw = ""
    result["bundle_id"] = _extract_bundle_id_from_text(raw) or selected.stem
    return result
