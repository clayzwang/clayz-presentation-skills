# Index-native retrieval foundation

v0.4.0 development begins by making retrieval a governed runtime rather than an optional file lookup. This stage does not change the five-stage ownership model and does not publish a new release.

## What the index owns

The index runtime owns stable record identifiers, provider snapshots, hard filters, lexical ranking, neighbor expansion, rights decisions, and retrieval receipts. It does not own business judgment, visual judgment, copy approval, or rendering.

Every candidate keeps its `provider_id`, source revision, license, `never_copy` rules, materialization status, and match basis. A stage may select or reject retrieved candidates, but it cannot select an identifier that was not present in the receipt.

## Provider model

The first contract supports multiple independent providers:

- `builtin-catalog`: project-maintained contracts and original methods safe for open-source distribution;
- `filesystem-library`: user-owned local or NAS knowledge;
- `host-library`: a host application's Library or enterprise knowledge service;
- `external-ephemeral`: task-local search metadata that is not automatically persisted.

Provider identities are never collapsed. Identical titles from different providers remain distinct records with distinct rights and revisions.

## Hallucination boundary

The runtime never fabricates a fallback record. If no registered and eligible record matches, the receipt contains:

```json
{
  "fallback": {
    "used": false,
    "reason": "no-eligible-registered-record"
  },
  "hallucination_guard": {
    "only_registered_records": true,
    "invented_record_count": 0
  }
}
```

A later stage may proceed without a reference, ask for an upstream decision, or perform a clearly marked external search. It may not pretend that a missing layout, source, or template exists.

## Public brand-asset guard

Private libraries may contain owner-authorized brand assets for local use. Retrieval success never turns them into public assets.

The public built-in catalog is metadata-and-method only. Machine validation rejects presentation templates, masters, themes, and font binaries under `catalog/`. A brand-specific template, master, font, or brand kit cannot be marked public-catalog eligible unless both redistribution and materialization are explicitly allowed and the record has been human admitted.

The rule is company-neutral: it protects every corporate template and prevents a private enterprise visual identity from leaking into the open-source model or examples.

## Contracts

- `packages/contracts/index-record.schema.json`
- `packages/contracts/retrieval-request.schema.json`
- `packages/contracts/retrieval-receipt.schema.json`

The runtime implementation is in `packages/index_runtime/`. Use `scripts/index_runtime_cli.py` to validate providers, search, and finalize a receipt.

## Development status

v0.4.0 capability routing, registered Layout Contracts, Composition Patterns,
linked Failure Patterns, and hash-bound private learning use the same receipts.
Stage 5 adds fixed provider-snapshot benchmarks, fail-closed legacy migration,
and a release record that requires all evidence gates plus a separate explicit
human decision before merge, immutable Tag, publication, or Experience Center
update. See
[`feedback-benchmark-release-readiness.md`](feedback-benchmark-release-readiness.md).
