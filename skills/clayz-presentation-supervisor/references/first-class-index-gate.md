# First-class Index gate

The Index is an execution dependency, not background reading. In owner-personal mode, a stage may not be approved from prose claims such as “the library was reviewed” or “the plan and render are consistent.”

## First-run version learning and task reuse

Before Logic, perform this work as part of the pre-Logic resource scan and record every source in `ppt-resource-inventory.json`:

1. Validate `runtime/personal-extension.json` and read its `index_execution` policy.
2. Build an `io.clayz.presentation.owner-learning-sources/1.0` manifest from the owner resources discovered during the scan. Every source declares `knowledge_kinds`; the complete manifest covers at least `private-knowledge`, `template`, `standard`, and `method`. The manifest remains a runtime input outside the public plugin.
3. Resolve each required source through the locked owner Library mount and read its real bytes. Resolve a persistent owner-private version-learning state root; an ephemeral task directory is not persistent state.
4. Run `scripts/bootstrap_owner_learning.py`. On the first run of the current Public Core version, it hashes every source, builds `task-private-learning`, exercises real CompositeIndex retrieval probes for the four required knowledge kinds, and writes a separate JSON and Markdown learning audit. The audit lists sources, record counts, kinds, stages, digests, representative titles, provider snapshot, probes, and gaps.
5. On later tasks for the same version, verify and reuse the exact index and audit without learning again. Changed source bytes under the same version are `PRIVATE_LEARNING_SOURCE_DRIFT`; do not overwrite the first-run audit silently.
6. Combine `builtin-catalog`, the locked owner-private Providers, and the version-bound `task-private-learning` into one `CompositeIndex`. Sort and hash the Provider snapshots once; never replace them mid-run.
7. Create `index_evidence` under `io.clayz.presentation.index-execution-evidence/1.0`. `owner_materialization.learning_mode` is `first-run` or `reused-version-index` and binds both `learning_key` and `version_learning_audit_sha256`. Add the source pools to the selected resource inventory, present the learning/resource brief to the user, and carry both locks through every handoff.

If a required Library source cannot be read, decompressed, parsed, hashed, learned on first run, persisted, or verified for reuse, stop before the affected stage. Do not replace it with memory, generic defaults, the inventory locator, per-task rematerialization, or an unreceipted web search.

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
