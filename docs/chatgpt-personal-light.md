# ChatGPT Personal Light

This is the host handoff for the private ZIP produced by `scripts/compose_personal_light.py`. The [official OpenAI skill format](https://learn.chatgpt.com/docs/build-skills) uses one root `SKILL.md` and permits optional references, assets, scripts, and UI metadata. The composer therefore compiles the five-stage source from the one Public Core into one self-contained ChatGPT Skill. Its root `SKILL.md` owns only the Supervisor control plane and internal routing; Logic, Copy, Art Direction, Output, and Supervisor remain responsibility-separated internal modules. ChatGPT tools are the body, so the archive neither relies on five detached Skills being reassembled nor repackages a local execution environment.

## Required control plane and recommended content layout

Use one Library root named `PPT`. Physical paths are host details and must never appear in a Skill, index record, or reusable Profile field. Only `_extension/providers/<provider>/provider.manifest.json` and its declared index location are required by the private cloud control plane. The `references`, `assets`, and `cases` branches below are the recommended normalized layout for new or gradually migrated content. Keep the source Profile in the local private control plane; the composer embeds only its resolved result, so the source Profile does not need to be uploaded as a Library file.

```text
PPT/
├── _extension/
│   └── providers/
│       └── private/
│           ├── provider.manifest.json
│           └── index/
│               └── records.jsonl
├── references/
│   ├── logic/
│   ├── copy/
│   ├── art-direction/
│   ├── output/
│   └── supervisor/
├── assets/
│   ├── masters/
│   ├── brand/
│   └── fonts/
└── cases/
    ├── admitted/
    └── rejected/
```

Index payload refs use logical URIs rooted at `library://<profile-namespace>/`. The profile's `chatgpt-personal` mount binds that logical root to `PPT`.

Existing private material does not have to move before the first test. It may remain in its current Library folders as long as admitted index records point to the correct logical URIs under the mounted root. When moving or renaming an item, update its source and payload URIs, rebuild `records.jsonl` and `provider.manifest.json`, and replace both at their stable control-plane locations. Do not move files first and leave stale index records behind.

## Compose locally

Keep the real profile and provider manifest outside the public repository:

```bash
python scripts/compose_personal_light.py <private-profile.json> \
  --provider-manifest <private-provider.manifest.json>
```

The default output is written under `dist/private/`, which is excluded from public release scans and Git tracking. The ChatGPT Skills-ready ZIP has exactly one root `SKILL.md` and contains `agents/openai.yaml`, the one Public Core, public Provider manifest/index, five internal stage modules, generated resolved config, `runtime/personal-extension.json`, external `runtime/runtime-lock.json`, `runtime/skill-mount-contract.json`, runtime preflight contract 1.2, supervision report contract 3.3, and the paired publisher. The external pack lock binds the exact set and snapshots of every required Provider so a runtime and config cannot be consistently shrunk together. The ZIP contains no `.codex-plugin/plugin.json`, nested `SKILL.md`, local adapter, platform pack, source Profile, source private manifest, private JSONL index, attachment, master, font, or case.

The repository and Codex plugin continue to use five independent Skills as source and runtime modules. Only the ChatGPT Skills host adapter compiles them into one publication unit; it creates neither a second public core nor merged stage authority. To build the marketplace plugin form explicitly, pass `--artifact-kind plugin --plugin-name clayz-presentation-skills-personal`. Do not upload that form through the ChatGPT Skills uploader.

At the start of a presentation task, Supervisor inventories the mounted runtime, task inputs, owner Library, public Index, brand assets, host capabilities, and fonts; it reports what was found and selected before Logic begins. Any owner-learning source manifest is generated task-locally from that inventory and passed to `scripts/materialize_owner_index.py`; the manifest and source bytes are never part of this public repository.

## Upload and update rules

1. Upload the default single-Skill ZIP. Do not give the ChatGPT Skills uploader the marketplace plugin ZIP or five detached Skills.
2. Require exactly one root `SKILL.md`; `runtime/skill-mount-contract.json` must enumerate and validate all five internal stage modules.
3. Do not edit the generated runtime or resolved config in ChatGPT; change the source Profile and recompose.
4. To add a reference, update the Library attachment, admitted index record, and provider manifest at their stable locations. Do not recompose unless the Profile or provider list changes.
5. Start a fresh chat for acceptance testing after replacing the package.
6. Keep the previous five personal skills only as rollback during acceptance. Remove them after direct invocation, implicit invocation, visible preflight/resource brief, five-stage handoff, required-asset failure, paired PPTX plus complete supervision-report delivery, and public fallback tests pass.
7. The old ChatGPT Project used to maintain the GitHub PPT workflow is not a runtime dependency and may be archived after its unique files are inventoried.

The final cloud runtime is “one ChatGPT Skill publication entry + one Cloud Public Light brain + five internal stage modules + ChatGPT tool body + Personal Extension Profile + private Library/index memory.” Host file and tool capabilities may differ from local Codex. A mount proves discoverability, not that a particular tool or font is available. Supervisor opens the lifecycle record, saves the canonical current request bytes, issues a fresh run challenge and task-root issuance record, resolves `config/personal-extension-resolved.json`, and runs preflight exactly once before Logic with the same task bytes. The preflight binds the script-issued run ID, task hash, nonce, task-root digest, canonical issuance/consumption receipts, and exact config hash; task requirements are additive only. Copying or renaming a challenge cannot replay it. An available host-capability declaration must be challenge-bound and backed by hash-checked inventory receipts, but remains `host-declared-unverified`: it can make a native route provisional/attemptable, never ready. That provisional route may be attempted once; only independently validated final PPTX, objects, and renders can authorize delivery. Failure to materialize and actually select every required private Provider, or absence of both a ready and attemptable authoring/render route, is fail-closed. Native PowerPoint/WPS target acceptance is always scanned but remains post-output observation rather than an authoring gate; when unavailable, it is `deferred` in the final report and limits the compatibility claim. Final delivery must be materialized by `scripts/publish_supervised_pair.py` and contain both the PPTX and `ppt-supervision-report.json`, with `delivery-manifest.json` proving the pair; neither file is complete alone.

At the start of a task, use the two-step fresh binding below. The issuer also creates `.clayz-run-challenges/<run>.issued.json`; the scan consumes the challenge through `.clayz-run-challenges/consumed/<challenge-sha>.json`. The scan must receive the same immutable task-request file used at issuance; a copied/reused challenge, missing issuance record, different task root, or different task bytes fails closed. If the host declares tools available, its attestation must repeat the challenge values and point to task-local `host-tool-inventory/1.0` JSON files through SHA-256 receipts; the resulting route is still provisional until final artifacts pass. Do not save that transient capability inventory in the Profile or Library index.

```bash
python scripts/runtime_preflight.py --issue-challenge \
  --task-request <canonical-task-request.txt> --output <run-challenge.json>
python scripts/runtime_preflight.py --challenge <run-challenge.json> \
  --task-request <canonical-task-request.txt> \
  --host-capabilities <host-capability-attestation.json> \
  --output <runtime-preflight.json>
```
