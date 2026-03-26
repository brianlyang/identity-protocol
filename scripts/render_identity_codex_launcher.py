#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path
from typing import Any

from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from identity_codex_launcher_common import (
    GENERIC_LAUNCHER_NAME,
    IDENTITY_LAUNCHER_COMMAND_DISCOVERY_CONTRACT_ID,
    IDENTITY_LAUNCHER_COMMAND_DISCOVERY_QUESTION_FAMILY,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    default_bin_dir,
    ensure_launcher_assets,
    exec_identity_codex,
    observe_launcher_surface,
    launcher_manifest_doc,
    launcher_readme_text,
    launcher_command_discovery_doc,
    load_launcher_continuity_support_bundle,
    render_generic_launcher_sh,
    render_shortcut_launcher_sh,
    resolve_catalog_path,
    resolve_launcher_tuple,
    resolve_launcher_pack_task,
    resolve_protocol_root,
    resolve_required_protocol_actor_id,
    shortcut_launcher_name,
)
from launcher_runtime_admissibility_projection_common import (
    build_launcher_runtime_admissibility_projection,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _build_display_command(raw_command: list[str]) -> str:
    return _shell_join(raw_command)


def _build_launcher_runtime_guard_fail_payload(
    *,
    identity_id: str,
    catalog_path: Path,
    admissibility_projection: dict[str, Any],
) -> dict[str, Any]:
    binding_class = str(admissibility_projection.get("runtime_mode_guard_binding_class", "")).strip()
    error_code = str(admissibility_projection.get("runtime_mode_guard_error_code", "")).strip()
    admissibility_reason = binding_class or error_code or "runtime_mode_guard_blocked"
    return {
        "status": STATUS_FAIL_REQUIRED,
        "command_bundle_contract_id": IDENTITY_LAUNCHER_COMMAND_DISCOVERY_CONTRACT_ID,
        "question_family": IDENTITY_LAUNCHER_COMMAND_DISCOVERY_QUESTION_FAMILY,
        "surface_governance": build_governed_runtime_summary_surface_payload(
            "identity_codex_launcher_command_bundle_surface"
        ),
        "identity_id": identity_id,
        "catalog_path": str(catalog_path),
        "ambient_catalog_path": str(resolve_catalog_path("")),
        "launcher_operator_surface_admissibility_status": str(
            admissibility_projection.get("launcher_runtime_admissibility_status", STATUS_FAIL_REQUIRED)
        ).strip()
        or STATUS_FAIL_REQUIRED,
        "launcher_operator_surface_admissibility_reason": admissibility_reason,
        "launcher_runtime_admissibility_projection": admissibility_projection,
        "launcher_runtime_admissibility_projection_status": str(
            admissibility_projection.get("launcher_runtime_admissibility_projection_status", STATUS_FAIL_REQUIRED)
        ).strip()
        or STATUS_FAIL_REQUIRED,
        "launcher_runtime_admissibility_status": str(
            admissibility_projection.get("launcher_runtime_admissibility_status", STATUS_FAIL_REQUIRED)
        ).strip()
        or STATUS_FAIL_REQUIRED,
        "launcher_runtime_admissibility_reason": str(
            admissibility_projection.get("launcher_runtime_admissibility_reason", admissibility_reason)
        ).strip()
        or admissibility_reason,
        "runtime_mode_guard_status": str(
            admissibility_projection.get("runtime_mode_guard_status", STATUS_FAIL_REQUIRED)
        ).strip()
        or STATUS_FAIL_REQUIRED,
        "runtime_mode_guard_error_code": error_code,
        "runtime_mode_guard_binding_class": binding_class,
        "runtime_mode_guard_payload": admissibility_projection.get("runtime_mode_guard_payload", {}),
        "preferred_start_command": "",
        "recommended_start_command": "",
        "preferred_resume_command": "",
        "recommended_resume_command": "",
        "recommended_user_command": "",
        "resume_status": STATUS_FAIL_REQUIRED,
        "runtime_mode_guard_stale_reasons": list(admissibility_projection.get("runtime_mode_guard_stale_reasons") or []),
        "projection_stale_reasons": list(admissibility_projection.get("stale_reasons") or []),
        "stale_reasons": list(
            admissibility_projection.get("runtime_mode_guard_stale_reasons")
            or admissibility_projection.get("stale_reasons")
            or []
        ),
        "error_code": error_code,
        "error": f"launcher_runtime_admissibility_blocked:{admissibility_reason}",
        "copyable_commands": {"start": None, "resume": None},
    }


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


def _build_generic_start_command(
    *,
    launcher: str,
    identity_id: str,
    catalog_path: Path,
    require_explicit_catalog: bool,
) -> str:
    parts = [launcher, "--identity-id", identity_id]
    if require_explicit_catalog:
        parts.extend(["--catalog", str(catalog_path)])
    return _build_display_command(parts)


def _build_generic_resume_command(
    *,
    launcher: str,
    identity_id: str,
    catalog_path: Path,
    thread_id: str,
    require_explicit_catalog: bool,
    session_id: str,
) -> str:
    parts = [launcher, "--identity-id", identity_id]
    if require_explicit_catalog:
        parts.extend(["--catalog", str(catalog_path)])
    if session_id:
        parts.extend(["--session-id", session_id])
    parts.extend(["--", "resume", thread_id])
    return _build_display_command(parts)


def _load_continuity_support_bundle(
    *,
    identity_id: str,
    catalog_path: Path,
    task_path: Path,
) -> dict[str, Any]:
    return load_launcher_continuity_support_bundle(
        identity_id=identity_id,
        catalog_path=catalog_path,
        task_path=task_path,
    )

def _emit_commands(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        _emit(payload, json_only=True)
        return
    if str(payload.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        print(f"identity_id={payload.get('identity_id', '')}")
        print(f"status={payload.get('status', STATUS_FAIL_REQUIRED)}")
        if str(payload.get("runtime_mode_guard_error_code", "")).strip():
            print(f"runtime_mode_guard_error_code={payload['runtime_mode_guard_error_code']}")
        if str(payload.get("runtime_mode_guard_binding_class", "")).strip():
            print(f"runtime_mode_guard_binding_class={payload['runtime_mode_guard_binding_class']}")
        print(
            "launcher_operator_surface_admissibility_status="
            f"{payload.get('launcher_operator_surface_admissibility_status', STATUS_FAIL_REQUIRED)}"
        )
        print(
            "launcher_operator_surface_admissibility_reason="
            f"{payload.get('launcher_operator_surface_admissibility_reason', 'runtime_mode_guard_blocked')}"
        )
        if str(payload.get("error", "")).strip():
            print(f"error={payload['error']}")
        return
    print(f"identity_id={payload['identity_id']}")
    print(f"recommended_command={payload['recommended_user_command']}")
    print(f"preferred_start={payload['preferred_start_command']}")
    shortcut_start_command = str(payload.get("shortcut_start_command", "")).strip()
    if shortcut_start_command and shortcut_start_command != payload["preferred_start_command"]:
        print(f"shortcut_start_reference={shortcut_start_command}")
    print(f"absolute_start={payload['absolute_start_command']}")
    print(f"generic_start={payload['generic_start_command']}")
    if str(payload.get("resume_status", "")).strip() == STATUS_PASS_REQUIRED:
        print(f"preferred_resume={payload['preferred_resume_command']}")
        shortcut_resume_command = str(payload.get("shortcut_resume_command", "")).strip()
        if shortcut_resume_command and shortcut_resume_command != payload["preferred_resume_command"]:
            print(f"shortcut_resume_reference={shortcut_resume_command}")
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
        "shortcut_launcher_text": render_shortcut_launcher_sh(
            args.identity_id,
            catalog_path,
            resolve_protocol_root(),
        ),
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
    protocol_home = resolve_protocol_root(str(os.environ.get("IDENTITY_PROTOCOL_HOME", "")).strip())
    catalog_path = resolve_catalog_path(args.catalog)
    admissibility_projection = build_launcher_runtime_admissibility_projection(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        operation="validate",
    )
    projection_status = str(
        admissibility_projection.get("launcher_runtime_admissibility_projection_status", "")
    ).strip()
    admissibility_status = str(admissibility_projection.get("launcher_runtime_admissibility_status", "")).strip()
    if projection_status != STATUS_PASS_REQUIRED or admissibility_status != STATUS_PASS_REQUIRED:
        _emit(
            {
                "status": STATUS_FAIL_REQUIRED,
                "identity_id": args.identity_id,
                "catalog_path": str(catalog_path),
                "launcher_exec_admissibility_status": admissibility_status or STATUS_FAIL_REQUIRED,
                "launcher_exec_admissibility_reason": str(
                    admissibility_projection.get("launcher_runtime_admissibility_reason")
                    or admissibility_projection.get("runtime_mode_guard_binding_class")
                    or admissibility_projection.get("runtime_mode_guard_error_code")
                    or "runtime_mode_guard_blocked"
                ),
                "runtime_mode_guard_status": str(
                    admissibility_projection.get("runtime_mode_guard_status", STATUS_FAIL_REQUIRED)
                ).strip()
                or STATUS_FAIL_REQUIRED,
                "runtime_mode_guard_error_code": str(
                    admissibility_projection.get("runtime_mode_guard_error_code", "")
                ).strip(),
                "runtime_mode_guard_binding_class": str(
                    admissibility_projection.get("runtime_mode_guard_binding_class", "")
                ).strip(),
                "launcher_runtime_admissibility_projection": admissibility_projection,
                "launcher_runtime_admissibility_projection_status": projection_status or STATUS_FAIL_REQUIRED,
                "runtime_mode_guard_payload": admissibility_projection.get("runtime_mode_guard_payload", {}),
                "error": "launcher_exec_runtime_admissibility_blocked",
            },
            json_only=args.json_only,
        )
        return 1
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
    payload.update(
        {
            "launcher_runtime_admissibility_projection": admissibility_projection,
            "launcher_runtime_admissibility_projection_status": projection_status or STATUS_FAIL_REQUIRED,
            "launcher_runtime_admissibility_status": admissibility_status or STATUS_FAIL_REQUIRED,
            "launcher_runtime_admissibility_reason": str(
                admissibility_projection.get("launcher_runtime_admissibility_reason", "")
            ).strip(),
            "runtime_mode_guard_status": str(
                admissibility_projection.get("runtime_mode_guard_status", STATUS_FAIL_REQUIRED)
            ).strip()
            or STATUS_FAIL_REQUIRED,
            "runtime_mode_guard_error_code": str(
                admissibility_projection.get("runtime_mode_guard_error_code", "")
            ).strip(),
            "runtime_mode_guard_binding_class": str(
                admissibility_projection.get("runtime_mode_guard_binding_class", "")
            ).strip(),
            "runtime_mode_guard_stale_reasons": list(
                admissibility_projection.get("runtime_mode_guard_stale_reasons") or []
            ),
            "projection_stale_reasons": list(admissibility_projection.get("stale_reasons") or []),
        }
    )
    if args.dry_run:
        _emit(payload, json_only=args.json_only)
        return 0
    return 0


def _cmd_commands(args: argparse.Namespace) -> int:
    catalog_path = resolve_catalog_path(args.catalog)
    protocol_home = resolve_protocol_root(str(os.environ.get("IDENTITY_PROTOCOL_HOME", "")).strip())
    admissibility_projection = build_launcher_runtime_admissibility_projection(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
        operation="inspection",
    )
    projection_status = str(
        admissibility_projection.get("launcher_runtime_admissibility_projection_status", "")
    ).strip()
    admissibility_status = str(admissibility_projection.get("launcher_runtime_admissibility_status", "")).strip()
    if projection_status != STATUS_PASS_REQUIRED or admissibility_status != STATUS_PASS_REQUIRED:
        _emit_commands(
            _build_launcher_runtime_guard_fail_payload(
                identity_id=args.identity_id,
                catalog_path=catalog_path,
                admissibility_projection=admissibility_projection,
            ),
            json_only=args.json_only,
        )
        return 1
    pack_root, task_path, _task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )
    actor_token = resolve_required_protocol_actor_id(str(args.actor_id or "").strip() or "assistant:codex")
    bin_dir = Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()
    shortcut = shortcut_launcher_name(args.identity_id)
    shortcut_path = (bin_dir / shortcut).resolve()
    generic_path = (bin_dir / GENERIC_LAUNCHER_NAME).resolve()
    ambient_catalog_path = resolve_catalog_path("")
    catalog_context_matches = ambient_catalog_path == catalog_path
    catalog_context_status = STATUS_PASS_REQUIRED if catalog_context_matches else STATUS_FAIL_REQUIRED
    catalog_context_reason = (
        "ambient_catalog_matches_resolved_catalog"
        if catalog_context_matches
        else "ambient_catalog_mismatch_requires_explicit_catalog"
    )
    require_explicit_catalog = not catalog_context_matches

    start_short = [shortcut]
    start_generic = [GENERIC_LAUNCHER_NAME, "--identity-id", args.identity_id]
    shortcut_start_command = _build_display_command(start_short)
    preferred_generic_start_command = _build_display_command(start_generic)
    absolute_start_command = _build_display_command([str(shortcut_path)])
    absolute_generic_start_command = _build_display_command([str(generic_path), "--identity-id", args.identity_id])
    fresh_shell_start_command = _build_generic_start_command(
        launcher=GENERIC_LAUNCHER_NAME,
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        require_explicit_catalog=require_explicit_catalog,
    )
    absolute_fresh_shell_start_command = _build_generic_start_command(
        launcher=str(generic_path),
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        require_explicit_catalog=require_explicit_catalog,
    )
    shortcut_surface = observe_launcher_surface(shortcut, shortcut_path)
    generic_surface = observe_launcher_surface(GENERIC_LAUNCHER_NAME, generic_path)
    shortcut_command_on_path = bool(shortcut_surface["command_on_path"])
    generic_command_on_path = bool(generic_surface["command_on_path"])
    shortcut_install_status = str(shortcut_surface["install_status"])
    generic_install_status = str(generic_surface["install_status"])
    if require_explicit_catalog:
        preferred_start_command = (
            fresh_shell_start_command
            if generic_command_on_path or generic_install_status != STATUS_PASS_REQUIRED
            else absolute_fresh_shell_start_command
        )
        preferred_start_surface_reason = "catalog_mismatch_requires_canonical_primary_surface"
    else:
        if shortcut_command_on_path:
            preferred_start_command = shortcut_start_command
            preferred_start_surface_reason = "shortcut_shell_discoverable_primary_surface"
        elif generic_command_on_path:
            preferred_start_command = preferred_generic_start_command
            preferred_start_surface_reason = "shortcut_shell_undiscoverable_promote_generic_primary_surface"
        elif shortcut_install_status == STATUS_PASS_REQUIRED:
            preferred_start_command = absolute_start_command
            preferred_start_surface_reason = "shortcut_shell_undiscoverable_promote_absolute_shortcut_surface"
        elif generic_install_status == STATUS_PASS_REQUIRED:
            preferred_start_command = absolute_generic_start_command
            preferred_start_surface_reason = "shortcut_shell_undiscoverable_promote_absolute_generic_surface"
        else:
            preferred_start_command = preferred_generic_start_command
            preferred_start_surface_reason = "launcher_install_missing_falls_back_to_generic_reference_surface"
    recommended_start_command = preferred_start_command
    command_discovery = launcher_command_discovery_doc(args.identity_id)

    thread_id, thread_source = _resolve_resume_thread(args.identity_id, args.thread_id)
    host_thread_id_status = STATUS_PASS_REQUIRED if thread_id else STATUS_SKIPPED_NOT_REQUIRED
    resolved_resume_session_id = ""
    resolved_resume_session_source = "resume_session_not_required"
    identity_session_tuple_status = STATUS_SKIPPED_NOT_REQUIRED
    identity_session_tuple_reason = "resume_thread_id_missing"
    if thread_id:
        try:
            resolved_resume_session_id, resolved_resume_session_source = resolve_launcher_tuple(
                identity_id=args.identity_id,
                actor_id=actor_token,
                explicit_session_id=str(args.session_id or ""),
                catalog_path=catalog_path,
                protocol_home=protocol_home,
            )
            identity_session_tuple_status = STATUS_PASS_REQUIRED if resolved_resume_session_id else STATUS_FAIL_REQUIRED
            identity_session_tuple_reason = (
                resolved_resume_session_source if resolved_resume_session_id else "session_tuple_unresolved"
            )
        except Exception as exc:
            identity_session_tuple_status = STATUS_FAIL_REQUIRED
            identity_session_tuple_reason = str(exc)
    resume_command_fresh_shell_executable_status = (
        STATUS_PASS_REQUIRED
        if thread_id and resolved_resume_session_id
        else (STATUS_FAIL_REQUIRED if thread_id else STATUS_SKIPPED_NOT_REQUIRED)
    )
    resume_status = resume_command_fresh_shell_executable_status
    continuity_support = _load_continuity_support_bundle(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        task_path=task_path,
    )
    payload = {
        "status": STATUS_PASS_REQUIRED,
        "command_bundle_contract_id": IDENTITY_LAUNCHER_COMMAND_DISCOVERY_CONTRACT_ID,
        "question_family": IDENTITY_LAUNCHER_COMMAND_DISCOVERY_QUESTION_FAMILY,
        "surface_governance": build_governed_runtime_summary_surface_payload(
            "identity_codex_launcher_command_bundle_surface"
        ),
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "bin_dir": str(bin_dir),
        "ambient_catalog_path": str(ambient_catalog_path),
        "catalog_context_status": catalog_context_status,
        "catalog_context_reason": catalog_context_reason,
        "catalog_explicit_flag_required": require_explicit_catalog,
        "shortcut_command": shortcut,
        "generic_command": GENERIC_LAUNCHER_NAME,
        "shortcut_launcher_path": str(shortcut_path),
        "generic_launcher_path": str(generic_path),
        "absolute_shortcut_path": str(shortcut_path),
        "absolute_generic_launcher_path": str(generic_path),
        "operator_shell_path_hint": str(bin_dir),
        "shortcut_command_on_path": shortcut_command_on_path,
        "generic_command_on_path": generic_command_on_path,
        "shortcut_install_status": shortcut_install_status,
        "shortcut_install_reason": shortcut_surface["install_reason"],
        "shortcut_shell_discoverability_status": shortcut_surface["shell_discoverability_status"],
        "shortcut_shell_discoverability_reason": shortcut_surface["shell_discoverability_reason"],
        "shortcut_resolved_command_path": shortcut_surface["resolved_command_path"],
        "shortcut_bin_dir_on_path": shortcut_surface["bin_dir_on_path"],
        "generic_launcher_install_status": generic_install_status,
        "generic_launcher_install_reason": generic_surface["install_reason"],
        "generic_launcher_shell_discoverability_status": generic_surface["shell_discoverability_status"],
        "generic_launcher_shell_discoverability_reason": generic_surface["shell_discoverability_reason"],
        "generic_resolved_command_path": generic_surface["resolved_command_path"],
        "generic_bin_dir_on_path": generic_surface["bin_dir_on_path"],
        "actor_id": actor_token,
        "preferred_start_command": preferred_start_command,
        "preferred_start_surface_reason": preferred_start_surface_reason,
        "shortcut_start_command": shortcut_start_command,
        "absolute_start_command": absolute_start_command,
        "generic_start_command": preferred_generic_start_command,
        "absolute_generic_start_command": absolute_generic_start_command,
        "fresh_shell_start_command": fresh_shell_start_command,
        "absolute_fresh_shell_start_command": absolute_fresh_shell_start_command,
        "recommended_start_command": recommended_start_command,
        "recommended_user_command": recommended_start_command,
        "resume_status": resume_status,
        "host_thread_id_status": host_thread_id_status,
        "host_thread_id_present": bool(thread_id),
        "current_host_thread_id": thread_id,
        "resume_thread_source": thread_source,
        "identity_session_tuple_status": identity_session_tuple_status,
        "identity_session_tuple_reason": identity_session_tuple_reason,
        "resolved_resume_session_id": resolved_resume_session_id,
        "resolved_resume_session_source": resolved_resume_session_source,
        "resume_command_fresh_shell_executable_status": resume_command_fresh_shell_executable_status,
        "command_discovery": command_discovery,
        "continuity_support": continuity_support,
        "launcher_runtime_admissibility_projection": admissibility_projection,
        "launcher_runtime_admissibility_projection_status": projection_status or STATUS_FAIL_REQUIRED,
        "launcher_runtime_admissibility_status": admissibility_status or STATUS_FAIL_REQUIRED,
        "launcher_runtime_admissibility_reason": str(
            admissibility_projection.get("launcher_runtime_admissibility_reason", "")
        ).strip(),
        "runtime_mode_guard_status": str(
            admissibility_projection.get("runtime_mode_guard_status", STATUS_FAIL_REQUIRED)
        ).strip()
        or STATUS_FAIL_REQUIRED,
        "runtime_mode_guard_error_code": str(
            admissibility_projection.get("runtime_mode_guard_error_code", "")
        ).strip(),
        "runtime_mode_guard_binding_class": str(
            admissibility_projection.get("runtime_mode_guard_binding_class", "")
        ).strip(),
        "runtime_mode_guard_stale_reasons": list(
            admissibility_projection.get("runtime_mode_guard_stale_reasons") or []
        ),
        "projection_stale_reasons": list(admissibility_projection.get("stale_reasons") or []),
        "instance_answer_guidance": {
            "instance_returns_concrete_commands": True,
            "manual_command_assembly_forbidden": True,
            "python_helper_surface_forbidden": True,
            "terminal_native_surface_required": True,
            "continuity_support_internal_only": True,
        },
        "copyable_commands": {
            "start": {
                "preferred": preferred_start_command,
                "preferred_surface_reason": preferred_start_surface_reason,
                "shortcut": shortcut_start_command,
                "recommended": recommended_start_command,
                "absolute": absolute_start_command,
                "generic": preferred_generic_start_command,
                "generic_absolute": absolute_generic_start_command,
                "fresh_shell": fresh_shell_start_command,
                "fresh_shell_absolute": absolute_fresh_shell_start_command,
                "catalog_explicit_flag_required": require_explicit_catalog,
                "shortcut_on_path": shortcut_command_on_path,
                "generic_on_path": generic_command_on_path,
                "shortcut_install_status": shortcut_install_status,
                "shortcut_shell_discoverability_status": shortcut_surface["shell_discoverability_status"],
                "generic_launcher_install_status": generic_install_status,
                "generic_launcher_shell_discoverability_status": generic_surface["shell_discoverability_status"],
            },
            "resume": None,
        },
    }
    if thread_id:
        resume_short = [shortcut, "resume", thread_id]
        resume_generic = [GENERIC_LAUNCHER_NAME, "--identity-id", args.identity_id, "--", "resume", thread_id]
        shortcut_resume_command = _build_display_command(resume_short)
        absolute_resume_command = _build_display_command([str(shortcut_path), "resume", thread_id])
        generic_resume_command = _build_display_command(resume_generic)
        absolute_generic_resume_command = _build_display_command([str(generic_path), "--identity-id", args.identity_id, "--", "resume", thread_id])
        fresh_shell_resume_command = _build_generic_resume_command(
            launcher=GENERIC_LAUNCHER_NAME,
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            thread_id=thread_id,
            require_explicit_catalog=require_explicit_catalog,
            session_id=resolved_resume_session_id,
        )
        absolute_fresh_shell_resume_command = _build_generic_resume_command(
            launcher=str(generic_path),
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            thread_id=thread_id,
            require_explicit_catalog=require_explicit_catalog,
            session_id=resolved_resume_session_id,
        )
        if resume_command_fresh_shell_executable_status == STATUS_PASS_REQUIRED:
            if require_explicit_catalog or resolved_resume_session_id:
                canonical_resume_command = (
                    fresh_shell_resume_command
                    if generic_command_on_path or generic_install_status != STATUS_PASS_REQUIRED
                    else absolute_fresh_shell_resume_command
                )
            else:
                if shortcut_command_on_path:
                    canonical_resume_command = shortcut_resume_command
                elif shortcut_install_status == STATUS_PASS_REQUIRED:
                    canonical_resume_command = absolute_resume_command
                elif generic_command_on_path:
                    canonical_resume_command = generic_resume_command
                elif generic_install_status == STATUS_PASS_REQUIRED:
                    canonical_resume_command = absolute_generic_resume_command
                else:
                    canonical_resume_command = generic_resume_command
        else:
            canonical_resume_command = ""
        recommended_resume_command = canonical_resume_command
        if require_explicit_catalog:
            preferred_resume_command = canonical_resume_command
            preferred_resume_surface_reason = (
                "catalog_mismatch_requires_canonical_primary_surface"
                if canonical_resume_command
                else "catalog_mismatch_resume_surface_unavailable"
            )
        else:
            if shortcut_command_on_path and resume_command_fresh_shell_executable_status == STATUS_PASS_REQUIRED:
                preferred_resume_command = shortcut_resume_command
                preferred_resume_surface_reason = "shortcut_shell_discoverable_primary_surface"
            elif canonical_resume_command:
                preferred_resume_command = canonical_resume_command
                if generic_command_on_path:
                    preferred_resume_surface_reason = "shortcut_shell_undiscoverable_promote_canonical_resume_surface"
                elif generic_install_status == STATUS_PASS_REQUIRED or shortcut_install_status == STATUS_PASS_REQUIRED:
                    preferred_resume_surface_reason = "shortcut_shell_undiscoverable_promote_absolute_resume_surface"
                else:
                    preferred_resume_surface_reason = "launcher_install_missing_falls_back_to_resume_reference_surface"
            else:
                preferred_resume_command = ""
                preferred_resume_surface_reason = "resume_surface_unavailable_without_authoritative_session_tuple"
        payload.update(
            {
                "preferred_resume_command": preferred_resume_command,
                "preferred_resume_surface_reason": preferred_resume_surface_reason,
                "shortcut_resume_command": shortcut_resume_command,
                "absolute_resume_command": absolute_resume_command,
                "generic_resume_command": generic_resume_command,
                "absolute_generic_resume_command": absolute_generic_resume_command,
                "fresh_shell_resume_command": fresh_shell_resume_command,
                "absolute_fresh_shell_resume_command": absolute_fresh_shell_resume_command,
                "recommended_resume_command": recommended_resume_command,
                "recommended_user_command": recommended_resume_command or recommended_start_command,
            }
        )
        payload["copyable_commands"]["resume"] = {
            "preferred": preferred_resume_command,
            "preferred_surface_reason": preferred_resume_surface_reason,
            "shortcut": shortcut_resume_command,
            "recommended": recommended_resume_command,
            "absolute": absolute_resume_command,
            "generic": generic_resume_command,
            "generic_absolute": absolute_generic_resume_command,
            "fresh_shell": fresh_shell_resume_command,
            "fresh_shell_absolute": absolute_fresh_shell_resume_command,
            "thread_id": thread_id,
            "thread_source": thread_source,
            "session_id": resolved_resume_session_id,
            "session_source": resolved_resume_session_source,
            "catalog_explicit_flag_required": require_explicit_catalog,
            "shortcut_on_path": shortcut_command_on_path,
            "generic_on_path": generic_command_on_path,
            "shortcut_install_status": shortcut_install_status,
            "shortcut_shell_discoverability_status": shortcut_surface["shell_discoverability_status"],
            "generic_launcher_install_status": generic_install_status,
            "generic_launcher_shell_discoverability_status": generic_surface["shell_discoverability_status"],
        }
        if resume_command_fresh_shell_executable_status != STATUS_PASS_REQUIRED:
            payload["resume_reason"] = identity_session_tuple_reason
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
    p_commands.add_argument("--actor-id", default="assistant:codex")
    p_commands.add_argument("--session-id", default="")
    p_commands.add_argument("--json-only", action="store_true")
    p_commands.set_defaults(func=_cmd_commands)

    args = ap.parse_args()
    if getattr(args, "codex_args", None) and args.codex_args and args.codex_args[0] == "--":
        args.codex_args = args.codex_args[1:]
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
