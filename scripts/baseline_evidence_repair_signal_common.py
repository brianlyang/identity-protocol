from __future__ import annotations

from typing import Any

PROTOCOL_REVIEW_EVIDENCE_MISSING_SIGNAL = "no protocol review evidence file matched"
ROLE_BINDING_EVIDENCE_MISSING_SIGNAL = "role-binding evidence not found"
ROLE_BINDING_EVIDENCE_STALE_SIGNAL = "role-binding evidence is stale"


def detect_baseline_evidence_repair_needs(text: Any) -> dict[str, Any]:
    merged = str(text or "")
    repair_protocol = PROTOCOL_REVIEW_EVIDENCE_MISSING_SIGNAL in merged
    role_binding_signals = [
        signal
        for signal in (
            ROLE_BINDING_EVIDENCE_MISSING_SIGNAL,
            ROLE_BINDING_EVIDENCE_STALE_SIGNAL,
        )
        if signal in merged
    ]
    return {
        "repair_protocol": repair_protocol,
        "repair_role_binding": bool(role_binding_signals),
        "detected_signals": role_binding_signals
        + ([PROTOCOL_REVIEW_EVIDENCE_MISSING_SIGNAL] if repair_protocol else []),
    }
