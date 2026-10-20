---
name: clayz-presentation-output
description: Build and verify an editable PPTX from a copy-approved package and art-direction-approved plan using the centrally configured theme, renderer, compatibility targets, delivery profile, and attribution metadata. Use for final presentation production, technical repair, media optimization, font and compatibility checks, and render-grounded QA. Do not invent content or redesign an approved composition.
---
## v0.20.5 current repair policy

The selected `consolidated-once` policy controls all reader return routes: Copy readers together → one Copy repair → both original readers confirm; final reader → one Art/Output repair → same reader confirms. Independent Auditor records only. Residual/new issues are reported, never another repair dispatch. Historical pass-until-clean or repeated returns below apply only to legacy `strict-pass`. See `../../packages/contracts/reader-cycle.md` from the plugin root.



# Clayz Presentation Output

## v0.20.2 Art cognition and audited changes

The current [Art cognition contract](../../packages/contracts/art-cognition.md) extends earlier fidelity instructions: preserve original Logic/Copy, but allow Art to revise meaning, argument, sequence and pagination without advance modification requests. Record actual presentation in `art_content`, conclusions/actions and selected knowledge in `art_cognition`. Output implements that recorded presentation. Independent final reading first sees only renders, then compares original Copy and every documented Art change. Difference alone is not failure; justification, accuracy, completeness and reasoning determine the audit result. Older “unchanged Copy” or “return wording/pagination to Copy” instructions apply only when no Art projection exists. New Art work covers A01—A11; these are cognitive results, not agents or approval gates.


Build the approved deck faithfully, preserve editability, and prove the written
PPTX matches its contracts. Consume Art Direction's artifact and the
Supervisor calibration as separate inputs; send the completed evidence to both
Supervisor and the shared Independent Auditor module.

## Current production boundary (v0.20.1)

Follow [reader review](../../packages/contracts/reader-review.md), with the current reader-cycle contract for bounded repair and original-reader confirmation. Logic explicitly supplies substantive research conclusions. Copy completes text before separate title and content readings against Logic. Art starts after the closed Copy cycle, including both original-reader confirmations when repaired; Output follows approved Art. Final reading compares actual pages to approved Copy and routes one consolidated repair to Art or Output, followed by confirmation by the same final reader. Record/receipt formatting repairs never require regenerating the deck. Upload is only a separately requested action.

## Production reliability (v0.17.6)

Read `../../packages/contracts/production-reliability.md` (or its `.zh-CN.md` peer). It supersedes older automatic font-size and consecutive-composition gates and inline report transport. Art owns rendered legibility and repetition; Output and Supervisor own editable delivery and PPTX size.

For v0.17.6, implement every tabular presentation as an integrated native table; return a medium change to Art when that is unavailable. Verify fonts inside native tables and charts, including Latin text and digits, using the current font audit and actual renders. Reserve approximately 10% internal usable capacity in text boxes and shapes under `layout.internal_content_reserve_ratio`; check internal overflow and object collisions as well as slide bounds and record PowerPoint/WPS coverage separately. See the production-reliability contract for the capacity definition.

## Reader understanding (v0.17.1)

Read `../../packages/contracts/reader-quality.md` or its `.zh-CN.md` peer
according to the task locale. Necessary explanation and evidence fidelity take
priority over shortness; use existing records for review observations.

Preserve the complete approved wording, including causal/comparison links
and qualifiers. Do not silently abbreviate, shrink illegibly or move necessary
body explanation into notes to solve overflow. Realize approved adjustments or
return the specific capacity problem to Art Direction/Copy with evidence.

## Research and visual handoff (v0.17.4)

Before authoring, read `../../packages/contracts/story-visual-handoff.md` (or
`story-visual-handoff.zh-CN.md` for zh-CN). New runs use package 3.4 and Art
Direction plan 2.3. The complete research, Copy content document, complete image drafts, visual tags and
report documents apply even when optional Library or A/B capabilities are absent.
Legacy page-first contracts remain readable only for existing runs. Preserve
the existing Supervisor calibration and Independent Auditor handoffs.

