# Portable knowledge scaffold

This directory is intentionally distributed without private knowledge, templates, decks, screenshots, fonts, or learned preferences. It provides a portable place for each user to build an independent reference system.

The structure has four stage-specific learning areas and one shared source-and-index area:

- `learning/logic/` records reusable reasoning and narrative observations.
- `learning/copy/` records reusable language and atomic-copy observations.
- `learning/art-direction/` records reusable visual judgment and regression observations.
- `learning/output/` records reusable implementation and compatibility observations.
- `sources/` and `registry/` store shared materials and their searchable, human-governed metadata.
- `index/` receives a generated local lexical index; the generated file is ignored by Git.

Supervisor deliberately has no separate learning silo. It reads all approved artifacts and rendered evidence, records findings in task outputs, and returns reusable observations to the responsible stage.

## Admission rules

1. Store source material by file type, not by skill ownership.
2. Register stable identifiers, origin, license, language, purpose, hash, and neighbor relationships before retrieval.
3. Treat learning records as observations, not quality truth.
4. Never promote a generated artifact, score, usage count, or Supervisor opinion into the reference set automatically.
5. Use only material with an explicit human admission record and a clear rights boundary.

## Operational commands

`scripts/knowledge_cli.py` registers sources, records human admission, builds the local index, searches admitted material, and appends non-promoted learning observations. Paths and retrieval limits come from `config/default.json`; no knowledge content is embedded in the skill files.

See [`../docs/knowledge-runtime.md`](../docs/knowledge-runtime.md) for commands and adapter boundaries.

The default provider is the local filesystem. Downloading this repository does not create or connect a ChatGPT Library. A host-specific adapter may map the same structure to ChatGPT Library or another storage system, but no such adapter is bundled or required. No source is searchable until its unchanged hash has a separate human-admission record.
