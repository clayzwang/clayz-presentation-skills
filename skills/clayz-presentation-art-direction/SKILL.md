---
name: clayz-presentation-art-direction
description: Design presentation structure, layout and full-deck image drafts from Copy-approved text. Organize the reader's attention and understanding through visual hierarchy, information relationships, composition and sequence rhythm. Use the model's design ability and relevant references when useful; use learning packages only when the user requests them. Hand a locked editable implementation specification to Output without rewriting approved content or creating the final PPTX.
---

# Clayz Presentation Art Direction

Art owns presentation structure and design. Read the whole Copy document and
the complete story it communicates, then decide how the audience should see
and understand it. Textual headings are meaning cues, not geometry or styling
commands. Copy's editorial order does not prescribe the visual reading path.

Fine body units expose semantic contributions, not a required number of boxes.
Read them together, their relationship purposes and the actual Copy explanation
when available. Decide which should share a paragraph, object or visual group,
which merit emphasis, and which can be separated without breaking the account.
Keep qualifications and referents intelligible when changing visual order.
If a passage's dependency is unclear or its splitting broke the prose, return
those Copy IDs for revision rather than inventing a relation or rewriting them.

Check that the actual page makes the argument and distinct judgments readable.
Font-size differences or faithful text alone are insufficient. If Copy's
grouping is ambiguous, return the affected passages to Copy. If the selected
medium duplicates prose, request a precise Copy revision rather than rewriting
it in Art. Use existing observations; no mandatory heading count or layout is
introduced.

## Current production boundary (v0.20.1)

Follow [reader review](../../packages/contracts/reader-review.md), including its eight-step order and minimal repair scope. Logic explicitly supplies substantive research conclusions. Copy completes text before separate title and content readings against Logic. Art starts only after both current gates pass; Output follows approved Art. Final reading compares actual pages to approved Copy and routes failures through Art. Record/receipt formatting repairs never require regenerating the deck. Upload is only a separately requested action.

## Composition guidance

Read [Reader-centered composition](references/reader-centered-composition.md)
or its [Chinese peer](references/reader-centered-composition.zh-CN.md) before
designing. Layout should help the reader perceive importance, relationships
and a useful reading path, with a comfortable rhythm across the whole deck.
Neat alignment, text containment and an explanation of the chosen layout do
not establish that result. Use the guidance to make and revise actual design
choices; it introduces no layout catalog, aesthetic score or approval form.

Judge page balance from the actual combined weight of color, filled area,
position, grouping and text density. Check that the strongest visible region
serves the intended hierarchy, including purposeful asymmetry. Revise a
secondary saturated panel or dense region that overwhelms the main evidence;
inspect the color drafts and sequence again before locking the baseline.

## Current handoff — v0.19.0

Read `../../packages/contracts/story-visual-handoff.md` or its `.zh-CN.md`
peer and locale-matched `references/art-direction-plan-contract.md`.
New runs use content package 3.4 and Art plan 2.3. Historical contracts apply
only to existing artifacts and never introduce old requirements into a new run.

The Light package contains no Art layout collection, design index or fixed
layout choices. Design is not restricted to a catalog, named pattern,
registered contract, container type or silhouette whitelist.

## Page planning before object specifications — v0.19.0

Read `../../packages/contracts/page-planning.md` or its Chinese peer. First
understand the page message, content groups, ownership, passage functions and
supported relationships. Save readable page planning before refining object
specifications: overall arrangement and reasons, attention and reading path,
important element treatments, and whether ordinals, labels, emphasis or a slogan
help. Record additions with their purpose and approved Copy basis; adding
nothing is valid. Preserve approved wording; Art may create grounded additive
expressive text. Replacements or changed meaning return to the upstream owner.

Let one element or coherent combination serve mutually supporting functions.
A process block's own direction-bearing shape may replace a separate arrow
when the relation and readable text space remain clear. Shape, line and type
are freely chosen means; no compulsory silhouette, equal group sizes, object
count or arrow prohibition applies. Explain semantic containment and native
editing groups separately.

Use `stage_documents.py record-planning` to save actual immutable planning,
then build and inspect images and matching specifications. Save real revisions
when the draft reveals a better choice. Lock with `--planning`; hand planning,
full-deck images and specifications to Output and Supervisor. Generic purpose
labels, technical coordinates and retrospective explanations do not establish
reader-centered planning. Audit actual realization and retain missing evidence
or ineffective choices as findings.

## References and original design

Use the model's design ability to develop the composition from this story and
audience. Seek relevant design references online when they help resolve a
specific design question. Choose useful references
from spatial design, graphic design, editorial composition, advertising or
other appropriate disciplines. Search and inspect them according to the
page's communication problem; there is no required number or finite menu.

Do not search for, download or load a learning package by default, including
one already available locally. When the user requests one, read its relevant
index and actual selected content, including visual material when present.
Connect the useful principles to this story and audience. An index entry,
method name or receipt alone is not learning adoption.

No match, unavailable browsing or insufficient references permits original
design. Record what was actually available and consulted and the limitation.
Never fabricate a source, named registered pattern, retrieval or attribution.
Original composition does not require registration or a source receipt.

