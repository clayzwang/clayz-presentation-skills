# Personal Extension Profile

The v0.5.2 foundation added one optional owner-private extension point before the existing five-stage workflow. It does not add a sixth skill, fork a stage, or create a second retrieval engine. Public material, its Library payloads, and its index remain organized and usable. What is deferred is the method for continuous learning, community aggregation, automatic update, and cross-source fusion of public material.

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
- `theme.typography.font_validation` models a canonical family and its equivalent aliases as one identity. Aliases resolve installed names; they never become extra fallback positions in `primary_fonts`. The identity's `pptx_family` is the only name written to Latin and East Asian PPTX font fields.
- `append_unique` extends capability, application, backend, or layout-role lists without deleting the public baseline.
- `stricter_only` may raise text thresholds or turn a validation guard on; it cannot lower a threshold or turn an existing guard off.
- All workflow, namespace, version, public attribution, route-budget, learning-admission, and core-contract fields remain sealed.

Every resolved override receives an origin-map entry. The generated runtime binds the resolved-config hash and its own deterministic lock digest. The composed Personal package also writes an external runtime-pack lock that binds both digests plus the exact sorted binding set for every Provider marked `required: true`. Validation must use all three objects; recomputing an internally self-consistent but reduced runtime/config pair cannot erase a required Provider.

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

Every presentation task first runs the component-version gate, compares the official latest release with the mounted Public Core, config, runtime, and stage contracts, and shows the version table to the user. Personal Runtime also declares a `version_learning` policy. The host supplies an owner-private state root that persists outside task sandboxes.

On the first run of a Public Core version, every owner-learning source declares `knowledge_kinds` and the complete set covers private knowledge, templates, standards, and methods. After the host materializes admitted bytes, `scripts/bootstrap_owner_learning.py` hashes the source set, invokes the existing Index materializer, runs four retrieval probes, and writes separate JSON and Markdown learning audits. Later tasks verify and reuse the same audit and index. Source drift under the same core version stops the run; it never triggers silent re-learning.

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
- `renderer.required_capabilities` adds only real authoring-route requirements. Per-application PowerPoint/WPS native reopen acceptance is governed by `target_applications` plus preflight observations and must not be promoted into a pre-Logic hard gate.
- In owner-personal mode, preflight must read the generated resolved config, issue a fresh challenge from the canonical task-request bytes, write the canonical task-root issuance ledger, resubmit the same bytes for the one scan, exclusively consume the challenge through the canonical task-root consumption ledger, bind both ledger byte hashes and the raw config SHA-256, and treat task-level requirements as additive only. Caller-chosen run/task values, missing or synthetic in-memory receipt claims, a copied/replayed/cross-root challenge, falling back to public `config/default.json`, or shrinking Personal Extension requirements are integration failures.
- The runtime pack lock and task Index evidence must preserve a non-empty snapshot for every required private Provider; every required Provider must be actually selected by a finalized receipt in each applicable governed stage, all under the same Provider snapshot lock. Merely listing the Provider in a shared snapshot is insufficient.
- Final delivery is materialized only by `scripts/publish_supervised_pair.py`, which revalidates the report against that same resolved config and preflight before creating the PPTX/report pair and manifest.
- A private record never bypasses rights, hash, admission, receipt, or materialization checks.
- Provider discovery and snapshot locking happen once before Logic; later stages reuse that task lock.
- The public Provider manifest explicitly marks `continuous_learning`, `community_aggregation`, `automatic_update`, and `cross_source_fusion` methods as `deferred`. Existing public material is not deferred or disabled.

Task Overlay, remote MCP Providers, and automatic private Library ingestion are also intentionally deferred.
