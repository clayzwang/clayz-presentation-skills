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

## Runtime routing

`runtime` defines process budgets and invariants, not discovered machine paths. Run `scripts/runtime_preflight.py` once per production run to materialize those paths and select one locked route. Keep that report task-local; do not copy local executable paths into central configuration.

The baseline authoring route is `renderer.baseline_adapter`. PDF support remains lazy, so Poppler is not a core authoring dependency. See [`runtime-architecture.md`](runtime-architecture.md).

## Locale and reference routing

`locale.default` selects the documentation route when the task does not specify a locale. English references use the base filename (`name.md`); Simplified Chinese references use the matching `name.zh-CN.md`. Skills load exactly one route by default so bilingual documentation does not double context cost. The locale controls instructions, formatting defaults, and language-aware QA; it does not translate approved content automatically.

## Portable knowledge paths

The public default points to the intentionally empty `knowledge/` scaffold. It contains four learning areas—Logic, Copy, Art Direction, and Output—plus shared sources and registries. Supervisor has no independent learning store.

Keep `require_human_admission=true` and `learning.auto_promote=false`. Learning records are observations until a human admission is written to the configured admission registry. A different host may replace the filesystem provider, but ChatGPT Library is optional and is not created or connected by downloading this repository.
