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
    DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN,
    DOWNSINK_REQUIRED_DOMAINS,
    DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
    DOWNSINK_RUNTIME_GATE_DOMAIN,
    DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN,
    HOST_GATEWAY_LIGHT_OPERATIONS,
    HOST_GATEWAY_STRICT_OPERATIONS,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-DSPATH-001"
ERR_CONTRACT_INVALID = "IP-DSPATH-002"
ERR_WRITE_GUARD = "IP-DSPATH-004"

ENTRY_TYPES = {"file", "dir", "glob"}
GLOB_MAGIC_RE = re.compile(r"[*?\[]")

EXPECTED_DOMAIN_ANCHOR = {
    DOWNSINK_RUNTIME_GATE_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_RUNTIME_BROADCAST_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN: "protocol_repo_root_ref",
}


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


def _is_abs_like(path_token: str) -> bool:
    token = str(path_token or "").strip()
    if not token:
        return False
    if Path(token).is_absolute():
        return True
    return token.startswith("~/") or re.match(r"^[A-Za-z]:[\\/]", token) is not None


def _contains_parent_escape(path_token: str) -> bool:
    token = str(path_token or "").replace("\\", "/").strip()
    if not token:
        return False
    return any(part == ".." for part in PurePosixPath(token).parts)


def _resolve_anchor_root(*, anchor_ref: str, pack_path: Path, repo_root: Path) -> Path | None:
    if anchor_ref == "identity_pack_root_ref":
        return pack_path.resolve()
    if anchor_ref == "protocol_repo_root_ref":
        return repo_root.resolve()
    return None


def _path_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _normalize_path_token(path_token: Any) -> str:
    return str(path_token or "").replace("\\", "/").strip()


def _to_rule_abs_pattern(anchor_root: Path, rel_pattern: str) -> str:
    return (anchor_root / rel_pattern).resolve().as_posix()


