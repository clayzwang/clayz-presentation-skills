# PPT v3.3 Copy 层合同

v0.18.0 新任务使用[研究与视觉交接](../../../packages/contracts/story-visual-handoff.zh-CN.md)。
Copy 阅读 Logic 的完整故事，可调整、重组、改写，保留事实、限定条件和真实业务关系。

`copy_layer` 保留 `logic_version`、`pagination_owner:"copy"`、
`research_sha256`、实际语义复核说明和按内容顺序组织的 `slides`。
每页包含 `slide_id` 与 `copy_units`；章节、页面职责、数据引用及原有或用户要求的备注按需保留。
不再另写一份 Logic 页面投影。

文案只分为标题 `title`（主 Storyline）、副标题 `subtitle`（次级 Storyline）、
各级标题 `heading`、正文 `body`、注释 `annotation`。
每段只有 `copy_id`、`text`、`role`，各级标题另有正整数 `heading_level`。
每类都可缺省，层级可以跳级，标题后不必有下级标题或正文，自然段落换行可以保留。

来源映射放在根级 `copy_provenance` 中，与干净文字分开；
绑定原始 Logic 文件与研究、任务、配置和证据，保留必要内容。
这些技术追溯信息不成为版式指令。

不再生成 columns/table/ladder、分组树、强制单独渲染、禁止合并、阅读序号、
视觉样式、强制换行或媒介请求。Art 可以合并可编辑对象、给同级文字不同样式、
自主安排阅读路径，仍需保留真实含义与用户明确要求。
旧合同只用于对应版本历史材料的回读。
