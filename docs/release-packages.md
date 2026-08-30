# Release packages

Version 0.6.0 builds two public Light targets from one public core, keeps local third-party Python dependencies separate, and provides an owner-private cloud composer outside the public release path. Local release validation is Windows-first; no other operating-system package is published in this version.

## Files

- `clayz-presentation-skills-0.6.0-cloud-light.zip` is the ChatGPT-facing public brain. It relies on host tools and excludes local adapters, operating-system packs, and offline dependencies.
- `clayz-presentation-skills-0.6.0-local-light.zip` is the Windows-validated local public plugin. Install dependencies online with `python -m pip install -r requirements.txt`, or pair it with the Windows offline add-on below.
- `clayz-presentation-skills-0.6.0-offline-windows-py312.zip` supports CPython 3.12 on Windows x86-64.
- `SHA256SUMS.txt` authenticates the two Light archives and the Windows offline add-on.

No macOS, Linux, or iOS archive is produced for v0.6.0. Source-level portability hooks remain future work and must not be treated as a tested release.

The offline add-on is a dependency bundle for Local Public Light, not a replacement plugin archive and never a Cloud Light dependency. Extract it and run:

```bash
python install_offline_dependencies.py
```

The installer uses `--no-index`, `--only-binary`, and `--require-hashes`. It never contacts a package index. Pass `--target <directory>` for an isolated installation. Use Local Public Light alone when the local environment can install `requirements.txt` normally.

## Boundaries

Both public Light archives contain the same `public_core_sha256`, bundled public Provider manifest/index, and five-stage method. They exclude Experience Center cases, examples, tests, presentation/PDF files, showcase media, fonts, caches, private Profiles, private Provider manifests, private indexes, and release working files. Cloud Light additionally excludes local execution adapters and platform packs. The Windows offline archive contains only reviewed dependency wheels, an exact hash lock, an installer, a machine-readable manifest, and third-party notices. PowerPoint, WPS, Poppler, and Python itself are never redistributed by these archives.

`scripts/compose_personal_light.py` is a separate local-only workflow. It reads private inputs outside the repository and writes a private cloud ZIP under `dist/private/`. Its default artifact is one self-contained Skill for the ChatGPT Skills uploader; the five stages remain internal modules rather than five detached uploads. That ZIP is not a public release artifact. See [`chatgpt-personal-light.md`](chatgpt-personal-light.md).

Every completed ZIP is reopened and scanned. Packaging fails and deletes the candidate archive if any term from the repository-external `CLAYZ_RELEASE_DENYLIST` is found in a member path, readable payload, nested wheel path, or nested wheel license/metadata text. The denylist itself is never committed or packaged.

## Maintainer commands

```bash
python scripts/validate_all.py
python scripts/fetch_offline_wheels.py --platform windows
python scripts/build_runtime_packs.py --platform windows
python scripts/verify_release_bundles.py --platform windows
```

Do not publish `.release-cache/`; it is only a local wheel staging directory. Preserve wheel contents and license metadata unchanged.
