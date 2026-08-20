# Environment-Grounded Observation and Repair-History Audit

This route is informed by execution history, error feedback, slide inspection, and content/design/coherence facets described by [PPTAgent](https://github.com/icip-cas/PPTAgent) and [DeepPresenter](https://arxiv.org/abs/2602.22839). Supervisor remains independent: it diagnoses but does not modify, and automated scores are never ground truth. See `provenance/manifest.yaml` for attribution and redistribution boundaries.

## Evidence order

1. Approved `ppt-design-package.json` and `ppt-art-direction-plan.json`.
2. Source hashes, observation cycles, controlled actions, failures, and challenges in `ppt-build-deviation-log.json`.
3. Written PPTX objects, final-reopen renders, fonts, configured target-application facts, size, and compatibility evidence.
4. Output QA self-assessment.
5. Automated scores and external-case comparisons.

Item 5 may identify anomalies worth review but cannot override items 1–4. “Tool succeeded,” an HTML check, an existing object, or one healthy previewer never replaces observation of the final reopened PPTX.

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
