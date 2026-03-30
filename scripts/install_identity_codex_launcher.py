#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
    RUNTIME_PATHS_BINDING_MODE_PROTOCOL_HOME_ONLY,
    STATUS_PASS_REQUIRED,
    default_bin_dir,
    ensure_launcher_assets,
    ensure_launcher_contract,
    install_launcher_shims,
    launcher_command_discovery_doc,
    launcher_manifest_path,
    observe_launcher_surface,
    resolve_launcher_config_home,
    runtime_identity_home_for_catalog,
    resolve_catalog_path,
    resolve_launcher_pack_task,
    shortcut_launcher_name,
    write_runtime_paths_config,
    GENERIC_LAUNCHER_NAME,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Install protocol-owned identity Codex launchers.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--current-task", default="")
    ap.add_argument("--bin-dir", default="")
    ap.add_argument("--identity-home", default="")
    ap.add_argument("--protocol-home", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = resolve_catalog_path(args.catalog)
    pack_root, task_path, task_doc = resolve_launcher_pack_task(
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        current_task=str(args.current_task or ""),
    )

    contract_changed = ensure_launcher_contract(task_doc, args.identity_id)
    if contract_changed:
        task_path.write_text(json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    asset_result = ensure_launcher_assets(pack_root, args.identity_id)
    expected_command_discovery = launcher_command_discovery_doc(args.identity_id)
    launcher_contract_doc = task_doc.get(IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY)
    manifest_doc = json.loads(launcher_manifest_path(pack_root).read_text(encoding="utf-8"))
    bin_dir = Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()
    protocol_home = (
        Path(args.protocol_home).expanduser().resolve()
        if str(args.protocol_home or "").strip()
        else Path(__file__).resolve().parents[1]
    )
    shim_result = install_launcher_shims(
        identity_id=args.identity_id,
        bin_dir=bin_dir,
        catalog_path=catalog_path,
        protocol_home=protocol_home,
    )

    identity_home, identity_home_source = resolve_launcher_config_home(
        explicit_identity_home=str(args.identity_home or "").strip(),
        bin_dir=bin_dir,
    )
    runtime_identity_home = runtime_identity_home_for_catalog(catalog_path)
    runtime_paths_env = write_runtime_paths_config(
        identity_home=identity_home,
        protocol_home=protocol_home,
        runtime_identity_home=runtime_identity_home,
        runtime_catalog=catalog_path,
        binding_mode=RUNTIME_PATHS_BINDING_MODE_PROTOCOL_HOME_ONLY,
    )
    generic_surface = observe_launcher_surface(GENERIC_LAUNCHER_NAME, Path(shim_result["generic_launcher_path"]))
    shortcut_surface = observe_launcher_surface(
        shortcut_launcher_name(args.identity_id),
        Path(shim_result["shortcut_launcher_path"]),
    )

    payload = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "launcher_config_identity_home": str(identity_home),
        "launcher_config_identity_home_source": identity_home_source,
        "runtime_identity_home": str(runtime_identity_home),
        "contract_key": IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
        "contract_changed": contract_changed,
        "contract_command_discovery_matches_expected": isinstance(launcher_contract_doc, dict)
        and launcher_contract_doc.get("command_discovery") == expected_command_discovery,
        "manifest_command_discovery_matches_expected": manifest_doc.get("command_discovery") == expected_command_discovery,
        "runtime_paths_env": str(runtime_paths_env),
        "operator_shell_path_hint": str(bin_dir),
        "absolute_generic_launcher_path": shim_result["generic_launcher_path"],
        "absolute_shortcut_path": shim_result["shortcut_launcher_path"],
        "generic_launcher_install_status": generic_surface["install_status"],
        "generic_launcher_install_reason": generic_surface["install_reason"],
        "generic_launcher_shell_discoverability_status": generic_surface["shell_discoverability_status"],
        "generic_launcher_shell_discoverability_reason": generic_surface["shell_discoverability_reason"],
        "generic_command_on_path": generic_surface["command_on_path"],
        "generic_resolved_command_path": generic_surface["resolved_command_path"],
        "shortcut_launcher_install_status": shortcut_surface["install_status"],
        "shortcut_launcher_install_reason": shortcut_surface["install_reason"],
        "shortcut_launcher_shell_discoverability_status": shortcut_surface["shell_discoverability_status"],
        "shortcut_launcher_shell_discoverability_reason": shortcut_surface["shell_discoverability_reason"],
        "shortcut_command_on_path": shortcut_surface["command_on_path"],
        "shortcut_resolved_command_path": shortcut_surface["resolved_command_path"],
        **asset_result,
        **shim_result,
    }
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
