#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent

DEFAULT_NATIVE_CHAT_MACHINE_PROFILE_TEMPLATE_REF = (
    "identity/protocol/plugins/templates/native-chat-headstamp.machine_verification_profiles_v1.json"
)
DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF = (
    "identity/protocol/plugins/templates/native-chat-headstamp.prompt_hard_guard_v1.json"
)
ALLOWED_NATIVE_CHAT_MACHINE_PROFILES = ("mini", "standard", "audit")

PLACEHOLDER_CURRENT_SESSION_IDENTITY_ID = "<current_session_identity_id>"
PLACEHOLDER_REQUESTED_IDENTITY_ID = "<requested_identity_id>"
PLACEHOLDER_RESOLVED_SCOPE = "<resolved_scope>"
PLACEHOLDER_RESOLVED_SOURCE_LAYER = "<resolved_source_layer>"
PLACEHOLDER_RESOLVED_WORK_LAYER = "<resolved_work_layer>"
PLACEHOLDER_RESOLVED_STATUS = "<resolved_status>"
PLACEHOLDER_RESOLVED_PROMPT_VERSION = "<resolved_prompt_version>"
PLACEHOLDER_RESOLVED_POINTER_PATH = "<resolved_pointer_path>"
PLACEHOLDER_RESOLVED_CATALOG_PATH = "<resolved_catalog_path>"
PLACEHOLDER_RESOLVED_PACK_PATH = "<resolved_pack_path>"
PLACEHOLDER_RESOLVED_BINDING_VERSION = "<resolved_binding_version>"
PLACEHOLDER_CONFLICT_REASON = "<reason>"
PLACEHOLDER_VERIFICATION_SOURCE = "<verification_source>"
PLACEHOLDER_COMPATIBILITY_POINTER_IDENTITY_ID = "<compatibility_pointer_identity_id>"
PLACEHOLDER_COMPATIBILITY_POINTER_SCOPE = "<compatibility_pointer_scope>"
PLACEHOLDER_CONTROL_STATE = "<control_state>"
TUPLE_MISSING_FAILURE_ENVELOPE_RULE = (
    "If `CODEX_SESSION_ID` / `IDENTITY_SESSION_ID` is missing, or the current-turn actor/session tuple cannot be "
    "resolved, line 1 and line 2 MUST fall back to the two-line withheld/conflict envelope; never drop the "
    "headstamp completely."
)

PROMPT_HARD_GUARD_BEGIN = "<!-- NATIVE_CHAT_HEADSTAMP_HARD_GUARD:BEGIN -->"
PROMPT_HARD_GUARD_END = "<!-- NATIVE_CHAT_HEADSTAMP_HARD_GUARD:END -->"
PROMPT_HARD_GUARD_INSERT_BEFORE = "## Mission"


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def fallback_native_chat_prompt_hard_guard_template() -> dict[str, Any]:
    return {
        "template_id": "native_chat_headstamp_prompt_hard_guard_v1",
        "version": "v1",
        "section_heading": "Native Chat Headstamp Hard Guard",
        "section_intro": "Apply these hard rules to every assistant-authored user-visible native-chat reply.",
        "default_machine_profile": "mini",
        "success_order": ["Identity-Context", "Machine-Verification", "body"],
        "failure_order": [
            "Identity-Context(withheld_or_conflict)",
            "Machine-Verification(verification_status=FAIL_REQUIRED)",
            "body",
        ],
        "required_invariants": [
            "Every assistant-authored user-visible native-chat reply MUST begin with a two-line headstamp before any body text.",
            "There is no headerless assistant-authored native-chat reply path.",
            TUPLE_MISSING_FAILURE_ENVELOPE_RULE,
            "If success-state identity injection is forbidden, the failure path still MUST emit the two-line withheld/conflict envelope; never drop the headstamp completely.",
            "Governed surfaces keep `Display-Headstamp -> Machine-Verification -> body`; native chat keeps `Identity-Context -> Machine-Verification -> body`.",
            "Failure line 1 may claim only `requested_identity_id`; it MUST NOT project a success identity when the current-turn machine tuple is missing, conflicted, or polluted.",
            "Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.",
        ],
    }


