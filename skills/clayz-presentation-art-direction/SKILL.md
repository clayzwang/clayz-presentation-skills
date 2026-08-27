---
name: clayz-presentation-art-direction
description: Convert a copy-approved presentation package into an art-direction-approved visual plan covering first visual, hierarchy, medium, area allocation, content-aware image composition, governed template and icon selection, semantic layout tree, cross-slide rhythm, and reference evidence. Use between final copy and PPTX production, or to diagnose composition, density, cardification, weak hierarchy, repetitive layouts, image-text conflict, template imitation, decorative icons, or unreadable charts. Do not rewrite approved content or build the final PPTX.
---

# Clayz Presentation Art Direction

Create an `art-direction-approved` plan that makes visual judgment explicit without becoming a second copy source or a coordinate engine.

## Boundaries

Own reference selection, first visual, visual anchor, dominant medium, hierarchy, area plan, content-aware canvas analysis, asset strategy, semantic layout tree, silhouette, density, reading path, whitespace, motif, series behavior, and cross-slide rhythm.

Do not modify approved facts, wording, numbers, punctuation, breaks, notes, page order, management stage, or cross-slide invariants. Do not create final PPTX objects.

## Required context

1. Resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its lock and resolved config hash with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. Do not create a private Art Direction fork.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Validate the copy-approved package.
4. Read `references/art-direction-plan-contract.md` and `references/material-routes.md`. These core contracts are mandatory and never search-dependent.
5. Read `references/layout-contract-routing.md` and `references/pattern-library-routing.md`. These routing boundaries are mandatory and never search-dependent; the existence of a matching registered Layout Contract, Composition Pattern, Failure Pattern, Reference, or Sequence is search-dependent.
6. Read `../../packages/contracts/knowledge-learning.md` before retrieval or learning writeback. This governance contract is mandatory and never search-dependent.
7. Reuse the one task Provider lock created before Logic; it always contains the bundled public Provider and may contain owner-private Providers whose declared stages include Art Direction. Private references remain governed index candidates; they do not bypass human admission, rights, hash, receipt, or `never_copy` checks.
8. Classify optional visual signals, then resolve them through the built-in Capability Index. Supported examples include `image-led`, `image-copy-conflict`, `asset-selection`, `template-candidate`, `icon-selection`, `high-risk-composition`, `ab-review`, `large-reference-set`, `reference-discovery`, `architecture-house`, and `enterprise-architecture`.
9. Load only optional `knowledge_refs` returned by selected capability records. Architecture-house routing may return the source index and pattern library together with its method reference; this is a governed capability bundle, not a template lookup.
10. Preserve every capability, Layout Contract, and Composition Pattern resolution plus retrieval receipt ID as task-local evidence. If a signal, contract, pattern, or linked failure record has no eligible record, mark it unresolved and use core contracts or return the gap; never invent a layout method, reference, template, contract, pattern, failure diagnosis, or brand asset.

## Workflow

1. Group slides by communication purpose, relationship, load, decision weight, series role, and silhouette risk.
2. Resolve optional capabilities before loading optional references. Use the configured reference provider for actual reference retrieval; admit only traceable, human-approved sources with clear rights boundaries.
3. For every slide, state the intended first impression, first visual, area allocation, dominant medium, density, reading path, semantic whitespace, and risks.
4. When an image-like canvas is present, use the resolved content-aware capability to inspect subject protection, placement suitability, crop and contrast risk, and directional flow before placing copy. Blank pixels are not automatically safe space.
5. Treat templates and icons as reviewed candidates. Use the resolved asset-grammar capability, re-derive composition from the current page job, select assets by semantic role, and record source and license evidence; never clone a master, layout, brand identity, or arbitrary ratio.
6. For a reference-architecture house, use the resolved architecture-house capability and apply the corpus-to-pattern-to-synthesis method. Record selected source IDs, relationship grammars, task adaptations, and accountability path.
7. Build a semantic layout tree that records containment, peers, sequence, cause, condition, support, comparison, feedback, or anchors.
8. Resolve an optional registered Composition Pattern from the approved page semantics, constraints, and expected visual effect. Compile it only when the selected pattern and every linked Failure Pattern are receipt-bound; record selected and rejected candidates. With no unique eligible pattern, record `unresolved` and continue through the core Art Direction method without claiming a named pattern.
9. Resolve an optional registered Layout Contract from the approved page semantics, then bind its slots to Semantic Layout Tree node IDs and `copy_id` values. Keep Theme, Visual Variant, Composition Pattern, Layout Contract, Layout Tree, and resolved coordinates as separate layers. With no eligible contract, record `unresolved` and continue through the core tree path without claiming a named contract.
10. Map every `copy_id` exactly once to a render target and verification method.
11. Use real rendered A/B prototypes for high-risk composition only when the A/B capability was resolved; do not treat automated scores or similarity as the winner.
12. Judge the deck as a sequence, not a collection of isolated pages. Reference and Sequence records are metadata-only evidence and never authorize copying source content or media.
13. Emit task-local learning candidates with rendered evidence, applicability, and `never_copy` boundaries; persist them only through the configured Art Direction learning route and never auto-promote them.
14. Emit one plan with `origin_namespace: io.clayz.presentation` and status `art-direction-approved`; task-local execution evidence should retain the capability, Layout Contract, Composition Pattern, linked Failure Pattern, and retrieval receipt IDs used.

## Validation

Run:

```bash
python ../../packages/validators/validate_art_direction_plan.py <copy-package.json> <art-direction-plan.json> --config ../../config/default.json
```

Hand the validated plan to `$clayz-presentation-output`.
