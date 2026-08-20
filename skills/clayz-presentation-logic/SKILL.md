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

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Record the configuration SHA-256 as `configuration_sha256`.
4. Read `references/logic-package-contract.md` for the package contract.
5. Read `references/research-and-reasoning.md` when evidence must be gathered or calculations must be audited.
6. Read `references/semantic-logic-model.md` for complex relationships or repeated series.
7. Read `../../packages/contracts/knowledge-learning.md` before retrieving prior learning or persisting a reusable observation.

## Workflow

1. Lock the audience, material type, desired outcome, scope, and production profile.
2. Inventory all supplied material before interpreting it. Separate facts, calculations, interpretations, causal claims, targets, recommendations, hypotheses, and missing data.
3. Define terms, metrics, time windows, dimensions, exclusions, and comparison bases.
4. Build a natural question chain. Each page must answer one necessary question and create a justified next question.
5. Specify every slide's responsibility, evidence, decision weight, management stage, and relationship to adjacent slides.
6. Define cross-slide invariants and series only when repetition carries meaning.
7. Consolidate missing inputs into the smallest useful user interaction. Never invent data or imply approval.
8. Emit task-local learning candidates with evidence and limits; persist them only through the configured Logic learning route and never auto-promote them.
9. Emit one logic package with `origin_namespace: io.clayz.presentation` and status `logic-approved`.

## Validation

Run:

```bash
python ../../packages/validators/validate_logic_package.py <logic-package.json>
```

Hand the validated package to `$clayz-presentation-copy`.