def fallback_native_chat_machine_profile_template() -> dict[str, Any]:
    return {
        "template_id": "native_chat_machine_verification_profiles_v1",
        "version": "v1",
        "surface_class": "host_native_chat_panel",
        "delivery_mode": "assistant_text_injection",
        "description": "Machine-Verification line profiles for native-chat assistant-visible identity injection.",
        "success_order": ["Identity-Context", "Machine-Verification", "body"],
        "default_machine_profile": "mini",
        "failure_default_machine_profile": "mini",
        "profiles": {
            "mini": {
                "description": "Compact native-chat default for ordinary user-visible replies.",
                "required_fields": ["authority_source", "identity_id", "status"],
                "field_order": [
                    "authority_source",
                    "identity_id",
                    "status",
                    "prompt_version",
                    "source_layer",
                ],
                "include_extra_fields": False,
            },
            "standard": {
                "description": "Readable debug profile for native-chat verification and delivery triage.",
                "required_fields": ["authority_source", "identity_id", "status", "pointer_path"],
                "field_order": [
                    "authority_source",
                    "actor_id",
                    "identity_id",
                    "status",
                    "pointer_path",
                    "prompt_version",
                    "work_layer",
                    "source_layer",
                ],
                "include_extra_fields": False,
            },
            "audit": {
                "description": "Full audit/native-debug projection with replay lineage when available.",
                "required_fields": [
                    "authority_source",
                    "identity_id",
                    "status",
                    "pointer_path",
                    "catalog_path",
                    "pack_path",
                ],
                "field_order": [
                    "authority_source",
                    "actor_id",
                    "identity_id",
                    "status",
                    "pointer_path",
                    "catalog_path",
                    "pack_path",
                    "prompt_version",
                    "binding_version",
                    "work_layer",
                    "source_layer",
                ],
                "include_extra_fields": True,
            },
        },
        "failure_profiles": {
            "mini": {
                "description": "Compact native-chat failure profile for ordinary user-visible replies.",
                "required_fields": [
                    "verification_source",
                    "verification_status",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                ],
                "field_order": [
                    "verification_source",
                    "verification_status",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                ],
                "include_extra_fields": False,
            },
            "standard": {
                "description": "Readable native-chat failure/debug profile with compatibility diagnostics kept off the visible identity line.",
                "required_fields": [
                    "verification_source",
                    "verification_status",
                    "compatibility_pointer_identity_id",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                ],
                "field_order": [
                    "verification_source",
                    "verification_status",
                    "compatibility_pointer_identity_id",
                    "compatibility_pointer_scope",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                    "source_layer",
                ],
                "include_extra_fields": False,
            },
            "audit": {
                "description": "Full failure/audit projection with compatibility-pointer lineage kept diagnostic-only.",
                "required_fields": [
                    "verification_source",
                    "verification_status",
                    "compatibility_pointer_identity_id",
                    "pointer_path",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                ],
                "field_order": [
                    "verification_source",
                    "verification_status",
                    "compatibility_pointer_identity_id",
                    "compatibility_pointer_scope",
                    "pointer_path",
                    "current_chat_surface_native_machine_attested",
                    "next_hop_admission_status",
                    "control_state",
                    "source_layer",
                ],
                "include_extra_fields": True,
            },
        },
        "failure_field_freeze": {
            "identity_line_claim_field": "requested_identity_id",
            "success_identity_field": "identity_id",
            "compatibility_pointer_field": "compatibility_pointer_identity_id",
            "compatibility_pointer_rule": "compatibility pointer identity is diagnostic only; it never becomes the current speaking identity",
        },
    }


def load_native_chat_prompt_hard_guard_template(template_ref: str = "") -> tuple[dict[str, Any], Path]:
    resolved_ref = str(template_ref or DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF).strip()
    template_path = (
        (PROTOCOL_ROOT / resolved_ref).resolve()
        if resolved_ref and not Path(resolved_ref).is_absolute()
        else Path(resolved_ref or DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF).expanduser().resolve()
    )
    template_doc = _load_json_if_exists(template_path)
    if not template_doc:
        template_doc = fallback_native_chat_prompt_hard_guard_template()
    return template_doc, template_path


