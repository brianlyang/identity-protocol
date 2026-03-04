#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_NOT_TRIGGERED = "NOT_TRIGGERED"
STATUS_TRIGGERED_NON_BLOCKING = "TRIGGERED_NON_BLOCKING"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

ERR_INSUFFICIENT_EVIDENCE = "IP-OPT-001"
ERR_PLATFORM_CLASS_MISSING = "IP-OPT-002"
ERR_TRIGGER_OUTPUT_INCOMPLETE = "IP-OPT-003"


OPTIMIZATION_HINTS = (
    "optimization",
    "optimize",
    "tuning",
    "提效",
    "优化",
    "性能",
    "加速",
)

NOT_CLOSED_HINTS = (
    "flow not closed",
    "not closed",
    "loop not closed",
    "未闭环",
    "没闭环",
    "仍未完成",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "platform_optimization_discovery_trigger_v1",
        "platform_optimization_discovery_trigger",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("platform_optimization_discovery_trigger_v1")
        if isinstance(nested, dict):
            return nested
    return {}


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback" / "outbox-to-protocol").resolve()
    if not root.exists():
        return False
    return any(p.is_file() for p in root.rglob("FEEDBACK_BATCH_*"))


def _collect_batches(pack_path: Path, pattern: str, limit: int = 2) -> list[Path]:
    raw = str(pattern).strip() if str(pattern).strip() else "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md"
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    hits: list[Path] = []
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = sorted(pack_path.glob(raw))
        if preferred:
            hits = [x.resolve() for x in preferred]
        else:
            hits = [x.resolve() for x in Path(".").glob(raw)]
    hits = [x for x in hits if x.exists() and x.is_file()]
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-limit:] if limit > 0 else hits


