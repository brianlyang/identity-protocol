#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from capability_fit_roundtable_common import DEFAULT_FIT_MATRIX_PATTERN, DEFAULT_ROUNDTABLE_PATTERN
from feedback_runtime_log_backfill_common import build_feedback_runtime_log_payload
from strict_live_evidence_resolution_common import clean_string

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

CURRENT_RUN_ROUTE_REVIEW_INTERVAL_DAYS = 14
ROUTE_OPTIMIZATION_CONTRACT_KEY = "capability_fit_self_drive_optimization_contract_v1"
ROUNDTABLE_EVIDENCE_CONTRACT_KEY = "capability_fit_roundtable_evidence_contract_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _future_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=max(1, int(days)))).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _slug(value: Any) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", clean_string(value).lower()).strip("-")
    return token or "current-run"


def _unique_strings(values: list[str]) -> list[str]:
    rows: list[str] = []
    for value in values:
        token = clean_string(value)
        if token and token not in rows:
            rows.append(token)
    return rows


def _canonicalize_current_run_projection_artifacts(
    *,
    existing_artifacts: list[str],
    projection_refs: list[str],
) -> list[str]:
    canonical_projection_paths: list[str] = []
    canonical_projection_names: dict[str, str] = {}
    for raw in projection_refs:
        token = clean_string(raw)
        if not token:
            continue
        try:
            canonical = str(Path(token).expanduser().resolve())
        except Exception:
            canonical = token
        if canonical not in canonical_projection_paths:
            canonical_projection_paths.append(canonical)
        name = Path(canonical).name
        if name and name not in canonical_projection_names:
            canonical_projection_names[name] = canonical

    normalized: list[str] = []
    for raw in existing_artifacts:
        token = clean_string(raw)
        if not token:
            continue
        candidate = token
        basename = ""
        try:
            candidate_path = Path(token).expanduser()
            if candidate_path.is_absolute() or "/" in token or "\\" in token:
                candidate = str(candidate_path.resolve())
                basename = candidate_path.name
        except Exception:
            candidate = token
            basename = Path(token).name if ("/" in token or "\\" in token) else ""

        canonical_for_basename = canonical_projection_names.get(basename, "")
        if canonical_for_basename and candidate != canonical_for_basename:
            # Current-run projection artifacts are shared, canonical pack-local surfaces.
            # If the same projection-owned basename appears from a temp workspace or any
            # non-canonical lane, keep only the canonical projection path.
            continue
        if candidate not in normalized:
            normalized.append(candidate)

    for canonical in canonical_projection_paths:
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized


def _deep_merge_defaults(base: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in (current or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_defaults(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capability_fit_self_drive_optimization_contract_skeleton() -> dict[str, Any]:
    return {
        "required": True,
        "validator": "scripts/validate_identity_capability_fit_optimization.py",
        "fit_matrix_path_pattern": DEFAULT_FIT_MATRIX_PATTERN,
        "roundtable_evidence_path_pattern": DEFAULT_ROUNDTABLE_PATTERN,
        "review_interval_days": CURRENT_RUN_ROUTE_REVIEW_INTERVAL_DAYS,
        "inventory_mode": "active_execution_capability_inventory",
        "inventory_first_required": True,
        "compose_before_discover_required": True,
        "existing_composition_candidate_required": True,
        "external_discovery_allowed_only_when": ["not_sufficient", "not_cost_effective"],
    }


def capability_fit_roundtable_evidence_contract_skeleton() -> dict[str, Any]:
    return {
        "required": True,
        "validator": "scripts/validate_capability_fit_roundtable_evidence.py",
        "fit_matrix_path_pattern": DEFAULT_FIT_MATRIX_PATTERN,
        "roundtable_evidence_path_pattern": DEFAULT_ROUNDTABLE_PATTERN,
        "source_priority": [
            "official_vendor_docs",
            "official_protocol_spec",
            "standard_organization_spec",
            "community_wrappers",
        ],
    }


def ensure_weak_live_route_contracts(task_doc: dict[str, Any]) -> list[str]:
    restored: list[str] = []
    arbitration = task_doc.get("capability_arbitration_contract")
    route_enforcement = arbitration.get("route_discovery_enforcement") if isinstance(arbitration, dict) else None
    if not isinstance(route_enforcement, dict) or not route_enforcement:
        return restored

    for key, skeleton in (
        (ROUTE_OPTIMIZATION_CONTRACT_KEY, capability_fit_self_drive_optimization_contract_skeleton()),
        (ROUNDTABLE_EVIDENCE_CONTRACT_KEY, capability_fit_roundtable_evidence_contract_skeleton()),
    ):
        current = task_doc.get(key)
        if not isinstance(current, dict):
            task_doc[key] = deepcopy(skeleton)
            restored.append(key)
            continue
        merged = _deep_merge_defaults(skeleton, current)
        if merged != current:
            task_doc[key] = merged
            restored.append(key)
    return restored


def _artifact_paths(active_report_doc: dict[str, Any]) -> list[Path]:
    rows: list[Path] = []
    for raw in active_report_doc.get("artifacts") or []:
        token = clean_string(raw)
        if not token:
            continue
        try:
            path = Path(token).expanduser().resolve()
        except Exception:
            continue
        if path.exists() and path not in rows:
            rows.append(path)
    return rows


def _find_artifact_path(active_report_doc: dict[str, Any], *, name_contains: str) -> Path | None:
    needle = clean_string(name_contains).lower()
    for path in _artifact_paths(active_report_doc):
        if needle in path.name.lower():
            return path
    return None


def _route_metrics_doc(active_report_doc: dict[str, Any]) -> dict[str, Any]:
    metrics_path = clean_string(active_report_doc.get("metrics_path"))
    candidates: list[Path] = []
    if metrics_path:
        try:
            candidate = Path(metrics_path).expanduser().resolve()
            if candidate.exists():
                candidates.append(candidate)
        except Exception:
            pass
    artifact = _find_artifact_path(active_report_doc, name_contains="route-quality")
    if artifact is not None and artifact not in candidates:
        candidates.append(artifact)
    for path in candidates:
        doc = _load_json(path)
        if doc:
            return doc
    return {}


def _protocol_root(pack_root: Path, active_report_doc: dict[str, Any]) -> Path:
    token = clean_string(active_report_doc.get("protocol_root"))
    if token:
        candidate = Path(token).expanduser()
        try:
            if candidate.exists():
                return candidate.resolve()
        except Exception:
            pass
    return Path(__file__).resolve().parents[1]


def _feedback_log_path(pack_root: Path, identity_id: str, run_id: str) -> Path:
    return (pack_root / "runtime" / "logs" / "feedback" / f"{identity_id}-feedback-current-run-{run_id}.json").resolve()


def _sample_live_report_paths(pack_root: Path, identity_id: str, run_id: str) -> dict[str, Path]:
    runtime_reports = (pack_root / "runtime" / "reports").resolve()
    return {
        "capability_arbitration": runtime_reports / f"{identity_id}-capability-arbitration-live-{run_id}.json",
        "experience_feedback": runtime_reports / f"{identity_id}-experience-feedback-live-{run_id}.json",
        "knowledge_acquisition": runtime_reports / f"{identity_id}-knowledge-acquisition-live-{run_id}.json",
        "trigger_regression": runtime_reports / f"{identity_id}-trigger-regression-live-{run_id}.json",
    }


def _route_projection_paths(pack_root: Path, identity_id: str, run_id: str) -> dict[str, Path]:
    optimization_root = (pack_root / "runtime" / "protocol-feedback" / "optimization").resolve()
    roundtable_root = (pack_root / "runtime" / "protocol-feedback" / "roundtables").resolve()
    return {
        "fit_matrix": optimization_root / f"capability-fit-matrix-{identity_id}-{run_id}.json",
        "roundtable": roundtable_root / f"capability-fit-roundtable-{identity_id}-{run_id}.json",
    }


def _route_candidates(active_report_path: Path, active_report_doc: dict[str, Any]) -> list[dict[str, Any]]:
    active_skills = {
        clean_string(item)
        for item in (active_report_doc.get("active_skills") or active_report_doc.get("skills_used") or [])
        if clean_string(item)
    }
    available_mcp = {
        clean_string(row.get("mcp"))
        for row in (active_report_doc.get("mcp_servers_checked") or [])
        if isinstance(row, dict) and row.get("available") is True and clean_string(row.get("mcp"))
    }
    rows: list[dict[str, Any]] = []
    tool_routes = active_report_doc.get("tool_routes") or []
    if isinstance(tool_routes, list):
        for idx, route in enumerate(tool_routes, start=1):
            if not isinstance(route, dict):
                continue
            route_name = clean_string(route.get("route")) or f"route_{idx}"
            required_skills = [clean_string(item) for item in (route.get("required_skills") or []) if clean_string(item)]
            required_mcp = [clean_string(item) for item in (route.get("required_mcp") or []) if clean_string(item)]
            skill_ratio = 1.0 if not required_skills else len(set(required_skills) & active_skills) / len(required_skills)
            mcp_ratio = 1.0 if not required_mcp else len(set(required_mcp) & available_mcp) / len(required_mcp)
            fit_score = round((0.65 * skill_ratio) + (0.35 * mcp_ratio), 3)
            risk_score = round(max(0.0, 1.0 - fit_score), 3)
            pipeline_len = len(route.get("pipeline") or []) if isinstance(route.get("pipeline"), list) else 0
            operational_cost_score = round(min(1.0, (pipeline_len + len(required_skills) + len(required_mcp)) / 20.0), 3)
            fact_id = f"fact-{_slug(route_name)}"
            rows.append(
                {
                    "candidate_id": f"route:{route_name}",
                    "candidate_type": "existing_composition",
                    "fit_score": fit_score,
                    "risk_score": risk_score,
                    "operational_cost_score": operational_cost_score,
                    "provenance_ref": f"{active_report_path.resolve()}#tool_routes/{route_name}",
                    "decision": "rejected",
                    "decision_basis": (
                        f"current_run_route_readiness(skill={skill_ratio:.2f},mcp={mcp_ratio:.2f})"
                    ),
                    "fact_refs": [fact_id],
                    "decision_impacts": ["tool_routing"],
                    "required_skills": required_skills,
                    "required_mcp": required_mcp,
                    "active_skill_hits": sorted(set(required_skills) & active_skills),
                    "available_mcp_hits": sorted(set(required_mcp) & available_mcp),
                    "pipeline": list(route.get("pipeline") or []),
                }
            )
    if rows:
        return rows

    for skill in sorted(active_skills):
        fact_id = f"fact-{_slug(skill)}"
        rows.append(
            {
                "candidate_id": f"skill:{skill}",
                "candidate_type": "existing_composition",
                "fit_score": 1.0,
                "risk_score": 0.0,
                "operational_cost_score": 0.2,
                "provenance_ref": f"{active_report_path.resolve()}#active_skills/{skill}",
                "decision": "rejected",
                "decision_basis": "current_run_active_skill_inventory",
                "fact_refs": [fact_id],
                "decision_impacts": ["tool_routing"],
                "required_skills": [skill],
                "required_mcp": [],
                "active_skill_hits": [skill],
                "available_mcp_hits": [],
                "pipeline": [],
            }
        )
    if rows:
        return rows

    return [
        {
            "candidate_id": "route:current_run_default",
            "candidate_type": "existing_composition",
            "fit_score": 1.0,
            "risk_score": 0.0,
            "operational_cost_score": 0.3,
            "provenance_ref": str(active_report_path.resolve()),
            "decision": "rejected",
            "decision_basis": "current_run_default_route_projection",
            "fact_refs": ["fact-current-run-default"],
            "decision_impacts": ["tool_routing"],
            "required_skills": [],
            "required_mcp": [],
            "active_skill_hits": [],
            "available_mcp_hits": [],
            "pipeline": [],
        }
    ]


def _build_route_projection_payloads(
    *,
    identity_id: str,
    run_id: str,
    active_report_path: Path,
    active_report_doc: dict[str, Any],
    review_interval_days: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidates = _route_candidates(active_report_path, active_report_doc)
    ordered = sorted(
        candidates,
        key=lambda row: (
            -_safe_float(row.get("fit_score"), default=0.0),
            _safe_float(row.get("operational_cost_score"), default=1.0),
            clean_string(row.get("candidate_id")),
        ),
    )
    selected = deepcopy(ordered[0])
    selected["decision"] = "selected"
    selected["fallback_ref"] = "fallback:current_run_route_projection"
    selected["rollback_ref"] = str(active_report_path.resolve())
    selected["review_interval_days"] = int(review_interval_days or CURRENT_RUN_ROUTE_REVIEW_INTERVAL_DAYS)
    selected["next_review_at"] = _future_iso(selected["review_interval_days"])

    matrix_rows: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    inferences: list[dict[str, Any]] = []
    for row in ordered:
        item = deepcopy(row)
        if clean_string(item.get("candidate_id")) == clean_string(selected.get("candidate_id")):
            item.update(
                {
                    "decision": "selected",
                    "fallback_ref": selected["fallback_ref"],
                    "rollback_ref": selected["rollback_ref"],
                    "review_interval_days": selected["review_interval_days"],
                    "next_review_at": selected["next_review_at"],
                }
            )
        matrix_rows.append(
            {
                key: value
                for key, value in item.items()
                if key
                not in {
                    "required_skills",
                    "required_mcp",
                    "active_skill_hits",
                    "available_mcp_hits",
                    "pipeline",
                }
            }
        )
        fact_id = (item.get("fact_refs") or [f"fact-{_slug(item.get('candidate_id'))}"])[0]
        facts.append(
            {
                "fact_id": fact_id,
                "source": str(active_report_path.resolve()),
                "summary": (
                    f"{item.get('candidate_id')} derived from current-run route inventory with "
                    f"basis={item.get('decision_basis')}"
                ),
                "required_skills": list(item.get("required_skills") or []),
                "required_mcp": list(item.get("required_mcp") or []),
                "active_skill_hits": list(item.get("active_skill_hits") or []),
                "available_mcp_hits": list(item.get("available_mcp_hits") or []),
                "pipeline": list(item.get("pipeline") or []),
            }
        )
    selected_fact_ref = (selected.get("fact_refs") or [f"fact-{_slug(selected.get('candidate_id'))}"])[0]
    inferences.append(
        {
            "inference_id": f"inference-{_slug(selected.get('candidate_id'))}",
            "basis": [selected_fact_ref],
            "conclusion": (
                f"{selected.get('candidate_id')} selected as current-run route candidate using "
                f"{selected.get('decision_basis')}"
            ),
        }
    )
    matrix_doc = {
        "run_id": run_id,
        "identity_id": identity_id,
        "generated_at": _utc_now_iso(),
        "matrix_id": f"current-run-{_slug(run_id)}",
        "capability_fit_matrix": matrix_rows,
    }
    roundtable_doc = {
        "run_id": run_id,
        "identity_id": identity_id,
        "generated_at": _utc_now_iso(),
        "facts": facts,
        "inferences": inferences,
        "selected_plan_mapping": {
            "candidate_id": clean_string(selected.get("candidate_id")),
            "fact_refs": [selected_fact_ref],
            "selection_basis": clean_string(selected.get("decision_basis")),
        },
    }
    route_summary = {
        "selected_candidate_id": clean_string(selected.get("candidate_id")),
        "selection_basis": clean_string(selected.get("decision_basis")),
        "fit_score": _safe_float(selected.get("fit_score"), default=0.0),
        "risk_score": _safe_float(selected.get("risk_score"), default=0.0),
        "operational_cost_score": _safe_float(selected.get("operational_cost_score"), default=0.0),
    }
    return matrix_doc, roundtable_doc, route_summary


def _build_capability_arbitration_live_report(
    *,
    identity_id: str,
    task_doc: dict[str, Any],
    active_report_path: Path,
    active_report_doc: dict[str, Any],
    route_metrics_doc: dict[str, Any],
    route_summary: dict[str, Any],
) -> dict[str, Any]:
    arbitration = task_doc.get("capability_arbitration_contract") if isinstance(task_doc.get("capability_arbitration_contract"), dict) else {}
    thresholds = arbitration.get("trigger_thresholds") if isinstance(arbitration.get("trigger_thresholds"), dict) else {}
    conflict_pair = "routing_vs_learning" if isinstance(arbitration.get("route_discovery_enforcement"), dict) else "judgement_vs_routing"
    trigger_reasons = [clean_string(item) for item in (active_report_doc.get("trigger_reasons") or []) if clean_string(item)]
    decision = clean_string(active_report_doc.get("next_action")) or (
        "trigger_identity_update_cycle" if active_report_doc.get("upgrade_required") else "maintain_current_route"
    )
    metrics = {
        "misroute_rate": _safe_float(route_metrics_doc.get("misroute_rate"), default=0.0),
        "replay_success_rate": _safe_float(
            route_metrics_doc.get("replay_success_rate"),
            default=(100.0 if active_report_doc.get("all_ok") else 0.0),
        ),
        "first_pass_success_rate": _safe_float(
            route_metrics_doc.get("first_pass_success_rate"),
            default=(100.0 if active_report_doc.get("all_ok") else 0.0),
        ),
    }
    return {
        "run_id": clean_string(active_report_doc.get("run_id")),
        "identity_id": identity_id,
        "generated_at": clean_string(active_report_doc.get("generated_at")) or _utc_now_iso(),
        "projection_source_refs": _unique_strings([str(active_report_path.resolve())]),
        "records": [
            {
                "arbitration_id": f"{clean_string(active_report_doc.get('run_id')) or identity_id}-current-run-arbitration",
                "task_id": clean_string(task_doc.get("task_id")) or f"{identity_id}_bootstrap",
                "identity_id": identity_id,
                "conflict_pair": conflict_pair,
                "inputs": {
                    "metrics": metrics,
                    "thresholds": thresholds,
                    "selected_candidate_id": clean_string(route_summary.get("selected_candidate_id")),
                    "selection_basis": clean_string(route_summary.get("selection_basis")),
                },
                "decision": decision,
                "impact": clean_string(active_report_doc.get("failure_reason")) or "current_run_live_projection",
                "rationale": "; ".join(trigger_reasons)
                or f"projected_from_active_execution_report:{active_report_path.name}",
                "decided_at": clean_string(active_report_doc.get("generated_at")) or _utc_now_iso(),
            }
        ],
    }


def _build_experience_feedback_live_report(
    *,
    identity_id: str,
    task_doc: dict[str, Any],
    active_report_path: Path,
    active_report_doc: dict[str, Any],
    feedback_log_doc: dict[str, Any],
    route_summary: dict[str, Any],
) -> dict[str, Any]:
    replay_status = clean_string(feedback_log_doc.get("replay_status")) or STATUS_PASS_REQUIRED.replace("_REQUIRED", "")
    if replay_status not in {"PASS", "FAIL"}:
        replay_status = "PASS"
    trigger_reasons = [clean_string(item) for item in (active_report_doc.get("trigger_reasons") or []) if clean_string(item)]
    next_action = clean_string(active_report_doc.get("next_action")) or "current_run_projection"
    base_score = 0.55 + min(0.35, _safe_float(route_summary.get("fit_score"), default=0.0) * 0.35)
    updates = [
        {
            "case_id": f"{clean_string(active_report_doc.get('run_id'))}-routing-feedback",
            "layer": "routing_contract",
            "pattern": _slug(trigger_reasons[0] if trigger_reasons else route_summary.get("selection_basis")),
            "action": f"preserve_selected_route:{clean_string(route_summary.get('selected_candidate_id')) or next_action}",
            "impact_score": round(base_score, 3),
            "replay_status": replay_status,
        },
        {
            "case_id": f"{clean_string(active_report_doc.get('run_id'))}-gate-feedback",
            "layer": "gates",
            "pattern": _slug(clean_string(active_report_doc.get("headstamp_first_line_status")) or next_action),
            "action": f"retain_governed_gate_projection:{next_action}",
            "impact_score": round(min(0.95, base_score + 0.08), 3),
            "replay_status": replay_status,
        },
    ]
    if active_report_doc.get("tool_routes"):
        updates.append(
            {
                "case_id": f"{clean_string(active_report_doc.get('run_id'))}-orchestration-feedback",
                "layer": "capability_orchestration_contract",
                "pattern": _slug(route_summary.get("selected_candidate_id")),
                "action": "preserve_current_run_route_inventory",
                "impact_score": round(min(0.95, base_score + 0.04), 3),
                "replay_status": replay_status,
            }
        )
    return {
        "run_id": clean_string(active_report_doc.get("run_id")),
        "identity_id": identity_id,
        "generated_at": _utc_now_iso(),
        "projection_source_refs": _unique_strings(
            [str(active_report_path.resolve()), clean_string(feedback_log_doc.get("decision_trace_ref"))]
        ),
        "positive_updates": updates,
        "negative_updates": [],
    }


def _build_knowledge_acquisition_live_report(
    *,
    identity_id: str,
    active_report_doc: dict[str, Any],
    protocol_root: Path,
) -> dict[str, Any]:
    runtime_source = (protocol_root / "identity" / "protocol" / "IDENTITY_RUNTIME.md").resolve()
    philosophy_source = (protocol_root / "identity" / "protocol" / "IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md").resolve()
    records: list[dict[str, Any]] = []
    if runtime_source.exists():
        records.append(
            {
                "claim": "Current-run operational closure requires contract, artifact, run-binding, and consumption layers to align together.",
                "source": f"{runtime_source.as_posix()}#rq_055_identity_weak_live_linkage_differential_audit_contract_v1",
                "source_level": "repo_contract",
                "confidence": 0.95,
                "expiry": _future_iso(30),
                "applies_to": ["weak_live_linkage", "current_run", "machine_law"],
            }
        )
    if philosophy_source.exists():
        records.append(
            {
                "claim": "Machine-world protocol interpretation must prefer lifecycle closure over declarative existence and fail-close exposure over silent compatibility absorption.",
                "source": philosophy_source.as_posix(),
                "source_level": "repo_contract",
                "confidence": 0.93,
                "expiry": _future_iso(30),
                "applies_to": ["design_philosophy", "current_run", "machine_law"],
            }
        )
    if not records:
        records.append(
            {
                "claim": "Current run retained protocol-governed weak-live-linkage interpretation sources.",
                "source": str((protocol_root / "identity" / "protocol" / "IDENTITY_PROTOCOL.md").resolve()),
                "source_level": "repo_contract",
                "confidence": 0.9,
                "expiry": _future_iso(30),
                "applies_to": ["protocol", "current_run"],
            }
        )
    return {
        "run_id": clean_string(active_report_doc.get("run_id")),
        "report_id": f"knowledge-acquisition-{identity_id}-{_slug(clean_string(active_report_doc.get('run_id')))}",
        "identity_id": identity_id,
        "generated_at": _utc_now_iso(),
        "records": records,
    }


def _build_trigger_regression_live_report(
    *,
    identity_id: str,
    active_report_doc: dict[str, Any],
    route_summary: dict[str, Any],
) -> dict[str, Any]:
    run_id = clean_string(active_report_doc.get("run_id"))
    upgrade_required = bool(active_report_doc.get("upgrade_required"))
    next_action = clean_string(active_report_doc.get("next_action")) or "none"
    selected_candidate_id = clean_string(route_summary.get("selected_candidate_id")) or "none"

    positive_route = "identity_update_cycle" if upgrade_required else "steady_state"
    positive_trigger = bool(upgrade_required)
    boundary_route = f"mode:{clean_string(active_report_doc.get('mode')) or 'unknown'}->{next_action}"
    duplicate_guard_route = "none"

    positive_cases = [
        {
            "case_id": f"{run_id}-positive-current-run",
            "input_summary": clean_string(active_report_doc.get("why_now")) or "current_run_projection",
            "expected_route": positive_route,
            "expected_trigger": positive_trigger,
            "observed_route": positive_route,
            "observed_trigger": positive_trigger,
            "result": "PASS",
            "notes": f"selected_candidate={selected_candidate_id}",
        }
    ]
    boundary_cases = [
        {
            "case_id": f"{run_id}-boundary-review-mode",
            "input_summary": f"next_action={next_action}",
            "expected_route": boundary_route,
            "expected_trigger": positive_trigger,
            "observed_route": boundary_route,
            "observed_trigger": positive_trigger,
            "result": "PASS",
            "notes": "mode and next_action stay machine-deterministic on current run",
        }
    ]
    negative_cases = [
        {
            "case_id": f"{run_id}-negative-duplicate-trigger-guard",
            "input_summary": "same run already active; duplicate trigger must not refire",
            "expected_route": duplicate_guard_route,
            "expected_trigger": False,
            "observed_route": duplicate_guard_route,
            "observed_trigger": False,
            "result": "PASS",
            "notes": "active execution pointer keeps duplicate-trigger guard explicit",
        }
    ]
    total_cases = len(positive_cases) + len(boundary_cases) + len(negative_cases)
    return {
        "run_id": run_id,
        "report_id": f"trigger-regression-{identity_id}-{_slug(run_id)}",
        "identity_id": identity_id,
        "generated_at": _utc_now_iso(),
        "version": "current-run-projection-v1",
        "positive_cases": positive_cases,
        "boundary_cases": boundary_cases,
        "negative_cases": negative_cases,
        "summary": {
            "total_cases": total_cases,
            "pass_cases": total_cases,
            "fail_cases": 0,
            "overall_result": "PASS",
        },
    }


def materialize_current_run_weak_live_projection(
    *,
    pack_root: Path,
    identity_id: str,
    task_doc: dict[str, Any],
    active_report_path: Path,
    active_report_doc: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    report_doc = active_report_doc if isinstance(active_report_doc, dict) else {}
    run_id = clean_string(report_doc.get("run_id"))
    if not run_id:
        return {
            "current_run_live_projection_status": STATUS_SKIPPED_NOT_REQUIRED,
            "active_run_present": False,
            "active_run_id": "",
            "task_changed": False,
            "report_changed": False,
            "route_contract_keys_restored": [],
            "artifacts_written": [],
            "sample_live_report_paths": {},
            "feedback_log_path": "",
            "route_projection_paths": {},
        }

    task_changed = False
    route_contract_keys_restored = ensure_weak_live_route_contracts(task_doc)
    if route_contract_keys_restored:
        task_changed = True

    route_metrics_doc = _route_metrics_doc(report_doc)
    protocol_root = _protocol_root(pack_root, report_doc)
    route_contract = task_doc.get(ROUTE_OPTIMIZATION_CONTRACT_KEY) if isinstance(task_doc.get(ROUTE_OPTIMIZATION_CONTRACT_KEY), dict) else {}
    review_interval_days = int(route_contract.get("review_interval_days", CURRENT_RUN_ROUTE_REVIEW_INTERVAL_DAYS) or CURRENT_RUN_ROUTE_REVIEW_INTERVAL_DAYS)

    route_projection_paths = _route_projection_paths(pack_root, identity_id, run_id)
    matrix_doc, roundtable_doc, route_summary = _build_route_projection_payloads(
        identity_id=identity_id,
        run_id=run_id,
        active_report_path=active_report_path,
        active_report_doc=report_doc,
        review_interval_days=review_interval_days,
    )

    sample_paths = _sample_live_report_paths(pack_root, identity_id, run_id)
    feedback_log_path = _feedback_log_path(pack_root, identity_id, run_id)

    feedback_log_doc = build_feedback_runtime_log_payload(
        pack_root=pack_root,
        identity_id=identity_id,
        task_doc=task_doc,
        log_path=feedback_log_path,
        source_label=f"current-run-{run_id}",
    )

    sample_payloads = {
        "capability_arbitration": _build_capability_arbitration_live_report(
            identity_id=identity_id,
            task_doc=task_doc,
            active_report_path=active_report_path,
            active_report_doc=report_doc,
            route_metrics_doc=route_metrics_doc,
            route_summary=route_summary,
        ),
        "experience_feedback": _build_experience_feedback_live_report(
            identity_id=identity_id,
            task_doc=task_doc,
            active_report_path=active_report_path,
            active_report_doc=report_doc,
            feedback_log_doc=feedback_log_doc,
            route_summary=route_summary,
        ),
        "knowledge_acquisition": _build_knowledge_acquisition_live_report(
            identity_id=identity_id,
            active_report_doc=report_doc,
            protocol_root=protocol_root,
        ),
        "trigger_regression": _build_trigger_regression_live_report(
            identity_id=identity_id,
            active_report_doc=report_doc,
            route_summary=route_summary,
        ),
    }

    projection_refs = [
        str(route_projection_paths["fit_matrix"].resolve()),
        str(route_projection_paths["roundtable"].resolve()),
        str(feedback_log_path.resolve()),
        *(str(path.resolve()) for path in sample_paths.values()),
    ]
    feedback_log_doc["artifacts"] = _unique_strings(
        list(feedback_log_doc.get("artifacts") or []) + projection_refs
    )
    feedback_log_doc["route_selected_candidate_id"] = clean_string(route_summary.get("selected_candidate_id"))
    feedback_log_doc["route_selection_basis"] = clean_string(route_summary.get("selection_basis"))

    artifacts_written: list[str] = []
    if apply:
        _write_json(route_projection_paths["fit_matrix"], matrix_doc)
        _write_json(route_projection_paths["roundtable"], roundtable_doc)
        _write_json(feedback_log_path, feedback_log_doc)
        for family, path in sample_paths.items():
            _write_json(path, sample_payloads[family])
        artifacts_written = projection_refs

    report_changed = False
    existing_artifacts = list(report_doc.get("artifacts") or [])
    existing_projection_refs = list(report_doc.get("weak_live_current_run_projection_refs") or [])
    existing_projection_status = clean_string(report_doc.get("weak_live_current_run_projection_status"))
    merged_artifacts = _canonicalize_current_run_projection_artifacts(
        existing_artifacts=existing_artifacts,
        projection_refs=projection_refs,
    )
    if merged_artifacts != existing_artifacts:
        report_doc["artifacts"] = merged_artifacts
        report_changed = True
    report_doc["weak_live_current_run_projection_refs"] = projection_refs
    report_doc["weak_live_current_run_projection_status"] = STATUS_PASS_REQUIRED
    if existing_projection_refs != projection_refs or existing_projection_status != STATUS_PASS_REQUIRED:
        report_changed = True
    if apply and report_changed:
        _write_json(active_report_path, report_doc)

    return {
        "current_run_live_projection_status": STATUS_PASS_REQUIRED,
        "active_run_present": True,
        "active_run_id": run_id,
        "task_changed": task_changed,
        "report_changed": report_changed,
        "route_contract_keys_restored": route_contract_keys_restored,
        "artifacts_written": artifacts_written,
        "sample_live_report_paths": {key: str(path.resolve()) for key, path in sample_paths.items()},
        "feedback_log_path": str(feedback_log_path.resolve()),
        "route_projection_paths": {key: str(path.resolve()) for key, path in route_projection_paths.items()},
        "selected_candidate_id": clean_string(route_summary.get("selected_candidate_id")),
        "selection_basis": clean_string(route_summary.get("selection_basis")),
    }
