#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import load_actor_binding, resolve_actor_id
from resolve_identity_context import resolve_identity
from tool_vendor_governance_common import load_json


@dataclass
class StampContext:
    actor_id: str
    identity_id: str
    catalog_path: Path
    pack_path: Path
    resolved_scope: str
    lock_state: str
    lease_id: str
    source_domain: str
    catalog_ref: str
    pack_ref: str


ALLOWED_DISCLOSURE_LEVELS = {"minimal", "standard", "verbose", "audit"}
DEFAULT_DISCLOSURE_LEVEL = "standard"
ALLOWED_WORK_LAYERS = {"protocol", "instance", "dual"}
ALLOWED_SOURCE_LAYERS = {"project", "global", "env", "auto"}
LAYER_INTENT_STRICT_THRESHOLD = 0.75
DEFAULT_WORK_LAYER = "instance"

PROTOCOL_TRIGGER_FLAG_PATTERNS = (
    re.compile(r"\bprotocol[_\-\s]?trigger(?:ed)?\s*[:=]\s*(true|1|yes|on)\b"),
    re.compile(r"\bwork[_\-\s]?layer\s*[:=]\s*protocol\b"),
)
PROTOCOL_TRIGGER_ERROR_CODE_PATTERN = re.compile(r"\bIP-[A-Z0-9-]{3,}\b")
PROTOCOL_TRIGGER_KEYWORDS = {
    "protocol",
    "governance",
    "contract",
    "validator",
    "gate",
    "audit",
    "spec",
    "ssot",
    "hotfix",
    "release",
    "readiness",
    "required",
    "fail",
    "failure",
    "blocker",
    "fail-closed",
    "identity-protocol",
    "协议",
    "治理",
    "契约",
    "校验",
    "门禁",
    "审计",
    "升级",
    "发布",
    "阻断",
}
PROTOCOL_TRIGGER_ACTIONS = {
    "upgrade",
    "fix",
    "repair",
    "remediate",
    "patch",
    "wire",
    "close",
    "enforce",
    "block",
    "rollback",
    "收口",
    "修复",
    "接线",
    "落地",
    "治理",
    "阻断",
    "回放",
}

LAYER_LITERAL_META_TOKENS = (
    "identity-context:",
    "layer-context:",
)


def _has_protocol_lane_directive(text: str) -> bool:
    raw = str(text or "").strip().lower()
    if not raw:
        return False
    directive_patterns = (
        re.compile(r"\bprotocol\s+(lane|layer|track)\b"),
        re.compile(r"\bprotocol[_\-\s]?lane\b"),
        re.compile(r"(协议层|协议轨|协议通道|协议lane)"),
        re.compile(r"(按|走|切到|进入)\s*protocol"),
    )
    return any(p.search(raw) for p in directive_patterns)


def _detect_repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    for parent in [base, *base.parents]:
        if (parent / ".git").exists():
            return parent.resolve()
    return base


def _project_identity_home(repo_root: Path) -> Path:
    if repo_root.name == "identity-protocol-local":
        return (repo_root.parent / ".agents" / "identity").resolve()
    return (repo_root / ".agents" / "identity").resolve()


def _global_identity_home() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "identity").resolve()
    return (Path.home() / ".codex" / "identity").resolve()


def _source_domain(catalog_path: Path, explicit_catalog: bool, *, repo_root_hint: Path | None = None) -> str:
    probe = repo_root_hint if repo_root_hint is not None else catalog_path.parent
    repo_root = _detect_repo_root(probe)
    project_home = _project_identity_home(repo_root)
    global_home = _global_identity_home()
    c = catalog_path.resolve()
    try:
        c.relative_to(project_home)
        return "project"
    except Exception:
        pass
    try:
        c.relative_to(global_home)
        return "global"
    except Exception:
        pass
    return "env" if explicit_catalog else "auto"


def _ref_token(path: Path) -> str:
    norm = str(path.resolve())
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]
    return f"{path.name}#{h}"


