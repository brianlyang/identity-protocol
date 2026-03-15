#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

import validate_control_plane_budget as budget_mod


DEFAULT_BUDGET_ENTRY = "identity/protocol/mappings/control-plane-budget.current.yaml"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_int(value: Any) -> int | None:
    try:
        text = str(value).strip()
        if text == "":
            return None
        return int(text)
    except Exception:
        return None


def _delta_from_existing(existing: Any, *, fallback: int) -> int:
    if isinstance(existing, dict):
        warn = _as_int(existing.get("warn"))
        fail = _as_int(existing.get("fail"))
        if warn is not None and fail is not None and fail > warn:
            return max(1, fail - warn)
    scalar = _as_int(existing)
    if scalar is not None and scalar > 0:
        return max(1, scalar)
    return max(1, fallback)


def _threshold_pair(existing: Any, observed: int, *, fallback_delta: int) -> dict[str, int]:
    delta = _delta_from_existing(existing, fallback=fallback_delta)
    warn = max(0, int(observed))
    fail = warn + delta
    return {"warn": warn, "fail": fail}


def _collect_observed(repo_root: Path) -> dict[str, Any]:
    codes, families = budget_mod._collect_error_codes(repo_root)
    missing_cnt, _missing_rows, _bundle_rows = budget_mod._mapping_bundle_gap(repo_root)
    return {
        "validator_scripts": budget_mod._count_validator_scripts(repo_root),
        "error_codes": len(codes),
        "error_code_families": len(families),
        "mapping_rows_missing_in_bundle": missing_cnt,
        "strict_direct_validate_calls": budget_mod._strict_direct_validate_calls(repo_root),
    }


def _build_next_budget(*, current_doc: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    next_doc = dict(current_doc)
    next_doc["last_updated_utc"] = _utc_now()

    budgets = dict(next_doc.get("budgets") or {})

    budgets["validator_scripts"] = _threshold_pair(
        budgets.get("validator_scripts"), int(observed["validator_scripts"]), fallback_delta=3
    )
    budgets["error_codes"] = _threshold_pair(
        budgets.get("error_codes"), int(observed["error_codes"]), fallback_delta=6
    )
    budgets["error_code_families"] = _threshold_pair(
        budgets.get("error_code_families"), int(observed["error_code_families"]), fallback_delta=6
    )
    budgets["mapping_rows_missing_in_bundle"] = _threshold_pair(
        budgets.get("mapping_rows_missing_in_bundle"), int(observed["mapping_rows_missing_in_bundle"]), fallback_delta=1
    )

    existing_direct = budgets.get("direct_validate_calls") or {}
    next_direct: dict[str, dict[str, int]] = {}
    observed_direct = observed.get("strict_direct_validate_calls") or {}
    for surface in budget_mod.STRICT_SURFACES:
        current_hits = int(observed_direct.get(surface, -1))
        baseline = existing_direct.get(surface)
        if current_hits < 0:
            # keep existing configuration for missing surfaces to avoid destructive rewrites.
            if isinstance(baseline, dict):
                next_direct[surface] = {
                    "warn": int(baseline.get("warn", 0)),
                    "fail": int(baseline.get("fail", 1)),
                }
            continue
        next_direct[surface] = _threshold_pair(baseline, current_hits, fallback_delta=5)
    budgets["direct_validate_calls"] = next_direct
    next_doc["budgets"] = budgets

    convergence_guard = dict(next_doc.get("convergence_guard") or {})
    ceilings = dict(convergence_guard.get("ceilings") or {})
    ceilings["validator_scripts"] = int(observed["validator_scripts"])
    ceilings["error_codes"] = int(observed["error_codes"])
    ceilings["error_code_families"] = int(observed["error_code_families"])
    ceilings["mapping_rows_missing_in_bundle"] = int(observed["mapping_rows_missing_in_bundle"])
    ceilings["direct_validate_calls"] = {
        surface: int(count)
        for surface, count in (observed_direct.items() if isinstance(observed_direct, dict) else [])
        if int(count) >= 0
    }
    convergence_guard["enabled"] = bool(convergence_guard.get("enabled", True))
    convergence_guard["mode"] = str(convergence_guard.get("mode") or "no_rebound")
    convergence_guard["enforce_mode"] = str(convergence_guard.get("enforce_mode") or "fail_required")
    convergence_guard["baseline_snapshot_utc"] = _utc_now()
    convergence_guard["ceilings"] = ceilings
    next_doc["convergence_guard"] = convergence_guard

    return next_doc


def main() -> int:
    ap = argparse.ArgumentParser(description="Render/sync control-plane budget from live observed metrics.")
    ap.add_argument(
        "--budget-file",
        default=DEFAULT_BUDGET_ENTRY,
        help="Budget current-pointer yaml (default: identity/protocol/mappings/control-plane-budget.current.yaml)",
    )
    ap.add_argument("--write", action="store_true", help="Persist updates to resolved active budget file")
    ap.add_argument("--json-only", action="store_true", help="Emit single-line JSON payload")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    budget_path, active_file, alias_error = budget_mod._resolve_current_yaml_alias(repo_root, args.budget_file)

    payload: dict[str, Any] = {
        "render_control_plane_budget_status": "PASS_REQUIRED",
        "error_code": "",
        "budget_entry_file": str((repo_root / args.budget_file).resolve()),
        "budget_file": str(budget_path),
        "budget_file_active_file": active_file,
        "budget_file_alias_error": alias_error,
        "write_applied": False,
        "observed": {},
        "before": {},
        "after": {},
        "stale_reasons": [],
    }

    if alias_error:
        payload["render_control_plane_budget_status"] = "FAIL_REQUIRED"
        payload["error_code"] = "IP-CP-BUDGET-001"
        payload["stale_reasons"].append(f"budget_alias_error:{alias_error}")
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if not budget_path.exists() or not budget_path.is_file():
        payload["render_control_plane_budget_status"] = "FAIL_REQUIRED"
        payload["error_code"] = "IP-CP-BUDGET-001"
        payload["stale_reasons"].append("budget_file_missing")
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    current_doc = yaml.safe_load(budget_path.read_text(encoding="utf-8")) or {}
    if not isinstance(current_doc, dict):
        current_doc = {}

    observed = _collect_observed(repo_root)
    next_doc = _build_next_budget(current_doc=current_doc, observed=observed)

    payload["observed"] = observed
    payload["before"] = {
        "last_updated_utc": current_doc.get("last_updated_utc", ""),
        "budgets": current_doc.get("budgets", {}),
        "convergence_guard": current_doc.get("convergence_guard", {}),
    }
    payload["after"] = {
        "last_updated_utc": next_doc.get("last_updated_utc", ""),
        "budgets": next_doc.get("budgets", {}),
        "convergence_guard": next_doc.get("convergence_guard", {}),
    }

    if args.write:
        budget_path.write_text(yaml.safe_dump(next_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        payload["write_applied"] = True

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