def load_native_chat_machine_profile_template(template_ref: str = "") -> tuple[dict[str, Any], Path]:
    resolved_ref = str(template_ref or DEFAULT_NATIVE_CHAT_MACHINE_PROFILE_TEMPLATE_REF).strip()
    template_path = (
        (PROTOCOL_ROOT / resolved_ref).resolve()
        if resolved_ref and not Path(resolved_ref).is_absolute()
        else Path(resolved_ref or DEFAULT_NATIVE_CHAT_MACHINE_PROFILE_TEMPLATE_REF).expanduser().resolve()
    )
    template_doc = _load_json_if_exists(template_path)
    if not template_doc:
        template_doc = fallback_native_chat_machine_profile_template()
    return template_doc, template_path


def normalize_native_chat_machine_profile(value: Any, *, default: str = "mini") -> str:
    token = str(value or "").strip().lower()
    aliases = {
        "minimal": "mini",
        "compact": "mini",
        "default": "mini",
        "full": "audit",
        "verbose": "audit",
    }
    token = aliases.get(token, token)
    if token in ALLOWED_NATIVE_CHAT_MACHINE_PROFILES:
        return token
    return default if default in ALLOWED_NATIVE_CHAT_MACHINE_PROFILES else "mini"


def _sequence_to_arrow(items: list[Any] | tuple[Any, ...]) -> str:
    tokens = [str(item).strip() for item in items if str(item).strip()]
    return " -> ".join(tokens)


def _stringify_machine_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value).strip()


def render_machine_line(
    payload: dict[str, Any],
    *,
    field_order: tuple[str, ...] | list[str],
    include_extra_fields: bool,
) -> str:
    ordered_parts: list[str] = []
    seen: set[str] = set()
    for key in field_order:
        rendered = _stringify_machine_value(payload.get(str(key)))
        if rendered == "":
            continue
        ordered_parts.append(f"{key}={rendered}")
        seen.add(str(key))
    extra_parts: list[str] = []
    if include_extra_fields:
        for key in sorted(payload.keys()):
            if key in seen:
                continue
            rendered = _stringify_machine_value(payload.get(key))
            if rendered == "":
                continue
            extra_parts.append(f"{key}={rendered}")
    parts = ordered_parts + extra_parts
    return "Machine-Verification: " + "; ".join(parts) if parts else ""


def resolve_native_chat_profile_doc(
    template_doc: dict[str, Any],
    *,
    profile_name: str,
    failure: bool = False,
) -> dict[str, Any]:
    fallback_doc = fallback_native_chat_machine_profile_template()
    profile_key = "failure_profiles" if failure else "profiles"
    profiles = template_doc.get(profile_key) if isinstance(template_doc.get(profile_key), dict) else {}
    fallback_profiles = (
        fallback_doc.get(profile_key) if isinstance(fallback_doc.get(profile_key), dict) else {}
    )
    doc = profiles.get(profile_name)
    if not isinstance(doc, dict):
        doc = fallback_profiles.get(profile_name) if isinstance(fallback_profiles.get(profile_name), dict) else {}
    field_order = tuple(str(item).strip() for item in (doc.get("field_order") or []) if str(item).strip())
    if not field_order:
        fallback_profile = fallback_profiles.get(profile_name) if isinstance(fallback_profiles.get(profile_name), dict) else {}
        field_order = tuple(
            str(item).strip() for item in (fallback_profile.get("field_order") or []) if str(item).strip()
        )
    return {
        "name": profile_name,
        "description": str(doc.get("description", "")).strip()
        or str((((fallback_profiles or {}).get(profile_name) or {}).get("description", ""))).strip(),
        "field_order": field_order,
        "include_extra_fields": bool(doc.get("include_extra_fields", False)),
    }


def native_chat_success_placeholder_payload(*, actor_id: str = "assistant:codex") -> dict[str, str]:
    return {
        "authority_source": "actor_session_store",
        "actor_id": str(actor_id or "assistant:codex").strip() or "assistant:codex",
        "identity_id": PLACEHOLDER_CURRENT_SESSION_IDENTITY_ID,
        "status": PLACEHOLDER_RESOLVED_STATUS,
        "pointer_path": PLACEHOLDER_RESOLVED_POINTER_PATH,
        "catalog_path": PLACEHOLDER_RESOLVED_CATALOG_PATH,
        "pack_path": PLACEHOLDER_RESOLVED_PACK_PATH,
        "prompt_version": PLACEHOLDER_RESOLVED_PROMPT_VERSION,
        "binding_version": PLACEHOLDER_RESOLVED_BINDING_VERSION,
        "work_layer": PLACEHOLDER_RESOLVED_WORK_LAYER,
        "source_layer": PLACEHOLDER_RESOLVED_SOURCE_LAYER,
    }


