#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate an external Art learning pack or read exact codes; no automatic admission."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.validators.art_learning import load_pack, lookup, validate_cognition, verify_cognition_sources

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'lookup', 'validate-cognition', 'diff'])
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--code')
    parser.add_argument('--record', type=Path)
    parser.add_argument('--package', type=Path)
    parser.add_argument('--presentation', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'diff':
            if args.package is None or args.presentation is None:
                raise ValueError('--package and --presentation required')
            from packages.validators.art_content import differences
            from packages.validators.art_learning import digest
            package = json.loads(args.package.read_text(encoding='utf-8'))
            slides = json.loads(args.presentation.read_text(encoding='utf-8'))
            result = {'contract': 'io.clayz.presentation.art-content/1.0', 'copy_package_sha256': digest(package),
                      'slides': slides, 'changes': differences(package, slides)}
        elif args.command == 'validate-cognition':
            if args.record is None:
                raise ValueError('--record required')
            value = json.loads(args.record.read_text(encoding='utf-8'))
            errors = verify_cognition_sources(value, [args.pack]) if args.pack else validate_cognition(value)
            if errors:
                raise ValueError('; '.join(errors))
            result = {'valid': True, 'scope': 'record integrity, not aesthetic quality'}
        else:
            if args.pack is None:
                raise ValueError('--pack required; no bundled or fabricated lookup')
            if args.command == 'lookup':
                result = lookup(args.pack, args.code)
            else:
                manifest, nodes = load_pack(args.pack)
                result = {'valid': True, 'package_id': manifest['package_id'], 'version': manifest['version'], 'codes': len(nodes)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}, ensure_ascii=False))
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
