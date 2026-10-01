# PPT v3.2 Copy-layer contract

The authoritative schema and ownership are in [Research, content structure and visual handoff](../../../packages/contracts/story-visual-handoff.md). Read its Logic and Copy sections in full.

Logic hands off immutable `research` with null `logic_layer` and `copy_layer`. Copy builds the PPT-suitable text and content structure, including its own pagination, chapters, page claims, titles and closing language. Copy does not build a presentation or prescribe Art's final medium, geometry or assets. `logic_layer.owner: "copy"` identifies the compatibility page projection; it does not restore Logic pagination.

Required research findings must remain visible, traceable via `source_finding_ids`, with source and data definitions intact. `logic_artifact` binds the original approved research. Copy's `presentation_requests` can request tables, charts, logos and numbering; Art chooses the concrete presentation structure and records the disposition.

Use the existing stage validation, calibration and work records. 2.4/3.0/3.1 are isolated historical replay contracts; never apply their page ownership to a new 3.2 run.
