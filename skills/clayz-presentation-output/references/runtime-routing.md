# Runtime Routing Contract

## One scan, one route

Before Logic, root Supervisor saves the canonical task-request bytes, issues a fresh run challenge with `../../../scripts/runtime_preflight.py --issue-challenge`, and runs the capability scan exactly once with the same task bytes and challenge. Issuance and consumption are separate canonical task-root ledgers keyed by run/challenge; the preflight library reopens both files and checks their byte hashes, so copying or renaming the challenge cannot replay it and moving it to another task root is rejected. Output consumes that same task-local `runtime-preflight.json`; it never launches another scan. The report must bind the script-issued run ID, task-request SHA-256, nonce, task-root SHA-256, issuance/consumption receipt hashes, and exact resolved-config file SHA-256. Treat `selected_route.locked=true` as an execution invariant.

Do not rediscover tools, reopen dependency selection, or switch backends during the run. If the locked backend has a hard failure, close the run as failed. At most once, begin a new run from preflight and select an already reported fallback route. A fallback restart is not an in-place route switch.

## Separate route gates from target-application acceptance

`renderer.required_capabilities` describes the hard requirements for a route that can author, write and inspect the PPTX; rendering is used when a render route is available and selected. `renderer.target_applications` describes compatibility targets to observe. Never promote application-specific capabilities such as `powerpoint-reopen-render` or `wps-reopen-render` into the route-required set merely because those applications are targets.

Preflight records every target as `available` or `unavailable` in `target_application_checks` with `blocks_authoring=false`. Any available host-provided capability declaration must carry the same run/task/nonce/challenge values plus structured receipts for hash-checked inventory files; it remains `host-declared-unverified`, cannot set route readiness, and can create only a `provisional`/`attemptable` route. Output may make one locked attempt on that route. When the render capability is available and selected, actual PPTX, object and render validation supports final delivery; when it is unavailable or unselected, record `deferred` or `not-run` coverage and continue with the written PPTX. Never claim a render pass or invent pixels. After writing the deck, Output records an available and selected target as `pass` or `fail`, an available but unused target as `not-selected`, and an unavailable target as `deferred`. Supervisor embeds all results—including absences—and their evidence in the final report to bound compatibility claims and support attribution; they do not block Logic.

`required_capabilities` is the union of the bound resolved configuration and any task-local additive requirements. A caller may add a requirement but may never use an override to remove a Personal Extension requirement.

In calibrated delivery, preflight retains that complete list while checking a
small format-level writer core for route attemptability. A real
writer may therefore be `attemptable` with `available=false` when master
preservation, layout inheritance, East Asian font naming, render coverage, or
another configured capability is still unverified. Treat those entries as
pending evidence rather than as proof that the writer is absent. Use the actual
selected master in Output and record observed load, object, font, render, and
failure results; `spec-only` is never an editable PPTX route. Legacy routing
continues to require every configured capability before selecting a route.

## Host-model-independent baseline

The baseline authoring chain is the public render-manifest contract plus the public `python-pptx` adapter. The host model never writes coordinates directly; it supplies approved semantic artifacts and the deterministic Output layer consumes the resolved manifest. Host-provided Artifact Tool support may be selected when it is available and satisfies the same contract, but it is not required by the baseline chain.

## Capability profiles

Profiles describe interaction capabilities, not model brands or size alone.

| Profile | Interaction route |
| --- | --- |
| A | Tool calling, structured output, and visual inspection; direct orchestration and final visual review. |
| B | Tool calling and structured output; direct orchestration with external or human visual QA. |
| C | Structured text/JSON without tools; an external adapter invokes the same locked runtime. |
| D | Constrained or small model; use one narrow tool call when available, otherwise the same adapter-mediated route as C. |

The user interacts in natural language. `runtime-preflight.json`, render manifests, and other JSON contracts are internal handoffs, not user-authored inputs.

## Bounded execution

Read budgets from central configuration. The normal path performs one capability scan, one source-collection round and one authoring write. When a render route is available, use one persistent Office process when Office is selected and one full-deck final render; a detected technical defect may use one targeted repair, one additional write and one additional full-deck render. When no render route is available, record the deferred coverage and do not fabricate a render. No technical repair may rewrite approved Logic, Copy, or Art Direction.

## Platform packs and PDF support

Use the common pack plus exactly one operating-system pack. Windows prefers a single persistent PowerPoint COM render process; macOS and Linux prefer one LibreOffice process. PDF page ingestion is lazy. Poppler is required only when PDF pages are inputs or the selected LibreOffice render route converts PPTX to PDF before PNG QA.
