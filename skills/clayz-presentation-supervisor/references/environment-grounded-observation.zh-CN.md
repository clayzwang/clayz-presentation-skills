# 环境落地观察与修复历史审计

本路由受 [PPTAgent](https://github.com/icip-cas/PPTAgent) 与 [DeepPresenter](https://arxiv.org/abs/2602.22839) 的执行历史、错误反馈、页面检查和内容／设计／连贯性分面观察启发，但保持 Supervisor 的独立性：只诊断，不修改，不把自动分数当真值。引用性质与再分发边界见仓库 `provenance/manifest.yaml`。

## 证据顺序

1. 批准的 `ppt-design-package.json` 与 `ppt-art-direction-plan.json`；
2. `ppt-build-deviation-log.json` 中的源哈希、观察循环、受控动作、失败和挑战；
3. 写盘后的PPTX对象、最终重开渲染、字体、配置目标应用、体积和兼容性机器事实；
4. Output QA自评；
5. 自动分数与外部案例对照。

第5项只可发现值得复核的异常，不得覆盖前四项。任何“工具成功”“HTML校验通过”“对象存在”或单一预览器正常，都不能替代最终PPTX重开后的真实画面。

## 环境事实必须进入最终审计

Supervisor 必须把 `runtime-preflight.json` 的扫描 ID、原始文件 SHA-256、脚本签发的运行 ID、任务请求 SHA-256、nonce、任务根 SHA-256、签发/过期时间、challenge SHA-256、规范签发与消费台账 SHA-256、resolved config SHA-256、锁定路线、全部路线必需能力的已满足/声明但未验证/缺失结果，以及每个目标应用的可用/不可用状态写入 `ppt-supervision-report.json.environment_observation`。两份台账必须存在于绑定任务根下的规范路径，且实际字节哈希必须与预检一致。任何“可用”的宿主能力还必须保留同一 run/task/challenge 绑定、实测来源、观察时间，以及指向经哈希校验 inventory 文件的结构化回执；普通 JSON 声明不得被改写成 `verified: true`，最多只能让原生路线成为 provisional/attemptable，不能成为 ready。仅保存文件名、未绑定的能力声明、通用占位审计记录或对话中口头说明都不算完整记录。

目标应用验收不是 Logic 前闸门；无论应用存在还是缺失，都必须扫描配置中的每一项。PowerPoint、WPS 或 LibreOffice 原生重开能力不可用时，记录 `deferred`；能力可用但本轮未选择时记录 `not-selected`；实际执行后记录 `pass` 或 `fail`。所有项目都必须有证据引用，且 `authoring_gate=false`。只有制作、写盘、检查或渲染路线本身无法满足配置硬条件时，才可在预检阶段阻止制作。

当存在 `deferred` 或 `not-selected` 且没有其他问题时，根状态使用 `complete-with-deferred-acceptance`，PPTX 与审计报告仍可成对交付，但报告不得宣称未执行应用已通过兼容认证。原生路线即使 Output 成功，也必须在预检段继续标为 provisional；交付之所以可变为 ready，只能因为发布器独立验证了写盘 PPTX、对象清单、QA 证据和最终渲染。只有 `scripts/publish_supervised_pair.py` 复核上述绑定，并在一个全新目录中物化 PPTX、报告和 `delivery-manifest.json` 后，最终交付才成立。

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
