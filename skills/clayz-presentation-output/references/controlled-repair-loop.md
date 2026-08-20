# Controlled Actions and Environment Feedback Contract v1.1

This contract is informed by [PPTAgent](https://github.com/icip-cas/PPTAgent), specifically its bounded action vocabulary, execution history, failure feedback, and targeted retry pattern. Here those ideas operate below `ppt-design-package.json` and `ppt-art-direction-plan.json`; they do not create a second source of content or visual truth. See `provenance/manifest.yaml` for attribution and redistribution boundaries.

## Authority order

`approved Logic / Copy / Art Direction → configured renderer's technical actions → written PPTX objects and renders → Output QA → independent Supervisor observation`

In-memory state, a tool's “success” response, one previewer, an automated score, or an agent's self-assessment cannot override the written object tree and actual renders. Environment feedback may trigger a technical repair or upstream challenge, never a silent copy, composition, or master change.

## Evidence record

Each build creates `ppt-build-deviation-log.json`, contract version `1.1`, containing both implementation deviations and a small number of critical observation cycles:

- `source_bindings`: SHA-256 values for the approved package, Art Direction plan, and current PPTX.
- `environment_precedence`: fixed to `written-pptx-and-render-over-in-memory-state`.
- `scoring_policy`: fixed to `evidence-not-score`.
- `cycles`: initial written-file observation, targeted repair, and final reopen observation.
- `deviations`: technical differences between plan and implementation.
- `challenges`: issues that require Logic, Copy, Art Direction, or environment backflow.
- `final_status`: `pass`, `known-risk`, or `incomplete`.

The log is execution evidence, not a new approval contract. It may not contain unapproved copy, an alternative composition, or arbitrary executable code.

## Controlled action vocabulary

Targeted repair is limited to:

- `reposition-object`
- `resize-object`
- `reorder-layer`
- `route-connector`
- `adjust-crop`
- `replace-approved-asset`
- `repair-native-chart`
- `repair-native-table`
- `repair-font-encoding`
- `repair-compatibility`
- `deduplicate-media`
- `optimize-raster`
- `remove-duplicate-object`
- `restore-master-inheritance`

Every action binds a `slide_id`, stable `target_ids`, preconditions, execution status, and evidence. `authority` is always `output-technical`; `changes_approved_content` and `changes_art_direction` are always `false`. If the approved baseline must change, create a `challenge` instead of an action and route it to Supervisor and the user.

## Cycle

1. `initial-render`: write and reopen the current PPTX; record object, font, compatibility, size, and slide-render evidence. It may contain no repair action.
2. `targeted-repair`: repair only affected slides and objects. Declare `repair_of`; do not rewrite the whole deck to conceal a local failure.
3. After each repair, rewrite, reopen, and render affected slides. Record machine evidence separately from visual interpretation.
4. `final-reopen`: reopen the final written file, render the complete deck, and bind its final hash. Only this cycle can produce final `pass`.

Any failed or partially successful cycle must lead to a further targeted repair, an upstream challenge, or a documented decision to proceed with visible risk. Failure cannot remain only in console output or model context.

## Validation

```powershell
python scripts/validate_build_deviation_log.py `
  ppt-design-package.json ppt-art-direction-plan.json `
  ppt-build-deviation-log.json --pptx final.pptx
```

Passing validation means the evidence structure is complete, actions stayed within authority, and hashes are traceable. It does not approve visual quality; slide-level Output QA and Supervisor still make that judgment.
