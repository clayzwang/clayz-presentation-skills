# Logic 内容包 3.1

新任务遵循[完整故事与图片稿交接](../../../packages/contracts/story-visual-handoff.zh-CN.md)。
Logic 输出完整 story、总论点、章节、逐页主张及放置位置；Copy 决定具体文字、剪裁和内容分组；Art Direction 决定视觉表达，Output 原生实施。

根包使用 `contract_version: "3.1"`，保留 package_id、version、status、origin_namespace、brief、acceptance_contract、resource_inventory、index_evidence、approvals、configuration_sha256 及真实来源、配置、校准和工作记录绑定。Logic 批准时 copy_layer 为 null。

`story` 保存未剪裁的完整论述：title、thesis、audience、desired_outcome、opening、conclusion，以及有序 chapters。每章含 chapter_id、title、purpose、blocks；transition 可选。每段含 story_id、完整 text、claim_status、source_ids、qualifiers、must_preserve。sources 绑定 source_id、resource_id、locator，保留来源性质与证据边界。glossary、metric_dictionary、open_items、invariants 为数组，不适用时为空。事实与计算必须有来源支持。

`logic_layer.slides` 是有序页面安排，每页包含：

- slide_id、chapter_id（封尾可为 null）、narrative_role；
- claim：完整的逐页实质主张，具体上屏措辞由 Copy 决定；
- 非空 source_story_ids：说明 story 中哪些内容放在这一页；
- data：有依据的量化记录数组，无数据时为空。

全部 story 段落都要安排位置，包括后续可能被 Copy 剪裁的内容；不得为适配页数而先剪短 story。正文页数由 Logic 按任务决定；除用户明确省略，默认含一页封面、一页尾页，正文数与总页数分开。`logic_layer.lock.slide_order_locked` 为 true。可补充有用的任务语义资料，不强制分析套路或消息树。

数据保留 data_id、metric_name、display_value、raw_value（缺失时 null）、unit、period、definition_ref、source_ids、evidence_status。口径、计算和不确定性应可复核。关系只描述真实含义，不强制父子树、兄弟组、分析步骤或配额；每个独立交给 Copy 的内容单元应足以被理解。

Copy 原样保留 story 和 logic_layer，用 logic_artifact 绑定真实 Logic 文件，在 copy_layer 写文案。页数、顺序、页面职责、主张或证据变化回 Logic；措辞、剪裁和分组归 Copy。不主动生成演讲备注或附录；用户要求及历史备注仍可读取。研究工作记录不等于 PPT 演讲备注。

历史 2.4、3.0 由隔离的兼容路径读取；旧节点和推理合同不约束新的 3.1 任务，不得只改版本号伪装为新合同。
