#!/usr/bin/env python3
"""Verify actual prior-round source changes and their byte-identical inheritance."""
import argparse
import hashlib
import json
from pathlib import Path


def file_ref(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def tree(root):
    root = Path(root).resolve()
    result = {}
    for path in sorted(root.rglob('*')):
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            raise ValueError('Source snapshots must not contain symlinks')
        if path.is_file():
            result[str(path.relative_to(root))] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'bytes': path.stat().st_size}
    if not result:
        raise ValueError('Source snapshot is empty')
    return result


def changed(before, after):
    return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))


def verify_upgrade(path, expected_round, cloned_skill=None, cloned_knowledge=None):
    path = Path(path)
    record = json.loads(path.read_text())
    if record.get('schema') != 'recursive-iteration-upgrade/1.0':
        raise ValueError('Unsupported iteration-upgrade record')
    if record.get('source_round') != expected_round:
        raise ValueError('Upgrade is not from the immediate preceding company')
    if record.get('status') != 'locally-validated-development-source':
        raise ValueError('Upgrade has not completed local source verification')
    for component in ['skill', 'knowledge-pack']:
        before, after = (record[k][component] for k in ['baseline', 'optimized'])
        if tree(before['root']) != before['files'] or tree(after['root']) != after['files']:
            raise ValueError('Frozen ' + component + ' snapshot changed')
        differences = changed(before['files'], after['files'])
        if not differences or differences != record['changes'][component]:
            raise ValueError('No actual or incorrectly recorded ' + component + ' improvement')
    for name, value in record['baseline']['skill']['files'].items():
        if name.startswith('packages/validators/'):
            if record['optimized']['skill']['files'].get(name) != value:
                raise ValueError('Existing validators must remain unchanged')
    for evidence in record['validation_evidence'].values():
        if file_ref(evidence['path']) != evidence:
            raise ValueError('Upgrade validation evidence changed')
    if (cloned_skill is None) != (cloned_knowledge is None):
        raise ValueError('Verify both inherited components together')
    if cloned_skill is not None:
        for component, root in [('skill', cloned_skill), ('knowledge-pack', cloned_knowledge)]:
            if tree(root) != record['optimized'][component]['files']:
                raise ValueError('Next company did not inherit optimized ' + component + ' bytes')
    return {'verified': True, 'source_round': expected_round, 'upgrade': file_ref(path),
            'optimized_skill': record['optimized']['skill']['root'],
            'optimized_knowledge': record['optimized']['knowledge-pack']['root'],
            'inherited_bytes_checked': cloned_skill is not None,
            'scope': 'Source changes and byte inheritance only; no claim of improved audience understanding.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--expected-round', type=int, required=True)
    parser.add_argument('--clone-skill', type=Path)
    parser.add_argument('--clone-knowledge', type=Path)
    args = parser.parse_args()
    try:
        result = verify_upgrade(args.record, args.expected_round,
                                args.clone_skill, args.clone_knowledge)
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({'verified': False, 'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
