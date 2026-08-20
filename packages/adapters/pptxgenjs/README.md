# Experimental PptxGenJS adapter — disabled by default

This original Clayz adapter maps a resolved `io.clayz.presentation.render-manifest/1.0` JSON file to editable PowerPoint objects through the public [PptxGenJS 4.0.1 API](https://gitbrent.github.io/PptxGenJS/). No PptxGenJS source, dependency lock, demos, templates, or media are bundled.

## Security status

The route is **disabled by central configuration** because PptxGenJS 4.0.1 currently depends on `image-size`, for which GitHub lists two unpatched high-severity denial-of-service advisories: [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) and [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq). No patched npm release is available as of the v0.2.0 review date.

Therefore this repository does not install or execute the dependency in CI, and the adapter blocks image/SVG routes. Do not enable it for untrusted or production input. A maintainer may re-evaluate the route after a patched, auditable upstream release. The source remains as an independently written API mapping and syntax-checked experimental reference.

Text, shapes, lines, tables, and standard charts are mapped; object IDs become editable object names. Manual local experimentation additionally requires explicit `--acknowledge-upstream-risk` and a separately obtained dependency. This is not a recommendation to install the currently vulnerable dependency.

Writing a PPTX is not final QA. Reopen the file in a configured target application, render every slide, inspect objects and glyphs, and run Output plus Supervisor checks.

If the route is safely re-enabled in a future version, use `scripts/stamp_pptx_metadata.py` separately to add the documented, removable Clayz brand signature. The adapter itself does not inject hidden slides, invisible shapes, tracking IDs, network callbacks, or unremovable watermarks.

This adapter does not import or reconstruct a reference deck master. A user-supplied master or native-presentation backend may be selected separately through central configuration when legally and technically appropriate.
