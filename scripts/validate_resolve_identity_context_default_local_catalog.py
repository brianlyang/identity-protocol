#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root
from resolve_identity_context_probe_common import (
    materialize_single_identity_runtime_workspace,
    pick_identity_id,
    run_json,
    write_runtime_defaults,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RESOLVE_DEFAULT_LOCAL_CATALOG = "IP-RCTX-001"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _assert_resolve_replay(
    label: str,
    replay: dict[str, Any],
    *,
    expected_catalog_path: str,
    expected_pack_path: str,
    expected_source_layer: str = "project",
    expected_scope: str = "USER",
) -> list[str]:
    stale_reasons: list[str] = []
    if str(replay.get("source_layer", "")).strip() != expected_source_layer:
        stale_reasons.append(f"{label}:source_layer")
    if str(replay.get("catalog_path", "")).strip() != expected_catalog_path:
        stale_reasons.append(f"{label}:catalog_path")
    if str(replay.get("pack_path", "")).strip() != expected_pack_path:
        stale_reasons.append(f"{label}:pack_path")
    if str(replay.get("resolved_scope", "")).strip().upper() != expected_scope:
        stale_reasons.append(f"{label}:resolved_scope")
    return stale_reasons


def _assert_metadata_hygiene_replay(
    replay: dict[str, Any],
    *,
    identity_id: str,
    expected_catalog_path: str,
    expected_pack_path: str,
) -> list[str]:
    stale_reasons: list[str] = []
    if str(replay.get("runtime_catalog_metadata_hygiene_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:status")
    if str(replay.get("catalog_path", "")).strip() != expected_catalog_path:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:catalog_path")
    if int(replay.get("checked_identity_count") or 0) != 1:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:checked_identity_count")
    if int(replay.get("violation_count") or 0) != 0:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:violation_count")

    rows = replay.get("checked_rows") or []
    if not isinstance(rows, list) or len(rows) != 1:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:checked_rows")
        return stale_reasons

    row = rows[0] if isinstance(rows[0], dict) else {}
    if str(row.get("identity_id", "")).strip() != identity_id:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:identity_id")
    if str(row.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:row_status")
    if str(row.get("canonical_scope", "")).strip().upper() != "USER":
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:canonical_scope")
    if str(row.get("resolved_scope", "")).strip().upper() != "USER":
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:resolved_scope")
    if str(row.get("resolved_source_layer", "")).strip() != "project":
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:resolved_source_layer")
    if str(row.get("canonical_pack_path_resolved", "")).strip() != expected_pack_path:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:canonical_pack_path")
    if str(row.get("resolved_pack_path", "")).strip() != expected_pack_path:
        stale_reasons.append("explicit_local_catalog_metadata_hygiene:resolved_pack_path")
    return stale_reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate resolve_identity_context.py defaults to the project-local catalog.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    local_catalog_path = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
    repo_catalog_path = (repo_root / "identity" / "catalog" / "identities.yaml").resolve()
    payload: dict[str, Any] = {
        "resolve_identity_context_local_catalog_closure_status": STATUS_FAIL_REQUIRED,
        "resolve_identity_context_default_local_catalog_status": STATUS_FAIL_REQUIRED,
        "resolve_identity_context_explicit_local_catalog_precedence_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_RESOLVE_DEFAULT_LOCAL_CATALOG,
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "repo_catalog_path": str(repo_catalog_path),
        "local_catalog_path": str(local_catalog_path),
        "identity_id": "",
        "workspace_replay": {},
        "protocol_replay": {},
        "explicit_local_catalog_probe_context": {},
        "explicit_local_catalog_precedence_replay": {},
        "explicit_local_catalog_metadata_hygiene_replay": {},
        "explicit_local_catalog_runtime_defaults_ref": "",
        "stale_reasons": [],
    }

    try:
        if not local_catalog_path.exists():
            raise FileNotFoundError(f"local catalog missing: {local_catalog_path}")
        if not repo_catalog_path.exists():
            raise FileNotFoundError(f"repo catalog missing: {repo_catalog_path}")

        identity_id = str(args.identity_id or "").strip() or pick_identity_id(local_catalog_path)
        payload["identity_id"] = identity_id
        workspace_payload = run_json(
            [
                "python3",
                "identity-protocol-local/scripts/resolve_identity_context.py",
                "resolve",
                "--identity-id",
                identity_id,
            ],
            cwd=workspace_root,
        )
        protocol_payload = run_json(
            [
                "python3",
                "scripts/resolve_identity_context.py",
                "resolve",
                "--identity-id",
                identity_id,
            ],
            cwd=repo_root,
        )
        payload["workspace_replay"] = workspace_payload
        payload["protocol_replay"] = protocol_payload

        expected_catalog_path = str(local_catalog_path)
        expected_pack_path = str((workspace_root / ".identity" / identity_id).resolve())
        stale_reasons: list[str] = []
        stale_reasons.extend(
            _assert_resolve_replay(
                "workspace_replay",
                workspace_payload,
                expected_catalog_path=expected_catalog_path,
                expected_pack_path=expected_pack_path,
            )
        )
        stale_reasons.extend(
            _assert_resolve_replay(
                "protocol_replay",
                protocol_payload,
                expected_catalog_path=expected_catalog_path,
                expected_pack_path=expected_pack_path,
            )
        )
        if not stale_reasons:
            payload["resolve_identity_context_default_local_catalog_status"] = STATUS_PASS_REQUIRED

        with tempfile.TemporaryDirectory(prefix="resolve-identity-context-local-catalog-precedence.") as tmp_dir_raw:
            tmp_dir = Path(tmp_dir_raw).resolve()
            temp_workspace_root = (tmp_dir / "workspace").resolve()
            temp_workspace_root.mkdir(parents=True, exist_ok=True)
            temp_codex_home = (tmp_dir / "codex-home").resolve()
            temp_codex_home.mkdir(parents=True, exist_ok=True)

            probe_context = materialize_single_identity_runtime_workspace(
                source_catalog_path=local_catalog_path,
                identity_id=identity_id,
                target_workspace_root=temp_workspace_root,
            )
            payload["explicit_local_catalog_probe_context"] = probe_context

            runtime_defaults_ref = write_runtime_defaults(
                codex_home=temp_codex_home,
                protocol_home=repo_root,
                identity_home=local_catalog_path.parent,
                identity_catalog=local_catalog_path,
            )
            payload["explicit_local_catalog_runtime_defaults_ref"] = str(runtime_defaults_ref)

            replay_env = os.environ.copy()
            replay_env["CODEX_HOME"] = str(temp_codex_home)
            replay_env.pop("IDENTITY_HOME", None)
            replay_env.pop("IDENTITY_CATALOG", None)
            replay_env.pop("IDENTITY_PROTOCOL_HOME", None)

            explicit_precedence_replay = run_json(
                [
                    "python3",
                    str((repo_root / "scripts" / "resolve_identity_context.py").resolve()),
                    "resolve",
                    "--identity-id",
                    identity_id,
                    "--local-catalog",
                    ".identity/catalog.local.yaml",
                ],
                cwd=temp_workspace_root,
                env=replay_env,
            )
            payload["explicit_local_catalog_precedence_replay"] = explicit_precedence_replay

            explicit_metadata_hygiene_replay = run_json(
                [
                    "python3",
                    str((repo_root / "scripts" / "validate_runtime_catalog_metadata_hygiene.py").resolve()),
                    "--catalog",
                    ".identity/catalog.local.yaml",
                    "--repo-catalog",
                    str(repo_catalog_path),
                    "--identity-id",
                    identity_id,
                    "--require-active",
                    "--json-only",
                ],
                cwd=temp_workspace_root,
                env=replay_env,
            )
            payload["explicit_local_catalog_metadata_hygiene_replay"] = explicit_metadata_hygiene_replay

            expected_temp_catalog_path = str(Path(probe_context["target_catalog_path"]).resolve())
            expected_temp_pack_path = str(Path(probe_context["target_pack_path"]).resolve())
            stale_reasons.extend(
                _assert_resolve_replay(
                    "explicit_local_catalog_precedence_replay",
                    explicit_precedence_replay,
                    expected_catalog_path=expected_temp_catalog_path,
                    expected_pack_path=expected_temp_pack_path,
                )
            )
            stale_reasons.extend(
                _assert_metadata_hygiene_replay(
                    explicit_metadata_hygiene_replay,
                    identity_id=identity_id,
                    expected_catalog_path=expected_temp_catalog_path,
                    expected_pack_path=expected_temp_pack_path,
                )
            )
            if not any(reason.startswith("explicit_local_catalog_") for reason in stale_reasons):
                payload["resolve_identity_context_explicit_local_catalog_precedence_status"] = STATUS_PASS_REQUIRED

        if stale_reasons:
            payload["stale_reasons"] = stale_reasons
            _emit(payload, json_only=args.json_only)
            return 1
    except Exception as exc:
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["resolve_identity_context_local_catalog_closure_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