def native_chat_failure_placeholder_payload() -> dict[str, Any]:
    return {
        "verification_source": PLACEHOLDER_VERIFICATION_SOURCE,
        "verification_status": "FAIL_REQUIRED",
        "compatibility_pointer_identity_id": PLACEHOLDER_COMPATIBILITY_POINTER_IDENTITY_ID,
        "compatibility_pointer_scope": PLACEHOLDER_COMPATIBILITY_POINTER_SCOPE,
        "pointer_path": PLACEHOLDER_RESOLVED_POINTER_PATH,
        "current_chat_surface_native_machine_attested": False,
        "next_hop_admission_status": "FAIL_REQUIRED",
        "control_state": PLACEHOLDER_CONTROL_STATE,
        "source_layer": PLACEHOLDER_RESOLVED_SOURCE_LAYER,
    }


def render_native_chat_success_identity_placeholder_line(*, actor_id: str = "assistant:codex") -> str:
    actor_token = str(actor_id or "assistant:codex").strip() or "assistant:codex"
    return (
        f"Identity-Context: actor_id={actor_token}; "
        f"identity_id={PLACEHOLDER_CURRENT_SESSION_IDENTITY_ID}; "
        f"scope={PLACEHOLDER_RESOLVED_SCOPE}; "
        f"lock=LOCK_MATCH; source={PLACEHOLDER_RESOLVED_SOURCE_LAYER} | "
        f"Layer-Context: work_layer={PLACEHOLDER_RESOLVED_WORK_LAYER}; "
        f"source_layer={PLACEHOLDER_RESOLVED_SOURCE_LAYER}"
    )


def render_native_chat_failure_identity_placeholder_line(*, actor_id: str = "assistant:codex") -> str:
    actor_token = str(actor_id or "assistant:codex").strip() or "assistant:codex"
    return (
        f"Identity-Context: withheld; actor_id={actor_token}; "
        f"requested_identity_id={PLACEHOLDER_REQUESTED_IDENTITY_ID}; "
        f"conflict={PLACEHOLDER_CONFLICT_REASON}; "
        f"scope={PLACEHOLDER_RESOLVED_SCOPE}; "
        f"source={PLACEHOLDER_RESOLVED_SOURCE_LAYER} | "
        f"Layer-Context: work_layer={PLACEHOLDER_RESOLVED_WORK_LAYER}; "
        f"source_layer={PLACEHOLDER_RESOLVED_SOURCE_LAYER}"
    )


def render_native_chat_success_identity_line(
    *,
    actor_id: str,
    identity_id: str,
    scope: str,
    source_layer: str,
    work_layer: str,
    lock_state: str = "LOCK_MATCH",
) -> str:
    actor_token = str(actor_id or "assistant:codex").strip() or "assistant:codex"
    identity_token = str(identity_id or "").strip() or PLACEHOLDER_CURRENT_SESSION_IDENTITY_ID
    scope_token = str(scope or "").strip() or PLACEHOLDER_RESOLVED_SCOPE
    source_token = str(source_layer or "").strip() or PLACEHOLDER_RESOLVED_SOURCE_LAYER
    work_token = str(work_layer or "").strip() or PLACEHOLDER_RESOLVED_WORK_LAYER
    lock_token = str(lock_state or "").strip() or "LOCK_MATCH"
    return (
        f"Identity-Context: actor_id={actor_token}; "
        f"identity_id={identity_token}; "
        f"scope={scope_token}; "
        f"lock={lock_token}; source={source_token} | "
        f"Layer-Context: work_layer={work_token}; "
        f"source_layer={source_token}"
    )