## Page planning consumption — v0.19.0

Read the actual Art planning under locale-matched
`../../packages/contracts/page-planning.md` together with complete images and
object specifications. It explains content grouping, hierarchy, meaningful
shape/line/type functions and grounded additions. Implement the locked objects
and native editing boundaries; unresolved meaning returns to Copy, necessary
composition changes return to Art. Preserve the planning source rather than
inventing a design rationale during implementation.

## Boundaries

### Local r08.1 — choose implementation from the locked native prototype

When Art supplies a hash-bound, editable native prototype, inspect that file
and its actual object properties before choosing to regenerate it. Check the
writer's coverage of the current specifications, including paragraph spacing,
text/table vertical anchors and connector endpoints when those are present.
A helper that handles only some fields cannot establish fidelity for the rest.
Adopt the verified native objects when that preserves the complete locked
design, or implement the missing properties explicitly. This choice does not
waive Output's final write, reopen, native comparison and actual rendering.

Keep native-object fidelity, visible clipping and text-metric capacity results
separate in the existing QA. A PDF font metric box is not a pixel-ink measure;
an uncut glyph in an image does not erase a recorded usable-capacity failure.
Retain the known result and the task's bounded repair policy rather than
regenerating unchanged pages to obtain a clean check. This is an implementation
action, not a new gate, font substitution or change to the approved content.

Own native object creation and technical coordinate realization within Art Direction tolerances, groups, charts, tables, SVG, media preparation, theme application, compatibility repair, package optimization, artifact metadata, and final write/reopen/render QA when the locked render route is available. Record deferred/not-run coverage when it is not.

Do not change approved text, data, relationships, page sequence, composition, or visual intent. Return material conflicts upstream with evidence.


### Local r10.1 — revision-safe evidence and truthful handoff

Before running a revision script, enumerate its new writable outputs, including
command receipts, glyph/size/rhythm evidence, failure logs and manifests. Assign
the current revision to each and refuse any existing path; a filename left in a
reused script can destroy history even if the main deck is versioned. Use
`../../scripts/output_evidence_io.py`'s `ensure_new_paths` before invoking tools and
`write_new_json` for author-owned receipts, or equivalent exclusive-create
semantics. Inputs may be reused; previously written evidence is never an output
slot. Preserve original failures and save record corrections under a new path.
If an overwrite happens, restore only from a real hash-bound copy, record the
incident and distinguish unrecoverable bytes; never regenerate plausible history.

Before writing the stage execution declaration and formal work record, consume
the actual current original-validator result and process return code. Explicitly
check completed execution, record validity and the quality status being claimed.
A present JSON file, zero wrapper return, completed record chain or an intended
pass does not establish successful quality verification. Use `verification_observation`
and `require_verification` from the same helper to bind those observations; they
do not replace or change an original validator. A valid fail/unverified result
may be handed off accurately as such; a tool error cannot be recorded as pass.
For record-only validators, require completed/valid but preserve quality=unverified.
A formatting or import-path correction needs a new result and corrected handoff,
not another PPTX write or deck render. Keep the actual task render total, including
Art previews where counted, visible alongside the current Output count.

## Required context

Read `../../packages/contracts/stage-enablement.md` for task authority, relevance-based retrieval, professional review, and measured execution. It supersedes legacy requirements to select every source, rediscover unchanged resources, or treat aesthetic heuristics as mandatory gates.


1. Validate the complete composite Skill root with `../../scripts/validate_composite_skill_mount.py`, then consume the root's v2 task selection and merged `task-config.json`. If missing, return to root to prepare the unified configuration once; never choose a different config because a Personal Runtime is installed. Resolve selected masters and assets through actual observed file references and preserve their hashes. Missing shared runtime files are `composite-skill-runtime-incomplete`, not permission to run as a detached Skill.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy package and art-direction plan, including their identical
   resource-inventory signature, and consume the hash-bound Art Direction-to-
   Output calibration. Build only with resources selected in that inventory;
   new assets or routes require Supervisor to revise, re-lock, and re-present
   the inventory first.
