#!/usr/bin/env python3
"""Validate identity catalog against local schema + manifest semantics."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


def fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def main() -> int:
    root = Path('.')
    schema_path = root / 'identity/catalog/schema/identities.schema.json'
    catalog_path = root / 'identity/catalog/identities.yaml'

    if not schema_path.exists():
        return fail(f"missing schema file: {schema_path}")
    if not catalog_path.exists():
        return fail(f"missing catalog file: {catalog_path}")

    # We intentionally perform semantic checks here to avoid hard dependency on jsonschema package.
    catalog: dict[str, Any] = yaml.safe_load(catalog_path.read_text(encoding='utf-8')) or {}

    for key in ('version', 'default_identity', 'identities'):
        if key not in catalog:
            return fail(f"catalog missing required key: {key}")

    identities = catalog.get('identities')
    if not isinstance(identities, list) or not identities:
        return fail("identities must be a non-empty list")

    ids: set[str] = set()
    has_default = False
    rc = 0

    for i, item in enumerate(identities):
        prefix = f"identities[{i}]"
        if not isinstance(item, dict):
            print(f"[FAIL] {prefix} must be an object")
            rc = 1
            continue

        required = ('id', 'title', 'description', 'status', 'methodology_version', 'pack_path')
        for key in required:
            if key not in item:
                print(f"[FAIL] {prefix} missing required key: {key}")
                rc = 1

        identity_id = str(item.get('id', '')).strip()
        if identity_id:
            if identity_id in ids:
                print(f"[FAIL] duplicate identity id: {identity_id}")
                rc = 1
            ids.add(identity_id)
            if identity_id == catalog['default_identity']:
                has_default = True

        pack_path = str(item.get('pack_path', '')).strip()
        if pack_path and not (root / pack_path).exists():
            print(f"[FAIL] {prefix} pack_path not found: {pack_path}")
            rc = 1

        # optional manifest blocks
        policy = item.get('policy')
        if policy is not None:
            if not isinstance(policy, dict):
                print(f"[FAIL] {prefix}.policy must be object")
                rc = 1
            else:
                pri = policy.get('activation_priority')
                if pri is not None and not (isinstance(pri, int) and 0 <= pri <= 100):
                    print(f"[FAIL] {prefix}.policy.activation_priority must be int[0..100]")
                    rc = 1

        deps = item.get('dependencies')
        if deps is not None:
            if not isinstance(deps, dict):
                print(f"[FAIL] {prefix}.dependencies must be object")
                rc = 1
            else:
                tools = deps.get('tools', [])
                if tools is not None and not isinstance(tools, list):
                    print(f"[FAIL] {prefix}.dependencies.tools must be list")
                    rc = 1

    if not has_default:
        print(f"[FAIL] default_identity {catalog['default_identity']} is not present in identities")
        rc = 1

    if rc == 0:
        print("[OK] identity manifest semantic validation passed")
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
