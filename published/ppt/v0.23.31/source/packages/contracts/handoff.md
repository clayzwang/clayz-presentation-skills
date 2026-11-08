# Cross-stage handoff

For new runs, [Story and visual handoff](story-visual-handoff.md) defines
package 3.0 and plan 2.0. Logic supplies the complete chaptered narrative, Copy
owns pagination, and Art Direction locks full-deck image drafts with matching
element specifications before Output. Existing Supervisor calibrations remain.

Every stage artifact carries:

- `origin_namespace: io.clayz.presentation`;
- the resolved `configuration_sha256`;
- its artifact type and approval status;
- SHA-256 bindings to every upstream artifact it claims to use;
- stable IDs for slides, claims, copy units, layout nodes, objects, and findings.

The Supervisor starts the run from the user's original request and records the
explicit objective, hard requirements, soft requirements, precedence and
delivery promise in the existing acceptance contract. User requirements take
precedence over saved personal settings, which take precedence over defaults.
Hard requirements are implementation commitments and deterministic checks; a
failure is recorded honestly and does not by itself force an endless repair
loop or refuse a usable delivery. A user instruction that explicitly forbids
delivery when a named requirement fails is a release condition.

## Dual handoffs and calibration

New runs keep one shared task/Index path and send each stage artifact to both
its next owner and Supervisor. The Supervisor evaluates the artifact against
the same acceptance contract and returns a hash-bound
`io.clayz.presentation.supervisor-calibration/1.0` record before the next owner
locks its result:

| Handoff | Required recipients | Required downstream action |
| --- | --- | --- |
| Logic | Copy and Supervisor | Copy absorbs the Logic-to-Copy calibration before final Copy |
| Copy | Art Direction and Supervisor | Art Direction absorbs the Copy-to-Art Direction calibration before final plan |
| Art Direction | Output and Supervisor | Output absorbs the Art Direction-to-Output calibration before writing |
| Output | Supervisor and Independent Auditor module | Supervisor receives the Auditor artifact before final release |

The current implementation uses `calibration_bindings` on the consuming stage
record. Each binding names the calibration ID and SHA-256 and records
`accepted`, `partially-accepted`, or `declined` with a reason. A changed source
artifact makes the calibration stale; the owner must refresh the affected
calibration and downstream bindings. Declining a recommendation preserves the
stage owner's authority when the reason is recorded; it does not erase the
Supervisor's finding.

## Work notes and report continuity

Record the work while it happens. The short stage record remains the binding
record for primary artifacts, checks, decisions and open issues. A stage may
also attach an observed `work-notes` artifact through the existing
`record-stage --artifact` mechanism when the work contains useful context that should survive
handoff. JSON or Markdown notes can explain the task question, evidence and
sources, counterevidence, assumptions, uncertainty, storyline, copy choices,
visual decisions, calibration response, actual output, audit observations,
release reasoning and limitations. They are optional richer evidence, not a
second source of truth, an approval form, or a requirement to fill every
category.

The assembled report is produced from the primary stage artifacts, work
records, bound Auditor artifact and observed final PPTX. The report core also
records actual PPTX statistics and page text/speaker notes when available. A
missing note or unavailable observation stays explicitly `not-recorded`,
`deferred`, or `uncertain`; a later stage may not reconstruct it from memory or
turn it into a pass. The formal JSON is the source for its deterministic,
readable Markdown derivation. The Markdown should explain the saved research,
viewpoints, exclusions, visual intent and actual result in context; it is not a
key listing or raw JSON dump. It may be richer than the deck, but it does not
invent facts or restore scattered administrative tables. An old summary-only
report is evidence-incomplete, while `not-recorded` does not establish that a
stage was never executed.

The three Supervisor calibration records must show the finding, the receiving
stage's `accepted`, `partially-accepted`, or `declined` response, and the reason
for the downstream state. The Independent Auditor remains a separate post-
Output actor; Supervisor preserves its observations and decides release. The
publisher/manifest records the derived Markdown alongside the PPTX and formal
report in the manifest's derived-files collection, and `verify-handoff` is the
source of the exact final paths, hashes, task identity and PPTX summary. Final
consumers use that returned bundle and do not discover a report by globbing a
task directory.

Supervisor coordinates and calibrates; it does not write stage content,
silently replace an artifact, or perform the independent final audit. The
Independent Auditor uses the shared Index and current rules but owns a separate
review context and returns the immutable `independent-audit/1.0` artifact. If a
separate model or process is unavailable, the same agent may use a fresh audit
context only when it discloses that limitation; it must not claim true process
independence.

Downstream stages may challenge an upstream artifact with evidence. They may
not silently replace its source of truth. Quality findings and open issues may
continue through handoff when they are explicitly recorded; binding, identity,
format, missing-required-artifact and evidence-integrity failures still stop a
verified handoff or paired publication.

