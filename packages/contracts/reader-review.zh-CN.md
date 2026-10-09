# 读者审读 — v0.20.0

结合[内容充分与自然表达](reader-quality.zh-CN.md)使用。Supervisor 在现有五阶段中调度两次读者审读：Copy 保存当前文字后、Copy→Art 校准前，以及 Output 完成最终渲染后。检查读者能否从可见内容解释主题核心、机制及有证据的具体差异。

## 调度与输入边界

制作材料时，本契约明确要求：宿主提供隔离审阅能力时，根协调者调用真实调度工具，将读者任务委派给**不继承对话历史**的新上下文／代理；支持时使用 `fork_turns="none"`。成品读者还须使用不同于 Copy 读者的新上下文。角色名、Python 子进程、新 JSON 或模型名称均不能证明隔离。先观察实际宿主能力，不能未经检查便声明无法隔离。

用 `scripts/reader_review.py prepare` 生成读者输入目录。只向读者传入目录内的 `reader-input.json` 和最终审读所需的编号 PNG。输入清单、完整内容包、研究、既有反馈、工作笔记、Art 理由、作者自评、讲者备注与审读历史留在 Supervisor 一侧。页面实际展示的来源和限定保留。最终审读看真实成品像素；Art 草图或抽取的正文不能代替成品。生成器按白名单抽取 Copy 可见字段并清除图片元数据，不自动证明中性说明或文案在语义上没有诱导。

读者说明仅含 `audience`、`purpose`、`task`，中性地描述原始任务与目标受众，不给作者预设答案、期待的差异或建议寻找的问题。读者先连读标题，再阅读全部可见内容，用自己的话解释核心、机制、比较及需要猜测之处，引用页码和实际文字。

宿主允许时限制读者的工具与文件访问。记录实际 `access_scope`：`host-restricted`、`instruction-only` 或 `unavailable`。仅靠指令限制输入可以减少历史上下文影响，但不能证明文件系统或网络隔离。保存真实调度工具返回的原始回执；标准化回执记录 `host_tool`、`context_id`、`production_context_id`、`history_inherited: false`、`access_scope`、准确的 `input_files`（输入 JSON 在前，图片在后）及 `raw_receipt` 文件引用。标准化不能将自我声明变为宿主证据，不得伪造回执或审阅回复。

无法新建上下文时，真实执行的同上下文审读记为 `same-context-limited` 并说明限制。无法审读时记 `not-run`、原因且不填虚构回复。同上下文记录仍交代实际上下文 ID、是否继承历史和访问范围，`host_receipt` 可以为空。缺少最终渲染时可绑定最终 PPTX 并用 `--unavailable-reason` 说明。这些情况保留 `incomplete-evidence`，依照既有交付政策处理，不新增用户审批。

## 先保存理解，再核对制作证据

首次回复包括：

- `assessment`：`understood`、`understanding-gaps` 或 `insufficient-input`，由实际专业审读判断。
- `title_reading`：连读标题后，读到了什么、还不明白什么。
- `understanding`：每项含 `question`、`answer`、`slide_ids`、`visible_evidence`、`uncertainty`。问题从中性任务与页面产生，不能照抄作者隐藏提纲。
- `findings`：每项含 `finding_id`、`slide_ids`、`copy_ids`（只看图片时可为空）、`statement`、`reader_impact`。

先用 `record-first` 保存实际回复及上下文，形成新建且不覆盖的文件。之后第二轮才读取完整 Logic、Copy、Art、来源与 QA，将理解缺口定位到最早责任层：缺少答案或差异缺乏证据交 Logic，空泛或编写者视角的表达交 Copy，批准图稿的分组／注意力问题交 Art，成品偏离图稿交 Output。必要时另记 Supervisor 漏检。读者有疑惑本身不证明业务事实有误。

`reconcile` 绑定首次审读和第二轮证据，每个原始 finding 必须有一项处置，含 `finding_id`、`owner_layer`、`status`（`open` 或 `disputed-with-evidence`）、`explanation`、`evidence_refs`。证据引用必须来自绑定的第二轮材料。可以依据证据解释分歧，但保留读者原来的理解。修复交还责任阶段，修改后在新上下文重读；通过 `--previous-review` 保留旧记录，在现有工作笔记和校准中记录修改及结果。旧审读不能冒充覆盖新版本，不能在 Output 后倒填 Copy→Art 前的审读。没有问题时不强制改稿。

## 命令与交接

```bash
python scripts/reader_review.py prepare --phase copy --package /task/copy.json --brief /task/reader-brief.json --directory /task/reader-copy-input --output /task/reader-copy-packet.json
# 此时调用真实宿主工具，仅传 reader-copy-input，不继承历史。
python scripts/reader_review.py record-first --packet /task/reader-copy-packet.json --context /task/reader-copy-context.json --response /task/reader-copy-response.json --output /task/reader-copy-first.json
python scripts/reader_review.py reconcile --first-read /task/reader-copy-first.json --dispositions /task/reader-copy-dispositions.json --evidence /task/logic.json --evidence /task/copy.json --output /task/reader-copy-review.json
```

上下文 JSON 字段为 `execution_mode`、`context_id`、`production_context_id`、`history_inherited`、`host_receipt`（文件引用或空）、`access_scope`、`limitations`（文字数组）。新上下文模式为 `separate-context`、`same-model-new-context`、`separate-process`，需要匹配的实际宿主回执。未执行时省略 `--response`，填写 `--reason`。

最终准备使用 `--phase final --pptx /task/final.pptx --renders /task/render-manifest.json`。渲染清单包含 `pptx_sha256` 和按页序排列的 `slides`；每页记录 `slide_id`、`path`、`sha256`、`bytes`。只能转换真实渲染记录，不能生成虚构回执。输入生成器检查页序覆盖与像素一致性，渲染来源真实性仍依赖 Output 的实际证据。

沿用 Independent Auditor 的 `source_records`：增加 `reader-review-copy` 和 `reader-review-final` 两种来源，分别绑定两份协调后的审读记录；`--expected-source-kind` 同时列入这两项、package、plan、qa、inventory 和所有实际来源。新配置要求这两份记录，也允许真实的未执行记录。历史任务按原配置回读。正式报告在同一审计中保留首次复述、上下文、输入包、处置和旧记录引用，并分别显示制作保真与读者审读结果。

校验器检查输入投影、字节／任务／版本绑定、时序、声明的调度证据及发现保留。它不能认证真人理解效果、模型身份、宿主声明真实性或文案质量。
