# Story, page allocation and visual handoff — v0.17.2

New runs use content package `3.1`, Art Direction plan `2.0` and handoff extension
`1.1`. Preserve the five stages, calibration, Independent Auditor, configuration,
resource inventory, Index receipts and actual stage work records.

## Logic: complete story and page allocation

Write a complete substantive narrative in `story`: title, thesis, audience,
desired_outcome, opening, conclusion, ordered chapters (chapter_id, title,
purpose, blocks; transition optional), sources, glossary, metric_dictionary,
open_items and invariants. Each block has story_id, full text, claim_status,
source_ids, qualifiers and must_preserve. Facts/calculations bind selected
resources and source locators; retain definitions and uncertainty.

Write `logic_layer.slides` in page order, with slide_id, chapter_id, narrative_role,
claim, source_story_ids and data. Allocate every story block without trimming it.
Logic owns the thesis, chapters, page claims, page responsibilities and body-page
count. Set `logic_layer.lock.slide_order_locked: true`; `copy_layer` remains null.
Default to one cover and one closing page unless the user explicitly omits them.
Final bookend text belongs to Copy. Art Direction should favor fitting illustrative
imagery when useful, size/crop/compress it for its placed resolution and budget,
and keep text native. A whole-slide picture is not native generation.

No built-in analytical route, parent/child reasoning contract or sibling quota
applies. Methods come from the task, personal settings or selected external knowledge.
No stage proactively generates speaker notes or appendices; requested or historical
notes remain readable. Existing research/work records are retained.

## Copy: wording, trimming and content tags

Read the complete story and preserve its original content and page allocation.
Bind `logic_artifact` to the actual original file using absolute path, sha256 and
bytes. Preserve story, logic_layer, brief, acceptance_contract, resource_inventory
and package identity exactly. Changes to page order/count/responsibility or meaning
return to Logic. Copy owns exact text, trimming and content grouping on each page.

`copy_layer` contains logic_version, pagination_owner: "logic", story_sha256,
chapter_order, semantic_preservation_review and ordered slides. Each page has
slide_id, title_copy_id, optional storyline_copy_id and footnote_copy_ids, and
copy_units. Each visible unit has globally unique copy_id, text, role, text_mode,
source_story_ids (within that page allocation), parent_copy_id, sibling_group_id,
nonnegative logic_level (Copy hierarchy), order, render_separately: true,
merge_with_children: false, intentional_line_breaks. Null parent/group tags are
valid. Copy decides grouping and wording without old Logic node mappings;
node_copy_map and source_logic_node_ids are historical optional fields, not
new-run requirements. Do not add a grammar or grouping quota. Required story
content remains visible; supplied notes are traceable but cannot hide required
visible caveats. Review actual fidelity through semantic_preservation_review.

Art Direction's visual_layers use Copy IDs as node_id in 3.1 and its existing
page_message_tree_depth records the Copy hierarchy depth. logic_statement binds
the page claim. Content density and attention are Art Direction judgments, not
mandatory Logic labels. The copy_unit_map and semantic_layout_tree retain the
Copy grouping; visual_baseline adds real visual tags. Output implements them.

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

Historical 2.4 and 3.0 content packages retain their original replay validation.
New tasks on v0.17.2 use 3.1/2.0. Bindings, coverage and files are machine checked;
reasoning, wording, readability and design remain professional judgments.
