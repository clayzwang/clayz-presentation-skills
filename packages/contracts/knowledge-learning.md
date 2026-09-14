# Knowledge and learning contract

For interactive material learning, follow [the plugin system contract](plugin-system.md).
The assistant discusses a candidate with the owner before recording an exact
hash-bound confirmation. `scripts/plugin_cli.py` saves the confirmed content,
original attachments and provider index as one immutable Library snapshot.
These records use the existing IndexRecord/CompositeIndex runtime. This is an
additional producer for the same reference system, not a competing search cache.
The old observation/admission commands remain available for legacy records.

The portable knowledge scaffold is an optional persistence layer, not a second source of truth for the current presentation.

1. Resolve the reference provider, source roots, registries, learning root, and admission policy from the central configuration.
2. Retrieve by task purpose, evidence need, page role, medium, object type, or language. Open only a small relevant set plus useful physical or semantic neighbors.
3. Use a source or prior learning as approved reference material only when its registry entry is current, its rights boundary is clear, and a matching human admission exists when required.
4. Write observations only to the responsible stage. Supervisor returns reusable observations to Logic, Copy, Art Direction, or Output and never owns a separate learning store.
5. Record evidence, applicability, uncertainty, user rulings, and rejected alternatives. Do not convert a score, similarity, frequency, generated artifact, or model opinion into quality truth.
6. Keep new records at `promotion_status=observation` unless a human explicitly admits them. Never auto-promote.
7. If the configured store is unavailable, emit a task-local learning candidate and report that persistence did not occur; never pretend a write succeeded.

Retrieval exists to improve judgment, not to create ceremonial evidence volume. Start each stage with one focused, substantive request. Issue a second or third receipt only when a material question remains unresolved, and treat the acceptance candidate/selection budget as cumulative for the whole stage rather than a fresh allowance per query. Rank compact metadata first, materialize only selected records or relevant excerpts, and keep rejected records as IDs, scores, and reasons rather than loading their full bodies. Reuse locked sources and stage artifacts by path plus hash instead of retrieving or restating them again.

These efficiency rules remove redundant transport and execution. They do not cap the depth of Logic deliberation. Owner-private knowledge supplies evidence, counterexamples, terminology, and methods; Logic must still connect them into a complete current-state, target-state, mechanism, and decision argument.

An observation can enter retrieval only through a second, hash-bound admission
record. The admission identifies the exact `record_id`, canonical SHA-256,
approved uses, `never_copy` boundaries, and promotion target. Editing the
observation after admission invalidates that admission. Admitted learning is a
private-runtime provider record by default; human admission does not imply
public-catalog publication.

Retrieval benchmarks pin every provider snapshot and use explicit expected and
forbidden candidate IDs. Snapshot drift, a missing expected candidate, a
forbidden candidate, or any invented ID fails the benchmark. Baselines may be
changed only by a reviewed source edit; runtime results never rewrite them.

The public filesystem implementation is `scripts/knowledge_cli.py`. It resolves all source, registry, learning, index, result-limit, and neighbor-expansion paths from the central configuration. Human admission requires the explicit `--confirm-human-decision` flag; registering an asset or recording an observation never admits it. Its v2 index includes unchanged admitted assets and unchanged, separately admitted learning observations while preserving their record type and responsible stage.
