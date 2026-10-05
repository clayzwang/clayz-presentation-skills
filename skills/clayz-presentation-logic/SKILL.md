---
name: clayz-presentation-logic
description: Research the subject and deliver complete evidence-backed findings before Copy organizes presentation content. Use for presentation planning, management reports, business analysis, strategy, proposals, and training decks when the facts, decision outcome, research answers or substantive judgments must be established. Do not paginate, write slide titles or presentation conclusions, choose composition, or build a PPTX.
---

# Clayz Presentation Logic

Create a `logic-approved` package that another stage can use without
reconstructing the argument. Supervisor supplies the task objective and the
shared hard/soft acceptance commitments; Logic owns substantive meaning and
does not invent a stronger requirement or change the user's precedence.

Logic is the most reasoning-intensive stage. Think sufficiently to reconstruct the subject, audience, supported analysis and uncertainty; think effectively by concentrating on distinctions that can change the conclusion, research findings or decision. Private knowledge is evidence and method support, never a substitute for this synthesis.

## Production reliability (v0.17.5)

Read `../../packages/contracts/production-reliability.md` (or its `.zh-CN.md` peer). It supersedes older automatic font-size and consecutive-composition gates and inline report transport. Art owns rendered legibility and repetition; Output and Supervisor own editable delivery and PPTX size.

## Reader understanding (v0.17.1)

Read `../../packages/contracts/reader-quality.md` or its `.zh-CN.md` peer
according to the task locale. Necessary explanation and evidence fidelity take
priority over shortness; use existing records for review observations.

Before handoff, read the complete research as an answer to the task, not a research agenda.
Develop the available facts, comparisons, mechanisms and supported judgment.
Keep remaining unknowns explicit; do not let “what to verify” replace analysis
that the evidence already permits. Do not invent a cause to make the story flow.

## Research and visual handoff (v0.17.4)

Before authoring, read `../../packages/contracts/story-visual-handoff.md` (or
`story-visual-handoff.zh-CN.md` for zh-CN). New runs use package 3.3 and Art
Direction plan 2.2. The complete research, Copy content document, complete image drafts, visual tags and
report documents apply even when optional Library or A/B capabilities are absent.
Legacy page-first contracts remain readable only for existing runs. Preserve
the existing Supervisor calibration and Independent Auditor handoffs.

## Generation mode

Infer the content responsibility from the actual task and the maturity of the
supplied material. New runs record `brief.preflight.generation_mode` as one of
`execution`, `research`, or `mixed`; legacy packages may omit the field. This
is an internal working decision and never a setup questionnaire, permission
request, or user-confirmation gate. It is independent of the runtime
Library availability and does not change the
existing source, evidence, master, visual, or five-stage checks.

- **Execution:** When substantive material is supplied for conversion into a
  deck, preserve its meaningful claims, facts, numbers, caveats, relationships,
  instructions, and information coverage. Organize, condense, and clarify for
  slides without reducing detailed evidence to large slogans or launching
  unrelated research. Fill routine transitions directly. Flag contradictions
  and substantive unknowns; distinguish any substantive unverified addition in
  the existing evidence, claim-status, or open-item fields.
- **Research:** When the task is a topic, question, or incomplete input, first
  define what must be understood, then gather credible evidence, compare
  definitions, time windows, and units, investigate counterevidence,
  responses, and mechanisms, and synthesize substantive content before fixing
  slide count or design. Website count, word count, elapsed time, and slide
  count do not establish depth; unsupported claims remain unsupported.
- **Mixed:** Apply execution responsibility to mature supplied sections and
  research responsibility to unresolved sections. Assign those responsibilities
  with the existing scope or notes fields and section/slide evidence; do not
  introduce a parallel mode schema.

## Boundaries

Own research scope, source inventory, substantive answers, definitions, calculations, research conclusions, counterevidence, uncertainty and semantic invariants. Research findings must be complete enough for Copy to organize independently.

Do not organize the PPT: pagination, page order, presentation chapters, titles, opening/closing and conclusion wording belong to Copy. Research prose still needs to be clear and complete. Visual presentation structure belongs to Art.

## Required context

Read `../../packages/contracts/stage-enablement.md` for task authority, relevance-based retrieval, professional review, and measured execution. It supersedes legacy requirements to select every source, rediscover unchanged resources, or treat aesthetic heuristics as mandatory gates.


1. Consume the root's validated v2 task selection, merged `task-config.json`,
   and Supervisor's initiation commitments from the unified configure-task
   flow. If absent, return to root to prepare them once; do not select a config
   by the presence of a Personal Runtime. Preserve that configuration and its
   hash through the remaining stages.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Record the configuration SHA-256 as `configuration_sha256`.
4. Read `references/logic-package-contract.md` for the package contract. This core contract is mandatory and never search-dependent.
5. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
6. Read the locale-matched `../clayz-presentation-supervisor/references/resource-inventory-gate.md` and `../clayz-presentation-supervisor/references/first-class-index-gate.md`. Require the finalized resource inventory to prove all seven scopes were scanned, the user-facing brief was presented, and authoring started afterward. When task source requirements declare it necessary, reuse the verified source revision or materialize newly admitted Logic sources into `task-private-learning` before reasoning; a locator-only inventory or prose claim is not evidence.
7. Bind the bundled public Provider, then only the actual task-selected sources and materialized task provider when used. Read and hash those sources through observed references, retain one CompositeIndex and its receipts, and check declared required sources. An installed personal profile does not impose a Provider quota.
8. Classify optional capability signals before loading optional references. Resolve them through the built-in Capability Index and retain the capability resolution plus full finalized Retrieval Receipts. Typical signals include `evidence-research`, `audited-calculation`, `complex-relationships`, and `repeated-series`.
9. Load only the optional `knowledge_refs` returned by selected capability records. If a signal is unresolved, record it explicitly and continue with core contracts or return the gap; never invent a capability or silently substitute unrelated guidance.

