---
name: clayz-presentation-art-direction
description: Design presentation structure, layout and full-deck image drafts from Copy-approved text. Organize the reader's attention and understanding through visual hierarchy, information relationships, composition and sequence rhythm. Use the model's design ability and relevant references when useful; use learning packages only when the user requests them. Hand a locked editable implementation specification to Output with original Copy and Art changes preserved for final audit; do not create the final PPTX.
---
## v0.20.5 current repair policy

The selected `consolidated-once` policy controls all reader return routes: Copy readers together → one Copy repair → both original readers confirm; final reader → one Art/Output repair → same reader confirms. Independent Auditor records only. Residual/new issues are reported, never another repair dispatch. Historical pass-until-clean or repeated returns below apply only to legacy `strict-pass`. See `../../packages/contracts/reader-cycle.md` from the plugin root.



# Clayz Presentation Art Direction

Art owns presentation structure and design. Read the whole Copy document and the complete story it communicates, then decide how the audience should see and understand it. Textual headings are meaning cues, not geometry or styling commands. Copy's editorial order does not prescribe the visual reading path.

Fine body units expose semantic contributions, not a required number of boxes. Read them together, their relationship purposes and the actual Copy explanation when available. Decide which should share a paragraph, object or visual group, which merit emphasis, and which can be separated without breaking the account. Keep qualifications and referents intelligible when changing visual order. If a dependency is unclear, inspect the evidence and make a defensible design or wording choice. Preserve its uncertainty and any change from Copy in the final audit.

Check that the actual page makes the argument and distinct judgments readable. Font-size differences or faithful text alone are insufficient. Art can clarify grouping and revise expression when the medium requires it; record before/after, reasons and evidence without a front-loaded request. No mandatory heading count or layout is introduced.

## Current production boundary (v0.20.2)

Follow [reader review](../../packages/contracts/reader-review.md), with the current reader-cycle contract for bounded repair and original-reader confirmation. Logic explicitly supplies substantive research conclusions. Copy completes text before separate title and content readings against Logic. Art starts after the closed Copy cycle, including both original-reader confirmations when repaired; Output follows approved Art. Final reading compares actual pages to approved Copy and routes one consolidated repair to Art or Output, followed by confirmation by the same final reader. Record/receipt formatting repairs never require regenerating the deck. Upload is only a separately requested action.

## Eleven concrete design results and knowledge codes — v0.20.2

Read [the Art design process](../../packages/contracts/art-design-process.md) or its [Chinese peer](../../packages/contracts/art-design-process.zh-CN.md). Execute the dependencies: whole-deck Copy preparation → whole-page semantic preparation → attention decisions → expression/composition/element language → draft observation and targeted revision. A04/A05 identify actual content responsibilities and ownership; A06 consumes them to assign visual responsibility; A07–A09 realize that intention. Text role, argument responsibility, category ownership and visual responsibility are distinct, compatible dimensions. For a consequential combination, use A04/A05 to read the title, column meanings, corresponding row or connected objects together as an ordinary business claim. What predicate does their combination add to the separate passages? A record of what happened can support a lookup without yet supporting a difference, cause or permission judgment. Check the comparison basis or other premise needed by that stronger claim; retain supported premises, or state the useful question the current evidence can answer. Individual Copy IDs and source matches do not establish the meaning created by the combination. Use applicable knowledge when making each choice, and explain the consequential Copy objects/groups and reasons in existing planning. Generic deck statements or code receipts alone do not complete these decisions.

Read [Art cognition and external learning](../../packages/contracts/art-cognition.md). Cover A01 task, A02 direction, A03 narrative, A04 page proposition, A05 roles/relations, A06 perception, A07 concept, A08 composition, A09 visual language, A10 integration, A11 critique. For each, state a scoped conclusion, actionable operations and checks/uncertainty in `art_cognition`; reuse unaffected work and revisit local choices. These are eleven thinking concerns, not eleven agents or approval steps.

When the user selects the foundations learning pack, validate it and use `../../scripts/art_learning.py lookup --pack <path> --code <Axx-or-principle>`. Read the principle, applicability, action, limitation and optional examples; cite exact consulted nodes and explain their effect on the choice. Do not merely append codes. Every code has a principle; cases are synthetic teaching examples, not university work or tested outcomes. Keep the package external to Light. The package is optional; concrete conclusions and actions are required for new Art work even without it.

