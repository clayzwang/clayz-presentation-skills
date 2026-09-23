---
name: clayz-presentation-logic
description: Build the evidence, question chain, claims, management logic, and a complete chaptered narrative for a presentation before wording or design. Use for presentation planning, management reports, business analysis, strategy, proposals, and training decks when the facts, decision outcome, argument structure, or page order must be established. Do not use to write final visible copy, choose composition, or build a PPTX.
---

# Clayz Presentation Logic

Create a `logic-approved` package that another stage can use without
reconstructing the argument. Supervisor supplies the task objective and the
shared hard/soft acceptance commitments; Logic owns substantive meaning and
does not invent a stronger requirement or change the user's precedence.

Logic is the most reasoning-intensive stage. Think sufficiently to reconstruct the subject, audience starting point, current state, target state, causal or operating mechanism, path, conditions, alternatives, and uncertainty; think effectively by concentrating on distinctions that can change the conclusion, page sequence, or decision. Private knowledge is evidence and method support, never a substitute for this synthesis.

## Reader understanding (v0.17.1)

Read `../../packages/contracts/reader-quality.md` or its `.zh-CN.md` peer
according to the task locale. Necessary explanation and evidence fidelity take
priority over shortness; use existing records for review observations.

Before handoff, read the full narrative as an explanation, not an agenda.
Develop the available facts, comparisons, mechanisms and supported judgment.
Keep remaining unknowns explicit; do not let “what to verify” replace analysis
that the evidence already permits. Do not invent a cause to make the story flow.

## Story and visual handoff (v0.17.0)

Before authoring, read `../../packages/contracts/story-visual-handoff.md` (or
`story-visual-handoff.zh-CN.md` for zh-CN). New runs use package 3.0 and Art
Direction plan 2.0. The mandatory story, complete image drafts, visual tags and
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

Own audience, desired outcome, scope, source inventory, content sufficiency, current state, target state, path and mechanism, definitions, claims, evidence, uncertainty, question chain, chapter responsibilities, semantic invariants, and the analysis still required.

Do not finalize wording, punctuation, line breaks, typography, composition, theme, coordinates, or PPTX objects.

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
and page sequence instead of searching only for support. Record the exact claim
or slide responsibility changed, or why the original survives. If downstream
copy or layout exposes missing meaning or excessive page scope, reopen this
stage and update the affected dependencies; do not prescribe a smaller font.

1. Validate and bind the Supervisor task-acceptance contract and resource-inventory lock, then lock the audience, desired outcome, scope, production profile, cover/conclusion policy, narrative requirements, typography identity, and performance budget. Preserve the user's hard and soft requirement classification and delivery policy as shared inputs. Capture `material_type`, `management_stage`, `narrative_archetype`, and `narrative.management_stage_path` only as optional task-specific descriptive labels; infer them when useful, never use them as enum gates, and never require user confirmation. Preserve the inferred or supplied `brief.preflight.generation_mode` on new runs. Unless the user explicitly omits them, distinguish body-page count from total-page count and require one opening cover plus one closing synthesis/action page; never infer their omission from a short page budget.
2. Translate blocking acceptance requirements into chapter responsibilities, questions, claims, relationships, conclusion constraints and semantic invariants; preserve explicit user page constraints for Copy. The contract is task-specific; do not universalize one user's cover or storyline preference.
3. Interpret only task material marked selected in that inventory. Use owner-private Logic knowledge and any confirmed committed discussion knowledge to deepen facts, counterexamples, mechanisms, terminology, and methods, then reason independently. Preserve each source's provenance and limits; user agreement does not turn an interpretation into an externally verified fact. Separate facts, calculations, interpretations, causal claims, targets, recommendations, hypotheses, and missing data, and keep unresolved questions unresolved.
4. Before choosing pages, establish three connected answers: where the audience is now and why the issue matters; where the decision or understanding must go; and how the mechanism, sequence, conditions, and risks move from the first state to the second. Do not assume the audience already knows the prior process, motive, or stakes unless the user explicitly says so.
5. Define terms, metrics, time windows, dimensions, exclusions, and comparison bases.
6. Write a complete opening, connected chapter paragraphs and conclusion in `story`; each chapter advances a natural question chain. Tag paragraphs with stable story IDs, sources, evidence status, qualifiers and preservation requirements. When problem-before-recommendation is required, establish the current-state friction, audience impact, and mechanism before any recommendation, even when an executive-summary role is used.
7. Finish the argument before pagination. Copy owns splitting and combining pages; provide complete actors, mechanisms, evidence and transitions without locked slides or page message trees. `logic_layer` and `copy_layer` are null in the Logic handoff.
8. Define cross-slide invariants and series only when repetition carries meaning.
9. Record missing inputs and research questions in the existing open-item, scope, and notes fields. Consolidate only truly blocking missing inputs into the smallest useful user interaction; generation-mode and taxonomy classification never require an interaction or confirmation. Never invent data or imply approval.
10. Emit task-local learning candidates with evidence and limits; persist them only through the configured Logic learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.
11. Emit one logic package with `origin_namespace: io.clayz.presentation`, status `logic-approved`, root `acceptance_contract`, root `resource_inventory`, and root `index_evidence`; on new runs, include `brief.preflight.generation_mode` and preserve any optional inferred-label metadata. Approval requires a ready inventory plus focused relevance-ranked Logic receipts whose selected records identify the exact claims, relations, or slide decisions they materially influenced. Efficiency may remove repeated retrieval and transport, but it may not shorten the reasoning needed for a complete argument.

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

Read the stage-work-record section of `../../packages/contracts/stage-enablement.md`. Save this stage's actual artifacts to immutable task-local revision files, record the work and real checks with `scripts/publish_supervised_pair.py record-stage --stage logic`, and attach `work-notes` when the task interpretation, evidence/source trace, counterevidence, assumptions, uncertainty, storyline, excluded alternatives, or material content decision needs richer context. Verify the available record chain with `check-records` before handoff. Include the immediate predecessor record after Logic. Binding, identity, format or evidence-integrity failures cannot be replaced by a prose pass; quality findings may travel with explicit evidence. Missing notes remain `not-recorded`; Supervisor collects all four records, adds its coordination record and binds the independent audit artifact; it must not invent prior work or deliver a separate summary as the final report.

The central baseline is `../../config/default.json`; consume it through the unified merger with personal settings and task overrides, never as a separate production route.