def render_native_chat_failure_identity_line(
    *,
    actor_id: str,
    requested_identity_id: str,
    conflict: str,
    scope: str,
    source_layer: str,
    work_layer: str,
) -> str:
    actor_token = str(actor_id or "assistant:codex").strip() or "assistant:codex"
    requested_token = str(requested_identity_id or "").strip() or PLACEHOLDER_REQUESTED_IDENTITY_ID
    conflict_token = str(conflict or "").strip() or PLACEHOLDER_CONFLICT_REASON
    scope_token = str(scope or "").strip() or PLACEHOLDER_RESOLVED_SCOPE
    source_token = str(source_layer or "").strip() or PLACEHOLDER_RESOLVED_SOURCE_LAYER
    work_token = str(work_layer or "").strip() or PLACEHOLDER_RESOLVED_WORK_LAYER
    return (
        f"Identity-Context: withheld; actor_id={actor_token}; "
        f"requested_identity_id={requested_token}; "
        f"conflict={conflict_token}; "
        f"scope={scope_token}; "
        f"source={source_token} | "
        f"Layer-Context: work_layer={work_token}; "
        f"source_layer={source_token}"
    )


def build_native_chat_success_machine_payload(
    *,
    actor_id: str,
    identity_id: str,
    status: str,
    prompt_version: str,
    source_layer: str,
    pointer_path: str = "",
    catalog_path: str = "",
    pack_path: str = "",
    binding_version: str | int | None = "",
    work_layer: str = "",
    authority_source: str = "actor_session_store",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "authority_source": str(authority_source or "actor_session_store").strip() or "actor_session_store",
        "actor_id": str(actor_id or "").strip(),
        "identity_id": str(identity_id or "").strip(),
        "status": str(status or "").strip() or PLACEHOLDER_RESOLVED_STATUS,
        "pointer_path": str(pointer_path or "").strip(),
        "catalog_path": str(catalog_path or "").strip(),
        "pack_path": str(pack_path or "").strip(),
        "prompt_version": str(prompt_version or "").strip() or PLACEHOLDER_RESOLVED_PROMPT_VERSION,
        "binding_version": str(binding_version or "").strip(),
        "work_layer": str(work_layer or "").strip(),
        "source_layer": str(source_layer or "").strip() or PLACEHOLDER_RESOLVED_SOURCE_LAYER,
    }
    return payload


def build_native_chat_failure_machine_payload(
    *,
    verification_source: str,
    source_layer: str,
    compatibility_pointer_identity_id: str = "",
    compatibility_pointer_scope: str = "",
    pointer_path: str = "",
    control_state: str = "withheld",
    current_chat_surface_native_machine_attested: bool = False,
    next_hop_admission_status: str = "FAIL_REQUIRED",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "verification_source": str(verification_source or "").strip() or PLACEHOLDER_VERIFICATION_SOURCE,
        "verification_status": "FAIL_REQUIRED",
        "compatibility_pointer_identity_id": str(compatibility_pointer_identity_id or "").strip(),
        "compatibility_pointer_scope": str(compatibility_pointer_scope or "").strip(),
        "pointer_path": str(pointer_path or "").strip(),
        "current_chat_surface_native_machine_attested": bool(current_chat_surface_native_machine_attested),
        "next_hop_admission_status": str(next_hop_admission_status or "").strip() or "FAIL_REQUIRED",
        "control_state": str(control_state or "").strip() or PLACEHOLDER_CONTROL_STATE,
        "source_layer": str(source_layer or "").strip() or PLACEHOLDER_RESOLVED_SOURCE_LAYER,
    }
    return payload


def render_native_chat_success_machine_line(
    *,
    actor_id: str,
    identity_id: str,
    status: str,
    prompt_version: str,
    source_layer: str,
    pointer_path: str = "",
    catalog_path: str = "",
    pack_path: str = "",
    binding_version: str | int | None = "",
    work_layer: str = "",
    authority_source: str = "actor_session_store",
    machine_profile: str = "mini",
    template_ref: str = "",
) -> str:
    template_doc, _ = load_native_chat_machine_profile_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        machine_profile,
        default=str(template_doc.get("default_machine_profile", "mini")),
    )
    profile_doc = resolve_native_chat_profile_doc(template_doc, profile_name=profile, failure=False)
    payload = build_native_chat_success_machine_payload(
        actor_id=actor_id,
        identity_id=identity_id,
        status=status,
        prompt_version=prompt_version,
        source_layer=source_layer,
        pointer_path=pointer_path,
        catalog_path=catalog_path,
        pack_path=pack_path,
        binding_version=binding_version,
        work_layer=work_layer,
        authority_source=authority_source,
    )
    return render_machine_line(
        payload,
        field_order=profile_doc["field_order"],
        include_extra_fields=profile_doc["include_extra_fields"],
    )