Record `art_cognition` and any `art_content` in planning before lock; carry both through the actual Art plan and final report. Original Copy remains available. For changed meaning, argument, order or pagination, use the actual presentation projection and the independent final-reader change audit specified in the contract. Differences alone do not fail; unsupported facts or lost qualifications do.

For problem-led learning, use the domain guidance in the Art design process. An optional pack's `domains` reading map can connect a symptom to relevant professional concepts without classifying it automatically. Learn the underlying judgment before prescribing a page repair; keep study, application and observed effect separate in existing notes. Let code follow the design decision.

## Composition guidance

Read [Reader-centered composition](references/reader-centered-composition.md) or its [Chinese peer](references/reader-centered-composition.zh-CN.md) before designing. Layout should help the reader perceive importance, relationships and a useful reading path, with a comfortable rhythm across the whole deck. Neat alignment, text containment and an explanation of the chosen layout do not establish that result. Use the guidance to make and revise actual design choices; it introduces no layout catalog, aesthetic score or approval form.

Judge page balance from the actual combined weight of color, filled area, position, grouping and text density. Check that the strongest visible region serves the intended hierarchy, including purposeful asymmetry. Revise a secondary saturated panel or dense region that overwhelms the main evidence; inspect the color drafts and sequence again before locking the baseline.

### Local r08.1 — preserve reading hierarchy during fit repairs

When repairing clipping, crowded sources or narrow columns, compare the actual revised page with the understanding task again. A wider line or an uncut paragraph can still flatten the distinction between the main result, its business owner and the explanation. Trace the title's judgment to its visible support, including any subject change within a paragraph. Inspect what the reader must still find and connect; revise affected typography, grouping or spatial correspondence when that supports the current task. Retain useful continuous prose and inspect the page in its real sequence. Containment and reading hierarchy remain separate observations in the existing Art critique.

Judge the contribution of a chosen cue, rather than inferring it from its appearance: it may help the reader select relevant information, discern the organization, or connect particular elements within or between representations. These functions can overlap; a salient area or a clear outline does not by itself explain the local relation. For a consequential condition, identify the work or result it qualifies and consider how the visible wording and arrangement let the reader connect them. If compression has removed a needed object, action, direction or scope, restore the supported meaning before choosing how to cue it; stronger emphasis cannot supply the missing explanation. Use this distinction inside the existing design reasoning, not as a page format or a requirement to give every passage a separate label or cue.

Distinguish source locators from evidence needed to make the current judgment. A comparison value or counterfactual may remain in a source line yet be absent from the main reading path. When it changes the interpretation, compare a placement near the relevant result with the current footnote treatment; preserve the comparison basis. A qualification may remain subordinate when that serves the task. Observe whether the current meaning and connection can be read, keeping salience, retained content and demonstrated understanding distinct; the cueing research does not establish the effects of this deck. This adds no required labels, argument count, layout, score or approval gate.


### Local r10.1 — measure native usable capacity before lock

Before locking, use the actual font and reopened native prototype to compare text metrics against each text object's usable box and every native table cell. Subtract the written native margins first; apply the configured internal reserve to that usable width and height, including normal padding, vertical anchors and paragraph spacing. A width scale or estimated line advance is only a design estimate. Distinguish line advance, PDF font-metric boxes and visible ink; none is interchangeable with the other two. Inspect the complete matched object/cell set, and retain unmatched or unmeasured targets as unknown rather than pass. Use the existing draft render and capacity evidence; this does not require a second full-deck render or a new approval gate. Reconcile the result with the locked object specifications. If the existing route cannot measure an item, state that coverage limit instead of estimating a verified reserve.

Resolve a measured shortfall through Art's content relationships and available space, preserving necessary explanation, font hierarchy and native editing boundaries. Review the affected whole page again: a title's wrap should preserve readable meaning units, and a narrow closing panel may repeat the nearby claim and consume attention without adding a useful conclusion. Decide whether that repetition aids recall or adds reading work from the actual sequence; no fixed column count, wrap dictionary or mandatory deletion follows. Bounds and capacity pass do not establish these reading qualities. The observed STKaiti metric height of about 1.30 times the size in the AIA/LibreOffice run is not a universal font, renderer, line-height or design constant.

