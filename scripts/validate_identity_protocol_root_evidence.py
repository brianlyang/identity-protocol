#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQ_FIELDS = [
    "protocol_mode",
    "protocol_root",
    "protocol_commit_sha",
    "protocol_ref",
    "identity_home",
    "catalog_path",
    "generated_at",
]

VALID_MODES = {"mode_a_shared", "mode_b_standalone"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_reports(identity_id: str) -> list[Path]:
    roots = [
        Path("identity/runtime/reports"),
        Path("identity/runtime/reports/install"),
        Path("identity/runtime/reports/activation"),
    ]
    rows: list[Path] = []
    for r in roots:
        if not r.exists():
            continue
        rows.extend(sorted(r.glob(f"*{identity_id}*.json"), key=lambda p: p.stat().st_mtime))
    return rows


def _is_abs_path(v: str) -> bool:
    try:
        return Path(v).is_absolute()
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-root evidence fields in creator/installer/update reports")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="", help="optional explicit report path")
    args = ap.parse_args()

    reports: list[Path] = []
    if args.report:
        p = Path(args.report)
        if not p.exists():
            print(f"[FAIL] report not found: {p}")
            return 1
        reports = [p]
    else:
        reports = _iter_reports(args.identity_id)

    if not reports:
        print(f"[FAIL] no protocol evidence reports found for identity={args.identity_id}")
        return 1

    rc = 0
    protocol_roots: set[str] = set()
    mode_b_seen = False
    arbitration_present = False

    for rp in reports:
        try:
            row = _load_json(rp)
        except Exception as e:
            print(f"[FAIL] invalid json report: {rp}: {e}")
            rc = 1
            continue

        if str(row.get("identity_id", "")).strip() != args.identity_id:
            # activation reports may use target_identity_id
            tid = str(row.get("target_identity_id", "")).strip()
            if tid != args.identity_id:
                continue

        missing = [k for k in REQ_FIELDS if k not in row]
        if missing:
            print(f"[FAIL] report missing protocol evidence fields: {rp} -> {missing}")
            rc = 1
            continue

        mode = str(row.get("protocol_mode", "")).strip()
        root = str(row.get("protocol_root", "")).strip()
        sha = str(row.get("protocol_commit_sha", "")).strip()

        if mode not in VALID_MODES:
            print(f"[FAIL] invalid protocol_mode in {rp}: {mode!r}")
            rc = 1
        if not _is_abs_path(root):
            print(f"[FAIL] protocol_root must be absolute in {rp}: {root!r}")
            rc = 1
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            print(f"[FAIL] protocol_commit_sha must be 40-hex in {rp}: {sha!r}")
            rc = 1

        protocol_roots.add(root)
        if mode == "mode_b_standalone":
            mode_b_seen = True
        if str(row.get("arbitration_note_id", "")).strip():
            arbitration_present = True

    if len(protocol_roots) > 1 and not arbitration_present:
        print("[FAIL] multiple protocol roots detected without arbitration_note_id")
        for r in sorted(protocol_roots):
            print(f"       - {r}")
        rc = 1

    if rc != 0:
        return 1

    print(f"[OK] protocol root evidence validated for identity={args.identity_id}")
    print(f"     reports_checked={len(reports)}")
    print(f"     protocol_roots={len(protocol_roots)}")
    if mode_b_seen:
        print("     mode_b_detected=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
