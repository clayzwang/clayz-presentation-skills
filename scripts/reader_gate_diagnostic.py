#!/usr/bin/env python3
"""Read-only evidence diagnostics; always run and retain the original Art gate.

Exit 0: original gate passed and additional references matched.
Exit 1: original gate blocked. Exit 2: invalid additional/reader evidence.
This is neither a replacement gate nor a review/calibration writer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.validators.reader_review import read, validate_review


def file_ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify_references(path):
    """Explicit role -> path/sha256/bytes mapping; never repair caller evidence."""
    value = read(path)
    if not isinstance(value, dict) or not value:
        raise ValueError('Reference file must be a nonempty role-to-reference object')
    for role, expected in value.items():
        if not isinstance(role, str) or not role or not isinstance(expected, dict):
            raise ValueError('Invalid reference role or object')
        if set(expected) != {'path', 'sha256', 'bytes'}:
            raise ValueError('Reference must contain exactly path, sha256, bytes: ' + role)
        if not isinstance(expected['path'], str) or not Path(expected['path']).is_absolute():
            raise ValueError('Reference must use an absolute path: ' + role)
        if not isinstance(expected['sha256'], str) or type(expected['bytes']) is not int:
            raise ValueError('Invalid digest/byte types: ' + role)
        observed = file_ref(expected['path'])
        if observed != expected:
            raise ValueError('Reference bytes or canonical path differ: ' + role)
    return {'file': file_ref(path), 'verified_roles': sorted(value)}


def diagnose(package, title_review, content_review, reference_files=(), config=None, reader_cycle=None):
    paths = dict(package=Path(package), title=Path(title_review), content=Path(content_review))
    result = {'diagnostic_only': True, 'gate_authority': 'scripts/reader_review.py check-art-gate',
              'inputs': {}, 'reader_observations': {}, 'reference_checks': [], 'errors': []}
    for role, path in paths.items():
        try:
            result['inputs'][role] = file_ref(path)
        except (OSError, ValueError) as exc:
            result['errors'].append({'role': role, 'error': str(exc)})
    try:
        pkg = read(paths['package'])
    except (OSError, ValueError, TypeError) as exc:
        pkg = None
        result['errors'].append({'role': 'package', 'error': str(exc)})
    from packages.validators.reader_cycle import bounded
    selected_bounded = config is not None and bounded(read(config))
    for phase in ('title', 'content'):
        try:
            value = validate_review(read(paths[phase]), current_package=None if selected_bounded else pkg)
            if value['review']['phase'] != phase:
                raise ValueError('Reader phase differs from selected input: ' + phase)
            response = value['first_read']['response']
            result['reader_observations'][phase] = {
                'record_valid': True, 'assessment': value['assessment'],
                'independence': value['independence'],
                'first_read_finding_ids': [x['finding_id'] for x in response['findings']] if response else [],
                'comparison_verdict': value['review'].get('comparison', {}).get('verdict'),
                'dispositions': [{'finding_id': x['finding_id'], 'status': x['status']}
                                 for x in value['review']['dispositions']],
                'meaning': 'Verified observations only; comparison pass does not establish original gate pass.'}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['reader_observations'][phase] = {'record_valid': False, 'error': str(exc)}
            result['errors'].append({'role': phase, 'error': str(exc)})
    for path in reference_files:
        try:
            result['reference_checks'].append(verify_references(path))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['errors'].append({'role': 'reference-file', 'path': str(path), 'error': str(exc)})
    command = [sys.executable, str(ROOT/'scripts/reader_review.py'), 'check-art-gate',
               '--package', str(paths['package']), '--title-review', str(paths['title']),
               '--content-review', str(paths['content'])]
    if config is not None: command += ['--config', str(config)]
    if reader_cycle is not None: command += ['--reader-cycle', str(reader_cycle)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    completed = subprocess.run(command, capture_output=True, text=True, env=env)
    result['original_gate'] = {'command': command, 'returncode': completed.returncode,
                               'stdout': completed.stdout, 'stderr': completed.stderr}
    # Check consumed top-level bytes again; nested refs were checked by original validators.
    for role, expected in result['inputs'].items():
        try:
            if file_ref(expected['path']) != expected:
                raise ValueError('Input changed during diagnosis')
        except (OSError, ValueError) as exc:
            result['errors'].append({'role': role, 'error': str(exc)})
    code = 2 if result['errors'] else (0 if completed.returncode == 0 else 1)
    result['exit_status'] = code
    result['status'] = 'invalid-evidence' if code == 2 else ('original-gate-passed' if code == 0 else 'original-gate-blocked')
    result['next_action'] = ('Use the original gate result and existing stage/iteration policy; '
                             'this diagnostic grants no approval and never edits source, first reading, or dispositions.')
    return result, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'title-review', 'content-review'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--reference-file', type=Path, action='append', default=[])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--reader-cycle', type=Path)
    args = parser.parse_args()
    result, code = diagnose(args.package, args.title_review, args.content_review, args.reference_file, args.config, args.reader_cycle)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
