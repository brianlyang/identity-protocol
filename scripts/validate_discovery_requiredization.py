#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import boolish, contract_required, load_json, resolve_pack_and_task, resolve_report_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_TRIGGER_NOT_APPLIED = "IP-DREQ-001"
ERR_RECEIPT_MISSING = "IP-DREQ-002"
ERR_RECEIPT_NOT_LINKED = "IP-DREQ-003"
ERR_CI_VALIDATOR_MISSING = "IP-DREQ-004"
ERR_NON_BLOCKING_EXPIRED = "IP-DREQ-005"

DISCOVERY_CONTRACT_KEYS = (
    "tool_installation_contract",
    "vendor_api_discovery_contract",
    "vendor_api_solution_contract",
)

DISCOVERY_VALIDATORS = {
    "tool_installation_contract": "scripts/validate_identity_tool_installation.py",
    "vendor_api_discovery_contract": "scripts/validate_identity_vendor_api_discovery.py",
    "vendor_api_solution_contract": "scripts/validate_identity_vendor_api_solution.py",
}

DISCOVERY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "tool_installation_contract": {
        "required": False,
        "report_path_pattern": "identity/runtime/reports/tool-installation-<identity-id>-*.json",
        "required_report_fields": [
            "tool_gap_detected",
            "tool_gap_summary_ref",
            "install_plan_ref",
            "approval_receipt_ref",
            "execution_log_ref",
            "installed_artifact_ref",
            "installed_version",
            "post_install_healthcheck_ref",
            "task_smoke_result_ref",
            "route_binding_update_ref",
            "fallback_route_if_install_fails",
            "rollback_ref",
        ],
        "enforcement_validator": "scripts/validate_identity_tool_installation.py",
    },
    "vendor_api_discovery_contract": {
        "required": False,
        "report_path_pattern": "identity/runtime/reports/vendor-api-discovery-<identity-id>-*.json",
        "required_report_fields": [
            "vendor_name",
            "vendor_surface_name",
            "official_reference_url",
            "machine_readable_contract_ref",
            "contract_kind",
            "auth_discovery_ref",
            "versioning_policy_ref",
            "rate_limit_policy_ref",
            "capability_probe_command_ref",
            "attach_readiness_decision",
            "fallback_vendor_or_route_ref",
        ],
        "enforcement_validator": "scripts/validate_identity_vendor_api_discovery.py",
    },
    "vendor_api_solution_contract": {
        "required": False,
        "report_path_pattern": "identity/runtime/reports/vendor-api-solution-<identity-id>-*.json",
        "required_report_fields": [
            "problem_statement_ref",
            "selected_vendor_api_ref",
            "solution_pattern",
            "decision_rationale_ref",
            "option_comparison_ref",
            "security_boundary_ref",
            "auth_scope_strategy_ref",
            "rate_limit_strategy_ref",
            "fallback_solution_ref",
            "rollback_solution_ref",
            "owner_layer_declaration_ref",
        ],
        "enforcement_validator": "scripts/validate_identity_vendor_api_solution.py",
    },
}

DEFAULT_TRIGGER_CLASSES = (
    "repeat_platform_optimization_intent",
    "repeat_quality_not_sufficient",
    "closure_failure_capability_gap",
)

OPTIMIZATION_HINTS = (
    "optimization",
    "optimize",
    "tuning",
    "性能",
    "提效",
    "优化",
    "加速",
)
QUALITY_NOT_SUFFICIENT_HINTS = (
    "quality-not-sufficient",
    "quality not sufficient",
    "usable but quality",
    "quality insufficient",
    "质量不足",
    "质量不够",
    "效果不足",
    "效果不够",
)
CAPABILITY_GAP_HINTS = (
    "capability gap",
    "tool gap",
    "vendor api gap",
    "missing tool",
    "missing capability",
    "ip-cap-003",
    "auth blocked",
    "能力缺口",
    "工具缺口",
    "能力不足",
)

NON_BLOCKING_WARNING_STATUSES = {"WARN_NON_BLOCKING", "TRIGGERED_NON_BLOCKING"}

