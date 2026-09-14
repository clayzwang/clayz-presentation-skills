---
name: clayz-presentation-copy
description: Turn a logic-approved presentation package into final visible copy with locked titles, storylines, numbers, punctuation, line breaks, notes, and atomic copy units. Use after presentation logic is approved and before visual composition. Do not change facts, evidence status, slide order, or business relationships, and do not design or build the PPTX.
---

# Clayz Presentation Copy

Create a `copy-approved` package in which every visible character is intentional
and traceable. Consume the Logic artifact and Supervisor's calibration as
separate inputs; Supervisor evaluates and coordinates but does not write Copy.

## Generation mode

Preserve the Logic-inferred `brief.preflight.generation_mode` when it is
present; new runs use `execution`, `research`, or `mixed`, while legacy
packages may omit it. The field is an internal working decision and never
requires user confirmation. It is independent of optional Library availability;
the production path remains unified.

- **Execution:** Preserve every meaningful supplied claim, number, caveat,
  relationship, instruction, and information-bearing detail while organizing
  and editing it for readable slides. Do not discard substance for oversized
  headlines or conduct unrelated research. Fill routine transitions directly;
  distinguish substantive unverified additions in the existing evidence or
  copy metadata.
- **Research:** Copy the substantive, source-traceable synthesis produced by
  Logic. Do not use copy editing to replace missing research, unsupported
  claims, or unresolved evidence with generic benefit language.
- **Mixed:** Keep section responsibilities assigned through existing scope or
  notes fields and preserve the boundary between execution sections and
  research sections. Do not add a new mode schema.

## Boundaries

Own precise wording for titles, the Storyline required by the active master, optional supporting copy, numbers, units, punctuation, intentional breaks, notes, copy hierarchy, and stable `copy_id` values. Do not decide master placeholder position or visual layout.

Do not change Logic-approved facts, claims, relationships, page responsibilities, management stages, cross-slide invariants, or slide order. Do not choose visual layout or create PPTX objects.

## Required context

Read `../../packages/contracts/stage-enablement.md` for task authority, relevance-based retrieval, professional review, and measured execution. It supersedes legacy requirements to select every source, rediscover unchanged resources, or treat aesthetic heuristics as mandatory gates.


1. Consume the root's validated v2 task selection and merged `task-config.json` from the unified configure-task flow. If absent, return to root to prepare it once; do not select a config by the presence of a Personal Runtime. Preserve that configuration and its hash through the remaining stages.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the Logic package, its ready `resource_inventory`, and the
   hash-bound Logic-to-Copy calibration before editing copy. Preserve the
   inventory lock; additional eligible records in its locked pools are normal
   retrieval. A new pool, Provider snapshot or external asset returns to
   Supervisor for a revised inventory and user brief.
4. Read `references/copy-package-contract.md`. This core contract is mandatory and never search-dependent.
5. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
6. Read the locale-matched `../clayz-presentation-supervisor/references/first-class-index-gate.md`. Reuse the unified task configuration and Provider lock. Materialized sources are required only when actually selected and declared for this stage; a personal settings layer alone never requires private learning sources.
7. Classify optional Copy signals and resolve them through the built-in Capability Index. For nested meaning or multiple renderable units, use signals such as `nested-meaning` or `atomic-copy` rather than hard-coding an optional reference read.
8. Load only optional `knowledge_refs` returned by selected capability records. Preserve the resolution and retrieval receipt IDs; unresolved signals remain explicit gaps and never trigger invented guidance.

When the root supplies knowledge from a prior discussion, consume only the
complete verified committed revision selected through the existing Index.
Preserve its confirmation and attachment hashes, provenance category,
evidence limits, applicability, and unresolved questions in the copy evidence.
A draft, unconfirmed consensus, or attachment outside that committed snapshot
is not a Copy source, and
Copy never creates or commits a discussion record.

## Workflow