def _session_pointer_path(catalog_path: Path) -> Path:
    return (catalog_path.parent / "session" / "active_identity.json").resolve()


def _session_data(catalog_path: Path, actor_id: str, identity_id: str) -> dict[str, Any]:
    actor_binding = load_actor_binding(catalog_path, actor_id, identity_id=identity_id)
    if actor_binding:
        payload = dict(actor_binding)
        payload["session_pointer_source"] = "actor"
        return payload
    p = _session_pointer_path(catalog_path)
    if not p.exists():
        return {}
    try:
        data = load_json(p)
    except Exception:
        return {}
    if isinstance(data, dict):
        data["session_pointer_source"] = "canonical"
        return data
    return {}


def _lock_state(identity_id: str, pointer: dict[str, Any]) -> str:
    if not pointer:
        return "UNKNOWN"
    active_id = str(pointer.get("identity_id", "")).strip()
    if not active_id:
        return "UNKNOWN"
    if active_id == identity_id:
        return "LOCK_MATCH"
    return "LOCK_MISMATCH"


def _lease_id(pointer: dict[str, Any]) -> str:
    lease = str(pointer.get("lease_id", "")).strip()
    if lease:
        return lease
    run_id = str(pointer.get("run_id", "")).strip()
    if run_id:
        return f"lease-{run_id[:16]}"
    lock_hash = str(pointer.get("state_hash", "")).strip()
    if lock_hash:
        return f"lease-{lock_hash[:10]}"
    return "lease-unknown"


def resolve_stamp_context(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    actor_id: str = "",
    explicit_catalog: bool = True,
) -> StampContext:
    actor = resolve_actor_id(actor_id)
    resolved = resolve_identity(
        identity_id,
        repo_catalog_path.resolve(),
        catalog_path.resolve(),
        allow_conflict=True,
    )
    pack_path = Path(str(resolved.get("pack_path", "")).strip()).expanduser().resolve()
    resolved_scope = str(resolved.get("resolved_scope", "")).strip().upper() or "UNKNOWN"
    pointer = _session_data(catalog_path, actor, identity_id)
    lock_state = _lock_state(identity_id, pointer)
    lease_id = _lease_id(pointer)
    source = _source_domain(
        catalog_path,
        explicit_catalog=explicit_catalog,
        repo_root_hint=repo_catalog_path.parent,
    )
    return StampContext(
        actor_id=actor,
        identity_id=identity_id,
        catalog_path=catalog_path.resolve(),
        pack_path=pack_path,
        resolved_scope=resolved_scope,
        lock_state=lock_state,
        lease_id=lease_id,
        source_domain=source,
        catalog_ref=_ref_token(catalog_path.resolve()),
        pack_ref=_ref_token(pack_path),
    )


def lease_id_short(lease_id: str) -> str:
    token = str(lease_id or "").strip()
    if not token:
        return "lease-unknown"
    return token[:12]


def normalize_disclosure_level(
    level: str,
    *,
    default: str = DEFAULT_DISCLOSURE_LEVEL,
    allow_empty: bool = False,
) -> str:
    raw = str(level or "").strip().lower()
    if not raw and allow_empty:
        return ""
    if raw in {"concise", "short", "lite"}:
        raw = "minimal"
    elif raw in {"default"}:
        raw = "standard"
    elif raw in {"full", "detailed"}:
        raw = "verbose"
    if raw in ALLOWED_DISCLOSURE_LEVELS:
        return raw
    fallback = str(default or "").strip().lower()
    if not fallback and allow_empty:
        return ""
    return fallback if fallback in ALLOWED_DISCLOSURE_LEVELS else DEFAULT_DISCLOSURE_LEVEL


def infer_disclosure_level_from_stamp_fields(fields: dict[str, str]) -> str:
    if str(fields.get("lease", "")).strip():
        return "verbose"
    if str(fields.get("catalog_ref", "")).strip() or str(fields.get("pack_ref", "")).strip():
        return "standard"
    return "minimal"


