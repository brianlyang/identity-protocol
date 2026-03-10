#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_BUDGET = "IP-CP-BUDGET-001"

STRICT_SURFACES: tuple[str, ...] = (
    "scripts/identity_creator.py",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/e2e_smoke_test.sh",
    ".github/workflows/_identity-required-gates.yml",
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _count_validator_scripts(repo_root: Path) -> int:
    return len(list((repo_root / "scripts").glob("validate_*.py")))


def _normalize_error_code_family(code: str) -> str:
    value = str(code or "").strip()
    if not value:
        return ""
    return re.sub(r"-\d+$", "", value)


def _collect_error_codes(repo_root: Path) -> tuple[set[str], set[str]]:
    codes: set[str] = set()
    families: set[str] = set()
    for path in (repo_root / "scripts").glob("*.py"):
        text = _read_text(path)
        for code in re.findall(r"IP-[A-Z0-9\\-]+", text):
            if code:
                codes.add(code)
                family = _normalize_error_code_family(code)
                if family:
                    families.add(family)
    return codes, families


def _resolve_contract_mapping(repo_root: Path) -> Path:
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    current_file = mapping_dir / "contract-binding.current.yaml"
    if current_file.exists():
        try:
            doc = yaml.safe_load(current_file.read_text(encoding="utf-8")) or {}
        except Exception:
            doc = {}
        if isinstance(doc, dict):
            active_file = str(doc.get("active_file", "")).strip()
            if active_file:
                active_path = (repo_root / active_file).resolve()
                if active_path.exists():
                    return active_path
        return current_file
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    return mapping_dir / "contract-binding.yaml"


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _mapping_bundle_gap(repo_root: Path) -> tuple[int, list[str], int]:
    mapping_path = _resolve_contract_mapping(repo_root)
    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    mapping_rows = sorted(k for k in data.keys() if isinstance(k, str) and k.startswith("asb16-rq-"))

    from required_gate_bundle_runner import BUNDLE_REQUIREMENT_ORDER  # local import to avoid boot issues

    bundle_rows = list(BUNDLE_REQUIREMENT_ORDER)
    missing_rows = sorted(k for k in mapping_rows if k not in bundle_rows)
    return len(missing_rows), missing_rows, len(bundle_rows)


def _strict_direct_validate_calls(repo_root: Path) -> dict[str, int]:
    py_re = re.compile(r'"python3"\s*,\s*"scripts/validate_[\w\-.]+\.py"')
    sh_re = re.compile(r"python3\s+scripts/validate_[\w\-.]+\.py")
    out: dict[str, int] = {}
    for rel in STRICT_SURFACES:
        path = repo_root / rel
        if not path.exists():
            out[rel] = -1
            continue
        text = _read_text(path)
        if rel.endswith(".py"):
            hits = set(m.group(0) for m in py_re.finditer(text))
        else:
            hits = set(m.group(0) for m in sh_re.finditer(text))
        out[rel] = len(hits)
    return out


def _load_budget_doc(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _parse_threshold(value: Any) -> tuple[int | None, int | None]:
    # Backward-compatible parser:
    # 1) scalar int => fail only
    # 2) dict {warn, fail} => dual threshold
    if isinstance(value, dict):
        warn = value.get("warn")
        fail = value.get("fail")
        warn_i = int(warn) if str(warn).strip() != "" else None
        fail_i = int(fail) if str(fail).strip() != "" else None
        return warn_i, fail_i
    if value is None or str(value).strip() == "":
        return None, None
    return None, int(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-close control-plane growth budget and drift envelope.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--budget-file",
        default="identity/protocol/mappings/control-plane-budget.current.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    budget_entry_path = (repo_root / str(args.budget_file)).resolve()
    budget_path, budget_active_file, budget_alias_error = _resolve_current_yaml_alias(
        repo_root, str(args.budget_file)
    )
    if not budget_entry_path.exists():
        payload = {
            "control_plane_budget_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_BUDGET,
            "budget_file_entry": str(budget_entry_path),
            "budget_file": str(budget_path),
            "budget_file_active_file": budget_active_file,
            "budget_file_alias_error": budget_alias_error,
            "stale_reasons": [f"budget_file_entry_missing:{budget_entry_path}"],
        }
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if budget_alias_error:
        payload = {
            "control_plane_budget_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_BUDGET,
            "budget_file_entry": str(budget_entry_path),
            "budget_file": str(budget_path),
            "budget_file_active_file": budget_active_file,
            "budget_file_alias_error": budget_alias_error,
            "stale_reasons": [f"budget_file_alias_error:{budget_alias_error}:{budget_active_file}"],
        }
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if not budget_path.exists():
        payload = {
            "control_plane_budget_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_BUDGET,
            "budget_file_entry": str(budget_entry_path),
            "budget_file": str(budget_path),
            "budget_file_active_file": budget_active_file,
            "budget_file_alias_error": budget_alias_error,
            "stale_reasons": [f"budget_file_missing:{budget_path}"],
        }
        print(json.dumps(payload, ensure_ascii=False) if args.json_only else json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    budget_doc = _load_budget_doc(budget_path)
    budgets = budget_doc.get("budgets") or {}
    if not isinstance(budgets, dict):
        budgets = {}
    convergence_guard = budget_doc.get("convergence_guard") or {}
    if not isinstance(convergence_guard, dict):
        convergence_guard = {}
    observed_validator_scripts = _count_validator_scripts(repo_root)
    observed_error_codes_raw_set, observed_error_code_families_set = _collect_error_codes(repo_root)
    observed_error_codes = len(observed_error_codes_raw_set)
    observed_error_code_families = len(observed_error_code_families_set)
    missing_mapping_rows_count, missing_mapping_rows, observed_bundle_rows = _mapping_bundle_gap(repo_root)
    observed_direct_validate_calls = _strict_direct_validate_calls(repo_root)

    warn_violations: list[dict[str, Any]] = []
    fail_violations: list[dict[str, Any]] = []

    v_warn, v_fail = _parse_threshold(budgets.get("validator_scripts"))
    if v_warn is not None and observed_validator_scripts > v_warn:
        warn_violations.append(
            {
                "field": "validator_scripts",
                "observed": observed_validator_scripts,
                "budget_warn": v_warn,
                "reason": "validator_script_count_warn",
            }
        )
    if v_fail is not None and observed_validator_scripts > v_fail:
        fail_violations.append(
            {
                "field": "validator_scripts",
                "observed": observed_validator_scripts,
                "budget_fail": v_fail,
                "reason": "validator_script_count_exceeded",
            }
        )

    e_warn, e_fail = _parse_threshold(budgets.get("error_codes"))
    if e_warn is not None and observed_error_codes > e_warn:
        warn_violations.append(
            {
                "field": "error_codes",
                "observed": observed_error_codes,
                "budget_warn": e_warn,
                "reason": "error_code_count_warn",
            }
        )
    if e_fail is not None and observed_error_codes > e_fail:
        fail_violations.append(
            {
                "field": "error_codes",
                "observed": observed_error_codes,
                "budget_fail": e_fail,
                "reason": "error_code_count_exceeded",
            }
        )

    ef_warn, ef_fail = _parse_threshold(budgets.get("error_code_families"))
    if ef_warn is not None and observed_error_code_families > ef_warn:
        warn_violations.append(
            {
                "field": "error_code_families",
                "observed": observed_error_code_families,
                "budget_warn": ef_warn,
                "reason": "error_code_family_count_warn",
            }
        )
    if ef_fail is not None and observed_error_code_families > ef_fail:
        fail_violations.append(
            {
                "field": "error_code_families",
                "observed": observed_error_code_families,
                "budget_fail": ef_fail,
                "reason": "error_code_family_count_exceeded",
            }
        )

    m_warn, m_fail = _parse_threshold(budgets.get("mapping_rows_missing_in_bundle"))
    if m_warn is not None and missing_mapping_rows_count > m_warn:
        warn_violations.append(
            {
                "field": "mapping_rows_missing_in_bundle",
                "observed": missing_mapping_rows_count,
                "budget_warn": m_warn,
                "reason": "bundle_coverage_gap_warn",
                "missing_rows": missing_mapping_rows,
            }
        )
    if m_fail is not None and missing_mapping_rows_count > m_fail:
        fail_violations.append(
            {
                "field": "mapping_rows_missing_in_bundle",
                "observed": missing_mapping_rows_count,
                "budget_fail": m_fail,
                "reason": "bundle_coverage_gap_growth",
                "missing_rows": missing_mapping_rows,
            }
        )

    direct_budget = budgets.get("direct_validate_calls") or {}
    if isinstance(direct_budget, dict):
        for rel, limits in direct_budget.items():
            observed = int(observed_direct_validate_calls.get(rel, -1))
            if observed < 0:
                fail_violations.append(
                    {
                        "field": "strict_surface_missing",
                        "surface": rel,
                        "reason": "strict_surface_not_found",
                    }
                )
                continue
            warn_limit, fail_limit = _parse_threshold(limits)
            if warn_limit is not None and observed > warn_limit:
                warn_violations.append(
                    {
                        "field": "strict_direct_validate_calls",
                        "surface": rel,
                        "observed": observed,
                        "budget_warn": warn_limit,
                        "reason": "strict_surface_direct_calls_warn",
                    }
                )
            if fail_limit is not None and observed > fail_limit:
                fail_violations.append(
                    {
                        "field": "strict_direct_validate_calls",
                        "surface": rel,
                        "observed": observed,
                        "budget_fail": fail_limit,
                        "reason": "strict_surface_direct_calls_growth",
                    }
                )

    convergence_enabled = bool(convergence_guard.get("enabled", False))
    convergence_mode = str(convergence_guard.get("mode", "")).strip() or "disabled"
    convergence_enforce_mode = str(convergence_guard.get("enforce_mode", "")).strip() or "fail_required"
    convergence_ceilings = convergence_guard.get("ceilings") or {}
    if not isinstance(convergence_ceilings, dict):
        convergence_ceilings = {}
    convergence_violations: list[dict[str, Any]] = []
    if convergence_enabled and convergence_mode == "no_rebound":
        metric_map: dict[str, int] = {
            "validator_scripts": observed_validator_scripts,
            "error_codes": observed_error_codes,
            "error_code_families": observed_error_code_families,
            "mapping_rows_missing_in_bundle": missing_mapping_rows_count,
        }
        for key, observed in metric_map.items():
            ceiling_value = convergence_ceilings.get(key)
            if ceiling_value is None or str(ceiling_value).strip() == "":
                continue
            try:
                ceiling_int = int(ceiling_value)
            except Exception:
                fail_violations.append(
                    {
                        "field": key,
                        "reason": "convergence_ceiling_parse_failed",
                        "ceiling": ceiling_value,
                    }
                )
                continue
            if observed > ceiling_int:
                convergence_violations.append(
                    {
                        "field": key,
                        "observed": observed,
                        "ceiling": ceiling_int,
                        "reason": "convergence_rebound_detected",
                    }
                )
        direct_ceilings = convergence_ceilings.get("direct_validate_calls") or {}
        if isinstance(direct_ceilings, dict):
            for rel, ceiling_value in direct_ceilings.items():
                observed = int(observed_direct_validate_calls.get(rel, -1))
                if observed < 0:
                    convergence_violations.append(
                        {
                            "field": "strict_direct_validate_calls",
                            "surface": rel,
                            "reason": "convergence_surface_missing",
                        }
                    )
                    continue
                try:
                    ceiling_int = int(ceiling_value)
                except Exception:
                    convergence_violations.append(
                        {
                            "field": "strict_direct_validate_calls",
                            "surface": rel,
                            "reason": "convergence_ceiling_parse_failed",
                            "ceiling": ceiling_value,
                        }
                    )
                    continue
                if observed > ceiling_int:
                    convergence_violations.append(
                        {
                            "field": "strict_direct_validate_calls",
                            "surface": rel,
                            "observed": observed,
                            "ceiling": ceiling_int,
                            "reason": "convergence_rebound_detected",
                        }
                    )

    if convergence_violations:
        if convergence_enforce_mode == "warn_non_blocking":
            warn_violations.extend(convergence_violations)
        else:
            fail_violations.extend(convergence_violations)

    if fail_violations:
        status = STATUS_FAIL_REQUIRED
    elif warn_violations:
        status = STATUS_WARN_NON_BLOCKING
    else:
        status = STATUS_PASS_REQUIRED
    payload = {
        "control_plane_budget_status": status,
        "error_code": "" if status in {STATUS_PASS_REQUIRED, STATUS_WARN_NON_BLOCKING} else ERR_BUDGET,
        "budget_file_entry": str(budget_entry_path),
        "budget_file": str(budget_path),
        "budget_file_active_file": budget_active_file,
        "budget_file_alias_error": budget_alias_error,
        "strict_surfaces": list(STRICT_SURFACES),
        "observed": {
            "validator_scripts": observed_validator_scripts,
            "error_codes": observed_error_codes,
            "error_code_families": observed_error_code_families,
            "mapping_rows_missing_in_bundle": missing_mapping_rows_count,
            "bundle_rows": observed_bundle_rows,
            "missing_mapping_rows": missing_mapping_rows,
            "strict_direct_validate_calls": observed_direct_validate_calls,
        },
        "budgets": budgets,
        "error_code_family_strategy": budget_doc.get("error_code_family_strategy") or {},
        "convergence_guard": {
            "enabled": convergence_enabled,
            "mode": convergence_mode,
            "enforce_mode": convergence_enforce_mode,
            "ceiling_count": len(convergence_ceilings),
            "violations": convergence_violations,
        },
        "warn_violation_count": len(warn_violations),
        "warn_violations": warn_violations,
        "fail_violation_count": len(fail_violations),
        "fail_violations": fail_violations,
        "stale_reasons": [v.get("reason", "") for v in (warn_violations + fail_violations)],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-BUDGET] status={status} "
            f"warn_violations={len(warn_violations)} "
            f"fail_violations={len(fail_violations)} "
            f"validator_scripts={observed_validator_scripts} "
            f"error_codes={observed_error_codes}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
