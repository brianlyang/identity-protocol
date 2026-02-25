#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CheckResult:
    rc: int
    ok: bool
    tail: str = ""
    stdout: str = ""
    stderr: str = ""


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> CheckResult:
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=env)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    tail = out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")
    return CheckResult(rc=p.returncode, ok=p.returncode == 0, tail=tail, stdout=out, stderr=err)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid yaml root: {path}")
    return data


def _catalog_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = _load_yaml(path)
    return [x for x in (data.get("identities") or []) if isinstance(x, dict)]


def _parse_json_safely(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    lines = raw.splitlines()
    if lines and lines[-1].startswith("overall_release_decision="):
        try:
            return json.loads("\n".join(lines[:-1]))
        except Exception:
            return None
    return None


def _latest_runtime_report(identity_id: str, report_dir: Path) -> Path | None:
    if not report_dir.exists():
        return None
    rows = [
        p
        for p in report_dir.glob(f"identity-upgrade-exec-{identity_id}-*.json")
        if not p.name.endswith("-patch-plan.json")
    ]
    if not rows:
        return None
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows[-1]


def _severity_for_row(row: dict[str, Any]) -> str:
    active = str(row.get("status", "")).lower() == "active"
    profile = str(row.get("profile", "")).lower()
    checks = row.get("checks", {})
    core_fail = any(
        not checks.get(name, {}).get("ok", False)
        for name in ("scope_resolution", "scope_isolation", "scope_persistence", "runtime_contract")
    )
    prompt_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("prompt_quality", "prompt_activation", "prompt_lifecycle")
    )
    capability_fail = any(
        name in checks and not checks.get(name, {}).get("ok", False)
        for name in ("capability_activation_preflight", "capability_activation_report")
    )
    if active and profile == "runtime" and (core_fail or prompt_fail or capability_fail):
        return "P0"
    if core_fail or prompt_fail or capability_fail:
        return "P1"
    return "OK"


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan all configured identities and emit cross-catalog governance status.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--project-catalog", default="")
    ap.add_argument("--global-catalog", default="")
    ap.add_argument("--include-repo-catalog", action="store_true")
    ap.add_argument("--with-docs-contract", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    repo_catalog = (repo_root / args.repo_catalog).resolve() if not Path(args.repo_catalog).is_absolute() else Path(args.repo_catalog)
    if not repo_catalog.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog}")
        return 2

    project_catalog = Path(args.project_catalog).expanduser().resolve() if args.project_catalog else (repo_root.parent / ".agents/identity/catalog.local.yaml").resolve()
    global_catalog = Path(args.global_catalog).expanduser().resolve() if args.global_catalog else (Path.home() / ".codex/identity/catalog.local.yaml").resolve()

    catalog_list: list[tuple[str, Path]] = []
    if args.include_repo_catalog:
        catalog_list.append(("repo", repo_catalog))
    catalog_list.extend([("project", project_catalog), ("global", global_catalog)])

    payload: dict[str, Any] = {
        "repo_root": str(repo_root),
        "repo_catalog": str(repo_catalog),
        "catalogs": [],
        "summary": {"total_identities": 0, "p0": 0, "p1": 0, "ok": 0},
    }

    for layer, catalog in catalog_list:
        rows = _catalog_rows(catalog) if catalog.exists() else []
        layer_out: dict[str, Any] = {"layer": layer, "catalog": str(catalog), "exists": catalog.exists(), "identities": []}
        for row in rows:
            iid = str(row.get("id", "")).strip()
            if not iid:
                continue
            item: dict[str, Any] = {
                "identity_id": iid,
                "status": row.get("status"),
                "profile": row.get("profile"),
                "runtime_mode": row.get("runtime_mode"),
                "pack_path": row.get("pack_path"),
                "checks": {},
            }
            resolve = _run(
                [
                    "python3",
                    "scripts/resolve_identity_context.py",
                    "resolve",
                    "--identity-id",
                    iid,
                    "--repo-catalog",
                    str(repo_catalog),
                    "--local-catalog",
                    str(catalog),
                ],
                cwd=repo_root,
            )
            item["checks"]["resolve"] = {"rc": resolve.rc, "ok": resolve.ok, "tail": resolve.tail}
            resolved_scope = "USER"
            if resolve.ok:
                data = _parse_json_safely(resolve.stdout) or {}
                item["resolved_scope"] = data.get("resolved_scope")
                item["source_layer"] = data.get("source_layer")
                item["conflict_detected"] = data.get("conflict_detected")
                resolved_scope = str(data.get("resolved_scope", "")).upper() or "USER"

            is_active_runtime = str(row.get("status", "")).lower() == "active" and str(row.get("profile", "")).lower() == "runtime"
            checks = {
                "scope_resolution": [
                    "python3",
                    "scripts/validate_identity_scope_resolution.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                ],
                "scope_isolation": [
                    "python3",
                    "scripts/validate_identity_scope_isolation.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                ],
                "scope_persistence": [
                    "python3",
                    "scripts/validate_identity_scope_persistence.py",
                    "--catalog",
                    str(catalog),
                    "--repo-catalog",
                    str(repo_catalog),
                    "--identity-id",
                    iid,
                ],
                "prompt_quality": [
                    "python3",
                    "scripts/validate_identity_prompt_quality.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                    "--scope",
                    resolved_scope,
                ],
                "runtime_contract": [
                    "python3",
                    "scripts/validate_identity_runtime_contract.py",
                    "--catalog",
                    str(catalog),
                    "--identity-id",
                    iid,
                ],
            }
            cap_preflight_cmd = [
                "python3",
                "scripts/validate_identity_capability_activation.py",
                "--catalog",
                str(catalog),
                "--repo-catalog",
                str(repo_catalog),
                "--identity-id",
                iid,
            ]
            if is_active_runtime:
                cap_preflight_cmd.append("--require-activated")
            checks["capability_activation_preflight"] = cap_preflight_cmd
            if is_active_runtime:
                runtime_report_dir_path = Path(str(row.get("pack_path", ""))).expanduser().resolve() / "runtime" / "reports"
                runtime_report_dir = str(runtime_report_dir_path)
                checks["prompt_activation"] = [
                    "python3",
                    "scripts/validate_identity_prompt_activation.py",
                    "--identity-id",
                    iid,
                    "--catalog",
                    str(catalog),
                    "--report-dir",
                    runtime_report_dir,
                ]
                checks["prompt_lifecycle"] = [
                    "python3",
                    "scripts/validate_identity_prompt_lifecycle.py",
                    "--identity-id",
                    iid,
                    "--report-dir",
                    runtime_report_dir,
                ]
                latest_report = _latest_runtime_report(iid, runtime_report_dir_path)
                if latest_report:
                    checks["capability_activation_report"] = [
                        "python3",
                        "scripts/validate_identity_capability_activation.py",
                        "--identity-id",
                        iid,
                        "--report",
                        str(latest_report),
                        "--require-activated",
                    ]
            for name, cmd in checks.items():
                r = _run(cmd, cwd=repo_root)
                item["checks"][name] = {"rc": r.rc, "ok": r.ok, "tail": r.tail}

            env = os.environ.copy()
            env["IDENTITY_CATALOG"] = str(catalog)
            three_plane = _run(
                [
                    "python3",
                    "scripts/report_three_plane_status.py",
                    "--identity-id",
                    iid,
                    *(["--with-docs-contract"] if args.with_docs_contract else []),
                ],
                cwd=repo_root,
                env=env,
            )
            item["checks"]["three_plane"] = {"rc": three_plane.rc, "ok": three_plane.ok, "tail": three_plane.tail}
            tp = _parse_json_safely(three_plane.stdout)
            if tp:
                item["three_plane"] = {
                    "instance": tp.get("instance_plane_status"),
                    "repo": tp.get("repo_plane_status"),
                    "release": tp.get("release_plane_status"),
                    "overall": tp.get("overall_release_decision"),
                }
            item["severity"] = _severity_for_row(item)
            payload["summary"]["total_identities"] += 1
            if item["severity"] == "P0":
                payload["summary"]["p0"] += 1
            elif item["severity"] == "P1":
                payload["summary"]["p1"] += 1
            else:
                payload["summary"]["ok"] += 1
            layer_out["identities"].append(item)

        payload["catalogs"].append(layer_out)

    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote: {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
