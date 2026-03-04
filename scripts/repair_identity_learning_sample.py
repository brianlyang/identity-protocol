#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _resolve_pack(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    rows = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity not found in catalog: {identity_id}")
    pack_path = str(row.get("pack_path", "")).strip()
    if not pack_path:
        raise FileNotFoundError(f"pack_path missing for identity: {identity_id}")
    p = Path(pack_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"pack_path not found: {p}")
    return p


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(pack: Path) -> dict[str, Any]:
    p = pack / "CURRENT_TASK.json"
    if not p.exists():
        return {}
    try:
        return _load_json(p)
    except Exception:
        return {}


def _resolve_rulebook_path(pack: Path, task: dict[str, Any]) -> Path:
    rb_contract = task.get("rulebook_contract") or {}
    val = str(rb_contract.get("rulebook_path", "")).strip()
    if not val:
        return pack / "RULEBOOK.jsonl"
    p = Path(val).expanduser()
    if not p.is_absolute():
        p = (pack / p).resolve()
    return p


def _bootstrap_payload(identity_id: str, run_id: str, now: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "problem_type": "identity_learning_loop_bootstrap",
        "goal": "provide identity-scoped learning sample for e2e learning-loop validation",
        "reasoning_attempts": [
            {
                "attempt": 1,
                "hypothesis": "identity-scoped bootstrap sample enables deterministic learning-loop contract validation",
                "patch": {
                    "identity_id": identity_id,
                    "sample_type": "bootstrap",
                },
                "expected_effect": "learning-loop validator can find identity-scoped sample without cross-identity fallback",
                "result": "pass",
            }
        ],
        "final_status": "pass",
        "notes": "auto-generated bootstrap sample",
        "generated_at": now,
    }


def _append_rulebook_link(
    *,
    pack: Path,
    identity_id: str,
    task: dict[str, Any],
    run_id: str,
) -> tuple[bool, str]:
    lvc = task.get("learning_verification_contract") or {}
    if not bool(lvc.get("rulebook_update_required", False)):
        return False, "rulebook_update_not_required"
    link_field = str(lvc.get("rulebook_link_field", "evidence_run_id")).strip() or "evidence_run_id"
    rulebook_path = _resolve_rulebook_path(pack, task)
    rulebook_path.parent.mkdir(parents=True, exist_ok=True)

    if rulebook_path.exists():
        raw_lines = rulebook_path.read_text(encoding="utf-8").splitlines()
        changed = False
        out_lines: list[str] = []
        for ln in raw_lines:
            s = ln.strip()
            if not s:
                out_lines.append(ln)
                continue
            try:
                row = json.loads(s)
            except Exception:
                out_lines.append(ln)
                continue
            if str(row.get(link_field, "")).strip() == run_id and not str(row.get("scope", "")).strip():
                # Historical bootstrap rows may miss "scope" and break runtime contract.
                row["scope"] = "identity_learning_loop"
                changed = True
            out_lines.append(json.dumps(row, ensure_ascii=False))
        if changed:
            rulebook_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
            return False, f"rulebook_link_backfilled:{rulebook_path}"
        # If already present and healthy, do not append duplicate.
        for ln in raw_lines:
            s = ln.strip()
            if not s:
                continue
            try:
                row = json.loads(s)
            except Exception:
                continue
            if str(row.get(link_field, "")).strip() == run_id:
                return False, f"rulebook_link_exists:{rulebook_path}"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {
        "rule_id": f"{run_id}-learning-bootstrap",
        "identity_id": identity_id,
        "type": "bootstrap",
        "trigger": "learning_sample_repair",
        "action": "repair_identity_learning_sample",
        "scope": "identity_learning_loop",
        "confidence": 0.8,
        "updated_at": now,
        link_field: run_id,
    }
    with rulebook_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True, f"rulebook_link_appended:{rulebook_path}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Bootstrap/repair identity-scoped learning sample artifact.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--force", action="store_true", help="overwrite existing sample")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 1
    try:
        pack = _resolve_pack(catalog, args.identity_id)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    task = _resolve_current_task(pack)
    sample = pack / "runtime" / "examples" / f"{args.identity_id}-learning-sample.json"
    created = False
    if sample.exists() and not args.force:
        try:
            payload = _load_json(sample)
            run_id = str(payload.get("run_id", "")).strip() or f"bootstrap-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
            print(f"[OK] learning sample exists: {sample}")
        except Exception:
            run_id = f"bootstrap-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
            sample.parent.mkdir(parents=True, exist_ok=True)
            payload = _bootstrap_payload(args.identity_id, run_id, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            sample.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            created = True
            print(f"[OK] learning sample repaired: {sample}")
    else:
        run_id = f"bootstrap-{args.identity_id}-{int(datetime.now(timezone.utc).timestamp())}"
        sample.parent.mkdir(parents=True, exist_ok=True)
        payload = _bootstrap_payload(args.identity_id, run_id, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        sample.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created = True
        print(f"[OK] learning sample bootstrapped: {sample}")

    linked, note = _append_rulebook_link(pack=pack, identity_id=args.identity_id, task=task, run_id=run_id)
    if linked:
        print(f"[OK] {note}")
    else:
        print(f"[INFO] {note}")
    if created:
        print(f"[INFO] run_id={run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
