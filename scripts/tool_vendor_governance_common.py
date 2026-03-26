#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import glob
import json
from pathlib import Path
from typing import Any

import yaml

ACTIVE_EXECUTION_POINTER_REL = Path("runtime/state/active_execution_report.json")
TOOL_VENDOR_GOVERNANCE_REPORT_DIR_REL = Path("runtime/reports/tool-vendor-governance")

IDENTITY_UPGRADE_REPORT_SELECTION_MODE_ACTIVE_EXECUTION_POINTER = "active_execution_pointer"
IDENTITY_UPGRADE_REPORT_SELECTION_MODE_CANDIDATE_ROOT_LATEST = "candidate_root_latest_report"
IDENTITY_UPGRADE_REPORT_SELECTION_MODE_EXPLICIT_REPORT_OVERRIDE = "explicit_report_override"
IDENTITY_UPGRADE_REPORT_SELECTION_MODE_NONE = "no_admissible_report"

IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_ACTIVE_EXECUTION_POINTER = (
    "active_execution_pointer_pack_local_report"
)
IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_CANDIDATE_ROOT_LATEST = (
    "candidate_root_latest_pack_local_report"
)
IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_EXPLICIT_REPORT_OVERRIDE = "explicit_report_override"
IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_NONE = "no_selected_report"

IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE = (
    "explicit_report_override"
)
IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE_MISSING = (
    "explicit_report_override_missing"
)


@dataclass(frozen=True)
class LatestIdentityUpgradeReportResolution:
    selected_report: Path | None
    selection_mode: str
    selected_report_authority_class: str
    pointer_resolution_mode: str
    pointer_path: Path | None


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def resolve_pack_and_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    catalog = load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    pack = Path(pack_raw).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task_path = pack / "CURRENT_TASK.json"
    if not task_path.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task_path}")
    return pack, task_path


def _find_parent_marker(path: Path, marker: str) -> Path | None:
    resolved = path.expanduser().resolve()
    for parent in [resolved, *resolved.parents]:
        if parent.name == marker:
            return parent
    return None


def derive_active_repo_root(*, catalog_path: Path, pack_path: Path, cwd: Path | None = None) -> tuple[Path, str]:
    """
    Resolve active repo root deterministically from runtime context without hardcoded user paths.

    Resolution order (deterministic):
    1) project-local catalog marker (.identity)
    2) legacy project-local catalog marker (.agents)
    3) pack path markers (.identity / .agents)
    4) cwd identity-protocol-local parent
    5) cwd fallback
    """
    catalog_resolved = catalog_path.expanduser().resolve()
    pack_resolved = pack_path.expanduser().resolve()

    catalog_identity_marker = _find_parent_marker(catalog_resolved, ".identity")
    if catalog_identity_marker is not None:
        return catalog_identity_marker.parent.resolve(), "catalog_project_identity_home"

    catalog_agents_marker = _find_parent_marker(catalog_resolved, ".agents")
    if catalog_agents_marker is not None:
        return catalog_agents_marker.parent.resolve(), "catalog_agents_identity_home"

    pack_identity_marker = _find_parent_marker(pack_resolved, ".identity")
    if pack_identity_marker is not None:
        return pack_identity_marker.parent.resolve(), "pack_project_identity_home"

    pack_agents_marker = _find_parent_marker(pack_resolved, ".agents")
    if pack_agents_marker is not None:
        return pack_agents_marker.parent.resolve(), "pack_agents_identity_home"

    cwd_resolved = (cwd or Path.cwd()).expanduser().resolve()
    if cwd_resolved.name == "identity-protocol-local":
        return cwd_resolved.parent.resolve(), "cwd_identity_protocol_parent"
    return cwd_resolved, "cwd_fallback"


