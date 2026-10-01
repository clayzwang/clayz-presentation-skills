# Research, content structure and visual handoff — v0.17.4

New runs use content package `3.2`, Art Direction plan `2.0`, and handoff extension `1.2`. Historical 2.4/3.0/3.1 artifacts retain their original validation and ownership; do not relabel an old file. Keep the five stages, calibrations, Independent Auditor, configuration, resource inventory, Index evidence and actual work records.

## Logic: research and research results

Logic investigates the subject and outputs a complete research report, independent of slide count or layout. Explain what the evidence establishes, how it was derived, competing explanations, implications and remaining uncertainty. Research conclusions belong here; the wording and placement of presentation conclusions belong to Copy. Research findings are not slide titles, a reading sequence or a checklist of work still to do. Retain detailed source material needed to understand and verify the findings.

The root `research` object contains `research_question`, `scope`, `summary`, `findings`, `data`, `sources`, `glossary`, `metric_dictionary`, `open_items`, and `invariants`. Findings contain `finding_id`, `question`, complete `text`, `claim_status`, `source_ids`, `qualifiers`, `must_preserve`, and `data_ids`. Findings can be grouped by research topic, but their array order does not prescribe presentation order. Sources bind `source_id`, selected `resource_id` and `locator`. Facts/calculations require source evidence. Data records retain `data_id`, `metric_name`, `display_value`, `raw_value` (null when unavailable), `unit`, `period`, `definition_ref`, `source_ids`, and `evidence_status`; calculations and limitations remain inspectable.

At `logic-approved`, `logic_layer` and `copy_layer` are null; `story` is absent/null. Logic must not allocate pages, write slide titles, fix presentation chapters, prescribe a cover/closing, or package research as final visible Copy. Brief/acceptance may retain the user's presentation requirements for Copy to implement. Topic labels and substantive research judgments are not forbidden; slide-organizing fields inside research are rejected.

## Copy: content structure and PPT-suitable text

Copy first reads the whole research, writes an independently understandable explanation, then chooses presentation chapters, page responsibilities, pagination, order, headings, opening/closing and on-slide conclusions. This handoff is a text/content document, not a PPTX or visual design. Copy may combine or split findings, change their order, edit wording and group content while preserving supported meaning, qualifiers, required coverage and user constraints. Layout pressure is never a reason to strengthen a claim or hide a necessary caveat.

Bind the original Logic file with `logic_artifact` (absolute path, SHA-256, bytes). Preserve `research`, brief, acceptance, inventory, package identity/version, configuration and run bindings verbatim. Use `copy_layer.pagination_owner: "copy"`, `research_sha256`, `logic_version`, Copy-authored `chapters` (chapter_id/title/purpose), `chapter_order`, `semantic_preservation_review`, and ordered `slides`. The compatibility slot `logic_layer` is now a **Copy-authored page projection**, marked `owner: "copy"`; it is never present in the Logic handoff. Its `slides` contain slide_id, chapter_id, narrative_role, a complete page claim, `source_finding_ids` and data records copied without alteration from research; `lock.slide_order_locked` binds Copy's approved order for downstream use.

Each Copy page contains slide_id, title_copy_id, optional storyline_copy_id, footnote_copy_ids and copy_units. Each visible unit carries unique copy_id, text, role, text_mode, source_finding_ids, parent_copy_id, sibling_group_id, nonnegative logic_level, order, render_separately:true, merge_with_children:false and intentional_line_breaks. These are content relationships, not a visual arrangement. Complete sentences can remain a single unit. Do not force parallel slogans or fragment causal explanations. Required findings must appear in visible content; notes cannot hide them. The semantic review must cite actual wording/coverage decisions and uncertainty, not merely assert that all fields exist.

Copy can optionally issue `presentation_requests` on a page: request_id, kind (`table`, `chart`, `logo`, `ordinal`, `image`, `diagram`, `other`), semantic purpose, relevant copy_ids/data_ids. A request states what the presentation should communicate or add, not its coordinates, chart encoding, final asset or visual geometry. It may ask for a table, chart, logo or numbering. Art owns the concrete presentation and records an accepted/adapted/declined disposition with reason; explicit user requirements remain binding.

Default cover/closing requirements are implemented by Copy. Pagination, chapter sequence, titles, conclusion wording and grouping changes return to Copy, without reopening research when the meaning is unchanged. New facts, calculations, changed research conclusions or unresolved evidence return to Logic. No default speaker notes or appendix. Optional Storyline stays optional unless the user-selected master requires it.

## Art Direction: presentation structure

Art decides how content is presented: paragraphs, tables, charts, diagrams, grouping, reading path, visual hierarchy, imagery, logos and numbering. Art may choose these even without a Copy request, using approved data and governed assets. Content grouping remains semantically intact but does not force one box per group or a table because the text was tabulated. Record each Copy request in that page's `presentation_request_resolutions` (request_id, status, reason).

Adding a logo or decorative ordinal is a visual decision, not a new research claim. Numbering must not imply an unsupported rank or sequence; a logo must not imply an unsupported relationship. Derived chart ticks, units or legends must retain the approved values and definitions. New explanatory prose goes back to Copy; new facts, calculations and judgments go back to Logic. Re-pagination goes to Copy. Art does not silently rewrite text or produce the final PPTX.

