# Personal Extension Profile

Version 0.5.2 adds one optional owner-private extension point before the existing five-stage workflow. It does not add a sixth skill, fork a stage, or create a second retrieval engine. Public material, its Library payloads, and its index are still organized and usable in this version. What is deferred is the method for continuous learning, community aggregation, automatic update, and cross-source fusion of public material.

```text
GitHub public source
  -> one Public Core + public Library + public Provider manifest/index
  -> Cloud Public Light / Local Public Light

Cloud Public Light (brain)
  + private Personal Extension Profile
  + private Library Provider (memory)
  + ChatGPT host tools (body)
  -> one resolved Personal Extension Runtime
  -> Logic -> Copy -> Art Direction -> Output -> Supervisor
```

## Three contracts

The public repository defines three generic contracts:

1. `personal-extension-profile.schema.json` validates a private, human-authored profile.
2. `provider-manifest.schema.json` describes bundled public and owner-private Providers through one contract.
3. `personal-extension-runtime.schema.json` validates the generated host-specific runtime envelope.

The existing `index-record`, retrieval-request, retrieval-receipt, `IndexProvider`, and `CompositeIndex` contracts remain the only retrieval path. `resource-inventory.schema.json` adds the pre-Logic scan and user brief, while `index-execution-evidence.schema.json` proves task-local owner materialization and stage receipt coverage. The owner-learning manifest is generated as a runtime input from that scan; it is not a repository file. `catalog/provider-manifest.json` and `catalog/records.jsonl` are the canonical public Provider control plane and sole public index source of truth. `knowledge/index/search-cache.json` is only a derived cache for the local Library tool. Private records keep their own `provider_id`, hashes, rights, human-admission state, and `never_copy` boundaries. The public repository contains no real private profile, manifest, index, attachment, master, font, brand value, or native path.

## Override policies

The resolver owns the policy for every supported path. A private profile cannot declare a weaker policy or override a sealed path.

- `replace` is limited to explicit presentation choices such as locale, theme identity, logical master URI, colors, the ordered font stack, selected layout values, and delivery profile.
- `append_unique` extends capability, application, backend, or layout-role lists without deleting the public baseline.
- `stricter_only` may raise text thresholds or turn a validation guard on; it cannot lower a threshold or turn an existing guard off.
- All workflow, namespace, version, public attribution, route-budget, learning-admission, and core-contract fields remain sealed.

Every resolved override receives an origin-map entry. The generated runtime binds the resolved-config hash and its own deterministic lock digest.

## Logical Library mounts

Skills and private index records use only `library://<namespace>/...` URIs. Native paths exist only in a host binding selected by the composer:

```json
{
  "mount_id": "private-library",
  "logical_root": "library://example-presentation/",
  "bindings": {
    "local": {"adapter": "filesystem", "root": "${CLAYZ_PRESENTATION_LIBRARY_ROOT}"},
    "chatgpt-personal": {"adapter": "host-library", "root": "PPT"}
  }
}
```

The same logical URI can resolve to a local file or a ChatGPT Library item without changing stage instructions or records. The public Provider uses the immutable `bundle://public-library/` mount in both light targets. A host binding may not traverse above its root. The cloud composer selects the `chatgpt-personal` binding and never copies a private Provider index or attachment into the plugin ZIP.

## Private index lifecycle

Create or update admitted private IndexRecords outside this repository, then build their manifest with the shared contract:

```bash
python scripts/build_provider_manifest.py \
  --provider-id example.private-library \
  --visibility owner-private \
  --records <private-path>/records.jsonl \
  --index-uri library://example-presentation/_extension/providers/private/index/records.jsonl \
  --output <private-path>/provider.manifest.json
```

Store `records.jsonl` and `provider.manifest.json` at stable logical locations declared by the profile. Each task reads a private manifest once and locks its current snapshot into retrieval evidence shared by all five stages. Adding an admitted reference therefore updates the private index and manifest but does not change the public plugin. Recompose the cloud personal runtime only when the core version, profile rules, host mount, or Provider list changes.

## Failure and evolution boundaries

- With no generated runtime, all skills use `config/default.json` and the bundled public Provider.
- An unavailable optional private Provider records an explicit public-core fallback.
- An unavailable required Provider, master, font, or brand asset fails closed for tasks that require it.
- A private record never bypasses rights, hash, admission, receipt, or materialization checks.
- Provider discovery and snapshot locking happen once before Logic; later stages reuse that task lock.
- The public Provider manifest explicitly marks `continuous_learning`, `community_aggregation`, `automatic_update`, and `cross_source_fusion` methods as `deferred`. Existing public material is not deferred or disabled.

Task Overlay, remote MCP Providers, and automatic private Library ingestion are also intentionally deferred.
