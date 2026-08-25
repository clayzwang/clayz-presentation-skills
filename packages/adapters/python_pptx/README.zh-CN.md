# python-pptx 基础适配器

此适配器使用公开的 `python-pptx` API，把 Clayz 的 render-manifest 合同映射为可编辑 PowerPoint 对象，是 v0.5.1 不依赖宿主模型私有工具的基础作者路线。

它支持文本、常见形状、线条、位图、表格和常见分类图表。SVG 需要明确可用的转换器或另一条已锁定路线。最终视觉 QA 仍需要 PowerPoint 或 LibreOffice；仅写出文件不等于完成交付。

```bash
python packages/adapters/python_pptx/render.py manifest.json output.pptx
```
