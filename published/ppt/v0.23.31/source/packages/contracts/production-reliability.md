# Production reliability in 0.17.6

This contract supersedes older font-size thresholds, consecutive-composition caps, table-downgrade exceptions and inline report storage requirements.

## Whitespace ownership

Art inspects actual whitespace on body, source and appendix pages: does it support grouping, hierarchy,
rhythm or focus? Reallocate regions or change presentation when content clusters in one area while large
unused regions coexist with cramped text. Fixed-coordinate gaps need an actual purpose; never add filler.
Supervisor reviews the final renders and Art's judgment, recording the page, region, purpose or repair.
Use existing area plans, semantic-whitespace evidence and work records, without a whitespace score or approval form.

## Native tables are required for tabular presentation

Whenever information is presented as rows, columns, headers and cells, use an integrated native table,
including qualitative comparisons. Rectangles plus text, fragmented one-cell tables and table images
cannot substitute while retaining tabular form. If native tables are unavailable, Art must change the
presentation to another appropriate medium before Output implements it. Renaming the medium, recording
an editing limitation or approving an alternative does not authorize a visually tabular substitute.
Output inspects real table objects and cell bindings; Supervisor checks both objects and final renders.
An object count alone cannot prove that the visible table is integrated.

## Internal capacity for application differences

Output uses `layout.internal_content_reserve_ratio` (default 0.10) to leave approximately 10% internal
capacity in text boxes and shapes, considering both width and height. Keep long numbers, units, final
lines and node labels away from capacity limits. After normal padding, target content occupying about
90% or less of the usable region. This is a layout target, not 10% per side or 10% of the entire slide.
Apply the same principle to table cells and chart-label regions. Expand containers, reflow or change the
presentation before reducing text; never silently shrink fonts, remove approved content or cover neighbors.
Review text overflow within containers and unintended collisions/tangencies between objects, not only slide bounds.
Account for PowerPoint (Office) and WPS font resolution, wrapping and text metrics. Reopen high-risk pages
in each available, selected target application. One renderer's pass does not establish another's pass;
record unavailable targets as deferred while still designing the reserve and checking available renders.
Record the object, usable region, measured or estimated content extent, adjustment and target results in
existing evidence. A 10% reserve is not proof of cross-application compatibility.

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

Output and Supervisor check fonts inside tables and charts: cells, headers, axis ticks, legends, data
labels, chart titles, Latin text, digits and units. Write the configured Latin and East Asian fields.
Body-text success cannot establish chart success; a font's presence in a PDF cannot establish every object's identity.
Run the current `audit_ppt_font_names.py` and review table/chart/Latin/digit coverage and findings.
Unresolved inheritance or missing fields remain deferred; explicitly wrong fonts fail. Review actual target
renders as well. Written fields, font-file identity, render output and native PowerPoint/WPS acceptance are separate evidence.

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

Tables follow the native requirement above. Prefer native chart data labels and standard slide numbering.
Independent chart labels and custom number fields are editing limitations requiring explicit deviation/audit records.
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