When the root supplies knowledge from a prior discussion, consume only the
complete verified committed revision selected through the existing Index. Keep
its confirmation and attachment hashes, provenance category, evidence limits,
applicability, and unresolved questions visible while reasoning. A draft,
unconfirmed consensus, or attachment outside that committed snapshot is
context only and cannot become Logic evidence. Do not start this stage for a
discussion-only request; emit no `logic-approved` package until a PPT artifact
is actually requested.

## Workflow

Before approving the argument, apply the artifact-led Library loop in
`../../packages/contracts/stage-enablement.md`: provisional Logic -> question-led
Logic Library lookup -> revised Logic -> evidence and audience-understanding
check. Read known definitions before drafting. Use a missing causal link, weak
comparison or plausible counterexample as the query, then revisit the conclusion
and research answer instead of searching only for support. Record the exact claim
or research answer changed, or why the original survives. If downstream
copy or layout exposes missing meaning or a missing research answer, reopen this
stage and update the affected dependencies; do not prescribe a smaller font.

1. Validate and bind the Supervisor task acceptance and resource inventory. Preserve the user brief, scope, hard/soft requirements, evidence standards and generation_mode. Treat page count, cover/closing, typography and other presentation requirements as unchanged inputs for Copy/Art to implement; Logic does not decide or lock them. Research topics and evidence needs follow the task, without a fixed analytical or presentation template.
2. Translate actual task requirements into research questions and complete supported answers, preserving the user’s precedence and explicit page constraints. Do not impose a fixed narrative or analytical sequence.
3. Interpret only task material marked selected in that inventory. Use owner-private Logic knowledge and any confirmed committed discussion knowledge to deepen facts, counterexamples, mechanisms, terminology, and methods, then reason independently. Preserve each source's provenance and limits; user agreement does not turn an interpretation into an externally verified fact. Separate facts, calculations, interpretations, causal claims, targets, recommendations, hypotheses, and missing data, and keep unresolved questions unresolved.
5. Define terms, metrics, time windows, dimensions, exclusions, and comparison bases.
6. Write the complete research report and findings with finding IDs, sources, evidence status, qualifiers, data IDs and preservation requirements. Include research conclusions and evidence limits; do not prewrite a presentation structure. Analytical methods are selected from task context, personal configuration or external knowledge; none is built in.
7. Emit research only, with logic_layer and copy_layer null. Copy owns all presentation chapters, page responsibilities, count/order, titles and conclusion wording, within the user brief. Do not generate speaker notes or appendices unless requested.
8. Define substantive research invariants only when necessary; presentation series and cross-page organization belong to Copy.
9. Record missing inputs and research questions in the existing open-item, scope, and notes fields. Consolidate only truly blocking missing inputs into the smallest useful user interaction; generation-mode and taxonomy classification never require an interaction or confirmation. Never invent data or imply approval.
10. Emit task-local learning candidates with evidence and limits; persist them only through the configured Logic learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.
11. Emit one logic package with `origin_namespace: io.clayz.presentation`, status `logic-approved`, root `acceptance_contract`, root `resource_inventory`, and root `index_evidence`; on new runs, include `brief.preflight.generation_mode` and preserve any optional inferred-label metadata. Approval requires a ready inventory plus focused relevance-ranked Logic receipts whose selected records identify the exact claims, relations, or research findings they materially influenced. Efficiency may remove repeated retrieval and transport, but it may not shorten the reasoning needed for a complete argument.

## Validation

Run:

```bash
python ../../packages/validators/validate_logic_package.py <logic-package.json>
```

Send the validated package to both `$clayz-presentation-copy` and Supervisor.
Copy consumes the Supervisor's hash-bound Logic calibration before locking its
final package. A later calibration can challenge the Logic package with
evidence, but Supervisor does not rewrite Logic on its behalf.

## Work record at handoff

Read the stage-work-record section of `../../packages/contracts/stage-enablement.md`. Save this stage's actual artifacts to immutable task-local revision files, record the work and real checks with `scripts/publish_supervised_pair.py record-stage --stage logic`, and attach `work-notes` when the task interpretation, evidence/source trace, counterevidence, assumptions, uncertainty, research interpretations, excluded alternatives, or material content decision needs richer context. Verify the available record chain with `check-records` before handoff. Include the immediate predecessor record after Logic. Binding, identity, format or evidence-integrity failures cannot be replaced by a prose pass; quality findings may travel with explicit evidence. Missing notes remain `not-recorded`; Supervisor collects all four records, adds its coordination record and binds the independent audit artifact; it must not invent prior work or deliver a separate summary as the final report.

The central baseline is `../../config/default.json`; consume it through the unified merger with personal settings and task overrides, never as a separate production route.

## v0.18.1 content handoff

New runs use content package 3.3 and the locale-matched story-visual-handoff contract.
Research ownership and source evidence are unchanged. Copy may reorganize the complete story.
Research order and topic labels do not prescribe visual order or layouts.