def _build_registry_rules(
    *,
    path_registry: dict[str, Any],
    pack_path: Path,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    rules: list[dict[str, Any]] = []
    issues: list[str] = []
    for domain in DOWNSINK_REQUIRED_DOMAINS:
        domain_node = path_registry.get(domain)
        if not isinstance(domain_node, dict):
            issues.append(f"{domain}:domain_missing")
            continue
        anchor_ref = str(domain_node.get("anchor_ref", "")).strip()
        expected_anchor_ref = EXPECTED_DOMAIN_ANCHOR.get(domain, "")
        if not anchor_ref:
            issues.append(f"{domain}:anchor_ref_missing")
            continue
        if expected_anchor_ref and anchor_ref != expected_anchor_ref:
            issues.append(f"{domain}:anchor_ref_mismatch")
        anchor_root = _resolve_anchor_root(anchor_ref=anchor_ref, pack_path=pack_path, repo_root=repo_root)
        if anchor_root is None:
            issues.append(f"{domain}:anchor_ref_unsupported")
            continue
        entries = domain_node.get("entries")
        if not isinstance(entries, list):
            issues.append(f"{domain}:entries_missing")
            continue
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                issues.append(f"{domain}:entry_{idx}_invalid")
                continue
            path_id = str(entry.get("path_id", "")).strip()
            entry_type = str(entry.get("entry_type", "")).strip().lower()
            rel_path = _normalize_path_token(entry.get("path"))
            if not path_id:
                issues.append(f"{domain}:entry_{idx}:path_id_missing")
                continue
            if entry_type not in ENTRY_TYPES:
                issues.append(f"{domain}:entry_{idx}:entry_type_invalid")
                continue
            if not rel_path:
                issues.append(f"{domain}:entry_{idx}:path_missing")
                continue
            if _is_abs_like(rel_path):
                issues.append(f"{domain}:entry_{idx}:path_must_be_relative")
                continue
            if _contains_parent_escape(rel_path):
                issues.append(f"{domain}:entry_{idx}:path_parent_escape_forbidden")
                continue
            if entry_type in {"file", "dir"} and GLOB_MAGIC_RE.search(rel_path):
                issues.append(f"{domain}:entry_{idx}:glob_not_allowed_for_entry_type")
                continue
            resolved_candidate = (anchor_root / rel_path).resolve()
            if not _path_within(resolved_candidate, anchor_root):
                issues.append(f"{domain}:entry_{idx}:anchor_containment_violation")
                continue
            rules.append(
                {
                    "domain": domain,
                    "path_id": path_id,
                    "entry_type": entry_type,
                    "anchor_root": anchor_root.as_posix(),
                    "rel_path": rel_path,
                    "abs_pattern": _to_rule_abs_pattern(anchor_root, rel_path),
                }
            )
    return rules, issues


def _match_rule(path: Path, rule: dict[str, Any]) -> bool:
    candidate = path.resolve().as_posix()
    entry_type = str(rule.get("entry_type", "")).strip().lower()
    pattern = str(rule.get("abs_pattern", "")).strip()
    if not pattern:
        return False
    if entry_type == "file":
        return candidate == pattern
    if entry_type == "dir":
        return candidate == pattern or candidate.startswith(f"{pattern.rstrip('/')}/")
    if entry_type == "glob":
        return fnmatch.fnmatch(candidate, pattern)
    return False


def _allowed_by_registry(path: Path, rules: list[dict[str, Any]]) -> bool:
    return any(_match_rule(path, rule) for rule in rules)


def _collect_runtime_write_candidates(pack_path: Path) -> list[Path]:
    out: list[Path] = []
    feedback_root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if feedback_root.exists():
        out.extend(p for p in feedback_root.rglob("*") if p.is_file())
    reports_root = (pack_path / "runtime" / "reports").resolve()
    if reports_root.exists():
        out.extend(p for p in reports_root.rglob("broadcast-receipt-*.json") if p.is_file())
        out.extend(p for p in reports_root.rglob("broadcast-ack-*.json") if p.is_file())
    state_root = (pack_path / "runtime" / "state").resolve()
    state_file = state_root / "broadcast_state.json"
    if state_file.exists() and state_file.is_file():
        out.append(state_file.resolve())
    dedup: dict[str, Path] = {}
    for path in out:
        dedup[path.resolve().as_posix()] = path.resolve()
    return [dedup[key] for key in sorted(dedup.keys())]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol downsink path write guard (v1.6.8).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--probe-write-path", action="append", default=[])
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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": op,
        "required_contract": required,
        "auto_required_signal": bool(auto_required_signal),
        "contract_key": contract_key,
        "protocol_downsink_path_write_guard_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "probe_write_paths": [str(x).strip() for x in args.probe_write_path if str(x).strip()],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["protocol_downsink_path_write_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    path_registry = contract.get("path_registry")
    if not isinstance(path_registry, dict):
        payload["protocol_downsink_path_write_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = ["path_registry_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    rules, registry_issues = _build_registry_rules(
        path_registry=path_registry,
        pack_path=pack_path,
        repo_root=repo_root,
    )

    if registry_issues:
        payload["protocol_downsink_path_write_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = registry_issues
        _emit(payload, json_only=args.json_only)
        return 1

    candidate_paths: list[Path] = []
    candidate_paths.extend(_collect_runtime_write_candidates(pack_path))
    for raw_probe in payload["probe_write_paths"]:
        probe_path = Path(raw_probe).expanduser()
        if probe_path.is_absolute():
            candidate_paths.append(probe_path.resolve())
        else:
            candidate_paths.append((pack_path / probe_path).resolve())

    dedup_candidates: dict[str, Path] = {}
    for candidate in candidate_paths:
        dedup_candidates[candidate.resolve().as_posix()] = candidate.resolve()
    candidate_paths = [dedup_candidates[key] for key in sorted(dedup_candidates.keys())]

    violations: list[str] = []
    for candidate in candidate_paths:
        if not _allowed_by_registry(candidate, rules):
            violations.append(f"non_registry_write_path:{candidate.as_posix()}")

    payload["checked_candidate_count"] = len(candidate_paths)
    payload["checked_candidates"] = [p.as_posix() for p in candidate_paths]
    payload["registry_rule_count"] = len(rules)

    if violations:
        payload["protocol_downsink_path_write_guard_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_WRITE_GUARD
        payload["stale_reasons"] = violations
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_downsink_path_write_guard_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
