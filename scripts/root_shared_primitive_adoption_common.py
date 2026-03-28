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

PREFERRED_PRIMITIVE_BY_MODULE: dict[str, dict[str, dict[str, str]]] = {}
for _contract in FORBIDDEN_PRIMITIVE_CONTRACTS:
    PREFERRED_PRIMITIVE_BY_MODULE.setdefault(_contract.module, {})[
        _contract.preferred_primitive
    ] = {
        "module": _contract.module,
        "primitive_name": _contract.preferred_primitive,
        "primitive_class": _contract.primitive_class,
    }

PREFERRED_PRIMITIVE_BY_NAME: dict[str, dict[str, str]] = {
    primitive_name: primitive_contract
    for primitive_contracts in PREFERRED_PRIMITIVE_BY_MODULE.values()
    for primitive_name, primitive_contract in primitive_contracts.items()
}

PLACEHOLDER_ASSIGNMENT_MODES = frozenset({"initializer_empty_list"})


def root_validator_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(sorted((repo_root / "scripts").glob("validate_protocol_root_*.py")))


def _rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return str(path.resolve())


def _is_empty_list_initializer(node: ast.AST) -> bool:
    if isinstance(node, ast.List):
        return len(node.elts) == 0
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id == "list" and len(node.args) == 0 and len(node.keywords) == 0
    return False


def _is_effective_row_family_projection_assignment(row: dict[str, Any]) -> bool:
    assignment_mode = str(row.get("assignment_mode") or "").strip()
    return assignment_mode not in PLACEHOLDER_ASSIGNMENT_MODES


