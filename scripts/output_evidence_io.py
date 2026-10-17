"""Preserve revision evidence and propagate original verification states.

Transport/assertion helper only: no presentation threshold or original validator
is replaced. Call with the process return code and that run's actual JSON result.
"""
import hashlib
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


def derive_render_manifest(raw_manifest_path, pptx_path, *, evidence_role,
                           provenance_clarification):
    """Bind an existing render to its actual PPTX without rendering or promotion.

    The caller explicitly describes the evidence role and actual execution;
    this function cannot infer that an Art preview is formal Output. Preserve
    the raw manifest, its limitations, page order, PDF and image references.
    The returned copy adds the canonical PPTX hash required by existing final
    readers. Use write_new_json separately to retain revision history.
    Identity consistency is transport evidence, never a quality or GUI claim.
    """
    if not isinstance(evidence_role, str) or not evidence_role.strip():
        raise ValueError('An explicit actual evidence role is required')
    if (not isinstance(provenance_clarification, str)
            or not provenance_clarification.strip()):
        raise ValueError('Describe the actual render provenance and limits')
    raw_path = Path(raw_manifest_path).resolve()
    pptx_path = Path(pptx_path).resolve()
    raw_bytes = raw_path.read_bytes()
    manifest = json.loads(raw_bytes)
    pptx_bytes = pptx_path.read_bytes()
    actual_hash = hashlib.sha256(pptx_bytes).hexdigest()
    bound = manifest.get('pptx') if isinstance(manifest, dict) else None
    if (not isinstance(bound, dict) or bound.get('sha256') != actual_hash
            or bound.get('bytes') != len(pptx_bytes)):
        raise ValueError('Raw render does not bind the actual supplied PPTX')
    if manifest.get('pptx_sha256', actual_hash) != actual_hash:
        raise ValueError('Raw canonical PPTX hash conflicts with its bound input')
    manifest.update(
        pptx_sha256=actual_hash,
        raw_manifest=dict(path=str(raw_path),
                          sha256=hashlib.sha256(raw_bytes).hexdigest(),
                          bytes=len(raw_bytes)),
        evidence_role=evidence_role,
        provenance_clarification=provenance_clarification)
    return manifest


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