def _extract_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _parse_batch(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parsed: dict[str, Any] = {}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            parsed = obj
    except Exception:
        parsed = {}

    platform_class = str(
        parsed.get("platform_class")
        or parsed.get("platform")
        or parsed.get("domain_class")
        or parsed.get("target_platform")
        or ""
    ).strip()
    if not platform_class:
        platform_class = _extract_first(raw, r"\b(platform_class|platform|target_platform)\b\s*[:=]\s*([a-zA-Z0-9_\-]+)")
        if platform_class and "=" in platform_class:
            platform_class = platform_class.split("=", 1)[-1].strip()

    low = raw.lower()
    intent_flag = bool(parsed.get("optimization_intent_signal", False))
    if not intent_flag:
        intent_raw = str(parsed.get("optimization_intent") or parsed.get("intent_type") or "").strip().lower()
        intent_flag = any(h in intent_raw for h in OPTIMIZATION_HINTS) or any(h in low for h in OPTIMIZATION_HINTS)

    flow_not_closed = bool(parsed.get("flow_not_closed", False))
    if not flow_not_closed:
        flow_raw = str(parsed.get("closure_status") or parsed.get("flow_status") or "").strip().lower()
        flow_not_closed = any(h in flow_raw for h in NOT_CLOSED_HINTS) or any(h in low for h in NOT_CLOSED_HINTS)

    upgrade_ref = str(parsed.get("upgrade_proposal_ref") or "").strip()
    if not upgrade_ref:
        upgrade_ref = _extract_first(raw, r"\bupgrade_proposal_ref\b\s*[:=]\s*(.+)$")
    if not upgrade_ref:
        m = re.search(r"runtime/protocol-feedback/upgrade-proposals/[^\s`]+", raw, flags=re.IGNORECASE)
        if m:
            upgrade_ref = m.group(0).strip()

    return {
        "path": str(path),
        "platform_class": platform_class,
        "optimization_intent_signal": intent_flag,
        "flow_not_closed": flow_not_closed,
        "upgrade_proposal_ref": upgrade_ref,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Trigger platform optimization discovery when repeated optimization signals are detected.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-batch", default="")
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
    required = contract_required(contract) if contract else False
    auto_required_signal = False
    if not required and _feedback_artifacts_present(pack_path):
        # keep P1 non-blocking; only mark auto signal for visibility when contract absent
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "platform_optimization_discovery_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "triggered": False,
        "trigger_reason": "",
        "discovery_scope": "",
        "official_doc_retrieval_set": [],
        "cross_validation_summary": {},
        "upgrade_proposal_ref": "",
        "feedback_batches": [],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(contract.get("feedback_batch_path_pattern", "")).strip()
    window = int(contract.get("signal_round_window", 2) or 2)
    if window < 2:
        window = 2

    if args.feedback_batch.strip():
        batch = Path(args.feedback_batch).expanduser().resolve()
        batches = [batch] if batch.exists() and batch.is_file() else []
    else:
        batches = _collect_batches(pack_path, pattern=pattern, limit=window)

    payload["feedback_batches"] = [str(x) for x in batches]
    if len(batches) < 2:
        payload["platform_optimization_discovery_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_INSUFFICIENT_EVIDENCE
        payload["stale_reasons"] = ["insufficient_consecutive_rounds"]
        _emit(payload, json_only=args.json_only)
        return 0

    parsed = [_parse_batch(p) for p in batches[-2:]]
    latest = parsed[-1]
    prev = parsed[-2]

    same_platform = bool(latest["platform_class"] and prev["platform_class"] and latest["platform_class"] == prev["platform_class"])
    repeat_optimization = same_platform and bool(latest["optimization_intent_signal"] and prev["optimization_intent_signal"])
    repeat_not_closed = bool(latest["flow_not_closed"] and prev["flow_not_closed"] and (latest["optimization_intent_signal"] or prev["optimization_intent_signal"]))

    payload["cross_validation_summary"] = {
        "window_size": 2,
        "latest_platform_class": latest["platform_class"],
        "previous_platform_class": prev["platform_class"],
        "same_platform_class": same_platform,
        "repeat_optimization_signal": repeat_optimization,
        "repeat_not_closed_signal": repeat_not_closed,
    }

    trigger = repeat_optimization or repeat_not_closed
    if trigger and not latest["platform_class"]:
        payload["platform_optimization_discovery_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_PLATFORM_CLASS_MISSING
        payload["stale_reasons"] = ["platform_class_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not trigger:
        payload["platform_optimization_discovery_status"] = STATUS_NOT_TRIGGERED
        payload["stale_reasons"] = ["trigger_conditions_not_met"]
        _emit(payload, json_only=args.json_only)
        return 0

    discovery_scope = str(contract.get("discovery_scope", "official_docs+cross_validation+upgrade_proposal")).strip()
    official_doc_set = contract.get("official_doc_retrieval_set")
    if not isinstance(official_doc_set, list) or not official_doc_set:
        official_doc_set = [
            "official_vendor_docs",
            "official_protocol_specs",
            "openapi_or_discovery_specs",
        ]

    upgrade_ref = latest.get("upgrade_proposal_ref") or prev.get("upgrade_proposal_ref")

    payload.update(
        {
            "platform_optimization_discovery_status": STATUS_TRIGGERED_NON_BLOCKING,
            "triggered": True,
            "trigger_reason": (
                "repeat_optimization_intent_same_platform" if repeat_optimization else "repeat_flow_not_closed_under_optimization"
            ),
            "discovery_scope": discovery_scope,
            "official_doc_retrieval_set": [str(x) for x in official_doc_set],
            "upgrade_proposal_ref": str(upgrade_ref or ""),
            "stale_reasons": [],
        }
    )

    required_fields_ok = bool(payload["discovery_scope"] and payload["official_doc_retrieval_set"] and payload["cross_validation_summary"])
    if not required_fields_ok:
        payload["platform_optimization_discovery_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_TRIGGER_OUTPUT_INCOMPLETE
        payload["stale_reasons"] = ["trigger_output_incomplete"]

    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
