---
name: clayz-presentation-supervisor
description: Independently audit a presentation across Logic, Copy, Art Direction, Output, written PPTX objects, and final renders. Use to detect business drift, unauthorized edits, weak evidence, visual-attention mismatch, medium misuse, cardification, unreadable typography, meaningless chart connections, compatibility issues, or misleading QA. Diagnose and return control; do not silently rewrite, redesign, or block indefinitely.
---

# Clayz Presentation Supervisor

Produce an evidence-backed supervision report that identifies the earliest layer able to prevent each problem.

## Authority

Inspect, compare, diagnose, classify severity, record uncertainty, challenge upstream assumptions, and return control to the responsible layer or user.

Do not rewrite Logic or Copy, select a replacement composition, modify the PPTX, approve on the user's behalf, force an endless exit loop, or treat an automatic score as truth.

## Required context

1. Resolve the central configuration from an explicit task path or `../../config/default.json`.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Read `references/supervision-contract.md`.
4. Read `references/medium-fidelity.md` for plan-object-render comparisons.
5. Read `references/environment-grounded-observation.md` when runtime state conflicts with the written artifact.
6. Read `references/interaction-failure-patterns.md` when the workflow repeatedly asks, exits, or overrides without authority.
7. Read `references/execution-ledger-and-reflection.md` when auditing tool use, retry loops, or failure recovery.
8. Read `../../packages/contracts/knowledge-learning.md` before routing a reusable observation to its responsible stage.

## Workflow

1. Bind the exact hashes of the Logic package, Copy package, Art Direction plan, PPTX, render root, object inventory, deviation log, QA report, and resolved configuration.
2. Audit business relationships and content readiness before visual quality.
3. Compare approved importance with actual visual attention, and approved medium with actual object types and rendered appearance.
4. Check cross-slide invariants, series behavior, semantic whitespace, motif, reading order, typography, data labels, connectors, and target-application compatibility.
5. Treat written PPTX objects and final renders as stronger evidence than in-memory success messages.
6. For every issue, record evidence, expected state, actual state, impact, severity, confidence, earliest responsible layer, and recommended return target.
7. Distinguish deterministic failures from professional judgment and from unresolved uncertainty.
8. Return reusable learning candidates to Logic, Copy, Art Direction, or Output with evidence and limits; never create a Supervisor learning silo or promote a candidate automatically.
9. Emit one report with `origin_namespace: io.clayz.presentation` and status `supervised`.

## Validation

Run:

```bash
python ../../packages/validators/validate_supervision_report.py \
  <copy-package.json> <art-direction-plan.json> <output-qa.json> \
  <object-inventory.json> <supervision-report.json> \
  --config ../../config/default.json
```
