# Built-in index catalog

`catalog/` contains only project-maintained contracts, original method records, and metadata that are safe to distribute with the open-source repository. It is not a template library and must not contain third-party presentation files, masters, themes, fonts, brand kits, screenshots, extracted company visual identities, datasets, or model weights.

The generated user knowledge index remains under `knowledge/index/`. Host or filesystem libraries may contain private material for their owners, but provider identity and rights remain attached to every retrieval candidate. A private brand asset never becomes public merely because it was retrieved or used successfully.

At the unreleased Capability Index stage, `records.jsonl` contains brand-neutral Clayz capability-routing records. They point to existing repository methods and validators; they do not embed templates, coordinates, company identities, external prompts, model weights, or generated presentation content.

Stage 3 adds original semantic Layout Contracts under `layout-contracts/`. They
define slot topology and relative weights, not presentation templates. Every
contract is hash-bound to an index record and must be selected through a
retrieval receipt before it can be compiled.

Stage 4 adds `composition-patterns/`, `failure-patterns/`, `references/`, and
`sequences/`. Composition and Failure Patterns are original method metadata.
Reference and Sequence payloads are fully synthetic, metadata-only fixtures:
they contain no source copy, image, coordinates, fonts, brand identity, or
model features. Every file is hash-bound, human-admitted, brand-neutral, and
cross-link validated before it can be retrieved or exported.

Stage 5 does not add task feedback to this public catalog. Human-admitted
observations are rebuilt as a separate private-runtime provider and remain
`public_catalog_eligible=false`. Benchmark fixtures may reference their stable
metadata IDs, but never copy private content into `catalog/`.
