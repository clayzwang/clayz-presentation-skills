---
name: clayz-presentation-copy
description: Organize Logic-approved research into clean presentation text, with title and subtitle Storylines, headings at any needed levels, body and annotations. Own wording, reorganization, pagination and page sequence; preserve supported meaning and evidence. Hand text to Art without layout kinds, rendering commands or visual-order assumptions. Do not design or build the PPTX.
---

# Clayz Presentation Copy

Read the whole Logic research and Supervisor calibration. Explain the story in
natural language for the intended reader, then organize and edit the text for
presentation. Copy may combine, split, reorder and rewrite the complete story.
Preserve facts, numbers, claim strength, qualifiers, relationships and required
coverage; return new facts or changed research judgments to Logic.

## Current handoff — v0.19.0

Read `../../packages/contracts/story-visual-handoff.md` or its `.zh-CN.md`
peer. New runs use content package 3.4, Art plan 2.3 and Output QA 4.1.
Resolve the explicit locale or `locale.default`; read `references/copy-package-contract.md` or its `.zh-CN.md` peer.

The content document contains only these kinds of visible text:

- `title`: the main Storyline.
- `subtitle`: a secondary Storyline.
- `heading`: a heading with a positive `heading_level`.
- `body`: complete body prose.
- `annotation`: qualifications, notes, sources and other annotations.

Every category is optional. Heading levels may be skipped; a heading does not
require a subordinate heading or body. Textual hierarchy describes meaning,
not font size, position, containers or visual importance. A page may consist
only of body text or annotations. No standard title/subtitle/body shell is
required. Honor an explicit user-selected master requirement when applicable.

Each paragraph has a stable `copy_id`, `text` and `role`; headings also have
`heading_level`. Natural paragraph breaks are allowed. Preserve source
references separately in `copy_provenance`, for content fidelity review.
The array order is editorial organization, not Art's visual reading order.

Do not emit columns/table/ladder/rows/flow kinds, parent or sibling trees,
render-separately or merge prohibitions, visual order, style tokens, forced
line breaks, grammar signatures or presentation requests. Art chooses media,
layout, grouping, combination, visual emphasis and reading paths.

## Explicit content relationships — v0.19.0

Read the locale-matched `../../packages/contracts/page-planning.md` contract.
Before handoff, give every body passage an explicit relationship: the heading
it explains, multiple headings it jointly supports, or no local heading
ownership with its page-level purpose stated. Explain heading relationships
from their actual meaning. Array order and heading level cannot supply them.
Record `content_relationships` separately from text units; meaning relations do
not prescribe visual nesting, equal-sized blocks, styles, spatial reading paths
or independent objects. Headings may have no body. Review supported meaning
and identify affected Copy IDs in the existing work record.

## Context and authority

Use the root's unified `task-config.json` and task selection, merged from `../../config/default.json`, with the resource
inventory, Provider lock and hash-bound Logic-to-Copy calibration. Preserve
their real bindings. Read `../../packages/contracts/stage-enablement.md`,
`reader-quality.md` and `production-reliability.md` in the task locale.
Read `../../packages/contracts/knowledge-learning.md` when retrieving or
writing learning observations.

Use relevant available Copy knowledge to improve actual wording; unavailable
optional knowledge does not stop editing. Preserve selected source IDs and
actual use. Never invent source evidence, a consultation or a saved revision.

Execution work preserves meaningful supplied material. Research work edits
Logic's source-backed synthesis. Mixed work preserves their assigned scope.
These are content responsibilities in one workflow.

## Work

1. Bind the original Logic file and unchanged research. Write a coherent
   explanation before editing it into presentation text.
2. Choose chapters when useful, pagination, page responsibilities, page order
   and conclusion wording. Copy owns these choices. Honor actual cover/closing
   and user constraints; do not add notes or appendices by default.
3. Categorize the final text using the five roles above. Do not split a useful
   paragraph merely to prescribe several visual boxes or a fixed card count.
4. Review actual wording for reader understanding and preservation of meaning.
   Record concrete decisions in the existing semantic preservation review.
5. Hand the clean content document and separate provenance to Art and
   Supervisor. A density-driven pagination or wording change returns to Copy;
   research changes return to Logic.

## Argument and reader review

Before assigning text roles, establish what the page answers, its supported
judgments and evidence, and the relation between paragraphs. Then write the
Storyline, useful local headings, body and annotations. Categorizing a passage
as body does not establish an organized argument.

Check each title against its explanation and approved evidence. Growth or
decline needs a comparison; a current-period amount alone does not establish a
trend. Contribution and causation need their own support. Narrow an unsupported
title or return missing research to Logic; never fill the gap by wording alone.

When passages answer different questions, use informative local headings where
they help readers distinguish the judgments. A continuous explanation can remain
body-only. No heading quota, fixed group count, mandatory three-level shell,
word-count limit or visual grouping tree is introduced.

Identify entity, period, metric and accounting scope before interpreting numbers.
Separate different scopes, such as group earnings and insurance-fund returns.
Keep qualifications that change the conclusion with the relevant body; source
details and incidental notes may be annotations.

Remove repetition between passages while retaining necessary evidence and
explanation. Art chooses the medium. When its chart/table repeats the prose,
Art returns the specific redundancy to Copy for an authorized wording revision;
Copy does not preselect a medium or remove facts merely to fit a layout.

Before handoff, actually read the text and answer in the existing
semantic_preservation_review or work notes, citing affected copy IDs as useful:

- Can the Storyline and any local headings communicate the page's argument?
- Does each judgment have matching evidence with a clear entity and scope?
- Does each passage add evidence, explanation or a necessary qualification?

These are professional reading checks, not keyword tests or another approval
form. Art checks their visible expression; Supervisor reads both the text and
actual page and routes defects to the earliest responsible stage.

Validate with:

```bash
python ../../packages/validators/validate_ppt_package.py <copy-package.json>
```

## Work record at handoff

Use the existing stage-work-record workflow in
`../../packages/contracts/stage-enablement.md`. Save immutable actual artifacts,
record the Copy stage and checks through
`../../scripts/publish_supervised_pair.py record-stage --stage copy`, preserve
the predecessor record, and check the record chain. Record material wording
decisions as work notes when useful. Missing observations remain not-recorded.
Supervisor calibrates the handoff and collects the final report; Copy does not
invent prior work or overwrite the research.

The central baseline is `../../config/default.json`; consume it through the unified merger.