def resolve_report_path(
    *,
    report: str,
    pattern: str,
    pack_root: Path,
) -> Path | None:
    if report.strip():
        p = Path(report.strip()).expanduser().resolve()
        return p if p.exists() else None

    raw = str(pattern or "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])

    def _workspace_root_from_pack(root: Path) -> Path | None:
        for marker in (".identity", ".agents"):
            marker_path = _find_parent_marker(root, marker)
            if marker_path is not None:
                return marker_path.parent.resolve()
        return None

    def _dedupe_resolution_candidates(rows: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
        dedup: list[tuple[Path, str]] = []
        seen: set[tuple[str, str]] = set()
        for base_root, rel_pattern in rows:
            key = (base_root.expanduser().resolve().as_posix(), str(rel_pattern or "").strip())
            if not key[1] or key in seen:
                continue
            seen.add(key)
            dedup.append((base_root.expanduser().resolve(), key[1]))
        return dedup

    def _relative_resolution_candidates(root: Path, raw_pattern: str) -> list[tuple[Path, str]]:
        normalized = str(raw_pattern or "").strip().replace("\\", "/")
        workspace_root = _workspace_root_from_pack(root)
        candidates: list[tuple[Path, str]] = [(root.resolve(), normalized)]

        if normalized.startswith("identity/runtime/"):
            # `identity/runtime/**` is a pack-scoped namespace in CURRENT_TASK contracts.
            # It must resolve to `<pack>/runtime/**`, not drift into repo fixture/demo paths.
            candidates.append((root.resolve(), normalized[len("identity/") :]))
            return _dedupe_resolution_candidates(candidates)

        if normalized.startswith("runtime/"):
            return _dedupe_resolution_candidates(candidates)

        if normalized.startswith("resource/"):
            if workspace_root is not None:
                candidates.append((workspace_root, normalized))
            return _dedupe_resolution_candidates(candidates)

        if normalized.startswith("identity/"):
            candidates.append((root.resolve(), normalized[len("identity/") :]))

        if workspace_root is not None:
            candidates.append((workspace_root, normalized))

        candidates.append((Path.cwd().resolve(), normalized))
        return _dedupe_resolution_candidates(candidates)

    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
            if not hits:
                return None
            hits.sort(key=lambda x: x.stat().st_mtime)
            return hits[-1]
        if p.exists():
            return p.resolve()
        return None

    for base_root, rel_pattern in _relative_resolution_candidates(pack_root, raw):
        if has_magic:
            hits = [x.resolve() for x in base_root.glob(rel_pattern)]
            if not hits:
                continue
            hits.sort(key=lambda x: x.stat().st_mtime)
            return hits[-1]
        candidate = (base_root / rel_pattern).resolve()
        if candidate.exists():
            return candidate
    return None


def materialize_report_path(
    *,
    pattern: str,
    identity_id: str,
    pack_root: Path,
    timestamp_token: str | int,
) -> Path:
    raw = str(pattern or "").strip()
    if not raw:
        raise ValueError("report pattern missing")
    materialized = raw.replace("<identity-id>", str(identity_id or "").strip())
    if "*" in materialized:
        materialized = materialized.replace("*", str(timestamp_token))
    path = Path(materialized).expanduser()
    if path.is_absolute():
        return path.resolve()

    normalized = materialized.replace("\\", "/")
    pack_resolved = pack_root.expanduser().resolve()
    workspace_root = _workspace_root_from_pack(pack_resolved)

    if normalized.startswith("identity/runtime/"):
        return (pack_resolved / normalized[len("identity/") :]).resolve()
    if normalized.startswith("runtime/"):
        return (pack_resolved / normalized).resolve()
    if workspace_root is not None:
        return (workspace_root / normalized).resolve()
    return (pack_resolved / normalized).resolve()


def candidate_upgrade_report_roots(pack_root: Path) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()

    def _push(p: Path) -> None:
        key = p.as_posix()
        if key in seen:
            return
        seen.add(key)
        roots.append(p)

    pack_resolved = pack_root.resolve()
    _push((pack_resolved / "runtime" / "reports").resolve())
    # Cross-repo custom catalog support:
    # identity pack often lives at <project>/.identity/<id>, while reports are in <project>/resource/reports.
    for parent in [pack_resolved, *pack_resolved.parents]:
        candidate = (parent / "resource" / "reports").resolve()
        _push(candidate)
        if candidate.exists():
            # Keep scan bounded once we hit the nearest project reports root.
            break
    return roots


def _candidate_upgrade_report_roots(pack_root: Path) -> list[Path]:
    # Backward-compatible private alias for older call sites inside this module.
    return candidate_upgrade_report_roots(pack_root)


def _resolve_active_execution_report_pointer(
    pack_root: Path,
    identity_id: str,
) -> tuple[Path | None, str, Path | None]:
    pointer_path = (pack_root.resolve() / ACTIVE_EXECUTION_POINTER_REL).resolve()
    if not pointer_path.exists():
        return None, "pointer_missing", pointer_path
    try:
        pointer = load_json(pointer_path)
    except Exception:
        return None, "pointer_parse_failed", pointer_path
    report_raw = str(pointer.get("report_path", "")).strip()
    run_id = str(pointer.get("run_id", "")).strip()
    if not report_raw:
        return None, "pointer_report_path_missing", pointer_path
    report_path = Path(report_raw).expanduser()
    if not report_path.is_absolute():
        report_path = (pack_root.resolve() / report_path).resolve()
    else:
        report_path = report_path.resolve()
    if not report_path.exists() or not report_path.is_file():
        return None, "pointer_report_missing", pointer_path
    name = report_path.name
    if not name.startswith("identity-upgrade-exec-") or not name.endswith(".json"):
        return None, "pointer_report_name_invalid", pointer_path
    if name.endswith("-patch-plan.json"):
        return None, "pointer_report_name_invalid", pointer_path
    normalized = str(identity_id or "").strip()
    if normalized not in {"", "*"} and f"identity-upgrade-exec-{normalized}-" not in name:
        return None, "pointer_identity_mismatch", pointer_path
    if run_id and run_id not in name:
        # Pointer stale / mismatched run id.
        return None, "pointer_run_id_mismatch", pointer_path
    candidate_roots = _candidate_upgrade_report_roots(pack_root)
    if not any(path_within(report_path, root) for root in candidate_roots):
        # Runtime active-report pointers are pack-local authority hints. A copied
        # or relocated pack may inherit an absolute pointer that still targets
        # the source pack; reject that drift and fall back to local discovery
        # rather than mutating a foreign report through the cloned runtime.
        return None, "external_pointer_report_rejected", pointer_path
    return report_path, "pointer_candidate_root_report", pointer_path


def _read_active_execution_report_pointer(pack_root: Path, identity_id: str) -> Path | None:
    pointed_report, _resolution_mode, _pointer_path = _resolve_active_execution_report_pointer(
        pack_root,
        identity_id,
    )
    return pointed_report


def _discover_latest_identity_upgrade_report(identity_id: str, pack_root: Path) -> Path | None:
    rows: list[Path] = []
    normalized = str(identity_id or "").strip()
    if normalized in {"", "*"}:
        pattern = "**/identity-upgrade-exec-*.json"
    else:
        pattern = f"**/identity-upgrade-exec-{normalized}-*.json"
    for root in _candidate_upgrade_report_roots(pack_root):
        if not root.exists():
            continue
        rows.extend(
            p
            for p in root.glob(pattern)
            if p.is_file()
            and not p.name.endswith("-patch-plan.json")
            and "/runtime/protocol-feedback/" not in p.as_posix()
            and "/archive/" not in p.as_posix()
            and "/archives/" not in p.as_posix()
        )
    if not rows:
        return None
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows[-1]


def resolve_latest_identity_upgrade_report(
    identity_id: str,
    pack_root: Path,
) -> LatestIdentityUpgradeReportResolution:
    pointed, pointer_resolution_mode, pointer_path = _resolve_active_execution_report_pointer(
        pack_root,
        identity_id,
    )
    if pointed is not None:
        return LatestIdentityUpgradeReportResolution(
            selected_report=pointed,
            selection_mode=IDENTITY_UPGRADE_REPORT_SELECTION_MODE_ACTIVE_EXECUTION_POINTER,
            selected_report_authority_class=(
                IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_ACTIVE_EXECUTION_POINTER
            ),
            pointer_resolution_mode=pointer_resolution_mode,
            pointer_path=pointer_path,
        )

    fallback_report = _discover_latest_identity_upgrade_report(identity_id, pack_root)
    if fallback_report is not None:
        return LatestIdentityUpgradeReportResolution(
            selected_report=fallback_report,
            selection_mode=IDENTITY_UPGRADE_REPORT_SELECTION_MODE_CANDIDATE_ROOT_LATEST,
            selected_report_authority_class=IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_CANDIDATE_ROOT_LATEST,
            pointer_resolution_mode=pointer_resolution_mode,
            pointer_path=pointer_path,
        )

    return LatestIdentityUpgradeReportResolution(
        selected_report=None,
        selection_mode=IDENTITY_UPGRADE_REPORT_SELECTION_MODE_NONE,
        selected_report_authority_class=IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_NONE,
        pointer_resolution_mode=pointer_resolution_mode,
        pointer_path=pointer_path,
    )


def resolve_identity_upgrade_report_selection(
    identity_id: str,
    pack_root: Path,
    *,
    explicit_report: str = "",
) -> LatestIdentityUpgradeReportResolution:
    explicit_token = str(explicit_report or "").strip()
    if explicit_token:
        explicit_path = Path(explicit_token).expanduser().resolve()
        if explicit_path.exists() and explicit_path.is_file():
            return LatestIdentityUpgradeReportResolution(
                selected_report=explicit_path,
                selection_mode=IDENTITY_UPGRADE_REPORT_SELECTION_MODE_EXPLICIT_REPORT_OVERRIDE,
                selected_report_authority_class=(
                    IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_EXPLICIT_REPORT_OVERRIDE
                ),
                pointer_resolution_mode=(
                    IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE
                ),
                pointer_path=None,
            )
        return LatestIdentityUpgradeReportResolution(
            selected_report=None,
            selection_mode=IDENTITY_UPGRADE_REPORT_SELECTION_MODE_EXPLICIT_REPORT_OVERRIDE,
            selected_report_authority_class=(
                IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_EXPLICIT_REPORT_OVERRIDE
            ),
            pointer_resolution_mode=(
                IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE_MISSING
            ),
            pointer_path=None,
        )
    return resolve_latest_identity_upgrade_report(identity_id, pack_root)


def build_identity_upgrade_report_selection_projection(
    resolution: LatestIdentityUpgradeReportResolution,
    *,
    field_prefix: str = "report",
) -> dict[str, Any]:
    prefix = str(field_prefix or "").strip() or "report"
    return {
        f"{prefix}_selected_path": (
            str(resolution.selected_report) if resolution.selected_report is not None else ""
        ),
        f"{prefix}_selection_mode": str(resolution.selection_mode or "").strip(),
        f"{prefix}_selected_authority_class": str(
            resolution.selected_report_authority_class or ""
        ).strip(),
        f"{prefix}_pointer_resolution_mode": str(resolution.pointer_resolution_mode or "").strip(),
        f"{prefix}_pointer_path": str(resolution.pointer_path) if resolution.pointer_path is not None else "",
    }


def latest_identity_upgrade_report(identity_id: str, pack_root: Path) -> Path | None:
    return resolve_latest_identity_upgrade_report(identity_id, pack_root).selected_report


def path_within(path: Path, root: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
        return True
    except Exception:
        return False


def dedupe_paths(rows: list[Path]) -> list[Path]:
    dedup: list[Path] = []
    seen: set[str] = set()
    for row in rows:
        token = row.expanduser().resolve()
        key = token.as_posix()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(token)
    return dedup


def select_skill_enforcement_roots(
    *,
    allowed_skill_roots: list[Path],
    active_repo_root: Path,
    active_runtime_root: Path,
    policy: str,
) -> list[Path]:
    normalized = str(policy or "").strip().lower() or "all_selected_paths"
    roots = dedupe_paths([root.expanduser().resolve() for root in allowed_skill_roots])
    if normalized == "all_selected_paths":
        return roots
    if normalized == "governed_selected_paths_only":
        return [root for root in roots if path_within(root, active_repo_root)]
    if normalized == "runtime_selected_paths_only":
        return [root for root in roots if path_within(root, active_runtime_root)]
    return roots


def root_family_for_path(path: Path, roots: list[Path]) -> Path | None:
    for root in dedupe_paths(list(roots)):
        if path_within(path, root):
            return root
    return None


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def contract_required(contract: dict[str, Any]) -> bool:
    return boolish(contract.get("required", False))