### Local systems.r04.1 — realize the referent at the chosen granularity

While implementing a selected relationship, distinguish what its endpoint means from the native shape carrying the line. The intended referent may be a named identity, a particular assertion, or a complete item of work including its actions and result. A heading can name that work without making the nearby body part of the same visible object. Choose the carrier and spatial scope from the actual meaning; preserve useful grouping and continuous prose. A label-only anchor can be appropriate when that label is the intended referent. Do not turn every paragraph into a node or every relation into a flow.

Use A05/A08 to distinguish the scope of a shared carrier from the claims made about its members. Several inputs may participate together without every input being the actor of every operation. A relation placed beside the last member can appear to select that member even when the intended referent is the set. A shared heading may likewise name a topic, an actor, or a predicate applied to the rows below it; those are different commitments. Read a consequential shared heading with its actual rows, or trace the visible path to the intended collection rather than relying on the author's internal grouping. Preserve a supported collective relation or distinguish the actual actors and actions with suitable wording or spatial organization. The choice need not add a container, repeated labels or a connector.

Use A05/A07 to decide which reading scale matters inside that referent. A complete item of work can remain one relationship endpoint while its internal objects, capabilities, tasks or conditions need distinguishable roles. For a consequential conversion from prose to fields or separate objects, notice what the original shared subject and action supplied. An outline or alignment does not automatically carry that context: what now makes these attributes belong to this particular record or work, and shows their use? Let supported wording, grouping or already established narrative context carry the needed meaning; complete field IDs are not a complete explanation. Recognizing the outer work and finding what happens inside it are related reading operations; satisfying one does not establish the other. Preserve a useful continuous explanation when that is what the current task needs.

In A09, follow the chosen scope into the actual implementation: does the arrangement still let the reader associate the relevant explanation with each endpoint, including after text reflow or capacity changes? When a common region is the selected carrier, comparing its extent with the current text frames can expose an incomplete implementation. Planned geometry and ordinary font estimates are only diagnostics; use the actual native draft and page view to judge the resulting association. Native groups, connector endpoint IDs, border contact and text containment each describe different properties. None alone establishes the intended visible relationship.

In A11, trace each consequential selected relationship in the real page and name its two referents at the chosen granularity, rather than treating a line plus complete prose as sufficient. Where the task also needs an internal distinction, locate that object or activity and its role in the whole page. Inspect whether the wording, grouping, position, label and direction support these selected readings together, retaining the necessary conditions. For a shared carrier, distinguish what is true of the collection from what is being asserted of a particular member: neither clear containment nor aligned rows alone establishes that scope. The actual page may let graphics identify the participants while nearby prose states their different work; judge that division of explanation rather than requiring the graphic to say everything. Revisit the consequential combined claim in the real page: the relation the reader can trace and the inference it warrants are separate judgments. If a row, heading or endpoint now promises a stronger answer, check whether its supported premise remains intelligible there or in the accompanying explanation. Adjust the claim or its expression to the useful supported answer, rather than treating clear correspondence as proof of the inference. Choose a local adjustment or retain a defensible loose association according to the task. This deepens the existing RELATION/GROUP and graphic/prose work; it adds no required frame, hard anchor, minimum line length, schema, automated quality gate or extra repair allowance. Actual reader comprehension, native geometry and untested efficiency remain separate evidence.

## Current handoff — v0.19.0

Read `../../packages/contracts/story-visual-handoff.md` or its `.zh-CN.md` peer and locale-matched `references/art-direction-plan-contract.md`. New runs use content package 3.4 and Art plan 2.3. Historical contracts apply only to existing artifacts and never introduce old requirements into a new run.

The Light package contains no Art layout collection, design index or fixed layout choices. Design is not restricted to a catalog, named pattern, registered contract, container type or silhouette whitelist.

## Page planning before object specifications — v0.19.0

Read `../../packages/contracts/page-planning.md` or its Chinese peer. First understand the page message, content groups, ownership, passage functions and supported relationships. Save readable page planning before refining object specifications: overall arrangement and reasons, attention and reading path, important element treatments, and whether ordinals, labels, emphasis or a slogan help. Record additions and revisions with purpose, original Copy basis, evidence and impact; adding nothing is valid. Art can change conclusions, argument, order and pagination. Preserve both versions in `art_content` for final audit, without an advance modification request.

