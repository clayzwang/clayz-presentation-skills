# Portable knowledge runtime

Version 0.2.0 makes the empty knowledge scaffold operational without shipping anyone's taste, private examples, or corporate assets. All runtime paths and limits resolve from `config/default.json` unless an explicit configuration override is supplied.

## Boundary

- Sources stay under `knowledge/sources/` and are organized by file type.
- Registration records identity, hash, source, license, language, purpose, and neighbors; it does not approve quality.
- Human admission is a separate explicit act and requires `--confirm-human-decision`.
- Indexing includes only sources with a matching admission record and an unchanged hash.
- Text-like files use local lexical indexing. Binary PPTX/PDF/image content is not silently extracted; only registered metadata is searchable unless a host supplies an authorized parser.
- Search scores retrieve candidates. They never promote quality, replace judgment, or change the current deck's approved source of truth.
- Learning writeback always starts as `promotion_status=observation`.
- Learning becomes retrievable only after a second human admission binds its
  exact canonical SHA-256. Changing the observation invalidates the admission.
- Admitted learning remains a private-runtime record and does not enter the
  public catalog automatically.

## Commands

Place a user-owned or properly licensed source beneath `knowledge/sources/`, then register it:

```bash
python scripts/knowledge_cli.py register knowledge/sources/documents/example.md \
  --source-uri https://example.org/source \
  --license CC-BY-4.0 \
  --language en-US \
  --purpose-tag narrative-structure
```

Record a real human admission separately:

```bash
python scripts/knowledge_cli.py admit asset <asset-id> \
  --admitted-by maintainer \
  --use-for narrative-structure \
  --never-copy wording \
  --confirm-human-decision
```

Build and query the local index:

```bash
python scripts/knowledge_cli.py build-index
python scripts/knowledge_cli.py search "evidence before recommendation" --purpose narrative-structure
```

Append a task-grounded observation without promoting it:

```bash
python scripts/knowledge_cli.py record-learning art-direction \
  --task-purpose comparison-page \
  --observation "The rendered labels collided after localization." \
  --evidence-ref output/rendered/3.png \
  --decision "Return the capacity conflict to Art Direction."
```

Admit that exact observation as private learning only after a human review:

```bash
python scripts/knowledge_cli.py admit learning <learning-record-id> \
  --admitted-by maintainer \
  --use-for renderer-compatibility \
  --never-copy generated-coordinates \
  --promotion-target compatibility-note \
  --confirm-human-decision

python scripts/knowledge_cli.py build-index
```

The generated index uses `io.clayz.presentation.knowledge-index/2.0` and keeps
asset and learning counts separate. Stage 5 also provides the generic provider
path, benchmark, and migration commands documented in
[`feedback-benchmark-release-readiness.md`](feedback-benchmark-release-readiness.md).

## Host adapters

A host may replace lexical search with embeddings, map the filesystem contract to ChatGPT Library, or add parsers for PDF/PPTX. The adapter must preserve stable IDs, source/license data, human admission, `never_copy`, hashes, and no-auto-promotion. It must report when persistence or retrieval did not occur.
