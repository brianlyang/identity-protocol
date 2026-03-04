#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

import yaml


DEFAULT_TOP3_THRESHOLDS = {
    "dialogue_constraint_coverage_rate": 95.0,
    "dialogue_traceability_rate": 95.0,
    "dialogue_change_reconciliation_rate": 95.0,
}

DEFAULT_TOP3_THRESHOLDS_PHASE1 = {
    "dialogue_constraint_coverage_rate": 95.0,
    "dialogue_traceability_rate": 95.0,
    "dialogue_change_reconciliation_rate": 90.0,
}

REDLINE_KEYS = ("hard_constraint_missing_artifact_count", "untraceable_final_claim_count")
DONE_BLOCKER_KEY = "unresolved_ambiguity_count"

TRACE_REQUIRED_FIELDS = (
    "user_turn_ref",
    "extracted_constraint_ref",
    "plan_step_ref",
    "artifact_ref",
    "final_claim_ref",
)

FINAL_CLAIM_REQUIRED_FIELDS = ("user_turn_ref", "artifact_ref")


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
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    pack = Path(pack_raw).expanduser().resolve()
    if not pack.exists():
        raise FileNotFoundError(f"pack_path not found: {pack}")
    task = pack / "CURRENT_TASK.json"
    if not task.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found: {task}")
    return pack, task


def resolve_dialogue_contract(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("dialogue_governance_contract") or {}
    return raw if isinstance(raw, dict) else {}


def contract_required(contract: dict[str, Any]) -> bool:
    return bool(contract.get("required", False))


def resolve_enforcement_mode(contract: dict[str, Any], override: str = "auto") -> str:
    o = str(override or "auto").strip().lower()
    if o in {"warn", "enforce"}:
        return o
    c = str(contract.get("rollout_mode", "")).strip().lower()
    if c in {"warn", "enforce"}:
        return c
    return "warn"


def resolve_report_path(
    *,
    identity_id: str,
    pack_path: Path,
    contract: dict[str, Any],
    report: str = "",
    report_dir: str = "",
    pattern_keys: tuple[str, ...] = ("report_path_pattern",),
) -> Path | None:
    if report.strip():
        p = Path(report.strip()).expanduser().resolve()
        return p if p.exists() else None

    candidates: list[Path] = []
    if report_dir.strip():
        d = Path(report_dir.strip()).expanduser().resolve()
        if d.exists():
            candidates.extend(sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime))

    for key in pattern_keys:
        pattern = str(contract.get(key, "")).strip()
        if not pattern:
            continue
        rendered = pattern.replace("<identity-id>", identity_id)
        hits = [Path(x).expanduser().resolve() for x in glob.glob(rendered, recursive=True)]
        candidates.extend(hits)

    runtime_report_dir = (pack_path / "runtime" / "reports").resolve()
    if runtime_report_dir.exists():
        candidates.extend(
            sorted(
                runtime_report_dir.glob(f"*{identity_id}*dialogue*.json"),
                key=lambda p: p.stat().st_mtime,
            )
        )

    # de-dup while keeping order; latest wins below.
    dedup: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        if not p.exists():
            continue
        s = str(p.resolve())
        if s in seen:
            continue
        seen.add(s)
        dedup.append(p.resolve())
    if not dedup:
        return None
    dedup.sort(key=lambda p: p.stat().st_mtime)
    return dedup[-1]


def _to_int(v: Any) -> int:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str) and v.strip():
        try:
            return int(float(v.strip()))
        except Exception:
            return 0
    return 0


def extract_counts(report: dict[str, Any]) -> dict[str, int]:
    raw = report.get("counts") if isinstance(report.get("counts"), dict) else {}
    return {
        "required_constraints": _to_int(raw.get("required_constraints")),
        "extracted_constraints": _to_int(raw.get("extracted_constraints")),
        "traceable_constraints": _to_int(raw.get("traceable_constraints")),
        "changed_constraints": _to_int(raw.get("changed_constraints")),
        "reconciled_constraints": _to_int(raw.get("reconciled_constraints")),
        "hard_constraint_missing_artifact_count": _to_int(raw.get("hard_constraint_missing_artifact_count")),
        "untraceable_final_claim_count": _to_int(raw.get("untraceable_final_claim_count")),
        "unresolved_ambiguity_count": _to_int(raw.get("unresolved_ambiguity_count")),
        "required_hard_constraints": _to_int(raw.get("required_hard_constraints")),
        "extracted_hard_constraints": _to_int(raw.get("extracted_hard_constraints")),
    }


def rate(part: int, whole: int) -> float:
    if whole <= 0:
        return 100.0
    return round((float(part) / float(whole)) * 100.0, 4)


def top3_thresholds(contract: dict[str, Any]) -> dict[str, float]:
    phase = str(contract.get("rollout_phase", "")).strip().lower()
    defaults = DEFAULT_TOP3_THRESHOLDS_PHASE1 if phase in {"phase1", "phase-1"} else DEFAULT_TOP3_THRESHOLDS
    raw = contract.get("top3_thresholds")
    if not isinstance(raw, dict):
        return dict(defaults)
    out = dict(defaults)
    for k in defaults.keys():
        v = raw.get(k)
        if isinstance(v, (int, float)):
            out[k] = float(v)
        elif isinstance(v, dict):
            min_v = v.get("min")
            if isinstance(min_v, (int, float)):
                out[k] = float(min_v)
    return out


def hard_subset_threshold(contract: dict[str, Any]) -> float:
    raw = contract.get("hard_subset_min")
    if isinstance(raw, (int, float)):
        return float(raw)
    raw2 = contract.get("top3_thresholds")
    if isinstance(raw2, dict):
        cfg = raw2.get("dialogue_constraint_coverage_rate")
        if isinstance(cfg, dict):
            v = cfg.get("hard_subset_min")
            if isinstance(v, (int, float)):
                return float(v)
    return 100.0


def redline_thresholds(contract: dict[str, Any]) -> dict[str, int]:
    default = {k: 0 for k in REDLINE_KEYS}
    raw = contract.get("redline_thresholds")
    if not isinstance(raw, dict):
        return default
    out = dict(default)
    for k in REDLINE_KEYS:
        v = raw.get(k)
        if isinstance(v, dict):
            max_v = v.get("max")
            if isinstance(max_v, (int, float)):
                out[k] = int(max_v)
        elif isinstance(v, (int, float)):
            out[k] = int(v)
    return out


def done_blocker_max(contract: dict[str, Any]) -> int:
    raw = contract.get("done_state_blocker")
    if isinstance(raw, dict):
        v = raw.get(DONE_BLOCKER_KEY)
        if isinstance(v, dict):
            mv = v.get("max")
            if isinstance(mv, (int, float)):
                return int(mv)
        if isinstance(v, (int, float)):
            return int(v)
    return 0


def has_nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return value is not None


def enforce_outcome(
    *,
    mode: str,
    failures: list[str],
    warnings: list[str] | None = None,
    summary: dict[str, Any] | None = None,
) -> int:
    warnings = warnings or []
    summary = summary or {}
    if failures and mode == "enforce":
        print("[FAIL] dialogue governance validation failed")
        for x in failures:
            print(f" - {x}")
        if warnings:
            print("[WARN] additional warnings:")
            for x in warnings:
                print(f" - {x}")
        if summary:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1
    if failures:
        print("[WARN] dialogue governance validation (warn mode) found issues")
        for x in failures:
            print(f" - {x}")
    for x in warnings:
        print(f"[WARN] {x}")
    if summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("[OK] dialogue governance validation passed")
    return 0

