# Source adoption boundaries

Clayz learns from open work by separating concepts, public APIs, optional dependencies, and redistributed files. "Inspired by" never means "silently copied."

## Adopted in v0.2.0

| Source | Adopted | Not adopted or bundled |
|---|---|---|
| PPT Master | later-stage reference for native editable PowerPoint workflows, presentation-asset taxonomy, and provenance practice | upstream code, prompts, knowledge documents, templates, charts, tables, icons, sample decks, datasets, models, and media; none are bundled |
| PPTAgent | bounded action vocabulary, execution history, reference decomposition, targeted retry concepts | prompts, orchestration code, reference slides, models, tools, datasets |
| DeepPresenter | environment-grounded observation, faceted reflection, explicit capability gaps | model weights, tasksets, sandbox images, agent runtime, prompts, external services |
| pom | declarative relative-layout tree, fixed-plus-flex reasoning, source/preview/build separation | pom XML, Yoga source, packages, themes, master generation, node implementations |
| VASCAR | render-observe-revise as a bounded diagnostic loop | figures, code, data, scoring model, automatic winner selection |
| PptxGenJS | public API mapping for editable objects | active default runtime, dependency lock, library snapshot, demos, templates, masters, media; v0.2.0 remains security-blocked pending patched transitive dependencies |
| PosterO | design-intent and hierarchical layout-tree research concepts | repository code, weights, datasets, annotations, saliency pipeline, figures, layouts |
| PosterLayout | content-aware subject protection, placement, overlap, and readability observation vocabulary | repository code, models, datasets, annotations, metrics, figures, layouts, media |
| Scan-and-Print | patch-level placement-suitability and candidate-zone observation concepts | repository code, models, datasets, patches, annotations, figures, layouts, media |
| CreatiPoster | foreground/background separation and editable layered-composition concepts | repository code, protocol, models, datasets, training recipe, figures, layouts, fonts, media |
| IBM, Microsoft, Oracle, AWS, Google Cloud, SAP, NVIDIA, and Apple official architecture materials | primary-source sampling and independent synthesis of business outcomes, capability floors, cross-cutting controls, infrastructure foundations, and governed feedback paths | diagrams, wording, product icons, brand identity, masters, templates, coordinates, and media |

## Deliberately excluded

The project does not absorb reveal.js, Marp, PosterLlama, Typst/Paged, external master systems, automatic aesthetic truth, or runtime/model weights. It also does not ship real presentation examples. Those are product-boundary decisions, not unfinished imports.

## Attribution practice

Every adopted source has an exact upstream link, paper where relevant, reviewed commit/version, known license status, influenced components, and redistribution statement in `provenance/manifest.yaml`. User-facing thanks and notices are in `provenance/THIRD_PARTY_NOTICES.md` and `NOTICE`. References cite the source at the actual decision point.
