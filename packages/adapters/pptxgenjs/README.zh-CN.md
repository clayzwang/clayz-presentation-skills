# 实验性 PptxGenJS 适配器——默认禁用

这是 Clayz 原创的轻量 API 映射：把 `io.clayz.presentation.render-manifest/1.0` JSON 转换成可编辑 PowerPoint 对象，并参考公开的 [PptxGenJS 4.0.1 API](https://gitbrent.github.io/PptxGenJS/)。仓库不捆绑其源码、依赖锁、演示文件、模板或媒体。

## 安全状态

中央配置已将本路线**默认禁用**：PptxGenJS 4.0.1 当前间接依赖 `image-size`，GitHub 已登记两个尚无修复版本的高危拒绝服务公告：[GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) 与 [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq)。截至 v0.2.0 审查日，没有可安装的修复版。

因此 CI 不安装或执行该依赖，适配器同时阻断图片与 SVG 路线。不得把它用于不可信或生产输入；待上游出现可审计修复版本后再重新评估。当前源码只作为原创 API 映射与语法检查通过的实验参考。

文字、形状、线条、表格和标准图表保留映射；对象 ID 会写入可编辑对象名。人工本地实验还必须显式提供 `--acknowledge-upstream-risk` 并自行另行获取依赖；这不构成安装当前脆弱依赖的建议。

成功写出 PPTX 不等于通过质量检查。仍须在配置的目标应用中重开、逐页渲染，并检查对象、中文字符、Output QA 与 Supervisor 审计。该适配器不会导入或重建参考稿母版。

未来若安全重新启用，可单独执行 `scripts/stamp_pptx_metadata.py` 写入已公开说明且可移除的 Clayz 品牌元数据。适配器本身不会注入隐藏页、不可见形状、追踪 ID、网络回传或不可移除水印。
