#!/usr/bin/env python3
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_VALIDATOR_GLOB = "scripts/validate_protocol_root_*.py"


@dataclass(frozen=True)
class ForbiddenPrimitiveContract:
    module: str
    primitive_name: str
    preferred_primitive: str
    primitive_class: str


FORBIDDEN_PRIMITIVE_CONTRACTS: tuple[ForbiddenPrimitiveContract, ...] = (
    ForbiddenPrimitiveContract(
        module="root_row_family_projection_common",
        primitive_name="project_row_family",
        preferred_primitive="project_row_families",
        primitive_class="row_family_projection",
    ),
    ForbiddenPrimitiveContract(
        module="root_contract_row_validation_common",
        primitive_name="validate_contract_rows",
        preferred_primitive="validate_contract_row_batches",
        primitive_class="contract_row_validation",
    ),
)

FORBIDDEN_PRIMITIVE_BY_MODULE: dict[str, dict[str, ForbiddenPrimitiveContract]] = {}
for _contract in FORBIDDEN_PRIMITIVE_CONTRACTS:
    FORBIDDEN_PRIMITIVE_BY_MODULE.setdefault(_contract.module, {})[
        _contract.primitive_name
    ] = _contract

FORBIDDEN_PRIMITIVE_BY_NAME: dict[str, ForbiddenPrimitiveContract] = {
    contract.primitive_name: contract for contract in FORBIDDEN_PRIMITIVE_CONTRACTS
}


def root_validator_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(sorted((repo_root / "scripts").glob("validate_protocol_root_*.py")))


def _rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return str(path.resolve())


def _scan_root_validator_file(
    repo_root: Path,
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rel_path = _rel_path(repo_root, path)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [], [{"rel_path": rel_path, "reason": "read_failed", "detail": str(exc)}]
    try:
        tree = ast.parse(text, filename=rel_path)
    except SyntaxError as exc:
        return [], [
            {
                "rel_path": rel_path,
                "reason": "parse_failed",
                "lineno": int(exc.lineno or 0),
                "detail": str(exc),
            }
        ]

    direct_name_bindings: dict[str, ForbiddenPrimitiveContract] = {}
    module_aliases: dict[str, str] = {}
    violations: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module_name = str(node.module or "").strip()
            forbidden_by_name = FORBIDDEN_PRIMITIVE_BY_MODULE.get(module_name, {})
            if not forbidden_by_name:
                continue
            for alias in node.names:
                contract = forbidden_by_name.get(alias.name)
                if contract is None:
                    continue
                local_name = str(alias.asname or alias.name)
                direct_name_bindings[local_name] = contract
                violations.append(
                    {
                        "rel_path": rel_path,
                        "reason": "forbidden_direct_import_binding",
                        "lineno": int(getattr(node, "lineno", 0) or 0),
                        "module": contract.module,
                        "primitive_name": contract.primitive_name,
                        "preferred_primitive": contract.preferred_primitive,
                        "primitive_class": contract.primitive_class,
                        "binding": local_name,
                    }
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_name = str(alias.name or "").strip()
                if module_name not in FORBIDDEN_PRIMITIVE_BY_MODULE:
                    continue
                local_name = str(alias.asname or module_name.rsplit(".", 1)[-1])
                module_aliases[local_name] = module_name

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            contract = direct_name_bindings.get(func.id)
            if contract is not None:
                violations.append(
                    {
                        "rel_path": rel_path,
                        "reason": "forbidden_direct_call_binding",
                        "lineno": int(getattr(node, "lineno", 0) or 0),
                        "module": contract.module,
                        "primitive_name": contract.primitive_name,
                        "preferred_primitive": contract.preferred_primitive,
                        "primitive_class": contract.primitive_class,
                        "binding": func.id,
                    }
                )
                continue
            contract = FORBIDDEN_PRIMITIVE_BY_NAME.get(func.id)
            if contract is not None:
                violations.append(
                    {
                        "rel_path": rel_path,
                        "reason": "forbidden_direct_call_literal",
                        "lineno": int(getattr(node, "lineno", 0) or 0),
                        "module": contract.module,
                        "primitive_name": contract.primitive_name,
                        "preferred_primitive": contract.preferred_primitive,
                        "primitive_class": contract.primitive_class,
                        "binding": func.id,
                    }
                )
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_name = module_aliases.get(func.value.id)
            if not module_name:
                continue
            contract = FORBIDDEN_PRIMITIVE_BY_MODULE.get(module_name, {}).get(func.attr)
            if contract is None:
                continue
            violations.append(
                {
                    "rel_path": rel_path,
                    "reason": "forbidden_module_attribute_call_binding",
                    "lineno": int(getattr(node, "lineno", 0) or 0),
                    "module": contract.module,
                    "primitive_name": contract.primitive_name,
                    "preferred_primitive": contract.preferred_primitive,
                    "primitive_class": contract.primitive_class,
                    "binding": f"{func.value.id}.{func.attr}",
                }
            )

    return violations, []


def scan_root_validator_shared_primitive_adoption(repo_root: Path) -> dict[str, Any]:
    validator_paths = root_validator_paths(repo_root)
    violations: list[dict[str, Any]] = []
    scan_errors: list[dict[str, Any]] = []
    for path in validator_paths:
        file_violations, file_errors = _scan_root_validator_file(repo_root, path)
        violations.extend(file_violations)
        scan_errors.extend(file_errors)

    primitive_class_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for row in violations:
        primitive_class = str(row.get("primitive_class") or "").strip() or "unknown"
        primitive_class_counts[primitive_class] = (
            primitive_class_counts.get(primitive_class, 0) + 1
        )
        reason = str(row.get("reason") or "").strip() or "unknown"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "root_validator_count": len(validator_paths),
        "scanned_validator_files": [_rel_path(repo_root, path) for path in validator_paths],
        "primitive_binding_violations": violations,
        "scan_errors": scan_errors,
        "primitive_violation_count": len(violations),
        "scan_error_count": len(scan_errors),
        "primitive_violation_file_count": len(
            {
                str(row.get("rel_path") or "")
                for row in violations
                if str(row.get("rel_path") or "").strip()
            }
        ),
        "primitive_violation_reason_counts": reason_counts,
        "primitive_class_violation_counts": primitive_class_counts,
    }
