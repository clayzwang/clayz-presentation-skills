# Bounded reading and repair contract — v0.20.5

A cycle is a production checkpoint, not a quality score. Each task has one Copy cycle and one final cycle. Do not create a new cycle/run ID to reset an exhausted repair allowance. User-requested new scope starts a distinct task with explicit provenance.

## Order and evidence

1. Deliver complete Copy. Prepare title and content packets using the same Copy bytes and `--config CONFIG`; title and content use different fresh host contexts and may execute concurrently. Do not expose research, author rationale or the other reader's feedback during their first reading. Each then reconciles with Logic. Preserve the existing first-read/review records.
2. `python scripts/reader_cycle.py collect --phase copy --config CONFIG --package COPY --review TITLE_REVIEW --review CONTENT_REVIEW --output COPY_CYCLE` freezes references to both reviews. Collection fails if either review is missing, not actually observed, stale or non-independent.
3. With findings: `start-repair --cycle COPY_CYCLE --owner copy --rationale "Consolidated title and content issues"`. This reserves the single repair before dispatch; a second reservation is rejected. Fix the consolidated issues in a new Copy file; preserve the old package/first readings. Do not rewrite research to make a title pass.
4. Send the revised title input back to the original title context and full visible Copy back to the original content context using the host's actual follow-up mechanism. They each confirm their original findings/comparison and report new findings. This follow-up has history; do not call it a new blind independent first reading. If the original context cannot be resumed, disclose incomplete evidence; do not impersonate it or substitute a new reader silently.
5. Close with `close --cycle COPY_CYCLE --closure CLOSURE_JSON`. Closure must bind actual repaired files, owner checks and both confirmations. Art calls `reader_review.py check-art-gate --config CONFIG --package REVISED_COPY --title-review TITLE_REVIEW --content-review CONTENT_REVIEW --reader-cycle COPY_CYCLE`. Pass the same arguments to `stage_documents.py record-planning` / `lock-design`. Bind the closed cycle as `reader-cycle-copy` in Copy work artifacts before Copy-to-Art calibration.
6. Final: `collect --phase final --config CONFIG --package COPY --plan PLAN --pptx PPTX --renders RENDERS --review FINAL_REVIEW --output FINAL_CYCLE`. It starts after Output and the closed Copy cycle. If findings exist, reserve one repair with owner `art-direction` or `output`. Art may change its documented presentation projection; the approved Copy bytes remain immutable. Re-render the repaired actual PPTX, then send it to the **same final context** for confirmation. Close once. Remaining/new issues are report-only.
7. Independent Auditor starts after both cycles close, records issues without dispatching repair, and binds `config`, current `package`, current `plan`, `reader-review-title`, `reader-review-content`, `reader-review-final`, `reader-cycle-copy`, `reader-cycle-final`, plus the actual final PPTX and normal audit artifacts. All paths, hashes, sizes, task/run binding and order must match. Supervision includes original observations and cycle outcomes; unresolved/new findings cannot be omitted.

A cycle with no findings closes without repair using unchanged baseline artifacts, `resolutions: []`, `confirmations: {}`. Each cycle with issues gets one attempt, not a promise to resolve everything. The second reading is mandatory after repair but cannot authorize a second attempt. Auditor recommendations are future-task/version recommendations only.

## JSON records

Every file reference is `{ "path": "/absolute/file", "sha256": "actual digest", "bytes": 123 }`. Validators verify actual bytes. These schemas document evidence; they never create a host receipt or decide comprehension.

Closure JSON has `artifacts`, `resolutions`, `confirmations` and (when repaired) `verification`. `artifacts` is `{package: REF}` for Copy and `{package: REF, plan: REF, pptx: REF, renders: REF}` for final. The CLI records `closed_at` only after successful validation.

Each resolution is `{issue_id, status, explanation, evidence: [REF]}`. Status is `resolved` or `remaining`. Issue IDs are `title:FINDING_ID`, `content:FINDING_ID`, `final:FINDING_ID`, plus `PHASE:comparison` for non-pass comparison. Every issue appears exactly once. Closure resolutions must exactly equal the corresponding original reader's confirmation, not an author's override.

`verification` references the repair owner's record: `{owner, artifacts, checks: [{status: "pass|fail|deferred", observation: "actual check result"}]}`. Failed checks remain disclosed, not rewritten as passes.

`confirmations` maps `title` and `content` (Copy) or `final` to separate files with:

```json
{
  "contract": "io.clayz.presentation.reader-confirmation/1.0",
  "phase": "title",
  "context_id": "actual-original-title-context",
  "binding": {"run_id": "actual-run", "task_request_sha256": "actual-task-digest"},
  "artifacts": {"package": {"path": "/actual/repaired-copy.json", "sha256": "actual", "bytes": 123}},
  "reviewed_at": "actual ISO timestamp after repair",
  "host_receipt": {"path": "/actual/follow-up-receipt.json", "sha256": "actual", "bytes": 123},
  "resolutions": [],
  "new_findings": []
}
```

Fill resolutions from that reader's actual review. A reader with no original issues must still reread after the shared Copy repair and explicitly return `[]` when nothing new is found. New findings have `finding_id`, `slide_ids`, `statement`, `reader_impact`, `visible_evidence` and are report-only. The host receipt contains `host_tool`, the same `context_id`, `input_artifacts` matching repaired artifacts, and `raw_receipt` pointing to the actual host response. Reader-facing visible inputs retain the title/content/final scopes; these bindings describe their source artifacts, not permission to expose author-only fields.

Cycle updates are guarded by an exclusive lock and closed cycles are immutable. After a crashed process, inspect retained evidence before clearing its lock; never automatically reserve another repair. This is local orchestration enforcement, not a security boundary against manually forged files.

## Compatibility and limits

Old records without `repair_policy` retain legacy validation; selected v0.20.5 config defaults to `consolidated-once`. Always pass the selected config to preparation and gates. Historical raw findings remain historical even when confirmation records them resolved. Numeric scoring, fabricated host execution, and silent conversion of concerns to clean passes are forbidden. A valid cycle proves traceable execution, not business truth, design quality or native PowerPoint/WPS acceptance.
