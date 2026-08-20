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
- `admitted_by`: human or governance role;
- `admitted_at`: ISO 8601 timestamp;
- `use_for`: approved uses;
- `never_copy`: elements that must not be reproduced;
- `decision_notes`: reason and limitations.

## Stage `learning-records.jsonl`

Each row records an observation without automatically promoting it:

- `record_id`: stable unique identifier;
- `stage`: `logic`, `copy`, `art-direction`, or `output`;
- `task_purpose`: the task class where the observation arose;
- `observation`: reusable learning or failure pattern;
- `evidence_refs`: task artifacts, renders, or source identifiers;
- `decision`: what was preserved, changed, or rejected;
- `user_ruling`: optional human judgment;
- `promotion_status`: `observation`, `rejected`, or `admitted`;
- `created_at`: ISO 8601 timestamp.

An `admitted` status is not sufficient by itself. Retrieval still requires a matching row in `admitted-references.jsonl` when `require_human_admission` is enabled.

## Generated `search-index.json`

`scripts/knowledge_cli.py build-index` writes the configured index path. Only unchanged assets with a matching human-admission row are included. Text-like sources receive local BM25-style lexical tokens; PPTX, PDF, and image assets expose registered metadata only unless an authorized host adapter supplies extraction. The generated index is runtime state and is not committed.
