#!/usr/bin/env python3
from __future__ import annotations

from validate_intake_evidence_core import MODE_PROMOTION_GATE, main as core_main


def main() -> int:
    return core_main(forced_mode=MODE_PROMOTION_GATE)


if __name__ == "__main__":
    raise SystemExit(main())
