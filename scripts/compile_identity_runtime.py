#!/usr/bin/env python3
"""Compile a concise identity runtime brief from catalog + active pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    load_actor_binding,
    load_actor_global_compatibility_projection,
    resolve_actor_id,
)
from resolve_identity_context import default_local_catalog_path, resolve_identity


SCRIPT_DIR = Path(__file__).resolve().parent
PROTOCOL_ROOT = SCRIPT_DIR.parent
DEFAULT_REPO_CATALOG = (PROTOCOL_ROOT / "identity" / "catalog" / "identities.yaml").resolve()
DEFAULT_OUTPUT = (PROTOCOL_ROOT / "identity" / "runtime" / "IDENTITY_COMPILED.md").resolve()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _format_source_entry(src: dict[str, Any]) -> str:
    if not isinstance(src, dict):
        return ""
    if src.get("repo") and src.get("path"):
        return f"{src.get('repo')}::{src.get('path')}"
    if src.get("url"):
        return str(src.get("url"))
    return ""


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _pick_active_identity(
    catalog_path: Path,
    identities: list[dict[str, Any]],
    *,
    explicit_id: str,
    actor_id: str,
    default_id: str,
) -> dict[str, Any]:
    if explicit_id:
        active = next((x for x in identities if isinstance(x, dict) and x.get("id") == explicit_id), None)
        if not active:
            raise SystemExit(f"identity_id not found in identities: {explicit_id}")
        return active

    actor_binding = load_actor_binding(
        catalog_path.resolve(),
        actor_id,
        identity_id="",
    )
    if not actor_binding:
        actor_binding = load_actor_global_compatibility_projection(
            catalog_path.resolve(),
            actor_id,
        )
    bound_identity_id = str(actor_binding.get("identity_id", "")).strip()
    if bound_identity_id:
        active = next((x for x in identities if isinstance(x, dict) and x.get("id") == bound_identity_id), None)
        if not active:
            raise SystemExit(f"actor-bound identity not found in identities: actor={actor_id} identity={bound_identity_id}")
        if str(active.get("status", "")).lower() != "active":
            raise SystemExit(
                f"actor-bound identity is not active: actor={actor_id} identity={bound_identity_id} "
                f"status={active.get('status', '')}"
            )
        return active

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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", default=str(default_local_catalog_path(start=SCRIPT_DIR)))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--identity-id", default="", help="explicit identity id for identity-neutral baseline")
    p.add_argument("--actor-id", default="", help="optional actor id used for actor-scoped identity resolution")
    args = p.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    catalog = load_yaml(catalog_path)
    repo_catalog_path = DEFAULT_REPO_CATALOG

    default_id = str(catalog.get("default_identity") or "").strip()
    explicit_id = str(args.identity_id or "").strip()
    actor_id = resolve_actor_id(args.actor_id)
    identities = catalog.get("identities") or []
    if not isinstance(identities, list):
        raise SystemExit("Invalid catalog: identities missing")
    active = _pick_active_identity(
        catalog_path,
        identities,
        explicit_id=explicit_id,
        actor_id=actor_id,
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
    scope = str(resolved_ctx.get("resolved_scope", "")).strip() or "USER"
    pack_path = Path(str(resolved_ctx.get("resolved_pack_path", "")).strip() or active.get("pack_path", "")).expanduser().resolve()
    current_task_path = pack_path / "CURRENT_TASK.json"
    if not current_task_path.exists():
        legacy = Path("identity") / active["id"] / "CURRENT_TASK.json"
        current_task_path = legacy if legacy.exists() else current_task_path

    if not current_task_path.exists():
        raise SystemExit(f"CURRENT_TASK.json not found: {current_task_path}")

    current_task = json.loads(current_task_path.read_text(encoding="utf-8"))
    agent_identity = current_task.get("agent_identity") or {}
    objective = (current_task.get("objective") or {}).get("title", "")
    state = (current_task.get("state_machine") or {}).get("current_state", "unknown")
    role = str(agent_identity.get("role", "")).strip()
    prompt_version = str(agent_identity.get("prompt_version", "")).strip() or str(agent_identity.get("methodology_version", "")).strip()
    methodology_version = str(agent_identity.get("methodology_version", "")).strip()
    prompt_path = pack_path / "IDENTITY_PROMPT.md"
    prompt_loaded = prompt_path.exists()
    prompt_digest = ""
    prompt_preview = ""
    if prompt_loaded:
        prompt_text = prompt_path.read_text(encoding="utf-8", errors="ignore").strip()
        prompt_digest = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        prompt_preview = " ".join(prompt_text.split())[:180]

    hard_guardrails = (((active.get("governance") or {}).get("hard_guardrails") or [])
        if isinstance(active.get("governance"), dict)
        else [])

    review_sources = []
    protocol_review_contract = current_task.get("protocol_review_contract") or {}
    for src in protocol_review_contract.get("must_review_sources") or []:
        formatted = _format_source_entry(src)
        if formatted:
            review_sources.append(formatted)

    canonical_pointer_path = (catalog_path.parent / "session" / "active_identity.json").resolve()
    pointer_payload = _load_json_if_exists(canonical_pointer_path)
    authority_source = str(pointer_payload.get("authoritative_source", "")).strip() or "actor_session_store"
    canonical_pointer_identity = str(pointer_payload.get("identity_id", "")).strip()

    native_identity_line = (
        f"Identity-Context: actor_id={actor_id}; identity_id={active_id}; scope={scope}; "
        f"lock=LOCK_MATCH; source={source_layer} | Layer-Context: work_layer=instance; source_layer={source_layer}"
    )
    native_machine_line = (
        f"Machine-Verification: authority_source={authority_source}; actor_id={actor_id}; identity_id={active_id}; "
        f"status=active; pointer_path={canonical_pointer_path}; prompt_version={prompt_version or 'unknown'}; "
        f"work_layer=instance; source_layer={source_layer}"
    )

    lines = [
        "# Identity Runtime Brief",
        "",
        f"Active identity: {active_id or 'unknown'}",
        f"Actor binding: {actor_id}",
        f"Resolved source layer: {source_layer}",
        "",
        "This file is generated/maintained by identity runtime tooling.",
        "",
        "Hard guardrails:",
    ]
    lines.extend([f"- {g}" for g in hard_guardrails] or ["- (none)"])

    lines += [
        "",
        "Current objective:",
        f"- {objective or '(not set)'}",
        "",
        "Current state:",
        f"- {state}",
        "",
        "Identity runtime metadata:",
        f"- role: {role or '(missing)'}",
        f"- prompt_version: {prompt_version or '(missing)'}",
        f"- methodology_version: {methodology_version or '(missing)'}",
        f"- runtime_mode: {runtime_mode or '(missing)'}",
        f"- canonical_pointer_path: {canonical_pointer_path}",
        f"- canonical_pointer_identity: {canonical_pointer_identity or '(missing)'}",
        f"- authority_source: {authority_source}",
        "",
        "Identity prompt activation:",
        f"- prompt_path: {prompt_path.as_posix()}",
        f"- prompt_loaded: {'yes' if prompt_loaded else 'no'}",
        f"- prompt_sha256: {prompt_digest or '(missing)'}",
        f"- prompt_preview: {prompt_preview or '(missing)'}",
    ]

    if review_sources:
        lines += [
            "",
            "Runtime baseline review references:",
        ]
        lines.extend([f"- {s}" for s in review_sources])

    lines += [
        "",
        "Native chat assistant-visible headstamp contract:",
        "- Apply this contract to every assistant-authored user-visible native-chat reply.",
        "- Success order is fixed: `Identity-Context` first, `Machine-Verification` second, then body.",
        f"- Success line 1 example: `{native_identity_line}`",
        f"- Success line 2 example: `{native_machine_line}`",
        "- This native-chat path is assistant text-layer injection, not host sender physical injection.",
        "- Governed repo-controlled surfaces keep the separate `Display-Headstamp` + `Machine-Verification` envelope; do not replace that contract here.",
        "- If machine verification is missing, conflicted, or polluted, do not emit a success identity line; emit a withheld/conflict `Identity-Context` plus `Machine-Verification: verification_status=FAIL_REQUIRED ...` instead.",
        "- Runtime loop is fixed: `machine-verify -> assistant-visible-inject -> next turn re-verify`.",
        "",
        "See source:",
        "- ${IDENTITY_CATALOG}",
        f"- ${{IDENTITY_HOME}}/{active_id or 'unknown'}/CURRENT_TASK.json  # resolved via catalog pack_path",
    ]

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0

"""main function"""
if __name__ == "__main__":
    raise SystemExit(main())
