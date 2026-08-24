# Node.js chart-engine case · v0.5.0

This Experience Center material reproduces the chart assets used in the two-slide “Global oil and demography” PowerPoint:

1. an Apache ECharts Sankey comparing 2024 oil-production and oil-consumption structures; and
2. a 100% radial stacked bar comparing three population age bands across representative countries.

## Rebuild the chart assets

Requirements: Node.js 20 or later.

```bash
npm install
npm run build
```

The script writes SVG and 2× PNG assets to `generated/`. Data inputs are stored in `data/`, and source/method notes are in `source-notes.txt`.

The [editable two-slide PPTX](../../assets/decks/nodejs-chart-engine-global-oil-demography-v0.5.0.pptx) and [web previews](../../assets/cases/nodejs-chart-engine-v0.5.0/) are published as public output evidence. They are isolated from Clayz's reference and knowledge corpora.

## Integration boundary

This example adds a public Node.js chart-asset route: ECharts renders server-side SVG, and sharp rasterizes the chart for PowerPoint-safe placement. The final slide composition and QA remain inside the Clayz workflow. This release does **not** enable the security-blocked experimental PptxGenJS adapter.

Apache ECharts 6.1.0 and sharp 0.35.3 are Apache-2.0 dependencies. They are installed by the user and are not vendored in this repository.

## 中文说明

该案例公开两页材料的可复用 Node.js 图表链路：Apache ECharts 以 SSR 方式生成 SVG，sharp 再输出适合 PowerPoint 的高清 PNG。第一页是全球石油生产与消费结构桑基图，第二页是三层径向 100% 堆叠年龄结构图。

代码、数据、来源说明、两张图表资产、网页预览和可编辑 PPTX 均在 Experience Center 范围内隔离保存，不进入 Clayz 的参考库或知识库；v0.5.0 也没有启用仍处于安全阻断状态的 PptxGenJS 实验适配器。
