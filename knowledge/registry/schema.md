# Registry schema

All registry and learning files use UTF-8 JSON Lines: one JSON object per non-empty line. Empty files are valid.

## `asset-registry.jsonl`

Each row describes one discoverable source:

- `asset_id`: stable unique identifier;
- `kind`: `document`, `data`, `image`, `svg`, `pptx`, or `pdf`;
- `relative_path`: path beneath `knowledge/sources`, without `..`;
- `sha256`: lowercase file hash;
- `source_uri`: public source, user-owned source label, or `local-private`;
- `license`: reuse boundary, such as `Apache-2.0`, `public-domain`, or `private-not-for-redistribution`;
- `language`: BCP 47 tag or `und`;
- `purpose_tags`: retrieval purposes, not quality scores;
- `physical_neighbors`: adjacent asset identifiers when sequence matters;
- `semantic_neighbors`: related asset identifiers when meaning matters;
- `human_admitted`: boolean;
- `notes`: optional factual note.

## `admitted-references.jsonl`

Each row records an explicit human decision:

- `admission_id`: stable unique identifier;
- `subject_type`: `asset` or `learning`;
- `subject_id`: an `asset_id` or learning `record_id`;
- `subject_sha256`: the exact file hash for an asset or canonical JSON hash for a learning record;
- `admitted_by`: human or governance role;
- `admitted_at`: ISO 8601 timestamp;
- `use_for`: approved uses;
- `never_copy`: elements that must not be reproduced;
- `decision_notes`: reason and limitations.

Learning admissions also contain `contract`, `promotion_target`, and
`public_catalog_eligible=false`. The promotion target classifies private reuse;
it does not authorize public publication.

## Stage `learning-records.jsonl`

Each row records an observation without automatically promoting it:

- `record_id`: stable unique identifier;
- `stage`: `logic`, `copy`, `art-direction`, or `output`;
- `task_purpose`: the task class where the observation arose;
- `observation`: reusable learning or failure pattern;
- `evidence_refs`: task artifacts, renders, or source identifiers;
- `decision`: what was preserved, changed, or rejected;
- `user_ruling`: optional human judgment;
- `promotion_status`: always `observation` in the source record;
- `created_at`: ISO 8601 timestamp.

Retrieval requires a separate row in `admitted-references.jsonl` whose
`subject_sha256` matches the unchanged record. Source records never promote
themselves.

## Generated `search-cache.json`

`scripts/knowledge_cli.py build-index` writes the configured v2 cache path. Only unchanged assets and unchanged learning records with matching human-admission rows are included. The cache preserves `record_type`, `source_type`, and responsible `stage`. Text-like sources receive local BM25-style lexical tokens; PPTX, PDF, and image assets expose registered metadata only unless an authorized host adapter supplies extraction. The generated cache is runtime state, is not a canonical Provider index, and is not committed.
