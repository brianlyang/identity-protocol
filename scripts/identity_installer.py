#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import (
    collect_protocol_evidence,
    default_identity_home,
    default_local_catalog_path,
    default_local_instances_root,
    ensure_local_catalog,
    resolve_identity,
)

REPO_TARGET_CONFIRM_TOKEN = "I_UNDERSTAND_REPO_TARGET_WRITE"


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
    catalog_path = Path(args.catalog)
    repo_catalog_path = Path(args.repo_catalog)
    try:
        ensure_local_catalog(repo_catalog_path, catalog_path)
    except Exception:
        pass
    try:
        resolved = resolve_identity(
            args.identity_id,
            repo_catalog_path,
            catalog_path,
            preferred_scope=args.scope,
        )
        pack = Path(str(resolved.get("resolved_pack_path") or resolved.get("pack_path") or "")).expanduser()
        if pack.exists():
            return pack
    except Exception:
        pass

    if catalog_path.exists():
        try:
            catalog = _load_yaml(catalog_path)
            identities = catalog.get("identities") or []
            target = next(
                (
                    x
                    for x in identities
                    if isinstance(x, dict) and str(x.get("id", "")).strip() == args.identity_id
                ),
                None,
            )
            if target:
                pack_path = str((target or {}).get("pack_path", "")).strip()
                if pack_path:
                    pack = Path(pack_path).expanduser()
                    if pack.exists():
                        return pack
        except Exception:
            pass
    src = Path(args.pack_root) / args.identity_id
    if not src.exists():
        raise FileNotFoundError(
            f"default source pack not found: {src} "
            f"(pass --source-pack or ensure identity is registered in {catalog_path})"
        )
    return src


def _resolve_target_pack(args: argparse.Namespace) -> Path:
    return Path(args.target_root) / args.identity_id


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _repo_root() -> Path:
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return cur


def _canonical_target_for_scope(args: argparse.Namespace) -> Path:
    scope = str(args.scope or "").strip().upper() or "USER"
    if args.canonical_root:
        root = Path(args.canonical_root).expanduser().resolve()
    elif scope == "REPO":
        root = (_repo_root() / ".agents" / "identity" / "instances").resolve()
    elif scope == "ADMIN":
        root = Path("/etc/codex/identity/instances").resolve()
    else:
        root = Path(args.target_root).expanduser().resolve()
    return root / args.identity_id


def _enforce_target_boundary(args: argparse.Namespace) -> None:
    target_root = Path(args.target_root).expanduser().resolve()
    repo_root = _repo_root()
    in_repo = _is_within(target_root, repo_root)
    if args.allow_repo_target and str(args.allow_repo_target_confirm).strip() != REPO_TARGET_CONFIRM_TOKEN:
        raise PermissionError(
            "--allow-repo-target requires explicit confirmation token. "
            f'Pass --allow-repo-target-confirm "{REPO_TARGET_CONFIRM_TOKEN}".'
        )
    if args.allow_repo_target and not str(args.allow_repo_target_purpose).strip():
        raise PermissionError("--allow-repo-target requires --allow-repo-target-purpose for audit intent.")
    if not args.allow_repo_target and (
        str(args.allow_repo_target_confirm).strip() or str(args.allow_repo_target_purpose).strip()
    ):
        raise PermissionError("--allow-repo-target-confirm/--allow-repo-target-purpose require --allow-repo-target.")
    if not args.allow_repo_target and in_repo:
        raise PermissionError(
            "repo target blocked by local-instance persistence boundary. "
            "Use --allow-repo-target only for explicit fixture/demo operations."
        )


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


def _register_identity(
    catalog_path: Path,
    identity_id: str,
    title: str,
    description: str,
    pack_path: str,
    activate: bool,
    *,
    profile: str,
    runtime_mode: str,
) -> None:
    if not catalog_path.exists():
        _dump_yaml(
            catalog_path,
            {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "default_identity": "",
                "identities": [],
            },
        )
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    existing = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    if existing:
        existing["pack_path"] = pack_path
        existing["title"] = title or existing.get("title", identity_id)
        existing["description"] = description or existing.get("description", "")
        existing["profile"] = profile
        existing["runtime_mode"] = runtime_mode
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
                "profile": profile,
                "runtime_mode": runtime_mode,
                "pack_path": pack_path,
                "tags": ["identity"],
            }
        )
    catalog["identities"] = identities
    _dump_yaml(catalog_path, catalog)


