# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""External authored references and observable Art decisions, never aesthetic scores."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

FLOWS = {f'A{i:02d}' for i in range(1, 12)}

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def text(value):
    return isinstance(value, str) and bool(value.strip())

def load_pack(path):
    root = Path(path).resolve()
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('contract') != 'io.clayz.presentation.art-learning-pack/1.0':
        raise ValueError('unsupported Art learning manifest')
    if not all(text(manifest.get(k)) for k in ('package_id', 'version', 'nodes', 'sources')):
        raise ValueError('learning package identity and entry files required')
    files = manifest.get('files', {})
    if not files or any(manifest[k] not in files for k in ('nodes', 'sources')):
        raise ValueError('learning entry files must be hash-bound')
    for name, sha in files.items():
        file = root / name
        if not file.resolve().is_relative_to(root) or file.is_symlink() or not file.is_file():
            raise ValueError('unsafe or missing learning file: ' + name)
        if hashlib.sha256(file.read_bytes()).hexdigest() != sha:
            raise ValueError('learning file hash mismatch: ' + name)
    nodes = json.loads((root / manifest['nodes']).read_text(encoding='utf-8'))['nodes']
    sources = json.loads((root / manifest['sources']).read_text(encoding='utf-8'))['sources']
    ids = {s['source_id'] for s in sources}
    codes = [n['code'] for n in nodes]
    if len(codes) != len(set(codes)) or not FLOWS <= set(codes):
        raise ValueError('learning codes must be unique and cover A01—A11')
    for node in nodes:
        if not all(text(node.get(k)) for k in ('code', 'title', 'principle')):
            raise ValueError('every code, including categories/actions, needs a principle')
        if node.get('parent') is not None and node['parent'] not in codes:
            raise ValueError('unknown parent code')
        if any(c not in codes for k in ('knowledge_codes', 'operation_codes') for c in node.get(k, [])):
            raise ValueError('unknown learning reference')
        if not set(node.get('source_ids', [])) <= ids or not set(node.get('flow_ids', [])) <= FLOWS:
            raise ValueError('unknown curriculum/flow reference')
        if node.get('kind') == 'PRINCIPLE' and (not node.get('actions') or not text(node.get('limits'))):
            raise ValueError('principle leaves need actionable operations and limitations')
    by_code = {n['code']: n for n in nodes}
    for code in codes:
        seen = set()
        while code is not None:
            if code in seen:
                raise ValueError('cycle in learning code tree')
            seen.add(code)
            code = by_code[code].get('parent')
    return manifest, by_code

def lookup(path, code):
    manifest, nodes = load_pack(path)
    if code not in nodes:
        raise ValueError('unknown Art learning code: ' + code)
    selected = [code, *nodes[code].get('knowledge_codes', [])]
    values = [nodes[c] for c in dict.fromkeys(selected)]
    return {'package_id': manifest['package_id'], 'version': manifest['version'],
            'manifest_sha256': digest(manifest), 'nodes_sha256': manifest['files'][manifest['nodes']],
            'requested_code': code, 'nodes': values, 'selection_sha256': digest(values)}

def validate_cognition(value):
    """Portable snapshots preserve consulted text, without claiming proof of thought."""
    errors = []
    if not isinstance(value, dict) or value.get('contract') != 'io.clayz.presentation.art-cognition/1.0':
        return ['art_cognition: supported decision record required']
    steps = value.get('steps')
    if not isinstance(steps, list) or not all(isinstance(s, dict) for s in steps):
        return ['art_cognition.steps: conclusions and actions required']
    codes = [s.get('flow_code') for s in steps]
    if not FLOWS <= set(codes) or not set(codes) <= FLOWS:
        errors.append('art_cognition: cover A01—A11; steps can recur for different page scopes')
    for step in steps:
        if not all(text(step.get(k)) for k in ('scope', 'conclusion', 'check_or_uncertainty')):
            errors.append('art_cognition: each step needs scope, concrete conclusion and check/uncertainty')
        if not isinstance(step.get('actions'), list) or not step['actions'] or not all(text(a) for a in step['actions']):
            errors.append('art_cognition: each conclusion must lead to actions')
        refs = step.get('knowledge_refs')
        if not isinstance(refs, list):
            errors.append('art_cognition: knowledge_refs array required')
            continue
        if not refs and not text(step.get('knowledge_not_used_reason')):
            errors.append('art_cognition: disclose why no external reference was used')
        for ref in refs:
            if not isinstance(ref, dict) or not text(ref.get('how_applied')):
                errors.append('art_cognition: explain the material effect of each reference')
                continue
            receipt = ref.get('receipt', {})
            nodes = receipt.get('nodes', [])
            if (not nodes or receipt.get('selection_sha256') != digest(nodes)
                    or not all(text(receipt.get(k)) for k in ('package_id', 'version', 'manifest_sha256', 'nodes_sha256'))
                    or ref.get('code') not in {n.get('code') for n in nodes}
                    or any(not text(n.get('principle')) for n in nodes)):
                errors.append('art_cognition: exact consulted nodes and receipt required')
    return errors

def verify_cognition_sources(value, pack_paths):
    """At recording time, reopen selected packages instead of trusting claimed hits."""
    errors = validate_cognition(value)
    if errors:
        return errors
    available = {}
    for path in pack_paths:
        manifest, _ = load_pack(path)
        available[(manifest['package_id'], manifest['version'], digest(manifest))] = path
    for step in value['steps']:
        for ref in step['knowledge_refs']:
            receipt = ref['receipt']
            path = available.get(tuple(receipt[k] for k in ('package_id', 'version', 'manifest_sha256')))
            if path is None:
                errors.append('art_cognition: pass the actually consulted --learning-pack for each receipt')
            elif lookup(path, receipt.get('requested_code')) != receipt:
                errors.append('art_cognition: consulted receipt differs from actual package bytes')
    return errors
