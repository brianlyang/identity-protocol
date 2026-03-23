#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    GENERIC_LAUNCHER_NAME,
    IDENTITY_CODEX_LAUNCHER_CONTRACT_ID,
    IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
    IDENTITY_CODEX_LAUNCHER_INSTALLER_ID,
    IDENTITY_CODEX_LAUNCHER_MANIFEST_REL,
    IDENTITY_CODEX_LAUNCHER_README_REL,
    IDENTITY_CODEX_LAUNCHER_RENDERER_ID,
    IDENTITY_CODEX_LAUNCHER_VALIDATOR_ID,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    active_identity_install_required,
    default_bin_dir,
    launcher_manifest_path,
    launcher_readme_path,
    launcher_required,
    observe_launcher_surface,
    read_runtime_paths_config,
    resolve_catalog_path,
    resolve_launcher_pack_task,
    runtime_identity_home_for_catalog,
    runtime_paths_config_path,
    shortcut_launcher_name,
    validate_launcher_contract_doc,
    validate_launcher_manifest_doc,
)
from resolve_identity_context import resolve_identity

ERR_LAUNCHER_MISSING = "IP-ILAUNCH-001"
ERR_LAUNCHER_INVALID = "IP-ILAUNCH-002"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_matches(raw_value: str, expected: Path) -> bool:
    token = str(raw_value or "").strip()
    if not token:
        return False
    try:
        return Path(token).expanduser().resolve() == expected.resolve()
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-owned identity Codex launcher assets.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--current-task", default="")
    ap.add_argument("--bin-dir", default="")
    ap.add_argument("--identity-home", default="")
    ap.add_argument("--require-installed", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = resolve_catalog_path(args.catalog)
    pack_root, task_path, task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )
    manifest_path = launcher_manifest_path(pack_root)
    readme_path = launcher_readme_path(pack_root)
    bin_dir = Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()
    config_identity_home = (
        Path(args.identity_home).expanduser().resolve()
        if str(args.identity_home or "").strip()
        else (bin_dir.parent / ".identity").resolve()
    )
    runtime_identity_home = runtime_identity_home_for_catalog(catalog_path)
    runtime_paths_env = runtime_paths_config_path(config_identity_home)
    runtime_paths_doc = read_runtime_paths_config(config_identity_home)
    protocol_home = Path(__file__).resolve().parents[1]
    generic_path = (bin_dir / GENERIC_LAUNCHER_NAME).resolve()
    shortcut_path = (bin_dir / shortcut_launcher_name(args.identity_id)).resolve()
    generic_surface = observe_launcher_surface(GENERIC_LAUNCHER_NAME, generic_path)
    shortcut_surface = observe_launcher_surface(shortcut_launcher_name(args.identity_id), shortcut_path)
    contract = task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY)
    try:
        resolved_identity = resolve_identity(
            args.identity_id,
            (Path(__file__).resolve().parents[1] / "identity" / "catalog" / "identities.yaml").resolve(),
            catalog_path,
            preferred_scope="USER",
        )
        identity_status = str(resolved_identity.get("status", "")).strip()
    except Exception:
        identity_status = ""
    install_required = active_identity_install_required(identity_status, force_installed=bool(args.require_installed))
    required = launcher_required(task_doc, pack_root)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "manifest_path": str(manifest_path),
        "readme_path": str(readme_path),
        "bin_dir": str(bin_dir),
        "launcher_config_identity_home": str(config_identity_home),
        "runtime_identity_home": str(runtime_identity_home),
        "runtime_paths_env": str(runtime_paths_env),
        "generic_launcher_path": str(generic_path),
        "shortcut_launcher_path": str(shortcut_path),
        "absolute_generic_launcher_path": str(generic_path),
        "absolute_shortcut_path": str(shortcut_path),
        "operator_shell_path_hint": str(bin_dir),
        "generic_launcher_install_status": generic_surface["install_status"],
        "generic_launcher_install_reason": generic_surface["install_reason"],
        "generic_launcher_shell_discoverability_status": generic_surface["shell_discoverability_status"],
        "generic_launcher_shell_discoverability_reason": generic_surface["shell_discoverability_reason"],
        "generic_command_on_path": generic_surface["command_on_path"],
        "generic_resolved_command_path": generic_surface["resolved_command_path"],
        "generic_bin_dir_on_path": generic_surface["bin_dir_on_path"],
        "shortcut_launcher_install_status": shortcut_surface["install_status"],
        "shortcut_launcher_install_reason": shortcut_surface["install_reason"],
        "shortcut_launcher_shell_discoverability_status": shortcut_surface["shell_discoverability_status"],
        "shortcut_launcher_shell_discoverability_reason": shortcut_surface["shell_discoverability_reason"],
        "shortcut_command_on_path": shortcut_surface["command_on_path"],
        "shortcut_resolved_command_path": shortcut_surface["resolved_command_path"],
        "shortcut_bin_dir_on_path": shortcut_surface["bin_dir_on_path"],
        "identity_status": identity_status,
        "launcher_required": required,
        "install_required": install_required,
        "identity_codex_launcher_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pack_assets_status": STATUS_SKIPPED_NOT_REQUIRED,
        "installed_launcher_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_paths_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    stale_reasons: list[str] = []
    manifest_doc: dict[str, Any] | None = None
    if not manifest_path.exists():
        stale_reasons.append("launcher_manifest_missing")
    else:
        try:
            manifest_doc = _load_json(manifest_path)
        except Exception as exc:
            stale_reasons.append(f"launcher_manifest_invalid_json:{type(exc).__name__}")
    if not readme_path.exists():
        stale_reasons.append("launcher_readme_missing")

    if not isinstance(contract, dict):
        stale_reasons.append("launcher_contract_missing")
    else:
        contract_issues = validate_launcher_contract_doc(contract_doc=contract, identity_id=args.identity_id)
        for issue in contract_issues:
            stale_reasons.append(f"launcher_{issue}")

    if manifest_doc is not None:
        stale_reasons.extend(validate_launcher_manifest_doc(manifest_doc=manifest_doc, identity_id=args.identity_id))

    pack_assets_ok = not stale_reasons
    payload["pack_assets_status"] = STATUS_PASS_REQUIRED if pack_assets_ok else STATUS_FAIL_REQUIRED

    install_stale: list[str] = []
    if install_required:
        if not generic_path.exists():
            install_stale.append("generic_launcher_missing")
        elif not generic_surface["is_executable"]:
            install_stale.append("generic_launcher_not_executable")
        else:
            text = generic_path.read_text(encoding="utf-8", errors="ignore")
            if "render_identity_codex_launcher.py" not in text:
                install_stale.append("generic_launcher_renderer_binding_missing")
        if not shortcut_path.exists():
            install_stale.append("shortcut_launcher_missing")
        elif not shortcut_surface["is_executable"]:
            install_stale.append("shortcut_launcher_not_executable")
        else:
            text = shortcut_path.read_text(encoding="utf-8", errors="ignore")
            if f"--identity-id {args.identity_id}" not in text:
                install_stale.append("shortcut_launcher_identity_binding_missing")
            expected_catalog = str(catalog_path.resolve())
            quoted_catalog = shlex.quote(expected_catalog)
            if "--catalog" not in text or (
                expected_catalog not in text
                and quoted_catalog not in text
                and f"# catalog_binding={quoted_catalog}" not in text
            ):
                install_stale.append("shortcut_launcher_catalog_binding_missing")
    runtime_stale: list[str] = []
    if install_required:
        if not runtime_paths_env.exists():
            runtime_stale.append("runtime_paths_config_missing")
        else:
            if not _path_matches(runtime_paths_doc.get("IDENTITY_HOME", ""), runtime_identity_home):
                runtime_stale.append("runtime_paths_identity_home_mismatch")
            if not _path_matches(runtime_paths_doc.get("IDENTITY_CATALOG", ""), catalog_path):
                runtime_stale.append("runtime_paths_catalog_mismatch")
            if not _path_matches(runtime_paths_doc.get("IDENTITY_PROTOCOL_HOME", ""), protocol_home):
                runtime_stale.append("runtime_paths_protocol_home_mismatch")
    payload["installed_launcher_status"] = (
        STATUS_PASS_REQUIRED if not install_stale else STATUS_FAIL_REQUIRED
    ) if install_required else STATUS_SKIPPED_NOT_REQUIRED
    payload["runtime_paths_status"] = (
        STATUS_PASS_REQUIRED if not runtime_stale else STATUS_FAIL_REQUIRED
    ) if install_required else STATUS_SKIPPED_NOT_REQUIRED
    stale_reasons.extend(install_stale)
    stale_reasons.extend(runtime_stale)
    payload["stale_reasons"] = stale_reasons

    if stale_reasons:
        payload["identity_codex_launcher_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_LAUNCHER_MISSING if any(reason.endswith("_missing") for reason in stale_reasons) else ERR_LAUNCHER_INVALID
        _emit(payload, json_only=args.json_only)
        return 1

    payload["identity_codex_launcher_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
