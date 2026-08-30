# Environment-Grounded Observation and Repair-History Audit

This route is informed by execution history, error feedback, slide inspection, and content/design/coherence facets described by [PPTAgent](https://github.com/icip-cas/PPTAgent) and [DeepPresenter](https://arxiv.org/abs/2602.22839). Supervisor remains independent: it diagnoses but does not modify, and automated scores are never ground truth. See `provenance/manifest.yaml` for attribution and redistribution boundaries.

## Evidence order

1. Approved `ppt-design-package.json` and `ppt-art-direction-plan.json`.
2. Source hashes, observation cycles, controlled actions, failures, and challenges in `ppt-build-deviation-log.json`.
3. Written PPTX objects, final-reopen renders, fonts, configured target-application facts, size, and compatibility evidence.
4. Output QA self-assessment.
5. Automated scores and external-case comparisons.

Item 5 may identify anomalies worth review but cannot override items 1–4. “Tool succeeded,” an HTML check, an existing object, or one healthy previewer never replaces observation of the final reopened PPTX.

## Environment facts belong in the final audit

Supervisor must embed the `runtime-preflight.json` scan ID, raw-file SHA-256, script-issued run ID, task-request SHA-256, nonce, task-root SHA-256, issue/expiry timestamps, challenge SHA-256, canonical issuance- and consumption-ledger SHA-256 values, resolved-config SHA-256, locked route, satisfied, declared-unverified, and missing route requirements, and every target application's available/unavailable state in `ppt-supervision-report.json.environment_observation`. Both ledger files must exist at their canonical paths under the bound task root and their actual bytes must match the preflight binding. Any available host capability must also preserve its challenge-bound run/task values, inspected source, observation time, and structured receipts for hash-checked inventory files. Never relabel an ordinary declaration as `verified: true`: it may make a native route provisional/attemptable but never ready. A filename-only reference, unbound capability claim, generic lifecycle placeholder, or conversational summary is not a complete record.

Target-application acceptance is not a pre-Logic gate. Scan every configured target even when absent. Record unavailable PowerPoint, WPS, or LibreOffice native reopen capability as `deferred`, an available but unused target as `not-selected`, and an executed target as `pass` or `fail`. Every target needs evidence references and `authoring_gate=false`. Only failure of the authoring, write, inspection, or rendering route itself may block production during preflight.

When any target is `deferred` or `not-selected` and no other issue exists, use root status `complete-with-deferred-acceptance`. The PPTX and audit report may still be delivered as a pair, but the report must not claim certification for an unexecuted application. A provisional native route remains provisional in the preflight section even after Output; delivery becomes ready only because the publisher independently validates the written PPTX, object inventory, QA evidence, and final renders. Final handoff is valid only after `scripts/publish_supervised_pair.py` revalidates these bindings and materializes the PPTX, report, and `delivery-manifest.json` in one new bundle.

## Audit questions

- Is each repair bound to affected slides and stable target IDs rather than an untargeted whole-deck rewrite?
- Does each action stay inside the controlled technical vocabulary without changing approved copy or Art Direction?
- Are failures and partial successes preserved as evidence and followed by a targeted repair or upstream challenge?
- Is the written file reopened and affected slides rerendered after repair, followed by a full final rerender?
- When the build log claims Art Direction is unchanged, do the final renders actually preserve first visual, area, medium, series behavior, and semantic whitespace?
- Does Output QA inspect environment facts before concluding, rather than restating its own action history?

## Suggested finding codes

- `BUILD_OBSERVATION_EVIDENCE_MISSING`: no environment-grounded observation or final-reopen evidence.
- `BUILD_ACTION_SCOPE_OVERREACH`: a technical action exceeds its target or silently changes the approved baseline.
- `REPAIR_WITHOUT_RENDER_EVIDENCE`: a repair is not verified from a reopened written-file render.
- `BUILD_ERROR_HISTORY_DROPPED`: a failure or partial success is absent from the execution log.
- `QA_SCORE_TREATED_AS_TRUTH`: an automated score overrides a contract, object fact, or real render.

Finding codes are diagnostic labels, not automatic stop decisions. Handle each issue through severity, evidence, impact, responsible layer, and user adjudication.