Let one element or coherent combination serve mutually supporting functions. A process block's own direction-bearing shape may replace a separate arrow when the relation and readable text space remain clear. Shape, line and type are freely chosen means; no compulsory silhouette, equal group sizes, object count or arrow prohibition applies. Explain semantic containment and native editing groups separately.

Use `stage_documents.py record-planning` to save actual immutable planning, then build and inspect images and matching specifications. Save real revisions when the draft reveals a better choice. Lock with `--planning`; hand planning, full-deck images and specifications to Output and Supervisor. After regrouping or rewriting passages, carry their actual local ownership or concrete page-level contribution into the existing relationship records. A passage may support several headings or none; an empty heading assignment is not a substitute for that judgment. Generic purpose labels, technical coordinates and retrospective explanations do not establish reader-centered planning. Audit actual realization and retain missing evidence or ineffective choices as findings.

## References and original design

Use the model's design ability to develop the composition from this story and audience. Seek relevant design references online when they help resolve a specific design question. Choose useful references from spatial design, graphic design, editorial composition, advertising or other appropriate disciplines. Search and inspect them according to the page's communication problem; there is no required number or finite menu.

Do not search for, download or load a learning package by default, including one already available locally. When the user requests one, read its relevant index and actual selected content, including visual material when present. Connect the useful principles to this story and audience. An index entry, method name or receipt alone is not learning adoption.

No match, unavailable browsing or insufficient references permits original design. Record what was actually available and consulted and the limitation. Never fabricate a source, named registered pattern, retrieval or attribution. Original composition does not require registration or a source receipt.

Use existing work notes and `reference_research` to preserve the actual source approach and consequential uses. The optional external Art foundations package ships as a separate release asset; it is not a layout catalog or owner-admitted knowledge. Online design research is authorized by this workflow; it does not require approval for every reference. Keep asset reuse rights distinct from looking at a composition for inspiration. Record a new asset in the normal resource evidence without silently changing user requirements or resetting an unchanged preflight.

## Context and authority

Consume the root's validated task selection and unified `task-config.json`, merged from `../../config/default.json`. Resolve the explicit locale or `locale.default`. Preserve the original Copy baseline, research, acceptance rules, resource lock, Provider lock and Copy-to-Art calibration. Read `../../packages/contracts/stage-enablement.md`, `reader-quality.md` and `production-reliability.md` in the task locale. Read `../../packages/contracts/knowledge-learning.md` when learning evidence is used.

Preserve actual source provenance and asset rights. Retrieve selected learning content through the host's available tools; optional Library absence does not block design. A named source must be real, but an original design is allowed. Do not require a built-in Capability Index before thinking, researching online or choosing a composition.

## Design

1. Prepare the entire Copy story, then each whole page under the
   [design process](../../packages/contracts/art-design-process.md). Distinguish
   text roles, argument responsibilities, category ownership and dependencies
   before assigning visual responsibility. Bind consequential A04/A05 judgments
   to identifiable content; use them to decide A06's intended attention and
   reading order. Preserve shared qualifications and complete comparison sets.
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
   When native reopening wraps a cell differently from measurement, consider
   a small target/font-specific `semantic_table.plan(native_width_scale=...)`
   calibration, then inspect the reflow and available height. Its default is 1;
   a previous case's value is not a universal preset. For source links, choosing
   the actual annotation object or Copy range can avoid linking a product name
   that happens to equal a source code (as AWS S3 did in the cloud trial).
   When an explicit source-link scope is selected, check whether an older
   whole-heading fallback still adds unrelated clickable text. Inspect the
   actual clickable objects as well as the correctly linked source codes.
5. Produce readable PNG/JPEG drafts of every page using the actual approved
   or Art-revised text, preserving differences. Inspect thumbnails, full-size pages and the actual page sequence.
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
7. Record Art changes and evidence in `art_content`; original research is retained for independent audit of any new inference. Do not require advance Copy/Logic approval. Output implements the locked actual presentation and preserves the original baseline for comparison.
8. Lock the full-deck baseline only after reconciling images and specifications.
   Use `../../scripts/stage_documents.py lock-design`, then validate:

