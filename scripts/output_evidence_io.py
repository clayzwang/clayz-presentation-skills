"""Preserve revision evidence and propagate original verification states.

Transport/assertion helper only: no presentation threshold or original validator
is replaced. Call with the process return code and that run's actual JSON result.
"""
import json
from pathlib import Path, PurePath


def ensure_new_paths(paths):
    """Check the complete output list before a revision invokes any tools."""
    paths = [Path(p).absolute() for p in paths]
    canonical = [p.resolve() for p in paths]
    if len(set(canonical)) != len(canonical):
        raise ValueError('Duplicate output path in this revision')
    existing = [str(p) for p in paths if p.exists() or p.is_symlink()]
    if existing:
        raise FileExistsError('Refusing existing evidence output: ' + ', '.join(existing))
    return paths


def _json_path(value):
    if isinstance(value, PurePath):
        return str(value)
    raise TypeError(f"Unsupported evidence JSON type: {type(value).__name__}")


def write_new_json(path, value):
    """Exclusive-create an author-owned receipt; never truncate history."""
    path = Path(path)
    payload = json.dumps(value, ensure_ascii=False, indent=2, default=_json_path) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)
    return path


def verification_observation(result_path, returncode):
    """Return the original statuses, including failure or tool-error states."""
    data = json.loads(Path(result_path).read_text(encoding='utf-8'))
    keys = ('execution_status', 'record_status', 'quality_status')
    if not isinstance(data, dict) or any(not isinstance(data.get(k), str) for k in keys):
        raise ValueError('Missing original verification statuses')
    if isinstance(returncode, bool) or not isinstance(returncode, int):
        raise ValueError('Actual integer process return code is required')
    return dict(result_path=str(Path(result_path).resolve()), returncode=returncode,
                **{k: data[k] for k in keys}, ok=data.get('ok'),
                errors=data.get('errors', []),
                quality_findings=data.get('quality_findings', []))


def require_verification(result_path, returncode, *, quality_status):
    """Assert the exact claim before recording it; do not manufacture pass.

    Use quality_status='pass' for successful QA, 'fail' for a valid failed QA
    handoff, or 'unverified' for a record-only tool. Error/unverified execution
    can still be preserved with verification_observation but cannot pass here.
    A legitimate quality failure may have nonzero process status; successful
    quality/record-only claims require original ok=true and returncode=0.
    """
    if quality_status not in {'pass', 'fail', 'unverified'}:
        raise ValueError('Explicit supported quality claim required')
    observation = verification_observation(result_path, returncode)
    if observation['execution_status'] != 'completed' or observation['record_status'] != 'valid':
        raise ValueError('Verification did not complete with a valid record: ' + str(observation))
    if observation['quality_status'] != quality_status:
        raise ValueError('Claim differs from original quality status: ' + str(observation))
    if quality_status in {'pass', 'unverified'} and (returncode != 0 or observation['ok'] is not True):
        raise ValueError('Successful verification requires original ok=true and zero exit: ' + str(observation))
    if quality_status == 'fail' and observation['ok'] is not False:
        raise ValueError('Failed quality must preserve original ok=false: ' + str(observation))
    return observation
