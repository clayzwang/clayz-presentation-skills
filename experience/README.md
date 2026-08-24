# Clayz Experience Center

This directory contains the static GitHub Pages experience for public output evidence.
It is deliberately separate from `examples/`, `knowledge/`, and the five production
skills.

## Boundary

- `examples/` remains fully synthetic and machine-oriented.
- Experience artifacts demonstrate output capability only.
- Experience artifacts are never admitted into the reference or knowledge corpus.
- Every downloadable presentation must be declared in `case-manifest.json`.
- `scripts/check_release_hygiene.py` scans the XML payload of each declared PPTX for
  private paths, opaque file identifiers, credentials, and private denylist terms.
- Company names and marks remain the property of their respective owners and do not
  imply affiliation or endorsement.

## Add a case

1. Add flattened, web-safe preview images under `assets/cases/<case-id>/`.
2. Add the editable output under `assets/decks/`.
3. Declare the repository path, public download path, and isolation policy in
   `case-manifest.json`.
4. Put optional reproducibility material under `materials/<case-id>/` and declare
   its `source_path`; do not place public-data cases in the synthetic `examples/` tree.
5. Add the case to `index.html` and `app.js`.
6. Run `python scripts/validate_all.py` before opening a pull request.

GitHub Pages is deployed by `.github/workflows/pages.yml`. The workflow publishes only
the assembled experience site and the existing showcase assets.