EXPIRY_CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "scripts/trigger_platform_optimization_discovery.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/build_vibe_coding_feeding_pack.py",
        ("--operation", "<operation>", "--out-root", "/tmp/vibe-coding-feeding-packs", "--json-only"),
    ),
    (
        "scripts/validate_identity_capability_fit_optimization.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/validate_capability_composition_before_discovery.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/validate_capability_fit_review_freshness.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/validate_capability_fit_roundtable_evidence.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/trigger_capability_fit_review.py",
        ("--operation", "<operation>", "--json-only"),
    ),
    (
        "scripts/build_capability_fit_matrix.py",
        ("--operation", "<operation>", "--out-root", "/tmp/capability-fit-matrices", "--json-only"),
    ),
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in ("discovery_requiredization_contract_v1", "discovery_requiredization_contract"):
        obj = task.get(key)
        if isinstance(obj, dict):
            return obj
    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("discovery_requiredization_contract_v1")
        if isinstance(nested, dict):
            return nested
    return {}


def _feedback_batches(pack_root: Path, pattern: str, window_rounds: int) -> list[Path]:
    raw = str(pattern or "").strip() or "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md"
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    hits: list[Path] = []
    protocol_root = Path(__file__).resolve().parent.parent
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = sorted((pack_root / raw).parent.glob((pack_root / raw).name)) if not has_magic else sorted(pack_root.glob(raw))
        if preferred:
            hits = [x.resolve() for x in preferred if x.exists()]
        else:
            fallback = sorted(protocol_root.glob(raw))
            hits = [x.resolve() for x in fallback if x.exists()]
    hits = [x for x in hits if x.is_file()]
    hits.sort(key=lambda x: x.stat().st_mtime)
    if window_rounds > 0:
        return hits[-window_rounds:]
    return hits


def _extract_platform_class(raw: str, parsed: dict[str, Any]) -> str:
    direct = str(
        parsed.get("platform_class")
        or parsed.get("platform")
        or parsed.get("target_platform")
        or parsed.get("domain_class")
        or ""
    ).strip()
    if direct:
        return direct
    m = re.search(r"\b(platform_class|platform|target_platform|domain_class)\b\s*[:=]\s*([A-Za-z0-9_\-]+)", raw, flags=re.I)
    return m.group(2).strip() if m else ""


