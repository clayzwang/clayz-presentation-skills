---
name: clayz-presentation-output
description: Build and verify an editable PPTX from a copy-approved package and art-direction-approved plan using the centrally configured theme, renderer, compatibility targets, delivery profile, and attribution metadata. Use for final presentation production, technical repair, media optimization, font and compatibility checks, and render-grounded QA. Do not invent content or redesign an approved composition.
---

# Clayz Presentation Output

Build the approved deck faithfully, preserve editability, and prove the written PPTX matches its contracts.

## Boundaries

Own object creation, coordinates, groups, charts, tables, SVG, media preparation, theme application, compatibility repair, package optimization, artifact metadata, and final write-reopen-render QA.

Do not change approved text, data, relationships, page sequence, composition, or visual intent. Return material conflicts upstream with evidence.

## Required context

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy package and art-direction plan.
4. Read `references/art-direction-handoff.md` and `references/build-only-contract.md`.
5. Read `references/expression-mode.md` to implement approved media.
6. Read `references/relative-layout.md` for constraint-based regions.
7. Read `references/lightweight-delivery.md` for the selected delivery profile.
8. Read `references/controlled-repair-loop.md` when the written artifact drifts from the plan.
9. Read `../../packages/contracts/knowledge-learning.md` before retrieving prior implementation learning or persisting a reusable observation.

## Workflow

1. Load colors, typography, layout roles, optional master, renderer, target applications, delivery profile, and QA thresholds only from the resolved configuration.
2. Select a renderer that satisfies every required capability. Record unavailable capabilities instead of pretending support.
3. Build editable objects from the semantic layout tree, area plan, and `copy_unit_map`.
4. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory.
5. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved.
6. Write the PPTX, reopen it, inspect package objects, render every slide, and perform thumbnail plus full-size review.
7. Run targeted technical repairs only. Never let a repair loop rewrite content or art direction.
8. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config ../../config/default.json
```

9. Emit the final PPTX, render evidence, object inventory, deviation log, and output QA report with status `built`.
10. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them.

## Validation

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass `--config ../../config/default.json` to policy-aware validators. A successful in-memory write is never a substitute for reopening and rendering the final file.

Hand all artifacts to `$clayz-presentation-supervisor`.
