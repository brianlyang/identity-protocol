#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
    STATUS_PASS_REQUIRED,
    default_bin_dir,
    default_identity_home,
    ensure_launcher_assets,
    ensure_launcher_contract,
    install_launcher_shims,
    runtime_identity_home_for_catalog,
    resolve_catalog_path,
    resolve_launcher_pack_task,
    write_runtime_paths_config,
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
    bin_dir = Path(args.bin_dir).expanduser().resolve() if str(args.bin_dir or "").strip() else default_bin_dir()
    shim_result = install_launcher_shims(
        identity_id=args.identity_id,
        bin_dir=bin_dir,
        catalog_path=catalog_path,
    )

    identity_home = (
        Path(args.identity_home).expanduser().resolve()
        if str(args.identity_home or "").strip()
        else default_identity_home()
    )
    runtime_identity_home = runtime_identity_home_for_catalog(catalog_path)
    protocol_home = (
        Path(args.protocol_home).expanduser().resolve()
        if str(args.protocol_home or "").strip()
        else Path(__file__).resolve().parents[1]
    )
    runtime_paths_env = write_runtime_paths_config(
        identity_home=identity_home,
        protocol_home=protocol_home,
        runtime_identity_home=runtime_identity_home,
        runtime_catalog=catalog_path,
    )

    payload = {
        "status": STATUS_PASS_REQUIRED,
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "pack_path": str(pack_root),
        "task_path": str(task_path),
        "launcher_config_identity_home": str(identity_home),
        "runtime_identity_home": str(runtime_identity_home),
        "contract_key": IDENTITY_CODEX_LAUNCHER_CONTRACT_KEY,
        "contract_changed": contract_changed,
        "runtime_paths_env": str(runtime_paths_env),
        **asset_result,
        **shim_result,
    }
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
