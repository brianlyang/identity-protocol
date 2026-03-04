#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from glob import glob
from pathlib import Path
from typing import Any

import yaml


def _repo_runtime_metrics_path(repo_root: Path, identity_id: str) -> Path:
    return repo_root / ".codex" / "identity" / "runtime" / identity_id / "metrics" / f"{identity_id}-route-quality.json"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _resolve_pack_and_task(catalog_path: Path, identity_id: str) -> tuple[Path, Path]:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")

    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        pack = Path(pack_path).expanduser().resolve()
        p = pack / "CURRENT_TASK.json"
        if p.exists():
            return pack, p

    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy.parent, legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _pct(n: int, d: int) -> float:
    if d <= 0:
        return 0.0
    return round((n / d) * 100.0, 2)


def _resolve_log_files(pattern: str) -> list[Path]:
    expanded = os.path.expanduser(pattern)
    if os.path.isabs(expanded):
        return [Path(p).expanduser().resolve() for p in sorted(glob(expanded))]
    return [p.resolve() for p in sorted(Path(".").glob(expanded))]


def main() -> int:
    ap = argparse.ArgumentParser(description="Export route quality metrics from handoff production logs")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument(
        "--allow-repo-runtime-fallback",
        action="store_true",
        help="explicitly allow fallback output under <repo>/.codex/identity/runtime for fixture/debug only",
    )
    args = ap.parse_args()

    pack_path, task_path = _resolve_pack_and_task(Path(args.catalog).expanduser().resolve(), args.identity_id)
    task = _load_json(task_path)

    contract = task.get("agent_handoff_contract") or {}
    pattern = str(contract.get("handoff_log_path_pattern") or "")
    if not pattern:
        print("[FAIL] agent_handoff_contract.handoff_log_path_pattern missing")
        return 1

    files = _resolve_log_files(pattern)
    if not files:
        print(f"[FAIL] no handoff logs for metrics: pattern={pattern}")
        return 1

    total = 0
    route_hit = 0
    misroute = 0
    fallback = 0
    blocked = 0
    first_pass_success = 0
    knowledge_reuse = 0
    replay_success = 0
    policy_drift_incidents = 0

    for p in files:
        rec = _load_json(p)
        total += 1

        rd = rec.get("route_decision") or {}
        is_hit = bool(rd.get("route_hit", False))
        is_misroute = bool(rd.get("misroute", False))
        used_fallback = bool(rd.get("fallback", False))

        result = str(rec.get("result") or "")
        if result == "BLOCKED":
            blocked += 1
        if result == "PASS" and not used_fallback:
            first_pass_success += 1

        if is_hit:
            route_hit += 1
        if is_misroute:
            misroute += 1
        if used_fallback:
            fallback += 1

        # Prefer explicit runtime fields; fallback to conservative heuristics.
        if bool(rec.get("knowledge_reuse", False)) or bool((rec.get("rulebook_update") or {}).get("applied", False)):
            knowledge_reuse += 1
        if str(rec.get("replay_status") or "").upper() == "PASS":
            replay_success += 1

        if bool(rec.get("policy_drift", False)) or bool(rec.get("contract_violation", False)):
            policy_drift_incidents += 1

    metrics = {
        "identity_id": args.identity_id,
        "task_id": str(task.get("task_id") or ""),
        "source_pattern": pattern,
        "total_routes": total,
        "route_hit_count": route_hit,
        "misroute_count": misroute,
        "fallback_count": fallback,
        "blocked_count": blocked,
        "first_pass_success_count": first_pass_success,
        "knowledge_reuse_count": knowledge_reuse,
        "replay_success_count": replay_success,
        "policy_drift_incidents": policy_drift_incidents,
        "route_hit_rate": _pct(route_hit, total),
        "misroute_rate": _pct(misroute, total),
        "fallback_rate": _pct(fallback, total),
        "first_pass_success_rate": _pct(first_pass_success, total),
        "knowledge_reuse_rate": _pct(knowledge_reuse, total),
        "replay_success_rate": _pct(replay_success, total),
    }

    if args.out:
        out = Path(args.out).expanduser().resolve()
    else:
        root = os.environ.get("IDENTITY_RUNTIME_OUTPUT_ROOT", "").strip()
        repo_root = Path.cwd().resolve()
        if root:
            out = Path(root).expanduser().resolve() / "metrics" / f"{args.identity_id}-route-quality.json"
        else:
            pack_runtime_out = pack_path / "runtime" / "metrics" / f"{args.identity_id}-route-quality.json"
            if _is_within(pack_runtime_out, repo_root):
                if args.allow_repo_runtime_fallback:
                    out = _repo_runtime_metrics_path(repo_root, args.identity_id)
                else:
                    print(
                        "[FAIL] IP-PATH-001 route metrics output would resolve inside protocol repo; "
                        "set IDENTITY_RUNTIME_OUTPUT_ROOT or pass --out. "
                        "For fixture/debug only, pass --allow-repo-runtime-fallback."
                    )
                    print(f"       candidate={pack_runtime_out}")
                    return 1
            else:
                out = pack_runtime_out
    if _is_within(out, Path.cwd().resolve()) and not args.allow_repo_runtime_fallback:
        print(
            "[FAIL] IP-PATH-001 metrics output inside repository is blocked by default; "
            "use IDENTITY_RUNTIME_OUTPUT_ROOT / --out, or explicit --allow-repo-runtime-fallback for debug only."
        )
        print(f"       out={out}")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] route quality metrics exported: {out}")
    print(json.dumps(metrics, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