```bash
python ../../packages/validators/validate_art_direction_plan.py <copy-package.json> <art-plan.json>
```

Each baseline element is one independently retained native object. Declare a unique `native_name` and `render_separately:true` on that Art element; several Copy IDs may belong to it. For native grouping, add `native_group_path` with group names outermost first. An omitted path means an ungrouped object. Use the existing purpose and work notes to explain consequential editing choices. Output must preserve these object boundaries and groups. It cannot merge, split, regroup or flatten them for convenience; a boundary change returns to Art. Text ranges prove content coverage, while native object structure proves the declared editing behavior. Neither alone proves comfortable editing.

A semantic layout tree, A/B prototype, relative-layout solver or external learning pattern may help a particular design. Use them when useful; none is a required style, creativity gate or substitute for inspecting the drafts. Avoid overloading a page or shortening necessary Copy to satisfy symmetry. Technical text capacity and approximately 10% internal reserve support editable delivery; they are not whole-slide whitespace quotas.

## Work record at handoff

Use the existing stage-work-record workflow in `../../packages/contracts/stage-enablement.md`. Save actual immutable artifacts and observations, record Art with `../../scripts/publish_supervised_pair.py record-stage --stage art-direction`, preserve the predecessor record and check the chain. Record reference uses, design decisions and unresolved limitations in existing work notes. Send the locked plan and drafts to Output and Supervisor with the normal calibration. Do not fabricate design evidence or retrofit a draft from the final Output PPTX.

The central baseline is `../../config/default.json`; consume it through the unified merger.


## Native production checks

For native production, also read `../../packages/contracts/local-development-gates.zh-CN.md`. Apply actual native preview, inspectable knowledge parameters, table-cell and footer checks, bound visual evidence, and stale-record rejection. The current external knowledge pack is stored and versioned separately; read its top-level learning philosophy when selected. Preserve failed readings and disclose actual Auditor context and unobserved target applications.


### Local r11.1 — choose the relationship before its visual form

Use the mounted knowledge's existing relationship, grouping and text-organization chapters to decide what the audience must connect. Trace a consequential reader operation through the actual draft: finding a business, locating its value, retaining a sign or scope, and connecting an explanation. Identify the operation that the current arrangement still leaves to memory or search. Compare a suitable alternative for that relationship before settling the existing page plan; a small sketch or native fragment within the current budget can reveal this without another full-deck production cycle. A sequence, shared semantic region, aligned values or continuous paragraphs may serve the relation. Rejecting an unsupported complete causal bridge does not require retaining every partial comparison as a paragraph. Keep attribution and quantified causation distinct. Distinguish sequence from elapsed time/causality, proximity from ownership, and an equation row from a single economic cause. Retain labels, units and the scope/purpose of mixed components when changing representation. No diagram quota, fixed column count, or company-specific layout is implied.

During actual native reading distinguish the font-metric box, visible ink, container inner bounds and total remaining space. A total reserve pass does not prove the box stays inside each padding edge; no visible clipping does not clear that geometric finding. An unmatched line remains unmatched in the original report even when spatially bound PDF-word evidence supports its full text. Keep unresolved results instead of deriving a new tolerance from one renderer. Read numeric ranges and their units as meaning units alongside words; preserve continuous reading where the current geometry allows, without a universal ban on breaks or shrinking the font. This extends existing native/semantic reading, not another review stage. See the mounted r11 production observation for limits.

### Local r12.1 — keep the scope of a typography repair explicit

A native measurement describes the current text, authored lines and allocated region together; it does not invalidate every existing line break. Choose the affected objects from the actual change: adding an identity or explanation, moving nearby material or changing line breaks can redistribute space beyond the old shortfall IDs. A wider frame does not remove saved paragraph or soft line breaks. Preserve unaffected lines and compare the current paragraph and its neighbours before and after. A global width recalibration needs evidence concerning those objects too; an ineffective layout may still be reorganized. This is a scoped design decision, not another approval gate.

Distinguish explicit user typography requirements from historical starting references and the current acceptance mode, including annotations. In visual review, a reference is neither a minimum nor a reason to resize all smaller text. Art judges the actual font, text roles, lines, available region and page. `../../scripts/native_text_revision.py` offers configured_size for candidate values, not a readability pass or a substitute for task requirements, and a line-only revision helper that leaves other objects unchanged. Art still chooses the lines. Its line_capacity helper describes candidate widths with measurement provenance; assess manual lines as well as automatic candidates. Joining a range or amount-unit phrase can exceed native capacity. Consider the surrounding clause and available region together; do not silently shrink or reflow the whole deck. The helper neither wraps text nor supplies a quality pass.