4. Read `references/runtime-routing.zh-CN.md`, `references/art-direction-handoff.zh-CN.md`, and `references/build-only-contract.zh-CN.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/expression-mode.zh-CN.md` for native implementation. Read relative-layout, layout-contract-compilation or composition-plan-consumption only when Art actually supplied that optional tool's artifacts; new runs do not require a registered contract, pattern or layout tree.
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

For a later correction to observation prose, it can be useful to keep a dated
supplement linked to the original record. Distinguish when the visual baseline
was actually formed from when its description was corrected. An unchanged
design need not be rebuilt to repair a receipt; preserve its real baseline and
the later correction rather than treating the correction as a new design event.

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
4. Implement Art's locked visual specification directly. An externally supplied Pattern, Layout Contract or Layout Tree is optional; use its compilation tools only when actually selected by Art. An absent pattern or tree does not require a fallback. Preserve Art's native mappings, shared text ranges and independently chosen styles and reading paths.
5. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory. Preserve Art's selected emphasis ranges across manual visual lines. If constructing runs from an approved logical paragraph, use `../../packages/layout/text_emphasis.py:project_emphasis` with its exact text, lines and selected source intervals; never infer ranges with per-line whole-phrase matching. Compare actual run styles and final pixels to the locked Art. A discovered omission already present in the locked design remains an upstream finding; Output cannot silently add emphasis.
6. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved. When a user master is configured, attempt that actual master and preserve its layout/theme mapping; do not silently replace it with a generated blank theme because inheritance is not yet verified.
7. Collect source material in one bounded round and cache it task-locally. Before the first write, verify the complete slide-role sequence including cover and closing, master/layout dependencies, any Storyline-to-placeholder binding explicitly required by a user-selected master, exact font names, copy-to-region capacity, intentional breaks, and internal object-collision risks. Never synthesize a smaller line beneath the Storyline merely because the master leaves room for one. Write the PPTX once. When the locked render capability is available and selected, reopen through that route, inspect package objects, run `../../packages/validators/audit_ppt_font_names.py` before rendering, render the selected final slide set and perform thumbnail plus full-size review. When rendering is unavailable or deliberately unselected, record `deferred` or `not-run` evidence and continue with the written PPTX; never claim render pass or invent pixels. Send the actual file, object and available render artifacts to Supervisor and the Independent Auditor; do not describe Output's own QA as an independent audit. Use `../../scripts/task_runtime.py check` to measure deterministic operations and reuse outputs only when their declared inputs and outputs still match. After a local repair, rerender affected pages when the route is available; master or global theme changes invalidate all affected pages. Final evidence must cover the final slide set when rendering is available, or state the exact coverage gap. For each configured target application, run native reopen/render only when that capability is available and selected within the bounded run; record available but unused targets as `not-selected`, unavailable targets as `deferred`, and executed targets as `pass` or `fail`. These states must flow into Supervisor's `environment_observation`. Resolve a deferred font identity against its canonical family plus aliases; one match satisfies the identity, and aliases never become fallback positions. Write the identity's exact `pptx_family` into both Latin and East Asian PPTX fields. `font-validation-pending` covers only native pixel acceptance and can never hide a wrong written family. When Office is selected, keep one process alive for the run instead of reopening the application per slide or check.
8. Run at most one targeted technical repair when the controlled-repair capability was resolved. Never let a repair loop rewrite content or art direction. Record write, render, repair, retrieval, and stage durations against the acceptance performance budget; an overrun is a reportable finding, not a silent loop.
9. Stamp documented, removable clayz provenance into custom document properties:

