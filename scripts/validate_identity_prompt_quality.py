#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import json

from native_chat_headstamp_common import prompt_hard_guard_required_tokens
from resolve_identity_context import resolve_identity


def _score_prompt(
    text: str,
    *,
    min_prompt_bytes: int = 200,
    required_sections: list[str] | None = None,
    forbid_template_markers: list[str] | None = None,
    required_literals: list[str] | None = None,
) -> tuple[bool, list[str]]:
    fails: list[str] = []
    if len(text.strip()) < int(min_prompt_bytes):
        fails.append(f"IDENTITY_PROMPT.md too short (<{min_prompt_bytes} chars)")
    lowered = text.lower()
    required_tokens = [
        "role",
        "principle",
        "decision",
        "gate",
    ]
    missing = [t for t in required_tokens if t not in lowered]
    if missing:
        fails.append(f"IDENTITY_PROMPT.md missing governance tokens: {missing}")
    for section in (required_sections or []):
        if str(section).strip() and str(section).lower() not in lowered:
            fails.append(f"IDENTITY_PROMPT.md missing required section marker: {section}")
    for marker in (forbid_template_markers or []):
        if str(marker).strip() and str(marker).lower() in lowered:
            fails.append(f"IDENTITY_PROMPT.md contains forbidden template marker: {marker}")
    for literal in (required_literals or []):
        if str(literal).strip() and str(literal) not in text:
            fails.append(f"IDENTITY_PROMPT.md missing required literal: {literal}")
    return (len(fails) == 0), fails


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity prompt quality baseline for runtime governance.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True, help="local runtime catalog path")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="", help="optional explicit scope (USER|SYSTEM|...); use AUTO/empty to infer")
    args = ap.parse_args()

    preferred_scope = str(args.scope or "").strip()
    if preferred_scope.upper() == "AUTO":
        preferred_scope = ""

    ctx = resolve_identity(
        args.identity_id,
        Path(args.repo_catalog).expanduser().resolve(),
        Path(args.catalog).expanduser().resolve(),
        preferred_scope=preferred_scope,
        allow_conflict=True,
    )
    pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    prompt = pack / "IDENTITY_PROMPT.md"
    if not prompt.exists():
        print(f"[FAIL] identity prompt missing: {prompt}")
        return 1
    text = prompt.read_text(encoding="utf-8", errors="ignore")
    task_path = pack / "CURRENT_TASK.json"
    min_prompt_bytes = 200
    required_sections: list[str] = []
    forbid_template_markers: list[str] = []
    required_literals: list[str] = []
    if task_path.exists():
        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
            contract = task.get("identity_prompt_activation_contract") or {}
            if isinstance(contract, dict):
                min_prompt_bytes = int(contract.get("min_prompt_bytes", 200))
                required_sections = [str(x) for x in (contract.get("required_sections") or []) if str(x).strip()]
                forbid_template_markers = [
                    str(x) for x in (contract.get("forbid_template_markers") or []) if str(x).strip()
                ]
            native_chat_contract = task.get("native_chat_headstamp_contract_v1") or {}
            if isinstance(native_chat_contract, dict) and native_chat_contract.get("required") is True:
                required_literals.extend(
                    prompt_hard_guard_required_tokens(
                        default_machine_profile=str(native_chat_contract.get("default_machine_profile", "mini")),
                        template_ref=str(native_chat_contract.get("prompt_hard_guard_template_ref", "")).strip(),
                    )
                )
        except Exception:
            pass
    ok, fails = _score_prompt(
        text,
        min_prompt_bytes=min_prompt_bytes,
        required_sections=required_sections,
        forbid_template_markers=forbid_template_markers,
        required_literals=required_literals,
    )
    if not ok:
        for f in fails:
            print(f"[FAIL] {f}")
        print(f"[FAIL] prompt quality gate failed for identity={args.identity_id} prompt={prompt}")
        return 1
    print(f"[OK] prompt quality gate passed: identity={args.identity_id} prompt={prompt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
