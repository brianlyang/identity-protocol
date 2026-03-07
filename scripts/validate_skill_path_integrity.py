#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_PATH_MISSING = "IP-SPATH-001"
ERR_PATH_OUT_OF_LAYOUT = "IP-SPATH-002"
ERR_OVERRIDE_FORMAT = "IP-SPATH-003"
ERR_SKILL_DECLARATION_MISSING = "IP-SPATH-004"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

CONTRACT_KEYS = (
    "skill_path_integrity_contract_v1",
    "skill_path_integrity_contract",
    "rq_020_skill_path_integrity_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _nonempty(value: Any) -> str:
    return str(value or "").strip()


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        token = _nonempty(raw)
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _detect_layout_mode(catalog_path: Path) -> str:
    p = catalog_path.resolve().as_posix()
    if "/.codex/.identity/" in p:
        return "global_codex"
    if "/.identity/" in p:
        return "project_local"
    if "/.agents/identity/" in p or "/.codex/identity/" in p:
        return "legacy_compat"
    return "custom"


def _find_parent_marker(path: Path, marker: str) -> Path | None:
    for parent in [path.resolve(), *path.resolve().parents]:
        if parent.name == marker:
            return parent
    return None


def _default_repo_root(*, catalog_path: Path, pack_path: Path) -> Path:
    marker = _find_parent_marker(catalog_path, ".agents")
    if marker is not None:
        return marker.parent.resolve()
    marker = _find_parent_marker(pack_path, ".agents")
    if marker is not None:
        return marker.parent.resolve()
    cwd = Path.cwd().resolve()
    if cwd.name == "identity-protocol-local":
        return cwd.parent.resolve()
    return cwd


def _default_runtime_root() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
    return codex_home


def _collect_contract_skills(contract: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in ("required_skills", "skills", "skill_ids"):
        rows = contract.get(key)
        if not isinstance(rows, list):
            continue
        for item in rows:
            token = _nonempty(item)
            if token:
                out.append(token)
    return _dedupe_keep_order(out)


def _collect_capability_skills(task: dict[str, Any]) -> list[str]:
    out: list[str] = []
    cap = task.get("capability_orchestration_contract")
    if not isinstance(cap, dict):
        return out
    routes = cap.get("task_type_routes")
    if not isinstance(routes, dict):
        return out
    for route in routes.values():
        if not isinstance(route, dict):
            continue
        for key in ("primary_skills", "fallback_skills"):
            rows = route.get(key)
            if not isinstance(rows, list):
                continue
            for item in rows:
                token = _nonempty(item)
                if token:
                    out.append(token)
    return _dedupe_keep_order(out)


def _expand_allowed_root_templates(
    *,
    templates: list[str],
    active_repo_root: Path,
    active_runtime_root: Path,
) -> list[Path]:
    rows: list[Path] = []
    for raw in templates:
        token = _nonempty(raw)
        if not token:
            continue
        rendered = token.replace("{active_repo_root}", str(active_repo_root)).replace(
            "{active_runtime_root}",
            str(active_runtime_root),
        )
        rows.append(Path(rendered).expanduser().resolve())
    return rows


def _build_allowed_skill_roots(
    *,
    active_repo_root: Path,
    active_runtime_root: Path,
    contract: dict[str, Any],
) -> list[Path]:
    rows = [
        (active_repo_root / "skills").resolve(),
        (active_repo_root / ".codex" / "skills").resolve(),
        (active_repo_root / "identity-protocol-local" / "skills").resolve(),
        (active_runtime_root / "skills").resolve(),
    ]
    extra_templates = contract.get("allowed_skill_roots")
    if isinstance(extra_templates, list):
        rows.extend(
            _expand_allowed_root_templates(
                templates=[str(x) for x in extra_templates],
                active_repo_root=active_repo_root,
                active_runtime_root=active_runtime_root,
            )
        )
    dedup: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        key = row.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def _relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _inside_layout(path: Path, roots: list[Path]) -> bool:
    return any(_relative_to(path, root) for root in roots)


def _candidate_skill_paths(skill: str, roots: list[Path]) -> list[Path]:
    names = [skill]
    if skill.startswith("identity-"):
        names.append(skill.replace("identity-", "skill-", 1))
    rows: list[Path] = []
    for root in roots:
        for name in names:
            rows.append((root / name / "SKILL.md").resolve())
            rows.append((root / ".system" / name / "SKILL.md").resolve())
    dedup: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        key = row.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return dedup


def _resolve_skill_path(*, skill: str, roots: list[Path], explicit_path: Path | None) -> tuple[Path | None, str]:
    if explicit_path is not None:
        return explicit_path.resolve(), "explicit_override"
    for cand in _candidate_skill_paths(skill, roots):
        if cand.exists() and cand.is_file():
            source = "repo_or_runtime_layout"
            return cand.resolve(), source
    return None, "not_found"


def _parse_skill_path_overrides(raw_rows: list[str]) -> tuple[dict[str, Path], list[str]]:
    mapping: dict[str, Path] = {}
    bad_rows: list[str] = []
    for raw in raw_rows:
        token = _nonempty(raw)
        if not token:
            continue
        if "=" not in token:
            bad_rows.append(token)
            continue
        skill, path_raw = token.split("=", 1)
        skill_id = _nonempty(skill)
        path_token = _nonempty(path_raw)
        if not skill_id or not path_token:
            bad_rows.append(token)
            continue
        mapping[skill_id] = Path(path_token).expanduser().resolve()
    return mapping, bad_rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate skill path integrity under active repo/runtime layout (RQ-020).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--skill-name", action="append", default=[])
    ap.add_argument(
        "--skill-path",
        action="append",
        default=[],
        help="explicit mapping skill=ABS_OR_REL_PATH_TO_SKILL_MD",
    )
    ap.add_argument("--active-repo-root", default="")
    ap.add_argument("--active-runtime-root", default="")
    ap.add_argument(
        "--layout-mode",
        choices=["auto", "project_local", "global_codex", "legacy_compat", "custom"],
        default="auto",
    )
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

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False
    auto_required = any(
        _nonempty(v)
        for v in (
            args.skill_name,
            args.skill_path,
            args.active_repo_root,
            args.active_runtime_root,
        )
    )
    if auto_required and args.operation in STRICT_OPERATIONS:
        required = True

    layout_mode = str(args.layout_mode)
    if layout_mode == "auto":
        layout_mode = _detect_layout_mode(catalog_path)

    active_repo_root = (
        Path(args.active_repo_root).expanduser().resolve()
        if _nonempty(args.active_repo_root)
        else _default_repo_root(catalog_path=catalog_path, pack_path=pack_path)
    )
    active_runtime_root = (
        Path(args.active_runtime_root).expanduser().resolve()
        if _nonempty(args.active_runtime_root)
        else _default_runtime_root()
    )

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required,
        "layout_mode": layout_mode,
        "active_repo_root": str(active_repo_root),
        "active_runtime_root": str(active_runtime_root),
        "allowed_skill_roots": [],
        "required_skills": [],
        "path_integrity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "path_integrity_error_code": "",
        "error_code": "",
        "skill_path_rows": [],
        "missing_skill_paths": [],
        "out_of_layout_skill_paths": [],
        "invalid_skill_path_overrides": [],
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    allowed_roots = _build_allowed_skill_roots(
        active_repo_root=active_repo_root,
        active_runtime_root=active_runtime_root,
        contract=contract if isinstance(contract, dict) else {},
    )
    payload["allowed_skill_roots"] = [str(x) for x in allowed_roots]

    if not required and not auto_required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract_skills = _collect_contract_skills(contract if isinstance(contract, dict) else {})
    capability_skills = _collect_capability_skills(task)
    cli_skills = _dedupe_keep_order([str(x) for x in (args.skill_name or []) if _nonempty(x)])
    declared_skills = _dedupe_keep_order(contract_skills + capability_skills + cli_skills)
    payload["required_skills"] = declared_skills

    override_map, bad_override_rows = _parse_skill_path_overrides([str(x) for x in (args.skill_path or [])])
    payload["invalid_skill_path_overrides"] = bad_override_rows

    if bad_override_rows:
        payload["path_integrity_status"] = STATUS_FAIL_REQUIRED
        payload["path_integrity_error_code"] = ERR_OVERRIDE_FORMAT
        payload["error_code"] = ERR_OVERRIDE_FORMAT
        payload["stale_reasons"] = ["invalid_skill_path_override_format"]
        _emit(payload, json_only=args.json_only)
        return 1

    for skill in override_map.keys():
        if skill not in declared_skills:
            declared_skills.append(skill)
    payload["required_skills"] = declared_skills

    if not declared_skills:
        payload["path_integrity_status"] = STATUS_FAIL_REQUIRED
        payload["path_integrity_error_code"] = ERR_SKILL_DECLARATION_MISSING
        payload["error_code"] = ERR_SKILL_DECLARATION_MISSING
        payload["stale_reasons"] = ["required_skill_declarations_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    missing: list[str] = []
    outside: list[str] = []
    rows: list[dict[str, Any]] = []
    for skill in declared_skills:
        explicit_path = override_map.get(skill)
        resolved_path, source = _resolve_skill_path(
            skill=skill,
            roots=allowed_roots,
            explicit_path=explicit_path,
        )
        path_exists = bool(resolved_path and resolved_path.exists() and resolved_path.is_file())
        inside = bool(path_exists and resolved_path and _inside_layout(resolved_path, allowed_roots))
        row = {
            "skill": skill,
            "path": str(resolved_path) if resolved_path else "",
            "path_exists": path_exists,
            "path_within_active_layout": inside,
            "path_source": source,
        }
        rows.append(row)
        if not path_exists:
            missing.append(skill)
        elif not inside:
            outside.append(skill)

    payload["skill_path_rows"] = rows
    payload["missing_skill_paths"] = missing
    payload["out_of_layout_skill_paths"] = outside

    stale_reasons: list[str] = []
    error_code = ""
    if missing:
        stale_reasons.append("skill_path_missing")
        error_code = ERR_PATH_MISSING
    if outside:
        stale_reasons.append("skill_path_out_of_active_layout")
        if not error_code:
            error_code = ERR_PATH_OUT_OF_LAYOUT

    if stale_reasons:
        payload["path_integrity_status"] = STATUS_FAIL_REQUIRED
        payload["path_integrity_error_code"] = error_code
        payload["error_code"] = error_code
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["path_integrity_status"] = STATUS_PASS_REQUIRED
    payload["path_integrity_error_code"] = ""
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
