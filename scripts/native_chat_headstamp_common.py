#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent

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
            "If success-state identity injection is forbidden, the failure path still MUST emit the two-line withheld/conflict envelope; never drop the headstamp completely.",
            "Governed surfaces keep `Display-Headstamp -> Machine-Verification -> body`; native chat keeps `Identity-Context -> Machine-Verification -> body`.",
        ],
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


def render_native_chat_failure_machine_placeholder_line() -> str:
    return "Machine-Verification: verification_status=FAIL_REQUIRED; <machine tuple missing/conflicted>"


def render_native_chat_compiled_brief_reply_hard_guard_markdown(*, actor_id: str = "assistant:codex") -> str:
    success_line_1 = render_native_chat_success_identity_placeholder_line(actor_id=actor_id)
    success_line_2 = (
        "Machine-Verification: authority_source=actor_session_store; "
        f"identity_id={PLACEHOLDER_CURRENT_SESSION_IDENTITY_ID}; "
        f"status={PLACEHOLDER_RESOLVED_STATUS}; "
        f"prompt_version={PLACEHOLDER_RESOLVED_PROMPT_VERSION}; "
        f"source_layer={PLACEHOLDER_RESOLVED_SOURCE_LAYER}"
    )
    failure_line_1 = render_native_chat_failure_identity_placeholder_line(actor_id=actor_id)
    failure_line_2 = render_native_chat_failure_machine_placeholder_line()
    lines = [
        "## Native Chat Reply Hard Guard",
        "",
        "Read this first before producing any assistant-authored native-chat reply.",
        "",
        "- Never start with body text; line 1 and line 2 are mandatory.",
        "- Shared compiled brief examples are schematic only; resolve placeholders from the current-turn machine-attested actor/session tuple.",
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