```bash
python ../../scripts/stamp_pptx_metadata.py <deck.pptx> --config <resolved-config.json>
```

10. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, runtime preflight, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
11. Emit the final PPTX, render evidence, object inventory, deviation log, font-name audit, and Output QA report with status `built` plus root `acceptance_contract`, `resource_inventory_lock`, and `index_evidence`. Verify each quantitative encoding against actual native chart/table/shape objects; a plan-object mismatch cannot be described away. Capture the written PPTX's actual slide count, object/media statistics, and per-slide visible text and speaker notes from the file when the runtime exposes them; distinguish extracted facts from planned intent and mark unavailable extraction as `not-recorded`. When deferred-native validation applies, include each identity's requested canonical family, matched installed name or `unavailable`, written-PPTX family counts, observed cloud renderer, diagnostic-only render status, and `font-validation-pending` acceptance state.
12. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.

## Validation

For each deferred identity with a configured `font_asset`, materialize that
exact font file and pass `--font-file <canonical-family-or-alias>=<path>` to
the font-name audit with the resolved config. The default STKAITI.TTF is
Version 1.02 and is pinned by SHA-256 and byte length. A same-name file is
not equivalent: missing bytes yield `deferred`, mismatched bytes yield
`fail`. Before rendering, register/load the verified file and record the
renderer-resolved path and hash. File identity alone does not prove the
renderer used it or that native PowerPoint/WPS acceptance passed. Keep
uploaded font binaries in private task/host assets, outside the public
source and release bundles.

Run the object, typography, rhythm, size, deviation, and final-QA validators from `../../packages/validators/`. Pass the exact bound `--config <resolved-config.json>` to policy-aware validators. A successful in-memory write is never a substitute for reopening the final file; when no render route is available, record the deferred/not-run render coverage rather than inventing a render result.

Send all artifacts to both `$clayz-presentation-supervisor` and the shared
Independent Auditor module. Output may stage the PPTX, but it must not present
the PPTX as the final user delivery. Supervisor consumes the immutable
`independent-audit/1.0` artifact, validates the report against the same
preflight and resolved config, and invokes `../../scripts/publish_supervised_pair.py`;
only that verified bundle may be handed off as the final PPTX, formal
`ppt-supervision-report.json`, and its deterministically derived Markdown report.

## Work record at handoff

Read the stage-work-record section of `../../packages/contracts/stage-enablement.md`. Save this stage's actual artifacts to immutable task-local revision files, record the work, calibration binding and real checks with `../../scripts/publish_supervised_pair.py record-stage --stage output`, and attach `work-notes` when implementation choices, actual PPTX/object/render statistics, extracted page text or speaker notes, target-application outcomes, or deviations need richer context. Verify the available record chain with `check-records` before handoff. Include the immediate predecessor record after Logic. Binding, identity, format or evidence-integrity failures cannot be replaced by a prose pass; quality findings may travel with explicit evidence. Missing extraction or notes remain `not-recorded`, `deferred`, or `uncertain` as applicable. Supervisor consumes the independent audit artifact, adds its coordination record and uses `assemble-report`; it must not invent prior work, alter audit findings or deliver a separate summary as the final report.

The central baseline is `../../config/default.json`; consume it through the unified merger with personal settings and task overrides, never as a separate production route.

## v0.18.2 implementation boundary

New runs use content package 3.4, Art plan 2.3 and QA 4.1. Implement Art's
locked drafts/specifications without inheriting old Copy atomicity, parent-target,
sibling-style or reading-order rules. Several Copy IDs may occupy one editable
text object or native cell through disjoint native_location.text_range bindings.
Verify each approved text range and actual complete coverage. Art chooses styles
and visual reading_sequence independently of textual heading levels and Copy array
order. No registered Pattern, Layout Contract or semantic tree is required.
Use such tools only when Art actually supplied them; optional absence is valid.
The current story-visual-handoff contract supersedes historical field examples.

