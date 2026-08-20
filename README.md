# Clayz Presentation Skills

[English](README.md) | [简体中文](README.zh-CN.md)

Clayz Presentation Skills is an open, five-stage system for producing evidence-based presentations:

1. **Logic** establishes the question chain, claims, evidence, and cross-slide invariants.
2. **Copy** locks every visible word, number, break, and atomic copy unit.
3. **Art Direction** turns approved copy into a visual plan without changing content.
4. **Output** builds an editable presentation against the approved plan.
5. **Supervisor** audits drift and evidence without silently redesigning the deck.

The original architecture was created and released under the **clayz** brand.

## Design principles

- Keep reasoning and visual production as separate approval stages.
- Treat models as capable decision makers; use contracts and scripts only where determinism matters.
- Keep themes, fonts, renderers, reference providers, delivery profiles, and attribution in one central configuration file.
- Never let automated scores replace business, editorial, or visual judgment.
- Preserve editability, source traceability, and final rendered evidence.

## Repository layout

- `skills/` contains the five focused skills.
- `config/default.json` is the single public configuration source.
- `packages/validators/` contains shared deterministic validators.
- `packages/contracts/` contains versioned cross-stage contracts.
- `knowledge/` contains the empty portable learning, source, and index scaffold.
- `examples/` contains synthetic examples only.
- `provenance/` records conceptual influences and redistributed dependencies.

## Quick start

Clone the complete repository so the five skills keep access to their shared configuration, contracts, validators, and empty knowledge scaffold:

```bash
git clone <your-repository-url> clayz-presentation-skills
cd clayz-presentation-skills
python -m pip install -r requirements.txt
python scripts/validate_all.py
```

Register or expose the five directories under `skills/` to your agent host. Start with Logic and pass each approved artifact to the next stage. Preserve the repository-relative paths; copying one skill directory by itself removes its shared configuration and contracts. Do not skip Supervisor for a final deliverable.

Validate the repository:

```bash
python -m pip install -r requirements.txt
python scripts/validate_all.py
```

Stamp non-visible clayz provenance into a generated PPTX:

```bash
python scripts/stamp_pptx_metadata.py deck.pptx --config config/default.json
```

The metadata stamp is documented, removable, and contains no tracking identifier or network behavior.

Remove only the Clayz-owned custom properties while preserving unrelated document metadata:

```bash
python scripts/stamp_pptx_metadata.py deck.pptx --config config/default.json --remove
```

## Runtime expectations

- The core scripts require Python 3.10 or later. Pillow is used by raster, rhythm, and size inspection utilities.
- GitHub Actions tests Python 3.10, 3.11, and 3.12 and starts every public command-line entry point with `--help` before release.
- Producing PPTX files requires a compatible agent host or a separately supplied backend such as a native presentation tool, PptxGenJS, or python-pptx.
- Full production QA requires a renderer that can reopen and render the written PPTX, such as PowerPoint, WPS, or LibreOffice.
- This repository currently provides skills, contracts, configuration, validators, and metadata tooling. It is not yet a standalone one-command model runner.
- MCP is optional. A capable model host can read the skills and call local tools directly; add MCP only when you want a portable interface to remote storage, search, rendering, or another external service.

## Language routing

`config/default.json` defaults to `en-US` and supports `zh-CN`. Every deep reference has an English base file such as `references/example.md` and a matching Chinese file such as `references/example.zh-CN.md`. Each skill resolves the task locale first and loads one language only, unless the user explicitly requests translation comparison. Generated deck language remains a task-level choice; it is not forced by the documentation language.

## Knowledge, learning, and reference index

The public repository includes an intentionally empty portable scaffold under `knowledge/`:

- four learning areas for Logic, Copy, Art Direction, and Output;
- one shared source tree organized by file type;
- empty asset and human-admission registries;
- stage navigation that defines retrieval, writeback, and promotion boundaries.

Supervisor has no separate learning silo. It returns reusable observations to the responsible stage. Generated artifacts, automated scores, usage counts, and Supervisor opinions never become approved references automatically.

Downloading the repository does not create, read, or connect a ChatGPT Library. The default provider is the local filesystem. A host-specific adapter may map the same structure to ChatGPT Library or another storage system, but no such adapter is bundled or required. See [`knowledge/README.md`](knowledge/README.md) and [`knowledge/registry/schema.md`](knowledge/registry/schema.md).

## Configuration

Edit or override `config/default.json`. Do not hard-code organization brands, master files, fonts, local paths, or renderer names inside a skill.

The repository intentionally includes no uploaded master, presentation, PDF, font, screenshot, or derived corporate asset. The example under `examples/` is fully synthetic.

Release validation accepts an optional, untracked denylist through `CLAYZ_RELEASE_DENYLIST` or `scripts/check_release_hygiene.py --denylist`. Keep organization-specific names and source-material phrases in that local file, never in the public repository.

For GitHub CI, store the UTF-8 denylist as a base64-encoded repository secret named `CLAYZ_RELEASE_DENYLIST_B64`. The workflow decodes it only on the runner and never commits the terms. Before a public release, also enable GitHub private vulnerability reporting as described in [`SECURITY.md`](SECURITY.md).

## Influence citations

Conceptual influences are identified at the exact reference points inside the skill documentation and summarized in `provenance/manifest.yaml`. They include [PPTAgent](https://github.com/icip-cas/PPTAgent), [DeepPresenter](https://arxiv.org/abs/2602.22839), [pom](https://github.com/hirokisakabe/pom), [VASCAR](https://arxiv.org/abs/2412.04237), and optional [PptxGenJS](https://github.com/gitbrent/PptxGenJS). No upstream source snapshot, template, media, or model is bundled.

## License and citation

Licensed under Apache-2.0. See `NOTICE`, `CITATION.cff`, and `provenance/THIRD_PARTY_NOTICES.md`.
