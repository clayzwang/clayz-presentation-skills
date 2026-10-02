# Optional licensed font bundle

STKaiti is NOT included in 0.17.5: redistribution authorization has not been supplied.
The user authorized release without it. Obtain it from a licensed source and install it
in the rendering environment when a task requires it; font absence/substitution must
remain explicit in the report and cannot establish font-accurate acceptance.
`manifest.json` lists each exact file path, byte count, SHA256, font family, source,
`redistribution_authorized: true`, license/authorization file path and its SHA256.
An empty font list is valid when required_families is empty. Every listed font still
requires verified redistribution authority and hashes.
No font is fetched from an unofficial mirror or silently substituted.

For authorized manifest-listed files only, on Linux run `python scripts/font_bundle.py --prepare <task-root>` and use the returned
`FONTCONFIG_FILE` for **both** design and final render processes. The command verifies
Fontconfig resolves the requested family to the supplied file, without system-wide changes.
Windows/macOS: install the manifest-listed font through the operating system font installer,
then open the deck in the intended PowerPoint/WPS version and inspect wrapping and glyphs.
PPTX font names alone do not establish installation or embedding.

Fonts are shipped once in the code bundle. Do not embed the entire font into every PPTX by
default. If embedding is explicitly requested and permitted, include its size in PPTX QA.
