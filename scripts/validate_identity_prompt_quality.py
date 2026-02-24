#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resolve_identity_context import resolve_identity


def _score_prompt(text: str) -> tuple[bool, list[str]]:
    fails: list[str] = []
    if len(text.strip()) < 200:
        fails.append("IDENTITY_PROMPT.md too short (<200 chars)")
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
    return (len(fails) == 0), fails


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity prompt quality baseline for runtime governance.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True, help="local runtime catalog path")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--scope", default="USER")
    args = ap.parse_args()

    ctx = resolve_identity(
        args.identity_id,
        Path(args.repo_catalog).expanduser().resolve(),
        Path(args.catalog).expanduser().resolve(),
        preferred_scope=args.scope,
        allow_conflict=True,
    )
    pack = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve()
    prompt = pack / "IDENTITY_PROMPT.md"
    if not prompt.exists():
        print(f"[FAIL] identity prompt missing: {prompt}")
        return 1
    text = prompt.read_text(encoding="utf-8", errors="ignore")
    ok, fails = _score_prompt(text)
    if not ok:
        for f in fails:
            print(f"[FAIL] {f}")
        print(f"[FAIL] prompt quality gate failed for identity={args.identity_id} prompt={prompt}")
        return 1
    print(f"[OK] prompt quality gate passed: identity={args.identity_id} prompt={prompt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

