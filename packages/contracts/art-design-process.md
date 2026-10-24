# Art: from content understanding to visual decisions

When reorganizing explanations, distinguish separated but available information
from omitted meaning. The former may benefit from local labels, corresponding
positions or continuous prose; the latter needs a sufficient conceptual entry.
Before compressing an existing first-use definition, consider whether the actual
audience can still identify its referent. Integration cannot supply missing
meaning. Retain claim-level source locations when shortening citations; internal
research IDs need not enter reader-facing explanation. This does not require
every term expanded or every explanation placed inside a diagram.

Plan page counting and visible numbering separately. Under body-and-closing,
cover_counting=true counts the cover without displaying a field on it. Optional
packages.layout.page_numbers.plan_page_numbers returns both decisions and
rejects unknown scopes rather than guessing. Art decides whether an object
exists; Output checks actual native fields and rendered scope. Presence and a
correct sequence alone do not establish correct applicability.

Choose a quantitative representation for the current reading operation: exact
lookup, detecting a trend or magnitude difference, and understanding a business
relationship can need different support. A number label still needs legibility
and clear association. Common position, length or direction can carry a
comparison, but a chart name does not identify the actual perceptual task.
Retain the compared objects, periods and relevant bases; shortening a heading
must not turn an increment-to-increment comparison into increment-to-stock.
For a part-to-whole claim, check consistent definitions of part and whole.
Other ratios can intentionally connect different bases, but valid arithmetic
and a valid interpretation are separate judgments.

When the main claim concerns a difference or an offset, consider representing a
verified derived quantity directly rather than relying only on curve separation
or mental arithmetic. Whether original levels also need to appear depends on
the task. In the actual full-size native preview, assess quantitative comparison,
exact-label recognition and label-to-object matching separately. A visual
difference does not establish causation; that explanation still needs research
and its limits. These choices do not prescribe a chart or medium quota.

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

Separate current page position from content origin after splitting, merging or
reordering. Existing `art_learning.py diff` compares structural `slide_id`
slots: `before` is the old slot, and `before=null` means no such slot. Neither
establishes where the current content came from or that old content disappeared.
Keep that exact structural difference and its original validator. Follow the
actual unit's existing `source_basis.source_copy_ids` to the used original
wording instead; one current page may use several originals and one original
may support several current pages. Never fill lineage from the new page number.

Optional `scripts/art_learning.py source-context --package <approved-copy.json>
--presentation <actual-slides-array.json>` and its read-only
`copy_source_context(package, slides)` expand declared stable Copy IDs into
original page/unit text beside current wording. Missing basis, unknown IDs and
orphan basis rows remain explicit, without positional fallback. Ambiguous
duplicate page/unit/basis identities refuse the helper call; repeated source
references expand once. It does not mutate packages/diffs, resolve research
support, infer splits/merges or create a new production gate. Attach an actually
used report through existing notes if useful; keep it out of a blind first read.

Finding the original is separate from retaining its claim. Resolved references
can still accompany a deleted actor, a changed period or a shift from an invalid
inference to an asserted state. A04/A05/A11 compare the actual propositions and
their scope; source context supplies material, never semantic approval, visual
quality or reader-effect evidence. No new per-sentence form or repagination is
required to obtain such a report.

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
Native implementation capabilities then serve the selected representation:
shape text, cells and attached connectors specify how selected objects can be
edited, not which boxes, tables or lines a page needs. API capability examples
illustrate call boundaries, not composition. Choose prose, space and
quantitative encoding from the current content and reading task.

Visible treatments can also come from inherited theme or object styles. Once
visible, shadows, gradients, opacity and line ends participate in the page
language even when an authoring call leaves them unset. For an unintended
treatment, trace selected explicit properties, theme references and local
overrides with the current native preview, then return to the intended hierarchy
and visual language. Keep deliberate effects where appropriate. An explicit
effect list can also remove other inherited effects; consider the combination
that the current design needs. A11 observes the result. Property provenance does
not establish benefit or prescribe a deck-wide effects-off default.

