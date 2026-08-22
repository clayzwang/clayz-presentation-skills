---
name: clayz-presentation-art-direction
description: Convert a copy-approved presentation package into an art-direction-approved visual plan covering first visual, hierarchy, medium, area allocation, content-aware image composition, governed template and icon selection, semantic layout tree, cross-slide rhythm, and reference evidence. Use between final copy and PPTX production, or to diagnose composition, density, cardification, weak hierarchy, repetitive layouts, image-text conflict, template imitation, decorative icons, or unreadable charts. Do not rewrite approved content or build the final PPTX.
---

# Clayz Presentation Art Direction

Create an `art-direction-approved` plan that makes visual judgment explicit without becoming a second copy source or a coordinate engine.

## Boundaries

Own reference selection, first visual, visual anchor, dominant medium, hierarchy, area plan, content-aware canvas analysis, asset strategy, semantic layout tree, silhouette, density, reading path, whitespace, motif, series behavior, and cross-slide rhythm.

Do not modify approved facts, wording, numbers, punctuation, breaks, notes, page order, management stage, or cross-slide invariants. Do not create final PPTX objects.

## Required context

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy-approved package.
4. Read `references/art-direction-plan-contract.md`.
5. Read `references/material-routes.md` to select the dominant medium.
6. Read `references/layout-intent-tree.md` when nested meaning, protected whitespace, or content-aware placement must be made explicit.
7. Read `references/content-aware-composition.md` when a photograph, screenshot, illustration, render, or mixed image canvas affects placement or cropping.
8. Read `references/asset-and-template-grammar.md` when templates, icons, charts, tables, samples, or other reusable assets are considered.
9. Read `references/ab-and-regression.md` only for high-risk pages requiring real alternatives.
10. Read `references/reference-cluster-discovery.md` when a large reference set must be narrowed.
11. When the task needs a capability house, enterprise reference architecture, data/AI platform overview, or operating-system architecture, read `references/reference-architecture-house.md`; then load its source index and pattern library.
12. Read `../../packages/contracts/knowledge-learning.md` before retrieving prior visual learning or persisting a reusable observation.

## Workflow

1. Group slides by communication purpose, relationship, load, decision weight, series role, and silhouette risk.
2. Use the configured reference provider. Admit only traceable, human-approved sources with clear rights boundaries.
3. For every slide, state the intended first impression, first visual, area allocation, dominant medium, density, reading path, semantic whitespace, and risks.
4. When an image-like canvas is present, inspect subject protection, placement suitability, crop and contrast risk, and directional flow before placing copy. Blank pixels are not automatically safe space.
5. Treat templates and icons as reviewed candidates. Re-derive composition from the current page job, select assets by semantic role, and record source and license evidence; never clone a master, layout, brand identity, or arbitrary ratio.
6. For a reference-architecture house, apply the corpus-to-pattern-to-synthesis method and record the selected source IDs, relationship grammars, task adaptations, and accountability path.
7. Build a semantic layout tree that records containment, peers, sequence, cause, condition, support, comparison, feedback, or anchors.
8. Map every `copy_id` exactly once to a render target and verification method.
9. Use real rendered A/B prototypes for high-risk composition; do not treat automated scores or similarity as the winner.
10. Judge the deck as a sequence, not a collection of isolated pages.
11. Emit task-local learning candidates with rendered evidence, applicability, and `never_copy` boundaries; persist them only through the configured Art Direction learning route and never auto-promote them.
12. Emit one plan with `origin_namespace: io.clayz.presentation` and status `art-direction-approved`.

## Validation

Run:

```bash
python ../../packages/validators/validate_art_direction_plan.py <copy-package.json> <art-direction-plan.json> --config ../../config/default.json
```

Hand the validated plan to `$clayz-presentation-output`.
