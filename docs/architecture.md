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

## Central configuration

All environmental and stylistic choices resolve from `config/default.json` or one explicit override. Skills may read the configuration but may not copy its values into their own instructions as fixed rules.

Resolution order:

1. Explicit task override.
2. User-supplied configuration path.
3. Plugin-root `config/default.json`.

The final resolved configuration hash belongs in every stage artifact as `configuration_sha256`.

## Distribution model

The source repository stores shared contracts and validators once. The plugin bundles five skills around that shared root. A future standalone release builder may vendor the required shared files into a single-skill package without changing source ownership.

## Portable knowledge model

The public distribution includes four stage learning areas—Logic, Copy, Art Direction, and Output—plus one shared source-and-index area. Supervisor reads across the full production chain and routes reusable observations to the earliest responsible stage; it does not own a fifth learning silo.

The default filesystem scaffold is empty and portable. It does not create or connect ChatGPT Library. Host adapters may map the same contract to another storage system, while human admission and no-auto-promotion remain invariant.
