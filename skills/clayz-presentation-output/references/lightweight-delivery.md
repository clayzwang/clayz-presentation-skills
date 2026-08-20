# Lightweight Delivery Contract

## Default and exceptions

Unless the user specifies otherwise, use `delivery_profile=lightweight`. High-resolution, print, very large display, pixel-faithful image reproduction, and preserving original media are explicit exceptions. Do not infer a high-resolution profile merely from “Pro mode,” “the image is important,” or a high-resolution source file.

The lightweight profile targets configured presentation applications, ordinary office hardware, messaging or email transfer, and standard projection. Optimize in this order: remove unnecessary media, resize to actual placed dimensions, choose an appropriate format, remove duplicates and unused objects, inspect attachments and fonts, then rerender. Never trade editability for size by rasterizing whole slides or converting body text to images.

## Raster preparation

Before inserting a raster image:

```powershell
python scripts/prepare_raster_asset.py source.png output/asset `
  --profile lightweight --role illustration `
  --placed-width-in 6.8 --placed-height-in 4.5 `
  --report output/asset-report.json
```

Use the final placed box at 96 dpi as the baseline. Lightweight assets normally retain about 1.75 times the linear pixel resolution. Do not preserve original dimensions unconditionally. A full-slide raster rarely needs a long edge above 1600–1920 pixels; a half-slide illustration rarely needs more than 1200–1600. When an image is heavily cropped, size for the crop coverage rather than the full source.

Format routing:

- Photos, complex opaque AI images, and full-slide backgrounds: JPEG, default quality 86. Increase quality only for a critical gradient or hero asset.
- Transparent illustrations: PNG, preferring 256-color quantization for lightweight delivery. Compare final renders for skin tones, gradients, translucent shadows, and soft edges; keep true-color PNG only for affected assets when banding or jagged edges appear.
- System screenshots, small UI text, QR codes, and line art: PNG. Do not use lossy JPEG or palette conversion that harms text or code recognition. Crop to the relevant region and keep roughly two times the placed resolution.
- Icons, simple diagrams, processes, tables, and charts: prefer SVG, DrawingML, or native objects rather than large PNGs.

## Non-image size

- Do not embed preferred fonts or entire families by default. Task-level font availability and final reopen probes establish correct rendering. Embed fonts only when the user explicitly requires offline packaging and the license permits it.
- Remove unused or duplicate images, audio, video, OLE objects, spreadsheet attachments, hidden media, external-link caches, and redundant previews.
- Reuse identical media content rather than generating a pixel-identical copy for every slide.
- Retain only data required for native chart editability. An embedded workbook directly referenced by a chart relationship is native chart structure; unrelated worksheets, workbooks, OLE objects, and source-data caches must be removed.
- Retain only structures required by the selected theme or master. Do not copy unrelated themes, layouts, or masters, and never break inheritance merely to save space.

## Size audit

After final write:

```powershell
python scripts/audit_pptx_size.py final.pptx `
  --profile lightweight --report ppt-size-audit.json
```

If the audit finds only exact duplicate media:

```powershell
python scripts/deduplicate_pptx_media.py final.pptx final-deduplicated.pptx
```

Treat the deduplicated file as a new final PPTX and rerun every render, glyph, target-application compatibility, and size check. Do not reuse reports from the previous file.

For an ordinary 10–15 slide deck, 1–2 MB is a preferred target. Image-heavy, screenshot-heavy, or necessary transparent-illustration decks may exceed it, but item-level efficiency checks still apply. Total size is a soft budget; these remain repair conditions:

- exact duplicate media;
- unused media with no relationship reference;
- fonts, audio/video, or attachments embedded without user request;
- raster resolution far above the largest placed box;
- large opaque PNGs that can safely be JPEG; and
- large media retained only in hidden slides, off-canvas objects, or source caches.

After optimization, reopen and render the final PPTX. Inspect text, transparency edges, skin tones, gradients, screenshot text, QR codes, slide numbers, and masters. Reduced size never overrides a rendering or compatibility failure.
