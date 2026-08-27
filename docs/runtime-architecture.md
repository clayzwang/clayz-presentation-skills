# Runtime architecture

v0.5.2 preserves the v0.5.1 separation of presentation reasoning from execution and adds one optional owner-private extension decision before Logic. One Public Core and one bundled public Provider remain the brain in every target. Local adapters execute the Local Light route; ChatGPT host tools form the body for Cloud Light. The five skills still own decisions. The runtime owns capability discovery, route locking, bounded tool use, and the host boundary.

## Fixed lifecycle

`natural-language request → five-stage approved artifacts → one preflight scan → locked route → one cached source collection → one build → final render QA → at most one targeted repair → delivery`

The route does not change mid-run. A hard backend failure closes the run; one configured fallback restart may begin from a fresh preflight report.

## Model interaction

A–D are capability profiles, not a brand ranking. A and B can orchestrate the runtime directly. C emits the internal structured handoff for an adapter. D uses one narrow tool invocation when possible, otherwise the C route. Users never need to write the JSON handoff.

Hosts should bind presentation-generation intent to the five Clayz skills, beginning with Logic for a new deck and following the approved stage handoffs. Merely exposing local PowerPoint automation without the skills is not a conforming integration.

Cloud hosts inspect their actually available presentation capabilities and pass a task-local `host_capabilities` declaration into preflight. Only then may the runtime lock `native-presentation-tool` as its authoring/render route. The declaration is evidence about the current host, not a bundled tool or a permanent promise.

## Dependency levels

1. Common authoring: Python 3.10+, `python-pptx`, Pillow, and PyYAML. This route does not require a host model's private presentation tool.
2. Final rendering in the v0.5.2 local release: one PowerPoint COM process on Windows. Cloud Public Light may select a host-provided presentation or Artifact Tool route during preflight. Other local operating-system routes are not v0.5.2 release claims.
3. Lazy media support: Poppler only for PDF page input or the LibreOffice PDF-to-PNG rendering route; an SVG converter only when the selected deck actually contains SVG on a backend that cannot insert it natively.

The repository bundles contracts, adapters, validators, preflight logic, and per-platform launcher scripts. Third-party applications and binaries remain external unless their licenses and platform packaging are separately reviewed.

## Public Light targets and local platform packages

Run `python scripts/build_runtime_packs.py --bundle light` to create deterministic Cloud Public Light and Local Public Light ZIPs under `dist/`. Both bind the same `public_core_sha256` and bundled public Provider snapshot. Cloud Light omits local adapters and platform packs because ChatGPT supplies tools; Local Light retains local execution routes. After `scripts/fetch_offline_wheels.py --platform windows` stages reviewed CPython 3.12 wheels, the v0.5.2 release build creates only the Windows offline dependency add-on. No Light archive contains third-party wheels, and no macOS, Linux, or iOS release package is produced. See [`release-packages.md`](release-packages.md).
