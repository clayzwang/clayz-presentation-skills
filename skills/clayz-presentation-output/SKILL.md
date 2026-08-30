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

1. Validate the complete plugin root with `../../scripts/validate_plugin_mount.py`, then resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its lock and resolved config hash with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. Resolve every private master or asset through a logical `library://` mount, never a path embedded in this Skill. Missing shared runtime files are `plugin-runtime-incomplete`, not permission to run as a detached Skill.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy package and art-direction plan, including their identical resource-inventory signature. Build only with resources selected in that inventory; new assets or routes require Supervisor to revise, re-lock, and re-present the inventory first.
4. Read `references/runtime-routing.md`, `references/art-direction-handoff.md`, and `references/build-only-contract.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/expression-mode.md`, `references/relative-layout.md`, `references/layout-contract-compilation.md`, and `references/composition-plan-consumption.md`; they define approved-medium implementation, constraint-based regions, registered-contract compilation, and the Pattern decision boundary.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
7. Read the locale-matched `../clayz-presentation-supervisor/references/first-class-index-gate.md`. Reuse the one task Provider lock created before Logic and consume the required Output learning source through finalized receipts. A required master, font, brand asset, or Index source that cannot be materialized on the selected host is a capability failure, not permission to substitute another identity. For identities listed by `theme.typography.font_validation.deferred_font_identities`, treat each canonical family and its aliases as one font, then follow the deferred-native cloud policy below instead of pretending the cloud renderer owns the full font.
8. Resolve optional Output capabilities through the built-in Capability Index. On ChatGPT, use `native-presentation-tool` only when task preflight locked it as the single provisional/attemptable route and its challenge-bound host declaration covers every required capability; that declaration does not establish readiness. The Output attempt must produce independently inspectable PPTX objects and final renders or return a hard route failure to Supervisor. Use `renderer-pptxgenjs` only when that renderer is explicitly selected and available; use `technical-drift` or `repair-loop` only when the written artifact actually drifts from the approved plan.
9. Load only optional `knowledge_refs` returned by selected capability records. Keep capability, Layout Contract, Composition Pattern, linked Failure Pattern, and retrieval receipt IDs as task-local evidence; unresolved signals never justify pretending renderer support, re-selecting a composition method, or inventing a repair method.

## Workflow

1. Load colors, typography, layout roles, optional master, renderer, target applications, delivery profile, and QA thresholds only from the resolved configuration.
2. Consume the one `runtime-preflight.json` created by root Supervisor before Logic; Output must not run a second preflight. Verify that its run ID, task-request SHA-256, task-root SHA-256, canonical issuance/consumption receipt hashes, and resolved-config SHA-256 match this run, then consume its locked authoring and render route without rediscovering tools or switching routes. Preserve `target_application_checks` as observations separate from the route gate: an unavailable target-native reopen check is deferred evidence, not a reason to stop Logic or authoring. If a hard route failure requires a fallback, return control to Supervisor so it can close the run and restart from a fresh bound preflight within the configured restart budget.
3. Verify the locked route satisfies every task-required authoring/rendering capability. Record unavailable capabilities instead of pretending support. Never add `*-reopen-render` target-acceptance capabilities to the route-required set merely because the application appears in `target_applications`. Renderer-specific optional guidance must have been resolved by Capability Index.
4. When Art Direction selected a registered Composition Pattern, verify the compiled Composition Plan and its receipts; consume its semantic mapping, constraints, expected visual effect, and failure guards without re-selecting the Pattern. Then, when Art Direction selected a registered Layout Contract, verify and compile it with `../../packages/layout/compile_layout_contract.py`; otherwise consume the explicitly approved core Layout Tree. Resolve approved relative regions with `../../packages/layout/solve_relative_layout.py`, then build editable objects from the resolved layout, area plan, and `copy_unit_map`. Output never selects or invents a Pattern or contract.
5. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory.
6. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved.
7. Collect source material in one bounded round, cache it task-locally, write the PPTX once, reopen it through the locked render route, inspect package objects, render every slide, and perform thumbnail plus full-size review. For each configured target application, run native reopen/render only when that capability is available and selected within the bounded run; record available but unused targets as `not-selected`, unavailable targets as `deferred`, and executed targets as `pass` or `fail`. These states must flow into Supervisor's `environment_observation`. Resolve a deferred font identity against its canonical family plus aliases; one match satisfies the identity, and aliases never become fallback positions. Write the identity's exact `pptx_family` into both Latin and East Asian PPTX fields. When `font_validation.mode` is `preserve-name-defer-native` and the cloud resolves none of the identity names, label cloud renders diagnostic-only, skip cloud PDF pixel-equivalence as an acceptance gate, and emit `font-validation-pending` for native-machine reopen/render. Never hide or normalize a substituted cloud font. When Office is selected, keep one process alive for the run instead of reopening the application per slide or check.
8. Run at most one targeted technical repair when the controlled-repair capability was resolved. Never let a repair loop rewrite content or art direction.
9. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config <resolved-config.json>
```

10. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, runtime preflight, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
11. Emit the final PPTX, render evidence, object inventory, deviation log, and output QA report with status `built` plus root `resource_inventory_lock` and `index_evidence`. Verify each quantitative encoding against actual native chart/table/shape objects; a plan-object mismatch cannot be described away. When deferred-native validation applies, include each identity's requested canonical family, matched installed name or `unavailable`, written PPTX family, observed cloud renderer, diagnostic-only render status, and `font-validation-pending` acceptance state.
12. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them.

## Validation

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass the exact bound `--config <resolved-config.json>` to policy-aware validators. A successful in-memory write is never a substitute for reopening and rendering the final file.

Hand all artifacts to `$clayz-presentation-supervisor`. Output may stage the PPTX, but it must not present the PPTX as the final user delivery. Supervisor performs the independent audit, validates the report against the same preflight and resolved config, and invokes `../../scripts/publish_supervised_pair.py`; only that verified bundle may be handed off as the final PPTX plus `ppt-supervision-report.json` pair.
