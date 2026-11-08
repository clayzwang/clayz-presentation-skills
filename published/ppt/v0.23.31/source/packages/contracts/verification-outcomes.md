# Interpreting verification results — v0.18.2

Keep tool execution, record integrity and artifact quality distinct. Use existing
checks, calibration findings, audit coverage and work notes; no additional manual
approval form or presentation-level gate is introduced.

| Observation | Interpretation and response |
| --- | --- |
| A tool throws an exception or does not finish | Tool error; that check has not established artifact quality. Preserve the command and error, fix the cause and rerun the affected check. |
| A rule cannot handle a supported format | Applicability/compatibility problem. Preserve the original failure and separately bind independent evidence; do not silently turn it into a pass. |
| Required identity, bindings, source evidence or record structure is invalid | Integrity defect. Repair the affected record and revalidate; a quality opinion cannot replace missing evidence. |
| Actual content, scope, numbers, legibility or editing behavior is wrong | Quality finding. Cite the sentence/object/page and route it to the earliest responsible stage. |
| A check completes successfully | Only the stated check and observed coverage pass. No whole-deck content or design pass is implied. |

Raw tool results, independent assessments and repair dispositions remain separate.
A declared quality `fail` is not itself a malformed record. `deferred` and
`uncertain` preserve missing coverage. Unknown statuses and contradictory pass
claims remain record errors. Nonempty remaining issues do not become syntax
errors merely because they exist; they still prevent an all-clear QA result.

The native comparator, Output QA validator and deviation-log validator support
`--result-json <path>` to write an automatic diagnostic alongside console output.
It distinguishes execution (`completed`, `error`, `not-run`), record validation
(`valid`, `invalid`, `unverified`) and scoped quality (`pass`, `fail`, `unverified`),
retaining the original messages. Existing nonzero outcomes remain nonzero. A
deviation-log structure pass does not certify the PPTX. A comparison allowing
extra text is diagnostic, not final acceptance.

Keep old results when a newer tool fixes a bug. An exception does not authorize
a pass or prove a content defect. Rerun only affected checks/pages after repair;
unchanged deterministic evidence can be reused. Follow existing user-defined
release conditions and binding-complete publication policy without another
approval loop.
