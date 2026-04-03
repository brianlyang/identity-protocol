#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

from runtime_summary_surface_governance_common import (
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STRICT_ACTOR_ENTRY = "IP-ACTOR-ENTRY-SEM-001"

STRICT_ACTOR_ENTRY_DISCOVERY_TOKENS = (
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/final_emit_governed.py",
    "scripts/full_identity_protocol_scan.py",
    "CANONICAL_FINAL_EMIT_SCRIPT",
)
STRICT_ACTOR_ENTRY_LITERAL_FORBIDDEN = "assistant:codex"
STRICT_PROJECT_CATALOG_REPO_FIXTURE_FORBIDDEN = "identity/catalog/identities.yaml"
STRICT_ACTOR_ENTRY_GATE_MARKERS = (
    "IP-ACTOR-ENTRY-001",
    "resolve_required_protocol_actor_id(",
)
STRICT_SHELL_ENTRY_DISCOVERY_TOKENS = (
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/final_emit_governed.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/validate_full_scan_target_regression.py",
    "scripts/report_three_plane_status.py",
    "--output-last-message",
)
STRICT_SHELL_ENTRY_RULES: dict[str, dict[str, bool]] = {
    "scripts/ci/run_full_scan_target_regression_ci.sh": {
        "require_actor_helper": True,
        "require_session_helper": False,
        "require_project_catalog_helper": True,
        "require_session_primary_resolver": False,
        "forbid_compatibility_pointer_literal": False,
    },
    "scripts/ci/run_required_runtime_gates_ci.sh": {
        "require_actor_helper": True,
        "require_session_helper": False,
        "require_project_catalog_helper": True,
        "require_session_primary_resolver": False,
        "forbid_compatibility_pointer_literal": False,
    },
    "scripts/e2e_smoke_test.sh": {
        "require_actor_helper": True,
        "require_session_helper": False,
        "require_project_catalog_helper": False,
        "require_session_primary_resolver": False,
        "forbid_compatibility_pointer_literal": False,
    },
    "scripts/run_native_chat_headstamp_smoke.sh": {
        "require_actor_helper": True,
        "require_session_helper": True,
        "require_project_catalog_helper": True,
        "require_session_primary_resolver": True,
        "require_codex_tuple_handoff": True,
        "forbid_compatibility_pointer_literal": True,
    },
}
STRICT_SHELL_ENTRY_EXEMPTIONS: dict[str, tuple[str, ...]] = {
    "scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh": ("probe_fixture_catalog_allowed",),
    "scripts/ci/run_host_visible_surface_live_probes_ci.sh": ("probe_fixture_literals_allowed",),
    "scripts/ci/run_privilege_escalation_write_probes_ci.sh": ("probe_fixture_catalog_allowed",),
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE: ("probe_fixture_literals_allowed",),
    "scripts/ci/run_semantic_clarity_probes_ci.sh": ("probe_fixture_literals_allowed",),
    "scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh": ("probe_fixture_catalog_allowed",),
}
STRICT_SHELL_ACTOR_HELPER_TOKENS = (
    "protocol_shell_entry_require_actor_id",
    'CODEX_ACTOR_ID:?"set CODEX_ACTOR_ID',
)
STRICT_SHELL_SESSION_HELPER_TOKENS = (
    "protocol_shell_entry_require_session_id",
    'CODEX_SESSION_ID / IDENTITY_SESSION_ID',
)
STRICT_SHELL_PROJECT_CATALOG_HELPER_TOKENS = (
    "protocol_shell_entry_resolve_project_catalog",
    'IDENTITY_CATALOG is required (implicit catalog fallback is disabled).',
)
STRICT_SHELL_SESSION_PRIMARY_RESOLVER_TOKENS = (
    "protocol_shell_entry_resolve_session_primary_identity",
    "resolve_runtime_authoritative_identity.py",
)
STRICT_SHELL_CODEX_TUPLE_HANDOFF_TOKEN_GROUPS: tuple[tuple[str, ...], ...] = (
    (
        'env["CODEX_ACTOR_ID"] = actor_id',
        'env["CODEX_SESSION_ID"] = session_id',
        'env["IDENTITY_SESSION_ID"] = session_id',
    ),
    (
        "CODEX_ACTOR_ID=",
        "CODEX_SESSION_ID=",
        "IDENTITY_SESSION_ID=",
        '"codex"',
    ),
)
STRICT_SHELL_ACTOR_LITERAL_RE = re.compile(r"(assistant:codex|CODEX_ACTOR_ID:-assistant:codex)")
STRICT_SHELL_PROJECT_CATALOG_LITERAL_RE = re.compile(
    r"((^|[^A-Z_])CATALOG_PATH=.*identity/catalog/identities\.yaml|--project-catalog[ =\"']+identity/catalog/identities\.yaml)"
)
STRICT_SHELL_COMPAT_POINTER_LITERAL_RE = re.compile(r"active_identity\.json")


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


def _forbidden_project_catalog_default_hits(tree: ast.Module, *, constants: dict[str, str]) -> list[int]:
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_add_argument_call(node):
            continue
        if "--project-catalog" not in _option_tokens(node):
            continue
        if _extract_default_literal(node, constants=constants) == STRICT_PROJECT_CATALOG_REPO_FIXTURE_FORBIDDEN:
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


def _first_regex_line(lines: list[str], pattern: re.Pattern[str]) -> int:
    for idx, line in enumerate(lines, start=1):
        if pattern.search(line):
            return idx
    return 0


def _missing_codex_tuple_handoff_tokens(text: str) -> list[str]:
    for token_group in STRICT_SHELL_CODEX_TUPLE_HANDOFF_TOKEN_GROUPS:
        if all(token in text for token in token_group):
            return []
    return list(STRICT_SHELL_CODEX_TUPLE_HANDOFF_TOKEN_GROUPS[0])


def _scan_shell_strict_entry_surfaces(repo_root: Path) -> tuple[list[str], dict[str, list[str]], list[dict[str, Any]]]:
    discovered: list[str] = []
    exemptions: dict[str, list[str]] = {}
    violations: list[dict[str, Any]] = []
    for path in sorted((repo_root / "scripts").rglob("*.sh")):
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in STRICT_SHELL_ENTRY_DISCOVERY_TOKENS):
            continue
        rel = _relative(path, repo_root)
        lines = text.splitlines()
        discovered.append(rel)

        exemption_reasons = list(STRICT_SHELL_ENTRY_EXEMPTIONS.get(rel, ()))
        if exemption_reasons:
            exemptions[rel] = exemption_reasons
            continue

        rule = STRICT_SHELL_ENTRY_RULES.get(rel)
        if rule is None:
            violations.append(
                {
                    "file": rel,
                    "line": 1,
                    "violation_type": "shell_strict_entry_registry_missing",
                    "snippet": next((line.strip() for line in lines if line.strip()), ""),
                }
            )
            actor_line = _first_regex_line(lines, STRICT_SHELL_ACTOR_LITERAL_RE)
            if actor_line:
                violations.append(
                    {
                        "file": rel,
                        "line": actor_line,
                        "violation_type": "shell_strict_actor_default_literal_forbidden",
                        "snippet": lines[actor_line - 1].strip(),
                    }
                )
            catalog_line = _first_regex_line(lines, STRICT_SHELL_PROJECT_CATALOG_LITERAL_RE)
            if catalog_line:
                violations.append(
                    {
                        "file": rel,
                        "line": catalog_line,
                        "violation_type": "shell_strict_project_catalog_repo_fixture_default_forbidden",
                        "snippet": lines[catalog_line - 1].strip(),
                    }
                )
            continue

        if rule.get("require_actor_helper", False):
            if not any(token in text for token in STRICT_SHELL_ACTOR_HELPER_TOKENS):
                violations.append(
                    {
                        "file": rel,
                        "line": 1,
                        "violation_type": "shell_strict_actor_helper_missing",
                        "snippet": "protocol_shell_entry_require_actor_id",
                    }
                )
            actor_line = _first_regex_line(lines, STRICT_SHELL_ACTOR_LITERAL_RE)
            if actor_line:
                violations.append(
                    {
                        "file": rel,
                        "line": actor_line,
                        "violation_type": "shell_strict_actor_default_literal_forbidden",
                        "snippet": lines[actor_line - 1].strip(),
                    }
                )

        if rule.get("require_project_catalog_helper", False):
            if not any(token in text for token in STRICT_SHELL_PROJECT_CATALOG_HELPER_TOKENS):
                violations.append(
                    {
                        "file": rel,
                        "line": 1,
                        "violation_type": "shell_strict_project_catalog_helper_missing",
                        "snippet": "protocol_shell_entry_resolve_project_catalog",
                    }
                )
            catalog_line = _first_regex_line(lines, STRICT_SHELL_PROJECT_CATALOG_LITERAL_RE)
            if catalog_line:
                violations.append(
                    {
                        "file": rel,
                        "line": catalog_line,
                        "violation_type": "shell_strict_project_catalog_repo_fixture_default_forbidden",
                        "snippet": lines[catalog_line - 1].strip(),
                    }
                )

        if rule.get("require_session_helper", False):
            if not any(token in text for token in STRICT_SHELL_SESSION_HELPER_TOKENS):
                violations.append(
                    {
                        "file": rel,
                        "line": 1,
                        "violation_type": "shell_strict_session_helper_missing",
                        "snippet": "protocol_shell_entry_require_session_id",
                    }
                )

        if rule.get("require_session_primary_resolver", False):
            if not any(token in text for token in STRICT_SHELL_SESSION_PRIMARY_RESOLVER_TOKENS):
                violations.append(
                    {
                        "file": rel,
                        "line": 1,
                        "violation_type": "shell_strict_session_primary_resolver_missing",
                        "snippet": "protocol_shell_entry_resolve_session_primary_identity",
                    }
                )

        if rule.get("require_codex_tuple_handoff", False):
            missing_tokens = _missing_codex_tuple_handoff_tokens(text)
            if missing_tokens:
                violations.append(
                    {
                        "file": rel,
                        "line": 1,
                        "violation_type": "shell_strict_codex_tuple_handoff_missing",
                        "snippet": missing_tokens[0],
                    }
                )

        if rule.get("forbid_compatibility_pointer_literal", False):
            compat_line = _first_regex_line(lines, STRICT_SHELL_COMPAT_POINTER_LITERAL_RE)
            if compat_line:
                violations.append(
                    {
                        "file": rel,
                        "line": compat_line,
                        "violation_type": "shell_strict_compatibility_pointer_literal_forbidden",
                        "snippet": lines[compat_line - 1].strip(),
                    }
                )

    return discovered, exemptions, violations


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fail-close when strict authority-entry orchestrators silently fall back to a default actor."
    )
    ap.add_argument("--repo-root", default="", help="repository root to scan; defaults to script parent repo")
    ap.add_argument("--scripts-root", default="", help="scripts root relative to repo root; defaults to repo_root/scripts")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = (
        Path(args.repo_root).expanduser().resolve()
        if str(args.repo_root or "").strip()
        else Path(__file__).resolve().parent.parent
    )
    scripts_root = (
        (repo_root / str(args.scripts_root)).resolve()
        if str(args.scripts_root or "").strip()
        else (repo_root / "scripts").resolve()
    )

    payload: dict[str, Any] = {
        "strict_actor_entry_semantics_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_STRICT_ACTOR_ENTRY,
        "repo_root": str(repo_root),
        "scripts_root": str(scripts_root),
        "discovered_surface_files": [],
        "discovered_surface_file_count": 0,
        "discovered_shell_surface_files": [],
        "discovered_shell_surface_file_count": 0,
        "exempt_shell_surface_files": {},
        "violation_count": 0,
        "violations": [],
        "stale_reasons": [],
    }

    if not scripts_root.exists() or not scripts_root.is_dir():
        payload["stale_reasons"] = ["scripts_root_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    discovered: list[str] = []
    discovered_shell: list[str] = []
    exempt_shell: dict[str, list[str]] = {}
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

        for line in _forbidden_project_catalog_default_hits(tree, constants=constants):
            violations.append(
                {
                    "file": rel,
                    "line": line,
                    "violation_type": "strict_project_catalog_repo_fixture_default_forbidden",
                    "snippet": STRICT_PROJECT_CATALOG_REPO_FIXTURE_FORBIDDEN,
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

    discovered_shell, exempt_shell, shell_violations = _scan_shell_strict_entry_surfaces(repo_root)
    violations.extend(shell_violations)

    if not discovered and not discovered_shell:
        violations.append(
            {
                "file": str(scripts_root),
                "line": 1,
                "violation_type": "strict_entry_surface_discovery_empty",
                "snippet": "no strict-entry surfaces discovered under scripts root",
            }
        )

    stale_reasons = sorted({str(item.get("violation_type", "")).strip() for item in violations if item.get("violation_type")})
    payload.update(
        {
            "strict_actor_entry_semantics_status": STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
            "error_code": "" if not violations else ERR_STRICT_ACTOR_ENTRY,
            "discovered_surface_files": discovered,
            "discovered_surface_file_count": len(discovered),
            "discovered_shell_surface_files": discovered_shell,
            "discovered_shell_surface_file_count": len(discovered_shell),
            "exempt_shell_surface_files": exempt_shell,
            "violation_count": len(violations),
            "violations": violations,
            "stale_reasons": stale_reasons,
        }
    )

    _emit(payload, json_only=args.json_only)
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
