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
        "checked_at": _iso_now(),
        "stale_reasons": [],
    }

    if not required_effective:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

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
        payload["discovery_requiredization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CI_VALIDATOR_MISSING
        payload["stale_reasons"] = ["ci_required_validators_missing_discovery_trio"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["discovery_requiredization_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

