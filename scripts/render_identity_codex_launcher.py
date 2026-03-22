#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    GENERIC_LAUNCHER_NAME,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    default_bin_dir,
    ensure_launcher_assets,
    exec_identity_codex,
    launcher_manifest_doc,
    launcher_readme_text,
    render_generic_launcher_sh,
    render_shortcut_launcher_sh,
    resolve_catalog_path,
    resolve_launcher_pack_task,
    shortcut_launcher_name,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _resolve_resume_thread(identity_id: str, explicit_thread_id: str) -> tuple[str, str]:
    explicit = str(explicit_thread_id or "").strip()
    if explicit:
        return explicit, "explicit_thread_id"
    host_thread_id = str(os.environ.get("CODEX_THREAD_ID", "")).strip()
    if not host_thread_id:
        return "", "host_thread_id_missing"
    current_identity_id = str(os.environ.get("IDENTITY_BOOTSTRAP_IDENTITY_ID", "")).strip()
    if current_identity_id and current_identity_id != identity_id:
        return "", "current_host_thread_belongs_to_another_identity"
    return host_thread_id, "current_host_thread"


def _build_shell_command(raw_command: list[str]) -> str:
    command_text = _shell_join(raw_command).replace("'", "'\"'\"'")
    return f"zsh -lic '{command_text}'"


def _emit_commands(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        _emit(payload, json_only=True)
        return
    print(f"identity_id={payload['identity_id']}")
    print(f"preferred_start={payload['preferred_start_command']}")
    print(f"absolute_start={payload['absolute_start_command']}")
    print(f"generic_start={payload['generic_start_command']}")
    if str(payload.get("resume_status", "")).strip() == STATUS_PASS_REQUIRED:
        print(f"preferred_resume={payload['preferred_resume_command']}")
        print(f"absolute_resume={payload['absolute_resume_command']}")
        print(f"generic_resume={payload['generic_resume_command']}")
    else:
        print(f"resume_status={payload.get('resume_status', STATUS_SKIPPED_NOT_REQUIRED)}")
        print(f"resume_reason={payload.get('resume_reason', 'host_thread_id_required')}")


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


def _cmd_commands(args: argparse.Namespace) -> int:
    catalog_path = resolve_catalog_path(args.catalog)
    pack_root, task_path, _task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )
    bin_dir = Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()
    shortcut = shortcut_launcher_name(args.identity_id)
    shortcut_path = (bin_dir / shortcut).resolve()
    generic_path = (bin_dir / GENERIC_LAUNCHER_NAME).resolve()

    start_short = [shortcut]
    start_generic = [GENERIC_LAUNCHER_NAME, "--identity-id", args.identity_id]
    preferred_start_command = _build_shell_command(start_short)
    preferred_generic_start_command = _build_shell_command(start_generic)

    thread_id, thread_source = _resolve_resume_thread(args.identity_id, args.thread_id)
    resume_status = STATUS_PASS_REQUIRED if thread_id else STATUS_SKIPPED_NOT_REQUIRED
    payload = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "bin_dir": str(bin_dir),
        "shortcut_command": shortcut,
        "generic_command": GENERIC_LAUNCHER_NAME,
        "shortcut_launcher_path": str(shortcut_path),
        "generic_launcher_path": str(generic_path),
        "preferred_start_command": preferred_start_command,
        "absolute_start_command": _shell_join([str(shortcut_path)]),
        "generic_start_command": preferred_generic_start_command,
        "resume_status": resume_status,
        "current_host_thread_id": thread_id,
        "resume_thread_source": thread_source,
    }
    if thread_id:
        resume_short = [shortcut, "resume", thread_id]
        resume_generic = [GENERIC_LAUNCHER_NAME, "--identity-id", args.identity_id, "--", "resume", thread_id]
        payload.update(
            {
                "preferred_resume_command": _build_shell_command(resume_short),
                "absolute_resume_command": _shell_join([str(shortcut_path), "resume", thread_id]),
                "generic_resume_command": _build_shell_command(resume_generic),
            }
        )
    else:
        payload["resume_reason"] = thread_source
    _emit_commands(payload, json_only=args.json_only)
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

    p_commands = sub.add_parser(
        "commands",
        help="Print full copyable start/resume commands for one identity",
    )
    p_commands.add_argument("--identity-id", required=True)
    p_commands.add_argument("--catalog", default="")
    p_commands.add_argument("--current-task", default="")
    p_commands.add_argument("--bin-dir", default="")
    p_commands.add_argument("--thread-id", default="")
    p_commands.add_argument("--json-only", action="store_true")
    p_commands.set_defaults(func=_cmd_commands)

    args = ap.parse_args()
    if getattr(args, "codex_args", None) and args.codex_args and args.codex_args[0] == "--":
        args.codex_args = args.codex_args[1:]
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
