# Production reliability in 0.17.5

This contract supersedes older font-size thresholds, consecutive-composition caps and inline report storage requirements.

## Art judgment

No configured consecutive silhouette/density ceiling applies to non-series body slides. Legacy fields are inert.
Art reviews excessive repetition in the actual deck; never reorder content just to break a run.
Remove automated minimum, even/integer-point and size-variant checks and generated numerical size commitments.
Historical style sizes remain draft suggestions. Preserve explicit user requirements for actual Art review.
Copy states concrete information relationships, importance and necessary qualifications; Art implements grouping,
space and attention. Generic reading-order prose, complete text and zero overflow do not establish good design.
Inspect the real pages: can necessary definitions be read, can values be understood with their conditions, should
available space relieve cramped information, does repetition help the reader? Use existing work records for the
specific page/object, observation, modification and result. No new approval form or aesthetic score.
Repair reversible issues; explain any retained defect. Disclosure is not repair. Supervisor challenges the actual
reason and returns issues to the earliest responsible stage.

## Fonts and environment

Release bundles may include only manifest-bound fonts with recorded source and redistribution authorization.
STKaiti is excluded from 0.17.5 because authorization is unavailable; its absence does not block release.
For tasks requiring it, install from a licensed source and report absence/substitution explicitly.
The following bundle registration command applies only when authorized fonts are actually bundled.
Run `python scripts/font_bundle.py --prepare <task-root>` and use its FONTCONFIG_FILE for Art and Output
render processes. It verifies fc-match resolves to the exact bundled file/hash; substitution is not acceptance.
Install the supplied fonts in Windows/macOS following the bundle instructions. Actual PowerPoint/WPS reopening
remains separate from Linux rendering. Pin requirements.txt and include renderer versions and the font manifest
among task_runtime inputs; changed environments invalidate cached render evidence.
Task runtime records start/end, elapsed time, timeout and consecutive failures. After two identical failed commands
with unchanged inputs, repair the cause before retrying. Record timestamps are not pure compute duration.
Recheck affected pages; unchanged deterministic checks may reuse byte-bound evidence.

## Editability and size

Prefer integrated native tables, native chart data labels and standard slide numbering. Fragmented one-cell tables,
independent chart labels and custom number fields are editing limitations requiring explicit deviation/audit records.
Object counts alone do not establish equivalent editing. Check row insertion, workbook/label updates and numbering
after page insertion, or disclose deferred checks. Output runs audit_pptx_size and optimizes duplicate/unused media
and oversized images while preserving visible quality and editable objects. A PPTX at or above 20,000,000 bytes
cannot use ordinary publication: optimize first, with Supervisor reviewing the final size and any loss. Evidence
bundle size is separate; never rasterize whole pages or remove necessary content to satisfy size control.

## Narrative, evidence and hashes

New configurations default to external-evidence. The publisher first validates original records, then losslessly
externalizes content-addressed evidence. The prose does not repeat inline images or large source bodies.
Relative paths, byte counts and SHA256 bind every file. verify-handoff expands and validates original records
and deterministic Markdown. `python scripts/restore_report.py <report.json> --output <new-full-report.json>`
restores complete records. Report 3.6 semantics and legacy embedded reading remain; do not relabel history.
The stage ZIP is a separately usable derived handoff. Distinguish independent and shared-context audits and
unperformed native application checks; missing fonts across a deck are material presentation evidence gaps.