For python-pptx native tables, write padding on the cell itself (tcPr); setting cell.text_frame margins addresses bodyPr and does not establish effective cell padding. The same helper accepts either a native cell or a TextFrame explicitly. Reopen the saved object and inspect the actual properties, then retain native metric and visible-ink observations separately. Keep the existing bounded repair policy: unsuccessful rereading is a retained failure, not permission to start another loop under a new label.

### Local r13.1 — carry the chosen font into the actual native process

Use the existing native renderer with the task's explicit font identity: `render(pptx, directory, slide_ids, font_file=resolved_font_path, font_family=resolved_family, fontconfig=existing_fontconfig_path)`. The equivalent CLI requires `--font-file` and `--font-family`; supply `--fontconfig` for the already configured runtime font environment. These are paths/values from this task's runtime setup, not a new font search or route. The old three-argument call now stops before conversion rather than rendering with an unbound font. With no fontconfig argument, inherited resolution must still match the requested file hash. The renderer forwards the environment to LibreOffice/Poppler, saves `font-environment.json`, and stops before PDF conversion on a mismatch. This precheck does not replace PDF font or glyph inspection and does not make another full render available under the budget.

For fixed-size native paragraphs, `set_paragraph_edge_space(cell_or_text_frame, left_pt, right_pt)` writes real paragraph space inside native padding. Choose its value and affected paragraphs deliberately; it replaces existing paragraph marL/marR and can affect indentation or bullets. It leaves font and shape size unchanged. When selected, `native_capacity` reads actual cell/TextFrame margins plus those paragraph edges and reports both axes. It also discloses the declared fit, wrap and text-frame anchor settings; a cell's anchor is separately declared on the cell. `None` retains unresolved inheritance, not a resolved `NONE` mode. The numeric reserves describe the caller's current rectangle and candidate metrics, not a prediction of the renderer's auto-fit response. Choose automatic or fixed-size behaviour from the current reading task and inspect the saved native result; a `NONE` setting can still overflow. This helper neither changes those properties nor establishes ink containment or quality. Before fitting candidate lines, derive usable width from the actual object margins and paragraph edges, then apply the reserve to that usable width. Construct the candidate emphasis runs before assessing their width: the ordinary font estimate used by measure_lines does not measure mixed bold/native runs. Keep that estimate distinct from reopened native metrics; a previously observed width_scale is not a guarantee. Inspect the actual longest styled lines in the existing native draft review, and compare both object capacity and its clearance from the actual adjacent footer. Do not infer footer clearance from a fixed body-bottom coordinate or infer inner-edge containment from total reserve. If the measurements differ, preserve the concrete dimensions and unresolved factors rather than increasing a global coefficient until the check passes.

When a candidate retains the same observed styled line span L, the optional lower bound L/(1-r) can help assess the space needed for reserve r; add actual object margins and paragraph-edge allowances only once. Select this diagnostic when it answers the current question, rather than making calculation or an estimate pass a prerequisite for every repair. ../../scripts/plan_text_capacity.py calculates that conditional bound, not acceptance. Compare it with available space and the intended reading relationship. If text, runs or line breaks change, the old span does not predict the new arrangement. Reopen and inspect the chosen current lines and regions within the existing render budget. Do not round near-threshold failures up, add global shrinkage, or alter the threshold. A font size is not measured text height. Auto-fit, hanging indents, bullets, vertical text and renderer transformations need their own geometry observation; the fixed-box estimate does not cover them. A positive reserve does not prove inner-edge containment, visible ink or readable relationships. Keep the original glyph/capacity checks and bounded visual reading unchanged.


### Local r15.1 — read beyond the entry point

