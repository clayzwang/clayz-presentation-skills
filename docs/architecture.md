# Architecture

## Stage ownership

| Stage | Owns | Must not silently change |
| --- | --- | --- |
| Logic | audience, decision outcome, question chain, claims, evidence, slide sequence | source facts or user constraints |
| Copy | titles, storylines, visible copy, numbers, punctuation, intentional breaks, notes | logic, evidence status, slide order |
| Art Direction | first visual, visual anchor, medium, area plan, semantic layout tree, rhythm | approved copy or logic |
| Output | editable objects, coordinates, theme application, technical repair, final files | approved content or visual intent |
| Supervisor | cross-layer diagnosis, evidence, severity, ownership, challenge record | any upstream or downstream artifact |

## Layout compilation layers

Theme and Visual Variant remain configuration and Art Direction concerns.
Registered Layout Contracts provide reusable semantic topology, while the
task-local Layout Tree binds approved Semantic Layout Tree nodes and copy IDs.
Only Output resolves coordinates and creates objects. See
[`layout-contracts.md`](layout-contracts.md).

## Composition and dataset metadata layers

Registered Composition Patterns describe how approved semantic relations may
become spatial relationships, while Layout Contracts describe reusable semantic
topology. Art Direction owns both decisions but keeps them independent. A
Composition Plan is coordinate-free and receipt-bound; Output consumes it with
the independently approved Layout Contract or core Layout Tree. Supervisor may
use receipt-selected Failure Patterns only to diagnose rendered evidence and
route repair to the earliest responsible stage.

Reference and Sequence records are dataset-ready metadata, not bundled cases.
Their exporter excludes source text, media, coordinates, fonts, model features,
generated-artifact auto-admission, and automatic aesthetic truth. See
[`pattern-dataset-library.md`](pattern-dataset-library.md).

## Central configuration

All environmental and stylistic choices resolve from `config/default.json` or one explicit override. Skills may read the configuration but may not copy its values into their own instructions as fixed rules.

Resolution order:

1. Explicit task override.
2. User-supplied configuration path.
3. Plugin-root `config/default.json`.

The final resolved configuration hash belongs in every stage artifact as `configuration_sha256`.

## Distribution model

The source repository stores shared contracts and validators once. The Codex and marketplace plugin bundles five Skills around that shared root. The ChatGPT Skills host adapter compiles the same five stage sources into one publication unit with one root `SKILL.md` and five responsibility-separated internal modules, because detached uploads cannot share the root safely. This is a packaging transform, not another Public Core and not a sixth decision-making stage. v0.5.1 adds a deterministic runtime beneath Output rather than a sixth decision-making skill. It provides a public baseline adapter, one-shot preflight, route locking, bounded calls, and common plus operating-system packs. See [`runtime-architecture.md`](runtime-architecture.md).

## Portable knowledge model

The public distribution includes four stage learning areas—Logic, Copy, Art Direction, and Output—plus one shared source-and-index area. Supervisor reads across the full production chain and routes reusable observations to the earliest responsible stage; it does not own a fifth learning silo.

The default filesystem scaffold is empty and portable. It does not create or connect ChatGPT Library. Host adapters may map the same contract to another storage system, while human admission and no-auto-promotion remain invariant.

An observation becomes retrievable only after a separate human admission binds
its canonical hash. The rebuilt learning provider remains private and distinct
from the public built-in catalog. Retrieval benchmarks pin provider snapshots,
while migration converts only unchanged admitted legacy records. These feedback
and release-readiness services support the five stages; they do not add a sixth
stage or transfer approval authority. See
[`feedback-benchmark-release-readiness.md`](feedback-benchmark-release-readiness.md).