def _infer_trigger_scope(trigger_text: str) -> str:
    text = str(trigger_text or "").strip().lower()
    if not text:
        return ""
    if any(x in text for x in ("once", "one-time", "one shot", "single response", "本轮", "一次", "单次")):
        return "once"
    if any(x in text for x in ("session", "会话", "持续", "一直", "后续")):
        return "session"
    return ""


def _normalize_work_layer(value: str, *, fallback: str = "protocol") -> str:
    v = str(value or "").strip().lower()
    if v in ALLOWED_WORK_LAYERS:
        return v
    fb = str(fallback or "").strip().lower()
    return fb if fb in ALLOWED_WORK_LAYERS else "protocol"


def _normalize_source_layer(value: str, *, fallback: str = "auto") -> str:
    v = str(value or "").strip().lower()
    if v in ALLOWED_SOURCE_LAYERS:
        return v
    fb = str(fallback or "").strip().lower()
    return fb if fb in ALLOWED_SOURCE_LAYERS else "auto"


def _detect_protocol_trigger(intent_text: str) -> dict[str, Any]:
    text = str(intent_text or "").strip().lower()
    if not text:
        return {
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
        }

    reasons: list[str] = []
    for pat in PROTOCOL_TRIGGER_FLAG_PATTERNS:
        if pat.search(text):
            reasons.append("explicit_protocol_trigger_flag")
            break

    if PROTOCOL_TRIGGER_ERROR_CODE_PATTERN.search(text):
        reasons.append("protocol_error_code_signal")

    if _has_protocol_lane_directive(text):
        reasons.append("protocol_lane_directive")

    tokens = set(re.findall(r"[a-zA-Z_]+|[\u4e00-\u9fff]{1,4}", text))
    keyword_hits = sum(1 for k in PROTOCOL_TRIGGER_KEYWORDS if k in text or k in tokens)
    action_hits = sum(1 for k in PROTOCOL_TRIGGER_ACTIONS if k in text or k in tokens)
    if keyword_hits > 0 and action_hits > 0:
        reasons.append("protocol_keyword_action_pair")
    elif keyword_hits >= 2:
        reasons.append("protocol_keyword_cluster")

    unique_reasons = sorted(set(reasons))
    triggered = len(unique_reasons) > 0
    confidence = 0.0
    if triggered:
        confidence = min(0.98, 0.55 + 0.15 * len(unique_reasons))
    return {
        "protocol_triggered": triggered,
        "protocol_trigger_reasons": unique_reasons,
        "protocol_trigger_confidence": confidence,
    }


def _sanitize_layer_intent_text(intent_text: str) -> str:
    raw = str(intent_text or "").strip()
    if not raw:
        return ""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if any(tok in lower for tok in LAYER_LITERAL_META_TOKENS):
            continue
        lines.append(stripped)
    cleaned = "\n".join([x for x in lines if x]).strip()
    return cleaned or raw


def _literal_match_in_interrogative_context(text: str, start: int, end: int) -> bool:
    s = max(0, int(start) - 64)
    e = min(len(text), int(end) + 64)
    window = text[s:e]
    if ("?" in window) or ("？" in window):
        return True
    return bool(re.search(r"\b(why|how|what)\b|为什么|为何", window))


