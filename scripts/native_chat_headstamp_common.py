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
