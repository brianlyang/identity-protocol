#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def _required_fields(pack: Path) -> list[str]:
    task_path = pack / "CURRENT_TASK.json"
    if not task_path.exists():
        return ["rule_id", "type", "trigger", "action", "evidence_run_id", "scope", "confidence", "updated_at"]
    try:
        task = _load_json(task_path)
    except Exception:
        return ["rule_id", "type", "trigger", "action", "evidence_run_id", "scope", "confidence", "updated_at"]
    contract = task.get("rulebook_contract") or {}
    fields = contract.get("required_fields") or []
    out = [str(x).strip() for x in fields if str(x).strip()]
    if not out:
        out = ["rule_id", "type", "trigger", "action", "evidence_run_id", "scope", "confidence", "updated_at"]
    return out


def _rulebook_path(pack: Path) -> Path:
    task_path = pack / "CURRENT_TASK.json"
    if not task_path.exists():
        return pack / "RULEBOOK.jsonl"
    try:
        task = _load_json(task_path)
    except Exception:
        return pack / "RULEBOOK.jsonl"
    contract = task.get("rulebook_contract") or {}
    value = str(contract.get("rulebook_path", "")).strip()
    if not value:
        return pack / "RULEBOOK.jsonl"
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (pack / p).resolve()
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill safe missing fields in RULEBOOK.jsonl historical rows.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--apply", action="store_true", help="persist changes to rulebook")
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
    required = _required_fields(pack)
    rulebook = _rulebook_path(pack)
    if not rulebook.exists():
        print(f"[OK] rulebook missing, nothing to backfill: {rulebook}")
        return 0

    lines = rulebook.read_text(encoding="utf-8").splitlines()
    changed = 0
    unresolved: list[tuple[int, list[str]]] = []
    out_lines: list[str] = []
    for i, raw in enumerate(lines, start=1):
        s = raw.strip()
        if not s:
            out_lines.append(raw)
            continue
        try:
            row = json.loads(s)
        except Exception:
            out_lines.append(raw)
            continue
        missing = [f for f in required if not str(row.get(f, "")).strip()]
        if not missing:
            out_lines.append(json.dumps(row, ensure_ascii=False))
            continue
        safe_fixed = []
        for field in missing:
            if field == "scope":
                row["scope"] = "identity_learning_loop" if str(row.get("type", "")).strip() == "bootstrap" else "identity_update_cycle"
                safe_fixed.append(field)
        unresolved_fields = [f for f in missing if f not in safe_fixed]
        if safe_fixed:
            changed += 1
        if unresolved_fields:
            unresolved.append((i, unresolved_fields))
        out_lines.append(json.dumps(row, ensure_ascii=False))

    if changed == 0 and not unresolved:
        print(f"[OK] rulebook schema already healthy: {rulebook}")
        return 0

    if args.apply and changed > 0:
        rulebook.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        print(f"[OK] backfilled rulebook rows: {changed}")
        print(f"     rulebook={rulebook}")
    else:
        print(f"[INFO] backfill preview rows: {changed}")
        print("       use --apply to persist")

    if unresolved:
        print("[FAIL] unresolved missing required fields remain:")
        for line_no, fields in unresolved[:20]:
            print(f"  - line {line_no}: missing {fields}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

