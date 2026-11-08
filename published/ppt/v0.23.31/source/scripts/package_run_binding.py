"""Carry an already issued run binding into authored packages; never issue one.

This producer helper checks transport identity only. Original preflight, package,
reader and record validation remain required. It does not attest host readiness.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path


def with_run_binding(package, preflight_path, challenge_path, *, upstream=None):
    """Return a copy; reject conflicting bindings instead of silently rebinding."""
    preflight = json.loads(Path(preflight_path).read_text(encoding='utf-8'))
    challenge_raw = Path(challenge_path).read_bytes()
    challenge = json.loads(challenge_raw)
    binding = preflight['run_binding']
    for key in ('run_id', 'task_request_sha256', 'nonce', 'task_root_sha256'):
        if not binding.get(key) or binding[key] != challenge.get(key):
            raise ValueError('Preflight/challenge binding mismatch: ' + key)
    if binding.get('challenge_sha256') != sha256(challenge_raw).hexdigest():
        raise ValueError('Challenge bytes do not match preflight binding')
    if binding.get('binding_source') != 'script-issued-challenge':
        raise ValueError('An existing script-issued binding is required')
    for key in ('issuance_receipt', 'consumption_receipt'):
        receipt = Path(binding[key])
        if sha256(receipt.read_bytes()).hexdigest() != binding.get(key + '_sha256'):
            raise ValueError('Receipt bytes do not match: ' + key)
    if upstream is not None and upstream.get('run_binding') != binding:
        raise ValueError('Upstream package binding differs or is missing')
    if 'run_binding' in package and package['run_binding'] != binding:
        raise ValueError('Refusing to replace a different package binding')
    result = deepcopy(package)
    result['run_binding'] = deepcopy(binding)
    return result
