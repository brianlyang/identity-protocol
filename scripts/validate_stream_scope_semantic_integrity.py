#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import is_requirement_id, is_stream_version

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_STREAM_SCOPE = "IP-SSCOPE-001"
DEFAULT_STREAM_MATRIX_ENTRY = "identity/protocol/mappings/stream-scope-matrix.current.yaml"
DEFAULT_STREAM_REGISTRY_ENTRY = "identity/protocol/mappings/stream-doc-registry.current.yaml"
DEFAULT_CONTRACT_BINDING_ENTRY = "identity/protocol/mappings/contract-binding.current.yaml"

REQ_KEY_RE = re.compile(r"^(asb16-rq-(\d{3}))\s*:")
REQ_ID_LINE_RE = re.compile(r"^requirement_id:\s*([A-Z0-9_-]+-RQ-\d{3})\b")


def _run_git(args: list[str], *, repo_root: Path) -> str:
    cp = subprocess.run(["git", *args], cwd=str(repo_root), capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _resolve_range(base: str | None, head: str | None, *, repo_root: Path) -> tuple[str, str]:
    resolved_head = str(head or "").strip() or _run_git(["rev-parse", "HEAD"], repo_root=repo_root)
    resolved_base = str(base or "").strip() or _run_git(["rev-parse", "HEAD~1"], repo_root=repo_root)
    return resolved_base, resolved_head


def _changed_files(base: str, head: str, *, repo_root: Path) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"], repo_root=repo_root)
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _relpath(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _extract_changed_requirement_ids(*, base: str, head: str, contract_binding_rel: str, repo_root: Path) -> list[str]:
    try:
        patch = _run_git(["diff", "--unified=0", f"{base}..{head}", "--", contract_binding_rel], repo_root=repo_root)
    except Exception:
        return []
    ids: set[str] = set()
    for raw in patch.splitlines():
        line = raw.rstrip("\n")
        if not line or line.startswith(("+++", "---", "@@")):
            continue
        if line[0] not in {"+", "-"}:
            continue
        content = line[1:].strip()
        m_key = REQ_KEY_RE.match(content)
        if m_key:
            ids.add(f"ASB16-RQ-{m_key.group(2)}")
            continue
        m_id = REQ_ID_LINE_RE.match(content)
        if m_id:
            requirement_id = str(m_id.group(1)).strip().upper()
            if is_requirement_id(requirement_id):
                ids.add(requirement_id)
    return sorted(ids)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate stream scope semantic integrity against stream scope matrix.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument("--stream-matrix", default=DEFAULT_STREAM_MATRIX_ENTRY)
    ap.add_argument("--stream-registry", default=DEFAULT_STREAM_REGISTRY_ENTRY)
    ap.add_argument("--contract-binding", default=DEFAULT_CONTRACT_BINDING_ENTRY)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()

    payload: dict[str, Any] = {
        "stream_scope_semantic_integrity_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_STREAM_SCOPE,
        "base": "",
        "head": "",
        "changed_file_count": 0,
        "changed_files": [],
        "stream_matrix_entry": str((repo_root / str(args.stream_matrix)).resolve()),
        "stream_matrix_path": "",
        "stream_matrix_active_file": "",
        "stream_matrix_alias_error": "",
        "stream_registry_entry": str((repo_root / str(args.stream_registry)).resolve()),
        "stream_registry_path": "",
        "stream_registry_active_file": "",
        "stream_registry_alias_error": "",
        "contract_binding_entry": str((repo_root / str(args.contract_binding)).resolve()),
        "contract_binding_path": "",
        "contract_binding_active_file": "",
        "contract_binding_alias_error": "",
        "touched_stream_versions": [],
        "touched_stream_docs": [],
        "changed_requirement_ids": [],
        "matrix_scope_row": {},
        "violations": [],
        "stale_reasons": [],
    }

    try:
        base, head = _resolve_range(args.base, args.head, repo_root=repo_root)
    except Exception as exc:
        payload["stale_reasons"] = [f"git_range_resolution_failed:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1
    payload["base"] = base
    payload["head"] = head

    try:
        changed = _changed_files(base, head, repo_root=repo_root)
    except Exception as exc:
        payload["stale_reasons"] = [f"git_changed_files_failed:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["changed_files"] = changed
    payload["changed_file_count"] = len(changed)

    if not changed:
        payload["stream_scope_semantic_integrity_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["error_code"] = ""
        payload["stale_reasons"] = ["no_changed_files_in_range"]
        _emit(payload, json_only=args.json_only)
        return 0

    matrix_path, matrix_active_file, matrix_alias_error = _resolve_current_yaml_alias(repo_root, str(args.stream_matrix))
    payload["stream_matrix_path"] = str(matrix_path)
    payload["stream_matrix_active_file"] = matrix_active_file
    payload["stream_matrix_alias_error"] = matrix_alias_error

    stream_registry_path, stream_registry_active_file, stream_registry_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.stream_registry)
    )
    payload["stream_registry_path"] = str(stream_registry_path)
    payload["stream_registry_active_file"] = stream_registry_active_file
    payload["stream_registry_alias_error"] = stream_registry_alias_error

    contract_binding_path, contract_binding_active_file, contract_binding_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.contract_binding)
    )
    payload["contract_binding_path"] = str(contract_binding_path)
    payload["contract_binding_active_file"] = contract_binding_active_file
    payload["contract_binding_alias_error"] = contract_binding_alias_error

    alias_errors: list[str] = []
    if matrix_alias_error:
        alias_errors.append(f"stream_matrix_alias_error:{matrix_alias_error}")
    if stream_registry_alias_error:
        alias_errors.append(f"stream_registry_alias_error:{stream_registry_alias_error}")
    if contract_binding_alias_error:
        alias_errors.append(f"contract_binding_alias_error:{contract_binding_alias_error}")
    if alias_errors:
        payload["stale_reasons"] = alias_errors
        _emit(payload, json_only=args.json_only)
        return 1

    if not (matrix_path.exists() and stream_registry_path.exists() and contract_binding_path.exists()):
        missing = []
        if not matrix_path.exists():
            missing.append("stream_matrix_missing")
        if not stream_registry_path.exists():
            missing.append("stream_registry_missing")
        if not contract_binding_path.exists():
            missing.append("contract_binding_missing")
        payload["stale_reasons"] = missing
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        matrix_doc = _load_yaml(matrix_path)
        stream_doc = _load_yaml(stream_registry_path)
    except Exception as exc:
        payload["stale_reasons"] = [f"yaml_parse_failed:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    matrix_rows = matrix_doc.get("streams")
    stream_rows = stream_doc.get("stream_docs")
    if not isinstance(matrix_rows, list) or not isinstance(stream_rows, list):
        payload["stale_reasons"] = ["matrix_or_stream_registry_schema_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    stream_docs_by_version: dict[str, set[str]] = {}
    for idx, row in enumerate(stream_rows):
        if not isinstance(row, dict):
            payload["violations"].append(f"stream_docs[{idx}]_not_object")
            continue
        stream_version = str(row.get("stream_version", "")).strip()
        if not is_stream_version(stream_version):
            payload["violations"].append(f"stream_docs[{idx}]_stream_version_invalid")
            continue
        paths = set()
        for key_name in ("governance_doc", "review_doc"):
            rel = str(row.get(key_name, "")).strip().replace("\\", "/")
            if rel:
                paths.add(rel)
        if paths:
            stream_docs_by_version.setdefault(stream_version, set()).update(paths)

    scope_by_stream: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(matrix_rows):
        if not isinstance(row, dict):
            payload["violations"].append(f"matrix_streams[{idx}]_not_object")
            continue
        stream_version = str(row.get("stream_version", "")).strip()
        if not is_stream_version(stream_version):
            payload["violations"].append(f"matrix_streams[{idx}]_stream_version_invalid")
            continue
        scope_by_stream[stream_version] = row

    changed_set = set(changed)
    touched_stream_versions: set[str] = set()
    touched_stream_docs: list[str] = []
    for stream_version, doc_paths in stream_docs_by_version.items():
        hits = sorted(path for path in doc_paths if path in changed_set)
        if hits:
            touched_stream_versions.add(stream_version)
            touched_stream_docs.extend(hits)

    payload["touched_stream_versions"] = sorted(touched_stream_versions)
    payload["touched_stream_docs"] = sorted(set(touched_stream_docs))

    contract_binding_rel = _relpath(contract_binding_path, repo_root=repo_root)
    contract_binding_changed = contract_binding_rel in changed_set

    if not touched_stream_versions:
        if contract_binding_changed:
            payload["violations"].append("contract_binding_changed_without_stream_docs")
            payload["stale_reasons"] = ["stream_scope_anchor_missing"]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["stream_scope_semantic_integrity_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["error_code"] = ""
        payload["stale_reasons"] = ["no_stream_docs_touched_in_range"]
        _emit(payload, json_only=args.json_only)
        return 0

    if len(touched_stream_versions) != 1:
        payload["violations"].append("multiple_stream_versions_touched")
        payload["stale_reasons"] = ["stream_scope_not_unique"]
        _emit(payload, json_only=args.json_only)
        return 1

    stream_version = next(iter(touched_stream_versions))
    scope_row = scope_by_stream.get(stream_version)
    if not isinstance(scope_row, dict):
        payload["violations"].append(f"stream_scope_row_missing:{stream_version}")
        payload["stale_reasons"] = ["stream_scope_row_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    allowed_ids = {
        str(x).strip().upper()
        for x in (scope_row.get("allowed_requirement_ids") if isinstance(scope_row.get("allowed_requirement_ids"), list) else [])
        if str(x).strip()
    }
    forbidden_ids = {
        str(x).strip().upper()
        for x in (scope_row.get("forbidden_requirement_ids") if isinstance(scope_row.get("forbidden_requirement_ids"), list) else [])
        if str(x).strip()
    }
    forbidden_path_tokens = [
        str(x).strip().replace("\\", "/")
        for x in (scope_row.get("forbidden_path_tokens") if isinstance(scope_row.get("forbidden_path_tokens"), list) else [])
        if str(x).strip()
    ]

    changed_requirement_ids: list[str] = []
    if contract_binding_changed:
        changed_requirement_ids = _extract_changed_requirement_ids(
            base=base,
            head=head,
            contract_binding_rel=contract_binding_rel,
            repo_root=repo_root,
        )
    payload["changed_requirement_ids"] = changed_requirement_ids

    violations: list[str] = list(payload["violations"])

    if changed_requirement_ids and allowed_ids:
        not_allowed = sorted(req for req in changed_requirement_ids if req not in allowed_ids)
        if not_allowed:
            violations.append(f"requirement_ids_not_allowed:{','.join(not_allowed)}")

    if changed_requirement_ids and forbidden_ids:
        forbidden_hits = sorted(req for req in changed_requirement_ids if req in forbidden_ids)
        if forbidden_hits:
            violations.append(f"requirement_ids_forbidden:{','.join(forbidden_hits)}")

    if forbidden_path_tokens:
        changed_joined = "\n".join(changed)
        hit_tokens = sorted({token for token in forbidden_path_tokens if token in changed_joined})
        if hit_tokens:
            violations.append(f"forbidden_path_tokens_touched:{','.join(hit_tokens)}")

    payload["matrix_scope_row"] = {
        "stream_version": stream_version,
        "scope_topic": str(scope_row.get("scope_topic", "")).strip(),
        "allowed_requirement_ids": sorted(allowed_ids),
        "forbidden_requirement_ids": sorted(forbidden_ids),
        "forbidden_path_tokens": forbidden_path_tokens,
    }

    if violations:
        payload["violations"] = violations
        payload["stale_reasons"] = ["stream_scope_semantic_violation"]
        payload["stream_scope_semantic_integrity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM_SCOPE
        _emit(payload, json_only=args.json_only)
        return 1

    payload["stream_scope_semantic_integrity_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["violations"] = []
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
