# Configuration guide

`config/default.json` is the single source for all values that vary by user, organization, runtime, locale, or delivery channel.

The only deliberate duplication is plugin UI metadata (`agents/openai.yaml` and its local icon), because each installable skill must carry its own interface descriptor. Those values identify the Clayz plugin itself; they do not style generated decks.

## Keep in configuration

- identity and attribution metadata;
- theme colors and optional master path;
- font stack and legibility thresholds;
- slide size, layout roles, margins, and gaps;
- reference provider and registries;
- renderer capabilities and target applications;
- runtime model profiles, one-shot preflight policy, fixed-route budgets, and platform-pack selection;
- delivery profile and media limits;
- deterministic QA toggles.

## Keep out of configuration

- facts and conclusions for one presentation;
- page-specific copy;
- page-specific composition decisions;
- evaluation results;
- private credentials or access tokens.

Never commit a local override that contains confidential paths, private template names, or internal brand values.

For reusable private settings, use a Personal Extension Profile outside the repository instead of editing this file. The composer applies only allowlisted `replace`, `append_unique`, or `stricter_only` operations, writes an origin map, and generates a host-specific resolved config. See [`personal-extension.md`](personal-extension.md). Native local or ChatGPT Library paths belong only in private host bindings; stage instructions and index records use logical `library://` URIs.

## Runtime routing

`runtime` defines process budgets and invariants, not discovered machine paths. Run `scripts/runtime_preflight.py` once per production run to materialize those paths and select one locked route. Keep that report task-local; do not copy local executable paths into central configuration.

The baseline authoring route is `renderer.baseline_adapter`. PDF support remains lazy, so Poppler is not a core authoring dependency. See [`runtime-architecture.md`](runtime-architecture.md).

## Locale and reference routing

`locale.default` selects the documentation route when the task does not specify a locale. English references use the base filename (`name.md`); Simplified Chinese references use the matching `name.zh-CN.md`. Skills load exactly one route by default so bilingual documentation does not double context cost. The locale controls instructions, formatting defaults, and language-aware QA; it does not translate approved content automatically.

## Public Provider and portable Library paths

`references.public_provider_manifest` and `references.public_index` identify the immutable bundled public Provider; their values remain `catalog/provider-manifest.json` and `catalog/records.jsonl` in every host target. The intentionally empty `knowledge/` scaffold is a separate owner-local Library authoring area. It contains four learning areas—Logic, Copy, Art Direction, and Output—plus shared sources and registries. Supervisor has no independent learning store. Its generated `references.index.path` has role `derived-local-search-cache` and is never a canonical Provider index.

Keep `require_human_admission=true` and `learning.auto_promote=false`. Learning records are observations until a human admission is written to the configured admission registry. A host binding may connect an owner-private Provider to ChatGPT Library, but downloading the repository does not create or connect that Library.