Use existing work notes and `reference_research` to preserve the actual source
approach and consequential uses. Learning-package authoring and packaging are
outside the engine version's scope. Online design research is authorized by
this workflow; it does not require approval for every reference. Keep asset
reuse rights distinct from looking at a composition for inspiration. Record a
new asset in the normal resource evidence without silently changing user
requirements or resetting an unchanged preflight.

## Context and authority

Consume the root's validated task selection and unified `task-config.json`, merged from `../../config/default.json`. Resolve the explicit locale or `locale.default`.
Preserve the Copy-approved text, research, acceptance rules, resource lock,
Provider lock and Copy-to-Art calibration. Read
`../../packages/contracts/stage-enablement.md`, `reader-quality.md` and
`production-reliability.md` in the task locale. Read
`../../packages/contracts/knowledge-learning.md` when learning evidence is used.

Preserve actual source provenance and asset rights. Retrieve selected learning
content through the host's available tools; optional Library absence does not
block design. A named source must be real, but an original design is allowed.
Do not require a built-in Capability Index before thinking, researching online
or choosing a composition.

## Design

1. Understand the argument, intended audience, evidence and relationships.
   Decide what the reader should first notice and then understand on each
   page. Distinguish the main evidence or relationship from supporting text.
2. Choose composition, hierarchy, grouping, medium, spacing and reading paths
   from that content. Make the important relationship perceptible in the
   spatial arrangement; a heading/body pair does not imply its own equal
   rectangle. Columns, tables, ladders and other arrangements remain available
   Art choices, without Copy prescribing them. Shared drawing code implements
   these choices rather than supplying their default geometry.
   Let the whole composition communicate alongside the words. Choose spatial,
   pictorial or typographic means freely for the content; frames, blocks and
   background depth are examples, never required objects or a layout recipe.
   Inspect whether the actual arrangement expresses the intended relationships
   and emphasis, and preserve useful contrast when correcting balance.
3. Decide native editing boundaries as part of the design. Content that needs
   independent selection, movement, width or format changes becomes a separate
   object. Natural continuous paragraphs may share one text box. Use native
   groups when separate editable children should move together. Equal textual levels may have different styles
   or visual weight. Preserve actual meaning; visual sequence must not invent a
   business sequence, rank, cause or relationship.
4. Use approved data for charts and tables. If choosing tabular presentation,
   specify an integrated native table. Govern images, logos and symbols by
   purpose and rights; decorative ordinals must not imply unsupported rank.
5. Produce readable PNG/JPEG drafts of every page using the actual approved
   text. Inspect thumbnails, full-size pages and the actual page sequence.
   Judge attention, relationships, reading effort, visual fatigue, purposeful
   repetition, whitespace and the combined weight of color and text. Check
   whether filled areas and dense passages pull attention to the intended
   evidence and conditions. If consecutive pages flatten different tasks
   into the same reading experience, revise the affected designs and inspect
   the sequence again. Retain repetition when its comparison or progression
   benefit remains visible. No fixed card count, area ratio, font-level parity
   or random variation establishes quality.
6. Refine a matching visual specification with coordinates, typography,
   native targets and bounded technical adjustments. Bind each Copy ID once
   for traceability; several IDs may bind one object through disjoint text
   ranges. Art's `reading_sequence` is independent of Copy's array order.
7. Return wording or pagination changes to Copy and changed facts/calculations
   to Logic. Output implements the approved design; it does not invent one.
8. Lock the full-deck baseline only after reconciling images and specifications.
   Use `../../scripts/stage_documents.py lock-design`, then validate:

```bash
python ../../packages/validators/validate_art_direction_plan.py <copy-package.json> <art-plan.json>
```

Each baseline element is one independently retained native object. Declare a
unique `native_name` and `render_separately:true` on that Art element; several
Copy IDs may belong to it. For native grouping, add `native_group_path` with
group names outermost first. An omitted path means an ungrouped object.
Use the existing purpose and work notes to explain consequential editing choices.
Output must preserve these object boundaries and groups. It cannot merge, split,
regroup or flatten them for convenience; a boundary change returns to Art.
Text ranges prove content coverage, while native object structure proves the
declared editing behavior. Neither alone proves comfortable editing.

A semantic layout tree, A/B prototype, relative-layout solver or external
learning pattern may help a particular design. Use them when useful; none is a
required style, creativity gate or substitute for inspecting the drafts.
Avoid overloading a page or shortening necessary Copy to satisfy symmetry.
Technical text capacity and approximately 10% internal reserve support editable
delivery; they are not whole-slide whitespace quotas.

## Work record at handoff

Use the existing stage-work-record workflow in
`../../packages/contracts/stage-enablement.md`. Save actual immutable artifacts
and observations, record Art with
`../../scripts/publish_supervised_pair.py record-stage --stage art-direction`,
preserve the predecessor record and check the chain. Record reference uses,
design decisions and unresolved limitations in existing work notes.
Send the locked plan and drafts to Output and Supervisor with the normal
calibration. Do not fabricate design evidence or retrofit a draft from the
final Output PPTX.

The central baseline is `../../config/default.json`; consume it through the unified merger.