def render_native_chat_failure_machine_line(
    *,
    verification_source: str,
    source_layer: str,
    compatibility_pointer_identity_id: str = "",
    compatibility_pointer_scope: str = "",
    pointer_path: str = "",
    control_state: str = "withheld",
    current_chat_surface_native_machine_attested: bool = False,
    next_hop_admission_status: str = "FAIL_REQUIRED",
    machine_profile: str = "mini",
    template_ref: str = "",
) -> str:
    template_doc, _ = load_native_chat_machine_profile_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        machine_profile,
        default=str(template_doc.get("failure_default_machine_profile", "mini")),
    )
    profile_doc = resolve_native_chat_profile_doc(template_doc, profile_name=profile, failure=True)
    payload = build_native_chat_failure_machine_payload(
        verification_source=verification_source,
        source_layer=source_layer,
        compatibility_pointer_identity_id=compatibility_pointer_identity_id,
        compatibility_pointer_scope=compatibility_pointer_scope,
        pointer_path=pointer_path,
        control_state=control_state,
        current_chat_surface_native_machine_attested=current_chat_surface_native_machine_attested,
        next_hop_admission_status=next_hop_admission_status,
    )
    return render_machine_line(
        payload,
        field_order=profile_doc["field_order"],
        include_extra_fields=profile_doc["include_extra_fields"],
    )


def render_native_chat_success_machine_placeholder_line(
    *,
    actor_id: str = "assistant:codex",
    default_machine_profile: str = "mini",
    template_ref: str = "",
) -> str:
    template_doc, _ = load_native_chat_machine_profile_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        default_machine_profile,
        default=str(template_doc.get("default_machine_profile", "mini")),
    )
    profile_doc = resolve_native_chat_profile_doc(template_doc, profile_name=profile, failure=False)
    return render_machine_line(
        native_chat_success_placeholder_payload(actor_id=actor_id),
        field_order=profile_doc["field_order"],
        include_extra_fields=profile_doc["include_extra_fields"],
    )


def render_native_chat_failure_machine_placeholder_line(
    *,
    default_machine_profile: str = "mini",
    template_ref: str = "",
) -> str:
    template_doc, _ = load_native_chat_machine_profile_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        default_machine_profile,
        default=str(template_doc.get("failure_default_machine_profile", "mini")),
    )
    profile_doc = resolve_native_chat_profile_doc(template_doc, profile_name=profile, failure=True)
    return render_machine_line(
        native_chat_failure_placeholder_payload(),
        field_order=profile_doc["field_order"],
        include_extra_fields=profile_doc["include_extra_fields"],
    )


def render_native_chat_compiled_brief_reply_hard_guard_markdown(
    *,
    actor_id: str = "assistant:codex",
    default_machine_profile: str = "mini",
    machine_profile_template_ref: str = "",
) -> str:
    success_line_1 = render_native_chat_success_identity_placeholder_line(actor_id=actor_id)
    success_line_2 = render_native_chat_success_machine_placeholder_line(
        actor_id=actor_id,
        default_machine_profile=default_machine_profile,
        template_ref=machine_profile_template_ref,
    )
    failure_line_1 = render_native_chat_failure_identity_placeholder_line(actor_id=actor_id)
    failure_line_2 = render_native_chat_failure_machine_placeholder_line(
        default_machine_profile=default_machine_profile,
        template_ref=machine_profile_template_ref,
    )
    lines = [
        "## Native Chat Reply Hard Guard",
        "",
        "Read this first before producing any assistant-authored native-chat reply.",
        "",
        "- Never start with body text; line 1 and line 2 are mandatory.",
        f"- {TUPLE_MISSING_FAILURE_ENVELOPE_RULE}",
        "- Shared compiled brief examples are schematic only; resolve placeholders from the current-turn machine-attested actor/session tuple.",
        "- Failure line 1 may claim only `requested_identity_id`; it never proves the current speaking identity.",
        "- Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.",
        "- Success path first two lines:",
        f"  1. `{success_line_1}`",
        f"  2. `{success_line_2}`",
        "- Failure path first two lines when the current-turn machine tuple is missing, conflicted, or polluted:",
        f"  1. `{failure_line_1}`",
        f"  2. `{failure_line_2}`",
        "- Only after those two lines may body text begin.",
    ]
    return "\n".join(lines).strip() + "\n"


