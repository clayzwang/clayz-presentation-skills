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

1. Resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its lock and resolved config hash with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. Do not re-resolve or change the extension route after Logic.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the Logic package before editing copy.
4. Read `references/copy-package-contract.md`. This core contract is mandatory and never search-dependent.
5. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
6. Reuse the one task Provider lock created before Logic; it always contains the bundled public Provider and may contain owner-private Providers whose declared stages include Copy. Do not rescan either Library, change mounts, or replace a Provider snapshot mid-run.
7. Classify optional Copy signals and resolve them through the built-in Capability Index. For nested meaning or multiple renderable units, use signals such as `nested-meaning` or `atomic-copy` rather than hard-coding an optional reference read.
8. Load only optional `knowledge_refs` returned by selected capability records. Preserve the resolution and retrieval receipt IDs; unresolved signals remain explicit gaps and never trigger invented guidance.

## Workflow

1. Preserve every approved claim and evidence qualifier.
2. Write titles that state the page function or conclusion without exaggeration.
3. Write a storyline only when it advances the argument; do not duplicate the title.
4. Break visible text into atomic units. Assign one stable `copy_id` to each unit and express parent-child and peer relationships explicitly.
5. Lock exact text, numbers, units, punctuation, intentional breaks, and speaker notes.
6. Keep charts and tables supplied with complete labels, units, sources, and explanation text.
7. Raise upstream conflicts instead of silently fixing Logic.
8. Emit task-local learning candidates with language, audience, evidence, and limits; persist them only through the configured Copy learning route and never auto-promote them.
9. Emit one package with `origin_namespace: io.clayz.presentation` and status `copy-approved`; task-local execution evidence should retain the capability resolution and retrieval receipt IDs used for optional knowledge.

## Validation

Run:

```bash
python ../../packages/validators/validate_ppt_package.py <copy-package.json>
```

Hand the validated package to `$clayz-presentation-art-direction`.
