#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _extract(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text, flags=re.MULTILINE)
    if not m:
        raise ValueError(f"cannot extract {label} using pattern: {pattern}")
    return m.group(1)


def main() -> int:
    protocol = _read("identity/protocol/IDENTITY_PROTOCOL.md")
    readme = _read("README.md")
    versioning = _read("VERSIONING.md")
    req = _read("requirements-dev.txt")

    try:
        protocol_v = _extract(r"^#\s+Identity Protocol\s+v(\d+\.\d+\.\d+)\s+\(draft\)", protocol, "protocol version")
        readme_v = _extract(r"Protocol version:\s+`v(\d+\.\d+\.\d+)`\s+\(draft\)", readme, "README protocol version")
        versioning_v = _extract(
            r"^##\s+Release metadata synchronization\s+\(v(\d+\.\d+\.\d+)\+\)",
            versioning,
            "VERSIONING release sync version",
        )
        req_v = _extract(r"release metadata synchronized in v(\d+\.\d+\.\d+)\s+draft", req, "requirements baseline version")
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    versions = {
        "IDENTITY_PROTOCOL.md": protocol_v,
        "README.md": readme_v,
        "VERSIONING.md": versioning_v,
        "requirements-dev.txt": req_v,
    }
    base = protocol_v
    mismatch = {k: v for k, v in versions.items() if v != base}
    if mismatch:
        print("[FAIL] release metadata version drift detected")
        print(f"       expected all files aligned to v{base}")
        for k, v in versions.items():
            print(f"       - {k}: v{v}")
        return 1

    print(f"[OK] release metadata synchronized to v{base}")
    print("validate_release_metadata_sync PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
