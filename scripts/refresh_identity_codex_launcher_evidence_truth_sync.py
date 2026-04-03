#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from identity_codex_launcher_common import (
    IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID,
    IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY,
)
from identity_codex_launcher_evidence_common import (
    artifact_path,
    canonical_json_bytes,
    launcher_convergence_closure_checker_command,
    launcher_convergence_entry_command,
    launcher_convergence_manifest_notes,
    load_json,
    manifest_path,
    path_ref,
    prepare_launcher_convergence_bundle,
    write_json,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_DISCOVERY = "IP-ILAUNCH-EVID-001"
ERR_BUNDLE = "IP-ILAUNCH-EVID-002"
RECEIPT_RE = re.compile(r"^launcher_convergence_receipt\.(?P<token>.+)_summary\.json$")
DEFAULT_STREAM = "v1614-identity-codex-launcher"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    if json_only:
        print(text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_path(value: str, *, workspace_root: Path, sibling_root: Path) -> Path:
    token = str(value or "").strip()
    if not token:
        raise ValueError("empty path")
    raw = Path(token).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    workspace_candidate = (workspace_root / raw).resolve()
    if workspace_candidate.exists():
        return workspace_candidate
    return (sibling_root / raw).resolve()


def _infer_run_token(receipt_path: Path, payload: dict[str, Any]) -> str:
    token = str(payload.get("run_token", "")).strip()
    if token:
        return token
    match = RECEIPT_RE.match(receipt_path.name)
    if not match:
        raise ValueError(f"unable to infer run token from receipt filename: {receipt_path.name}")
    return str(match.group("token")).strip()


def _artifact_timestamp(payload: dict[str, Any], path: Path) -> str:
    token = str(payload.get("generated_at", "")).strip()
    if token:
        return token
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _closure_checker_command(*, repo_root: Path, catalog_path: Path) -> list[str]:
    return launcher_convergence_closure_checker_command(repo_root=repo_root, catalog_path=catalog_path)


def _receipt_candidates(*, artifact_root: Path, explicit_receipt: Path | None, run_token: str) -> list[Path]:
    if explicit_receipt is not None:
        return [explicit_receipt.resolve()]
    receipts = sorted(artifact_root.rglob("launcher_convergence_receipt.*_summary.json"))
    if run_token:
        suffix = f".{run_token}_summary.json"
        receipts = [path for path in receipts if path.name.endswith(suffix)]
    return receipts


def _prepare_row(*, receipt_path: Path, workspace_root: Path, repo_root: Path) -> tuple[dict[str, Any], bool]:
    payload = load_json(receipt_path)
    artifact_root = receipt_path.parent.resolve()
    run_token = _infer_run_token(receipt_path, payload)
    catalog_path = Path(str(payload.get("catalog_path", "")).strip()).expanduser().resolve()
    mode = str(payload.get("mode", "")).strip() or "dry-run"
    generated_at = _artifact_timestamp(payload, receipt_path)
    codex_home_token = str(payload.get("codex_home", "")).strip()
    codex_home = Path(codex_home_token).expanduser().resolve() if codex_home_token else None

    precheck_ref = str(payload.get("precheck_evidence_ref", "")).strip()
    precheck_path = (
        _resolve_path(precheck_ref, workspace_root=workspace_root, sibling_root=artifact_root)
        if precheck_ref
        else artifact_path(artifact_root, "launcher_convergence_precheck", run_token)
    )
    if not precheck_path.exists():
        raise FileNotFoundError(f"missing precheck artifact for {receipt_path.name}: {precheck_path}")

    postcheck_path: Path | None = None
    postcheck_ref = str(payload.get("postcheck_evidence_ref", "")).strip()
    if postcheck_ref:
        resolved_post = _resolve_path(postcheck_ref, workspace_root=workspace_root, sibling_root=artifact_root)
        if resolved_post.exists():
            postcheck_path = resolved_post
    else:
        sibling_post = artifact_path(artifact_root, "launcher_convergence_postcheck", run_token)
        if sibling_post.exists():
            postcheck_path = sibling_post

    entry_cmd = launcher_convergence_entry_command(
        repo_root=repo_root,
        catalog_path=catalog_path,
        mode=mode,
        codex_home=codex_home,
        artifact_root=artifact_root,
        run_token=run_token,
        receipt_path=receipt_path,
    )
    checker_cmd = _closure_checker_command(repo_root=repo_root, catalog_path=catalog_path)

    precheck_payload = load_json(precheck_path)
    precheck_rc = 0 if str(precheck_payload.get("identity_codex_launcher_migration_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1
    postcheck_rc: int | None = None
    if postcheck_path is not None:
        postcheck_payload = load_json(postcheck_path)
        postcheck_rc = 0 if str(postcheck_payload.get("identity_codex_launcher_migration_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1

    entry_rc = 0 if str(payload.get("status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1
    next_receipt, manifest_out, manifest_payload = prepare_launcher_convergence_bundle(
        workspace_root=workspace_root,
        artifact_root=artifact_root,
        receipt_path=receipt_path,
        run_token=run_token,
        generated_at=generated_at,
        mode=mode,
        catalog_path=catalog_path,
        entry_id=str(payload.get("entry_id", IDENTITY_CODEX_LAUNCHER_CONVERGENCE_ENTRY_ID)).strip(),
        receipt_family=str(payload.get("receipt_family", IDENTITY_CODEX_LAUNCHER_CONVERGENCE_RECEIPT_FAMILY)).strip(),
        receipt_payload=payload,
        evidence_record_inputs=[
            {
                "kind": "launcher_convergence_receipt",
                "path": str(receipt_path),
                "command": entry_cmd,
                "rc": entry_rc,
                "timestamp": generated_at,
                "use_prepared_receipt_payload": True,
            },
            {
                "kind": "launcher_convergence_precheck",
                "path": str(precheck_path),
                "command": checker_cmd,
                "rc": precheck_rc,
                "timestamp": _artifact_timestamp(precheck_payload, precheck_path),
            },
            *(
                [
                    {
                        "kind": "launcher_convergence_postcheck",
                        "path": str(postcheck_path),
                        "command": checker_cmd,
                        "rc": int(postcheck_rc),
                        "timestamp": _artifact_timestamp(load_json(postcheck_path), postcheck_path),
                    }
                ]
                if postcheck_path is not None and postcheck_rc is not None
                else []
            ),
        ],
        notes=launcher_convergence_manifest_notes(),
        manifest_out=manifest_path(artifact_root, run_token),
    )

    receipt_changed = canonical_json_bytes(next_receipt) != canonical_json_bytes(payload)
    current_manifest = load_json(manifest_out) if manifest_out.exists() else None
    manifest_changed = current_manifest is None or canonical_json_bytes(manifest_payload) != canonical_json_bytes(current_manifest)
    return (
        {
            "receipt_path": str(receipt_path.resolve()),
            "artifact_root": str(artifact_root),
            "run_token": run_token,
            "receipt_changed": receipt_changed,
            "manifest_changed": manifest_changed,
            "manifest_path": str(manifest_out),
            "summary_ref": path_ref(receipt_path, workspace_root),
            "manifest_ref": path_ref(manifest_out, workspace_root),
            "next_receipt": next_receipt,
            "manifest_payload": manifest_payload,
            "precheck_path": str(precheck_path),
            "postcheck_path": str(postcheck_path) if postcheck_path is not None else "",
        },
        receipt_changed or manifest_changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Truth-sync launcher convergence receipts with governed evidence manifests."
    )
    parser.add_argument(
        "--artifact-root",
        default="",
        help="artifact root or search root (defaults to <workspace>/activity/evidence/v1614-identity-codex-launcher)",
    )
    parser.add_argument("--receipt", default="", help="optional explicit convergence receipt path")
    parser.add_argument("--run-token", default="", help="optional run-token filter when scanning artifact roots")
    parser.add_argument("--workspace-root", default="", help="optional workspace root override")
    parser.add_argument("--apply", action="store_true", help="write corrected receipt/manifest bundles instead of dry-run")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = (
        Path(str(args.workspace_root or "")).expanduser().resolve()
        if str(args.workspace_root or "").strip()
        else repo_root.parent.resolve()
    )
    artifact_root = (
        Path(str(args.artifact_root or "")).expanduser().resolve()
        if str(args.artifact_root or "").strip()
        else (workspace_root / "activity" / "evidence" / DEFAULT_STREAM).resolve()
    )
    receipt_path = Path(str(args.receipt or "")).expanduser().resolve() if str(args.receipt or "").strip() else None

    payload: dict[str, Any] = {
        "status": STATUS_PASS_REQUIRED,
        "truth_sync_status": STATUS_PASS_REQUIRED,
        "apply_mode": bool(args.apply),
        "workspace_root": str(workspace_root),
        "artifact_root": str(artifact_root),
        "receipt_count": 0,
        "receipts_with_changes": 0,
        "receipt_ref_change_count": 0,
        "manifest_write_count": 0,
        "rows": [],
        "stale_reasons": [],
    }

    if receipt_path is None and not artifact_root.exists():
        payload.update(
            {
                "status": STATUS_FAIL_REQUIRED,
                "truth_sync_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_DISCOVERY,
                "stale_reasons": [f"artifact_root_missing:{artifact_root}"],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    receipts = _receipt_candidates(artifact_root=artifact_root, explicit_receipt=receipt_path, run_token=str(args.run_token or "").strip())
    payload["receipt_count"] = len(receipts)
    if not receipts:
        payload.update(
            {
                "status": STATUS_FAIL_REQUIRED,
                "truth_sync_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_DISCOVERY,
                "stale_reasons": ["launcher_convergence_receipts_missing"],
            }
        )
        _emit(payload, json_only=args.json_only)
        return 1

    any_change = False
    had_error = False
    for receipt in receipts:
        try:
            row, changed = _prepare_row(receipt_path=receipt, workspace_root=workspace_root, repo_root=repo_root)
        except Exception as exc:
            had_error = True
            payload["rows"].append(
                {
                    "receipt_path": str(receipt.resolve()),
                    "status": STATUS_FAIL_REQUIRED,
                    "error": str(exc),
                }
            )
            continue
        any_change = any_change or changed
        if changed:
            payload["receipts_with_changes"] += 1
            if row["receipt_changed"]:
                payload["receipt_ref_change_count"] += 1
            if row["manifest_changed"]:
                payload["manifest_write_count"] += 1
            if args.apply:
                write_json(Path(row["receipt_path"]), row.pop("next_receipt"))
                write_json(Path(row["manifest_path"]), row.pop("manifest_payload"))
            else:
                row.pop("next_receipt")
                row.pop("manifest_payload")
        else:
            row.pop("next_receipt")
            row.pop("manifest_payload")
        row["status"] = STATUS_PASS_REQUIRED if not changed or args.apply else STATUS_FAIL_REQUIRED
        payload["rows"].append(row)

    if had_error:
        payload.update(
            {
                "status": STATUS_FAIL_REQUIRED,
                "truth_sync_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_BUNDLE,
            }
        )
    elif any_change and not args.apply:
        payload.update(
            {
                "status": STATUS_FAIL_REQUIRED,
                "truth_sync_status": STATUS_FAIL_REQUIRED,
                "error_code": ERR_BUNDLE,
                "repair_status": "dry_run_changes_detected",
            }
        )
        payload["stale_reasons"].append("launcher_convergence_evidence_truth_sync_pending_apply")
    else:
        payload.update(
            {
                "status": STATUS_PASS_REQUIRED,
                "truth_sync_status": STATUS_PASS_REQUIRED,
                "error_code": "",
                "repair_status": "apply_truth_synced" if any_change and args.apply else "already_truth_synced",
            }
        )

    _emit(payload, json_only=args.json_only)
    return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
