#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    default_bin_dir,
    ensure_launcher_assets,
    exec_identity_codex,
    launcher_manifest_doc,
    launcher_readme_text,
    render_generic_launcher_sh,
    render_shortcut_launcher_sh,
    resolve_catalog_path,
    resolve_launcher_pack_task,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _cmd_render(args: argparse.Namespace) -> int:
    catalog_path = resolve_catalog_path(args.catalog)
    pack_root, task_path, _task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )
    payload = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str((pack_root / "scripts" / "launchers" / "identity-codex-launcher.manifest.json").resolve()),
        "readme_path": str((pack_root / "scripts" / "launchers" / "README.md").resolve()),
        "bin_dir": str(Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()),
        "manifest_doc": launcher_manifest_doc(args.identity_id),
        "readme_text": launcher_readme_text(args.identity_id),
        "generic_launcher_text": render_generic_launcher_sh(),
        "shortcut_launcher_text": render_shortcut_launcher_sh(args.identity_id),
    }
    _emit(payload, json_only=args.json_only)
    return 0


def _cmd_write_pack_assets(args: argparse.Namespace) -> int:
    catalog_path = resolve_catalog_path(args.catalog)
    pack_root, task_path, _task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )
    result = ensure_launcher_assets(pack_root, args.identity_id)
    payload = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        **result,
    }
    _emit(payload, json_only=args.json_only)
    return 0


def _cmd_exec(args: argparse.Namespace) -> int:
    codex_args = list(args.codex_args or [])
    try:
        payload = exec_identity_codex(
            identity_id=args.identity_id,
            codex_args=codex_args,
            actor_id=args.actor_id,
            explicit_session_id=args.session_id,
            raw_catalog=args.catalog,
            work_layer=args.work_layer,
            machine_profile=args.machine_profile,
            explicit_config=args.config,
            explicit_base_instructions_file=args.base_instructions_file,
            dry_run=bool(args.dry_run),
        )
    except Exception as exc:
        _emit(
            {
                "status": STATUS_FAIL_REQUIRED,
                "identity_id": args.identity_id,
                "error": str(exc),
            },
            json_only=args.json_only,
        )
        return 1
    if args.dry_run:
        _emit(payload, json_only=args.json_only)
        return 0
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Protocol-owned identity Codex launcher renderer / entrypoint.")
    sub = ap.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="Render launcher manifest and shim payloads without writing")
    p_render.add_argument("--identity-id", required=True)
    p_render.add_argument("--catalog", default="")
    p_render.add_argument("--current-task", default="")
    p_render.add_argument("--bin-dir", default="")
    p_render.add_argument("--json-only", action="store_true")
    p_render.set_defaults(func=_cmd_render)

    p_write = sub.add_parser("write-pack-assets", help="Write pack-local launcher manifest and README")
    p_write.add_argument("--identity-id", required=True)
    p_write.add_argument("--catalog", default="")
    p_write.add_argument("--current-task", default="")
    p_write.add_argument("--json-only", action="store_true")
    p_write.set_defaults(func=_cmd_write_pack_assets)

    p_exec = sub.add_parser("exec", help="Launch codex through the governed identity launcher")
    p_exec.add_argument("--identity-id", required=True)
    p_exec.add_argument("--actor-id", default="assistant:codex")
    p_exec.add_argument("--session-id", default="")
    p_exec.add_argument("--catalog", default="")
    p_exec.add_argument("--work-layer", default="instance")
    p_exec.add_argument("--machine-profile", default="mini", choices=["mini", "standard", "audit"])
    p_exec.add_argument("--config", default="")
    p_exec.add_argument("--base-instructions-file", default="")
    p_exec.add_argument("--dry-run", action="store_true")
    p_exec.add_argument("--json-only", action="store_true")
    p_exec.add_argument("codex_args", nargs=argparse.REMAINDER)
    p_exec.set_defaults(func=_cmd_exec)

    args = ap.parse_args()
    if getattr(args, "codex_args", None) and args.codex_args and args.codex_args[0] == "--":
        args.codex_args = args.codex_args[1:]
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