Consult relevant knowledge at the decision that needs it. When a user-selected
learning pack is available, read applicable principles and examples before
settling the choice, then record the actual influence. A05's `P.REL.ROLE` and
`P.REL.GROUP` can support semantic preparation; A06's `P.PER.HIERARCHY` and
`P.PER.SIGNAL` support attention; A09's `P.LANG.COLOR_IMAGE`, `P.LANG.TYPE` and
`P.LANG.DATA` support implementation. These are lookup routes, not instructions
to load everything. Keep all A01–A11 represented under the existing cognition
contract; reuse applicable knowledge while making page/group-specific choices.

When comparing representations, trace the current reader's actual task: where
to find the objects, how to match them, which relationships can be recognized
directly, and what still requires memory, arithmetic or explanation. The same
information need not demand the same work. Making an offset, comparison or
ownership visible can also introduce unsupported temporal, causal, area or
funding implications. Use this distinction for A07 medium and A08 space choices,
without requiring a diagram or a number of alternatives. A11 checks whether
those operations are possible in the actual pages. Successful independent
retelling establishes this reading, not a measured speed improvement.
For adjacent quantitative plots, consider the physical length per unit in the
actual plot areas; identical tick numbers alone do not make their bars
comparable across plots. Choose a common scale or clearer separation from the
current comparison task, without imposing a chart or layout quota.

Save planning with `record-planning` before producing the full drafts and
refining native-object specifications. Preserve original Copy; document actual
Art changes, evidence and consequences under `art_content`. A change in
presentation is independently audited under the existing contract.

The outer chart frame, rendered plot region and label attachment use different references. Frame coordinates or equal divisions of its height do not by themselves locate rendered bar centers; axes, titles, labels and category order also participate in layout. If external direct labels are chosen, trace each to its actual mark in the full-size page and revisit that correspondence after consequential local changes. Native axis or point labels can delegate part of placement maintenance to the chart; fixed external text retains independent composition and synchronization responsibilities. Choose for the current task, without requiring all labels inside, all labels separate or a particular chart type. Correct data, complete labels, visible association and future updating supply different evidence. Placement attachment and value updating can belong to different objects: custom rich-text point labels can retain literal strings while remaining attached to their indexed points. Read the actual axis, legend, label-group, individual-label or custom-run style rather than inferring each size from an enclosing chart default. Value formatting and literal label text are distinct; a shared unit context is an option only when the current quantity remains clear. Neither global no-wrap nor a label or layout quota follows.

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

For native chart typefaces, the optional
`packages.layout.native_chart_text.bind_chart_typeface(chart, family)` writes
Latin, East Asian and Complex Script fields after axis, legend and label styles
have been authored. It freezes existing target nodes before replacing their
children, avoiding skipped siblings in a live XML iterator. It neither selects
a font nor changes sizes; numerical continuity, collisions and rendered font
acceptance still require actual native observation.

Keep numeric value, cache spelling, number format, unit and visible label
separate. For existing category-series reference caches, the optional
`packages.layout.native_chart_cache.format_numeric_cache(chart, decimals,
signed=False)` spells values at an explicitly chosen precision only when every
Decimal value remains exactly equal. It validates all targets before mutation
and rejects rounding or nonfinite values. It leaves categories, workbooks,
formulas, selectors, number formats and label text unchanged. It does not repair
an invalid native selector: automatic data labels and their value bindings still
need independent native comparison and rendered observation. Percent scaling
and unit choice remain the author's decisions; a matching cache is not evidence
that a label or business interpretation is correct.

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

### Main handoffs and side conditions

A readable main path does not automatically carry an adjacent condition. A resource can support an activity, an order can initiate work, a delivery can satisfy a recognition condition, and use can incur cost. These are compatible claims rather than interchangeable arrow labels. For a consequential transformation, read the actual graphic and prose back as a business claim: where is the agent now stated, and which activity or result does the side condition qualify? Retain needed prose or make that specific relation discernible. This is a local design judgment, not a requirement to diagram every condition, add edges or fill a new form. Matching individual words to Copy does not prove the composed claim survives.

Distinguish the target object, selected connection site, stored path geometry and the entry, route and label association actually rendered. Choose the supported relationship and representation before the attachment API. Read the selected relationship cluster in its whole-page context: native attachment or a successful programmatic refresh does not establish that its paths, subjects and annotations work together. Local placement, routing, wording or label treatment may change; no orthogonal route, common entry or enclosure is prescribed.

