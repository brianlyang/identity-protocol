#!/usr/bin/env python3
"""Compile a concise identity runtime brief from catalog + active pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    load_actor_binding,
    load_actor_binding_store,
    resolve_protocol_actor_id,
)
from native_chat_headstamp_common import (
    DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF,
    fallback_native_chat_machine_profile_template,
    load_native_chat_prompt_hard_guard_template,
    render_native_chat_compiled_brief_reply_hard_guard_markdown,
    render_native_chat_failure_identity_placeholder_line,
    render_native_chat_failure_machine_placeholder_line,
    render_native_chat_success_machine_placeholder_line,
    render_native_chat_success_identity_placeholder_line,
    resolve_native_chat_profile_doc,
)
from resolve_identity_context import resolve_identity, resolve_local_catalog_path


SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent
DEFAULT_REPO_CATALOG = (PROTOCOL_ROOT / "identity" / "catalog" / "identities.yaml").resolve()
DEFAULT_OUTPUT = (PROTOCOL_ROOT / "identity" / "runtime" / "IDENTITY_COMPILED.md").resolve()
DEFAULT_NATIVE_CHAT_HEADSTAMP_TEMPLATE_REF = (
    "identity/protocol/plugins/templates/native-chat-headstamp.machine_verification_profiles_v1.json"
)
DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF = (
    "identity/protocol/plugins/templates/headstamp-surface-semantics.matrix_v1.json"
)
ALLOWED_NATIVE_CHAT_MACHINE_PROFILES = ("mini", "standard", "audit")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _default_native_chat_headstamp_contract() -> dict[str, Any]:
    return {
        "required": True,
        "surface_class": "host_native_chat_panel",
        "delivery_mode": "assistant_text_injection",
        "template_ref": DEFAULT_NATIVE_CHAT_HEADSTAMP_TEMPLATE_REF,
        "default_machine_profile": "mini",
        "allowed_machine_profiles": list(ALLOWED_NATIVE_CHAT_MACHINE_PROFILES),
        "success_order": ["Identity-Context", "Machine-Verification", "body"],
        "runtime_loop": ["machine-verify", "assistant-visible-inject", "next-turn-reverify"],
        "failure_mode": "withhold_success_identity_line",
    }


def _fallback_native_chat_headstamp_template() -> dict[str, Any]:
    return fallback_native_chat_machine_profile_template()


def _fallback_headstamp_surface_semantics_template() -> dict[str, Any]:
    return {
        "template_id": "headstamp_surface_semantics_matrix_v1",
        "version": "v1",
        "surface_semantics_matrix": [
            {
                "surface_id": "native_chat_assistant_visible",
                "surface_label": "native chat",
                "surface_class": "host_native_chat_panel",
                "visible_order": ["Identity-Context", "Machine-Verification", "body"],
                "primary_human_literal": "Identity-Context: ... | Layer-Context: ...",
                "machine_literal": "Machine-Verification: ...",
                "proof_owner": "machine_headstamp + headstamp_admission_receipt + controlled-runtime artifacts",
            },
            {
                "surface_id": "governed_wrapper_visible",
                "surface_label": "governed wrapper",
                "surface_class": "controlled_runtime_surface",
                "visible_order": ["Display-Headstamp", "Machine-Verification", "body"],
                "primary_human_literal": "Display-Headstamp: Identity-Context: ... | Layer-Context: ...",
                "machine_literal": "Machine-Verification: ...",
                "proof_owner": "machine_headstamp + headstamp_admission_receipt + controlled-runtime artifacts",
            },
        ],
        "three_orders_matrix": [
            {
                "order_id": "processing_order",
                "label": "processing order",
                "applies_to": "v1.6.6 control plane",
                "sequence": [
                    "Display render",
                    "Machine truth resolve",
                    "Consistency review",
                    "Business next-hop admission",
                ],
                "not_equivalent_to": "visible line order",
            },
            {
                "order_id": "runtime_loop",
                "label": "runtime loop",
                "applies_to": "v1.6.1 native chat injection",
                "sequence": [
                    "machine-verify",
                    "assistant-visible-inject",
                    "next turn re-verify",
                ],
                "not_equivalent_to": "visible line order",
            },
        ],
        "object_literal_mapping": [
            {
                "semantic_object": "display_headstamp",
                "native_chat_literal": "Identity-Context: ... | Layer-Context: ...",
                "governed_literal": "Display-Headstamp: Identity-Context: ... | Layer-Context: ...",
                "authority_rule": "display object never becomes an authority source",
            },
            {
                "semantic_object": "requested_identity_id",
                "native_chat_literal": "Identity-Context: withheld; ... requested_identity_id=...",
                "governed_literal": "rendered only inside failure envelopes when needed",
                "authority_rule": "requested target only; never the current speaking identity",
            },
            {
                "semantic_object": "compatibility_pointer_identity_id",
                "native_chat_literal": "Machine-Verification: ... compatibility_pointer_identity_id=...",
                "governed_literal": "diagnostic-only when explicitly rendered",
                "authority_rule": "compatibility diagnostic only; never replace current-turn authoritative identity",
            },
        ],
        "clarity_freeze": {
            "manual_headstamp": "`manual_headstamp` = render_origin tag only; never verdict axis.",
            "excluded_non_blocking": "`EXCLUDED_NON_BLOCKING` only removes blocker aggregation; it never upgrades next-hop admission.",
            "sender_boundary_visibility": "Ordinary replies should stay focused on the standard native-chat output path; governed receipt or attestation boundaries are audit/debug-only.",
            "compile_runtime_authority": "compile/replay metadata may read compatibility mirror; current-session authority must not.",
            "compiled_example_label": "generated from current runtime; re-verify each turn",
            "compiled_brief_projection_rule": "shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.",
            "compiled_brief_default_reply_rule": "without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.",
            "failure_envelope_claim_scope": "`requested_identity_id` in native-chat failure line 1 is the requested target only; it never proves the current speaking identity.",
            "compatibility_pointer_diagnostic_rule": "`compatibility_pointer_identity_id` is diagnostic-only compatibility metadata; it MUST NOT replace `identity_id` or appear as success-state identity injection.",
            "failure_profile_default": "native-chat failure `Machine-Verification` defaults to the compact `mini` profile unless debug/audit context explicitly requires escalation.",
        },
    }


def _normalize_native_chat_machine_profile(value: Any, *, default: str = "mini") -> str:
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


def _normalize_native_chat_headstamp_contract(raw: Any) -> dict[str, Any]:
    contract = dict(_default_native_chat_headstamp_contract())
    source = raw if isinstance(raw, dict) else {}

    template_ref = str(source.get("template_ref", "")).strip()
    if template_ref:
        contract["template_ref"] = template_ref

    allowed_profiles = []
    for item in source.get("allowed_machine_profiles") or []:
        normalized = _normalize_native_chat_machine_profile(item, default="")
        if normalized and normalized not in allowed_profiles:
            allowed_profiles.append(normalized)
    if allowed_profiles:
        contract["allowed_machine_profiles"] = allowed_profiles

    default_profile = _normalize_native_chat_machine_profile(
        source.get("default_machine_profile", ""),
        default=str(contract.get("default_machine_profile", "mini")),
    )
    if default_profile not in contract["allowed_machine_profiles"]:
        contract["allowed_machine_profiles"].append(default_profile)
    contract["default_machine_profile"] = default_profile
    return contract


def _load_native_chat_headstamp_template(template_ref: str) -> tuple[dict[str, Any], Path]:
    template_path = (
        (PROTOCOL_ROOT / template_ref).resolve()
        if template_ref and not Path(template_ref).is_absolute()
        else Path(template_ref or DEFAULT_NATIVE_CHAT_HEADSTAMP_TEMPLATE_REF).expanduser().resolve()
    )
    template_doc = _load_json_if_exists(template_path)
    if not template_doc:
        template_doc = _fallback_native_chat_headstamp_template()
    return template_doc, template_path


def _load_headstamp_surface_semantics_template(template_ref: str) -> tuple[dict[str, Any], Path]:
    template_path = (
        (PROTOCOL_ROOT / template_ref).resolve()
        if template_ref and not Path(template_ref).is_absolute()
        else Path(template_ref or DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF).expanduser().resolve()
    )
    template_doc = _load_json_if_exists(template_path)
    if not template_doc:
        template_doc = _fallback_headstamp_surface_semantics_template()
    return template_doc, template_path


def _resolve_native_chat_profile_doc(
    template_doc: dict[str, Any],
    *,
    profile_name: str,
    failure: bool = False,
) -> dict[str, Any]:
    return resolve_native_chat_profile_doc(template_doc, profile_name=profile_name, failure=failure)


def _format_profile_fields(field_order: tuple[str, ...]) -> str:
    return ", ".join(field_order)


def _sequence_to_arrow(items: list[Any] | tuple[Any, ...]) -> str:
    tokens = [str(item).strip() for item in items if str(item).strip()]
    return " -> ".join(tokens)


def _pick_active_identity(
    catalog_path: Path,
    identities: list[dict[str, Any]],
    *,
    explicit_id: str,
    actor_id: str,
    session_id: str,
    default_id: str,
) -> dict[str, Any]:
    if explicit_id:
        active = next((x for x in identities if isinstance(x, dict) and x.get("id") == explicit_id), None)
        if not active:
            raise SystemExit(f"identity_id not found in identities: {explicit_id}")
        return active

    actor = str(actor_id or "").strip()
    sid = str(session_id or "").strip()
    if actor and sid:
        actor_binding = load_actor_binding(
            catalog_path.resolve(),
            actor_id,
            session_id=sid,
        )
        bound_identity_id = str(actor_binding.get("identity_id", "")).strip()
        if not bound_identity_id:
            raise SystemExit(
                "session-primary actor binding missing; "
                f"pass --identity-id explicitly or repair actor/session binding: actor={actor} session_id={sid}"
            )
        active = next((x for x in identities if isinstance(x, dict) and x.get("id") == bound_identity_id), None)
        if not active:
            raise SystemExit(
                f"actor session-bound identity not found in identities: actor={actor} session={sid} identity={bound_identity_id}"
            )
        if str(active.get("status", "")).lower() != "active":
            raise SystemExit(
                f"actor session-bound identity is not active: actor={actor} session={sid} "
                f"identity={bound_identity_id} status={active.get('status', '')}"
            )
        return active

    if actor:
        actor_binding = load_actor_binding(
            catalog_path.resolve(),
            actor,
            identity_id="",
        )
        bound_identity_id = str(actor_binding.get("identity_id", "")).strip()
        if bound_identity_id:
            active = next((x for x in identities if isinstance(x, dict) and x.get("id") == bound_identity_id), None)
            if not active:
                raise SystemExit(
                    f"actor-bound identity not found in identities: actor={actor} identity={bound_identity_id}"
                )
            if str(active.get("status", "")).lower() != "active":
                raise SystemExit(
                    f"actor-bound identity is not active: actor={actor} identity={bound_identity_id} "
                    f"status={active.get('status', '')}"
                )
            return active

        store = load_actor_binding_store(catalog_path.resolve(), actor)
        bound_identity_ids = sorted(
            {
                str(item.get("identity_id", "")).strip()
                for item in (store.get("bindings") or [])
                if isinstance(item, dict) and str(item.get("identity_id", "")).strip()
            }
        )
        if bound_identity_ids:
            raise SystemExit(
                "actor has multiple session-primary identities; "
                f"pass --session-id or --identity-id explicitly: actor={actor} identities={','.join(bound_identity_ids)}"
            )

    if default_id:
        active = next((x for x in identities if isinstance(x, dict) and x.get("id") == default_id), None)
        if not active:
            raise SystemExit(f"default_identity not found in identities: {default_id}")
        return active

    active_rows = [x for x in identities if isinstance(x, dict) and str(x.get("status", "")).lower() == "active"]
    if len(active_rows) == 1:
        return active_rows[0]
    if len(active_rows) > 1:
        raise SystemExit("multiple active identities found; pass --identity-id or --actor-id explicitly")
    raise SystemExit("identity-neutral baseline with no active/default identity; pass --identity-id explicitly")


def _resolve_compile_actor_id(explicit_actor_id: str = "") -> str:
    return resolve_protocol_actor_id(explicit_actor_id, allow_host_fallback=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", default="")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--identity-id", default="", help="explicit identity id for identity-neutral baseline")
    p.add_argument("--actor-id", default="", help="optional actor id used for actor-scoped identity resolution")
    p.add_argument(
        "--session-id",
        default="",
        help="optional session-primary selector (run:<id>) used for multi-session actor resolution",
    )
    args = p.parse_args()

    catalog_path = resolve_local_catalog_path(args.catalog, start=SCRIPT_DIR)
    catalog = load_yaml(catalog_path)
    repo_catalog_path = DEFAULT_REPO_CATALOG

    default_id = str(catalog.get("default_identity") or "").strip()
    explicit_id = str(args.identity_id or "").strip()
    actor_id = _resolve_compile_actor_id(args.actor_id)
    identities = catalog.get("identities") or []
    if not isinstance(identities, list):
        raise SystemExit("Invalid catalog: identities missing")
    active = _pick_active_identity(
        catalog_path,
        identities,
        explicit_id=explicit_id,
        actor_id=actor_id,
        session_id=str(args.session_id or "").strip(),
        default_id=default_id,
    )
    active_id = str(active.get("id", "")).strip()
    resolved_ctx = resolve_identity(
        active_id,
        repo_catalog_path,
        catalog_path,
        preferred_scope="USER",
    )
    source_layer = str(resolved_ctx.get("source_layer", "")).strip() or "unknown"
    runtime_mode = str(resolved_ctx.get("runtime_mode", "")).strip() or str(active.get("runtime_mode", "")).strip()
    pack_path = Path(str(resolved_ctx.get("resolved_pack_path", "")).strip() or active.get("pack_path", "")).expanduser().resolve()
    current_task_path = pack_path / "CURRENT_TASK.json"
    if not current_task_path.exists():
        legacy = Path("identity") / active["id"] / "CURRENT_TASK.json"
        current_task_path = legacy if legacy.exists() else current_task_path

    if not current_task_path.exists():
        raise SystemExit(f"CURRENT_TASK.json not found: {current_task_path}")

    current_task = json.loads(current_task_path.read_text(encoding="utf-8"))
    agent_identity = current_task.get("agent_identity") or {}
    prompt_version = str(agent_identity.get("prompt_version", "")).strip() or str(agent_identity.get("methodology_version", "")).strip()
    native_chat_contract = _normalize_native_chat_headstamp_contract(
        current_task.get("native_chat_headstamp_contract_v1")
    )
    native_chat_template, native_chat_template_path = _load_native_chat_headstamp_template(
        str(native_chat_contract.get("template_ref", "")).strip()
    )
    native_chat_machine_profile = _normalize_native_chat_machine_profile(
        native_chat_contract.get("default_machine_profile", "mini")
    )
    headstamp_semantics_template, headstamp_semantics_template_path = _load_headstamp_surface_semantics_template(
        DEFAULT_HEADSTAMP_SURFACE_SEMANTICS_TEMPLATE_REF
    )
    prompt_hard_guard_template, prompt_hard_guard_template_path = load_native_chat_prompt_hard_guard_template(
        DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF
    )
    headstamp_clarity_freeze = (
        headstamp_semantics_template.get("clarity_freeze")
        if isinstance(headstamp_semantics_template.get("clarity_freeze"), dict)
        else {}
    )
    success_identity_line = render_native_chat_success_identity_placeholder_line(actor_id=actor_id)
    success_machine_line = render_native_chat_success_machine_placeholder_line(
        actor_id=actor_id,
        default_machine_profile=native_chat_machine_profile,
        template_ref=str(native_chat_contract.get("template_ref", "")).strip(),
    )
    failure_identity_line = render_native_chat_failure_identity_placeholder_line(actor_id=actor_id)
    failure_machine_line = render_native_chat_failure_machine_placeholder_line(
        default_machine_profile=native_chat_machine_profile,
        template_ref=str(native_chat_contract.get("template_ref", "")).strip(),
    )
    prompt_hard_guard_intro = str(
        prompt_hard_guard_template.get(
            "section_intro",
            "Apply these hard rules to every assistant-authored user-visible native-chat reply.",
        )
    ).strip()
    prompt_hard_guard_invariants = [
        str(item).strip()
        for item in (prompt_hard_guard_template.get("required_invariants") or [])
        if str(item).strip()
    ]
    prompt_hard_guard_success_order = _sequence_to_arrow(list(prompt_hard_guard_template.get("success_order") or []))
    prompt_hard_guard_failure_order = _sequence_to_arrow(list(prompt_hard_guard_template.get("failure_order") or []))
    compiled_brief_projection_rule = str(
        headstamp_clarity_freeze.get(
            "compiled_brief_projection_rule",
            "shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.",
        )
    ).strip()
    compiled_brief_default_reply_rule = str(
        headstamp_clarity_freeze.get(
            "compiled_brief_default_reply_rule",
            "without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.",
        )
    ).strip()
    failure_envelope_claim_scope = str(
        headstamp_clarity_freeze.get(
            "failure_envelope_claim_scope",
            "`requested_identity_id` in native-chat failure line 1 is the requested target only; it never proves the current speaking identity.",
        )
    ).strip()
    compatibility_pointer_diagnostic_rule = str(
        headstamp_clarity_freeze.get(
            "compatibility_pointer_diagnostic_rule",
            "`compatibility_pointer_identity_id` is diagnostic-only compatibility metadata; it MUST NOT replace `identity_id` or appear as success-state identity injection.",
        )
    ).strip()
    failure_profile_default_rule = str(
        headstamp_clarity_freeze.get(
            "failure_profile_default",
            "native-chat failure `Machine-Verification` defaults to the compact `mini` profile unless debug/audit context explicitly requires escalation.",
        )
    ).strip()
    top_reply_hard_guard = render_native_chat_compiled_brief_reply_hard_guard_markdown(
        actor_id=actor_id,
        default_machine_profile=native_chat_machine_profile,
        machine_profile_template_ref=str(native_chat_contract.get("template_ref", "")).strip(),
    ).strip()

    lines = [
        "# Identity Runtime Brief",
        "",
        top_reply_hard_guard,
        "",
        "This file is generated/maintained by identity runtime tooling.",
        "",
        "Artifact classification:",
        "- artifact_class: tracked_compiled_brief_artifact",
        "- path_status: tracked_compiled_brief_frozen_path",
        "- generation_mode: source_first",
        f"- runtime_mode_default: {runtime_mode or '(missing)'}",
        f"- default_machine_profile: `{native_chat_machine_profile}`",
        f"- {compiled_brief_projection_rule}",
        f"- {compiled_brief_default_reply_rule}",
        f"- compile/runtime authority note: {str(headstamp_clarity_freeze.get('compile_runtime_authority', 'compile/replay metadata may read compatibility mirror; current-session authority must not.')).strip()}",
        "",
        "Source-first generation inputs:",
        "- `${IDENTITY_CATALOG}`",
        "- `${IDENTITY_HOME}/<resolved_identity_id>/CURRENT_TASK.json`",
        "- `${IDENTITY_HOME}/<resolved_identity_id>/IDENTITY_PROMPT.md`",
        "",
        "Native chat assistant-visible headstamp contract:",
        "- Apply this contract to every assistant-authored user-visible native-chat reply.",
        "- Success order is fixed: `Identity-Context` first, `Machine-Verification` second, then body.",
        f"- Native chat machine profile default: `{native_chat_machine_profile}`.",
        "- Available native chat machine profiles: `mini`, `standard`, `audit`.",
        (
            "- `mini`: compact human-facing default; fields = "
            f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='mini')['field_order'])}`."
        ),
        (
            "- `standard`: readable debug projection; fields = "
            f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='standard')['field_order'])}`."
        ),
        (
            "- `audit`: full lineage/debug projection; fields = "
            f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='audit')['field_order'])}`."
        ),
        "- Failure `mini`: compact fail-close projection; fields = "
        f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='mini', failure=True)['field_order'])}`.",
        "- Failure `standard`: readable fail-close debug projection; fields = "
        f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='standard', failure=True)['field_order'])}`.",
        "- Failure `audit`: full fail-close audit projection; fields = "
        f"`{_format_profile_fields(_resolve_native_chat_profile_doc(native_chat_template, profile_name='audit', failure=True)['field_order'])}`.",
        "- Ordinary user-facing native chat replies must stay on `mini`; only expand to `standard` or `audit` when debug/audit context explicitly requires it.",
        f"- {failure_profile_default_rule}",
        "- This native-chat path is the standard assistant-visible delivery path for host-native chat surfaces.",
        f"- {str(headstamp_clarity_freeze.get('sender_boundary_visibility', 'Ordinary replies should stay focused on the standard native-chat output path; governed receipt or attestation boundaries are audit/debug-only.')).strip()}",
        "- Native-chat display alone does not replace governed proof, admission, or runtime receipt ownership.",
        "- Governed repo-controlled surfaces keep the separate `Display-Headstamp` + `Machine-Verification` envelope; do not replace that contract here.",
        f"- {compiled_brief_projection_rule}",
        f"- {compiled_brief_default_reply_rule}",
        f"- {failure_envelope_claim_scope}",
        f"- {compatibility_pointer_diagnostic_rule}",
        "- If machine verification is missing, conflicted, or polluted, do not emit a success identity line; emit a withheld/conflict `Identity-Context` plus `Machine-Verification: verification_status=FAIL_REQUIRED ...` instead.",
        "- Runtime loop is fixed: `machine-verify -> assistant-visible-inject -> next turn re-verify`.",
        "",
        "Native chat headstamp hard guard:",
        f"- template source: `{prompt_hard_guard_template_path.as_posix()}`.",
        f"- {prompt_hard_guard_intro}",
    ]
    lines.extend([f"- {item}" for item in prompt_hard_guard_invariants])
    lines += [
        f"- Success visible order: `{prompt_hard_guard_success_order}`.",
        f"- Failure visible order: `{prompt_hard_guard_failure_order}`.",
        f"- Success example line 1 (schematic only; placeholders resolve only from current-turn machine tuple): `{success_identity_line}`",
        f"- Success example line 2 (schematic only; profile `{native_chat_machine_profile}`): `{success_machine_line}`",
        f"- Failure example line 1: `{failure_identity_line}`",
        f"- Failure example line 2: `{failure_machine_line}`",
    ]
    lines += [
        "",
        "Headstamp semantic clarity freeze:",
        f"- canonical semantic matrix template: `{headstamp_semantics_template_path.as_posix()}`.",
        "- surface semantics matrix:",
    ]
    for row in headstamp_semantics_template.get("surface_semantics_matrix") or []:
        if not isinstance(row, dict):
            continue
        label = str(row.get("surface_label", row.get("surface_id", ""))).strip() or "surface"
        visible_order = _sequence_to_arrow(list(row.get("visible_order") or []))
        primary_literal = str(row.get("primary_human_literal", "")).strip()
        proof_owner = str(row.get("proof_owner", "")).strip()
        lines.append(
            f"- `{label}`: visible order = `{visible_order}`; first literal = `{primary_literal}`; proof owner = `{proof_owner}`."
        )
    lines += [
        "- three orders matrix:",
    ]
    for row in headstamp_semantics_template.get("three_orders_matrix") or []:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", row.get("order_id", ""))).strip() or "order"
        applies_to = str(row.get("applies_to", "")).strip()
        sequence = _sequence_to_arrow(list(row.get("sequence") or []))
        not_equivalent_to = str(row.get("not_equivalent_to", "")).strip()
        lines.append(
            f"- `{label}` ({applies_to}): `{sequence}`; do not collapse with `{not_equivalent_to}`."
        )
    lines += [
        "- object vs literal mapping:",
    ]
    for row in headstamp_semantics_template.get("object_literal_mapping") or []:
        if not isinstance(row, dict):
            continue
        obj = str(row.get("semantic_object", "")).strip() or "object"
        native_literal = str(row.get("native_chat_literal", "")).strip()
        governed_literal = str(row.get("governed_literal", "")).strip()
        authority_rule = str(row.get("authority_rule", "")).strip()
        lines.append(
            f"- `{obj}`: native literal = `{native_literal}`; governed literal = `{governed_literal}`; rule = {authority_rule}"
        )
    lines += [
        f"- {str(headstamp_clarity_freeze.get('manual_headstamp', '`manual_headstamp` = render_origin tag only; never verdict axis.')).strip()}",
        f"- {str(headstamp_clarity_freeze.get('excluded_non_blocking', '`EXCLUDED_NON_BLOCKING` only removes blocker aggregation; it never upgrades next-hop admission.')).strip()}",
        f"- {str(headstamp_clarity_freeze.get('sender_boundary_visibility', 'Ordinary replies should stay focused on the standard native-chat output path; governed receipt or attestation boundaries are audit/debug-only.')).strip()}",
        f"- {compiled_brief_projection_rule}",
        f"- {compiled_brief_default_reply_rule}",
        "",
        "See source:",
        "- ${IDENTITY_CATALOG}",
        "- ${IDENTITY_HOME}/<resolved_identity_id>/CURRENT_TASK.json  # resolved via catalog pack_path",
        "- ${IDENTITY_HOME}/<resolved_identity_id>/IDENTITY_PROMPT.md  # resolved via catalog pack_path",
        f"- {native_chat_template_path}",
        f"- {prompt_hard_guard_template_path}",
        f"- {headstamp_semantics_template_path}",
    ]

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0

"""main function"""
if __name__ == "__main__":
    raise SystemExit(main())
