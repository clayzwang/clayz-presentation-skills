"""Physical context lifecycle. This cannot delete the host's persisted history."""
import json
from pathlib import Path


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS retired_contexts (
      context_id TEXT PRIMARY KEY, checkpoint TEXT NOT NULL, reason TEXT NOT NULL,
      retired_at TEXT NOT NULL)''')


def require_active(db, context_id):
    schema(db)
    if db.execute('SELECT 1 FROM retired_contexts WHERE context_id=?', (context_id,)).fetchone():
        raise ValueError('retired_image_context_must_not_be_continued')


def require_text_only_continuation(db, context_id):
    require_active(db, context_id)
    if db.execute('SELECT 1 FROM images WHERE context_id=? AND observation IS NOT NULL LIMIT 1',
                  (context_id,)).fetchone():
        raise ValueError('image_history_requires_fresh_physical_context')


def retire(db, context_id, checkpoint, reason, retired_at):
    schema(db)
    if not reason or not isinstance(checkpoint, dict):
        raise ValueError('full_evidence_checkpoint_and_reason_required')
    previous = db.execute('SELECT * FROM retired_contexts WHERE context_id=?', (context_id,)).fetchone()
    if previous:
        return False
    db.execute('INSERT INTO retired_contexts VALUES (?,?,?,?)',
               (context_id, json.dumps(checkpoint), reason, retired_at))
    return True


def no_inline_images(value):
    if isinstance(value, str) and ('data:image/' in value or 'data:application/octet-stream;base64,' in value):
        raise ValueError('checkpoint_must_reference_files_not_inline_images')
    if isinstance(value, dict):
        for item in value.values(): no_inline_images(item)
    elif isinstance(value, list):
        for item in value: no_inline_images(item)
