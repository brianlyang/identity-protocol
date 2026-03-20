#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from repo_root_resolution_common import resolve_repo_root, resolve_workspace_root
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_CLI_CATALOG_DEFAULT = "IP-CLICAT-001"
REPO_FIXTURE_CATALOG = "identity/catalog/identities.yaml"
GLOBAL_HOME_CATALOG_TOKEN = ".codex/.identity/catalog.local.yaml"
PATH_ERROR_MARKERS = (
    "repo catalog not found:",
    "catalog not found:",
    "missing catalog:",
)


def _const_str(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return str(node.value)
    return ""


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _collect_string_constants(node: ast.AST) -> set[str]:
    values: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.add(str(child.value))
    return values


def _contains_path_home_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute) and func.attr == "home":
            base = func.value
            if isinstance(base, ast.Name) and base.id == "Path":
                return True
    return False


def _looks_like_global_runtime_catalog(node: ast.AST | None) -> bool:
    if node is None:
        return False
    string_constants = {_norm_path(token) for token in _collect_string_constants(node)}
    if any(GLOBAL_HOME_CATALOG_TOKEN in token for token in string_constants):
        return True
    if not _contains_path_home_call(node):
        return False
    return {".codex", ".identity", "catalog.local.yaml"}.issubset(string_constants)


def _mentions_args_catalog(node: ast.AST | None) -> bool:
    if node is None:
        return False
    for child in ast.walk(node):
        if not isinstance(child, ast.Attribute):
            continue
        if child.attr != "catalog":
            continue
        if isinstance(child.value, ast.Name) and child.value.id == "args":
            return True
    return False


