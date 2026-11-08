# Pattern & Dataset Library

Stage 4 adds governed, dataset-ready metadata without turning the public
repository into a template, case, or model library. Every optional record has a
stable ID, a human-admitted index record, a hash-bound JSON payload, explicit
rights, and a Retrieval Receipt before selection.

## Four record contracts

| Record | Answers | Does not contain |
| --- | --- | --- |
| Composition Pattern | How an approved semantic relation may become a spatial relationship | coordinates, themes, variants, templates, or assets |
| Failure Pattern | What rendered evidence identifies a failure, who could first prevent it, and how to verify repair | automatic aesthetic truth or Supervisor-owned repair authority |
| Reference Record | Dataset-ready metadata for page role, first visual, relation, density, medium, series role, and governed links | source copy, media, coordinates, fonts, or model features |
| Sequence Record | Persistent elements, progressive change, allowed variation, and break reason across registered references | slides, screenshots, masters, or source presentation files |

The initial public records are original Clayz methods and fully synthetic
metadata. They are examples of the contracts, not a claim that one pattern is a
universal aesthetic answer.

## Receipt-bound pattern decision

Art Direction builds a structured request from approved task mode, page role,
semantic relations, purpose tags, locale, constraints, and expected visual
effect. `packages/patterns/compile_composition_pattern.py` then:

1. retrieves registered Composition Pattern candidates;
2. selects automatically only when exactly one materializable candidate
   remains, or accepts an explicit preferred ID that appears in the receipt;
3. retrieves every Failure Pattern linked by the selected record into a second
   receipt;
4. emits a coordinate-free Composition Plan only when the pattern and all
   linked failures are registered, admitted, hash-current, rights-eligible, and
   receipt-selected.

No match, an unretrieved preferred ID, ambiguity, a missing linked failure, or
hash drift yields `unresolved` or a validation error. The fallback is the core
Art Direction workflow without claiming a named pattern. It never invents a
replacement.

## Layer boundary

A Composition Plan records the selected pattern, task-specific constraints,
expected visual effect, rejected alternatives, semantic-to-spatial mapping, and
receipt-bound failure guards. It does not consume or emit Theme, Visual Variant,
Layout Contract, Layout Tree, or resolved coordinates.

Art Direction owns pattern selection and visual judgment. Output consumes the
approved plan and builds editable objects without re-selecting the method.
Supervisor may use registered Failure Patterns to diagnose rendered evidence
and route repair to the earliest responsible stage; Supervisor does not own the
repair or promote the record.

## Metadata-only dataset export

`packages/patterns/export_metadata_dataset.py` exports only registered,
human-admitted public metadata from the four Stage 4 record types. The export
includes stable IDs, source revisions and hashes, classification, and validated
metadata. Its guards explicitly exclude asset bytes, raw source text,
coordinates, fonts, model weights, generated-artifact auto-admission, and
automatic aesthetic truth.

The exporter is a future interoperability surface, not a bundled training set
or training pipeline. It never downloads an upstream dataset, embeds a visual
feature, or turns generated output into reference truth.

## Synthetic commands

```bash
python packages/patterns/compile_composition_pattern.py \
  examples/synthetic-pattern-library/comparison-request.json \
  --resolution-output /tmp/pattern-resolution.json \
  --receipt-dir /tmp/pattern-receipts \
  --plan-output /tmp/composition-plan.json

python packages/patterns/export_metadata_dataset.py \
  /tmp/clayz-metadata-dataset.json
```

All public catalog payloads are JSON method metadata. CI rejects presentation
files, masters, themes, images, fonts, tabular datasets, model weights,
unregistered payloads, stale hashes, orphan links, and brand-specific records.