Apply the shared artifact-led Library loop to an actual copy draft before locking
it: draft -> specific expression question -> Copy Library passage/example ->
revised copy -> meaning and reading check. Compare the before/after wording of
the affected copy IDs for clarity, evidence qualifiers and on-slide load. Borrow
an expression principle, not unrelated facts or a stock slogan. An unchanged
draft with a concrete rejection reason is valid. When a rendered page is too
dense, shorten or redistribute copy within Logic's meaning, then return it to
Art Direction; meaning or page-sequence changes belong to Logic.

1. Preserve every approved claim, evidence qualifier, task acceptance requirement, and generation-mode responsibility, including the provenance, limits, and unresolved questions carried by confirmed discussion knowledge. Absorb the Supervisor's Logic calibration before locking Copy; record an `accepted`, `partially-accepted`, or `declined` calibration binding with a reason. In execution sections, keep supplied information coverage and fill only routine editorial gaps; in research sections, keep the Logic synthesis and its evidence boundaries explicit.
2. If Logic does not contain enough concrete evidence or relations to satisfy a Copy-owned requirement, raise an upstream conflict instead of replacing the gap with abstract benefit language.
3. Write titles that state the page function or conclusion without exaggeration and respect the task's cover and conclusion-placement policy.
4. Write the required Storyline according to the active master's semantic role. A smaller supporting sentence beneath it is optional: add one only when it contributes independent information, and omit it entirely when it would merely restate the Storyline or fill space. Do not treat this optional support line as a mandatory Storyline field.
5. Break visible text into atomic units. Assign one stable `copy_id` to each unit and express parent-child and peer relationships explicitly.
6. Lock exact text, numbers, units, punctuation, intentional breaks, and speaker notes.
7. Keep charts and tables supplied with complete labels, units, sources, and explanation text.
8. Raise upstream conflicts instead of silently fixing Logic. Generic phrases such as reduced experience, weakened certainty, or better coordination do not satisfy a requirement unless the Copy units identify the responsible operation and audience consequence.
9. Emit task-local learning candidates with language, audience, evidence, and limits; persist them only through the configured Copy learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.
10. Emit one package with `origin_namespace: io.clayz.presentation` and status `copy-approved`; preserve root `acceptance_contract` and `resource_inventory`, and add bounded relevance-ranked Copy receipts to root `index_evidence`. Every selected record must name the concrete title, storyline, copy unit, or language decision it materially influenced. Passing structure alone is insufficient: cross-slide duplicate titles, storylines, transition formulas, grammar vectors, and substantial phrases must pass deterministic variation checks unless Logic declared a purposeful series.

## Validation

Run:

```bash
python ../../packages/validators/validate_ppt_package.py <copy-package.json>
```

Send the validated package to both `$clayz-presentation-art-direction` and
Supervisor. Art Direction consumes the hash-bound Copy calibration before
locking its plan. Supervisor may identify a defect or route an upstream change,
but Copy remains the owner of wording and never rewrites Logic silently.

## Work record at handoff

Read the stage-work-record section of `../../packages/contracts/stage-enablement.md`. Save this stage's actual artifacts to immutable task-local revision files, record the work and real checks with `scripts/publish_supervised_pair.py record-stage --stage copy`, and attach `work-notes` when evidence qualifiers, wording tradeoffs, coverage preserved or omitted, intentional breaks, speaker notes, or a material copy decision needs richer context. Verify the available record chain with `check-records` before handoff. Include the immediate predecessor record after Logic. Binding, identity, format or evidence-integrity failures cannot be replaced by a prose pass; quality findings may travel with explicit evidence. Missing notes remain `not-recorded`; Supervisor collects all four records, adds its coordination record and binds the independent audit artifact; it must not invent prior work or deliver a separate summary as the final report.

The central baseline is `../../config/default.json`; consume it through the unified merger with personal settings and task overrides, never as a separate production route.
