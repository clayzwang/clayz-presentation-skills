# Execution ledger and bounded reflection

Use this route when more than one tool call, renderer attempt, repair cycle, or environment is involved. It operationalizes execution-history and environment-grounded reflection ideas cited from [PPTAgent](https://github.com/icip-cas/PPTAgent) and [DeepPresenter](https://arxiv.org/abs/2602.22839) without copying their orchestration code, prompts, models, or tools.

## Ledger first, interpretation second

Record observable facts with `scripts/execution_ledger.py`:

- stage and tool identity;
- cycle number and bounded maximum;
- status and stable error code;
- hashes of concrete input and output files;
- render, inspection, or validation evidence references;
- a concise environment message.

Do not write hidden chain-of-thought, speculative motives, or unverified success into the ledger. It is an audit trail, not a model transcript and not a new approval source.

```bash
python scripts/execution_ledger.py init run-ledger.json --run-id RUN-001 --config config/default.json
python scripts/execution_ledger.py record run-ledger.json --cycle 1 --stage output \
  --tool pptxgenjs --status failed --input render-manifest.json \
  --error-code PPTX_WRITE_FAILED --message "Renderer returned a non-zero exit status"
python scripts/execution_ledger.py close run-ledger.json --final-status incomplete
```

## Reflection routing

For each failure, classify the owning boundary before suggesting a response:

- invalid facts, claims, sequence, or evidence → Logic;
- locked wording, length, grammar, or terminology → Copy;
- visual idea, area allocation, medium, semantic tree, or reading order → Art Direction;
- coordinates, object API, media, font, compatibility, or file repair → Output;
- missing capability, dependency, permission, or renderer → environment/user.

Supervisor reports the conflict and route. It does not execute a new composition, invent approval, or repeat until a favorable result appears.

## Stop conditions

Stop the technical loop when it passes, reaches the configured cycle limit, repeats the same error without new evidence, requires an upstream baseline change, or lacks a required capability. Close as `known-risk` or `incomplete` rather than hiding the gap. Automated scores remain diagnostic; the written PPTX and actual render evidence take precedence.
