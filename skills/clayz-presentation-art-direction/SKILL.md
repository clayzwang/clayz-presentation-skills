---
name: clayz-presentation-art-direction
description: Design presentation structure, layout and full-deck image drafts from Copy-approved text. Prefer relevant learning-package indexes and content when available; otherwise seek web design references and use the model's own design ability. Independently choose visual hierarchy, grouping, media, combined objects and reading paths, then hand a locked editable implementation specification to Output. Do not rewrite approved content or create the final PPTX.
---

# Clayz Presentation Art Direction

Art owns presentation structure and design. Read the whole Copy document and
the complete story it communicates, then decide how the audience should see
and understand it. Textual headings are meaning cues, not geometry or styling
commands. Copy's editorial order does not prescribe the visual reading path.

## Current handoff — v0.18.0

Read `../../packages/contracts/story-visual-handoff.md` or its `.zh-CN.md`
peer and locale-matched `references/art-direction-plan-contract.md`.
New runs use content package 3.3 and Art plan 2.1. Historical contracts apply
only to existing artifacts and never introduce old requirements into a new run.

The Light package contains no Art layout collection, design index or fixed
layout choices. Design is not restricted to a catalog, named pattern,
registered contract, container type or silhouette whitelist.

## References and original design

When a learning package is available, first consult its relevant index and
content. Read the actual selected references, including visual material when
present, and connect their useful principles to this story and audience.
An index entry, method name or receipt alone is not learning adoption.
Supplement insufficient coverage with relevant web references.

Without a learning package, use the model's design ability and proactively
seek relevant layouts and design references online. Choose useful references
from spatial design, graphic design, editorial composition, advertising or
other appropriate disciplines. Search and inspect them according to the
page's communication problem; there is no required number or finite menu.

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
   Decide the important content and intended first visual for each page.
2. Choose composition, hierarchy, grouping, medium, spacing and reading paths
   from that content. Columns, tables, ladders and other arrangements remain
   available Art choices, without Copy prescribing them.
3. Combine multiple Copy paragraphs in one editable text object when suitable,
   including headings and body. Equal textual levels may have different styles
   or visual weight. Preserve actual meaning; visual sequence must not invent a
   business sequence, rank, cause or relationship.
4. Use approved data for charts and tables. If choosing tabular presentation,
   specify an integrated native table. Govern images, logos and symbols by
   purpose and rights; decorative ordinals must not imply unsupported rank.
5. Produce readable PNG/JPEG drafts of every page using the actual approved
   text. Inspect full-size pages and the whole deck. Judge rhythm, purposeful
   repetition, whitespace and legibility professionally. No fixed card count,
   area ratio, font-level parity or random variation establishes quality.
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
