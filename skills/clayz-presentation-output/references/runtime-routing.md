# Runtime Routing Contract

## One scan, one route

Before authoring, run `../../../scripts/runtime_preflight.py` exactly once for the run. Persist the emitted `runtime-preflight.json` beside task-local evidence and treat `selected_route.locked=true` as an execution invariant.

Do not rediscover tools, reopen dependency selection, or switch backends during the run. If the locked backend has a hard failure, close the run as failed. At most once, begin a new run from preflight and select an already reported fallback route. A fallback restart is not an in-place route switch.

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

Read budgets from central configuration. The normal path performs one capability scan, one source-collection round, one authoring write, one persistent Office process when Office is selected, and one full-deck final render. A detected technical defect may use one targeted repair, one additional write, and one additional full-deck render. No technical repair may rewrite approved Logic, Copy, or Art Direction.

## Platform packs and PDF support

Use the common pack plus exactly one operating-system pack. Windows prefers a single persistent PowerPoint COM render process; macOS and Linux prefer one LibreOffice process. PDF page ingestion is lazy. Poppler is required only when PDF pages are inputs or the selected LibreOffice render route converts PPTX to PDF before PNG QA.
