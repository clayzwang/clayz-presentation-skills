# Art: from content understanding to visual decisions

This process operationalizes A01–A11 in the existing Art stage. Read it after
the current title and content reviews pass, before page planning and drafts.
Its Chinese peer is [Art 设计工作流](art-design-process.zh-CN.md).
The external knowledge pack is stored and versioned separately. These are dependencies
between design decisions, not new agents, approval gates or a layout catalog.

## Develop the knowledge that produces design judgment

An iteration can start with an observed problem or an opportunity to improve.
Deepen relevant concepts, mechanisms, applicability, tradeoffs and connections
before making a contextual choice for the audience, content and medium.
Knowledge influences design through a better understanding of the task.
Keep page-specific repairs in practice records; cases and demonstrated actions
support understanding rather than define universal fixes. If the selected pack
provides a top-level learning philosophy, understand that direction before
entering relevant domains. Separate observations, causal hypotheses, choices
and results. Reading can revise the initial diagnosis. Small revisits, retaining
the current design or deferring judgment are valid; no node quota or layout rule
follows.

When an observed problem exposes a gap in design judgment, consider the relevant
knowledge domain before choosing a repair. Editorial narrative and orientation,
perception and visual variables, and semantic rules in a visual system are
connected starting points, not a closed symptom classifier. A user-selected pack
may offer an open reading map through `art_learning.py domains --pack <path>`.
Study concepts, mechanisms, applicability and professional sources; examples
help explain this knowledge rather than replace it. In existing work notes,
describe the consequential understanding, then let Art independently adopt,
adapt or decline it for the actual content, audience and medium. Implementation
follows that judgment. Keep knowledge enrichment, application and observed
reader effect distinct. No layout prescription, change quota or new gate follows.

When relations are easily confused, graphic syntax offers another connected
domain: what are the objects, does space carry quantity, order or grouping, and
which objects do labels and connectors refer to? A series can preserve these
meanings while adapting its organization to the current task. These questions
inform judgment without specifying a graphic or equating reading order with an
industry process.

When whole-page hierarchy is clear but reading still requires backtracking within
a passage, connect typography with representation: paragraph boundaries,
alignment, space and line measure support different reading operations. Study
continuous exposition, correspondence and conditions before deciding whether to
retain or adapt the expression. Preserve the script and medium limits of numeric
advice from professional sources rather than converting it to Chinese-slide quotas.

## 1. Read and prepare the whole Copy document

Read the complete visible text, its explanation and `content_relationships`
together. Identify the audience's knowledge gap, the central question, supported
judgments, evidence, qualifications, recurring entities and the responsibility
of each page. Notice transitions, repetition and missing dependencies across
pages. Preserve periods, units, actual/forecast/scenario status and uncertainty.
An absent relationship is unknown; do not infer it from heading levels or array
order. Inspect the available evidence when meaning is unclear and record any
remaining uncertainty or Art revision.

Use this understanding for A01 communication task and A03 narrative. Form an
A02 direction grounded in this subject and audience, then revisit it when page
analysis reveals a better choice. A shared direction can span a series, but
changing the company name in generic prose does not establish contextual design.
Record consequential whole-deck conclusions and actions in `art_cognition`.

## 2. Prepare the semantics of each whole page

Before choosing containers or assigning colors, use A04 and A05 to state the
page judgment and identify what supports, explains or limits it. Read passages
continuously before regrouping them; one body passage may contain both evidence
and a qualification, while several Copy units may form one coherent comparison.
Identify shared qualifications and their complete scope. In numerical evidence,
identify the intended comparison, its members, periods and units; account for
relevant values already in the visible Copy before choosing a table or chart.
Missing values stay unknown, never silently zero.

Distinguish four compatible dimensions:

| Dimension | Question | Examples |
| --- | --- | --- |
| Text role | How is the text organized editorially? | title, subtitle, heading, body, annotation |
| Argument responsibility | What does it contribute to the page judgment? | claim, fact, explanation, qualification, source |
| Entity/category ownership | Which object or comparison does it belong to? | entity, metric, period, actual or guidance; shared scope |
| Visual responsibility | How should it participate in the reader's attention? | focal comparison, supporting explanation, lookup detail |

