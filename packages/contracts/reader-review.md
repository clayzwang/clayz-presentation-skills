# Reader review — v0.20.1

## Production order and ownership

1. **Logic research:** save substantive conclusions, supporting evidence, reasoning, scope and uncertainty in the approved research package. Explicitly show what was learned. A research agenda, framework or method is not a conclusion. Repeated research rework belongs to Logic quality accounting.
2. **Copy:** finish the complete reader-facing explanation, page sequence, titles and body against Logic. Preserve the research baseline.
3. **Title reader:** a fresh context sees only the ordered visible titles and neutral task brief. Freeze its understanding, then compare it with approved Logic. Supported research conclusions advance; expression defects return to Copy.
4. **Content reader:** another fresh context reads all visible Copy. Freeze understanding, then compare accuracy, completeness and reasoning with approved Logic. Pass advances; expression defects return to Copy. A demonstrated source or research fault may return to Logic with evidence and accountable ownership.
5. **Art:** begin task-specific design, page planning and prototypes only after both current reviews pass. Do not build a full draft or render speculative pages while Copy is unsettled.
6. **Output:** implement the approved Art plan and render the actual deliverable.
7. **Final reader and audit:** a third fresh context reads the actual rendered pages, freezes understanding, then compares with approved Copy. Failure returns to Art; Art can assign a faithful implementation repair to Output without redesigning unaffected pages.
8. **Supervision report and delivery:** assemble the actual evidence and deliver after the final gate passes. Upload is outside this workflow; perform it only when separately requested.

These are internal production gates, not repeated user approval requests. A missing capability is honestly recorded; a new-flow gate cannot call unavailable or shared-context execution a pass. Historical `copy`/`final` reviews remain replayable under their original policy.

## Reader isolation and reconciliation

For a presentation task this contract explicitly requests fresh reader delegation when the host supports it. Use actual host dispatch with no inherited conversation (for example `fork_turns="none"`). Title, content and final readers must use distinct contexts. A Python subprocess, role label or claimed model name is not evidence of isolation.

Prepare a packet with `scripts/reader_review.py prepare --phase title|content|final --package COPY --brief BRIEF --directory INPUT --output PACKET`. Final also needs `--pptx PPTX --renders RENDERS` (or an honest unavailable reason). Give the reader only the input directory. Keep manifests, research, author notes, prior findings and design rationale outside its first input. The neutral brief contains only `audience`, `purpose`, `task`; it must not suggest an answer. PNG metadata is removed without changing pixels.

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

Each original finding gets exactly one disposition: `finding_id`, `owner_layer`, `status` (`open` or `disputed-with-evidence`), `explanation`, and `evidence_refs` drawn from the bound evidence. Preserve disagreement and first impressions; a correction requires a new reading, linked with `--previous-review`. Never relabel an old observation as a new pass.

## Executable handoffs and recovery

Run `check-art-gate --package COPY --title-review TITLE --content-review CONTENT` before Art. Pass those two review arguments to `scripts/stage_documents.py record-planning` and `lock-design`; the current default config enforces the gate. Bind `config`, `package`, `reader-review-title`, `reader-review-content` into the Copy work record so Copy-to-Art calibration verifies it too. The content packet must be created after title reconciliation. Final audit binds these plus `reader-review-final`; new-flow delivery requires all three to pass.

Original files and SHA-256 bindings stay immutable. Current title reuse compares ordered titles, task binding and the complete Logic research/brief. Current content reuse also compares all visible text. Body-only edits can reuse title reading; title or research changes invalidate the appropriate readings. Metadata-only edits can rebind records without rerunning readers. Changed PPTX bytes always invalidate final reading; unchanged prose alone cannot certify unchanged rendering.

`record-stage`, `record-calibration`, `record-audit`, `record-first` and `reconcile` accept an identical-input retry at the same destination, verify bound bytes and preserve original timestamps. Changed input requires a new destination/version. Explicit timestamp changes must not be used to manufacture order. Audits validate completely before saving; invalid model disclosure, evidence, roles or coverage must be repaired locally before recording.

Use `repair-scope --before OLD_COPY --after NEW_COPY --artifact copy|report|audit-record|receipt` to obtain the minimal restart route. Report/receipt formatting errors resume record validation and assembly, without rebuilding PPTX or repeating Office execution. Actual content changes rerun affected readers and downstream production. Final visual failures return to Art for affected-page repair, then Output and fresh final reading.

Use canonical artifact roles: Logic/Copy `package`; Art `plan`; Output `qa`, `inventory`, `pptx`; Supervisor `draft`, `pptx`, `auditor`. Known aliases normalize before validation; missing roles fail at the recording call. Evidence references use a bound kind (preferred), absolute path, or an unambiguous basename plus `sha256=...`; relative paths resolve from the command working directory. Ambiguous basenames never silently select a file. Model disclosure is an enum: `not-attested`, `same-model-possible`, `provided-by-host`; put explanatory prose in context limitations.

The supervision report collects all frozen reviews and prior findings, the actual repair route and Logic returns. It must distinguish substantive failures from handoff/format failures and report retries without attributing them to business research.
