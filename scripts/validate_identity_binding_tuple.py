#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


def _load_report(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"report root must be object: {path}")
    return data


def _is_abs_path(value: str) -> bool:
    try:
        return Path(value).expanduser().is_absolute()
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate identity binding tuple fields in upgrade report (machine-checkable P0 gate)."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", required=True, help="identity upgrade execution report JSON path")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser().resolve()
    if not report_path.exists():
        print(f"[FAIL] report not found: {report_path}")
        return 1

    data = _load_report(report_path)
    failed = False

    def fail(msg: str) -> None:
        nonlocal failed
        failed = True
        print(f"[FAIL] {msg}")

    # Required tuple fields
    identity_id = str(data.get("identity_id", "")).strip()
    identity_home = str(data.get("identity_home", "")).strip()
    catalog_path = str(data.get("catalog_path", "")).strip()
    protocol_root = str(data.get("protocol_root", "")).strip()
    protocol_sha = str(data.get("protocol_commit_sha", "")).strip()
    runtime_output_root = str(data.get("runtime_output_root", "")).strip()
    resolved_pack_path = str(data.get("resolved_pack_path", "")).strip()
    resolved_scope = str(data.get("resolved_scope", "")).strip()

    if identity_id != args.identity_id:
        fail(f"identity_id mismatch: expected={args.identity_id} got={identity_id!r}")

    for key, value in [
        ("identity_home", identity_home),
        ("catalog_path", catalog_path),
        ("protocol_root", protocol_root),
        ("runtime_output_root", runtime_output_root),
        ("resolved_pack_path", resolved_pack_path),
    ]:
        if not value:
            fail(f"{key} missing")
        elif not _is_abs_path(value):
            fail(f"{key} must be absolute path, got={value!r}")

    if not protocol_sha:
        fail("protocol_commit_sha missing")
    elif not SHA40_RE.match(protocol_sha):
        fail(f"protocol_commit_sha must be 40-hex, got={protocol_sha!r}")

    if not resolved_scope:
        fail("resolved_scope missing")

    if not failed:
        # same-domain check: runtime output must be under pack runtime
        pack_runtime = (Path(resolved_pack_path).expanduser().resolve() / "runtime") if resolved_pack_path else None
        if pack_runtime and not Path(runtime_output_root).expanduser().resolve().is_relative_to(pack_runtime):
            fail(
                "runtime_output_root must be under resolved_pack_path/runtime; "
                f"runtime_output_root={runtime_output_root} expected_prefix={pack_runtime}"
            )

    if failed:
        return 1

    print("[OK] identity binding tuple validated")
    print(f"     identity_id={identity_id}")
    print(f"     resolved_scope={resolved_scope}")
    print(f"     catalog_path={catalog_path}")
    print(f"     protocol_root={protocol_root}")
    print(f"     runtime_output_root={runtime_output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

