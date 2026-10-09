---
name: clayz-presentation-copy
description: Explain Logic-approved research for the intended reader, review the actual explanation for understanding and meaning preservation, then edit it into finely resolved, coherent text passages. Own wording, reorganization, pagination and page sequence; preserve supported meaning and evidence. Hand semantic body units and their relationships to Art without prescribing objects or layouts. Do not design or build the PPTX.
---

# Clayz Presentation Copy

Copy owns substantive editorial judgment: what the reader needs to know first,
what requires explanation, and how the supported facts form a coherent account.
Develop that account before filling text roles or page slots. Logic owns research
judgments; that boundary does not reduce Copy to summarizing or labeling them.

Read the whole Logic research and Supervisor calibration. Explain the story in
natural language for the intended reader, then organize and edit the text for
presentation. Copy may combine, split, reorder and rewrite the complete story.
Preserve facts, numbers, claim strength, qualifiers, relationships and required
coverage; return new facts or changed research judgments to Logic.

## Current production boundary (v0.20.1)

Follow [reader review](../../packages/contracts/reader-review.md), including its eight-step order and minimal repair scope. Logic explicitly supplies substantive research conclusions. Copy completes text before separate title and content readings against Logic. Art starts only after both current gates pass; Output follows approved Art. Final reading compares actual pages to approved Copy and routes failures through Art. Record/receipt formatting repairs never require regenerating the deck. Upload is only a separately requested action.

## Current handoff — v0.19.0

Read `../../packages/contracts/story-visual-handoff.md` or its `.zh-CN.md`
peer. New runs use content package 3.4, Art plan 2.3 and Output QA 4.1.
Resolve the explicit locale or `locale.default`; read `references/copy-package-contract.md` or its `.zh-CN.md` peer.

The content document contains only these kinds of visible text:

- `title`: the main Storyline.
- `subtitle`: a secondary Storyline.
- `heading`: a heading with a positive `heading_level`.
- `body`: a meaningful passage of body prose, resolved as finely as coherence permits.
- `annotation`: qualifications, notes, sources and other annotations.

Every category is optional. Heading levels may be skipped; a heading does not
require a subordinate heading or body. Textual hierarchy describes meaning,
not font size, position, containers or visual importance. A page may consist
only of body text or annotations. No standard title/subtitle/body shell is
required. Honor an explicit user-selected master requirement when applicable.

Each text passage has a stable `copy_id`, `text` and `role`; headings also have
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
   reader-facing explanation before editing it into presentation text. Preserve
   the actual explanation in existing work notes or reference its real draft;
   this is editorial prose, not a private reasoning transcript.
2. Choose chapters when useful, pagination, page responsibilities, page order
   and conclusion wording. Copy owns these choices. Honor actual cover/closing
   and user constraints; do not add notes or appendices by default.
3. Resolve body into the smallest meaningful passages that preserve fluency,
   logical links and qualifications. A paragraph may yield several body units
   under the same heading; a grammatically or logically dependent passage stays
   intact when splitting would break it. Read the units continuously and explain
   their actual roles/dependencies in existing content relationships. Art decides
   whether to combine them; fine text units do not prescribe separate boxes.
4. Review Logic findings against the explanation, then the explanation against
   edited text. Check actual reader understanding, retained mechanisms and
   discriminating facts, and coherence after decomposition. Record concrete
   observations, exclusions or deferrals in the existing semantic preservation
   review/work notes. Source IDs and schema success do not establish these results.
5. Hand the clean content document and separate provenance to Art and
   Supervisor. A density-driven pagination or wording change returns to Copy;
   research changes return to Logic.

## Argument and reader review

Apply [reader review](../../packages/contracts/reader-review.md) (or its zh-CN
peer). Write for the audience's substantive questions: what the subject does,
how it works and what the supported comparison actually establishes. Keep this
reader-question/answer judgment in the actual explanation and work notes.
For explanatory/comparative tasks, explain the mechanisms and differences before
offering writing procedures or due-diligence advice. Preserve a procedure-first
sequence when the user's task and reader genuinely need that sequence.

Titles may ask, judge or orient. Read them together, then check that the body
delivers the promised answer. A title saying requirements differ has not itself
explained the difference; a reminder to distinguish evidence types may belong
in a qualification instead of displacing the subject's core meaning. Do not
force every heading into a conclusion, question, contrast or slogan. Preserve
scope and uncertainty: strengthen expression only as far as the evidence allows.

After saving the current Copy revision, send it to Supervisor for the fresh
reader pass before Copy-to-Art calibration. Respond to actual comprehension
findings in existing work notes; change the substantive explanation and page
responsibility when needed, then derive titles/body again. Cosmetic title changes
cannot repair missing analysis. Preserve old findings and re-read revised bytes.

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
- Which concrete actors, mechanisms and differences survived editing, and which
  were omitted or moved? Cite the affected findings and Copy IDs; explain a
  consequential omission or an actual destination instead of asserting coverage.
- When the fine body units are read together, do pronouns, connectors, conditions
  and qualifications still communicate the same fluent account?

These are professional reading checks, not keyword tests or another approval
form. Art checks their visible expression; Supervisor reads both the text and
actual page and routes defects to the earliest responsible stage.
Record a content-reading result only after that reading, with evidence in the
existing notes. A generic structure-check pass or an empty issue list must not
automatically become a content-quality pass; missing reading remains deferred.

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