After choosing straight connectors and ordinary unrotated, unflipped rectangles in one direct slide spTree, the optional `packages.layout.native_connector.attach_rectangular_connector` integrates the existing experimental library API. Its invocation belongs to implementation guidance, not a cognitive composition example. It checks all endpoints before mutation and refuses groups even on the same slide part. It creates no objects, styles, routes, labels or line endings. Independent labels and triangles do not follow it. Programmatic refresh, saved structure, the selected renderer’s actual entry and GUI behaviour provide different evidence; a stored custom connection site does not establish application adoption. Use the existing A11 native page observation, without new forms, gates or repair allowances.


### Local star50.r05.1 — select chart label wrapping in its own scope

Chart point labels receive space from the chart engine, not the enclosing graphic frame or an ordinary TextFrame preparation call. Numeric caches, ordinary text capacity and an intact visible label are separate evidence. Compare inherited wrapping, a local explicit wrap choice, chart-space adjustment or a named external annotation according to the current reading task. Disabling wrap can replace broken text with overflow; it is no layout verdict and does not remove hard breaks.

The optional `packages.layout.native_chart_text.set_point_label_wrapping` selects existing custom point labels by series/point and expected literal text. It preflights all requests before writing only word_wrap. It does not create custom text from automatic labels or alter text, runs, size, position, data or workbooks. True/False/None mean wrap/no-wrap/inherit; None is not no-wrap. The existing library supplies this text-body behavior. Do not apply it globally or treat ordinary protected_terms as controlling chart internals.

Read intact values with their series, unit and period. A correct series name in the data cache, a visibly identifiable series, and correspondence between its legend symbol and actual marks are different evidence. Individually colored points can coexist with inherited series or theme styles that give the legend another color. Follow a currently important series through its name, chosen legend or direct label, and actual marks on the rendered page, rather than checking palette parameters alone. Choose a legend, direct naming or clear shared context for the reading task; a software default name is not evidence of category meaning. Separately fitting table/text objects can still cover each other in painter order; inspect the real page and affected neighbours, optionally reusing the existing selected-label observer. External annotations trade explicit placement for separately verified update/link behavior. No diagram, font-size, clearance or label-count gate follows.


### Local star50.r06.1 — choose native line endings without inferring meaning

For a line-end arrow, default to the connector's own headEnd/tailEnd properties, not a separate triangle. Register actual node IDs/sites for node connections. A whole direction-bearing block may be a native arrow AutoShape with its own short label. The content still determines direction and whether an arrow is needed; do not add arrows to every line. A legacy separate triangle remains another object and does not follow a changed or reattached endpoint. Retain that limitation rather than using the old structure as the default node connector. Native endings do not move independent annotations either.

Optional `packages.layout.set_connector_line_ends(line, tail={"type":"triangle", "w":"med", "len":"med"})` preflights both selected ends before mutation. head/tail are DrawingML names, not screen sides. None preserves an end, explicit type=none disables its decoration, and 'inherit' removes only that element to resume style inheritance. Omitted w/len preserve existing attributes; these size categories are relative to line width, not absolute triangle dimensions. The narrow scope is nonzero, unrotated straight connectors in a direct slide spTree, retaining native flips. Grouped, curved and rotated connectors are refused. Geometry, bindings, width/color, the other end and unrelated XML remain; no independent object migration, routing or GUI assurance occurs.

A rate describing a result and an adjustment operating on it are different relations. Existing GROUP/RELATION/DATA principles already cover mistaken association. After splitting a supported sentence, read the particular rate/result or member/set relation from the real page, then choose local naming, position, continuous explanation or an appropriate shared region. Do not turn this into repeated full names, frames or a new checklist/gate. Native endpoint decoration cannot solve semantic attachment elsewhere.


### Local star50.r08.1 — conditional rules and actual membership

A supported conditional rule and evidence that a particular instance satisfies its category are different claims. A commercial use of service, product or confirmation need not share a contract or policy taxonomy with the same words. Turning a conditional rule into an organization-wide realization path can silently classify its instances when the endpoint names only a particular category. Unknown membership does not refute the rule and does not license an invented classification.

