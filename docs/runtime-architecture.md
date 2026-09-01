# Runtime architecture

v0.8.0 preserves the v0.5.2 separation of presentation reasoning, governed retrieval, and execution while making pre-Logic resource inventory mandatory. One Public Core and one bundled public Provider remain the brain in every target. Local adapters execute the Local Light route; ChatGPT host tools form the body for Cloud Light. The five skills still own decisions. The runtime owns resource and capability discovery, route locking, bounded tool use, and the host boundary.

## Fixed lifecycle

`natural-language request → official latest-version/component gate → first private learning for this version or hash-verified reuse → Supervisor issues a fresh task-bound challenge and binds config → one preflight and resource brief → locked route/sources → Logic → Copy → Art Direction → Output build → Supervisor final-render audit → at most one targeted repair → validated paired publisher bundle`

The route does not change mid-run. A hard backend failure closes the run; one configured fallback restart may begin from a fresh preflight report.

Every task checks the official GitHub Latest Release and prints the mounted core-component table before other presentation work. Runtime preflight re-binds a report generated within the last 15 minutes. Unavailable freshness evidence, a stale core, a missing component, or within-package version drift fails before Logic.

In owner-personal mode, `scripts/bootstrap_owner_learning.py` keys a persistent private index by Public Core version and the real private source-set hash. The first run reads admitted knowledge, templates, standards, and methods, builds the index, exercises retrieval probes, and writes a separate JSON/Markdown learning audit. Later tasks verify and reuse it. Source drift under the same core version fails closed instead of silently replacing the first-run evidence. “Learning” here means persistent, retrievable, audited private indexing—not model-weight modification.

## Model interaction

A–D are capability profiles, not a brand ranking. A and B can orchestrate the runtime directly. C emits the internal structured handoff for an adapter. D uses one narrow tool invocation when possible, otherwise the C route. Users never need to write the JSON handoff.

Codex and marketplace-plugin hosts bind presentation-generation intent to the five Clayz Skills, beginning at Supervisor and routing a new deck into Logic before the approved stage handoffs. The ChatGPT Skills host uses one composite root Skill that performs the same Supervisor-first control and reads only the needed internal stage module at each transition. Merely exposing presentation automation without these governed stages is not a conforming integration.

Cloud hosts inspect their actually available presentation capabilities and pass a task-local `host_capabilities` declaration into preflight. An available declaration is accepted only when it carries the same run/task/nonce/challenge fields and structured SHA-256 receipts for inventory files checked by the preflight script. The runtime may then lock `native-presentation-tool` only as a provisional, attemptable route. The declaration stays `host-declared-unverified`; it is not `verified: true`, cannot make the route ready, and is neither a bundled tool nor a permanent promise. A provisional route permits the non-authoring stages and one locked Output attempt, but delivery still requires independently validated written PPTX objects and final renders.

Runtime preflight contract 1.3 first binds the fresh latest-component report, then issues the run ID, task-request SHA-256, nonce, task-root digest, and bounded validity window from the actual canonical task bytes. The issuer writes `.clayz-run-challenges/<run>.issued.json`; the single scan must receive the same task bytes and the same task root, reopen and hash-check that issuance record, and exclusively create `.clayz-run-challenges/consumed/<challenge-sha>.json`. Both ledger files are reopened and byte-hash validated by the preflight library. Copying or renaming the challenge therefore cannot create a second run, and moving it to another task root is rejected. The scan then binds the exact resolved-config SHA-256. Its `required_capabilities` is the union of the resolved configuration and any additive task requirements; callers cannot shrink the configured set. Preflight separates those route requirements from target-application acceptance. `target_application_checks` records every configured PowerPoint, WPS, LibreOffice, or other target as `available` or `unavailable` with `blocks_authoring=false`. An unavailable target is produced and audited as `deferred`; an available but unused target is `not-selected`; only an executed check may be `pass` or `fail`.

After final report validation, `scripts/publish_supervised_pair.py` is the only normal handoff path. It first copies the PPTX and report into a new staging bundle, performs semantic validation on those staged bytes, atomically publishes the directory, and repeats hash and semantic validation on the published bytes. The bundle contains exactly the PPTX, `ppt-supervision-report.json`, and `delivery-manifest.json`. A manually copied PPTX or report does not establish completed delivery.

## Dependency levels

1. Common authoring: Python 3.10+, `python-pptx`, Pillow, and PyYAML. This route does not require a host model's private presentation tool.
2. Final rendering in the v0.8.0 local release: one PowerPoint COM process on Windows. Cloud Public Light may select a host-provided presentation or Artifact Tool route during preflight. Other local operating-system routes are not v0.8.0 release claims.
3. Lazy media support: Poppler only for PDF page input or the LibreOffice PDF-to-PNG rendering route; an SVG converter only when the selected deck actually contains SVG on a backend that cannot insert it natively.

The repository bundles contracts, adapters, validators, preflight logic, and per-platform launcher scripts. Third-party applications and binaries remain external unless their licenses and platform packaging are separately reviewed.

## Public Light targets and local platform packages

Run `python scripts/build_runtime_packs.py --bundle light` to create deterministic Cloud Public Light and Local Public Light ZIPs under `dist/`. Both bind the same `public_core_sha256` and bundled public Provider snapshot. Cloud Light omits local adapters and platform packs because ChatGPT supplies tools; Local Light retains local execution routes. After `scripts/fetch_offline_wheels.py --platform windows` stages reviewed CPython 3.12 wheels, the v0.8.0 release build creates only the Windows offline dependency add-on. No Light archive contains third-party wheels, and no macOS, Linux, or iOS release package is produced. See [`release-packages.md`](release-packages.md).
