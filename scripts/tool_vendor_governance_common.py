#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

import yaml


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
    _push((pack_resolved / "runtime").resolve())
    # Cross-repo custom catalog support:
    # identity pack often lives at <project>/.agents/identity/<id>, while reports are in <project>/resource/reports.
    for parent in [pack_resolved, *pack_resolved.parents]:
        candidate = (parent / "resource" / "reports").resolve()
        _push(candidate)
        if candidate.exists():
            # Keep scan bounded once we hit the nearest project reports root.
            break
    return roots


def latest_identity_upgrade_report(identity_id: str, pack_root: Path) -> Path | None:
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
            if p.is_file() and not p.name.endswith("-patch-plan.json")
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