def resolve_layer_intent(
    *,
    explicit_work_layer: str = "",
    explicit_source_layer: str = "",
    intent_text: str = "",
    default_work_layer: str = DEFAULT_WORK_LAYER,
    default_source_layer: str = "auto",
) -> dict[str, Any]:
    resolved_source = _normalize_source_layer(explicit_source_layer, fallback=default_source_layer)
    fallback_work = _normalize_work_layer(default_work_layer, fallback=DEFAULT_WORK_LAYER)
    text = _sanitize_layer_intent_text(intent_text).strip().lower()
    trigger = _detect_protocol_trigger(text)
    base_triggered = bool(trigger.get("protocol_triggered", False))
    base_trigger_reasons = list(trigger.get("protocol_trigger_reasons") or [])
    trigger_confidence = float(trigger.get("protocol_trigger_confidence", 0.0) or 0.0)

    def _result(
        *,
        work_layer: str,
        confidence: float,
        intent_source: str,
        fallback_reason: str,
        protocol_triggered: bool = False,
        protocol_trigger_reasons: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_work = _normalize_work_layer(work_layer, fallback=fallback_work)
        applied_trigger = bool(protocol_triggered and resolved_work in {"protocol", "dual"})
        reasons = sorted(set(protocol_trigger_reasons or [])) if applied_trigger else []
        return {
            "resolved_work_layer": resolved_work,
            "resolved_source_layer": resolved_source,
            "intent_confidence": confidence,
            "intent_source": intent_source,
            "fallback_reason": fallback_reason,
            "strict_threshold": LAYER_INTENT_STRICT_THRESHOLD,
            "protocol_triggered": applied_trigger,
            "protocol_trigger_reasons": reasons,
            "protocol_trigger_confidence": trigger_confidence if applied_trigger else 0.0,
        }

    explicit_work = str(explicit_work_layer or "").strip().lower()
    if explicit_work in ALLOWED_WORK_LAYERS:
        if explicit_work == "protocol":
            reasons = sorted(set([*base_trigger_reasons, "explicit_work_layer_protocol"]))
            return _result(
                work_layer="protocol",
                confidence=1.0,
                intent_source="explicit_arg",
                fallback_reason="",
                protocol_triggered=True,
                protocol_trigger_reasons=reasons,
            )
        return _result(
            work_layer=explicit_work,
            confidence=1.0,
            intent_source="explicit_arg",
            fallback_reason="",
            protocol_triggered=base_triggered,
            protocol_trigger_reasons=base_trigger_reasons,
        )

    if not text:
        return _result(
            work_layer=fallback_work,
            confidence=0.0,
            intent_source="default_fallback",
            fallback_reason="intent_text_missing",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )

    m_work = re.search(r"(work[_\-\s]?layer)\s*[:=]\s*(protocol|instance|dual)\b", text)
    m_source = re.search(r"(source[_\-\s]?layer)\s*[:=]\s*(project|global|env|auto)\b", text)
    if m_source:
        resolved_source = _normalize_source_layer(m_source.group(2), fallback=resolved_source)
    if m_work:
        candidate = _normalize_work_layer(m_work.group(2), fallback=fallback_work)
        protocol_keyword_detected = any((k in text) for k in PROTOCOL_TRIGGER_KEYWORDS)
        if (
            candidate == "instance"
            and protocol_keyword_detected
            and _literal_match_in_interrogative_context(text, m_work.start(), m_work.end())
        ):
            reasons = [*base_trigger_reasons] if base_trigger_reasons else ["protocol_keyword_interrogative_override"]
            return _result(
                work_layer="protocol",
                confidence=max(0.8, trigger_confidence),
                intent_source="natural_language",
                fallback_reason="",
                protocol_triggered=True,
                protocol_trigger_reasons=["protocol_context_instance_literal_override", *reasons],
            )
        if candidate == "protocol" and not base_triggered:
            return _result(
                work_layer=fallback_work,
                confidence=0.45,
                intent_source="default_fallback",
                fallback_reason="protocol_trigger_not_met",
                protocol_triggered=False,
                protocol_trigger_reasons=[],
            )
        return _result(
            work_layer=candidate,
            confidence=0.99,
            intent_source="natural_language",
            fallback_reason="",
            protocol_triggered=(candidate == "protocol") or base_triggered,
            protocol_trigger_reasons=(["explicit_layer_tuple_protocol"] if candidate == "protocol" else []) + base_trigger_reasons,
        )

    # Deterministic dynamic rule: protocol_actions / instance_actions counters.
    m_protocol_actions = re.search(r"protocol[_\-\s]?actions?\s*[:=]\s*(-?\d+)\b", text)
    m_instance_actions = re.search(r"instance[_\-\s]?actions?\s*[:=]\s*(-?\d+)\b", text)
    if m_protocol_actions or m_instance_actions:
        protocol_actions = int(m_protocol_actions.group(1)) if m_protocol_actions else 0
        instance_actions = int(m_instance_actions.group(1)) if m_instance_actions else 0
        protocol_actions = max(0, protocol_actions)
        instance_actions = max(0, instance_actions)
        if protocol_actions > 0 and instance_actions == 0:
            return _result(
                work_layer="protocol",
                confidence=0.98,
                intent_source="natural_language",
                fallback_reason="",
                protocol_triggered=True,
                protocol_trigger_reasons=["protocol_actions_counter_positive", *base_trigger_reasons],
            )
        if protocol_actions == 0 and instance_actions > 0:
            return _result(
                work_layer="instance",
                confidence=0.98,
                intent_source="natural_language",
                fallback_reason="",
                protocol_triggered=base_triggered,
                protocol_trigger_reasons=base_trigger_reasons,
            )
        if protocol_actions > 0 and instance_actions > 0:
            return _result(
                work_layer="dual",
                confidence=0.98,
                intent_source="natural_language",
                fallback_reason="",
                protocol_triggered=True,
                protocol_trigger_reasons=["dual_action_counters_positive", *base_trigger_reasons],
            )
        return _result(
            work_layer=fallback_work,
            confidence=0.4,
            intent_source="default_fallback",
            fallback_reason="zero_action_counters",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )

    instance_keywords = {
        "instance",
        "runtime",
        "delivery",
        "deliver",
        "execution",
        "execute",
        "run",
        "apply",
        "operate",
        "operation",
        "business",
        "实例",
        "执行",
        "交付",
        "业务",
    }
    protocol_keywords = {
        "protocol",
        "governance",
        "contract",
        "validator",
        "gate",
        "audit",
        "spec",
        "ssot",
        "协议",
        "治理",
        "审计",
        "规范",
    }
    dual_keywords = {"dual", "both", "hybrid", "双层", "两层", "双轨"}
    tokens = set(re.findall(r"[a-zA-Z_]+|[\u4e00-\u9fff]{1,4}", text))

    if any(k in text for k in dual_keywords):
        return _result(
            work_layer="dual",
            confidence=0.9,
            intent_source="natural_language",
            fallback_reason="",
            protocol_triggered=base_triggered,
            protocol_trigger_reasons=base_trigger_reasons,
        )

    score_instance = sum(1 for k in instance_keywords if k in text or k in tokens)
    score_protocol = sum(1 for k in protocol_keywords if k in text or k in tokens)

    if score_instance == 0 and score_protocol == 0:
        return _result(
            work_layer=fallback_work,
            confidence=0.25,
            intent_source="default_fallback",
            fallback_reason="no_intent_signal",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )

    if score_instance > 0 and score_protocol > 0:
        protocol_directive = _has_protocol_lane_directive(text)
        protocol_strong_trigger = bool(
            {"explicit_protocol_trigger_flag", "protocol_error_code_signal"} & set(base_trigger_reasons)
        )
        protocol_signal_dominates = score_protocol > score_instance
        if base_triggered and (protocol_directive or protocol_strong_trigger or protocol_signal_dominates):
            reasons = list(base_trigger_reasons)
            if protocol_directive:
                reasons.append("protocol_lane_directive_mixed_signal")
            elif protocol_strong_trigger:
                reasons.append("protocol_strong_trigger_mixed_signal")
            else:
                reasons.append("protocol_signal_dominates_mixed_signal")
            confidence = max(
                0.78,
                min(
                    0.98,
                    0.56 + 0.06 * score_protocol + 0.02 * len(set(reasons)),
                ),
            )
            return _result(
                work_layer="protocol",
                confidence=confidence,
                intent_source="natural_language",
                fallback_reason="",
                protocol_triggered=True,
                protocol_trigger_reasons=reasons,
            )
        return _result(
            work_layer=fallback_work,
            confidence=0.45,
            intent_source="default_fallback",
            fallback_reason="ambiguous_intent_signal",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )

    if score_instance > 0:
        confidence = min(0.95, 0.55 + 0.1 * score_instance)
        if confidence < LAYER_INTENT_STRICT_THRESHOLD:
            return _result(
                work_layer=fallback_work,
                confidence=confidence,
                intent_source="default_fallback",
                fallback_reason="instance_intent_low_confidence",
                protocol_triggered=False,
                protocol_trigger_reasons=[],
            )
        return _result(
            work_layer="instance",
            confidence=confidence,
            intent_source="natural_language",
            fallback_reason="",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )

    # protocol-only signal: only allow protocol layer when protocol trigger conditions are met.
    if not base_triggered:
        return _result(
            work_layer=fallback_work,
            confidence=0.5,
            intent_source="default_fallback",
            fallback_reason="protocol_trigger_not_met",
            protocol_triggered=False,
            protocol_trigger_reasons=[],
        )
    confidence = max(0.8, min(0.98, 0.55 + 0.08 * score_protocol))
    return _result(
        work_layer="protocol",
        confidence=confidence,
        intent_source="natural_language",
        fallback_reason="",
        protocol_triggered=True,
        protocol_trigger_reasons=base_trigger_reasons or ["protocol_signal_high_confidence"],
    )


def parse_disclosure_level_trigger(trigger_text: str) -> tuple[str, float]:
    text = str(trigger_text or "").strip().lower()
    if not text:
        return "", 0.0
    if any(x in text for x in ("minimal", "concise", "short", "简洁", "简版", "精简")):
        return "minimal", 0.95
    if any(x in text for x in ("standard", "default", "标准", "默认")):
        return "standard", 0.95
    if any(x in text for x in ("verbose", "full", "detailed", "全量", "详细", "完整")):
        return "verbose", 0.95
    if any(x in text for x in ("audit", "internal", "审计", "内部")):
        return "audit", 0.95
    m = re.search(r"(minimal|standard|verbose|audit)", text)
    if m:
        return normalize_disclosure_level(m.group(1)), 0.9
    return "", 0.0


def _response_stamp_profile_state_path(catalog_path: Path, actor_id: str) -> Path:
    token = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(actor_id or "unknown"))
    return (catalog_path.parent / "session" / "response-stamp-profiles" / f"{token}.json").resolve()


