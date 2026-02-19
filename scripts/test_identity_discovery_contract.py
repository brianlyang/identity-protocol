#!/usr/bin/env python3
"""Lightweight local discovery contract test for identity/list draft."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def main() -> int:
    root = Path('.')
    catalog_path = root / 'identity/catalog/identities.yaml'
    data = yaml.safe_load(catalog_path.read_text(encoding='utf-8')) or {}

    result = {
        'data': [
            {
                'cwd': str(root.resolve()),
                'defaultIdentity': data.get('default_identity'),
                'identities': [],
                'errors': [],
            }
        ]
    }

    for i, item in enumerate(data.get('identities', [])):
        pack_path = item.get('pack_path')
        exists = bool(pack_path) and (root / pack_path).exists()
        if not exists:
            result['data'][0]['errors'].append(
                {
                    'code': 'PACK_PATH_NOT_FOUND',
                    'path': pack_path,
                    'message': f'identities[{i}] pack path missing',
                    'severity': 'error',
                }
            )
        result['data'][0]['identities'].append(
            {
                'id': item.get('id'),
                'title': item.get('title'),
                'description': item.get('description'),
                'status': item.get('status'),
                'packPath': pack_path,
                'enabled': item.get('status') == 'active',
                'policy': {
                    'allowImplicitActivation': (item.get('policy') or {}).get('allow_implicit_activation', True),
                    'activationPriority': (item.get('policy') or {}).get('activation_priority', 50),
                    'conflictResolution': (item.get('policy') or {}).get('conflict_resolution', 'priority_then_objective'),
                },
                'dependencies': item.get('dependencies', {}),
                'interface': item.get('interface', {}),
            }
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    has_errors = any(block.get('errors') for block in result['data'])
    if has_errors:
        print('[FAIL] discovery contract test found errors')
        return 1

    print('[OK] discovery contract test passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
