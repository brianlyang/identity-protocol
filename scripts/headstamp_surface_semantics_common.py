#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF = (
    "identity/protocol/plugins/templates/headstamp-surface-semantics.matrix_v1.json"
)

NATIVE_CHAT_ASSISTANT_VISIBLE_SURFACE_ID = "native_chat_assistant_visible"
GOVERNED_WRAPPER_VISIBLE_SURFACE_ID = "governed_wrapper_visible"
EXPLANATORY_HOST_NATIVE_ENVELOPE_SURFACE_ID = "explanatory_host_native_envelope"
CONTROLLED_RUNTIME_ARTIFACT_SURFACE_ID = "controlled_runtime_artifact"

SURFACE_ROW_KEYS = (
    "surface_id",
    "surface_label",
    "surface_class",
    "visible_order",
    "primary_human_literal",
    "machine_literal",
    "proof_owner",
    "attestation_mode",
    "next_hop_rule",
    "failure_visibility_rule",
)

SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_headstamp_surface_semantics_template(
    template_ref: str = "",
    *,
    repo_root: str | Path | None = None,
) -> tuple[dict[str, Any], Path]:
    resolved_ref = str(template_ref or DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF).strip()
    if resolved_ref and Path(resolved_ref).is_absolute():
        template_path = Path(resolved_ref).expanduser().resolve()
    else:
        base_root = (
            Path(repo_root).expanduser().resolve()
            if repo_root is not None and str(repo_root).strip()
            else PROTOCOL_ROOT
        )
        template_path = (base_root / resolved_ref).resolve()
    template_doc = _load_json_if_exists(template_path)
    return template_doc, template_path


def normalize_headstamp_surface_row(row: Any) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    normalized: dict[str, Any] = {}
    for key in SURFACE_ROW_KEYS:
        value = source.get(key)
        if isinstance(value, list):
            normalized[key] = [str(item).strip() for item in value if str(item).strip()]
        else:
            normalized[key] = str(value or "").strip()
    return normalized


def _surface_row_map(template_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in template_doc.get("surface_semantics_matrix") or []:
        row = normalize_headstamp_surface_row(item)
        surface_id = str(row.get("surface_id", "")).strip()
        if surface_id:
            out[surface_id] = row
    return out


def infer_visible_headstamp_surface_id(
    *,
    render_surface: str = "",
    machine_payload: dict[str, Any] | None = None,
) -> str:
    surface = str(render_surface or "").strip().lower() or "operator"
    if surface == "native-chat":
        return NATIVE_CHAT_ASSISTANT_VISIBLE_SURFACE_ID

    payload = machine_payload if isinstance(machine_payload, dict) else {}
    verification_source = str(payload.get("verification_source", "")).strip()
    closure_blocker_scope = str(payload.get("closure_blocker_scope", "")).strip().upper()
    surface_class = str(payload.get("surface_class", "")).strip()
    attested_token = payload.get(
        "current_chat_surface_native_machine_attested",
        payload.get("current_surface_native_machine_attested", ""),
    )
    attested = str(attested_token).strip().lower()

    if (
        verification_source == "not_claimed"
        or closure_blocker_scope == "EXCLUDED_NON_BLOCKING"
        or surface_class == "host_native_chat_panel"
        or attested == "false"
    ):
        return EXPLANATORY_HOST_NATIVE_ENVELOPE_SURFACE_ID
    return GOVERNED_WRAPPER_VISIBLE_SURFACE_ID


def build_headstamp_surface_semantics_payload(
    *,
    render_surface: str = "",
    machine_payload: dict[str, Any] | None = None,
    template_ref: str = "",
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    template_doc, template_path = load_headstamp_surface_semantics_template(
        template_ref,
        repo_root=repo_root,
    )
    template_rows = _surface_row_map(template_doc)
    visible_surface_id = infer_visible_headstamp_surface_id(
        render_surface=render_surface,
        machine_payload=machine_payload,
    )
    artifact_surface_id = CONTROLLED_RUNTIME_ARTIFACT_SURFACE_ID

    stale_reasons: list[str] = []
    visible_surface = template_rows.get(visible_surface_id)
    artifact_surface = template_rows.get(artifact_surface_id)
    if not visible_surface:
        stale_reasons.append(f"template_surface_missing:{visible_surface_id}")
    if not artifact_surface:
        stale_reasons.append(f"template_surface_missing:{artifact_surface_id}")

    status = STATUS_FAIL_REQUIRED if stale_reasons else STATUS_PASS_REQUIRED
    return {
        "headstamp_surface_semantics_status": status,
        "template_ref": str(template_ref or DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF).strip()
        or DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF,
        "template_path": str(template_path),
        "template_id": str(template_doc.get("template_id", "")).strip(),
        "template_version": str(template_doc.get("version", "")).strip(),
        "render_surface": str(render_surface or "").strip().lower() or "operator",
        "visible_surface_id": visible_surface_id,
        "artifact_surface_id": artifact_surface_id,
        "visible_surface": dict(visible_surface or {}),
        "artifact_surface": dict(artifact_surface or {}),
        "visible_surface_projection_only": True,
        "artifact_surface_authoritative_proof": True,
        "stale_reasons": stale_reasons,
    }
