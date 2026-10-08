# Research, clean text and visual handoff — v0.18.2

New runs use content package `3.3`, Art plan `2.2`, Output QA `4.1` and
handoff extension `1.3`. Retain the five stages, configuration, real source
evidence, calibrations, work records and Independent Auditor. Historical
contracts retain versioned replay validation; never relabel an old artifact.

## Logic and Copy

Copy organizes the question, judgments, evidence and paragraph relationships
before assigning text roles. Review claim/evidence correspondence, entity and
accounting scope, useful local headings and repetition under
[reader-quality guidance](reader-quality.md). Missing headings alone are not a
defect; use the existing semantic review rather than a new approval form.

Art checks whether these relationships can be understood from the actual page
and returns ambiguous grouping or medium-induced repetition to Copy. Supervisor
reads both text and renders. Preserve raw tool outcomes and independent findings
under [verification outcomes](verification-outcomes.md); execution, integrity
and artifact quality require separate conclusions.

Logic produces complete research without allocating pages. Preserve sources,
findings, data, qualifiers, claim status, required coverage and invariants.
The existing research fields and source rules remain unchanged. At
logic-approved, logic_layer and copy_layer are null. Research findings may be
reorganized for presentation; their array order is not a reading-order command.

Copy reads the whole story, rewrites it for understanding and chooses content
organization, pagination, page order and conclusion wording. Copy may combine,
split and reorder findings while preserving their supported meaning.
Bind the original approved Logic file as logic_artifact and preserve research,
brief, acceptance, inventory, identity/version, configuration and run bindings.

copy_layer binds logic_version, pagination_owner:"copy", research_sha256,
semantic_preservation_review and ordered slides. Each slide has slide_id and
copy_units. Chapters, page responsibilities (narrative_role), data_ids and
requested/historical speaker notes may be supplied when useful.
logic_layer remains null: Copy no longer manufactures a duplicate Logic page
projection. Honor actual cover/closing and explicit user/master requirements.

The visible text document has only:

- title: main Storyline;
- subtitle: secondary Storyline;
- heading: a heading with a positive heading_level;
- body: complete body prose;
- annotation: qualifications, sources and notes.

Every type is optional; heading levels may be skipped. No type requires a
following type, subordinate heading or body. A unit has copy_id, text, role
and, only for heading, heading_level. Natural paragraph breaks are allowed.
The ordered array describes editorial organization, not spatial reading order.

Keep source tracking separately in root copy_provenance:
`{"S01-P1":["F1","F2"]}`. Cover each visible ID and preserve required findings
in visible content. Review actual meaning professionally; a hash, source link
or schema pass alone cannot establish equivalence.

Copy does not supply layout kinds such as columns/table/ladder/rows/flow,
parent/sibling graphs, forced separate rendering, merge prohibitions, style
parity, visual-order numbers, forced line-break indexes, grammar signatures
or presentation requests. Historical rules do not apply to package 3.3.

## Art and references

Art owns presentation structure: composition, media, visual grouping,
combination, hierarchy, typography, reading paths, space and rhythm.
Columns, tables, ladders and other arrangements remain available design
choices. Multiple text units may share one editable object. Equal textual
levels may receive different styles or emphasis. Preserve actual business
sequence and meaning; Copy order alone does not determine visual order.

Light packages ship no Art layout collection or design/layout index. If a
learning package is available, first consult its relevant index and content;
supplement gaps with web references. Without one, use the model's design
ability and proactively seek relevant layouts online. Inspect real references
when available and explain consequential adoption in existing work notes.
No match or unavailable browsing allows original design with the actual
limitation recorded. Original composition needs no catalog registration.
Never fabricate sources or claim a named pattern was retrieved.

Learning-package authoring and packaging are outside this engine version.
Asset reuse still needs provenance and rights. Reference research does not
require a per-search approval or a restart of unchanged preflight.

## Art plan 2.2 and full-deck baseline

Preserve package identity, acceptance_contract, resource_inventory_lock,
communication_contract (brief.preflight), task Provider lock and real consulted
source evidence. Record the source approach in reference_research:

```json
{"learning_package_available":false,"source_strategy":"web-first","references":[],"notes":"Record actual searches, inspected references or access limitations here."}
```

source_strategy may be learning-first, web-first or autonomous. Available
learning is preferred; insufficient or unavailable references do not block
original design. There is no required reference count or layout match.

Each Art slide binds slide_id, Art's chosen reading_sequence, copy_unit_map
and medium_execution_contract with a freely described structure_type and actual
minimum_object_counts. The global art_direction.approval retains the existing
approval basis. Optional design-intent, area, hierarchy, tree, motif or prototype
fields support the particular design; no preset proportions or sibling styles
are required. Preserve chosen decisions for Output, not a mandatory form quota.

Each copy_unit_map entry has copy_id, render_target_id, target_type and
native_location. Native target types describe editable object verification,
not layout styles. Several entries may share a target. native_location
identifies shape_name, zero-based row/column for a table cell, or a native chart
label selector. Shared text uses non-overlapping text_range:[start,end)
character ranges in the object's text body (paragraphs joined by newline).
Visual reading order and text styles are independently chosen by Art.
No parent-target matching, separate-target assertion or same-level style gate.

Produce and inspect readable PNG/JPEG drafts of every page with the approved
Copy, numbers and relationships. Reconcile drafts and specifications before
Output. Retain visual_baseline's locked status/time, canonical Copy and
specification SHA-256 values, ordered slide images and concrete observations.
Each element binds element_id, purpose/kind, copy_ids, native_type, normalized
box, group_id, alignment, resolved typography, locked_properties and bounded
allowed_adjustments. An element may carry several Copy IDs. Optional per-unit
text_styles may describe mixed typography. Charts bind approved research
data_ids; images/icons bind governed asset_ref. Technical binding does not
certify visual quality.

Use scripts/stage_documents.py lock-design. Never retrofit Art drafts from
the final Output PPTX. New explanatory wording/pagination returns to Copy;
new facts/calculations return to Logic.

Art also owns native editing boundaries. Each baseline element is a physical
native object with a unique native_name and render_separately:true. The flag
belongs to Art's object, not a Copy ID; multiple paragraphs may remain in one
declared text object. Content needing independent selection, movement, width
or format changes gets separate objects. When objects should move together,
declare native_group_path (group names outermost first) while preserving the
editable children. An omitted path means ungrouped. Mapping shape_name must
match its baseline element's native_name. Use existing purpose/work notes to
explain material editing choices. Plan 2.1 remains historical replay support.

## Output, Supervisor and Independent Auditor

Output implements the locked Art images and specification in editable native
objects. Verify Copy in exact native text locations/ranges; merged paragraphs,
different peer styles and Art's reading sequence are valid. Output QA 4.1
removes atomic_copy_separation, parent_child_hierarchy, peer_parallelism,
storyline_single_line and list_alignment as inherited Copy requirements.
Do not reintroduce them in scripts, QA or Supervisor findings.

Preserve actual text, punctuation, case, numbers, necessary qualifiers and
user constraints. A chosen table must be an integrated native table; charts,
font naming, internal capacity, final reopening/render coverage, object
editability and delivery size retain their existing reliability requirements.

Output must preserve Art's named native objects and exact grouping. Merging,
splitting, regrouping or flattening changes the approved editing behavior and
returns to Art. Final PPTX comparison and QA inspect real object names, native
types and group paths; text coverage alone cannot establish editing fidelity.

Supervisor and Auditor check omissions, changed meanings, unsupported relations,
readability failures and deviations from Art's approved design. They do not
design the pages or impose the removed rules. Correctness passing and an
unremarkable design may coexist; Art owns improving design. Do not add aesthetic
quotas or extra challenge/approval hurdles.

Keep the actual three handoff documents, baseline images, final PPTX object
evidence and design_comparison. Bind real final render hashes and coverage;
unavailable native checks remain deferred. assemble-report derives the complete
documents and portable comparison from real artifacts. Preserve the existing
PPTX/report publication pair and stage-handoff.zip. Bindings prove integrity;
reasoning, writing and design remain professional judgments.