def _load_task_response_stamp_profile(ctx: StampContext) -> dict[str, Any]:
    task_path = (ctx.pack_path / "CURRENT_TASK.json").resolve()
    if not task_path.exists():
        return {}
    try:
        doc = load_json(task_path)
    except Exception:
        return {}
    profile = doc.get("response_stamp_profile")
    return profile if isinstance(profile, dict) else {}


def _load_response_stamp_profile_state(ctx: StampContext) -> dict[str, Any]:
    p = _response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)
    if not p.exists():
        return {}
    try:
        data = load_json(p)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _persist_response_stamp_profile_state(ctx: StampContext, *, level: str, trigger_text: str) -> Path:
    p = _response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "actor_id": ctx.actor_id,
        "identity_id": ctx.identity_id,
        "disclosure_level": normalize_disclosure_level(level),
        "trigger_text": str(trigger_text or "").strip(),
        "trigger_source": "natural_language",
        "scope": "session",
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def resolve_disclosure_level(
    ctx: StampContext,
    *,
    explicit_level: str = "",
    trigger_text: str = "",
    trigger_scope: str = "",
    persist_session_trigger: bool = True,
) -> dict[str, Any]:
    normalized_explicit = normalize_disclosure_level(explicit_level, default="", allow_empty=True)
    if normalized_explicit:
        return {
            "disclosure_level": normalized_explicit,
            "disclosure_source": "explicit_arg",
            "trigger_applied": False,
            "trigger_scope": "",
            "trigger_text": "",
            "trigger_confidence": 1.0,
            "session_profile_path": "",
        }

    parsed_level, confidence = parse_disclosure_level_trigger(trigger_text)
    normalized_scope = str(trigger_scope or "").strip().lower()
    if normalized_scope not in {"once", "session"}:
        normalized_scope = _infer_trigger_scope(trigger_text)
    if parsed_level:
        profile_path = ""
        if normalized_scope == "session" and persist_session_trigger:
            profile_path = str(_persist_response_stamp_profile_state(ctx, level=parsed_level, trigger_text=trigger_text))
        return {
            "disclosure_level": parsed_level,
            "disclosure_source": "trigger_session" if normalized_scope == "session" else "trigger_once",
            "trigger_applied": True,
            "trigger_scope": normalized_scope or "once",
            "trigger_text": str(trigger_text or "").strip(),
            "trigger_confidence": confidence,
            "session_profile_path": profile_path,
        }

    session_state = _load_response_stamp_profile_state(ctx)
    session_level = normalize_disclosure_level(
        str(session_state.get("disclosure_level", "")).strip(),
        default="",
        allow_empty=True,
    )
    if session_level:
        return {
            "disclosure_level": session_level,
            "disclosure_source": "session_state",
            "trigger_applied": False,
            "trigger_scope": str(session_state.get("scope", "session")).strip() or "session",
            "trigger_text": str(session_state.get("trigger_text", "")).strip(),
            "trigger_confidence": 1.0,
            "session_profile_path": str(_response_stamp_profile_state_path(ctx.catalog_path, ctx.actor_id)),
        }

    task_profile = _load_task_response_stamp_profile(ctx)
    task_level = normalize_disclosure_level(
        str(task_profile.get("disclosure_level", "")).strip(),
        default="",
        allow_empty=True,
    )
    if task_level:
        return {
            "disclosure_level": task_level,
            "disclosure_source": "task_profile",
            "trigger_applied": False,
            "trigger_scope": "",
            "trigger_text": "",
            "trigger_confidence": 1.0,
            "session_profile_path": "",
        }

    return {
        "disclosure_level": DEFAULT_DISCLOSURE_LEVEL,
        "disclosure_source": "default",
        "trigger_applied": False,
        "trigger_scope": "",
        "trigger_text": "",
        "trigger_confidence": 1.0,
        "session_profile_path": "",
    }