def _scan_root_validator_file(
    repo_root: Path,
    path: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
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
    preferred_direct_bindings: dict[str, dict[str, str]] = {}
    module_aliases: dict[str, str] = {}
    violations: list[dict[str, Any]] = []
    primitive_adoption_rows: list[dict[str, Any]] = []
    row_family_projection_assignment_rows: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module_name = str(node.module or "").strip()
            forbidden_by_name = FORBIDDEN_PRIMITIVE_BY_MODULE.get(module_name, {})
            preferred_by_name = PREFERRED_PRIMITIVE_BY_MODULE.get(module_name, {})
            if not forbidden_by_name:
                for alias in node.names:
                    primitive_contract = preferred_by_name.get(alias.name)
                    if primitive_contract is None:
                        continue
                    local_name = str(alias.asname or alias.name)
                    preferred_direct_bindings[local_name] = primitive_contract
                continue
            for alias in node.names:
                contract = forbidden_by_name.get(alias.name)
                if contract is None and alias.name in preferred_by_name:
                    local_name = str(alias.asname or alias.name)
                    preferred_direct_bindings[local_name] = preferred_by_name[alias.name]
                    continue
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
                if (
                    module_name not in FORBIDDEN_PRIMITIVE_BY_MODULE
                    and module_name not in PREFERRED_PRIMITIVE_BY_MODULE
                ):
                    continue
                local_name = str(alias.asname or module_name.rsplit(".", 1)[-1])
                module_aliases[local_name] = module_name

    def _call_binding_details(func: ast.AST) -> tuple[dict[str, str] | None, str]:
        if isinstance(func, ast.Name):
            contract = preferred_direct_bindings.get(func.id)
            if contract is not None:
                return contract, func.id
            contract = PREFERRED_PRIMITIVE_BY_NAME.get(func.id)
            if contract is not None:
                return contract, func.id
            return None, func.id
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_name = module_aliases.get(func.value.id)
            if not module_name:
                return None, f"{func.value.id}.{func.attr}"
            contract = PREFERRED_PRIMITIVE_BY_MODULE.get(module_name, {}).get(func.attr)
            return contract, f"{func.value.id}.{func.attr}"
        return None, ast.dump(func, include_attributes=False)

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
                _, binding = _call_binding_details(func)
                primitive_contract = None
            else:
                contract = FORBIDDEN_PRIMITIVE_BY_MODULE.get(module_name, {}).get(func.attr)
                if contract is not None:
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
                primitive_contract, binding = _call_binding_details(func)
            if primitive_contract is not None:
                primitive_adoption_rows.append(
                    {
                        "rel_path": rel_path,
                        "lineno": int(getattr(node, "lineno", 0) or 0),
                        "module": primitive_contract["module"],
                        "primitive_name": primitive_contract["primitive_name"],
                        "primitive_class": primitive_contract["primitive_class"],
                        "binding": binding,
                        "call_mode": "module_attribute_binding",
                    }
                )
            continue
        primitive_contract, binding = _call_binding_details(func)
        if primitive_contract is not None:
            primitive_adoption_rows.append(
                {
                    "rel_path": rel_path,
                    "lineno": int(getattr(node, "lineno", 0) or 0),
                    "module": primitive_contract["module"],
                    "primitive_name": primitive_contract["primitive_name"],
                    "primitive_class": primitive_contract["primitive_class"],
                    "binding": binding,
                    "call_mode": "direct_name_binding",
                }
            )

    assignment_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    for node in assignment_nodes:
        target_names: list[str] = []
        if isinstance(node, ast.Assign):
            target_names = [
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            ]
            value = node.value
        else:
            target_names = [node.target.id] if isinstance(node.target, ast.Name) else []
            value = node.value
        if "row_family_projection_rows" not in target_names or value is None:
            continue

        assignment_row: dict[str, Any] = {
            "rel_path": rel_path,
            "lineno": int(getattr(node, "lineno", 0) or 0),
            "target": "row_family_projection_rows",
            "assignment_mode": "",
            "binding": "",
            "assignment_role": "",
            "violation": False,
        }
        if _is_empty_list_initializer(value):
            assignment_row["assignment_mode"] = "initializer_empty_list"
            assignment_row["binding"] = type(value).__name__
            row_family_projection_assignment_rows.append(assignment_row)
            continue
        if isinstance(value, ast.Call):
            primitive_contract, binding = _call_binding_details(value.func)
            assignment_row["binding"] = binding
            if (
                primitive_contract is not None
                and primitive_contract["primitive_name"] == "project_row_families"
            ):
                assignment_row["assignment_mode"] = "shared_primitive_call"
                assignment_row["primitive_class"] = primitive_contract["primitive_class"]
                assignment_row["primitive_name"] = primitive_contract["primitive_name"]
                assignment_row["module"] = primitive_contract["module"]
            else:
                assignment_row["assignment_mode"] = "non_shared_call"
        else:
            assignment_row["assignment_mode"] = f"non_call_{type(value).__name__}"
            assignment_row["binding"] = type(value).__name__
        row_family_projection_assignment_rows.append(assignment_row)

    row_family_projection_assignment_rows.sort(
        key=lambda row: int(row.get("lineno", 0) or 0)
    )
    effective_assignment_indices = [
        index
        for index, row in enumerate(row_family_projection_assignment_rows)
        if _is_effective_row_family_projection_assignment(row)
    ]
    if effective_assignment_indices:
        effective_assignment_index = effective_assignment_indices[-1]
        for index, row in enumerate(row_family_projection_assignment_rows):
            if index < effective_assignment_index:
                row["assignment_role"] = (
                    "superseded_assignment"
                    if _is_effective_row_family_projection_assignment(row)
                    else "prebinding_placeholder"
                )
            elif index == effective_assignment_index:
                row["assignment_role"] = "effective_assignment"
            else:
                row["assignment_role"] = "post_effective_assignment"

        effective_row = row_family_projection_assignment_rows[effective_assignment_index]
        assignment_mode = str(effective_row.get("assignment_mode") or "").strip()
        if assignment_mode != "shared_primitive_call":
            effective_row["violation"] = True
            violations.append(
                {
                    "rel_path": rel_path,
                    "reason": (
                        "row_family_projection_effective_assignment_not_shared_call"
                        if assignment_mode == "non_shared_call"
                        else "row_family_projection_effective_assignment_not_call"
                    ),
                    "lineno": int(effective_row.get("lineno", 0) or 0),
                    "primitive_class": "row_family_projection",
                    "preferred_primitive": "project_row_families",
                    "binding": str(effective_row.get("binding") or "").strip(),
                }
            )
    elif row_family_projection_assignment_rows:
        effective_row = row_family_projection_assignment_rows[-1]
        for row in row_family_projection_assignment_rows[:-1]:
            row["assignment_role"] = "prebinding_placeholder"
        effective_row["assignment_role"] = "missing_effective_assignment"
        effective_row["violation"] = True
        violations.append(
            {
                "rel_path": rel_path,
                "reason": "row_family_projection_missing_effective_assignment",
                "lineno": int(effective_row.get("lineno", 0) or 0),
                "primitive_class": "row_family_projection",
                "preferred_primitive": "project_row_families",
                "binding": str(effective_row.get("binding") or "").strip(),
            }
        )

    return (
        violations,
        [],
        primitive_adoption_rows,
        row_family_projection_assignment_rows,
    )


def scan_root_validator_shared_primitive_adoption(repo_root: Path) -> dict[str, Any]:
    validator_paths = root_validator_paths(repo_root)
    violations: list[dict[str, Any]] = []
    scan_errors: list[dict[str, Any]] = []
    primitive_adoption_rows: list[dict[str, Any]] = []
    row_family_projection_assignment_rows: list[dict[str, Any]] = []
    for path in validator_paths:
        (
            file_violations,
            file_errors,
            file_primitive_adoption_rows,
            file_row_family_projection_assignment_rows,
        ) = _scan_root_validator_file(repo_root, path)
        violations.extend(file_violations)
        scan_errors.extend(file_errors)
        primitive_adoption_rows.extend(file_primitive_adoption_rows)
        row_family_projection_assignment_rows.extend(
            file_row_family_projection_assignment_rows
        )

    primitive_class_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for row in violations:
        primitive_class = str(row.get("primitive_class") or "").strip() or "unknown"
        primitive_class_counts[primitive_class] = (
            primitive_class_counts.get(primitive_class, 0) + 1
        )
        reason = str(row.get("reason") or "").strip() or "unknown"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    adoption_class_counts: dict[str, int] = {}
    for row in primitive_adoption_rows:
        primitive_class = str(row.get("primitive_class") or "").strip() or "unknown"
        adoption_class_counts[primitive_class] = (
            adoption_class_counts.get(primitive_class, 0) + 1
        )

    row_family_projection_assignment_violation_rows = [
        row
        for row in row_family_projection_assignment_rows
        if bool(row.get("violation"))
    ]

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
        "primitive_adoption_rows": primitive_adoption_rows,
        "primitive_adoption_row_count": len(primitive_adoption_rows),
        "primitive_adoption_file_count": len(
            {
                str(row.get("rel_path") or "")
                for row in primitive_adoption_rows
                if str(row.get("rel_path") or "").strip()
            }
        ),
        "primitive_adoption_class_counts": adoption_class_counts,
        "row_family_projection_assignment_rows": row_family_projection_assignment_rows,
        "row_family_projection_assignment_count": len(
            row_family_projection_assignment_rows
        ),
        "row_family_projection_assignment_violation_rows": (
            row_family_projection_assignment_violation_rows
        ),
        "row_family_projection_assignment_violation_count": len(
            row_family_projection_assignment_violation_rows
        ),
    }
