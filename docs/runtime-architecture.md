# Runtime architecture

v0.5.1 separates model reasoning from deterministic presentation execution. The five skills still own decisions. The runtime owns capability discovery, route locking, bounded tool use, authoring adapters, and platform rendering.

## Fixed lifecycle

`natural-language request → five-stage approved artifacts → one preflight scan → locked route → one cached source collection → one build → final render QA → at most one targeted repair → delivery`

The route does not change mid-run. A hard backend failure closes the run; one configured fallback restart may begin from a fresh preflight report.

## Model interaction

A–D are capability profiles, not a brand ranking. A and B can orchestrate the runtime directly. C emits the internal structured handoff for an adapter. D uses one narrow tool invocation when possible, otherwise the C route. Users never need to write the JSON handoff.

Hosts should bind presentation-generation intent to the five Clayz skills, beginning with Logic for a new deck and following the approved stage handoffs. Merely exposing local PowerPoint automation without the skills is not a conforming integration.

## Dependency levels

1. Common authoring: Python 3.10+, `python-pptx`, Pillow, and PyYAML. This route does not require a host model's private presentation tool.
2. Final rendering: one PowerPoint COM process on Windows, or one LibreOffice process on macOS/Linux. Host-provided Artifact Tool is an optional route selected only during preflight.
3. Lazy media support: Poppler only for PDF page input or the LibreOffice PDF-to-PNG rendering route; an SVG converter only when the selected deck actually contains SVG on a backend that cannot insert it natively.

The repository bundles contracts, adapters, validators, preflight logic, and per-platform launcher scripts. Third-party applications and binaries remain external unless their licenses and platform packaging are separately reviewed.

## Local platform packages

Run `python scripts/build_runtime_packs.py` to create deterministic Windows, macOS, and Linux plugin ZIPs under `dist/`. Each package contains common source plus exactly one operating-system pack and a runtime lock manifest. It deliberately contains no unreviewed third-party binary bundle.
