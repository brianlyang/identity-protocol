#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from native_chat_headstamp_common import (
    PLACEHOLDER_REQUESTED_IDENTITY_ID,
    TUPLE_MISSING_FAILURE_ENVELOPE_RULE,
    native_chat_success_placeholder_payload,
    normalize_native_chat_machine_profile,
    render_machine_line,
    render_native_chat_failure_identity_placeholder_line,
    render_native_chat_failure_machine_placeholder_line,
    render_native_chat_success_identity_placeholder_line,
    resolve_native_chat_profile_doc,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_COMPILED_BRIEF = "IP-CBRIEF-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_COMPILED_BRIEF = REPO_ROOT / "identity" / "runtime" / "IDENTITY_COMPILED.md"
DEFAULT_MACHINE_PROFILE_TEMPLATE = (
    REPO_ROOT / "identity" / "protocol" / "plugins" / "templates" / "native-chat-headstamp.machine_verification_profiles_v1.json"
)
DEFAULT_SURFACE_TEMPLATE = (
    REPO_ROOT / "identity" / "protocol" / "plugins" / "templates" / "headstamp-surface-semantics.matrix_v1.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}

def _detect_default_profile(text: str) -> str:
    patterns = (
        r"default_machine_profile: `([^`]+)`",
        r"Native chat machine profile default: `([^`]+)`",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_native_chat_machine_profile(match.group(1), default="mini")
    return "mini"


def _required_tokens(
    *,
    profile: str,
    surface_template: dict[str, Any],
    machine_profile_template: dict[str, Any],
    machine_profile_template_path: Path,
) -> list[str]:
    clarity = surface_template.get("clarity_freeze") if isinstance(surface_template.get("clarity_freeze"), dict) else {}
    projection_rule = str(
        clarity.get(
            "compiled_brief_projection_rule",
            "shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.",
        )
    ).strip()
    default_reply_rule = str(
        clarity.get(
            "compiled_brief_default_reply_rule",
            "without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.",
        )
    ).strip()
    failure_envelope_claim_scope = str(
        clarity.get(
            "failure_envelope_claim_scope",
            "`requested_identity_id` in native-chat failure line 1 is the requested target only; it never proves the current speaking identity.",
        )
    ).strip()
    compatibility_pointer_diagnostic_rule = str(
        clarity.get(
            "compatibility_pointer_diagnostic_rule",
            "`compatibility_pointer_identity_id` is diagnostic-only compatibility metadata; it MUST NOT replace `identity_id` or appear as success-state identity injection.",
        )
    ).strip()
    failure_profile_default = str(
        clarity.get(
            "failure_profile_default",
            "native-chat failure `Machine-Verification` defaults to the compact `mini` profile unless debug/audit context explicitly requires escalation.",
        )
    ).strip()
    success_profile_doc = resolve_native_chat_profile_doc(
        machine_profile_template,
        profile_name=profile,
        failure=False,
    )
    success_machine_line = render_machine_line(
        native_chat_success_placeholder_payload(),
        field_order=success_profile_doc["field_order"],
        include_extra_fields=success_profile_doc["include_extra_fields"],
    )
    return [
        "Artifact classification:",
        "artifact_class: tracked_compiled_brief_artifact",
        "path_status: legacy_canonical_compatibility_path",
        "generation_mode: source_first",
        projection_rule,
        default_reply_rule,
        "Source-first generation inputs:",
        "${IDENTITY_HOME}/<resolved_identity_id>/CURRENT_TASK.json",
        "${IDENTITY_HOME}/<resolved_identity_id>/IDENTITY_PROMPT.md",
        "Native chat assistant-visible headstamp contract:",
        "Runtime loop is fixed: `machine-verify -> assistant-visible-inject -> next turn re-verify`.",
        TUPLE_MISSING_FAILURE_ENVELOPE_RULE,
        failure_envelope_claim_scope,
        compatibility_pointer_diagnostic_rule,
        failure_profile_default,
        "Native chat headstamp hard guard:",
        (
            "Success example line 1 (schematic only; placeholders resolve only from current-turn machine tuple): "
            f"`{render_native_chat_success_identity_placeholder_line()}`"
        ),
        f"Success example line 2 (schematic only; profile `{profile}`): `{success_machine_line}`",
        f"Failure example line 1: `{render_native_chat_failure_identity_placeholder_line()}`",
        (
            "Failure example line 2: "
            f"`{render_native_chat_failure_machine_placeholder_line(default_machine_profile=profile, template_ref=str(machine_profile_template_path))}`"
        ),
        PLACEHOLDER_REQUESTED_IDENTITY_ID,
    ]


FORBIDDEN_TOKENS = [
    "Active identity:",
    "Actor binding:",
    "Resolved source layer:",
    "Current objective:",
    "Current state:",
    "Identity runtime metadata:",
    "Identity prompt activation:",
    "Runtime baseline review references:",
    "Compile-time generated line 1",
    "Compile-time generated line 2",
    "prompt_preview:",
    "prompt_sha256:",
    "canonical_pointer_identity:",
    "current_pointer_identity_id=",
]


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate shared compiled brief stays projection-neutral for native chat.")
    ap.add_argument("--compiled-brief", default=str(DEFAULT_COMPILED_BRIEF))
    ap.add_argument("--machine-profile-template", default=str(DEFAULT_MACHINE_PROFILE_TEMPLATE))
    ap.add_argument("--surface-template", default=str(DEFAULT_SURFACE_TEMPLATE))
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    compiled_brief = Path(str(args.compiled_brief)).expanduser().resolve()
    machine_profile_template = Path(str(args.machine_profile_template)).expanduser().resolve()
    surface_template = Path(str(args.surface_template)).expanduser().resolve()

    payload: dict[str, Any] = {
        "compiled_brief_projection_boundary_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_COMPILED_BRIEF,
        "compiled_brief": str(compiled_brief),
        "machine_profile_template": str(machine_profile_template),
        "surface_template": str(surface_template),
        "default_machine_profile": "",
        "missing_required_tokens": [],
        "forbidden_token_hits": [],
        "top_hard_guard_status": STATUS_FAIL_REQUIRED,
        "stale_reasons": [],
    }

    missing_paths = [
        str(path)
        for path in (compiled_brief, machine_profile_template, surface_template)
        if not path.exists() or not path.is_file()
    ]
    if missing_paths:
        payload["stale_reasons"] = [f"missing_required_path:{path}" for path in missing_paths]
        _emit(payload, json_only=args.json_only)
        return 1

    text = compiled_brief.read_text(encoding="utf-8", errors="ignore")
    profile = _detect_default_profile(text)
    payload["default_machine_profile"] = profile
    required = _required_tokens(
        profile=profile,
        surface_template=_load_json(surface_template),
        machine_profile_template=_load_json(machine_profile_template),
        machine_profile_template_path=machine_profile_template,
    )
    missing_required_tokens = [token for token in required if token not in text]
    forbidden_hits = [token for token in FORBIDDEN_TOKENS if token in text]
    first_nonempty_lines = [line for line in text.splitlines() if line.strip()][:20]
    top_section = "\n".join(first_nonempty_lines)
    top_guard_tokens = [
        "## Native Chat Reply Hard Guard",
        "Read this first before producing any assistant-authored native-chat reply.",
        "- Never start with body text; line 1 and line 2 are mandatory.",
        f"- {TUPLE_MISSING_FAILURE_ENVELOPE_RULE}",
        "- Shared compiled brief examples are schematic only; resolve placeholders from the current-turn machine-attested actor/session tuple.",
        "- Only after those two lines may body text begin.",
    ]
    top_guard_status = (
        STATUS_PASS_REQUIRED
        if all(token in top_section for token in top_guard_tokens)
        else STATUS_FAIL_REQUIRED
    )
    payload["missing_required_tokens"] = missing_required_tokens
    payload["forbidden_token_hits"] = forbidden_hits
    payload["top_hard_guard_status"] = top_guard_status

    stale_reasons: list[str] = []
    if missing_required_tokens:
        stale_reasons.append("compiled_brief_missing_required_projection_tokens")
    if forbidden_hits:
        stale_reasons.append("compiled_brief_contains_stale_runtime_projection_tokens")
    if top_guard_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("compiled_brief_top_reply_hard_guard_missing_or_not_front_loaded")

    if stale_reasons:
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["compiled_brief_projection_boundary_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
