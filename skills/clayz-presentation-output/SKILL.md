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
4. Read `references/art-direction-handoff.md` and `references/build-only-contract.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/expression-mode.md` and `references/relative-layout.md`; they define approved-medium implementation and constraint-based regions and remain core Output execution guidance.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
7. Resolve optional Output capabilities through the built-in Capability Index. Use `renderer-pptxgenjs` only when that renderer is explicitly selected and available; use `technical-drift` or `repair-loop` only when the written artifact actually drifts from the approved plan.
8. Load only optional `knowledge_refs` returned by selected capability records. Keep capability resolution and retrieval receipt IDs as task-local evidence; unresolved signals never justify pretending renderer support or inventing a repair method.

## Workflow

1. Load colors, typography, layout roles, optional master, renderer, target applications, delivery profile, and QA thresholds only from the resolved configuration.
2. Select a renderer that satisfies every required capability. Record unavailable capabilities instead of pretending support. Renderer-specific optional guidance must have been resolved by Capability Index.
3. Resolve approved relative regions with `../../packages/layout/solve_relative_layout.py`, then build editable objects from the resolved layout, area plan, and `copy_unit_map`.
4. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory.
5. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved.
6. Write the PPTX, reopen it, inspect package objects, render every slide, and perform thumbnail plus full-size review.
7. Run targeted technical repairs only when the controlled-repair capability was resolved. Never let a repair loop rewrite content or art direction.
8. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config ../../config/default.json
```

9. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
10. Emit the final PPTX, render evidence, object inventory, deviation log, and output QA report with status `built`.
11. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them.

## Validation

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass `--config ../../config/default.json` to policy-aware validators. A successful in-memory write is never a substitute for reopening and rendering the final file.

Hand all artifacts to `$clayz-presentation-supervisor`.
