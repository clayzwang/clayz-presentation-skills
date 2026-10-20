#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate an external Art learning pack or read exact codes; no automatic admission."""
import argparse
from copy import deepcopy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.validators.art_learning import load_pack, lookup, validate_cognition, verify_cognition_sources


def copy_source_context(package, slides):
    """Expand explicit Copy-unit references without treating page slots as lineage.

    Optional read-only authoring context, not an Art-content validator. References
    express the author's claim of use; resolved text does not establish faithful
    paraphrase, complete coverage, current visual grouping or reader acceptance.
    """
    from packages.validators.art_learning import digest

    def identifier(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('nonempty string identity required')
        return value

    def unique_pages(pages):
        if not isinstance(pages, list):
            raise ValueError('slides array required')
        page_ids, unit_ids = set(), set()
        for page in pages:
            sid = identifier(page['slide_id'])
            if sid in page_ids:
                raise ValueError('duplicate slide identity: ' + sid)
            page_ids.add(sid)
            if not isinstance(page['copy_units'], list):
                raise ValueError('copy_units array required')
            for unit in page['copy_units']:
                uid = identifier(unit['copy_id'])
                if uid in unit_ids:
                    raise ValueError('ambiguous duplicate Copy-unit identity: ' + uid)
                unit_ids.add(uid)
        return page_ids

    original = package['copy_layer']['slides']
    original_pages = unique_pages(original)
    unique_pages(slides)
    sources = {u['copy_id']: {'slide_id': p['slide_id'], 'copy_unit': u}
               for p in original for u in p['copy_units']}
    pages = []
    for page in slides:
        basis = page.get('source_basis', [])
        if not isinstance(basis, list):
            raise ValueError('source_basis must be an array when supplied')
        by_id = {}
        for row in basis:
            uid = identifier(row['copy_id'])
            if uid in by_id:
                raise ValueError('ambiguous duplicate source_basis: ' + uid)
            for key in ('source_copy_ids', 'source_data_ids'):
                refs = row.get(key, [])
                if not isinstance(refs, list):
                    raise ValueError(key + ' must be an array')
                for ref in refs:
                    identifier(ref)
            by_id[uid] = row
        units, used = [], set()
        for unit in page['copy_units']:
            uid = unit['copy_id']
            row = by_id.get(uid)
            refs = list(dict.fromkeys(row.get('source_copy_ids', []))) if row else []
            units.append({'copy_id': uid, 'current_text': unit.get('text'),
                          'basis_supplied': row is not None,
                          'declared_source_copy_ids': refs,
                          'source_units': [deepcopy(sources[r]) for r in refs if r in sources],
                          'unresolved_copy_ids': [r for r in refs if r not in sources],
                          'declared_source_data_ids': deepcopy(row.get('source_data_ids', [])) if row else [],
                          'author_basis': row.get('basis') if row else None})
            used.add(uid)
        pages.append({'slide_id': page['slide_id'],
                      'same_slot_copy_page_id': page['slide_id'] if page['slide_id'] in original_pages else None,
                      'units': units,
                      'unmatched_basis_rows': deepcopy([r for uid, r in by_id.items() if uid not in used])})
    return {'contract': 'io.clayz.presentation.copy-source-context/1.0',
            'copy_package_sha256': digest(package), 'pages': pages,
            'scope': 'Declared stable Copy references expanded only. Same-slot identity is structural, not content ancestry; missing basis and unresolved references remain explicit. Research/data IDs are declarations, not verified support. No quality or semantic verdict.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'domains', 'lookup', 'validate-cognition', 'diff', 'source-context'])
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--code')
    parser.add_argument('--record', type=Path)
    parser.add_argument('--package', type=Path)
    parser.add_argument('--presentation', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'source-context':
            if args.package is None or args.presentation is None:
                raise ValueError('--package and --presentation required')
            result = copy_source_context(json.loads(args.package.read_text(encoding='utf-8')),
                                         json.loads(args.presentation.read_text(encoding='utf-8')))
        elif args.command == 'diff':
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
            if args.command == 'domains':
                manifest, _ = load_pack(args.pack)
                entry = manifest.get('domain_map')
                if not entry:
                    result = {'available': False, 'guidance': 'No domain map in this optional pack; identify the relevant discipline from the communication problem.'}
                else:
                    # An open reading map, never a keyword classifier or gate.
                    if entry not in manifest['files']:
                        raise ValueError('domain map must be hash-bound')
                    result = json.loads((args.pack / entry).read_text(encoding='utf-8'))
            elif args.command == 'lookup':
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
