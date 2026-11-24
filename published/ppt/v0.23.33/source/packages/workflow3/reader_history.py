"""Explicit fresh physical context, anchored to an immutable first reading.

Local host-call observations are not signed context isolation attestations.
Professional verdicts, repair rules and first-reading immutability are unchanged.
"""
from pathlib import Path
from . import io

CONTRACT = 'io.clayz.presentation.frozen-reader-lineage/1'
MODE = 'fresh-context-frozen-reader-lineage'


def local_ref(case, value):
    if not isinstance(value, dict) or set(value) != {'path', 'bytes', 'sha256'}:
        raise ValueError('exact_absolute_lineage_file_reference_required')
    path = Path(value['path']).resolve(strict=True)
    path.relative_to(case)
    raw = path.read_bytes()
    if len(raw) != value['bytes'] or io.digest(raw) != value['sha256']:
        raise ValueError('lineage_file_identity_changed')
    return path


def validate(root, context, first, packet, packet_path):
    root = Path(root).resolve(); case = root.parent
    lineage = io.read(local_ref(case, context.get('history_continuity')))
    if lineage.get('contract') != CONTRACT or context.get('execution_mode') != MODE:
        raise ValueError('explicit_frozen_reader_lineage_mode_required')
    if (lineage.get('case_root'), lineage.get('run_id'), lineage.get('role'), lineage.get('phase')) != (
            str(case), packet['run_id'], packet['role'], packet['phase']):
        raise ValueError('lineage_case_run_role_phase_mismatch')
    if packet['phase'] == 'first' or lineage.get('no_first_resampling') is not True:
        raise ValueError('lineage_cannot_replace_an_independent_first_reading')
    new = context['context_id']
    if lineage.get('new_context_id') != new or new == first['context_id']:
        raise ValueError('truthful_distinct_physical_context_id_required')
    if lineage.get('frozen_first_context_id') != first['context_id']:
        raise ValueError('original_frozen_reader_identity_changed')
    if (lineage.get('frozen_first_packet_sha256'), lineage.get('frozen_first_source_sha256')) != (
            first['packet']['sha256'], first['source_sha256']):
        raise ValueError('original_frozen_packet_identity_changed')
    first_path = local_ref(case, lineage['frozen_first_response'])
    if first_path.read_bytes() != io.resolve(root, first['response']).read_bytes():
        raise ValueError('full_original_first_response_must_be_preserved')
    coverage = io.read(local_ref(case, lineage['own_coverage']))
    if (coverage.get('context_id'), coverage.get('run_id'), coverage.get('role'), coverage.get('phase'),
        coverage.get('packet_sha256'), coverage.get('source_sha256')) != (
            first['context_id'], packet['run_id'], packet['role'], 'first',
            first['packet']['sha256'], first['source_sha256']):
        raise ValueError('original_own_coverage_identity_changed')
    if local_ref(case, lineage['current_packet']).read_bytes() != Path(packet_path).read_bytes():
        raise ValueError('lineage_current_packet_mismatch')
    if lineage.get('fork_turns') != 'none' or not lineage.get('user_instruction'):
        raise ValueError('fresh_noninheriting_lineage_authority_required')
    observed = io.read(local_ref(case, context['observed_dispatch']))
    if (observed.get('tool'), observed.get('target'), observed.get('fork_turns')) != (
            'collaboration.spawn_agent', new, 'none'):
        raise ValueError('actual_fresh_spawn_observation_required')
    if Path(observed['host_receipt']).resolve() != Path(context['host_receipt']).resolve():
        raise ValueError('observed_host_receipt_mismatch')
    receipt = io.read(Path(context['host_receipt']))
    if receipt.get('task_name') != new:
        raise ValueError('actual_returned_context_mismatch')
    scope = io.read(local_ref(case, context['dispatch_scope']))
    if scope.get('actor_role') != packet['role'] or scope.get('packet') != lineage['current_packet']:
        raise ValueError('actual_dispatch_packet_or_role_mismatch')
    # No image bytes belong in the small lineage/checkpoint document.
    from ..history_lifecycle import no_inline_images
    no_inline_images(lineage)
    return lineage
