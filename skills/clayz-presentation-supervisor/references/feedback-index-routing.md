# Feedback index routing

Supervisor diagnoses and routes evidence; it does not own the feedback store or
decide that an observation has become reusable truth.

1. Route each learning candidate to the earliest responsible stage: Logic,
   Copy, Art Direction, or Output.
2. Keep the source record at `promotion_status=observation`.
3. A separate human admission must bind the candidate's exact canonical
   SHA-256, approved uses, `never_copy` boundary, and promotion target.
4. After admission, the responsible runtime may rebuild a private learning
   provider. A changed record, missing admission, or malformed admission is
   skipped and reported.
5. Public-open-source retrieval excludes these private learning records. Moving
   one into the built-in catalog is a separate source-review and publication
   decision.
6. Retrieval benchmark snapshots are review evidence, not an adaptive memory.
   Supervisor reports drift but never updates a baseline automatically.

When no admitted record matches, preserve `unresolved` or the core fallback
already allowed by the responsible stage. Do not invent a learning record,
Failure Pattern, Layout Contract, or Composition Pattern to fill the gap.