def render_external_stamp(ctx: StampContext, *, disclosure_level: str = DEFAULT_DISCLOSURE_LEVEL) -> str:
    return render_external_stamp_with_layer_context(ctx, disclosure_level=disclosure_level)


def render_external_stamp_with_layer_context(
    ctx: StampContext,
    *,
    disclosure_level: str = DEFAULT_DISCLOSURE_LEVEL,
    work_layer: str = DEFAULT_WORK_LAYER,
    source_layer: str = "",
) -> str:
    level = normalize_disclosure_level(disclosure_level)
    wl = str(work_layer or "").strip().lower() or DEFAULT_WORK_LAYER
    if wl not in ALLOWED_WORK_LAYERS:
        wl = DEFAULT_WORK_LAYER
    sl = str(source_layer or "").strip().lower() or ctx.source_domain
    if sl not in ALLOWED_SOURCE_LAYERS:
        sl = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"
    parts = [
        f"actor_id={ctx.actor_id}",
        f"identity_id={ctx.identity_id}",
    ]
    if level in {"standard", "verbose", "audit"}:
        parts.append(f"catalog_ref={ctx.catalog_ref}")
        parts.append(f"pack_ref={ctx.pack_ref}")
    parts.extend(
        [
            f"scope={ctx.resolved_scope}",
            f"lock={ctx.lock_state}",
            f"source={ctx.source_domain}",
        ]
    )
    if level in {"verbose", "audit"}:
        parts.append(f"lease={lease_id_short(ctx.lease_id)}")
    return (
        "Identity-Context: "
        + "; ".join(parts)
        + f" | Layer-Context: work_layer={wl}; source_layer={sl}"
    )


