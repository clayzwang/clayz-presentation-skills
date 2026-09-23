---
name: clayz-presentation-output
description: Build and verify an editable PPTX from a copy-approved package and art-direction-approved plan using the centrally configured theme, renderer, compatibility targets, delivery profile, and attribution metadata. Use for final presentation production, technical repair, media optimization, font and compatibility checks, and render-grounded QA. Do not invent content or redesign an approved composition.
---

# Clayz Presentation Output

Build the approved deck faithfully, preserve editability, and prove the written
PPTX matches its contracts. Consume Art Direction's artifact and the
Supervisor calibration as separate inputs; send the completed evidence to both
Supervisor and the shared Independent Auditor module.

## Reader understanding (v0.17.1)

Read `../../packages/contracts/reader-quality.md` or its `.zh-CN.md` peer
according to the task locale. Necessary explanation and evidence fidelity take
priority over shortness; use existing records for review observations.

Preserve the complete approved wording, including causal/comparison links
and qualifiers. Do not silently abbreviate, shrink illegibly or move necessary
body explanation into notes to solve overflow. Realize approved adjustments or
return the specific capacity problem to Art Direction/Copy with evidence.

## Story and visual handoff (v0.17.0)

Before authoring, read `../../packages/contracts/story-visual-handoff.md` (or
`story-visual-handoff.zh-CN.md` for zh-CN). New runs use package 3.0 and Art
Direction plan 2.0. The mandatory story, complete image drafts, visual tags and
report documents apply even when optional Library or A/B capabilities are absent.
Legacy page-first contracts remain readable only for existing runs. Preserve
the existing Supervisor calibration and Independent Auditor handoffs.

## Boundaries

Own native object creation and technical coordinate realization within Art Direction tolerances, groups, charts, tables, SVG, media preparation, theme application, compatibility repair, package optimization, artifact metadata, and final write/reopen/render QA when the locked render route is available. Record deferred/not-run coverage when it is not.

Do not change approved text, data, relationships, page sequence, composition, or visual intent. Return material conflicts upstream with evidence.

## Required context

Read `../../packages/contracts/stage-enablement.md` for task authority, relevance-based retrieval, professional review, and measured execution. It supersedes legacy requirements to select every source, rediscover unchanged resources, or treat aesthetic heuristics as mandatory gates.


1. Validate the complete plugin root with `../../scripts/validate_plugin_mount.py`, then consume the root's v2 task selection and merged `task-config.json`. If missing, return to root to prepare the unified configuration once; never choose a different config because a Personal Runtime is installed. Resolve selected masters and assets through actual observed file references and preserve their hashes. Missing shared runtime files are `plugin-runtime-incomplete`, not permission to run as a detached Skill.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy package and art-direction plan, including their identical
   resource-inventory signature, and consume the hash-bound Art Direction-to-
   Output calibration. Build only with resources selected in that inventory;
   new assets or routes require Supervisor to revise, re-lock, and re-present
   the inventory first.
4. Read `references/runtime-routing.md`, `references/art-direction-handoff.md`, and `references/build-only-contract.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/expression-mode.md`, `references/relative-layout.md`, `references/layout-contract-compilation.md`, and `references/composition-plan-consumption.md`; they define approved-medium implementation, constraint-based regions, registered-contract compilation, and the Pattern decision boundary.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
7. Read the locale-matched `../clayz-presentation-supervisor/references/first-class-index-gate.md`. Reuse the one task Provider lock created before Logic and query the available Output learning sources with finalized receipts and adopt only relevant records. A required master, font, brand asset, or Index source that cannot be materialized on the selected host is a capability failure, not permission to substitute another identity. For identities listed by `theme.typography.font_validation.deferred_font_identities`, treat each canonical family and its aliases as one font, then follow the deferred-native cloud policy below instead of pretending the cloud renderer owns the full font.
8. Resolve optional Output capabilities through the built-in Capability Index. On ChatGPT, use `native-presentation-tool` only when task preflight locked it as the single provisional/attemptable route and its challenge-bound host declaration covers every required capability; that declaration does not establish readiness. The Output attempt must produce independently inspectable PPTX objects. When a render route is available and selected, it also produces final renders; when no render route is available or it is deliberately unselected, record `deferred`/`not-run` coverage and continue with the written PPTX. Only a failure to write or inspect any PPTX is a hard route failure to Supervisor. Use `renderer-pptxgenjs` only when that renderer is explicitly selected and available; use `technical-drift` or `repair-loop` only when the written artifact actually drifts from the approved plan.

   In calibrated runs, `attemptable=true` with `available=false` can describe a
   real writer whose fidelity, font, render, or other configured capability is
   still unverified. Read the full preflight `missing_capabilities` as pending
   evidence and continue the single locked Output attempt; do not turn an
   unobserved static capability into an unsupported verdict. If the configured
   theme names a user master, load and use that master for the attempt and
   preserve its layout/theme dependencies. A baseline adapter that writes a
   blank presentation cannot claim master inheritance. Record an observed load,
   write, inspection, or fidelity failure when it occurs, and leave unknown
   conditions pending until Output or the Auditor has evidence.