Preserve Art's editing boundaries: each baseline element's native_name,
render_separately:true, native type and optional native_group_path. Create
separate native children inside declared groups. Do not merge, split, regroup
or flatten objects for convenience; return boundary changes to Art. Inspect
real final PPTX objects with compare_package_to_pptx.py as well as text ranges.

Read `../../packages/contracts/verification-outcomes.md` or its `.zh-CN.md` peer.
Use `--result-json <path>` on native comparison, Output QA and deviation-log
validation to retain automatic execution/integrity/quality diagnostics with the
existing command evidence. Do not interpret an exception as a quality finding,
or rewrite declared fail/deferred/uncertain results as pass to satisfy a record.
Fix affected tool/input causes, rerun affected checks and preserve earlier output.
The deviation-log validator's record pass is not a PPTX quality verdict.


## Native production checks

For native production, also read `../../packages/contracts/local-development-gates.zh-CN.md`. Apply actual native preview, inspectable knowledge parameters, table-cell and footer checks, bound visual evidence, and stale-record rejection. The current external knowledge pack is stored and versioned separately; read its top-level learning philosophy when selected. Preserve failed readings and disclose actual Auditor context and unobserved target applications.


### Local r11.1 — preserve destination identity when restoring page fields

When a targeted prototype returns to full-deck order, restore the approved
slide-number text body into its existing destination shape; do not clone the
whole source shape with its slide-local cNvPr ID. `../../scripts/native_slide_number.py`
provides a narrow `restore_slide_number_field(target, source)` helper: it keeps
the destination ID/name/geometry, requires an automatic slidenum source and
matching geometry/style, and refuses relationship-bearing text. Other cloning
cases still need their own relationship and identity handling. Inspect actual
written IDs and reopen the exact final PPTX; unchanged parts or a mixed PDF do
not replace a required full-file reopen.

`write_new_json` in `../../scripts/output_evidence_io.py` serializes Path values as
paths but still rejects unknown objects before opening the output. Keep actual
process exit/status assertions; this helper is transport, not a validator.

When reusing an already executed render, the same module's optional
`derive_render_manifest(raw_manifest_path, pptx_path, evidence_role=...,
provenance_clarification=...)` returns a new binding with the existing reader
contract's `pptx_sha256`. It checks the raw manifest's bound input against the
actual supplied PPTX and retains raw limitations, page order and file references.
Describe the actual role explicitly: use formal Output evidence only for the
actual formal input and export, not by relabeling an Art prototype. This helper
does not render, establish that role, change quality states or waive original
consumer checks. Preserve the raw receipt and write any derivative as a new
revision; a binding repair alone does not call for a new native save or render.

### Local r12.1 — consume actual native text properties

When consuming Art's native text or table objects, distinguish cell tcPr padding
from TextFrame bodyPr margins. Inspect the written effective properties rather
than assuming a shared text helper set both. `../../scripts/native_text_revision.py`
provides an explicit cell/TextFrame margin operation and config-bound size
resolution for authoring; it does not waive approved-Art entry, permit Output
to reflow Art's text, or replace original validators and native checks.

### Local r13.1 — preserve the approved font and paragraph space

The Art-preview helper now requires explicit `font_file` and `font_family`;
when it is used for a permitted native probe, also pass the existing
`fontconfig` path (CLI: `--font-file … --font-family … --fontconfig …`).
Do not use the old positional-only call. Reuse the approved runtime's file and
family; its fontconfig must reach the actual child process, not only a parent
shell. A pre-conversion identity receipt and the resulting PDF font/glyph
inspection answer different questions. Final Output still follows the locked
route and its original evidence requirements; a preview cannot replace them.

Read approved paragraph marL/marR as well as effective cell/TextFrame padding.
`native_capacity` can describe a fixed object from its actual native properties
and supplied measured run widths/height, without shrinking text or declaring
quality. Existing paragraph edge space consumes capacity and must survive
implementation. Output cannot add or remove it to redesign unapproved Art;
return an implementation discrepancy through the existing stage boundaries.


