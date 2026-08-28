---
name: clayz-presentation-logic
description: Build the evidence, question chain, claims, management logic, and slide sequence for a presentation before wording or design. Use for presentation planning, management reports, business analysis, strategy, proposals, and training decks when the facts, decision outcome, argument structure, or page order must be established. Do not use to write final visible copy, choose composition, or build a PPTX.
---

# Clayz Presentation Logic

Create a `logic-approved` package that another agent can use without reconstructing the argument.

## Boundaries

Own audience, desired outcome, scope, source inventory, definitions, claims, evidence, uncertainty, question chain, page responsibilities, cross-slide invariants, and the analysis still required.

Do not finalize wording, punctuation, line breaks, typography, composition, theme, coordinates, or PPTX objects.

## Required context

1. Resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its lock and resolved config hash with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. The extension decision happens once before Logic and never creates another workflow stage.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Record the configuration SHA-256 as `configuration_sha256`.
4. Read `references/logic-package-contract.md` for the package contract. This core contract is mandatory and never search-dependent.
5. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
6. Read the locale-matched `../clayz-presentation-supervisor/references/resource-inventory-gate.md` and `../clayz-presentation-supervisor/references/first-class-index-gate.md`. Require the finalized resource inventory to prove all seven scopes were scanned, the user-facing brief was presented, and authoring started afterward. In owner-personal mode, materialize the required Logic Library source into `task-private-learning` before reasoning; a locator-only inventory or prose claim is not evidence.
7. Load the bundled public Provider declared by the resolved configuration or Personal Extension Runtime and bind its immutable snapshot first. When the extension is enabled, add only owner-private Providers whose declared stages include Logic plus the materialized task provider. Read each private manifest once through its selected logical mount, lock the current snapshot in the same task evidence, and build one `CompositeIndex`; a required missing Provider fails closed, while an optional missing Provider records public-core fallback.
8. Classify optional capability signals before loading optional references. Resolve them through the built-in Capability Index and retain the capability resolution plus full finalized Retrieval Receipts. Typical signals include `evidence-research`, `audited-calculation`, `complex-relationships`, and `repeated-series`.
9. Load only the optional `knowledge_refs` returned by selected capability records. If a signal is unresolved, record it explicitly and continue with core contracts or return the gap; never invent a capability or silently substitute unrelated guidance.

## Workflow

1. Validate and bind the Supervisor resource-inventory lock, then lock the audience, material type, desired outcome, scope, and production profile.
2. Interpret only task material marked selected in that inventory. Separate facts, calculations, interpretations, causal claims, targets, recommendations, hypotheses, and missing data.
3. Define terms, metrics, time windows, dimensions, exclusions, and comparison bases.
4. Build a natural question chain. Each page must answer one necessary question and create a justified next question.
5. Specify every slide's responsibility, evidence, decision weight, management stage, and relationship to adjacent slides.
6. Define cross-slide invariants and series only when repetition carries meaning.
7. Consolidate missing inputs into the smallest useful user interaction. Never invent data or imply approval.
8. Emit task-local learning candidates with evidence and limits; persist them only through the configured Logic learning route and never auto-promote them.
9. Emit one logic package with `origin_namespace: io.clayz.presentation`, status `logic-approved`, root `resource_inventory`, and root `index_evidence`; approval requires a ready inventory plus a finalized Logic receipt that consumed every required Logic source.

## Validation

Run:

```bash
python ../../packages/validators/validate_logic_package.py <logic-package.json>
```

Hand the validated package to `$clayz-presentation-copy`.