9. Load only optional `knowledge_refs` returned by selected capability records. Keep capability, Layout Contract, Composition Pattern, linked Failure Pattern, and retrieval receipt IDs as task-local evidence; unresolved signals never justify pretending renderer support, re-selecting a composition method, or inventing a repair method.

When the root supplies knowledge from a prior discussion, consume only the
complete verified committed revision selected through the existing Index and
the locked resource inventory. Preserve its confirmation and attachment
hashes, provenance category, evidence limits, applicability, and unresolved
questions in Output evidence. An attachment may be materialized only when its
stable ID, origin, rights, locator, and hash are verified; materialization does
not grant reuse or public-distribution rights. A draft, unconfirmed consensus,
or attachment outside that snapshot cannot be cited as committed learned knowledge.
Current task attachments remain usable under the normal task-input rules.
Output never creates or commits a discussion record during production.

## Consume the visual baseline

Inspect all locked drafts together with the specification before building.
Record `output_started_at` and `visual_baseline_sha256` in QA. Do not start
without a complete valid baseline or replace native pages with preview images.
Preserve editable text, data-bound charts/tables and editable diagram objects;
photographs remain image assets. Log permitted micro-adjustments; return
changes to content, hierarchy or composition to the responsible upstream stage.

## Workflow

Apply the shared artifact-led Library loop to the implementation plan: approved
visual intent -> concrete object/font/connector/capacity question -> Output
Library method -> revised implementation -> written-object and render check.
Inspect relevant implementation details, not only index metadata. Use a targeted
prototype when it resolves a material technical uncertainty before the full
build. Record which object behavior or rendered defect the reference improved.
The full deck follows the current approved Art Direction revision; do not reduce
it to familiar layout shells because they are easier to script. Return hierarchy
changes to Art Direction, text compression to Copy and page-scope changes to
Logic. Rebuild only after the responsible artifact and dependent bindings change.

