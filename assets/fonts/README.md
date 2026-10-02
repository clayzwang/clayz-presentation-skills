# STKaiti release dependency

The release requires original STKaiti bytes and documented redistribution authority.
`manifest.json` lists each exact file path, byte count, SHA256, font family, source,
`redistribution_authorized: true`, license/authorization file path and its SHA256.
An empty manifest is a development placeholder and makes release packaging fail.
No font is fetched from an unofficial mirror or silently substituted.

Linux: run `python scripts/font_bundle.py --prepare <task-root>` and use the returned
`FONTCONFIG_FILE` for **both** design and final render processes. The command verifies
Fontconfig resolves the requested family to the supplied file, without system-wide changes.
Windows/macOS: install the manifest-listed font through the operating system font installer,
then open the deck in the intended PowerPoint/WPS version and inspect wrapping and glyphs.
PPTX font names alone do not establish installation or embedding.

Fonts are shipped once in the code bundle. Do not embed the entire font into every PPTX by
default. If embedding is explicitly requested and permitted, include its size in PPTX QA.