During A04/A05, identify whether the consequential path explains a rule, a selected instance or the whole organization. A07/A08 can retain an explicitly conditional example, or stop the broader graphic at a supported neutral result and explain the applicable rules in prose. Existing clear context need not be repeated. Individually sourced labels do not establish that their combination preserved the condition.

When a local revision narrows a scope or exposes an unknown, A10/A11 should revisit the later passage or graphic that actually reuses that premise. Repeated names do not propagate a qualification by themselves. This is a local meaning judgment, not a requirement for repeated disclaimers, frames, edge tables or a new gate. A compressed modifier may identify the set being discussed; retain that referent or an equivalent contextual reading rather than assuming it was expendable wording. Keep original Copy, changes and reader residuals; explaining an unknown is not obtaining the missing fact.

For company figures quoted by different shareholders, identify the start and end dates as well as the accounting entity before making a visual comparison. A full-year amount and an amount recognized only after an acquisition date are not two comparable full years; their difference does not by itself establish the unrecognized period's profit. A threshold calculated as last full year's result minus a disclosed current half-year result is a conditional hurdle, not a forecast. If either disclosed input is rounded, label the hurdle at that precision as approximate rather than using a strict inequality that implies an exact sufficient cutoff. Select visual form from the reading task; this is not a calendar-band or bar-chart requirement.


### Local star50.r09.1 — aggregate names and the members they select

An aggregate value, a member count and the identities of those members answer different questions. A correct total with a label such as “four items” or “other” can lose which objects were included. Nearby words from the same domain do not establish that set: mentioning expenses and taxes does not tell a reader whether a particular expense total includes tax. This applies existing object/grouping principles to compression; it is not a new accounting taxonomy or an automatic tool defect.

During A04/A05, read a consequential aggregate name against its actual members and operation. A07/A08 can retain a compact name when visible context has already established the set. Otherwise, preserve the necessary member names, identify the composition in a local explanation, or make the actual members and their aggregate readable together. Raw data, source IDs, file grouping and equal numbers do not themselves establish visible context. Do not require every component value, a complete earnings bridge, uniformly long labels or added frames.

The level selected by a label also matters to placement. A name for a set must not appear to name only its nearest member. A region carrying a whole activity cannot be judged complete merely because each internal TextFrame fits. During A10/A11, read the current aggregate and its local context, considering how actual objects, wording and regions jointly select its referent. Keep an adequate open layout or existing context. Numeric measurement, visible ownership and semantic support have distinct evidence scopes; none automatically passes the others. No new field, gate, prescribed graphic or per-page quota follows.


### Local star50.r10.1 — finding evidence and identifying an adjustment's starting point

A title selects a task as well as stating a judgment. During A04/A06, distinguish what the different claims in a compound conclusion depend on: one may require a two-period amount comparison, another an expense or result change. Having both facts somewhere on the page does not make both usable in the actual primary reading path. A07/A08 can choose shared principal evidence, a main comparison with clear support, continuous explanation or pagination, or an evidenced change to the title's responsibility. This does not require equal size for every clause, two charts or promoting all annotations. A11 reads actual evidence entry points rather than inferring support from numeric presence, even allocation or individual-frame fit.

A prominent adjusted result still needs an identifiable named starting quantity and the operation changing it. During A05, recover the approved base, excluded or added item and target definition. A07/A09 can preserve that relationship with a named expression, continuous prose, local explanation or unambiguous shared context. Equal values do not make metric identities equal; another complete subtraction on the same page does not provide the base for a neighbouring adjustment. Do not retain only a positive result and a warning that it differs from another definition when the source already explains the starting point. Do not invent a missing expense schedule, full earnings bridge, or rename an author's net difference as an original pretax expense.

These apply existing hierarchy, data-identity and actual-render principles. Selected phrase protection, individual-frame capacity and intact native glyphs have limited coverage: protecting a few phrases does not protect every meaningful phrase on neighbouring lines. Recoverable original text may still force cross-line assembly of a keyword. A09/A11 can choose existing local protection, semantic line breaks, wording or geometry as the actual importance and space require. No topic dictionary, universal nowrap or per-word quota follows. Record actual selections and written lines; Output preserves the locked line choices rather than silently redesigning or reopening a closed repair.


