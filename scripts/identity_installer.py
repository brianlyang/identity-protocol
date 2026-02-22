#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _sha256_bytes(payload: bytes) -> str:
    h = hashlib.sha256()
    h.update(payload)
    return h.hexdigest()


def _dir_signature(path: Path) -> str:
    if not path.exists() or not path.is_dir():
        return ""
    rows: list[str] = []
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(path).as_posix()
        rows.append(f"{rel}:{_sha256_bytes(p.read_bytes())}")
    return _sha256_bytes("\n".join(rows).encode("utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_source_pack(args: argparse.Namespace) -> Path:
    if args.source_pack:
        src = Path(args.source_pack)
        if not src.exists():
            raise FileNotFoundError(f"source pack not found: {src}")
        return src
    src = Path(args.pack_root) / args.identity_id
    if not src.exists():
        raise FileNotFoundError(f"default source pack not found: {src} (pass --source-pack)")
    return src


def _resolve_target_pack(args: argparse.Namespace) -> Path:
    return Path(args.target_root) / args.identity_id


def _classify_conflict(src_sig: str, dst_sig: str, has_dst: bool, destructive_replace: bool) -> tuple[str, str]:
    if not has_dst:
        return "fresh_install", "guarded_apply"
    if src_sig and dst_sig and src_sig == dst_sig:
        return "same_signature", "no_op_with_report"
    if destructive_replace:
        return "destructive_replace", "guarded_apply"
    return "compatible_upgrade", "abort_and_explain"


def _sync_pack(src: Path, dst: Path) -> list[str]:
    copied: list[str] = []
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        copied.append(target.as_posix())
    return copied


def _register_identity(catalog_path: Path, identity_id: str, title: str, description: str, pack_path: str, activate: bool) -> None:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    existing = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if existing:
        existing["pack_path"] = pack_path
        existing["title"] = title or existing.get("title", identity_id)
        existing["description"] = description or existing.get("description", "")
        if activate:
            existing["status"] = "active"
    else:
        identities.append(
            {
                "id": identity_id,
                "title": title or identity_id,
                "description": description or "",
                "status": "active" if activate else "inactive",
                "methodology_version": "v1.2.3",
                "pack_path": pack_path,
                "tags": ["identity"],
            }
        )
    catalog["identities"] = identities
    _dump_yaml(catalog_path, catalog)


def _build_report(args: argparse.Namespace, *, operation: str, conflict_type: str, action: str, source_pack: Path, target_pack: Path, preserved: list[str], backup_ref: str = "", rollback_ref: str = "", dry_run: bool = False, changed_files: list[str] | None = None) -> tuple[dict[str, Any], Path]:
    ts = datetime.now(timezone.utc)
    report_id = f"identity-install-{args.identity_id}-{operation}-{int(ts.timestamp())}-{int(ts.microsecond/1000):03d}"
    report = {
        "report_id": report_id,
        "identity_id": args.identity_id,
        "generated_at": _now_iso(),
        "operation": operation,
        "conflict_type": conflict_type,
        "action": action,
        "source_pack": source_pack.as_posix(),
        "target_pack": target_pack.as_posix(),
        "source_signature": _dir_signature(source_pack),
        "target_signature_before": _dir_signature(target_pack) if target_pack.exists() else "",
        "preserved_paths": preserved,
        "dry_run": dry_run,
        "changed_files": changed_files or [],
        "installer_invocation": {
            "tool": "identity-installer",
            "entrypoint": "scripts/identity_installer.py",
            "command": " ".join(["identity-installer", operation, "--identity-id", args.identity_id]),
        },
    }
    if backup_ref:
        report["backup_ref"] = backup_ref
    if rollback_ref:
        report["rollback_ref"] = rollback_ref
    report_path = Path(args.report_dir) / f"{report_id}.json"
    return report, report_path


def cmd_plan(args: argparse.Namespace) -> int:
    src = _resolve_source_pack(args)
    dst = _resolve_target_pack(args)
    src_sig = _dir_signature(src)
    dst_sig = _dir_signature(dst) if dst.exists() else ""
    conflict_type, action = _classify_conflict(src_sig, dst_sig, dst.exists(), args.destructive_replace)
    report, report_path = _build_report(
        args,
        operation="plan",
        conflict_type=conflict_type,
        action=action,
        source_pack=src,
        target_pack=dst,
        preserved=[dst.as_posix()] if dst.exists() else [],
        dry_run=True,
    )
    _write_json(report_path, report)
    print(f"report={report_path}")
    print(f"conflict_type={conflict_type}")
    print(f"action={action}")
    return 0


def cmd_install(args: argparse.Namespace, *, dry_run: bool) -> int:
    src = _resolve_source_pack(args)
    dst = _resolve_target_pack(args)
    src_sig = _dir_signature(src)
    dst_sig = _dir_signature(dst) if dst.exists() else ""
    conflict_type, action = _classify_conflict(src_sig, dst_sig, dst.exists(), args.destructive_replace)

    backup_ref = ""
    rollback_ref = ""
    changed: list[str] = []
    if not dry_run and action == "guarded_apply":
        if dst.exists():
            backup_dir = Path(args.backup_dir) / f"{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dst, backup_dir)
            backup_ref = backup_dir.as_posix()
            rollback_ref = f"restore_from:{backup_ref}"
        changed = _sync_pack(src, dst)

    if args.register and not dry_run:
        _register_identity(
            Path(args.catalog),
            args.identity_id,
            args.title,
            args.description,
            (Path(args.target_root) / args.identity_id).as_posix(),
            args.activate,
        )

    op = "dry-run" if dry_run else "install"
    report, report_path = _build_report(
        args,
        operation=op,
        conflict_type=conflict_type,
        action=action,
        source_pack=src,
        target_pack=dst,
        preserved=[dst.as_posix()] if dst.exists() else [],
        backup_ref=backup_ref,
        rollback_ref=rollback_ref,
        dry_run=dry_run,
        changed_files=changed,
    )
    _write_json(report_path, report)

    # compatibility mirror for install_safety sample validator
    mirror = Path("identity/runtime/examples/install") / f"install-report-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{args.identity_id}.json"
    _write_json(mirror, report)

    print(f"report={report_path}")
    print(f"mirror={mirror}")
    print(f"conflict_type={conflict_type}")
    print(f"action={action}")
    if action == "abort_and_explain":
        print("next_action=abort_and_explain_conflict")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    pattern = Path(args.report_dir).glob(f"identity-install-{args.identity_id}-*.json")
    reports = sorted(pattern, key=lambda p: p.stat().st_mtime)
    if not reports:
        print(f"[FAIL] no install report found under {args.report_dir} for identity={args.identity_id}")
        return 1
    latest = reports[-1]
    data = _load_json(latest)
    required = ["report_id", "identity_id", "generated_at", "operation", "conflict_type", "action", "preserved_paths", "installer_invocation"]
    miss = [k for k in required if k not in data]
    if miss:
        print(f"[FAIL] install report missing fields: {miss}")
        return 1
    if str(data.get("identity_id", "")).strip() != args.identity_id:
        print("[FAIL] report identity mismatch")
        return 1
    inv = data.get("installer_invocation") or {}
    if str(inv.get("tool", "")).strip() != "identity-installer":
        print("[FAIL] installer_invocation.tool must be identity-installer")
        return 1
    verify_report, verify_path = _build_report(
        args,
        operation="verify",
        conflict_type=str(data.get("conflict_type", "")),
        action="verified",
        source_pack=Path(str(data.get("source_pack", ""))),
        target_pack=Path(str(data.get("target_pack", ""))),
        preserved=list(data.get("preserved_paths") or []),
        dry_run=False,
        changed_files=[],
    )
    verify_report["verified_report_id"] = str(data.get("report_id", ""))
    _write_json(verify_path, verify_report)
    print(f"[OK] install report verified: {latest}")
    print(f"verify_report={verify_path}")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    if not args.rollback_ref:
        print("[FAIL] --rollback-ref is required")
        return 1
    ref = str(args.rollback_ref)
    if not ref.startswith("restore_from:"):
        print(f"[FAIL] rollback_ref format invalid: {ref}")
        return 1
    backup = Path(ref.split(":", 1)[1])
    if not backup.exists():
        print(f"[FAIL] backup path not found: {backup}")
        return 1
    dst = _resolve_target_pack(args)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(backup, dst)
    print(f"[OK] rollback complete from {backup} -> {dst}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Identity installer CLI (installer-plane)")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--identity-id", required=True)
    common.add_argument("--source-pack", default="")
    common.add_argument("--target-root", default="identity/packs")
    common.add_argument("--pack-root", default="identity/packs")
    common.add_argument("--catalog", default="identity/catalog/identities.yaml")
    common.add_argument("--report-dir", default="identity/runtime/reports/install")
    common.add_argument("--backup-dir", default="identity/runtime/backups/install")
    common.add_argument("--destructive-replace", action="store_true")
    common.add_argument("--register", action="store_true")
    common.add_argument("--activate", action="store_true")
    common.add_argument("--title", default="")
    common.add_argument("--description", default="")

    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", parents=[common])
    sub.add_parser("dry-run", parents=[common])
    sub.add_parser("install", parents=[common])
    sub.add_parser("verify", parents=[common])
    p_rb = sub.add_parser("rollback", parents=[common])
    p_rb.add_argument("--rollback-ref", required=True)

    args = ap.parse_args()
    if args.command == "plan":
        return cmd_plan(args)
    if args.command == "dry-run":
        return cmd_install(args, dry_run=True)
    if args.command == "install":
        return cmd_install(args, dry_run=False)
    if args.command == "verify":
        return cmd_verify(args)
    if args.command == "rollback":
        return cmd_rollback(args)
    print(f"[FAIL] unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
