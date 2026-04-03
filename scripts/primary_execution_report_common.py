#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

IDENTITY_UPGRADE_EXEC_PREFIX = "identity-upgrade-exec-"
DERIVATIVE_REPORT_SUFFIXES: tuple[str, ...] = (
    "-patch-plan.json",
    "-postexec-receipt.json",
    "-receipt.json",
)
DERIVATIVE_REPORT_PATH_TOKENS: tuple[str, ...] = (
    "/runtime/protocol-feedback/",
    "/archive/",
    "/archives/",
    "/runtime/reports/postexec/",
)


def dedupe_resolved_paths(rows: Iterable[Path]) -> list[Path]:
    dedup: dict[str, Path] = {}
    for row in rows:
        resolved = row.expanduser().resolve()
        dedup[resolved.as_posix()] = resolved
    return list(dedup.values())


def report_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def prompt_file_sha(path: Path | None) -> str:
    if not isinstance(path, Path):
        return ""
    try:
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        return digest.hexdigest()
    except Exception:
        return ""


def report_prompt_sha(path: Path) -> str:
    payload = load_execution_report_payload(path)
    if not payload:
        return ""
    return str(
        payload.get("identity_prompt_sha256", "")
        or payload.get("prompt_policy_hash", "")
    ).strip()


def load_execution_report_payload(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def report_pack_root(path: Path) -> Path | None:
    payload = load_execution_report_payload(path)
    if not payload:
        return None
    pack_raw = str(
        payload.get("resolved_pack_path", "")
        or payload.get("pack_path", "")
        or ""
    ).strip()
    if pack_raw:
        return Path(pack_raw).expanduser().resolve()
    prompt_raw = str(payload.get("identity_prompt_path", "") or "").strip()
    if not prompt_raw:
        return None
    prompt_path = Path(prompt_raw).expanduser().resolve()
    return prompt_path.parent


def report_run_id(path: Path) -> str:
    payload = load_execution_report_payload(path)
    run_id = str(payload.get("run_id", "") or "").strip()
    if run_id:
        return run_id
    if is_primary_execution_report(path) and path.name.startswith(IDENTITY_UPGRADE_EXEC_PREFIX):
        return path.stem
    return ""


def report_logical_identity_key(path: Path) -> str:
    payload = load_execution_report_payload(path)
    pack_root = report_pack_root(path)
    catalog_raw = str(payload.get("catalog_path", "") or "").strip()
    logical_identity = {
        "identity_id": str(payload.get("identity_id", "") or "").strip(),
        "run_id": report_run_id(path),
        "catalog_path": str(Path(catalog_raw).expanduser().resolve()) if catalog_raw else "",
        "resolved_pack_path": str(pack_root) if isinstance(pack_root, Path) else "",
        "identity_prompt_sha256": report_prompt_sha(path),
    }
    if not any(logical_identity.values()):
        logical_identity["fallback_path"] = path.expanduser().resolve().as_posix()
    return json.dumps(logical_identity, ensure_ascii=False, sort_keys=True)


def infer_pack_root_from_report_root(report_root: Path | None) -> Path | None:
    if not isinstance(report_root, Path):
        return None
    resolved = report_root.expanduser().resolve()
    if resolved.name == "reports" and resolved.parent.name == "runtime":
        return resolved.parent.parent.resolve()
    if resolved.name == "runtime":
        return resolved.parent.resolve()
    return None


def preferred_prompt_sha_from_pack_root(pack_root: Path | None) -> str:
    if not isinstance(pack_root, Path):
        return ""
    return prompt_file_sha((pack_root.expanduser().resolve() / "IDENTITY_PROMPT.md").resolve())


def preferred_prompt_sha_from_report_roots(
    report_roots: Iterable[Path],
    *,
    explicit_pack_root: Path | None = None,
) -> str:
    candidate_pack_roots: list[Path] = []
    if isinstance(explicit_pack_root, Path):
        candidate_pack_roots.append(explicit_pack_root.expanduser().resolve())
    for root in dedupe_resolved_paths(report_roots):
        inferred = infer_pack_root_from_report_root(root)
        if inferred is not None:
            candidate_pack_roots.append(inferred)
    for pack_root in dedupe_resolved_paths(candidate_pack_roots):
        prompt_sha = preferred_prompt_sha_from_pack_root(pack_root)
        if prompt_sha:
            return prompt_sha
    return ""


def report_glob_pattern(identity_id: str) -> str:
    normalized_identity = str(identity_id or "").strip()
    if normalized_identity in {"", "*"}:
        return f"**/{IDENTITY_UPGRADE_EXEC_PREFIX}*.json"
    return f"**/{IDENTITY_UPGRADE_EXEC_PREFIX}{normalized_identity}-*.json"


def is_derivative_execution_report(path: Path) -> bool:
    lower_name = path.name.lower()
    if any(lower_name.endswith(suffix) for suffix in DERIVATIVE_REPORT_SUFFIXES):
        return True
    path_text = path.expanduser().resolve().as_posix().lower()
    return any(token in path_text for token in DERIVATIVE_REPORT_PATH_TOKENS)


def is_primary_execution_report(
    path: Path,
    *,
    identity_id: str = "",
    include_generic_upgrade_json: bool = False,
) -> bool:
    if not path.is_file():
        return False
    lower_name = path.name.lower()
    if not lower_name.endswith(".json"):
        return False
    if is_derivative_execution_report(path):
        return False
    normalized_identity = str(identity_id or "").strip()
    if lower_name.startswith(IDENTITY_UPGRADE_EXEC_PREFIX):
        if normalized_identity in {"", "*"}:
            return True
        return f"{IDENTITY_UPGRADE_EXEC_PREFIX}{normalized_identity.lower()}-" in lower_name
    if not include_generic_upgrade_json:
        return False
    return "upgrade" in lower_name


def collect_primary_execution_reports_from_roots(
    report_roots: Iterable[Path],
    identity_id: str,
    *,
    include_generic_upgrade_json: bool = False,
) -> list[Path]:
    rows: list[Path] = []
    generic_rows: list[Path] = []
    pattern = report_glob_pattern(identity_id)
    for root in dedupe_resolved_paths(report_roots):
        if not root.exists():
            continue
        for candidate in root.glob(pattern):
            resolved = candidate.resolve()
            if is_primary_execution_report(resolved, identity_id=identity_id):
                rows.append(resolved)
        if not include_generic_upgrade_json or rows:
            continue
        for candidate in root.glob("**/*.json"):
            resolved = candidate.resolve()
            if is_primary_execution_report(
                resolved,
                include_generic_upgrade_json=True,
            ):
                generic_rows.append(resolved)
    selected_rows = rows if rows else generic_rows
    return sorted(dedupe_resolved_paths(selected_rows), key=report_mtime)


def latest_primary_execution_report_from_roots(
    report_roots: Iterable[Path],
    identity_id: str,
    *,
    include_generic_upgrade_json: bool = False,
    preferred_prompt_sha: str = "",
    preferred_pack_root: Path | None = None,
) -> Path | None:
    rows = collect_primary_execution_reports_from_roots(
        report_roots,
        identity_id,
        include_generic_upgrade_json=include_generic_upgrade_json,
    )
    if not rows:
        return None
    prompt_sha = str(preferred_prompt_sha or "").strip()
    preferred_pack_root_resolved = (
        preferred_pack_root.expanduser().resolve()
        if isinstance(preferred_pack_root, Path)
        else None
    )
    if not prompt_sha and preferred_pack_root_resolved is None:
        return rows[-1]
    candidate_rows = rows
    if prompt_sha:
        prompt_rows = [path for path in rows if report_prompt_sha(path) == prompt_sha]
        if prompt_rows:
            candidate_rows = prompt_rows
    if preferred_pack_root_resolved is not None:
        pack_rows = [
            path
            for path in candidate_rows
            if report_pack_root(path) == preferred_pack_root_resolved
        ]
        if pack_rows:
            candidate_rows = pack_rows
    return candidate_rows[-1]


def latest_prompt_bound_primary_execution_report_from_roots(
    report_roots: Iterable[Path],
    identity_id: str,
    *,
    include_generic_upgrade_json: bool = False,
    explicit_pack_root: Path | None = None,
) -> Path | None:
    return latest_primary_execution_report_from_roots(
        report_roots,
        identity_id,
        include_generic_upgrade_json=include_generic_upgrade_json,
        preferred_prompt_sha=preferred_prompt_sha_from_report_roots(
            report_roots,
            explicit_pack_root=explicit_pack_root,
        ),
        preferred_pack_root=explicit_pack_root,
    )