def _single_active_precheck(catalog_path: Path, target_identity_id: str, auto_converge: bool = False) -> int:
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 1
    data = _load_yaml(catalog_path)
    identities = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    actives = [str(x.get("id", "")).strip() for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    actives = [x for x in actives if x]
    if len(actives) <= 1:
        return 0
    if auto_converge:
        print(
            "[WARN] --auto-converge-active is deprecated under multi-active model; "
            f"preserving active identities: {actives}"
        )
    else:
        print(f"[INFO] multi-active catalog detected (allowed): active_identities={actives}")
    return 0


def _all_scan_candidates(args: argparse.Namespace) -> list[Path]:
    identity_home = default_identity_home()
    repo = _repo_root()
    roots = [
        Path(args.target_root),
        Path(args.pack_root),
        identity_home,
        identity_home / "instances",
        identity_home / "identity",
        identity_home / "identities",
        repo / ".agents" / "identity",
        repo / ".agents" / "identity" / "instances",
        repo / "identity",
        repo / "identity" / "packs",
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        p = (r.expanduser() / args.identity_id).resolve()
        key = str(p)
        if key not in seen:
            out.append(p)
            seen.add(key)
    return out


PATH_FIELD_HINTS = {
    "path",
    "pack_path",
    "canonical_pack_path",
    "catalog_path",
    "evidence_path",
    "log_path",
    "report_path",
    "required_file_paths",
}

# Protocol/path-governance anchors must remain canonical absolute in runtime reports.
ABSOLUTE_ANCHOR_FIELDS = {
    "resolved_pack_path",
    "catalog_path",
    "identity_home",
    "protocol_root",
    "report_selected_path",
    "identity_prompt_path",
    "runtime_output_root",
    "metrics_path",
    "task_path",
    }


def _looks_path_key(key: str) -> bool:
    k = str(key or "").strip().lower()
    return (
        k in PATH_FIELD_HINTS
        or k.endswith("_path")
        or k.endswith("_paths")
        or k.endswith("_path_pattern")
    )


def _rewrite_path_string(
    value: str,
    *,
    key_hint: str,
    pack_dir: Path,
    old_prefix: str,
    identity_id: str,
) -> str:
    s = str(value)
    new_prefix = str(pack_dir.resolve())
    if old_prefix and old_prefix in s:
        s = s.replace(old_prefix, new_prefix)

    key_norm = str(key_hint or "").strip().lower()
    if key_norm in ABSOLUTE_ANCHOR_FIELDS:
        try:
            p_abs = Path(s).expanduser()
            if p_abs.is_absolute():
                return str(p_abs.resolve())
        except Exception:
            return s
        return s

    legacy_marker = f"/identity/packs/{identity_id}"
    idx = s.find(legacy_marker)
    if idx >= 0:
        tail = s[idx + len(legacy_marker) :].lstrip("/")
        s = f"{new_prefix}/{tail}" if tail else new_prefix

    if not _looks_path_key(key_hint):
        return s
    if "<identity-id>" in s or "*" in s:
        return s

    try:
        p = Path(s).expanduser()
    except Exception:
        return s
    if not p.is_absolute():
        return s
    try:
        rel = p.resolve().relative_to(pack_dir.resolve())
    except Exception:
        return s
    return rel.as_posix()


def _rewrite_identity_contract_paths(pack_dir: Path, old_root: Path | None = None) -> tuple[int, int]:
    files: list[Path] = []
    current_task = pack_dir / "CURRENT_TASK.json"
    if current_task.exists():
        files.append(current_task)
    runtime_dir = pack_dir / "runtime"
    if runtime_dir.exists():
        files.extend(sorted(runtime_dir.rglob("*.json")))
    if not files:
        return 0, 0

    old_prefix = str(old_root.resolve()) if old_root else ""
    identity_id = pack_dir.name
    changed_files = 0
    changed_fields = 0

    def _rewrite(obj: Any, *, key_hint: str) -> Any:
        nonlocal changed_fields
        if isinstance(obj, dict):
            return {k: _rewrite(v, key_hint=str(k)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_rewrite(v, key_hint=key_hint) for v in obj]
        if isinstance(obj, str):
            new_val = _rewrite_path_string(
                obj,
                key_hint=key_hint,
                pack_dir=pack_dir,
                old_prefix=old_prefix,
                identity_id=identity_id,
            )
            if new_val != obj:
                changed_fields += 1
            return new_val
        return obj

    for fp in files:
        try:
            payload = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        before = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        rewritten = _rewrite(payload, key_hint="")
        after = json.dumps(rewritten, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        fp.write_text(json.dumps(rewritten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed_files += 1

    return changed_files, changed_fields


def cmd_scan(args: argparse.Namespace) -> int:
    _enforce_target_boundary(args)
    repo_catalog = Path(args.repo_catalog).expanduser().resolve()
    local_catalog = Path(args.catalog).expanduser().resolve()
    ensure_local_catalog(repo_catalog, local_catalog)

    hits: list[dict[str, Any]] = []
    for cand in _all_scan_candidates(args):
        if cand.exists() and cand.is_dir():
            sig = _dir_signature(cand)
            hits.append({"path": str(cand), "signature": sig, "source": "filesystem"})

    # include catalog references even if path currently missing
    for catalog_path, layer in ((repo_catalog, "repo_catalog"), (local_catalog, "local_catalog")):
        if not catalog_path.exists():
            continue
        c = _load_yaml(catalog_path)
        identities = [x for x in (c.get("identities") or []) if isinstance(x, dict)]
        row = next((x for x in identities if str(x.get("id", "")).strip() == args.identity_id), None)
        if not row:
            continue
        p = Path(str(row.get("pack_path", "")).strip() or "").expanduser()
        if str(p):
            hits.append(
                {
                    "path": str(p.resolve()) if str(p) else "",
                    "exists": bool(p.exists()),
                    "source": layer,
                    "status": str(row.get("status", "")).strip(),
                    "profile": str(row.get("profile", "")).strip(),
                    "runtime_mode": str(row.get("runtime_mode", "")).strip(),
                }
            )

    dedup: dict[str, dict[str, Any]] = {}
    for h in hits:
        path = str(h.get("path", "")).strip()
        if not path:
            continue
        if path not in dedup:
            dedup[path] = h
        else:
            dedup[path]["source"] = f"{dedup[path].get('source', '')}+{h.get('source', '')}"

    rows = sorted(dedup.values(), key=lambda x: str(x.get("path", "")))
    report = {
        "scan_id": f"identity-install-scan-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}",
        "generated_at": _now_iso(),
        "identity_id": args.identity_id,
        "candidate_count": len(rows),
        "candidates": rows,
    }
    path = Path(args.report_dir) / f"{report['scan_id']}.json"
    _write_json(path, report)
    print(f"report={path}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_adopt(args: argparse.Namespace) -> int:
    _enforce_target_boundary(args)
    if not args.source_pack:
        print("[FAIL] adopt requires --source-pack")
        return 1
    src = Path(args.source_pack).expanduser().resolve()
    if not src.exists():
        print(f"[FAIL] source pack not found: {src}")
        return 1
    dst = _canonical_target_for_scope(args)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if not args.destructive_replace:
            print(
                f"[FAIL] canonical target already exists: {dst}. "
                "pass --destructive-replace to overwrite during adopt."
            )
            return 1
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    rewritten_files, rewritten_fields = _rewrite_identity_contract_paths(dst, old_root=src)

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog = Path(args.repo_catalog).expanduser().resolve()
    ensure_local_catalog(repo_catalog, catalog_path)
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == args.identity_id), None)
    if not row:
        row = {
            "id": args.identity_id,
            "title": args.title or args.identity_id,
            "description": args.description or "",
            "status": "inactive",
            "methodology_version": "v1.4.x",
            "tags": ["identity", "runtime"],
        }
        identities.append(row)
    previous = str(row.get("pack_path", "")).strip()
    if previous and previous != str(dst):
        deprecated = [str(x).strip() for x in (row.get("deprecated_pack_paths") or []) if str(x).strip()]
        if previous not in deprecated:
            deprecated.append(previous)
        row["deprecated_pack_paths"] = deprecated
    row["pack_path"] = str(dst)
    row["canonical_pack_path"] = str(dst)
    row["canonical_scope"] = str(args.scope or "USER").upper()
    row["profile"] = "runtime"
    row["runtime_mode"] = "local_only"
    row["instance_uid"] = str(row.get("instance_uid", "")).strip() or f"inst-{uuid.uuid4()}"
    if args.activate:
        for item in identities:
            if isinstance(item, dict):
                item["status"] = "active" if str(item.get("id", "")).strip() == args.identity_id else "inactive"
    catalog["identities"] = identities
    _dump_yaml(catalog_path, catalog)

    print(f"[OK] adopted identity={args.identity_id} canonical={dst}")
    print(
        "contract_paths_rewritten="
        f"{bool(rewritten_files)} files={rewritten_files} fields={rewritten_fields}"
    )
    print(f"catalog={catalog_path}")
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog = Path(args.repo_catalog).expanduser().resolve()
    ensure_local_catalog(repo_catalog, catalog_path)
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == args.identity_id), None)
    if not row:
        print(f"[FAIL] identity not found in catalog: {args.identity_id}")
        return 1
    canonical = str(row.get("canonical_pack_path") or row.get("pack_path") or "").strip()
    if not canonical:
        print(f"[FAIL] canonical pack path missing for identity={args.identity_id}")
        return 1
    row["pack_path"] = canonical
    row["canonical_pack_path"] = canonical
    row["canonical_scope"] = str(row.get("canonical_scope") or args.scope or "USER").upper()
    row["instance_uid"] = str(row.get("instance_uid", "")).strip() or f"inst-{uuid.uuid4()}"
    catalog["identities"] = identities
    _dump_yaml(catalog_path, catalog)
    print(f"[OK] lock applied for identity={args.identity_id}")
    print(f"canonical_pack_path={canonical}")
    return 0


def cmd_repair_paths(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog = Path(args.repo_catalog).expanduser().resolve()
    ensure_local_catalog(repo_catalog, catalog_path)
    c = _load_yaml(catalog_path)
    identities = [x for x in (c.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == args.identity_id), None)
    if not row:
        print(f"[FAIL] identity not found in catalog: {args.identity_id}")
        return 1
    pack = Path(str(row.get("pack_path", "")).strip()).expanduser().resolve()
    if not pack.exists():
        print(f"[FAIL] pack path not found: {pack}")
        return 1
    rewritten_files, rewritten_fields = _rewrite_identity_contract_paths(pack, old_root=None)
    print(
        f"[OK] repaired contract paths for {args.identity_id}: "
        f"changed={bool(rewritten_files)} files={rewritten_files} fields={rewritten_fields}"
    )
    return 0


def _build_report(
    args: argparse.Namespace,
    *,
    operation: str,
    conflict_type: str,
    action: str,
    source_pack: Path,
    target_pack: Path,
    preserved: list[str],
    backup_ref: str = "",
    rollback_ref: str = "",
    dry_run: bool = False,
    changed_files: list[str] | None = None,
    rewritten_files_count: int = 0,
    rewritten_fields_count: int = 0,
) -> tuple[dict[str, Any], Path]:
    ts = datetime.now(timezone.utc)
    report_id = f"identity-install-{args.identity_id}-{operation}-{int(ts.timestamp())}-{int(ts.microsecond/1000):03d}"
    protocol = collect_protocol_evidence(args.protocol_root, args.protocol_mode)
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
        "rewritten_files_count": int(rewritten_files_count),
        "rewritten_fields_count": int(rewritten_fields_count),
        "installer_invocation": {
            "tool": "identity-installer",
            "entrypoint": "scripts/identity_installer.py",
            "command": " ".join(["identity-installer", operation, "--identity-id", args.identity_id]),
        },
        "protocol_mode": protocol["protocol_mode"],
        "protocol_root": protocol["protocol_root"],
        "protocol_commit_sha": protocol["protocol_commit_sha"],
        "protocol_ref": protocol["protocol_ref"],
        "identity_home": str(default_identity_home()),
        "catalog_path": str(Path(args.catalog).expanduser().resolve()),
        "resolved_scope": str(args.scope or ""),
        "resolved_pack_path": str(source_pack.expanduser().resolve()),
    }
    if backup_ref:
        report["backup_ref"] = backup_ref
    if rollback_ref:
        report["rollback_ref"] = rollback_ref
    report_path = Path(args.report_dir) / f"{report_id}.json"
    return report, report_path


def cmd_plan(args: argparse.Namespace) -> int:
    _enforce_target_boundary(args)
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
    rc = _single_active_precheck(
        Path(args.catalog).expanduser().resolve(),
        args.identity_id,
        auto_converge=bool(getattr(args, "auto_converge_active", False)),
    )
    if rc != 0:
        return rc
    _enforce_target_boundary(args)
    src = _resolve_source_pack(args)
    dst = _resolve_target_pack(args)
    src_sig = _dir_signature(src)
    dst_sig = _dir_signature(dst) if dst.exists() else ""
    conflict_type, action = _classify_conflict(src_sig, dst_sig, dst.exists(), args.destructive_replace)

    backup_ref = ""
    rollback_ref = ""
    changed: list[str] = []
    rewritten_files_count = 0
    rewritten_fields_count = 0
    if not dry_run and action == "guarded_apply":
        if dst.exists():
            backup_dir = Path(args.backup_dir) / f"{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(dst, backup_dir)
            backup_ref = backup_dir.as_posix()
            rollback_ref = f"restore_from:{backup_ref}"
        changed = _sync_pack(src, dst)
        rewritten_files_count, rewritten_fields_count = _rewrite_identity_contract_paths(dst, old_root=src)

    if args.register and not dry_run:
        identity_profile = "fixture" if bool(args.allow_repo_target) else "runtime"
        identity_runtime_mode = "demo_only" if bool(args.allow_repo_target) else "local_only"
        _register_identity(
            Path(args.catalog),
            args.identity_id,
            args.title,
            args.description,
            (Path(args.target_root) / args.identity_id).as_posix(),
            args.activate,
            profile=identity_profile,
            runtime_mode=identity_runtime_mode,
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
        rewritten_files_count=rewritten_files_count,
        rewritten_fields_count=rewritten_fields_count,
    )
    _write_json(report_path, report)

    mirror = None
    if bool(getattr(args, "emit_repo_fixture_evidence", False)):
        # explicit compatibility mirror for fixture/demo-only validation
        mirror = Path("identity/runtime/examples/install") / f"install-report-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{args.identity_id}.json"
        _write_json(mirror, report)

    print(f"report={report_path}")
    if mirror is not None:
        print(f"mirror={mirror}")
    print(f"conflict_type={conflict_type}")
    print(f"action={action}")
    if not dry_run and action == "guarded_apply":
        print(
            "rewrite_summary="
            f"files:{rewritten_files_count} fields:{rewritten_fields_count}"
        )
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
    _enforce_target_boundary(args)
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
    identity_home = default_identity_home()
    ap = argparse.ArgumentParser(description="Identity installer CLI (installer-plane)")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--identity-id", required=True)
    common.add_argument("--source-pack", default="")
    common.add_argument("--target-root", default=str(default_local_instances_root(identity_home)))
    common.add_argument("--pack-root", default=str(default_local_instances_root(identity_home)))
    common.add_argument("--catalog", default=str(default_local_catalog_path(identity_home)))
    common.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    common.add_argument("--scope", default="")
    common.add_argument("--canonical-root", default="")
    common.add_argument("--report-dir", default="/tmp/identity-install-reports")
    common.add_argument("--backup-dir", default="/tmp/identity-install-backups")
    common.add_argument("--destructive-replace", action="store_true")
    common.add_argument("--allow-repo-target", action="store_true")
    common.add_argument("--allow-repo-target-confirm", default="")
    common.add_argument("--allow-repo-target-purpose", default="")
    common.add_argument("--register", action="store_true")
    common.add_argument("--activate", action="store_true")
    common.add_argument("--title", default="")
    common.add_argument("--description", default="")
    common.add_argument("--auto-converge-active", action="store_true")
    common.add_argument("--protocol-root", default="")
    common.add_argument("--protocol-mode", choices=["mode_a_shared", "mode_b_standalone"], default="mode_a_shared")
    common.add_argument(
        "--emit-repo-fixture-evidence",
        action="store_true",
        help="emit repository fixture mirror evidence under identity/runtime/examples/install (default disabled)",
    )

    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", parents=[common])
    sub.add_parser("dry-run", parents=[common])
    sub.add_parser("install", parents=[common])
    sub.add_parser("verify", parents=[common])
    sub.add_parser("scan", parents=[common])
    sub.add_parser("adopt", parents=[common])
    sub.add_parser("lock", parents=[common])
    sub.add_parser("repair-paths", parents=[common])
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
    if args.command == "scan":
        return cmd_scan(args)
    if args.command == "adopt":
        return cmd_adopt(args)
    if args.command == "lock":
        return cmd_lock(args)
    if args.command == "repair-paths":
        return cmd_repair_paths(args)
    if args.command == "rollback":
        return cmd_rollback(args)
    print(f"[FAIL] unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PermissionError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
