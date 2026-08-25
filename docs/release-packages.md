# Release packages

Version 0.5.1 separates plugin code from optional third-party Python dependencies.

## Files

- `clayz-presentation-skills-0.5.1-light.zip` is the default plugin. Install dependencies online with `python -m pip install -r requirements.txt`, or pair it with one offline add-on below.
- `clayz-presentation-skills-0.5.1-offline-windows-py312.zip` supports CPython 3.12 on Windows x86-64.
- `clayz-presentation-skills-0.5.1-offline-macos-py312.zip` supports CPython 3.12 on macOS arm64 and x86-64.
- `clayz-presentation-skills-0.5.1-offline-linux-py312.zip` supports CPython 3.12 on manylinux 2.28 x86-64 and aarch64.
- `SHA256SUMS.txt` authenticates the four archives.

The offline add-ons are dependencies, not replacement plugin archives. Extract the matching add-on and run:

```bash
python install_offline_dependencies.py
```

The installer uses `--no-index`, `--only-binary`, and `--require-hashes`. It never contacts a package index. Pass `--target <directory>` for an isolated installation. Use the light archive alone when the environment can install `requirements.txt` normally.

## Boundaries

The light archive excludes Experience Center cases, examples, tests, presentation/PDF files, showcase media, fonts, caches, and release working files. Offline archives contain only the reviewed dependency wheels, an exact hash lock, an installer, a machine-readable manifest, and third-party notices. PowerPoint, WPS, LibreOffice, Poppler, and Python itself are never redistributed by these archives.

Every completed ZIP is reopened and scanned. Packaging fails and deletes the candidate archive if a private corporate showcase token is found in a member path, readable payload, nested wheel path, or nested wheel license/metadata text.

## Maintainer commands

```bash
python scripts/validate_all.py
python scripts/fetch_offline_wheels.py
python scripts/build_runtime_packs.py
python scripts/verify_release_bundles.py
```

Do not publish `.release-cache/`; it is only a local wheel staging directory. Preserve wheel contents and license metadata unchanged.
