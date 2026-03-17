#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STRICT_ACTOR_ENTRY = "IP-ACTOR-ENTRY-SEM-001"

STRICT_ACTOR_ENTRY_DISCOVERY_TOKENS = (
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/final_emit_governed.py",
    "CANONICAL_FINAL_EMIT_SCRIPT",
)
STRICT_ACTOR_ENTRY_LITERAL_FORBIDDEN = "assistant:codex"
STRICT_ACTOR_ENTRY_GATE_MARKERS = (
    "IP-ACTOR-ENTRY-001",
    "resolve_required_protocol_actor_id(",
)


def _const_str(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return str(node.value)
    return ""


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


def _extract_default_literal(node: ast.Call, *, constants: dict[str, str]) -> str:
    default_node: ast.AST | None = None
    for kw in node.keywords:
        if kw.arg == "default":
            default_node = kw.value
            break
    if default_node is None:
        return ""
    token = _const_str(default_node)
    if token:
        return token
    if isinstance(default_node, ast.Name):
        return str(constants.get(default_node.id, ""))
    if (
        isinstance(default_node, ast.Call)
        and isinstance(default_node.func, ast.Attribute)
        and default_node.func.attr == "get"
        and isinstance(default_node.func.value, ast.Attribute)
        and default_node.func.value.attr == "environ"
        and len(default_node.args) >= 2
    ):
        return _const_str(default_node.args[1])
    return ""


def _has_resolve_actor_id_call(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "resolve_actor_id":
            return True
    return False


def _forbidden_actor_default_hits(tree: ast.Module, *, constants: dict[str, str]) -> list[int]:
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_add_argument_call(node):
            continue
        if "--actor-id" not in _option_tokens(node):
            continue
        if _extract_default_literal(node, constants=constants) == STRICT_ACTOR_ENTRY_LITERAL_FORBIDDEN:
            hits.append(int(getattr(node, "lineno", 0) or 0))
    return hits


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path.resolve())


def _first_line(lines: list[str], token: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if token in line:
            return idx
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-close when strict authority-entry orchestrators silently fall back to a default actor."
    )
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--scripts-root", default="scripts")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    scripts_root = (repo_root / str(args.scripts_root)).resolve()

    payload: dict[str, Any] = {
        "strict_actor_entry_semantics_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_STRICT_ACTOR_ENTRY,
        "repo_root": str(repo_root),
        "scripts_root": str(scripts_root),
        "discovered_surface_files": [],
        "violation_count": 0,
        "violations": [],
        "stale_reasons": [],
    }

    if not scripts_root.exists() or not scripts_root.is_dir():
        payload["stale_reasons"] = ["scripts_root_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    discovered: list[str] = []
    violations: list[dict[str, Any]] = []
    for path in sorted(scripts_root.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(path))
        except Exception:
            continue
        if not any(token in text for token in STRICT_ACTOR_ENTRY_DISCOVERY_TOKENS):
            continue

        rel = _relative(path, repo_root)
        lines = text.splitlines()
        constants = _collect_constant_assignments(tree)
        discovered.append(rel)

        for line in _forbidden_actor_default_hits(tree, constants=constants):
            violations.append(
                {
                    "file": rel,
                    "line": line,
                    "violation_type": "strict_actor_default_literal_forbidden",
                    "snippet": STRICT_ACTOR_ENTRY_LITERAL_FORBIDDEN,
                }
            )

        if _has_resolve_actor_id_call(tree) and not any(marker in text for marker in STRICT_ACTOR_ENTRY_GATE_MARKERS):
            violations.append(
                {
                    "file": rel,
                    "line": _first_line(lines, "resolve_actor_id("),
                    "violation_type": "strict_actor_entry_gate_missing",
                    "snippet": "resolve_actor_id(",
                }
            )

    stale_reasons = sorted({str(item.get("violation_type", "")).strip() for item in violations if item.get("violation_type")})
    payload.update(
        {
            "strict_actor_entry_semantics_status": STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
            "error_code": "" if not violations else ERR_STRICT_ACTOR_ENTRY,
            "discovered_surface_files": discovered,
            "violation_count": len(violations),
            "violations": violations,
            "stale_reasons": stale_reasons,
        }
    )

    _emit(payload, json_only=args.json_only)
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