The first three inform the fourth; visual responsibility is a design decision,
not a fixed attribute inherited from a Copy role. A body can carry the focal
claim. An annotation can contain a decisive condition. Category identity does
not automatically confer emphasis. Roles may coexist and shared material may
belong to several groups. These examples are not a closed classifier.

Put concrete groups, responsibilities, ownership, dependencies and known gaps
in the existing `content_analysis`; put the judgment in `page_message`. Refer
to consequential Copy IDs or clearly identifiable groups, not just “evidence”
or “support.” Do not add a form for every word or a mandatory object-per-unit
mapping. The result must be sufficient for the next design choice.

## 3. Decide attention from those responsibilities

A06 consumes the page judgment and semantic groups. Identify the first useful
understanding, the comparison or relationship the reader must notice, and the
supporting explanation and lookup material. Explain why each consequential
object or group receives its visual weight. A comparison may require multiple
equally prominent members; no universal one-highlight quota applies.

Distinguish category encoding from emphasis. A stronger category color must not
accidentally imply importance, quality or risk. Preserve the visibility and
proximity of conditions needed to understand a claim. Supporting or lookup
status never licenses illegibility. Record the intended reading path and
emphasis in `composition`, with object/group treatments in `element_strategy`.

## 4. Select expression, composition and element language

A07 chooses a medium that explains the identified relationship. A08 allocates
space, groups content and balances the whole page around the A06 intention.
A09 translates those decisions into type, color, shape, image and data
encoding. Text role alone must not select a fixed color, equal box or style.
Define what a consequential color distinguishes or emphasizes and why; use
position, type, spacing, labels or line style when they explain it better.
Update language that refers to a prior medium when the medium changes.

Consult relevant knowledge at the decision that needs it. When a user-selected
learning pack is available, read applicable principles and examples before
settling the choice, then record the actual influence. A05's `P.REL.ROLE` and
`P.REL.GROUP` can support semantic preparation; A06's `P.PER.HIERARCHY` and
`P.PER.SIGNAL` support attention; A09's `P.LANG.COLOR_IMAGE`, `P.LANG.TYPE` and
`P.LANG.DATA` support implementation. These are lookup routes, not instructions
to load everything. Keep all A01–A11 represented under the existing cognition
contract; reuse applicable knowledge while making page/group-specific choices.

Save planning with `record-planning` before producing the full drafts and
refining native-object specifications. Preserve original Copy; document actual
Art changes, evidence and consequences under `art_content`. A change in
presentation is independently audited under the existing contract.

## 5. Observe the drafts and revise the responsible decision

A10 checks the sequence, category mappings, continuity and useful variation.
A11 compares actual full-deck drafts and full-size pages with the intended
attention, grouping, relationships and legibility. Name the observed object or
group: what attracts attention, what comparison can be made, what condition
is missed. A planning sentence, receipt or populated field cannot prove this.

If the wrong material dominates, revisit A06 and then its A08/A09 realization.
If ownership or a qualification is misunderstood, revisit A04/A05 and the
affected expression. If the medium obscures the relation, revisit A07. Preserve
unaffected work and record real revisions, then reconcile images with editable
specifications and lock the baseline for Output.

Art's draft inspection is separate from the reader gates. Early title/content
readers read text only; the final reader first reads actual deliverable renders,
freezes understanding, then compares original Copy and all recorded Art changes.
This update neither adds early image reading nor changes that isolation order.

## Synthetic example: roles become visible choices

A page says revenue rose while operating profit fell. Its Copy contains the
comparison, disclosed exceptional expenses, and a warning that the remaining
cost increase has not been decomposed. A04 identifies the divergent outcomes;
A05 groups the comparison, explanatory facts and the limit on attribution.
A06 gives the comparison focal weight while keeping that limit adjacent to the
explanation. A07–A09 choose a suitable comparison medium and supporting language;
period labels distinguish categories without implying good or bad performance.
A11 checks whether the draft makes both the divergence and attribution limit
readable. This invented example demonstrates a dependency, not a fixed layout,
palette or measured reader outcome.