def render_internal_stamp(ctx: StampContext) -> str:
    return (
        "Identity-Context-Internal: "
        f"actor_id={ctx.actor_id}; "
        f"identity_id={ctx.identity_id}; "
        f"catalog_path={ctx.catalog_path}; "
        f"resolved_pack_path={ctx.pack_path}; "
        f"scope={ctx.resolved_scope}; "
        f"lock={ctx.lock_state}; "
        f"lease={lease_id_short(ctx.lease_id)}; "
        f"source={ctx.source_domain}"
    )


def render_structured_context(
    ctx: StampContext,
    *,
    work_layer: str = DEFAULT_WORK_LAYER,
    source_layer: str = "",
) -> dict[str, Any]:
    wl = str(work_layer or "").strip().lower() or DEFAULT_WORK_LAYER
    if wl not in ALLOWED_WORK_LAYERS:
        wl = DEFAULT_WORK_LAYER
    sl = str(source_layer or "").strip().lower() or ctx.source_domain
    if sl not in ALLOWED_SOURCE_LAYERS:
        sl = ctx.source_domain if ctx.source_domain in ALLOWED_SOURCE_LAYERS else "auto"
    return {
        "actor_id": ctx.actor_id,
        "identity_id": ctx.identity_id,
        "catalog_ref": ctx.catalog_ref,
        "pack_ref": ctx.pack_ref,
        "catalog_path": str(ctx.catalog_path),
        "resolved_pack_path": str(ctx.pack_path),
        "scope": ctx.resolved_scope,
        "lock_state": ctx.lock_state,
        "lease_id": ctx.lease_id,
        "lease_id_short": lease_id_short(ctx.lease_id),
        "work_layer": wl,
        "source_layer": sl,
        "source_domain": ctx.source_domain,
    }


