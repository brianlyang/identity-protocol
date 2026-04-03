#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from create_identity_pack import (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
    DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
    DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
    DOWNSINK_LITERAL_LOCK_SCAN_GLOBS,
    HOST_GATEWAY_LIGHT_OPERATIONS,
    HOST_GATEWAY_STRICT_OPERATIONS,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-DSPATH-001"
ERR_CONTRACT_INVALID = "IP-DSPATH-002"
ERR_LITERAL_LOCK = "IP-DSPATH-005"

STRING_LITERAL_RE = re.compile(
    r"""(?P<quote>["'])(?P<value>(?:\\.|(?!\1).){1,2048}?)(?P=quote)""",
    re.DOTALL,
)

DEFAULT_SCAN_GLOBS: tuple[str, ...] = tuple(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS)
DEFAULT_ALLOW_MARKER = DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in (
        DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
        "protocol_downsink_path_immutability_contract",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node, key
    for key, value in task.items():
        if not isinstance(value, dict):
            continue
        token = str(key or "").strip().lower()
        if "downsink" in token and "path" in token and "immutability" in token:
            return value, str(key)
    return {}, DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY


def _normalize_path_token(token: str) -> str:
    out = str(token or "").replace("\\", "/").strip()
    while out.startswith("./"):
        out = out[2:]
    return out


def _token_is_governed_path(token: str, governed_roots: list[str]) -> bool:
    normalized = _normalize_path_token(token)
    if not normalized:
        return False
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return False
    return any(normalized == root or normalized.startswith(f"{root.rstrip('/')}/") for root in governed_roots)


def _build_registry_matchers(path_registry: dict[str, Any]) -> list[tuple[str, str]]:
    matchers: list[tuple[str, str]] = []
    for domain_node in path_registry.values():
        if not isinstance(domain_node, dict):
            continue
        entries = domain_node.get("entries")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_type = str(entry.get("entry_type", "")).strip().lower()
            path_token = _normalize_path_token(str(entry.get("path", "")).strip())
            if not path_token:
                continue
            if entry_type in {"file", "dir", "glob"}:
                matchers.append((entry_type, path_token))
    return matchers


def _normalize_interpolation(path_token: str) -> str:
    token = _normalize_path_token(path_token)
    if not token:
        return token
    token = re.sub(r"\$\{[^}]+\}", "*", token)
    token = re.sub(r"\{[^{}]+\}", "*", token)
    token = re.sub(r"%\([^)]+\)s", "*", token)
    token = re.sub(r"%s", "*", token)
    return token


def _token_in_registry(path_token: str, matchers: list[tuple[str, str]]) -> bool:
    token = _normalize_interpolation(path_token)
    if not token:
        return True
    for entry_type, pattern in matchers:
        if entry_type == "file":
            if token == pattern:
                return True
            continue
        if entry_type == "dir":
            if token == pattern or token.startswith(f"{pattern.rstrip('/')}/"):
                return True
            continue
        if entry_type == "glob":
            if fnmatch.fnmatch(token, pattern):
                return True
    return False


def _derive_governed_roots(matchers: list[tuple[str, str]]) -> list[str]:
    roots: set[str] = set()
    for entry_type, pattern in matchers:
        token = _normalize_path_token(pattern)
        if not token:
            continue
        if entry_type == "glob":
            split_idx = len(token)
            for marker in ("*", "?", "["):
                idx = token.find(marker)
                if idx >= 0:
                    split_idx = min(split_idx, idx)
            token = token[:split_idx].rstrip("/")
        if not token:
            continue
        roots.add(token.rstrip("/"))
        parts = [part for part in PurePosixPath(token).parts if part not in {"", "."}]
        if len(parts) >= 2 and parts[0] == "runtime":
            if parts[1] in {"gate", "protocol-feedback"}:
                roots.add("/".join(parts[:2]))
            if parts[1] == "reports" and len(parts) >= 3 and parts[2] == "broadcast":
                roots.add("/".join(parts[:3]))
        if len(parts) >= 3 and parts[0] == "identity" and parts[1] == "protocol":
            roots.add("/".join(parts[:3]))
    return sorted(root for root in roots if root)


def _derive_literal_anchor_tokens(matchers: list[tuple[str, str]]) -> set[str]:
    anchors: set[str] = set()
    for entry_type, pattern in matchers:
        token = _normalize_path_token(pattern)
        if not token:
            continue
        candidate = token
        if entry_type == "glob":
            normalized = _normalize_interpolation(token)
            split_idx = len(normalized)
            for marker in ("*", "?", "["):
                idx = normalized.find(marker)
                if idx >= 0:
                    split_idx = min(split_idx, idx)
            candidate = normalized[:split_idx].rstrip("/")
        path_candidate = PurePosixPath(candidate)
        if entry_type in {"file", "glob"}:
            parent = path_candidate.parent.as_posix()
            if parent and parent not in {".", ""}:
                anchors.add(parent)
        elif entry_type == "dir":
            anchors.add(path_candidate.as_posix())

        parts = [part for part in path_candidate.parts if part not in {"", "."}]
        if len(parts) >= 2 and parts[0] == "runtime" and parts[1] in {"gate", "protocol-feedback"}:
            anchors.add("/".join(parts[:2]))
        if len(parts) >= 3 and parts[0] == "runtime" and parts[1] == "reports" and parts[2] == "broadcast":
            anchors.add("/".join(parts[:3]))
    return {anchor.rstrip("/") for anchor in anchors if anchor and anchor not in {".", ""}}


def _token_matches_literal_anchor(path_token: str, literal_anchors: set[str]) -> bool:
    token = _normalize_path_token(path_token).rstrip("/")
    if not token:
        return True
    return token in literal_anchors


def _iter_scan_files(repo_root: Path, globs: list[str]) -> list[Path]:
    files: dict[str, Path] = {}
    for pattern in globs:
        token = str(pattern or "").strip()
        if not token:
            continue
        for p in repo_root.glob(token):
            if not p.is_file():
                continue
            files[p.resolve().as_posix()] = p.resolve()
    return [files[key] for key in sorted(files.keys())]


def _scan_source_file(
    *,
    path: Path,
    repo_root: Path,
    matchers: list[tuple[str, str]],
    literal_anchors: set[str],
    governed_roots: list[str],
    allow_marker: str,
) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return [f"scan_read_failed:{path.relative_to(repo_root).as_posix()}"]

    # Most source files never mention governed runtime roots; skip regex-heavy literal scanning for them.
    if not any(root in text for root in governed_roots):
        return []

    violations: list[str] = []
    lines = text.splitlines()
    candidate_rows = [
        (lineno, line)
        for lineno, line in enumerate(lines, start=1)
        if any(root in line for root in governed_roots)
    ]
    if not candidate_rows:
        return []

    rel = path.relative_to(repo_root).as_posix()
    marker = str(allow_marker or "").strip()
    for lineno, line in candidate_rows:
        for m in STRING_LITERAL_RE.finditer(line):
            token = _normalize_path_token(m.group("value"))
            if not _token_is_governed_path(token, governed_roots):
                continue
            if _token_in_registry(token, matchers):
                continue
            if _token_matches_literal_anchor(token, literal_anchors):
                continue
            if marker and marker in line:
                continue
            violations.append(f"non_registry_literal:{rel}:{lineno}:{token}")
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol downsink source path literal lock (v1.6.8).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--scan-glob", action="append", default=[])
    ap.add_argument("--probe-path-literal", action="append", default=[])
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract, contract_key = _resolve_contract(task)
    required = contract_required(contract)
    op = str(args.operation or "").strip().lower()
    auto_required_signal = op in set(HOST_GATEWAY_STRICT_OPERATIONS) or op in set(HOST_GATEWAY_LIGHT_OPERATIONS)
    if auto_required_signal:
        required = True
    if args.force_required:
        required = True

    repo_root = Path(__file__).resolve().parent.parent
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": op,
        "required_contract": required,
        "auto_required_signal": bool(auto_required_signal),
        "contract_key": contract_key,
        "protocol_downsink_path_literal_lock_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "scan_file_count": 0,
        "scan_files": [],
        "scan_globs": [],
        "probe_path_literals": [str(x).strip() for x in args.probe_path_literal if str(x).strip()],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    source_policy = contract.get("source_literal_lock_policy")
    if not isinstance(source_policy, dict):
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["source_literal_lock_policy_missing"]
        _emit(payload, json_only=args.json_only)
        return 1
    if source_policy.get("required") is not True:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["source_literal_lock_policy_required_not_true"]
        _emit(payload, json_only=args.json_only)
        return 1
    if str(source_policy.get("validator_id", "")).strip() != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["source_literal_lock_policy_validator_id_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1
    if bool(source_policy.get("enforce_registered_runtime_path_literals_only")) is not True:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["source_literal_lock_policy_enforce_registered_literals_not_true"]
        _emit(payload, json_only=args.json_only)
        return 1

    path_registry = contract.get("path_registry")
    if not isinstance(path_registry, dict):
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["path_registry_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    matchers = _build_registry_matchers(path_registry)
    if not matchers:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["path_registry_entries_missing"]
        _emit(payload, json_only=args.json_only)
        return 1
    governed_roots = _derive_governed_roots(matchers)
    literal_anchors = _derive_literal_anchor_tokens(matchers)
    if not governed_roots:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["governed_roots_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    policy_scan_globs = source_policy.get("scan_globs")
    effective_scan_globs = [str(item).strip() for item in (policy_scan_globs or []) if str(item).strip()]
    if not effective_scan_globs:
        effective_scan_globs = list(DEFAULT_SCAN_GLOBS)
    cli_scan_globs = [str(item).strip() for item in args.scan_glob if str(item).strip()]
    if cli_scan_globs:
        effective_scan_globs = cli_scan_globs

    allow_marker = str(source_policy.get("allow_inline_override_marker", "")).strip() or DEFAULT_ALLOW_MARKER
    scan_files = _iter_scan_files(repo_root, effective_scan_globs)
    violations: list[str] = []
    for file_path in scan_files:
        violations.extend(
            _scan_source_file(
                path=file_path,
                repo_root=repo_root,
                matchers=matchers,
                literal_anchors=literal_anchors,
                governed_roots=governed_roots,
                allow_marker=allow_marker,
            )
        )

    for literal in payload["probe_path_literals"]:
        if not _token_is_governed_path(literal, governed_roots):
            continue
        if not _token_in_registry(literal, matchers) and not _token_matches_literal_anchor(literal, literal_anchors):
            violations.append(f"non_registry_literal:probe:{literal}")

    payload["scan_globs"] = effective_scan_globs
    payload["scan_file_count"] = len(scan_files)
    payload["scan_files"] = [p.relative_to(repo_root).as_posix() for p in scan_files]
    payload["registry_rule_count"] = len(matchers)

    if violations:
        payload["protocol_downsink_path_literal_lock_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_LITERAL_LOCK
        payload["stale_reasons"] = sorted(set(violations))
        payload["evidence_ref"] = str(repo_root)
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_downsink_path_literal_lock_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    payload["evidence_ref"] = str(repo_root)
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
