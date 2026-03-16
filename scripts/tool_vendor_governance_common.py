#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

import yaml

ACTIVE_EXECUTION_POINTER_REL = Path("runtime/state/active_execution_report.json")


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
    hits: list[Path] = []
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = sorted(pack_root.glob(raw))
        if preferred:
            hits = [x.resolve() for x in preferred]
        else:
            hits = [x.resolve() for x in Path(".").glob(raw)]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def _candidate_upgrade_report_roots(pack_root: Path) -> list[Path]:
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


def _read_active_execution_report_pointer(pack_root: Path, identity_id: str) -> Path | None:
    pointer_path = (pack_root.resolve() / ACTIVE_EXECUTION_POINTER_REL).resolve()
    if not pointer_path.exists():
        return None
    try:
        pointer = load_json(pointer_path)
    except Exception:
        return None
    report_raw = str(pointer.get("report_path", "")).strip()
    run_id = str(pointer.get("run_id", "")).strip()
    if not report_raw:
        return None
    report_path = Path(report_raw).expanduser().resolve()
    if not report_path.exists() or not report_path.is_file():
        return None
    name = report_path.name
    if not name.startswith("identity-upgrade-exec-") or not name.endswith(".json"):
        return None
    if name.endswith("-patch-plan.json"):
        return None
    normalized = str(identity_id or "").strip()
    if normalized not in {"", "*"} and f"identity-upgrade-exec-{normalized}-" not in name:
        return None
    if run_id and run_id not in name:
        # Pointer stale / mismatched run id.
        return None
    return report_path


def latest_identity_upgrade_report(identity_id: str, pack_root: Path) -> Path | None:
    pointed = _read_active_execution_report_pointer(pack_root, identity_id)
    if pointed is not None:
        return pointed

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