def _parse_kv_pairs(fragment: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pairs = [x.strip() for x in str(fragment or "").split(";") if x.strip()]
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def parse_identity_context_stamp(stamp_line: str) -> dict[str, Any]:
    raw = str(stamp_line or "").strip()
    if not raw.startswith("Identity-Context:"):
        return {}

    tail_marker = "| Layer-Context:"
    identity_segment = raw
    layer_segment = ""
    has_layer_context = False
    if tail_marker in raw:
        identity_segment, layer_segment = raw.split(tail_marker, 1)
        has_layer_context = True

    identity_body = identity_segment.split(":", 1)[1].strip()
    fields = _parse_kv_pairs(identity_body)
    layer_fields = _parse_kv_pairs(layer_segment.strip()) if layer_segment else {}
    fields.update(layer_fields)

    # Legacy compatibility: old stamps may only carry source_layer in the main block.
    if not str(fields.get("source", "")).strip() and str(fields.get("source_layer", "")).strip():
        fields["source"] = str(fields.get("source_layer", "")).strip()
    if not str(fields.get("source_layer", "")).strip() and str(fields.get("source", "")).strip():
        fields["source_layer"] = str(fields.get("source", "")).strip()

    fields["_has_layer_context"] = has_layer_context
    fields["_raw_identity_segment"] = identity_segment.strip()
    fields["_raw_layer_segment"] = layer_segment.strip()
    return fields


def blocker_receipt(
    *,
    error_code: str,
    expected_identity_id: str,
    actual_identity_id: str,
    source_domain: str,
    resolver_ref: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "error_code": str(error_code).strip(),
        "expected_identity_id": str(expected_identity_id).strip(),
        "actual_identity_id": str(actual_identity_id).strip(),
        "source_domain": str(source_domain).strip(),
        "resolver_ref": str(resolver_ref).strip(),
        "next_action": str(next_action).strip(),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
