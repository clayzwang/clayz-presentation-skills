# Design-intent layout tree

Use this route when a page contains nested meaning, a dominant visual anchor, protected negative space, or relationships that would be damaged by flattening everything into peer rectangles.

This abstraction is conceptually informed by [PosterO](https://openaccess.thecvf.com/content/CVPR2025/html/Hsu_PosterO_Structuring_Layout_Trees_to_Enable_Language_Models_in_Generalized_CVPR_2025_paper.html), which studies structured layout trees and design intent for generalized content-aware layout generation. Clayz does not redistribute or run its code, datasets, annotations, weights, figures, saliency pipeline, or generated layouts. The referenced repository does not publish a clear repository-level license, so this integration is citation-only and independently expressed. Exact provenance is recorded in `provenance/manifest.yaml`.

## Separate intent from geometry

Before choosing coordinates, state the intended visual relationship:

- what the audience should notice first;
- which elements form a semantic group;
- whether the relationship is sequence, comparison, containment, causality, hierarchy, or annotation;
- which visual/content region must remain unobstructed;
- which region may absorb variation in copy or media;
- what change is allowed across a series and what must persist.

Intent is a hypothesis to be judged against approved Logic and Copy. A detector, saliency map, similarity score, or language model label is supporting evidence only.

## Tree grammar

- The root expresses the page-level communication task, not a generic canvas.
- Internal nodes express grouping, containment, reading order, alignment, or layering.
- Leaves bind approved `copy_id` values or an approved non-text object.
- `role` describes function; `intent` explains why the node exists.
- `protected=true` marks semantic whitespace or a visual subject area that descendants may not consume.
- A tree may use `row`, `column`, `grid`, and `layers`, but the vocabulary is not a component library and does not choose the composition by itself.

Every approved copy unit must map exactly once. Parent-child relations must survive into object groups and rendered reading order. If two leaves have different relationships, do not give them identical containers merely to simplify production.

## Content-aware use

For a photographic or illustrated canvas, identify the subject, directional movement, visual weight, and safe text region. Preserve the useful image evidence; do not claim that a generic saliency tool knows presentation intent. For data pages, treat plot area, labels, annotations, and source notes as semantically distinct regions even if they share a chart container.

## Handoff and proof

Export the approved tree using `packages/contracts/layout-tree.schema.json`. Output can resolve a technical coordinate proposal with:

```bash
python packages/layout/solve_relative_layout.py layout-tree.json resolved-layout.json
```

The solver is intentionally limited: it allocates approved relationships and reports impossible constraints. It cannot select the winning visual idea, shrink copy silently, consume protected whitespace, or replace rendered A/B review. The final evidence must compare the approved tree, editable object hierarchy, and actual rendered reading order.
