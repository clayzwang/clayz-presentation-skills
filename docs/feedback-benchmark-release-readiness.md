# Feedback, benchmark, migration, and release readiness

Stage 5 closes the v0.4.0 development loop without changing the five-stage
ownership model. Release remains blocked until a separate explicit human
authorization is recorded.

## Human-admitted feedback loop

Logic, Copy, Art Direction, and Output may append evidence-backed observations.
Supervisor can route a candidate to one of those stages but owns no fifth
learning store. Every source record remains `promotion_status=observation`.

`packages/feedback/learning.py` creates an index provider only from records that
have a separate human admission whose canonical SHA-256 matches exactly. A
missing admission, content change, malformed decision, or duplicate identity is
rejected or reported. Admitted learning remains `local-private`, `local-only`,
and `public_catalog_eligible=false`.

## Retrieval benchmark

The synthetic benchmark fixes two provider snapshots and four cases:

- a registered Composition Pattern;
- a registered Failure Pattern;
- one hash-bound, human-admitted private learning record;
- one unregistered request that must stay empty and `unresolved`.

The run fails on provider drift, missing expected candidates, forbidden
candidates, non-empty unresolved results, or an invented record ID. The runtime
never updates the expected baseline automatically.

## Legacy migration

`scripts/migrate_knowledge_index.py` converts the legacy filesystem registries
into the generic index-record contract. It migrates only unchanged,
human-admitted assets and learning records. It preserves private scope, removes
or reports orphan neighbors, and records every skipped subject and reason.

The repository fixture is synthetic: three assets and two learning observations
produce one migrated knowledge record and one migrated learning record. One
stale asset and two unadmitted subjects are skipped.

## Release readiness requires separate authority

Each release uses `release/vX.Y.Z-readiness.json` for the version named by
`VERSION`. The record preserves the five development-stage gates and a separate
explicit user decision authorizing merge, immutable tag creation, GitHub
publication, and the current Experience Center marker. Starting with v0.5.0,
the record also names the Experience Center, Node.js chart-build, and
presentation-overflow checks. The release workflow still validates the full
tree before it may publish.

Validate the stage with:

```bash
python scripts/validate_feedback_benchmark.py
python scripts/validate_all.py
```

All Stage 5 fixtures contain original method metadata and synthetic text only.
They include no template, master, brand kit, logo, font, corporate data, source
media, dataset, model feature, or model weight.
