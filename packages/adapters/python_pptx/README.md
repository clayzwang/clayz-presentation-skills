# Python-pptx baseline adapter

This adapter maps the public Clayz render-manifest contract to editable PowerPoint objects with the public `python-pptx` API. It is the host-model-independent baseline authoring route in v0.5.1.

It supports text, common shapes, lines, raster images, tables, and common category charts. SVG requires an explicitly available converter or a different locked route. Final visual QA still requires PowerPoint or LibreOffice; successful file creation alone is not delivery evidence.

```bash
python packages/adapters/python_pptx/render.py manifest.json output.pptx
```
