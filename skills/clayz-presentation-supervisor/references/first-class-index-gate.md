# First-class Index gate

The Index is an execution dependency, not background reading. In owner-personal mode, a stage may not be approved from prose claims such as “the library was reviewed” or “the plan and render are consistent.”

## Root materialization inside the resource inventory

Before Logic, perform this work as part of the pre-Logic resource scan and record every source in `ppt-resource-inventory.json`:

1. Validate `runtime/personal-extension.json` and read its `index_execution` policy.
2. Build a task-local `io.clayz.presentation.owner-learning-sources/1.0` manifest from the owner resources discovered during the scan. The manifest is a runtime input; it is never bundled into the public plugin.
3. Through the selected owner Library mounts, read every source marked `required` for the stages in this run. Reading only locator metadata is insufficient.
4. Preserve the exact bytes task-locally and run `scripts/materialize_owner_index.py --manifest <task-manifest>` with one `source_id=path` binding per source. The materializer hashes the bytes and creates the ephemeral `task-private-learning` Index provider.
5. Combine `builtin-catalog`, the locked owner-private Providers, and `task-private-learning` into one `CompositeIndex`. Sort and hash the Provider snapshots once; never replace them mid-run.
6. Create `index_evidence` under `io.clayz.presentation.index-execution-evidence/1.0`, add the materialized Provider and source pools to the selected resource inventory, present the resource brief to the user, and carry both locks through every handoff.

If a required Library source cannot be read, decompressed, parsed, hashed, or materialized, stop before the affected stage with `first-class-index-unavailable`. Do not replace it with memory, generic defaults, the inventory locator, or an unreceipted web search.

## Per-stage gate

Before approving each stage:

1. Issue stage-specific Retrieval Requests against the locked CompositeIndex.
2. Finalize every Retrieval Receipt with selected and rejected registered records plus concrete reasons.
3. In owner-personal mode, select every `task-private-learning` source declared for that stage by the task manifest. Stage requirements come from the locked evidence, never from hard-coded source names or counts.
4. Append the full finalized receipts to `index_evidence.stage_receipts.<stage>`.
5. Run the current stage validator. Missing selections, missing source coverage, fallback use, invented records, changed snapshots, or receipt-free assertions fail closed.

The Index may influence decisions only through selected receipt-bound records. Record IDs, source IDs, hashes, Provider snapshots, `never_copy` boundaries, and adoption outcomes remain visible evidence.

## Substance gate

Receipt presence does not excuse weak work. Copy must still pass its cross-slide syntax and phrase-variation checks. Art Direction must still pass content-specific first-visual, silhouette-run, structure-reuse, dominant-medium diversity, quantitative-encoding, and reference-adoption checks. Output must prove the planned native object types exist in the final PPTX. Supervisor must rerun upstream validation against the final PPTX and reject duplicated or slide-agnostic check evidence.
