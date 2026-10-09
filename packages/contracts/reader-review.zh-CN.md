# 读者审读 — v0.20.1

## v0.20.2 Art cognition and audited changes

The current [Art cognition contract](art-cognition.md) extends earlier fidelity instructions: preserve original Logic/Copy, but allow Art to revise meaning, argument, sequence and pagination without advance modification requests. Record actual presentation in `art_content`, conclusions/actions and selected knowledge in `art_cognition`. Output implements that recorded presentation. Independent final reading first sees only renders, then compares original Copy and every documented Art change. Difference alone is not failure; justification, accuracy, completeness and reasoning determine the audit result. Older “unchanged Copy” or “return wording/pagination to Copy” instructions apply only when no Art projection exists. New Art work covers A01—A11; these are cognitive results, not agents or approval gates.


## 八步生产顺序

1. **Logic 研究**：明示真正的研究结论、证据、推理关系、适用范围和不确定性。过程、框架、方法论不能冒充结论。频繁重返研究记为 Logic 质量问题。
2. **Copy 文案**：完成全文讲述、页序、标题和正文，忠实保留 Logic 研究基准。
3. **标题读者**：新上下文只读标题序列及中性任务说明，先冻结理解，再对照 Logic。确实表达研究结论则推进；表达问题退回 Copy。
4. **内容读者**：另一个新上下文读完整可见文案，先冻结理解，再对照 Logic 核对信息准确、表达完整、论证逻辑一致。通过再推进，否则退回 Copy。若证据确实指出研究错误，可带证据退回 Logic 并记责。
5. **Art**：当前标题和内容审读都通过后，才开始任务相关设计、逐页规划、原型及视觉制作。不提前制作整套初稿或渲染。
6. **Output**：按批准的 Art 方案制作并渲染成品。
7. **成品读者与审计**：第三个新上下文独立阅读实际渲染，先冻结理解，再与批准 Copy 核对。失败退回 Art；属于实现偏差的，由 Art 指派 Output 局部修复。
8. **监督报告、交付**：成品关卡通过后组装报告、交付。上传不属于标准流程，仅按用户额外要求执行。

上述均为内部生产关卡，不要求用户反复确认。能力缺失如实记录，不能当成审读通过。旧版 copy/final 记录按原政策继续回读。

## 输入、冻结和对照

本合同为制作任务明确要求在宿主支持时使用真实的新上下文读者委派，不继承制作历史，例如 `fork_turns="none"`。三个读者的上下文必须不同。角色名称、Python 子进程、自报模型名称不能证明独立。

使用 `scripts/reader_review.py prepare --phase title|content|final --package COPY --brief BRIEF --directory INPUT --output PACKET`。成品还需实际 `--pptx`、`--renders`；缺失时如实记录。只向读者提供 INPUT 目录，清单、研究、作者说明、设计理由和历史反馈不进入首读。中性 brief 仅有 audience、purpose、task，不提示预期答案。成品图片清除元数据并保留原始像素。

保存真实宿主调度回执，披露 context_id、production_context_id、history_inherited、access_scope、input_files、raw_receipt。instruction-only 不等于文件系统隔离。禁止捏造回执和审读；无法执行记 not-run，同上下文记 same-context-limited，均不构成新流程通过。

首读保存 assessment、title_reading、understanding（问题、回答、页码、可见依据、不确定性）、findings（发现 ID、页码、copy_id、问题、读者影响）。先 `record-first` 冻结，再看制作证据；结构校验不代替业务判断。

`reconcile` 必须绑定首读、evidence、dispositions，并为新流程提供 `--comparison`。comparison 字段为 baseline（真实 path/sha256/bytes，且在 evidence 中）、checks、verdict、explanation。标题 checks 为 research_conclusions；内容及成品为 accuracy、completeness、reasoning，逐项填写有依据的实际核对意见。标题与内容 baseline 是原始 logic-approved 包，研究必须与 Copy 一致；成品 baseline 是 copy-approved 文案。verdict 为 pass、return-copy、return-art、return-logic。没有发现也必须实际核对。

每条首读发现保留一条 disposition：finding_id、owner_layer、status（open 或 disputed-with-evidence）、explanation、evidence_refs。修复后须新审读并用 --previous-review 关联历史，不把旧发现改写成新通过。

## 交接和最小返工

Art 前运行 `check-art-gate --package COPY --title-review TITLE --content-review CONTENT`；`stage_documents.py record-planning` 与 `lock-design` 同样传两份 review，默认配置硬校验。Copy 阶段记录绑定 config、package、reader-review-title、reader-review-content，校准再次核对。内容输入包创建时间须晚于标题核对。最终审计再绑定 reader-review-final，新流程三关通过才交付。

不可变字节证据照旧保留。标题复用核对标题顺序、任务绑定及完整 Logic 研究/brief；内容复用还核对全部可见文字。仅正文变化可复用标题审读；标题或研究变化触发相应重读；仅元数据变化可重绑记录。PPTX 字节变化必须重做成品审读，不能用文字未变推断像素未变。

同输入重试 record-stage、record-calibration、record-audit、record-first、reconcile，核验绑定文件后返回原记录和原时间；输入变化须新版本，禁止覆盖或修改时间伪造顺序。审计完整校验后才写文件。错误的模型披露枚举、证据引用、角色、覆盖列表在本次交接就返回错误。

运行 `repair-scope --before OLD --after NEW --artifact copy|report|audit-record|receipt` 获取最小恢复路线。报告/回执格式错误只修记录并重校验组装，不重做 PPT、不重复真实 Office 执行。内容变化才重做受影响读者及后续制作；成品视觉问题由 Art 判断局部修复。

标准角色：Logic/Copy 用 package；Art 用 plan；Output 用 qa、inventory、pptx；Supervisor 用 draft、pptx、auditor。已知别名自动规范化，缺角色当场报错。证据优先使用绑定 kind 加 sha256；支持绝对路径、工作目录相对路径和无歧义文件名，重名不覆盖。模型披露只允许 not-attested、same-model-possible、provided-by-host，解释写入 limitations。

监督报告保留所有首读、历史发现、返工路线和 Logic 退回，区分内容质量与交接格式错误。字段与命令细节见 [英文合同](reader-review.md)。