def _collect_constant_assignments(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            continue
        token = _const_str(stmt.value)
        if token:
            out[target.id] = token
    return out


def _extract_default_literal(node: ast.Call, *, constants: dict[str, str]) -> str:
    default_node = _extract_default_node(node)
    if default_node is None:
        return ""
    token = _const_str(default_node)
    if token:
        return token
    if isinstance(default_node, ast.Name):
        return str(constants.get(default_node.id, ""))
    return ""


def _extract_default_node(node: ast.Call) -> ast.AST | None:
    for kw in node.keywords:
        if kw.arg == "default":
            return kw.value
    return None


def _is_add_argument_call(node: ast.Call) -> bool:
    fn = node.func
    return isinstance(fn, ast.Attribute) and fn.attr == "add_argument"


def _option_tokens(node: ast.Call) -> list[str]:
    out: list[str] = []
    for arg in node.args:
        token = _const_str(arg)
        if token:
            out.append(token)
    return out


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _pick_identity_id(local_catalog_path: Path) -> str:
    catalog = _load_yaml(local_catalog_path)
    identities = [row for row in (catalog.get("identities") or []) if isinstance(row, dict)]
    default_identity = str(catalog.get("default_identity", "")).strip()
    if default_identity:
        return default_identity
    for row in identities:
        if str(row.get("status", "")).strip().lower() == "active":
            identity_id = str(row.get("id", "")).strip()
            if identity_id:
                return identity_id
    for row in identities:
        identity_id = str(row.get("id", "")).strip()
        if identity_id:
            return identity_id
    raise ValueError(f"no identity rows found in local catalog: {local_catalog_path}")


def _trim(text: str, *, limit: int = 1200) -> str:
    raw = str(text or "").strip()
    return raw[-limit:]


def _run_command(command: list[str], *, cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    return {
        "cwd": str(cwd),
        "command": command,
        "rc": proc.returncode,
        "stdout": str(proc.stdout or ""),
        "stderr": str(proc.stderr or ""),
    }


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _has_path_error(result: dict[str, Any]) -> bool:
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    return any(marker in combined for marker in PATH_ERROR_MARKERS)


def _evaluate_path_probe(workspace_result: dict[str, Any], protocol_result: dict[str, Any]) -> tuple[bool, list[str]]:
    stale_reasons: list[str] = []
    if _has_path_error(workspace_result):
        stale_reasons.append("workspace_launch_context_path_error")
    if _has_path_error(protocol_result):
        stale_reasons.append("protocol_launch_context_path_error")
    return not stale_reasons, stale_reasons


def _evaluate_identity_status_probe(
    workspace_result: dict[str, Any],
    protocol_result: dict[str, Any],
    *,
    identity_id: str,
    expected_pack_path: Path,
) -> tuple[bool, list[str]]:
    stale_reasons: list[str] = []
    for label, result in (("workspace", workspace_result), ("protocol", protocol_result)):
        payload = _parse_json_payload(str(result.get("stdout", "")))
        if not payload:
            stale_reasons.append(f"{label}_identity_status_non_json")
            continue
        if str(payload.get("identity_id", "")).strip() != identity_id:
            stale_reasons.append(f"{label}_identity_status_identity_mismatch")
        if str(payload.get("pack_path", "")).strip() != str(expected_pack_path):
            stale_reasons.append(f"{label}_identity_status_pack_path_mismatch")
    return not stale_reasons, stale_reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate CLI catalog default semantics (no silent repo-fixture fallback).")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--scripts-root", default="scripts")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    scripts_root = (repo_root / str(args.scripts_root)).resolve()

    payload: dict[str, Any] = {
        "cli_catalog_default_semantics_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_CLI_CATALOG_DEFAULT,
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "scripts_root": str(scripts_root),
        "python_file_count": 0,
        "catalog_argument_count": 0,
        "repo_catalog_argument_count": 0,
        "runtime_catalog_repo_fixture_default_hits": [],
        "runtime_catalog_global_home_default_hits": [],
        "repo_catalog_repo_fixture_default_count": 0,
        "launch_context_parity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "launch_context_probe_identity_id": "",
        "launch_context_parity_probes": [],
        "stale_reasons": [],
    }

    if not scripts_root.exists() or not scripts_root.is_dir():
        payload["stale_reasons"] = ["scripts_root_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    py_files = sorted(scripts_root.glob("*.py"))
    payload["python_file_count"] = len(py_files)

    repo_fixture_hits: list[dict[str, Any]] = []
    global_home_hits: list[dict[str, Any]] = []
    repo_catalog_repo_fixture_default_count = 0
    catalog_argument_count = 0
    repo_catalog_argument_count = 0

    for path in py_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except Exception:
            continue

        constants = _collect_constant_assignments(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_add_argument_call(node):
                continue
            option_tokens = _option_tokens(node)
            if not option_tokens:
                continue

            default_literal = _norm_path(_extract_default_literal(node, constants=constants))
            has_catalog = "--catalog" in option_tokens
            has_repo_catalog = "--repo-catalog" in option_tokens

            if has_catalog:
                catalog_argument_count += 1
                if default_literal == REPO_FIXTURE_CATALOG:
                    repo_fixture_hits.append(
                        {
                            "file": str(path),
                            "line": int(getattr(node, "lineno", 0) or 0),
                            "options": option_tokens,
                            "default": default_literal,
                        }
                    )
                default_node = _extract_default_node(node)
                if _looks_like_global_runtime_catalog(default_node):
                    global_home_hits.append(
                        {
                            "file": str(path),
                            "line": int(getattr(node, "lineno", 0) or 0),
                            "kind": "catalog_argument_default",
                            "options": option_tokens,
                        }
                    )

            if has_repo_catalog:
                repo_catalog_argument_count += 1
                if default_literal == REPO_FIXTURE_CATALOG:
                    repo_catalog_repo_fixture_default_count += 1

        for node in ast.walk(tree):
            if not isinstance(node, ast.IfExp):
                continue
            if not _mentions_args_catalog(node.test):
                continue
            if _looks_like_global_runtime_catalog(node.body) or _looks_like_global_runtime_catalog(node.orelse):
                global_home_hits.append(
                    {
                        "file": str(path),
                        "line": int(getattr(node, "lineno", 0) or 0),
                        "kind": "args_catalog_fallback",
                        "options": [],
                    }
                )

    payload["catalog_argument_count"] = catalog_argument_count
    payload["repo_catalog_argument_count"] = repo_catalog_argument_count
    payload["runtime_catalog_repo_fixture_default_hits"] = repo_fixture_hits
    payload["runtime_catalog_global_home_default_hits"] = global_home_hits
    payload["repo_catalog_repo_fixture_default_count"] = repo_catalog_repo_fixture_default_count

    local_catalog_path = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
    launch_context_stale_reasons: list[str] = []
    if local_catalog_path.exists():
        try:
            identity_id = str(args.identity_id or "").strip() or _pick_identity_id(local_catalog_path)
            payload["launch_context_probe_identity_id"] = identity_id
            expected_pack_path = (workspace_root / ".identity" / identity_id).resolve()
            repo_catalog_path = (repo_root / REPO_FIXTURE_CATALOG).resolve()
            issue_021_probes = [
                {
                    "name": "validate_fixture_runtime_boundary",
                    "workspace_cmd": [
                        "python3",
                        f"{repo_root.name}/scripts/validate_fixture_runtime_boundary.py",
                        "--identity-id",
                        identity_id,
                        "--catalog",
                        str(local_catalog_path),
                        "--json-only",
                    ],
                    "protocol_cmd": [
                        "python3",
                        "scripts/validate_fixture_runtime_boundary.py",
                        "--identity-id",
                        identity_id,
                        "--catalog",
                        str(local_catalog_path),
                        "--json-only",
                    ],
                    "evaluator": "path_probe",
                },
                {
                    "name": "validate_protocol_entry_candidate_bridge",
                    "workspace_cmd": [
                        "python3",
                        f"{repo_root.name}/scripts/validate_protocol_entry_candidate_bridge.py",
                        "--catalog",
                        str(local_catalog_path),
                        "--identity-id",
                        identity_id,
                        "--json-only",
                    ],
                    "protocol_cmd": [
                        "python3",
                        "scripts/validate_protocol_entry_candidate_bridge.py",
                        "--catalog",
                        str(local_catalog_path),
                        "--identity-id",
                        identity_id,
                        "--json-only",
                    ],
                    "evaluator": "path_probe",
                },
                {
                    "name": "render_identity_response_stamp",
                    "workspace_cmd": [
                        "python3",
                        f"{repo_root.name}/scripts/render_identity_response_stamp.py",
                        "--identity-id",
                        identity_id,
                        "--catalog",
                        str(local_catalog_path),
                        "--actor-id",
                        "assistant:codex",
                        "--session-id",
                        "test-session",
                        "--json-only",
                    ],
                    "protocol_cmd": [
                        "python3",
                        "scripts/render_identity_response_stamp.py",
                        "--identity-id",
                        identity_id,
                        "--catalog",
                        str(local_catalog_path),
                        "--actor-id",
                        "assistant:codex",
                        "--session-id",
                        "test-session",
                        "--json-only",
                    ],
                    "evaluator": "path_probe",
                },
                {
                    "name": "validate_identity_local_persistence",
                    "workspace_cmd": [
                        "python3",
                        f"{repo_root.name}/scripts/validate_identity_local_persistence.py",
                        "--repo-catalog",
                        str(repo_catalog_path),
                        "--local-catalog",
                        str(local_catalog_path),
                    ],
                    "protocol_cmd": [
                        "python3",
                        "scripts/validate_identity_local_persistence.py",
                        "--repo-catalog",
                        str(repo_catalog_path),
                        "--local-catalog",
                        str(local_catalog_path),
                    ],
                    "evaluator": "local_persistence",
                },
                {
                    "name": "identity_status",
                    "workspace_cmd": [
                        "python3",
                        f"{repo_root.name}/scripts/identity_status.py",
                        "--identity-id",
                        identity_id,
                        "--json",
                    ],
                    "protocol_cmd": [
                        "python3",
                        "scripts/identity_status.py",
                        "--identity-id",
                        identity_id,
                        "--json",
                    ],
                    "evaluator": "identity_status",
                },
            ]
            for probe in issue_021_probes:
                workspace_result = _run_command(probe["workspace_cmd"], cwd=workspace_root)
                protocol_result = _run_command(probe["protocol_cmd"], cwd=repo_root)
                if probe["evaluator"] == "path_probe":
                    ok, reasons = _evaluate_path_probe(workspace_result, protocol_result)
                elif probe["evaluator"] == "local_persistence":
                    reasons = []
                    if int(workspace_result.get("rc", 1)) != 0:
                        reasons.append("workspace_local_persistence_failed")
                    if int(protocol_result.get("rc", 1)) != 0:
                        reasons.append("protocol_local_persistence_failed")
                    ok = not reasons
                else:
                    ok, reasons = _evaluate_identity_status_probe(
                        workspace_result,
                        protocol_result,
                        identity_id=identity_id,
                        expected_pack_path=expected_pack_path,
                    )
                payload["launch_context_parity_probes"].append(
                    {
                        "name": probe["name"],
                        "status": STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED,
                        "workspace_replay": workspace_result,
                        "protocol_replay": protocol_result,
                        "stale_reasons": reasons,
                    }
                )
                launch_context_stale_reasons.extend(f"{probe['name']}:{reason}" for reason in reasons)
        except Exception as exc:
            launch_context_stale_reasons.append(f"launch_context_probe_error:{exc}")
    else:
        launch_context_stale_reasons.append(f"workspace_local_catalog_missing:{local_catalog_path}")

    payload["launch_context_parity_status"] = (
        STATUS_FAIL_REQUIRED
        if launch_context_stale_reasons and local_catalog_path.exists()
        else STATUS_SKIPPED_NOT_REQUIRED if launch_context_stale_reasons else STATUS_PASS_REQUIRED
    )

    if repo_fixture_hits or global_home_hits:
        payload["cli_catalog_default_semantics_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CLI_CATALOG_DEFAULT
        stale_reasons: list[str] = []
        if repo_fixture_hits:
            stale_reasons.append("runtime_catalog_default_repo_fixture_fallback_detected")
        if global_home_hits:
            stale_reasons.append("runtime_catalog_default_global_home_fallback_detected")
        stale_reasons.extend(launch_context_stale_reasons)
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    if launch_context_stale_reasons and local_catalog_path.exists():
        payload["cli_catalog_default_semantics_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CLI_CATALOG_DEFAULT
        payload["stale_reasons"] = launch_context_stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["cli_catalog_default_semantics_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
