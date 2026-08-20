---
name: clayz-presentation-art-direction
description: Convert a copy-approved presentation package into an art-direction-approved visual plan covering first visual, hierarchy, medium, area allocation, semantic layout tree, cross-slide rhythm, and reference evidence. Use between final copy and PPTX production, or to diagnose composition, density, cardification, weak hierarchy, repetitive layouts, or unreadable charts. Do not rewrite approved content or build the final PPTX.
---

# Clayz Presentation Art Direction

Create an `art-direction-approved` plan that makes visual judgment explicit without becoming a second copy source or a coordinate engine.

## Boundaries

Own reference selection, first visual, visual anchor, dominant medium, hierarchy, area plan, semantic layout tree, silhouette, density, reading path, whitespace, motif, series behavior, and cross-slide rhythm.

Do not modify approved facts, wording, numbers, punctuation, breaks, notes, page order, management stage, or cross-slide invariants. Do not create final PPTX objects.

## Required context

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy-approved package.
4. Read `references/art-direction-plan-contract.md`.
5. Read `references/material-routes.md` to select the dominant medium.
6. Read `references/ab-and-regression.md` only for high-risk pages requiring real alternatives.
7. Read `references/reference-cluster-discovery.md` when a large reference set must be narrowed.
8. Read `../../packages/contracts/knowledge-learning.md` before retrieving prior visual learning or persisting a reusable observation.

## Workflow

1. Group slides by communication purpose, relationship, load, decision weight, series role, and silhouette risk.
2. Use the configured reference provider. Admit only traceable, human-approved sources with clear rights boundaries.
3. For every slide, state the intended first impression, first visual, area allocation, dominant medium, density, reading path, semantic whitespace, and risks.
4. Build a semantic layout tree that records containment, peers, sequence, cause, condition, support, comparison, feedback, or anchors.
5. Map every `copy_id` exactly once to a render target and verification method.
6. Use real rendered A/B prototypes for high-risk composition; do not treat automated scores or similarity as the winner.
7. Judge the deck as a sequence, not a collection of isolated pages.
8. Emit task-local learning candidates with rendered evidence, applicability, and `never_copy` boundaries; persist them only through the configured Art Direction learning route and never auto-promote them.
9. Emit one plan with `origin_namespace: io.clayz.presentation` and status `art-direction-approved`.

## Validation

Run:

```bash
python ../../packages/validators/validate_art_direction_plan.py <copy-package.json> <art-direction-plan.json> --config ../../config/default.json
```

Hand the validated plan to `$clayz-presentation-output`.
