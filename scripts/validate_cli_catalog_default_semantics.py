#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from repo_root_resolution_common import resolve_repo_root
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CLI_CATALOG_DEFAULT = "IP-CLICAT-001"
REPO_FIXTURE_CATALOG = "identity/catalog/identities.yaml"
GLOBAL_HOME_CATALOG_TOKEN = ".codex/.identity/catalog.local.yaml"


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate CLI catalog default semantics (no silent repo-fixture fallback).")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--scripts-root", default="scripts")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    scripts_root = (repo_root / str(args.scripts_root)).resolve()

    payload: dict[str, Any] = {
        "cli_catalog_default_semantics_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_CLI_CATALOG_DEFAULT,
        "repo_root": str(repo_root),
        "scripts_root": str(scripts_root),
        "python_file_count": 0,
        "catalog_argument_count": 0,
        "repo_catalog_argument_count": 0,
        "runtime_catalog_repo_fixture_default_hits": [],
        "runtime_catalog_global_home_default_hits": [],
        "repo_catalog_repo_fixture_default_count": 0,
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

    if repo_fixture_hits or global_home_hits:
        payload["cli_catalog_default_semantics_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CLI_CATALOG_DEFAULT
        stale_reasons: list[str] = []
        if repo_fixture_hits:
            stale_reasons.append("runtime_catalog_default_repo_fixture_fallback_detected")
        if global_home_hits:
            stale_reasons.append("runtime_catalog_default_global_home_fallback_detected")
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["cli_catalog_default_semantics_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