def prompt_hard_guard_required_tokens(
    *,
    default_machine_profile: str = "mini",
    template_ref: str = "",
) -> list[str]:
    template_doc, _ = load_native_chat_prompt_hard_guard_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        default_machine_profile,
        default=str(template_doc.get("default_machine_profile", "mini")),
    )
    required = [
        str(template_doc.get("section_heading", "Native Chat Headstamp Hard Guard")).strip(),
        str(
            template_doc.get(
                "section_intro",
                "Apply these hard rules to every assistant-authored user-visible native-chat reply.",
            )
        ).strip(),
        *[
            str(item).strip()
            for item in (template_doc.get("required_invariants") or [])
            if str(item).strip()
        ],
        "Failure line 1 may claim only `requested_identity_id`; it MUST NOT project a success identity when the current-turn machine tuple is missing, conflicted, or polluted.",
        "Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.",
        f"Default native-chat Machine-Verification profile: `{profile}`.",
        f"Success visible order: `{_sequence_to_arrow(list(template_doc.get('success_order') or []))}`.",
        f"Failure visible order: `{_sequence_to_arrow(list(template_doc.get('failure_order') or []))}`.",
    ]
    return [token for token in required if token]


def render_native_chat_prompt_hard_guard_markdown(
    *,
    default_machine_profile: str = "mini",
    template_ref: str = "",
) -> str:
    template_doc, _ = load_native_chat_prompt_hard_guard_template(template_ref)
    profile = normalize_native_chat_machine_profile(
        default_machine_profile,
        default=str(template_doc.get("default_machine_profile", "mini")),
    )
    section_heading = str(template_doc.get("section_heading", "Native Chat Headstamp Hard Guard")).strip()
    section_intro = str(
        template_doc.get(
            "section_intro",
            "Apply these hard rules to every assistant-authored user-visible native-chat reply.",
        )
    ).strip()
    required_invariants = [
        str(item).strip() for item in (template_doc.get("required_invariants") or []) if str(item).strip()
    ]
    success_order = _sequence_to_arrow(list(template_doc.get("success_order") or []))
    failure_order = _sequence_to_arrow(list(template_doc.get("failure_order") or []))
    lines = [
        PROMPT_HARD_GUARD_BEGIN,
        f"## {section_heading}" if not section_heading.startswith("## ") else section_heading,
        "",
        section_intro,
        "",
        *[f"- {item}" for item in required_invariants],
        f"- Default native-chat Machine-Verification profile: `{profile}`.",
        f"- Success visible order: `{success_order}`.",
        f"- Failure visible order: `{failure_order}`.",
        PROMPT_HARD_GUARD_END,
    ]
    return "\n".join(lines).strip() + "\n"


def ensure_native_chat_prompt_hard_guard(
    text: str,
    *,
    default_machine_profile: str = "mini",
    template_ref: str = "",
) -> tuple[str, list[str], bool]:
    source_text = str(text or "")
    rendered = render_native_chat_prompt_hard_guard_markdown(
        default_machine_profile=default_machine_profile,
        template_ref=template_ref,
    )
    required_tokens = prompt_hard_guard_required_tokens(
        default_machine_profile=default_machine_profile,
        template_ref=template_ref,
    )
    missing_tokens = [token for token in required_tokens if token not in source_text]
    if PROMPT_HARD_GUARD_BEGIN in source_text and PROMPT_HARD_GUARD_END in source_text:
        start = source_text.index(PROMPT_HARD_GUARD_BEGIN)
        end = source_text.index(PROMPT_HARD_GUARD_END) + len(PROMPT_HARD_GUARD_END)
        updated = (source_text[:start] + rendered + source_text[end:]).strip() + "\n"
        return updated, missing_tokens, updated != source_text
    if not missing_tokens:
        return source_text, [], False
    if PROMPT_HARD_GUARD_INSERT_BEFORE in source_text:
        updated = source_text.replace(PROMPT_HARD_GUARD_INSERT_BEFORE, rendered + "\n" + PROMPT_HARD_GUARD_INSERT_BEFORE, 1)
    else:
        base = source_text.rstrip()
        updated = (base + "\n\n" + rendered).strip() + "\n"
    return updated, missing_tokens, updated != source_text
