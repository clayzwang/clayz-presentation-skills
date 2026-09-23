# Story and visual handoff — v0.17.0

Read for every new presentation run. This is the current cross-stage contract,
using package `3.0`, Art Direction plan `2.0`, and handoff extension `1.0`.
It changes artifact ownership without changing the five stages, Supervisor's
three calibration handoffs, Independent Auditor, task commitments, configuration,
Library/Index or publication authority. Read the Chinese peer for zh-CN tasks.

For language and substantive-content review, also read [reader-quality guidance](reader-quality.md). Prefer a sufficient natural explanation to premature compression; review real passages through existing stage records. This adds no schema, word-count gate or extra approval stage.

## Logic: a complete argument, before pages

Write a coherent narrative that can be read without a slide deck. Choose an
argument suited to the task: chronology, diagnosis, comparison or proposal are
possibilities, not prescribed templates. Include actual substantive paragraphs,
evidence, mechanisms, qualifications, transitions and a conclusion. An outline,
slide title list or collection of schema labels is not a complete story.

The original Logic JSON contains `contract_version: "3.0"`, the existing package
identity, version, status, acceptance contract, brief, resource inventory,
approvals and Index evidence. Set `logic_layer` and `copy_layer` to null.
Its authoritative `story` contains:

- `title`, `thesis`, `audience`, `desired_outcome`, `opening`, `conclusion`;
- `sources` using existing source IDs, selected resource IDs and locators;
- `glossary`, `metric_dictionary`, `open_items`, `invariants`;
- ordered `chapters`, each with stable `chapter_id`, `title`, `purpose`,
  substantive `blocks`, and a `transition` (including a closing transition);
- each block has stable `story_id`, full `text`, `claim_status`, `source_ids`,
  explicit `qualifiers` and boolean `must_preserve`.

Claims, calculations and evidence retain their original status and definitions.
Use the existing source/calculation evidence facilities; prose does not replace
them. Logic owns chapter/argument order and semantic invariants, not fixed page
boundaries. Preserve user page constraints for Copy. Save the real approved
Logic revision before Copy begins and record it with the existing stage recorder.

## Copy: pagination and structured presentation language

Read the whole story, choose page boundaries and hierarchy, and write exact
presentation text. Parallel construction, rhythm and slogans are optional
language techniques, subordinate to accuracy and audience understanding.
Spatial alignment belongs to Art Direction. Split or combine pages within the
approved argument; return changes to evidence, meaning or chapter order to Logic.

The Copy package preserves `story`, `brief`, `acceptance_contract`, source
inventory and package identity from Logic. `logic_artifact` is an absolute
task-local `{path, sha256, bytes}` reference to the actual original Logic file.
`copy_layer` adds `pagination_owner: "copy"`, canonical `story_sha256`,
`chapter_order` and a substantive `semantic_preservation_review` covering
numbers, qualifiers, coverage and relationships. Its existing page/copy-unit
structure remains editable by Copy; every visible unit and note adds nonempty
`source_story_ids`. Required blocks must appear in visible copy or explicitly
traced speaker notes. Do not hide a necessary visible caveat in notes merely to
pass coverage. Review semantic fidelity; hashes do not prove paraphrase quality.

### Compatibility projection, not a second Logic document

After pagination, Copy populates `logic_layer` with the existing v2.4 semantic
page data consumed by existing layout/render tools: slide IDs, page message
trees, slide claims/data/relationships, narrative and cross-page invariants.
That field is a **Copy-owned derived page projection** in package 3.0. Its
sources, glossary, metric dictionary and open items exactly preserve `story`.
Its page-order locks begin at Copy approval. It never replaces the original
Logic artifact or transfers substantive reasoning authority to Copy.
The old v2.4 field reference documents its shape; new Logic does not create it.

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

Historical 2.4/1.7 artifacts remain readable. New tasks on v0.17.0 use 3.0/2.0;
legacy validation is not permission to skip story or visual evidence. Validators
check bindings, coverage and files; reviewers still judge reasoning, wording,
image readability and design quality.
