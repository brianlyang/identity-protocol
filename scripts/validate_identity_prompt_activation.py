#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from resolve_identity_context import resolve_identity


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _latest(identity_id: str, report_dir: Path) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    rows = [p for p in rows if not p.name.endswith("-patch-plan.json")]
    return rows[-1] if rows else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate IDENTITY_PROMPT activation contract from execution report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="/tmp/identity-upgrade-reports")
    ap.add_argument("--scope", default="")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser().resolve() if args.report else _latest(
        args.identity_id, Path(args.report_dir).expanduser().resolve()
    )
    if report_path is None or not report_path.exists():
        print(f"[FAIL] execution report not found for identity={args.identity_id}")
        return 1
    data = json.loads(report_path.read_text(encoding="utf-8"))

    required = [
        "identity_prompt_path",
        "identity_prompt_sha256",
        "identity_prompt_bytes",
        "identity_prompt_activated_at",
        "identity_prompt_source_layer",
        "identity_prompt_scope",
        "identity_prompt_status",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"[FAIL] prompt activation fields missing in report: {missing}")
        return 1

    prompt_path = Path(str(data.get("identity_prompt_path", ""))).expanduser().resolve()
    status = str(data.get("identity_prompt_status", "")).strip().upper()
    sha = str(data.get("identity_prompt_sha256", "")).strip()
    b = int(data.get("identity_prompt_bytes", 0) or 0)
    if status != "ACTIVATED":
        print(f"[FAIL] identity_prompt_status must be ACTIVATED, got: {status}")
        return 1
    if not prompt_path.exists():
        print(f"[FAIL] prompt path missing on disk: {prompt_path}")
        return 1
    disk_sha = _sha256(prompt_path)
    disk_b = int(prompt_path.stat().st_size)
    if sha != disk_sha:
        print(f"[FAIL] prompt sha mismatch report={sha} disk={disk_sha}")
        return 1
    if b != disk_b:
        print(f"[FAIL] prompt bytes mismatch report={b} disk={disk_b}")
        return 1

    ctx = resolve_identity(
        args.identity_id,
        Path(args.repo_catalog).expanduser().resolve(),
        Path(args.catalog).expanduser().resolve(),
        preferred_scope=str(args.scope or ""),
        allow_conflict=True,
    )
    resolved_path = Path(str(ctx.get("resolved_pack_path") or ctx.get("pack_path") or "")).expanduser().resolve() / "IDENTITY_PROMPT.md"
    if resolved_path != prompt_path:
        print(f"[FAIL] prompt path not aligned with resolved pack path: report={prompt_path} resolved={resolved_path}")
        return 1
    source_layer = str(ctx.get("source_layer", "")).strip()
    resolved_scope = str(ctx.get("resolved_scope", "")).strip()
    if str(data.get("identity_prompt_source_layer", "")).strip() != source_layer:
        print(
            f"[FAIL] identity_prompt_source_layer mismatch: report={data.get('identity_prompt_source_layer')} resolved={source_layer}"
        )
        return 1
    if str(data.get("identity_prompt_scope", "")).strip() != resolved_scope:
        print(f"[FAIL] identity_prompt_scope mismatch: report={data.get('identity_prompt_scope')} resolved={resolved_scope}")
        return 1

    print(f"[OK] identity prompt activation validated: {report_path}")
    print(f"     prompt={prompt_path}")
    print(f"     sha256={sha}")
    print(f"     bytes={b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

