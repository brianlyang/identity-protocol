#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any

import yaml

REQ_KEYS = [
    "required",
    "positive_rulebook_path",
    "negative_rulebook_path",
    "required_fields",
    "cross_layer_feedback_targets",
    "promote_requires_replay_pass",
    "sample_report_path_pattern",
]


def _protocol_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    catalog_dir = catalog_path.expanduser().resolve().parent
    protocol_root = _protocol_root().resolve()
    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        raw_pack = Path(pack_path).expanduser()
        candidate_packs: list[Path] = []
        if raw_pack.is_absolute():
            candidate_packs.append(raw_pack.resolve())
        else:
            candidate_packs.append((catalog_dir / raw_pack).resolve())
            candidate_packs.append((protocol_root / raw_pack).resolve())
        for pack in candidate_packs:
            p = (pack / "CURRENT_TASK.json").resolve()
            if p.exists():
                return p
    legacy = _protocol_root() / "identity" / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _validate_rulebook(path: Path, req_fields: list[str], label: str) -> int:
    if not path.exists():
        print(f"[FAIL] {label} not found: {path}")
        return 1
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print(f"[FAIL] {label} empty: {path}")
        return 1
    rc = 0
    for i, ln in enumerate(lines, start=1):
        try:
            row = json.loads(ln)
        except Exception as e:
            print(f"[FAIL] {label} line {i} invalid json: {e}")
            rc = 1
            continue
        missing = [k for k in req_fields if k not in row]
        if missing:
            print(f"[FAIL] {label} line {i} missing fields: {missing}")
            rc = 1
    if rc == 0:
        print(f"[OK] {label} validated: {path}")
    return rc


def _resolve_contract_path(raw: str, *, pack_root: Path, protocol_root: Path) -> Path:
    text = str(raw or "").strip()
    if not text:
        return Path()
    p = Path(text).expanduser()
    if p.is_absolute():
        return p.resolve()
    pack_candidate = (pack_root / p).resolve()
    if pack_candidate.exists():
        return pack_candidate
    protocol_candidate = (protocol_root / p).resolve()
    if protocol_candidate.exists():
        return protocol_candidate
    # deterministic fail-path: prefer pack-root anchored interpretation
    return pack_candidate


def _glob_paths(pattern: str, *, pack_root: Path, protocol_root: Path) -> list[Path]:
    raw = str(pattern or "").strip()
    if not raw:
        return []
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    if p.is_absolute():
        if has_magic:
            return sorted(Path(x).resolve() for x in glob.glob(str(p)))
        return [p.resolve()] if p.exists() else []
    preferred = sorted(pack_root.glob(raw))
    if preferred:
        return preferred
    return sorted(protocol_root.glob(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate experience feedback contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate experience feedback for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")
    pack_root = task_path.parent.resolve()
    protocol_root = _protocol_root().resolve()

    task = _load_json(task_path)
    c = task.get("experience_feedback_contract") or {}
    if not isinstance(c, dict) or not c:
        print("[FAIL] missing experience_feedback_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        print(f"[FAIL] experience_feedback_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        print("[FAIL] experience_feedback_contract.required must be true")
        return 1

    req_fields = c.get("required_fields") or []
    rc = 0
    positive_path = _resolve_contract_path(
        str(c.get("positive_rulebook_path", "")),
        pack_root=pack_root,
        protocol_root=protocol_root,
    )
    negative_path = _resolve_contract_path(
        str(c.get("negative_rulebook_path", "")),
        pack_root=pack_root,
        protocol_root=protocol_root,
    )
    rc |= _validate_rulebook(positive_path, req_fields, "positive_rulebook")
    rc |= _validate_rulebook(negative_path, req_fields, "negative_rulebook")

    targets = set(c.get("cross_layer_feedback_targets") or [])
    need = {"routing_contract", "capability_orchestration_contract", "gates"}
    if not need.issubset(targets):
        print(f"[FAIL] cross_layer_feedback_targets missing: {sorted(need-targets)}")
        rc = 1

    replay_gate = c.get("promote_requires_replay_pass")
    if replay_gate is None:
        replay_gate = c.get("promotion_requires_replay_pass")
    if replay_gate is not True:
        print("[FAIL] replay-pass promotion gate must be true (promote_requires_replay_pass or promotion_requires_replay_pass)")
        rc = 1

    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else (pack_root / "runtime" / "examples" / f"{args.identity_id}-experience-feedback-sample.json").resolve()
    )
    if not report_path.exists():
        files = _glob_paths(
            str(c.get("sample_report_path_pattern", "")),
            pack_root=pack_root,
            protocol_root=protocol_root,
        )
        if files:
            report_path = files[-1]
    if not report_path.exists():
        print(f"[FAIL] missing experience feedback sample report: {report_path}")
        return 1

    report = _load_json(report_path)
    all_updates = (report.get("positive_updates") or []) + (report.get("negative_updates") or [])
    if not all_updates:
        print("[FAIL] sample report requires positive_updates or negative_updates")
        return 1

    for i, u in enumerate(all_updates):
        if not isinstance(u, dict):
            print(f"[FAIL] update[{i}] must be object")
            rc = 1
            continue
        missing_u = [k for k in req_fields if k not in u]
        if missing_u:
            print(f"[FAIL] update[{i}] missing fields: {missing_u}")
            rc = 1
        if u.get("replay_status") != "PASS":
            print(f"[FAIL] update[{i}].replay_status must be PASS")
            rc = 1

    if rc:
        return 1

    if args.self_test:
        pos = sorted((protocol_root / "identity/runtime/examples/experience/positive").glob("*.json"))
        neg = sorted((protocol_root / "identity/runtime/examples/experience/negative").glob("*.json"))
        if len(pos) < 2 or len(neg) < 1:
            print("[FAIL] experience self-test requires >=2 positive and >=1 negative samples")
            return 1
        # positives should pass required fields + replay PASS
        for p in pos:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] positive sample missing updates: {p}")
                return 1
            for i, u in enumerate(updates):
                miss = [k for k in req_fields if k not in u]
                if miss:
                    print(f"[FAIL] positive sample missing fields {miss}: {p}#{i}")
                    return 1
                if u.get("replay_status") != "PASS":
                    print(f"[FAIL] positive sample replay_status must be PASS: {p}#{i}")
                    return 1
        # negatives should contain at least one non-PASS replay
        for p in neg:
            r = _load_json(p)
            updates = (r.get("positive_updates") or []) + (r.get("negative_updates") or [])
            if not updates:
                print(f"[FAIL] negative sample missing updates: {p}")
                return 1
            if not any(u.get("replay_status") != "PASS" for u in updates if isinstance(u, dict)):
                print(f"[FAIL] negative sample did not include replay_status!=PASS: {p}")
                return 1
        print("[OK] experience self-test passed")

    print("Experience feedback contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