### Local r17.1 — separate line-break fidelity from design preference

Preserve the locked Art line breaks and emphasis. When checking Chinese text,
distinguish missing characters, clipping, broken numeric/symbol combinations
and implementation deviations from an ordinary inter-character line break.
The latter alone does not establish a defect. A concrete ambiguity or hard-to-
track relation is a design observation to route to Art within the existing
return budget, not permission to silently reflow the deck. Keep actual
observations and unresolved findings even when the reader understands the page.

### Local star50.r02.1 — preserve the actual authored entry and color roles

Neutral page creation does not authorize Output to add a conventional title band,
short rule or fixed top gap. Consume Art's explicit title/body positions and
selected layout; retain genuine user-master inheritance. When adopting native
objects, preserve independently authored data-mark and identifying-text colors.
Do not restore a pale swatch's color onto the label because a helper exposes one
shared foreground parameter. Actual editable properties, page images and reader
understanding remain separate evidence; no new color or page-layout gate applies.

### Local star50.r03.1 — preserve authored groups without new reflow

Consume Art's actual selected lines, typography and object geometry. Optional
author-selected `protected_terms` belongs to the existing preparation call in
`packages.layout.text_flow.wrap` / `authoring_text.measure_lines`; native helpers
must pass that choice when used, not substitute a topic-wide dictionary.
The existing date/number/Latin atoms remain intact when choices overlap them.

Do not add a wrapping engine to the manifest adapter or reflow an already locked
native prototype to apply a later preference. Compare actual final text, line
breaks, native properties and pixels. An overwide protected group returns to
Art's current spatial decision, rather than justifying smaller type, hidden
joiner characters or changed approved wording. Successful grouping does not
clear unmatched PDF lines, capacity diagnostics or unobserved target behavior.

### Local star50.r04.1 — preserve explicit native endpoint scope

Implement the locked relation and geometry without automatically attaching every line or adding frames. When Art explicitly selects the optional `packages.layout.native_connector.attach_rectangular_connector`, validate its direct-slide rectangle/site scope before touching either endpoint. The helper uses the library's existing experimental connection methods; it does not route lines or monitor later property edits. Preserve separate arrowheads/labels as separate objects, and do not infer that they follow a bound connector. Reopen the written native file and observe its actual render; native id/site references, coordinate coincidence, GUI drag behavior and reader-visible correspondence require separate evidence. Existing validators, capacity diagnostics and bounded return remain unchanged.


### Local star50.r05.1 — preserve chart-label scope and actual visibility

Consume Art's actual point-label wrapping, literal text and placement decisions, including external annotations when selected. `packages.layout.native_chart_text.set_point_label_wrapping` is an optional identity-checked integration for existing custom labels only; preserve automatic labels as automatic rather than creating fixed text just to control wrapping. The helper changes no data/style/geometry and reports authorship, not fit. Reopen and view the actual written chart: ordinary TextFrame/grouping checks do not cover internally allocated chart-label space, and individually fitting neighbours may obscure each other. Retain the exact font audit, existing PDF-label observer scope and original QA thresholds. A manual label's future workbook update behavior remains unverified unless actually exercised; no universal nowrap, automatic shrinking, extra render cycle or gate is introduced.


### Local star50.r06.1 — preserve native endings and separate objects

Preserve the approved connector's headEnd/tailEnd style and selected inheritance state as part of its existing native line, not as another object. `packages.layout.set_connector_line_ends` is optional; omitted ends, explicit none and removal to inherit are distinct author choices. Keep authored independent triangles and labels independent when that is the locked design; do not silently migrate or remove them. Inspect actual line geometry after an explicit reattachment before positioning separate objects. Reopen and view actual positive/reversed/flipped directions where used; native marker ownership does not prove semantic direction, label association or GUI movement. Existing QA, edit boundaries and finite repair remain unchanged.
