# Reader review — v0.20.5

## v0.20.2 Art cognition and audited changes

The current [Art cognition contract](art-cognition.md) extends earlier fidelity instructions: preserve original Logic/Copy, but allow Art to revise meaning, argument, sequence and pagination without advance modification requests. Record actual presentation in `art_content`, conclusions/actions and selected knowledge in `art_cognition`. Output implements that recorded presentation. Independent final reading first sees only renders, then compares original Copy and every documented Art change. Difference alone is not failure; justification, accuracy, completeness and reasoning determine the audit result. Older “unchanged Copy” or “return wording/pagination to Copy” instructions apply only when no Art projection exists. New Art work covers A01—A11; these are cognitive results, not agents or approval gates.


## v0.20.5 bounded reader workflow (current default)

`workflow.reader_review.repair_policy = consolidated-once` is authoritative for repair timing and routing. It supersedes historical pass-until-clean, title-before-content and repeated-return instructions in this file. Legacy `strict-pass` remains available only for replaying its original evidence.

Complete Logic and Copy first. Two distinct independent readers then read the same delivered Copy: title-only and full-content; neither waits for the other's approval. Freeze both initial readings, reconcile each against Logic, and consolidate all issues before dispatching at most one Copy repair. After that repair, **both original readers reread their respective revised inputs**, confirm each original issue as resolved or remaining, and record newly found issues. This is confirmation, not another repair authorization. Close the Copy cycle and advance to Art with disclosed residual issues.

After Output, an independent final reader inspects actual rendered pages and compares them with Copy and the documented Art changes. Consolidate issues into at most one repair to **Art Direction or Output only**. The **same final reader reinspects the repaired rendered result**. Remaining and newly found issues enter the audit report; do not reopen Logic/Copy or dispatch a second repair. No issue means no repair or redundant confirmation.

The independent Auditor records issues and evidence only; its findings never trigger rework. Preserve original findings, owner checks, reader confirmations and all unresolved issues in the final report. Report `issues-found`/limitations honestly, not a fabricated clean pass. Missing actual reader execution or stale/mismatched evidence is not a completed cycle. Use the executable [reader-cycle contract](reader-cycle.md) and keep the two cycle budgets separate.

## Reader isolation and reconciliation

For a presentation task this contract explicitly requests fresh reader delegation when the host supports it. Use actual host dispatch with no inherited conversation (for example `fork_turns="none"`). Title, content and final readers must use distinct contexts. A Python subprocess, role label or claimed model name is not evidence of isolation.

Prepare a packet with `scripts/reader_review.py prepare --phase title|content|final --package COPY --brief BRIEF --directory INPUT --output PACKET --config CONFIG`. Final also needs `--pptx PPTX --renders RENDERS` (or an honest unavailable reason). Give the reader only the input directory. Keep manifests, research, author notes, prior findings and design rationale outside its first input. The neutral brief contains only `audience`, `purpose`, `task`; it must not suggest an answer. PNG metadata is removed without changing pixels.

The prepared input directory is the reader's first-reading evidence scope, not a response workspace. In the actual host dispatch, point to this run's generated neutral input and let its instruction specify the response fields and types; do not paraphrase a second, conflicting schema from memory. Separately give an explicit response output path outside the input directory. Permission to save that response does not permit reading neighbouring production evidence. This makes the existing prepare/isolation contract concrete; it adds no new reader phase or gate.

A refused record is evidence about the actual rejected condition, not by itself a judgment of comprehension or independence. For a format-only correction, preserve the first response and failure receipt, have the same reader map its original wording to the required representation, and retain the exact mapping and exposure scope. A string and an array are different JSON values even when they contain related wording; joining evidence items is not a general proof of semantic equivalence. Changed answers/findings or prior exposure to production evidence cannot be relabelled as a transport-only correction. Save the actual first reading before exposing comparison evidence, as already required; successful parsing, a fresh-context label and an empty finding list do not substitute for one another.

For the later confirmation dispatch, derive the requested issue coverage from the actual collected cycle, including PHASE:comparison for a non-pass comparison as defined in reader-cycle.md; do not copy only the first response finding list from a prior pass-case template. A missing resolution status or explanation needs the same original reader's professional addendum. It is not merely a format conversion, even when the earlier two issue judgments and the PPTX stay unchanged. Preserve the original response and the later addendum chronology. This implements the existing confirmation coverage, not an additional reading or repair allowance.

Capture the actual dispatch response in a raw receipt. The normalized host receipt binds `host_tool`, `context_id`, `production_context_id`, `history_inherited: false`, `access_scope`, exact `input_files` and `raw_receipt`. Access is `host-restricted`, `instruction-only` or `unavailable`; instruction-only is not filesystem isolation. Never manufacture receipts or responses. `same-context-limited` and `not-run` remain disclosed incomplete evidence.

The first response contains `assessment` (`understood`, `understanding-gaps`, `insufficient-input`), `title_reading`, `understanding` (question, answer, slide_ids, visible_evidence, uncertainty), and `findings` (finding_id, slide_ids, copy_ids, statement, reader_impact). Save it with `record-first` before exposing production evidence. Retelling is professional judgment; validators do not judge business truth or turn empty findings into comprehension.

Use `reconcile --first-read FIRST --dispositions DISPOSITIONS --evidence BASELINE --comparison COMPARISON --output REVIEW`. The comparison JSON contains:

```json
{
  "baseline": {"path": "/absolute/path/logic.json", "sha256": "actual-file-sha256", "bytes": 123},
  "checks": {"research_conclusions": "Cite the substantive Logic finding and explain how the title reading corresponds."},
  "verdict": "pass",
  "explanation": "Record the actual evidence-based comparison, not a generated approval."
}
```

For content and final, `checks` has `accuracy`, `completeness`, `reasoning`, each with a grounded observation. Title/content bind original `logic-approved` research equal to Copy's research; final binds `copy-approved` Copy. `baseline` must also occur in the bound evidence. Verdicts are `pass`, `return-copy`, `return-art`, `return-logic`. Freeze first, compare second even when no finding exists.

Each original finding gets exactly one disposition: `finding_id`, `owner_layer`, `status` (`open` or `disputed-with-evidence`), `explanation`, and `evidence_refs` drawn from the bound evidence. Preserve disagreement and first impressions; a correction requires the original reader confirmation specified in the cycle contract. Never relabel an old observation as a new pass.

## Executable handoffs

Use [reader-cycle.md](reader-cycle.md) for current handoffs, original-reader confirmation, artifact roles, one-repair budgets and audit bindings. Strict sequential gates and `repair-scope` apply only to historical strict-pass replay. They do not override the current selected policy.