After identifying the title and the first emphasized element, follow the body in the actual requested font: can the audience distinguish the current claim, its necessary explanation and relevant qualification at their point of use? A whole paragraph in an accent color or a large tinted box may give an entry without expressing the relationships inside it. Choose emphasis spans, paragraph boundaries, alignment and space around those relationships; do not treat every Copy unit or sentence as requiring equal visual weight or a separate card. When a native writer breaks a logical paragraph into manual visual lines, represent authored emphasis as half-open Unicode character intervals in the original paragraph. Use `../../packages/layout/text_emphasis.py:project_emphasis` to project those ranges into each line's runs; concatenated lines must preserve the exact original text. Do not search each already-broken line for a whole phrase: a cross-line phrase would silently lose its styling, and repeated text could select the wrong occurrence. Art chooses the ranges and line breaks; the helper chooses neither. Inspect the actual runs and rendered fragments, including both members of a comparison when both were meant to be emphasized. This is a faithful implementation aid, not proof of a useful visual hierarchy. Keep long prose where continuous reasoning needs it. Across the sequence, check whether a familiar-looking value still refers to the same metric and scope. Record what the real prototype makes visible in existing Art observations; capacity, object counts and unchanged text do not establish this result. No fixed argument count, layout quota, font replacement or additional reader gate is introduced. Preserve the original final reader and repair budgets.


### Local r17.1 — judge Chinese line breaks in their reading context

When inspecting Chinese text, distinguish an allowed inter-character break from a broken numeric/symbol combination and from an observed loss of meaning or correspondence. Read P.LANG.TEXT_ORGANIZATION and its scoped W3C sources for that distinction. A dictionary word crossing a line is not by itself a defect. In a short heading or comparison label, a phrase boundary may still help the current reading task; compare it on the actual page rather than extending it to a deck-wide protected-word list. Identify the affected subject, unit, qualifier or reading path before requesting a repair. Preserve ordinary flow when a change would merely exchange one acceptable break for another. Inspect hierarchy separately: a brightly emphasized exception can overshadow the main result even if every line break is acceptable. These judgments do not waive clipping, capacity, content, final-reader or bounded-return checks.


### Local systems r01.1 — make the whole and the current part recognizable

For a composition-learning task, read the actual parts and relationships in the complete account before selecting a diagram. Compare a broad verbal summary with what the prototype lets a reader identify together: the relevant functions, their supported connections and the current detail's place. Naming more modules or repeating the same geometry does not itself establish those connections. Choose grouping, labels, spatial correspondence or paths for the actual relation; a shared record, optional extension and temporal handoff need not use the same graphic. A whole can include multiple relationships rather than one strict hierarchy. Do not make a house, three tiers, universal arrows or a repeated panorama template the target. Consult P.ED.ORIENTATION and its scoped overview/relate discussion when relevant. In existing Art observations, describe what the current image actually exposes, and distinguish this from independent-reader comprehension or an untested efficiency claim. No extra page quota, schema, gate or repair allowance is introduced.


### Local systems r02.1 — choose the graphic and prose division from the task

When a functional whole contains several relations, identify the reading task the main graphic actually offers. Carry the concrete proposition into the chosen wording and space: a function, the data it reuses and a business item being handled are different referents even when their names overlap. A shortened relation label must still support the intended subject and scope; author classifications alone do not establish the reader's business question.

Choose the mechanism by what this reader needs to identify, correspond, trace or understand. Common identity, meaningful row/column correspondence, a recognizable business object, a path and continuous explanation can share that work; these are possible mechanisms, not a required menu. Selecting a table or relationship-diagram name does not establish what a row, column or connection actually means. Where a consequential choice is uncertain, compare mechanisms that preserve the needed meaning and conditions, and acknowledge other differences such as typography rather than attributing all visible benefit to the representation. Use the existing A05/A07/A08/A11 judgments, without requiring alternatives on every page.

A branch from a portal to functions exposes access; it does not by itself expose document sharing or a meeting-to-task handoff. Conversely, nearby complete prose can explain a supported connection without making the graphic alone a process model. Trace the current objects, endpoints and conditions in the real draft, then decide which relation should be visible at a glance and which needs words or an example. Preserve the explanation when changing representation; neither more lines nor replacing prose is a general improvement. Do this within the existing A05/A07/A11 judgments, without a required diagram, field, page, connection count or gate. Consult P.REL.EXTERNAL_REP when its task/operation distinction helps. Report what the combined page lets the actual reader infer, separately from what the graphic alone depicts; comprehension without a comparison does not establish faster reading or the superiority of the chosen division.