### Edge association and intact glyphs

Within a selected relation graphic, distinguish recognizing which edge a label belongs to from reading its intact glyphs. Proximity to its own edge can aid association while that edge can still occlude the text. Space beside the edge, routing and any necessary text protection have tradeoffs. Read the actual label with its edge and neighbouring nodes before choosing a local position. Native endpoint binding and metric rectangles provide implementation or geometric evidence in their own scope. This judgment follows the content and chosen medium; it prescribes no universal label background, on-edge/off-edge placement, or additional diagram.

### Optional value labels with an independent format source

For a selected native chart that will be edited, choose value-generated label content separately from numeric format and text styling. Font or position control alone need not introduce fixed rich-text values. Existing automatic point labels may use packages.layout.native_chart_text.set_point_value_label_formats: explicit series/point indices, expected_value and number_format are checked together before only the selected numeric formats are written. Custom text is rejected, not converted; font/position siblings and data stay intact. An unlinked format source is not a fixed value source. Select content modes for meaning and future use, then inspect the actual chart and neighbours; no label/chart quota or new gate follows.

### Maintaining an explicitly selected connector set

After changing node geometry in a selected native relation graphic, distinguish maintaining one connector from an explicitly selected set. Optional packages.layout.refresh_rectangular_connectors accepts a same-slide list and validates all registered targets/sites and its narrow scope before updating selected paths. The single-path interface remains available. This does not discover all affected edges, move nodes or independent labels, choose new sites, reroute paths or install an observer. Read actual paths, labels/proportions and shared conditions in the whole graphic; one successful refresh does not establish that every dependency was maintained. This maintains chosen objects, without selecting a node-link composition or adding a gate.

### Evidence strength for a manager's revenue, net profit, and residual

For the same reporting entity and period, revenue minus net profit is an aggregate residual that can include operating costs, expenses, tax, and other results. It is not an identified expense or distribution cost. When revenue rises and net profit falls, show the matched-period divergence, then check whether disclosed components support causal attribution. If they do not, label the cause unresolved; do not turn the residual into invented cost segments in a visual bridge. Period revenue and profit also differ from an end-date asset stock. Choose the representation the relation needs rather than prescribing a bridge, table, funnel, or columns.

### Fee-paying assets, contract rates, and profit entities

For asset-based management fees, multiply period-average fee-paying assets by the applicable rate within each contract, then sum across contracts. Performance fees, distribution fees, and the manager's own investment results may follow other terms. One end-date AUM observation and one product rate do not produce the company's recognized full-year revenue. A rate-offset AUM multiple is a static condition for a specified product, not a company forecast. Identify period, payee, product, and assumptions. A fund's accounting profit belongs to fund assets and investors; a manager's net profit belongs to the operating company. Map products, contracts, shareholders, manager, and investors to their actual layers before drawing cross relations. Do not invent intersections or mandate a matrix. When a source date changes, scan every date label on the rendered page, not only the title and footnote.

### Canvas bounds and visual comparison

Audit all native PowerPoint shape bounds, not only extracted PDF text. Bars, fills, connectors, and integrated labels can be clipped while every word stays in the canvas. Run `scripts/audit_native_shape_bounds.py` on the finished PPTX, then inspect the rendered endpoints, relative lengths, and scale. Compute same-scale bars from the usable drawing width with a right margin. Correct labels cannot compensate for a clipped mark. Preserve the original audit and a separately evidenced emergency fix if a late review finds an out-of-bounds object. This check does not mandate bars or a fixed layout.

### Conditional arrows and known baselines

A known historical baseline is a reference, not automatically the cause of future hypotheses. For an if-then scenario, attach a native arrow from the condition object's appropriate edge to its possible outcome. Keep the known baseline independent when its causal role is not evidenced. Inspect rendered endpoint positions, direction, text overlap, and crossings. A registered connector is not a semantic verdict. Asset share comparisons must use matching dates and scopes; one product's AUM share is not the manager's revenue share.