1. Load the task acceptance contract, colors, typography, layout roles, optional master, renderer, target applications, delivery profile, and QA thresholds only from the resolved configuration.
2. Bind the acceptance typography and performance budgets before creating objects. Consume the one `runtime-preflight.json` created by root Supervisor before Logic; Output must not run a second preflight. Verify that its run ID, task-request SHA-256, task-root SHA-256, canonical issuance/consumption receipt hashes, and resolved-config SHA-256 match this run, then consume its locked authoring and render route without rediscovering tools or switching routes. Preserve `target_application_checks` as observations separate from the route gate: an unavailable target-native reopen check is deferred evidence, not a reason to stop Logic or authoring. If a hard route failure requires a fallback, return control to Supervisor so it can close the run and restart from a fresh bound preflight within the configured restart budget.
3. Verify the locked route satisfies every task-required authoring/rendering capability. Record unavailable capabilities instead of pretending support. Never add `*-reopen-render` target-acceptance capabilities to the route-required set merely because the application appears in `target_applications`. Renderer-specific optional guidance must have been resolved by Capability Index.
4. When Art Direction selected a registered Composition Pattern, verify the compiled Composition Plan and its receipts; consume its semantic mapping, constraints, expected visual effect, and failure guards without re-selecting the Pattern. Then, when Art Direction selected a registered Layout Contract, verify and compile it with `../../packages/layout/compile_layout_contract.py`; otherwise consume the explicitly approved core Layout Tree. Resolve approved relative regions with `../../packages/layout/solve_relative_layout.py`, then build editable objects from the resolved layout, area plan, and `copy_unit_map`. Output never selects or invents a Pattern or contract.
5. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory.
6. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved. When a user master is configured, attempt that actual master and preserve its layout/theme mapping; do not silently replace it with a generated blank theme because inheritance is not yet verified.
7. Collect source material in one bounded round and cache it task-locally. Before the first write, verify the complete slide-role sequence including cover and closing, master/layout dependencies, the required Storyline-to-master-placeholder binding, exact font names, copy-to-region capacity, intentional breaks, and internal object-collision risks. Never synthesize a smaller line beneath the Storyline merely because the master leaves room for one. Write the PPTX once. When the locked render capability is available and selected, reopen through that route, inspect package objects, run `../../packages/validators/audit_ppt_font_names.py` before rendering, render the selected final slide set and perform thumbnail plus full-size review. When rendering is unavailable or deliberately unselected, record `deferred` or `not-run` evidence and continue with the written PPTX; never claim render pass or invent pixels. Send the actual file, object and available render artifacts to Supervisor and the Independent Auditor; do not describe Output's own QA as an independent audit. Use `scripts/task_runtime.py check` to measure deterministic operations and reuse outputs only when their declared inputs and outputs still match. After a local repair, rerender affected pages when the route is available; master or global theme changes invalidate all affected pages. Final evidence must cover the final slide set when rendering is available, or state the exact coverage gap. For each configured target application, run native reopen/render only when that capability is available and selected within the bounded run; record available but unused targets as `not-selected`, unavailable targets as `deferred`, and executed targets as `pass` or `fail`. These states must flow into Supervisor's `environment_observation`. Resolve a deferred font identity against its canonical family plus aliases; one match satisfies the identity, and aliases never become fallback positions. Write the identity's exact `pptx_family` into both Latin and East Asian PPTX fields. `font-validation-pending` covers only native pixel acceptance and can never hide a wrong written family. When Office is selected, keep one process alive for the run instead of reopening the application per slide or check.
8. Run at most one targeted technical repair when the controlled-repair capability was resolved. Never let a repair loop rewrite content or art direction. Record write, render, repair, retrieval, and stage durations against the acceptance performance budget; an overrun is a reportable finding, not a silent loop.
9. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config <resolved-config.json>
```

10. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, runtime preflight, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
11. Emit the final PPTX, render evidence, object inventory, deviation log, font-name audit, and Output QA report with status `built` plus root `acceptance_contract`, `resource_inventory_lock`, and `index_evidence`. Verify each quantitative encoding against actual native chart/table/shape objects; a plan-object mismatch cannot be described away. Capture the written PPTX's actual slide count, object/media statistics, and per-slide visible text and speaker notes from the file when the runtime exposes them; distinguish extracted facts from planned intent and mark unavailable extraction as `not-recorded`. When deferred-native validation applies, include each identity's requested canonical family, matched installed name or `unavailable`, written-PPTX family counts, observed cloud renderer, diagnostic-only render status, and `font-validation-pending` acceptance state.
12. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.

## Validation

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass the exact bound `--config <resolved-config.json>` to policy-aware validators. A successful in-memory write is never a substitute for reopening the final file; when no render route is available, record the deferred/not-run render coverage rather than inventing a render result.

Send all artifacts to both `$clayz-presentation-supervisor` and the shared
Independent Auditor module. Output may stage the PPTX, but it must not present
the PPTX as the final user delivery. Supervisor consumes the immutable
`independent-audit/1.0` artifact, validates the report against the same
preflight and resolved config, and invokes `../../scripts/publish_supervised_pair.py`;
only that verified bundle may be handed off as the final PPTX, formal
`ppt-supervision-report.json`, and its deterministically derived Markdown report.

## Work record at handoff

Read the stage-work-record section of `../../packages/contracts/stage-enablement.md`. Save this stage's actual artifacts to immutable task-local revision files, record the work, calibration binding and real checks with `scripts/publish_supervised_pair.py record-stage --stage output`, and attach `work-notes` when implementation choices, actual PPTX/object/render statistics, extracted page text or speaker notes, target-application outcomes, or deviations need richer context. Verify the available record chain with `check-records` before handoff. Include the immediate predecessor record after Logic. Binding, identity, format or evidence-integrity failures cannot be replaced by a prose pass; quality findings may travel with explicit evidence. Missing extraction or notes remain `not-recorded`, `deferred`, or `uncertain` as applicable. Supervisor consumes the independent audit artifact, adds its coordination record and uses `assemble-report`; it must not invent prior work, alter audit findings or deliver a separate summary as the final report.

The central baseline is `../../config/default.json`; consume it through the unified merger with personal settings and task overrides, never as a separate production route.
