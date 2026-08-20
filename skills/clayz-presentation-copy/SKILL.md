---
name: clayz-presentation-copy
description: Turn a logic-approved presentation package into final visible copy with locked titles, storylines, numbers, punctuation, line breaks, notes, and atomic copy units. Use after presentation logic is approved and before visual composition. Do not change facts, evidence status, slide order, or business relationships, and do not design or build the PPTX.
---

# Clayz Presentation Copy

Create a `copy-approved` package in which every visible character is intentional and traceable.

## Boundaries

Own titles, storylines, visible copy, numbers, units, punctuation, intentional breaks, notes, copy hierarchy, and stable `copy_id` values.

Do not change Logic-approved facts, claims, relationships, page responsibilities, management stages, cross-slide invariants, or slide order. Do not choose visual layout or create PPTX objects.

## Required context

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the Logic package before editing copy.
4. Read `references/copy-package-contract.md`.
5. Read `references/atomic-copy-and-hierarchy.md` when a sentence contains multiple renderable units or nested meaning.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieving prior language learning or persisting a reusable observation.

## Workflow

1. Preserve every approved claim and evidence qualifier.
2. Write titles that state the page function or conclusion without exaggeration.
3. Write a storyline only when it advances the argument; do not duplicate the title.
4. Break visible text into atomic units. Assign one stable `copy_id` to each unit and express parent-child and peer relationships explicitly.
5. Lock exact text, numbers, units, punctuation, intentional breaks, and speaker notes.
6. Keep charts and tables supplied with complete labels, units, sources, and explanation text.
7. Raise upstream conflicts instead of silently fixing Logic.
8. Emit task-local learning candidates with language, audience, evidence, and limits; persist them only through the configured Copy learning route and never auto-promote them.
9. Emit one package with `origin_namespace: io.clayz.presentation` and status `copy-approved`.

## Validation

Run:

```bash
python ../../packages/validators/validate_ppt_package.py <copy-package.json>
```

Hand the validated package to `$clayz-presentation-art-direction`.
