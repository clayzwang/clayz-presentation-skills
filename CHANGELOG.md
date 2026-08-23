# Changelog

All notable public changes are recorded here. This project follows Semantic Versioning.

## Unreleased

- Begin the unreleased v0.4.0 Index Foundation without changing `VERSION` or publishing a release.
- Add provider-aware index records, structured retrieval requests, deterministic retrieval receipts, and selection guards that reject identifiers not present in the receipt.
- Preserve source revision, provider identity, license, `never_copy`, and materialization status for every candidate; return an explicit empty result instead of fabricating a fallback record.
- Add a public-catalog validator that rejects presentation templates, masters, themes, and font binaries, and prevents brand-specific assets from becoming public without explicit redistribution and materialization rights.
- Add a fully synthetic three-provider example and regression tests proving that private local brand masters are excluded from public-open-source retrieval.
- Add Stage 2 Capability Index routing: mandatory stage contracts remain deterministic while optional knowledge is selected only from registered, human-admitted, brand-neutral capability records with auditable per-signal retrieval receipts.
- Convert the five stage skills to index-native optional-reference routing without adding a sixth decision-making skill; unresolved capability signals remain explicit instead of triggering invented guidance.
- Keep the public capability catalog method-only and validate every referenced repository path; no company template, master, brand kit, font binary, dataset, model weight, or generated presentation enters the catalog.
- Add Stage 3 Layout Contracts as original, brand-neutral, hash-bound semantic topology above the existing Semantic Layout Tree and relative solver, without changing the five-skill ownership model.
- Separate Theme, Visual Variant, Layout Contract, task-local Layout Tree, and resolved coordinates; the compiler consumes no theme or variant input and preserves receipt-to-contract-to-tree lineage.
- Reject unregistered, unretrieved, ambiguous, hash-drifted, or invalid contracts; an empty match stays explicitly `unresolved` and emits no invented fallback tree.
- Add two synthetic public contracts, schemas, compiler, validators, regression fixtures, and Tahta conceptual attribution with a strict no-code/no-template/no-asset redistribution boundary.

## 0.3.0 — 2026-08-22

- Add a validated index of 76 distinct official, diagram-bearing architecture documents from ten publishers and a bilingual 16-card relationship-pattern library.
- Replace rule-oriented architecture-house guidance with an eight-step corpus-to-pattern-to-synthesis method covering source selection, relationship extraction, pattern combination, task-specific derivation, slide translation, diagnosis, and research-ledger closure.
- Thank and record the official enterprise architecture authors and design teams behind IBM, Microsoft, Google Cloud, AWS, Oracle, SAP, NVIDIA, Databricks, Snowflake, and Apple under documentation-reference-only, no-redistribution boundaries.
- Upgrade Art Direction contract to v1.4 with content-aware canvas analysis and governed template/icon asset selection; image-led slides must record subject protection, usable copy zones, crop, contrast, directional flow, and local overlay decisions.
- Add bilingual content-aware composition and asset/template grammar references that treat external layouts and icons as reviewed moves to re-derive, never fixed templates to clone.
- Add a machine-validated eleven-case synthetic visual regression suite covering four material routes, four cross-slide behaviors, image-led composition, licensed asset selection, and reference-architecture houses.
- Cite and thank PosterLayout, Scan-and-Print, and CreatiPoster under paper-citation-only boundaries; redistribute no upstream code, models, datasets, figures, layouts, fonts, or media.
- Clarify that Clayz independently implemented its first five core capabilities before later reviewing PPT Master and other sources; add pinned attribution and explicit non-redistribution boundaries.
- Add a bilingual GitHub Pages Experience Center with slide-level browsing, release capability mapping, visual-range examples, and downloadable editable output evidence.
- Add a public A-share market-analysis case with nine web-safe previews and a 16-slide editable deck.
- Keep public output evidence isolated from `examples/`, `knowledge/`, and the reference corpus through a machine-readable case manifest.
- Extend release-hygiene validation so only declared public PPTX artifacts are allowed and their XML payloads are scanned for private paths, opaque file identifiers, credentials, and denylist terms.
- Establish `VERSION` as the release source of truth, add atomic release preparation and cross-surface validation, and make release tags immutable.

## 0.2.0 — 2026-08-20

- Turn the empty knowledge scaffold into a human-admitted, hash-bound, local lexical register/index/search workflow with neighbor expansion and observation-only learning writeback.
- Add an original renderer-neutral relative-layout solver plus layout-tree and render-manifest contracts.
- Add an original experimental PptxGenJS API adapter and synthetic render-manifest fixture, but fail closed and omit the dependency lock because the current upstream dependency chain has two unpatched high-severity denial-of-service advisories.
- Add a bounded execution ledger for tool calls, artifacts, hashes, failures, and technical repair cycles without storing private chain-of-thought.
- Add English-first, Chinese-paired references for design-intent trees, editable-object output, execution evidence, and source-adoption boundaries.
- Record exact reviewed upstream revisions, licenses, citation-only boundaries, and explicit thanks for PPTAgent, DeepPresenter, pom, VASCAR, PosterO, and PptxGenJS.
- Preserve the public-growth boundary: no real presentation cases, taste corpus, personal preferences, templates, masters, private assets, runtime/model weights, or automatic aesthetic truth.

## 0.1.0 — 2026-08-20

- Publish the five-stage Logic, Copy, Art Direction, Output, and Supervisor architecture.
- Centralize public configuration, Clayz attribution metadata, renderer routing, delivery profiles, and QA policy.
- Provide 19 English deep references with 19 matching Simplified Chinese references and locale-aware loading.
- Provide four empty stage-learning areas, one empty shared-source area, registries, and navigation contracts.
- Add contract validators, public CLI smoke tests, Markdown-link validation, and a synthetic approved handoff regression.
- Test Python 3.10, 3.11, and 3.12 in CI.
- Exclude presentation templates, uploaded source material, bundled fonts, and private reference data.
