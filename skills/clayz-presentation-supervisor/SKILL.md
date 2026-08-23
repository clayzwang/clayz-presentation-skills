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
3. Read `references/supervision-contract.md` and `references/failure-pattern-routing.md`. These authority and routing contracts are mandatory and never search-dependent; the existence of a matching Failure Pattern is search-dependent.
4. Read `../../packages/contracts/knowledge-learning.md` before routing reusable observations. This governance contract is mandatory and never search-dependent.
5. Classify optional audit signals and resolve them through the built-in Capability Index. Typical signals include `plan-object-render`, `medium-fidelity`, `runtime-conflict`, `environment-observation`, `interaction-failure`, `retry-loop`, `execution-ledger`, and `failure-recovery`.
6. Load only optional `knowledge_refs` returned by selected capability records. Resolve an optional Failure Pattern only from observed evidence and keep its retrieval receipt ID. Unresolved signals stay explicit and never authorize invented diagnoses, repair methods, or silent intervention.

## Workflow

1. Bind the exact hashes of the Logic package, Copy package, Art Direction plan, PPTX, render root, object inventory, deviation log, QA report, resolved configuration, and available retrieval receipts.
2. Audit business relationships and content readiness before visual quality.
3. Compare approved importance with actual visual attention, and approved medium with actual object types and rendered appearance; use the resolved medium-fidelity capability when applicable.
4. Check cross-slide invariants, series behavior, semantic whitespace, motif, reading order, typography, data labels, connectors, and target-application compatibility.
5. Treat written PPTX objects and final renders as stronger evidence than in-memory success messages; use environment-grounded observation only when that capability was resolved.
6. For every issue, record evidence, expected state, actual state, impact, severity, confidence, earliest responsible layer, and recommended return target. A registered Failure Pattern may support this classification only when selected in a receipt and matched to actual rendered evidence.
7. Distinguish deterministic failures from professional judgment and from unresolved uncertainty. Interaction and retry-loop diagnoses require their corresponding resolved capabilities; optional Failure Pattern gaps remain `unresolved` rather than becoming invented codes.
8. Return reusable learning candidates to Logic, Copy, Art Direction, or Output with evidence and limits; never create a Supervisor learning silo or promote a candidate automatically.
9. Emit one report with `origin_namespace: io.clayz.presentation` and status `supervised`; task-local audit evidence should retain the capability resolution and retrieval receipt IDs used for optional knowledge.

## Validation

Run:

```bash
python ../../packages/validators/validate_supervision_report.py \
  <copy-package.json> <art-direction-plan.json> <output-qa.json> \
  <object-inventory.json> <supervision-report.json> \
  --config ../../config/default.json
```
