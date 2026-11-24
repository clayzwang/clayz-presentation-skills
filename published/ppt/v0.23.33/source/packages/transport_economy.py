"""Lossless image transport and case-bound context accounting.

No model judgment, reader verdict, renderer, Office, or network code lives here.
Receipts are caller observations, not signed host or VPN byte attestations.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import uuid
import importlib.util

_history_spec = importlib.util.spec_from_file_location(
    'presentation_history_lifecycle', Path(__file__).with_name('history_lifecycle.py'))
history_lifecycle = importlib.util.module_from_spec(_history_spec)
_history_spec.loader.exec_module(history_lifecycle)


def now():
    return datetime.now(timezone.utc).isoformat()


def ref(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def verify(value):
    if ref(value['path']) != {k: value[k] for k in ('path', 'bytes', 'sha256')}:
        raise ValueError('referenced_bytes_changed')
    return Path(value['path'])


def within(path, case):
    path = Path(path).resolve()
    path.relative_to(Path(case).resolve(strict=True))
    return path


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def command_summary(stdout, stderr, returncode):
    """Keep raw command evidence locally; do not replay embedded company bodies."""
    result = dict(returncode=returncode, stdout_bytes=len(stdout), stderr_bytes=len(stderr),
                  stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                  stderr_sha256=hashlib.sha256(stderr).hexdigest())
    text = stdout.decode('utf-8', errors='replace')
    for line in text.splitlines():
        if line.startswith('NATIVE_RECEIPT='):
            result['native_receipt'] = line.partition('=')[2]
    try:
        value, _ = json.JSONDecoder().raw_decode(text.lstrip())
        if isinstance(value, dict):
            for key in ('kind','sequence','record_sha256','run_id','session_id','status'):
                item = value.get(key)
                if type(item) in (str,int,bool) and len(str(item)) <= 256:
                    result[key] = item
            payload = value.get('payload', {})
            if isinstance(payload, dict):
                fields = {}
                for key in ('role','stage','verdict','disposition','owner','number','outcome'):
                    item = payload.get(key)
                    if type(item) in (str,int,bool) and len(str(item)) <= 256:
                        fields[key] = item
                if fields:
                    result['native_payload'] = fields
    except (ValueError,TypeError):
        pass
    if returncode:
        result['diagnostic_tail'] = stderr.decode('utf-8',errors='replace')[-1200:]
    return result


def validate_scope(case, packet, prompt=None):
    """Check actual packet references, not just the spelling of an actor name."""
    case = Path(case).resolve(strict=True)
    payload = json.loads(within(packet, case).read_text())
    metadata = case / 'initialized.json'
    if not metadata.exists():
        candidates = [p for p in (case/'run/run.json', case/'run.json') if p.is_file()]
        if len(candidates) != 1:
            raise ValueError('one_existing_native_task_binding_required')
        metadata = candidates[0]
    binding = json.loads(metadata.read_text())
    if not isinstance(binding.get('run_id'), str) or not binding['run_id']:
        raise ValueError('existing_native_run_identity_required')
    if payload.get('run_id') not in (None, binding['run_id']):
        raise ValueError('foreign_run_packet')
    shared = set()
    if case.parent.name == 'rounds':
        batch = case.parent.parent
        for stage in ('logic','copy','art','output'):
            shared.add(batch / 'goals' / (stage+'.json'))
        selection = batch / 'protocol/current-goal-selection.json'
        if selection.exists():
            selected = json.loads(selection.read_text())
            for value in selected.get('files', {}).values():
                path = batch / value['path']
                path.relative_to(batch / 'goals-revisions')
                shared.add(path)
        shared.add(batch / 'config/art-selection-reading-guidance-v2.json')

    def walk(value):
        if isinstance(value, dict):
            if {'path', 'sha256'} <= set(value):
                # original_path is provenance only and never grants read access.
                source = Path(value['path']).resolve(strict=True)
                if source not in shared:
                    within(source, case)
                actual = ref(source)
                if actual['sha256'] != value['sha256'] or ('bytes' in value and actual['bytes'] != value['bytes']):
                    raise ValueError('referenced_bytes_changed')
            for key, item in value.items():
                if key not in {'original_path', 'canonical_rules_origin'}:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(payload)
    if prompt:
        text = within(prompt, case).read_text()
        for number in re.findall(r'rounds/(R\d{2})(?:/|\b)', text):
            if number != case.name:
                raise ValueError('foreign_round_prompt_path')
    return payload, binding


class Economy:
    def __init__(self, registry):
        self.registry = Path(registry)
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS contexts (
              id TEXT PRIMARY KEY, case_root TEXT NOT NULL, run_id TEXT NOT NULL,
              role TEXT NOT NULL, mode TEXT NOT NULL, created_at TEXT NOT NULL,
              provenance TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS images (
              id TEXT PRIMARY KEY, context_id TEXT NOT NULL, case_root TEXT NOT NULL,
              plan_path TEXT NOT NULL, page_id TEXT NOT NULL, pixel_sha TEXT NOT NULL,
              item TEXT NOT NULL, action TEXT NOT NULL, previous_id TEXT,
              observation TEXT, coverage TEXT, created_at TEXT NOT NULL);
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.registry), timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def context(self, context_id, case, run_id, role, *, mode, fork_turns=None,
                provenance='caller-observed-dispatch'):
        case = str(Path(case).resolve(strict=True))
        if not context_id or mode not in {'fresh', 'continue', 'legacy-observed'}:
            raise ValueError('invalid_context_mode')
        if mode == 'fresh' and fork_turns != 'none':
            raise ValueError('fresh_context_must_not_inherit_history')
        with self.connection() as db:
            history_lifecycle.schema(db)
            previous = db.execute('SELECT * FROM contexts WHERE id=?', (context_id,)).fetchone()
            if previous:
                if (previous['case_root'], previous['run_id'], previous['role']) != (case, run_id, role):
                    raise ValueError('context_cannot_cross_case_run_or_role')
                if mode == 'fresh':
                    raise ValueError('fresh_context_id_already_used')
                if mode == 'continue':
                    history_lifecycle.require_text_only_continuation(db, context_id)
                return dict(previous)
            if mode == 'continue':
                raise ValueError('unknown_original_context')
            db.execute('INSERT INTO contexts VALUES (?,?,?,?,?,?,?)',
                       (context_id, case, run_id, role, mode, now(), provenance))
        return dict(context_id=context_id, case_root=case, run_id=run_id, role=role,
                    mode=mode, fork_turns=fork_turns,
                    limitation='Dispatch binding only; not an OS sandbox or signed model isolation proof.')

    def require_context(self, context_id, case, run_id):
        with self.connection() as db:
            row = db.execute('SELECT * FROM contexts WHERE id=?', (context_id,)).fetchone()
        if not row or (row['case_root'], row['run_id']) != (str(Path(case).resolve()), run_id):
            raise ValueError('unregistered_or_foreign_context')
        return dict(row)

    def prepare(self, *, case, packet, context_id, output, reread_reason=None):
        from PIL import Image, features
        payload, binding = validate_scope(case, packet)
        self.require_context(context_id, case, binding['run_id'])
        with self.connection() as db:
            history_lifecycle.require_active(db, context_id)
        output = within(output, case)
        if output.exists():
            raise FileExistsError(output)
        pages = payload.get('files', {}).get('pages')
        if pages is None:
            pages = payload.get('content_files', {}).get('page_images', [])
        if not isinstance(pages, list):
            raise ValueError('image_page_list_required')
        cache = Path(case) / 'transport/images'
        cache.mkdir(parents=True, exist_ok=True)
        items = []
        for page in pages:
            source = within(page['path'], case)
            actual = ref(source)
            if actual['sha256'] != page['sha256'] or ('bytes' in page and actual['bytes'] != page['bytes']):
                raise ValueError('image_source_changed')
            with Image.open(source) as opened:
                if getattr(opened, 'n_frames', 1) != 1:
                    raise ValueError('animated_source_requires_explicit_route')
                im = opened.convert('RGBA')
                eligible = opened.mode in {'RGB','RGBA'} and not any(opened.info.get(k) for k in ('icc_profile','exif'))
            pixel_sha = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest() if eligible else actual['sha256']
            encoded = io.BytesIO()
            if eligible and features.check('webp'):
                im.save(encoded, format='WEBP', lossless=True, exact=True, method=6)
                with Image.open(io.BytesIO(encoded.getvalue())) as decoded:
                    if decoded.convert('RGBA').tobytes() != im.tobytes() or decoded.size != im.size:
                        raise ValueError('lossless_pixel_verification_failed')
            with Image.open(source) as original:
                mime = Image.MIME.get(original.format, 'image/png')
            selected = source
            if encoded.tell() and encoded.tell() < source.stat().st_size:
                selected, mime = cache / (pixel_sha + '.webp'), 'image/webp'
                if not selected.exists():
                    with selected.open('xb') as target:
                        target.write(encoded.getvalue())
                if selected.read_bytes() != encoded.getvalue():
                    raise ValueError('cached_encoding_changed')
            with self.connection() as db:
                old = db.execute('SELECT * FROM images WHERE context_id=? AND pixel_sha=? '
                                 'AND action IN ("send","legacy-observed") AND observation IS NOT NULL AND coverage IS NOT NULL '
                                 'ORDER BY created_at DESC LIMIT 1', (context_id, pixel_sha)).fetchone()
            previous = None
            if old and not reread_reason:
                # Reuse only this reader's completed observation, never another reader's answer.
                coverage = json.loads(old['coverage'])
                verify(coverage)
                previous = dict(entry_id=old['id'], own_coverage=coverage,
                                own_observation=json.loads(old['observation']))
            item = dict(id=uuid.uuid4().hex, page_id=page['slide_id'], source=ref(source),
                        selected=ref(selected), mime=mime, dimensions=list(im.size),
                        pixel_sha256=pixel_sha, pixel_identity_verified=True,
                        host_detail='original' if max(im.size)>2048 else 'high',
                        encoding_scope='verified-8bit-RGBA-lossless' if eligible else 'original-bytes-preserved-no-color-or-bit-depth-conversion',
                        action='reuse-own-evidence' if previous else 'send',
                        previous=previous, reread_reason=reread_reason,
                        original_base64_data_url_chars=22 + 4 * ((source.stat().st_size + 2) // 3))
            items.append(item)
        plan = dict(schema='io.clayz.presentation.transport-plan/1', created_at=now(),
                    case_root=str(Path(case).resolve()), run_id=binding['run_id'],
                    context_id=context_id, packet=ref(packet), items=items,
                    quality_policy='Same dimensions and every decoded RGBA pixel preserved. '
                                   'No scale-down, text deletion, visual verdict, or new reader exemption.',
                    tool_image_handling='Use view_image(high) on selected.path; if WebP is returned '
                                        'as application/octet-stream, change the data URL MIME to image/webp '
                                        'without changing its base64 bytes. Forward once and record actual URL length.',
                    measurement_scope='Prepared file sizes are not VPN bytes. Record actual forwarded '
                                      'data URL length separately; only completed own observations permit reuse.')
        write_new(output, plan)
        with self.connection() as db:
            for item in items:
                db.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           (item['id'], context_id, plan['case_root'], str(output), item['page_id'],
                            item['pixel_sha256'], json.dumps(item), item['action'],
                            item['previous']['entry_id'] if item['previous'] else None,
                            None, None, now()))
        return plan

    def adopt(self, *, case, packet, context_id, coverage):
        """Preserve real pre-mechanism readings without inventing payload lengths."""
        from PIL import Image
        payload, binding = validate_scope(case, packet)
        context = self.require_context(context_id, case, binding['run_id'])
        coverage_ref = ref(within(coverage, case))
        evidence = json.loads(Path(coverage).read_text())
        for key in ('run_id', 'packet_id', 'source_sha256', 'role'):
            if evidence.get(key) != payload.get(key):
                raise ValueError('legacy_coverage_packet_identity_mismatch')
        if payload.get('role') != context['role']:
            raise ValueError('legacy_coverage_not_this_original_role')
        declared = {p.get('slide_id'): p for p in evidence.get('pages', [])}
        inserted = 0
        for page in payload.get('files', {}).get('pages', []):
            previous = declared.get(page['slide_id'], {})
            if (previous.get('actual_view') is not True or previous.get('sha256') != page['sha256']
                    or not previous.get('observation')):
                raise ValueError('legacy_read_must_be_explicit_and_hash_bound')
            source = verify(page)
            with Image.open(source) as opened:
                im = opened.convert('RGBA'); mime = Image.MIME.get(opened.format, 'image/png')
                eligible = opened.mode in {'RGB','RGBA'} and not any(opened.info.get(k) for k in ('icc_profile','exif'))
            pixel_sha = hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest() if eligible else ref(source)['sha256']
            item = dict(source=ref(source), selected=ref(source), mime=mime,
                        dimensions=list(im.size), pixel_sha256=pixel_sha,
                        original_base64_data_url_chars=22+4*((source.stat().st_size+2)//3))
            observed = dict(recorded_at=now(), observation=previous['observation'],
                            actual_forwarded_data_url_chars=None, reuse_of_own_evidence=False,
                            legacy_before_measurement=True,
                            scope='Original reader declared actual earlier viewing; length not observed. '
                                  'Do not count this migration as a new view or bandwidth saving.')
            with self.connection() as db:
                exists = db.execute('SELECT id FROM images WHERE context_id=? AND pixel_sha=? AND action=? '
                                    'AND coverage=?', (context_id,pixel_sha,'legacy-observed',json.dumps(coverage_ref))).fetchone()
                if exists: raise ValueError('legacy_coverage_already_adopted')
                db.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           (uuid.uuid4().hex,context_id,str(Path(case).resolve()),str(Path(packet).resolve()),
                            page['slide_id'],pixel_sha,json.dumps(item),'legacy-observed',None,
                            json.dumps(observed),json.dumps(coverage_ref),now()))
            inserted += 1
        return dict(adopted_prior_own_pages=inserted, actual_new_image_forwards=0,
                    prior_payload_length_observed=False, coverage=coverage_ref)

    def observe(self, *, entry_id, context_id, actual_data_url_chars=None, mime=None,
                observation, reuse=False):
        if not observation.strip():
            raise ValueError('actual_observation_required')
        with self.connection() as db:
            row = db.execute('SELECT * FROM images WHERE id=? AND context_id=?',
                             (entry_id, context_id)).fetchone()
            if not row or row['observation']:
                raise ValueError('unknown_or_already_recorded_image')
            item = json.loads(row['item'])
            verify(item['source']); verify(item['selected'])
            if reuse:
                if row['action'] != 'reuse-own-evidence' or actual_data_url_chars is not None:
                    raise ValueError('reuse_requires_prior_own_evidence_and_no_new_upload')
                verify(item['previous']['own_coverage'])
            elif (row['action'] != 'send' or type(actual_data_url_chars) is not int
                  or actual_data_url_chars < 32 or mime not in {'image/png', 'image/jpeg', 'image/webp'}):
                raise ValueError('actual_forwarded_image_metadata_required')
            value = dict(recorded_at=now(), observation=observation,
                         actual_forwarded_data_url_chars=0 if reuse else actual_data_url_chars,
                         mime=None if reuse else mime, reuse_of_own_evidence=reuse,
                         scope='Caller-observed forward or evidence reuse; not signed host/VPN attestation.')
            db.execute('UPDATE images SET observation=? WHERE id=?', (json.dumps(value), entry_id))
        return value

    def complete(self, *, plan_path, context_id, coverage):
        plan = json.loads(Path(plan_path).read_text())
        if plan['context_id'] != context_id:
            raise ValueError('wrong_original_reader')
        coverage_ref = ref(within(coverage, plan['case_root']))
        with self.connection() as db:
            rows = db.execute('SELECT * FROM images WHERE plan_path=? AND context_id=?',
                              (str(Path(plan_path).resolve()), context_id)).fetchall()
            if len(rows) != len(plan['items']) or any(not row['observation'] for row in rows):
                raise ValueError('unread_images_cannot_be_completed')
            for row in rows:
                if row['coverage']:
                    raise ValueError('read_completion_already_bound')
                db.execute('UPDATE images SET coverage=? WHERE id=?', (json.dumps(coverage_ref), row['id']))
            if rows:
                history_lifecycle.retire(db, context_id, coverage_ref,
                    'Image inspection complete: preserve evidence, finish current response and never follow up this physical context.', now())
        return coverage_ref

    def report(self, case=None):
        with self.connection() as db:
            rows = db.execute('SELECT * FROM images' + (' WHERE case_root=?' if case else ''),
                              (str(Path(case).resolve()),) if case else ()).fetchall()
        original, prepared, forwarded, observed_baseline, views, reuse, legacy = 0, 0, 0, 0, 0, 0, 0
        for row in rows:
            if row['action'] == 'legacy-observed':
                legacy += 1
                continue
            item = json.loads(row['item'])
            original += item['source']['bytes']
            prepared += item['selected']['bytes']
            if row['observation']:
                event = json.loads(row['observation'])
                observed_baseline += item['original_base64_data_url_chars']
                forwarded += event['actual_forwarded_data_url_chars']
                reuse += int(event['reuse_of_own_evidence'])
                views += int(not event['reuse_of_own_evidence'])
        return dict(schema='io.clayz.presentation.transport-metrics/1', recorded_at=now(),
                    planned_image_occurrences=len(rows)-legacy, prepared_source_bytes=original,
                    prepared_selected_bytes=prepared, prepared_file_bytes_reduced=original-prepared,
                    actual_observed_image_forwards=views, actual_own_evidence_reuses=reuse,
                    legacy_own_pages_adopted_without_new_transfer=legacy,
                    actual_forwarded_image_data_url_chars=forwarded,
                    png_data_url_counterfactual_for_observed_actions=observed_baseline,
                    observed_input_chars_reduced_vs_png_counterfactual=observed_baseline-forwarded,
                    vpn_actual_bytes=None, vpn_bytes_saved=None,
                    caveat='Image input character accounting only, not model tokens or measured VPN. '
                           'No savings are credited for merely planned, unviewed images. '
                           'Host framing, compression, history replay and unrelated traffic are unobserved.')
