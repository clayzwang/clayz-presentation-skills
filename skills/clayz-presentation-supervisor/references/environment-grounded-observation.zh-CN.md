# 环境落地观察与修复历史审计

本路由受 [PPTAgent](https://github.com/icip-cas/PPTAgent) 与 [DeepPresenter](https://arxiv.org/abs/2602.22839) 的执行历史、错误反馈、页面检查和内容／设计／连贯性分面观察启发，但保持 Supervisor 的独立性：只诊断，不修改，不把自动分数当真值。引用性质与再分发边界见仓库 `provenance/manifest.yaml`。

## 证据顺序

1. 批准的 `ppt-design-package.json` 与 `ppt-art-direction-plan.json`；
2. `ppt-build-deviation-log.json` 中的源哈希、观察循环、受控动作、失败和挑战；
3. 写盘后的PPTX对象、最终重开渲染、字体、配置目标应用、体积和兼容性机器事实；
4. Output QA自评；
5. 自动分数与外部案例对照。

第5项只可发现值得复核的异常，不得覆盖前四项。任何“工具成功”“HTML校验通过”“对象存在”或单一预览器正常，都不能替代最终PPTX重开后的真实画面。

## 审计问题

- 每次修复是否绑定受影响页面和稳定目标ID，而不是无目标整稿重写；
- 动作是否只属于受控技术词表，且没有改批准文案或艺术指导；
- 失败与部分成功是否保留错误证据，并形成下一轮定点修复或上游挑战；
- 修复后是否重开写盘文件、重渲染受影响页，最终是否整稿重渲染；
- 运行日志声称“不改变艺术指导”时，最终渲染是否真的保持第一视觉、面积、媒介、系列与语义留白；
- Output QA是否先看环境事实，再给结论，而非复述自身操作历史。

## 建议finding code

- `BUILD_OBSERVATION_EVIDENCE_MISSING`：缺少环境落地观察或最终重开证据；
- `BUILD_ACTION_SCOPE_OVERREACH`：技术动作越过目标对象或静默改变批准基准；
- `REPAIR_WITHOUT_RENDER_EVIDENCE`：修复后未用写盘重开渲染确认；
- `BUILD_ERROR_HISTORY_DROPPED`：失败或部分成功未进入运行日志；
- `QA_SCORE_TREATED_AS_TRUTH`：自动评分覆盖合同、对象或真实渲染。

这些finding code是诊断标签，不是自动拒绝推进的依据。问题仍按严重度、证据、影响、责任层和用户裁决处理。
