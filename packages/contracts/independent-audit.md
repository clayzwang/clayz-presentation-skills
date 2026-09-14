# Independent audit module

`io.clayz.presentation.independent-audit/1.0` is the shared post-Output audit
contract. It is an internal module used by the Supervisor publication unit; it
is not a sixth production stage, a second Public Core, or a second retrieval
engine.

## Purpose and authority

Output sends the completed PPTX, its object evidence and available render
evidence to both Supervisor and this module. The Auditor reads the immutable
original user request and the Supervisor's current commitments and changes,
then checks the actual written file and renders when available. It returns an immutable audit artifact to
Supervisor. The Auditor reports facts, findings and uncertainty; it does not
rewrite the deck, grant release authority, or change a stage conclusion.

Supervisor remains the coordinator and final release owner. It may route a
finding to the responsible stage or release a usable deck with disclosed
quality findings when the user's delivery policy allows that. Supervisor must
preserve the Auditor's findings and statuses verbatim. A quality defect is not
the same as an artifact binding, identity, format, or evidence-integrity
failure.

## Required evidence and interface

The audit artifact uses the contract name above and binds, by actual path,
byte count and SHA-256 where applicable:

- `task_request`: the original immutable user request;
- `acceptance_rules`: the canonical task-acceptance contract, including the
  user's explicit hard and soft requirements and their precedence;
- `supervisor_rules`: the Supervisor's initiation commitments, calibration
  findings, and any recorded task-scope or requirement changes;
- the final PPTX, object inventory and any final render evidence available for
  the checks; and
- `run_id`, task request hash, configuration/acceptance bindings and
  `audited_at`.

For a current calibrated report3.6 delivery, this artifact is assembled with
the five real stage records, any bound `work-notes`, three
`calibration_artifacts`, and a `supervisor_release`; its derived
`core_sequence` is the lifecycle summary. The formal supervision JSON also
assembles the full work report from those records and the actual primary
artifacts, then derives a readable Markdown companion from the JSON. v3.5 and
older lifecycle, Index, retrieval and performance sections remain readable as
legacy or optional supporting evidence and are validated only when supplied.

The Auditor contributes independent observations about the actual written PPTX,
objects, renders, page text/notes when available, and disclosed coverage
limits. It does not fill missing stage notes or reconstruct the work history;
the report must mark such evidence `not-recorded`, `deferred`, or `uncertain`.
It also does not replace the stage-owned professional judgment. Supervisor
preserves the artifact and decides release.

The artifact records `findings`, `audit_status`, and `coverage`. Each finding
states the observed evidence, expected state, actual state, impact, severity,
confidence and affected requirement or slide IDs when known. An unchecked item
is `deferred` with its coverage limitation; it is never a fabricated `pass`. If
no render route is available, the Auditor may audit the written PPTX and object
evidence, record render coverage as deferred/not-run, and return the
binding-complete artifact without blocking a written-PPTX delivery solely
because pixels could not be produced.

`independent_context` is mandatory evidence about how the review was run. It
records `execution_mode`, `context_id`, `model_identity_disclosure`, and
`limitations`. A separate model or process may be used when the host provides
one. If the host cannot provide an isolated executor or context, use the
available review context and state that isolation was unavailable; do not
describe it as a separate model, process or person or claim stronger
independence than the evidence supports. This limitation does not block
production or delivery by itself.

The assembled supervision report binds this artifact as `auditor_artifact`,
including its path, SHA-256 and `audited_at`. A new run may be released only
after that binding is valid and the release time is no earlier than the audit
time. The compatibility `supervisor_roles.final_auditor` entry, when retained
in a report3.6 or v3.5 report, is `not-needed` or `incomplete`; the stage-five
work record uses role `auditor`. Historical reports that contain a complete
Supervisor `final_auditor` role remain readable as legacy evidence.

## Rule precedence and delivery policy

The Auditor evaluates requirements with the existing precedence: the original
user request, saved personal configuration, then defaults. Supervisor records
the parsed objective, commitments and user-authorized changes and may clarify
how a requirement is checked, but does not become a new authority that
overrides the user or saved layer. The Supervisor cannot turn a user hard
requirement into a soft one during delivery. If a hard requirement is unmet,
the Auditor records `fail` with evidence; it is not rewritten as `pass`.

Only an explicit user no-delivery condition is entered in
`acceptance.release_conditions`; the default is `[]`. A hard classification or
legacy `blocking=true` value does not create that condition automatically.

By default, a binding-complete artifact with quality findings remains a valid
delivery candidate and is reported with its findings (normally
`run_status=issues-found`). Optional Library knowledge that cannot be read,
unexecuted target-application acceptance, and disclosed quality shortcomings
do not by themselves refuse generation or delivery. They remain limitations or
deferred checks. A user instruction that explicitly says not to deliver when a
named requirement is unmet adds a release condition; otherwise no per-finding
approval or repeated repair loop is required.

Binding, identity, format, missing-required-artifact, or audit-evidence
integrity failures prevent a verified paired publication because the result
cannot be established. This is an evidence failure, not a quality judgment.

## Shared knowledge boundary

The Auditor may read the same locked CompositeIndex, selected receipts and
source passages as the run when a knowledge-backed check needs them. It does
not create a fifth learning silo, a private replacement index, or an automatic
promotion route. Reusable observations remain observation-only and return to
Logic, Copy, Art Direction or Output through the existing feedback route.

## Operating sequence

1. Receive the Output handoff and the immutable task/acceptance/Supervisor-rule
   bindings.
2. Establish the review context and disclose whether it is a separate executor,
   an isolated context, or the available same-agent context. Do not claim an
   isolation level that the host did not provide.
3. Inspect the written PPTX and object evidence directly, and inspect final
   renders when available. Check every declared hard and soft requirement that
   the evidence covers, and keep unavailable or unexecuted checks visibly
   deferred.
4. Emit the immutable audit artifact with concrete findings, coverage and
   limitations. Preserve failed findings even when the deck remains deliverable.
5. Return the artifact to Supervisor. Supervisor reconciles it with stage
   evidence, decides the release disposition under the user's policy, and may
   route repairs without editing the audit result.