## Art Direction: image drafts and matching visual specification

Use actual approved Copy to design the complete deck, including every opening,
body and closing page. First establish hierarchy, grouping, relationships,
first visual, reading path, medium and rhythm. Produce a readable PNG/JPEG image
draft of **every page**, then refine the visual specification from those drafts.
Iterate and reconcile both before handoff. The drafts need not be native or at
delivery resolution, but text, numbers and relationships must be readable and
correct. Inspect all pages; a thumbnail, blank placeholder or approximate-text
mockup is not a completed baseline. No universal pixel size or similarity score
can replace this professional judgment.

Drawing/rendering tools and image generation are both allowed. Image generation
does not authorize corrupt text, invented data or changed relationships. Keep
approved Copy and source data as truth; do not OCR/re-infer them from images.
The complete draft requirement is independent of optional A/B capability. If
draft creation is unavailable, report the specific missing handoff; never
silently substitute the old text-only route or fabricate a preview.

Plan 2.0 retains the existing semantic design fields and adds `visual_baseline`:

- `status: "locked"`, timezone-aware `locked_at`, canonical
  `copy_package_sha256`, and `spec_sha256` (whole plan excluding visual_baseline);
- ordered `slides` exactly matching Copy, each with `slide_id`, actual `image`
  file reference, `first_visual`, `reading_path`, `legibility_review`,
  `copy_and_data_review`, `spec_consistency_review`, and `elements`;
- every element has `element_id`, `kind`, semantic `purpose`, `copy_ids`,
  normalized `[x,y,width,height]` `box`, `native_type`, `group_id`, `alignment`,
  `locked_properties` and numeric/bounded `allowed_adjustments`;
- text elements have `typography` including the resolved `font_family`,
  `size_pt` and necessary color/weight/spacing. Bind charts to `chart_type` and
  approved `data_ids`; images/icons require a governed `asset_ref`, crop and
  placement information as applicable. Added symbols/decorations get IDs too;
- every visible Copy unit maps exactly once. Content rendered as chart labels
  still maps to an element; it is not silently omitted from verification.

Reusable composition patterns remain semantic/coordinate-free. The **task
specification** now owns target coordinates, typography and adjustment bounds,
all resolved from the active configuration/master. Output does not invent these.
New labels return to Copy; new calculations/claims return to Logic.
Use `scripts/stage_documents.py lock-design` to finalize the hashes/time into a
new immutable plan file, then the normal Art Direction validation and work record.
Never lock a preview made from the final Output PPTX after the fact. If design
changes, create a new revision and invalidate affected downstream evidence.

## Output: native implementation

For package 3.2, `storyline_single_line` is not a required QA check. A supplied historical check remains valid with its existing status/evidence rules; 2.4/3.0 validation is unchanged. Honor only explicit Storyline constraints of a user-selected master.

Read both the locked images and specification. Record `output_started_at` and
canonical `visual_baseline_sha256` in QA before authoring. Apply the active
master and reproduce the design using editable text, native data charts/tables
and editable diagram objects where specified; photos remain image assets.
A whole-page bitmap is not an editable implementation. Technical adjustments
must stay within declared bounds and be recorded; content, hierarchy or
composition changes return to the owner. Reopen the actual final PPTX and render
it when the route is available. Preserve explicit deferred checks otherwise.

## Supervisor and Independent Auditor

Keep the existing handoff/calibration/independent-audit sequence. Compare final
PPTX renders to Art Direction's locked drafts, never to a retrofitted design.
`design_comparison` in the Supervisor draft binds `visual_baseline_sha256`,
actual final `pptx_sha256`, and ordered `slides`. Each page binds `slide_id`,
`preview_sha256` and either:

- `status: "reviewed"`, real `final_render` file reference,
  `rendered_from_pptx_sha256`, and four checks: `content`, `visual_fidelity`,
  `native_editability`, `design_quality`; each has `status` and concrete
  `observation`. Failed/uncertain checks add report `issue_ids` and
  `earliest_owner` (`logic`, `copy`, `art-direction`, `output`);
- `status: "deferred"` with `reason` when final render inspection cannot run.
  This does not waive Art Direction drafts or permit a clean/visual-pass claim.

Check actual objects for editability; visual comparison alone cannot prove it.
A matching bad design is still a design finding. Record downstream detection
failures without moving primary responsibility. Preserve independent findings,
delivery policy and professional judgment; pixel identity is not the goal.

`assemble-report` derives `stage_documents` from the **actual** immutable Logic
file, Copy package and Art Direction plan. It embeds full structured contents,
deterministic readable Markdown and the locked image bytes. Final render bytes
are embedded alongside the comparison. Do not write independent summaries and
call them original handoffs. The existing atomic publisher retains the formal
PPTX/report pair and exports `stage-handoff.zip` as a derived companion containing
the three documents, images and a portable side-by-side comparison HTML.

Historical 2.4, 3.0 and 3.1 content packages retain their original replay validation.
New tasks on v0.17.4 use 3.2/2.0. Bindings, coverage and files are machine checked;
reasoning, wording, readability and design remain professional judgments.
