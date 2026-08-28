# ChatGPT Personal Light

This is the host handoff for the private ZIP produced by `scripts/compose_personal_light.py`. The [official OpenAI skill format](https://learn.chatgpt.com/docs/build-skills) permits instructions plus optional references, assets, scripts, and UI metadata; a plugin may contain multiple skills. The composer uses Cloud Public Light as the brain, retains the five stages and bundled public Provider, and attaches one generated runtime/config pair. ChatGPT tools are the body, so the archive neither relies on same-name skill merging nor repackages a local execution environment.

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

The default output is written under `dist/private/`, which is excluded from public release scans and Git tracking. The install-ready ZIP places `.codex-plugin/plugin.json` at its root and contains the one Public Core, public Provider manifest/index, five skills, generated resolved config, `runtime/personal-extension.json`, and a complete-plugin mount contract. It contains no local adapters, platform packs, source Profile, source private manifest, private JSONL index, attachment, master, font, or case.

At the start of a presentation task, Supervisor inventories the mounted runtime, task inputs, owner Library, public Index, brand assets, host capabilities, and fonts; it reports what was found and selected before Logic begins. Any owner-learning source manifest is generated task-locally from that inventory and passed to `scripts/materialize_owner_index.py`; the manifest and source bytes are never part of this public repository.

## Upload and update rules

1. Upload the personal cloud composition ZIP. Cloud Public Light is its public brain base and should not be installed again beside it.
2. Do not install a second set of same-name private skills and expect automatic merging.
3. Do not edit the generated runtime or resolved config in ChatGPT; change the source Profile and recompose.
4. To add a reference, update the Library attachment, admitted index record, and provider manifest at their stable locations. Do not recompose unless the Profile or provider list changes.
5. Start a fresh chat for acceptance testing after replacing the package.
6. Keep the previous five personal skills until direct invocation, implicit invocation, five-stage handoff, required-asset failure, and public fallback tests pass. Then disable or archive them.
7. The old ChatGPT Project used to maintain the GitHub PPT workflow is not a runtime dependency and may be archived after its unique files are inventoried.

The final cloud runtime is “Cloud Public Light brain + ChatGPT tool body + Personal Extension Profile + private Library/index memory.” Host file and tool capabilities may differ from local Codex. A mount proves discoverability, not that a particular tool or font is available. Output must still use host capability preflight and fail closed when a required private asset cannot be materialized.

At the start of a task, the host adapter should inspect available presentation tools and pass an equivalent task-local declaration to `scripts/runtime_preflight.py --host-capabilities <json>`. Do not save that transient capability inventory in the Profile or Library index.