def _parse_feedback_batch(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parsed: dict[str, Any] = {}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parsed = obj
    except Exception:
        parsed = {}
    low = raw.lower()
    platform_class = _extract_platform_class(raw, parsed)
    optimization_signal = boolish(parsed.get("optimization_intent_signal", False)) or any(h in low for h in OPTIMIZATION_HINTS)
    quality_signal = boolish(parsed.get("quality_not_sufficient", False)) or any(h in low for h in QUALITY_NOT_SUFFICIENT_HINTS)
    capability_gap_signal = boolish(parsed.get("capability_gap", False)) or any(h in low for h in CAPABILITY_GAP_HINTS)
    return {
        "path": str(path),
        "platform_class": platform_class,
        "optimization_signal": optimization_signal,
        "quality_not_sufficient": quality_signal,
        "capability_gap": capability_gap_signal,
    }


def _trigger_flags(items: list[dict[str, Any]]) -> tuple[dict[str, bool], list[str]]:
    repeat_platform = False
    if len(items) >= 2:
        pair = items[-2:]
        same_platform = bool(
            pair[0].get("platform_class")
            and pair[1].get("platform_class")
            and pair[0]["platform_class"] == pair[1]["platform_class"]
        )
        repeat_platform = same_platform and bool(pair[0].get("optimization_signal") and pair[1].get("optimization_signal"))
    repeat_quality = sum(1 for x in items if bool(x.get("quality_not_sufficient"))) >= 2
    closure_cap_gap = any(bool(x.get("capability_gap")) for x in items)
    flags = {
        "repeat_platform_optimization_intent": repeat_platform,
        "repeat_quality_not_sufficient": repeat_quality,
        "closure_failure_capability_gap": closure_cap_gap,
    }
    classes = [k for k, v in flags.items() if v]
    return flags, classes


def _required_flags(task: dict[str, Any]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for key in DISCOVERY_CONTRACT_KEYS:
        c = task.get(key)
        out[key] = contract_required(c) if isinstance(c, dict) else False
    return out


def _validate_receipt(receipt_path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        obj = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"requiredization_receipt_invalid_json:{exc}"
    if not isinstance(obj, dict):
        return None, "requiredization_receipt_root_not_object"
    required_fields = (
        "requiredization_triggered",
        "trigger_classes",
        "window_rounds",
        "evidence_refs",
        "previous_required_state",
        "new_required_state",
        "requiredized_at",
    )
    missing = [k for k in required_fields if k not in obj]
    if missing:
        return None, f"requiredization_receipt_missing_fields:{','.join(missing)}"
    if not isinstance(obj.get("trigger_classes"), list) or not obj.get("trigger_classes"):
        return None, "requiredization_receipt_trigger_classes_invalid"
    if not isinstance(obj.get("evidence_refs"), list) or not obj.get("evidence_refs"):
        return None, "requiredization_receipt_evidence_refs_invalid"
    if not isinstance(obj.get("new_required_state"), dict):
        return None, "requiredization_receipt_new_required_state_invalid"
    ts = str(obj.get("requiredized_at") or "").strip()
    if not ts:
        return None, "requiredization_receipt_requiredized_at_missing"
    return obj, ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_contract_skeleton(identity_id: str, key: str) -> dict[str, Any]:
    base = dict(DISCOVERY_CONTRACT_DEFAULTS.get(key, {}))
    pattern = str(base.get("report_path_pattern", "")).replace("<identity-id>", identity_id)
    if pattern:
        base["report_path_pattern"] = pattern
    return base


def _receipt_output_path(pack_path: Path, pattern: str) -> Path:
    raw = str(pattern or "").strip() or "runtime/protocol-feedback/outbox-to-protocol/DISCOVERY_REQUIREDIZATION_RECEIPT_*.json"
    p = Path(raw)
    if p.is_absolute():
        parent = p.parent
    else:
        if any(ch in raw for ch in ["*", "?", "["]):
            parent = (pack_path / p.parent).resolve()
        else:
            parent = (pack_path / p).resolve().parent
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return parent / f"DISCOVERY_REQUIREDIZATION_RECEIPT_{ts}.json"


def _append_index_link(index_path: Path, receipt_path: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    rel = f"outbox-to-protocol/{receipt_path.name}"
    if not index_path.exists():
        index_path.write_text("# protocol-feedback evidence index\n", encoding="utf-8")
    raw = index_path.read_text(encoding="utf-8", errors="ignore")
    if receipt_path.name.lower() in raw.lower() or rel.lower() in raw.lower():
        return
    with index_path.open("a", encoding="utf-8") as f:
        if not raw.endswith("\n"):
            f.write("\n")
        f.write(f"- {rel}\n")


def _receipt_linked(index_path: Path, receipt_path: Path) -> bool:
    if not index_path.exists():
        return False
    raw = index_path.read_text(encoding="utf-8", errors="ignore").lower()
    name = receipt_path.name.lower()
    rel = f"outbox-to-protocol/{receipt_path.name}".lower()
    return (name in raw) or (rel in raw)


def _run_discovery_validator(script: str, catalog: Path, identity_id: str) -> tuple[int, str]:
    cmd = ["python3", script, "--catalog", str(catalog), "--identity-id", identity_id]
    p = subprocess.run(cmd, capture_output=True, text=True)
    tail = (p.stdout or "").strip().splitlines()
    if tail:
        return p.returncode, tail[-1]
    err = (p.stderr or "").strip().splitlines()
    return p.returncode, (err[-1] if err else "")


def _parse_iso_datetime(raw: str) -> datetime | None:
    txt = str(raw or "").strip()
    if not txt:
        return None
    try:
        if txt.endswith("Z"):
            txt = txt[:-1] + "+00:00"
        return datetime.fromisoformat(txt)
    except Exception:
        return None


def _payload_status(payload: dict[str, Any]) -> str:
    for k, v in payload.items():
        if k.endswith("_status") and isinstance(v, str):
            return v.strip().upper()
    return ""


def _collect_candidate_paths(payload: dict[str, Any]) -> list[Path]:
    refs: list[str] = []
    for key in (
        "feedback_batch_path",
        "fit_matrix_path",
        "matrix_path",
        "roundtable_evidence_path",
    ):
        token = str(payload.get(key, "")).strip()
        if token:
            refs.append(token)
    batches = payload.get("feedback_batches")
    if isinstance(batches, list):
        for x in batches:
            token = str(x).strip()
            if token:
                refs.append(token)
    out: list[Path] = []
    for token in refs:
        p = Path(token).expanduser()
        if p.exists():
            out.append(p.resolve())
    return out


def _warning_age_days(payload: dict[str, Any]) -> float | None:
    overdue = payload.get("overdue_by_days")
    if isinstance(overdue, (int, float)) and overdue >= 0:
        return float(overdue)
    next_review = _parse_iso_datetime(str(payload.get("next_review_at", "")).strip())
    if next_review is not None:
        now = datetime.now(timezone.utc)
        if next_review.tzinfo is None:
            next_review = next_review.replace(tzinfo=timezone.utc)
        delta = (now - next_review).total_seconds() / 86400.0
        return max(0.0, round(delta, 3))
    paths = _collect_candidate_paths(payload)
    if not paths:
        return None
    now = datetime.now(timezone.utc).timestamp()
    ages = []
    for p in paths:
        try:
            ages.append((now - p.stat().st_mtime) / 86400.0)
        except Exception:
            continue
    if not ages:
        return None
    return round(max(ages), 3)


def _run_expiry_checks(*, catalog: Path, identity_id: str, operation: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    warning_rows: list[dict[str, Any]] = []
    for script, suffix_tpl in EXPIRY_CHECKS:
        suffix: list[str] = []
        for token in suffix_tpl:
            if token == "<operation>":
                suffix.append(operation)
            else:
                suffix.append(token)
        cmd = ["python3", script, "--catalog", str(catalog), "--identity-id", identity_id, *suffix]
        p = subprocess.run(cmd, capture_output=True, text=True)
        raw = (p.stdout or "").strip()
        payload: dict[str, Any] = {}
        try:
            obj = json.loads(raw) if raw else {}
            if isinstance(obj, dict):
                payload = obj
        except Exception:
            payload = {}
        status = _payload_status(payload)
        age_days = _warning_age_days(payload) if status in NON_BLOCKING_WARNING_STATUSES else None
        row = {
            "script": script,
            "rc": p.returncode,
            "status": status,
            "warning_age_days": age_days,
            "tail": (raw.splitlines()[-1] if raw else ((p.stderr or "").strip().splitlines()[-1] if (p.stderr or "").strip() else "")),
        }
        rows.append(row)
        if status in NON_BLOCKING_WARNING_STATUSES:
            warning_rows.append(row)
    return {
        "checks": rows,
        "warnings": warning_rows,
        "warning_count": len(warning_rows),
    }


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate discovery requiredization and CI synchronization contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--receipt", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument(
        "--apply-requiredization",
        action="store_true",
        help=(
            "apply deterministic requiredization writeback when trigger conditions are met "
            "(promote discovery contracts to required=true, sync ci required validators, write receipt+index)."
        ),
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
    required_declared = contract_required(contract) if contract else False
    window_rounds = int(contract.get("window_rounds", 2) or 2) if isinstance(contract, dict) else 2
    if window_rounds < 2:
        window_rounds = 2
    feedback_pattern = (
        str(contract.get("feedback_batch_path_pattern", "")).strip()
        if isinstance(contract, dict)
        else ""
    )
    batches = _feedback_batches(pack_path, feedback_pattern, window_rounds)
    parsed_batches = [_parse_feedback_batch(p) for p in batches]
    trigger_flags, trigger_classes = _trigger_flags(parsed_batches)
    requiredization_triggered = len(trigger_classes) > 0
    non_blocking_expiry_days = int(contract.get("non_blocking_expiry_days", 7) or 7) if isinstance(contract, dict) else 7
    if non_blocking_expiry_days < 0:
        non_blocking_expiry_days = 0

    required_state = _required_flags(task)
    requiredized_all = all(required_state.values())
    required_effective = required_declared or requiredization_triggered or requiredized_all
    auto_required_signal = (not required_declared) and (requiredization_triggered or requiredized_all)

    discovery_results: dict[str, Any] = {}
    discovery_required_total = 0
    discovery_required_passed = 0
    for key in DISCOVERY_CONTRACT_KEYS:
        script = DISCOVERY_VALIDATORS[key]
        rc, tail = _run_discovery_validator(script, catalog_path, args.identity_id)
        if required_state.get(key, False):
            discovery_required_total += 1
            if rc == 0:
                discovery_required_passed += 1
        discovery_results[key] = {
            "validator": script,
            "required": required_state.get(key, False),
            "rc": rc,
            "tail": tail,
        }

    discovery_required_coverage_rate = round(
        (discovery_required_passed / discovery_required_total) * 100.0, 2
    ) if discovery_required_total > 0 else 0.0

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required_effective,
        "required_contract_declared": required_declared,
        "auto_required_signal": auto_required_signal,
        "discovery_requiredization_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "requiredization_applied": False,
        "requiredization_apply_receipt_ref": "",
        "requiredization_triggered": requiredization_triggered,
        "trigger_classes": trigger_classes,
        "trigger_classes_declared": list(contract.get("trigger_classes", DEFAULT_TRIGGER_CLASSES)) if isinstance(contract, dict) else list(DEFAULT_TRIGGER_CLASSES),
        "window_rounds": window_rounds,
        "feedback_batches": [str(x) for x in batches],
        "trigger_condition_flags": trigger_flags,
        "discovery_contract_required_state": required_state,
        "requiredized_all_discovery_contracts": requiredized_all,
        "requiredization_receipt_path": "",
        "requiredization_receipt_linked": False,
        "requiredization_receipt_fields": {},
        "evidence_index_path": "",
        "ci_required_validators_missing": [],
        "ci_required_validators_present": [],
        "discovery_required_total": discovery_required_total,
        "discovery_required_passed": discovery_required_passed,
        "discovery_required_coverage_rate": discovery_required_coverage_rate,
        "discovery_validator_results": discovery_results,
        "non_blocking_expiry_days": non_blocking_expiry_days,
        "non_blocking_warnings": [],
        "non_blocking_warning_count": 0,
        "non_blocking_expired": False,
        "checked_at": _iso_now(),
        "stale_reasons": [],
    }

    expiry_eval = _run_expiry_checks(
        catalog=catalog_path,
        identity_id=args.identity_id,
        operation=args.operation,
    )
    warnings = expiry_eval.get("warnings", [])
    payload["non_blocking_warnings"] = warnings
    payload["non_blocking_warning_count"] = int(expiry_eval.get("warning_count", 0) or 0)
    expired_warning_rows = [
        row
        for row in warnings
        if isinstance(row.get("warning_age_days"), (int, float))
        and float(row.get("warning_age_days", 0.0)) > float(non_blocking_expiry_days)
    ]
    payload["non_blocking_expired"] = len(expired_warning_rows) > 0

    if not required_effective:
        if payload["non_blocking_expired"]:
            payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_NON_BLOCKING_EXPIRED
            payload["stale_reasons"] = [
                "non_blocking_discovery_warning_expired",
                f"expiry_days={non_blocking_expiry_days}",
            ]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if requiredization_triggered and not requiredized_all and args.apply_requiredization:
        previous_state = dict(required_state)
        for key in DISCOVERY_CONTRACT_KEYS:
            current = task.get(key)
            normalized = _normalize_contract_skeleton(args.identity_id, key)
            merged = dict(normalized)
            if isinstance(current, dict):
                merged.update(current)
            merged["required"] = True
            task[key] = merged
        ci_contract = task.get("ci_enforcement_contract")
        if not isinstance(ci_contract, dict):
            ci_contract = {"required": True}
            task["ci_enforcement_contract"] = ci_contract
        required_validators = ci_contract.get("required_validators")
        if not isinstance(required_validators, list):
            required_validators = []
        for script in (DISCOVERY_VALIDATORS[k] for k in DISCOVERY_CONTRACT_KEYS):
            if script not in required_validators:
                required_validators.append(script)
        ci_contract["required_validators"] = required_validators
        _write_json(task_path, task)

        required_state = _required_flags(task)
        requiredized_all = all(required_state.values())
        required_effective = True
        auto_required_signal = True

        receipt_pattern_apply = (
            str(contract.get("requiredization_receipt_pattern", "")).strip()
            if isinstance(contract, dict)
            else ""
        ) or "runtime/protocol-feedback/outbox-to-protocol/DISCOVERY_REQUIREDIZATION_RECEIPT_*.json"
        receipt_out = _receipt_output_path(pack_path, receipt_pattern_apply)
        receipt_payload = {
            "requiredization_triggered": True,
            "trigger_classes": trigger_classes or list(DEFAULT_TRIGGER_CLASSES),
            "window_rounds": window_rounds,
            "evidence_refs": [str(x) for x in batches],
            "previous_required_state": previous_state,
            "new_required_state": required_state,
            "requiredized_at": _iso_now(),
            "required_contract_keys": list(DISCOVERY_CONTRACT_KEYS),
        }
        _write_json(receipt_out, receipt_payload)
        payload["requiredization_applied"] = True
        payload["requiredization_apply_receipt_ref"] = str(receipt_out)
        payload["requiredization_receipt_path"] = str(receipt_out)
        payload["requiredization_receipt_fields"] = receipt_payload

        index_rel_apply = (
            str(contract.get("evidence_index_path", "")).strip()
            if isinstance(contract, dict)
            else ""
        ) or "runtime/protocol-feedback/evidence-index/INDEX.md"
        index_apply = (pack_path / index_rel_apply).resolve()
        _append_index_link(index_apply, receipt_out)
        payload["evidence_index_path"] = str(index_apply)
        payload["requiredization_receipt_linked"] = _receipt_linked(index_apply, receipt_out)

        discovery_results = {}
        discovery_required_total = 0
        discovery_required_passed = 0
        for key in DISCOVERY_CONTRACT_KEYS:
            script = DISCOVERY_VALIDATORS[key]
            rc, tail = _run_discovery_validator(script, catalog_path, args.identity_id)
            if required_state.get(key, False):
                discovery_required_total += 1
                if rc == 0:
                    discovery_required_passed += 1
            discovery_results[key] = {
                "validator": script,
                "required": required_state.get(key, False),
                "rc": rc,
                "tail": tail,
            }
        discovery_required_coverage_rate = round(
            (discovery_required_passed / discovery_required_total) * 100.0, 2
        ) if discovery_required_total > 0 else 0.0
        payload["discovery_contract_required_state"] = required_state
        payload["requiredized_all_discovery_contracts"] = requiredized_all
        payload["discovery_required_total"] = discovery_required_total
        payload["discovery_required_passed"] = discovery_required_passed
        payload["discovery_required_coverage_rate"] = discovery_required_coverage_rate
        payload["discovery_validator_results"] = discovery_results

    if requiredization_triggered and not requiredized_all:
        payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TRIGGER_NOT_APPLIED
        payload["stale_reasons"] = ["requiredization_triggered_but_discovery_contracts_not_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    receipt_pattern = (
        str(contract.get("requiredization_receipt_pattern", "")).strip()
        if isinstance(contract, dict)
        else ""
    ) or "runtime/protocol-feedback/outbox-to-protocol/DISCOVERY_REQUIREDIZATION_RECEIPT_*.json"
    receipt_path = resolve_report_path(report=args.receipt, pattern=receipt_pattern, pack_root=pack_path)
    if receipt_path is None:
        if args.apply_requiredization:
            synthetic_receipt = _receipt_output_path(pack_path, receipt_pattern)
            synthetic_payload = {
                "requiredization_triggered": bool(requiredization_triggered),
                "trigger_classes": trigger_classes or ["legacy_requiredized_state"],
                "window_rounds": window_rounds,
                "evidence_refs": [str(x) for x in batches],
                "previous_required_state": required_state,
                "new_required_state": required_state,
                "requiredized_at": _iso_now(),
                "required_contract_keys": list(DISCOVERY_CONTRACT_KEYS),
            }
            _write_json(synthetic_receipt, synthetic_payload)
            receipt_path = synthetic_receipt
            payload["requiredization_applied"] = True
            payload["requiredization_apply_receipt_ref"] = str(synthetic_receipt)
            payload["requiredization_receipt_path"] = str(synthetic_receipt)
            payload["requiredization_receipt_fields"] = synthetic_payload
        else:
            payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_RECEIPT_MISSING
            payload["stale_reasons"] = ["requiredization_receipt_missing"]
            _emit(payload, json_only=args.json_only)
            return 1
    if receipt_path is None:
        payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = ["requiredization_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1
    payload["requiredization_receipt_path"] = str(receipt_path)
    receipt_doc, receipt_err = _validate_receipt(receipt_path)
    if receipt_doc is None:
        payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = [receipt_err]
        _emit(payload, json_only=args.json_only)
        return 1
    payload["requiredization_receipt_fields"] = receipt_doc

    index_rel = (
        str(contract.get("evidence_index_path", "")).strip()
        if isinstance(contract, dict)
        else ""
    ) or "runtime/protocol-feedback/evidence-index/INDEX.md"
    index_path = (pack_path / index_rel).resolve()
    payload["evidence_index_path"] = str(index_path)
    linked = _receipt_linked(index_path, receipt_path)
    payload["requiredization_receipt_linked"] = linked
    if not linked:
        if args.apply_requiredization:
            _append_index_link(index_path, receipt_path)
            linked = _receipt_linked(index_path, receipt_path)
            payload["requiredization_receipt_linked"] = linked
        if not linked:
            payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_RECEIPT_NOT_LINKED
            payload["stale_reasons"] = ["requiredization_receipt_not_linked_in_evidence_index"]
            _emit(payload, json_only=args.json_only)
            return 1

    ci_contract = task.get("ci_enforcement_contract")
    ci_required = ci_contract.get("required_validators", []) if isinstance(ci_contract, dict) else []
    if not isinstance(ci_required, list):
        ci_required = []
    trio_required_validators = [DISCOVERY_VALIDATORS[k] for k in DISCOVERY_CONTRACT_KEYS]
    missing = [v for v in trio_required_validators if v not in ci_required]
    payload["ci_required_validators_missing"] = missing
    payload["ci_required_validators_present"] = [v for v in trio_required_validators if v in ci_required]
    if missing:
        if args.apply_requiredization and isinstance(ci_contract, dict):
            merged = list(ci_required)
            for v in missing:
                if v not in merged:
                    merged.append(v)
            ci_contract["required_validators"] = merged
            task["ci_enforcement_contract"] = ci_contract
            _write_json(task_path, task)
            ci_required = merged
            missing = [v for v in trio_required_validators if v not in ci_required]
            payload["ci_required_validators_missing"] = missing
            payload["ci_required_validators_present"] = [v for v in trio_required_validators if v in ci_required]
            payload["requiredization_applied"] = True
        if missing:
            payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CI_VALIDATOR_MISSING
            payload["stale_reasons"] = ["ci_required_validators_missing_discovery_trio"]
            _emit(payload, json_only=args.json_only)
            return 1

    payload["discovery_requiredization_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    if payload["non_blocking_expired"]:
        payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_NON_BLOCKING_EXPIRED
        payload["stale_reasons"] = [
            "non_blocking_discovery_warning_expired",
            f"expiry_days={non_blocking_expiry_days}",
        ]
        _emit(payload, json_only=args.json_only)
        return 1
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
