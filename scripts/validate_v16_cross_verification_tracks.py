#!/usr/bin/env python3
from __future__ import annotations

from validate_v16_intake_evidence_core import MODE_INTAKE_CONTRACT, main as core_main


def main() -> int:
    return core_main(forced_mode=MODE_INTAKE_CONTRACT)


if __name__ == "__main__":
    raise SystemExit(main())
