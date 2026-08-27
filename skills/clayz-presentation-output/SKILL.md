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

1. Resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its lock and resolved config hash with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. Resolve every private master or asset through a logical `library://` mount, never a path embedded in this Skill.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy package and art-direction plan.
4. Read `references/runtime-routing.md`, `references/art-direction-handoff.md`, and `references/build-only-contract.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/expression-mode.md`, `references/relative-layout.md`, `references/layout-contract-compilation.md`, and `references/composition-plan-consumption.md`; they define approved-medium implementation, constraint-based regions, registered-contract compilation, and the Pattern decision boundary.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
7. Reuse the one task Provider lock created before Logic; it always contains the bundled public Provider and may contain owner-private Providers whose declared stages include Output. A required master, font, or brand asset that cannot be materialized on the selected host is a capability failure, not permission to substitute another identity.
8. Resolve optional Output capabilities through the built-in Capability Index. On ChatGPT, use `native-presentation-tool` only when the task preflight's inspected host-capability declaration satisfies every required capability. Use `renderer-pptxgenjs` only when that renderer is explicitly selected and available; use `technical-drift` or `repair-loop` only when the written artifact actually drifts from the approved plan.
9. Load only optional `knowledge_refs` returned by selected capability records. Keep capability, Layout Contract, Composition Pattern, linked Failure Pattern, and retrieval receipt IDs as task-local evidence; unresolved signals never justify pretending renderer support, re-selecting a composition method, or inventing a repair method.

## Workflow

1. Load colors, typography, layout roles, optional master, renderer, target applications, delivery profile, and QA thresholds only from the resolved configuration.
2. Run `../../scripts/runtime_preflight.py` exactly once, persist its report, and lock one authoring and render route. Do not rediscover tools or switch routes during the run. If a hard failure requires a fallback, close the run and restart from preflight within the configured restart budget.
3. Verify the locked route satisfies every task-required capability. Record unavailable capabilities instead of pretending support. Renderer-specific optional guidance must have been resolved by Capability Index.
4. When Art Direction selected a registered Composition Pattern, verify the compiled Composition Plan and its receipts; consume its semantic mapping, constraints, expected visual effect, and failure guards without re-selecting the Pattern. Then, when Art Direction selected a registered Layout Contract, verify and compile it with `../../packages/layout/compile_layout_contract.py`; otherwise consume the explicitly approved core Layout Tree. Resolve approved relative regions with `../../packages/layout/solve_relative_layout.py`, then build editable objects from the resolved layout, area plan, and `copy_unit_map`. Output never selects or invents a Pattern or contract.
5. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory.
6. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved.
7. Collect source material in one bounded round, cache it task-locally, write the PPTX once, reopen it, inspect package objects, render every slide, and perform thumbnail plus full-size review. When Office is selected, keep one process alive for the run instead of reopening the application per slide or check.
8. Run at most one targeted technical repair when the controlled-repair capability was resolved. Never let a repair loop rewrite content or art direction.
9. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config ../../config/default.json
```

10. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, runtime preflight, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
11. Emit the final PPTX, render evidence, object inventory, deviation log, and output QA report with status `built`.
12. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them.

## Validation

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass `--config ../../config/default.json` to policy-aware validators. A successful in-memory write is never a substitute for reopening and rendering the final file.

Hand all artifacts to `$clayz-presentation-supervisor`.
