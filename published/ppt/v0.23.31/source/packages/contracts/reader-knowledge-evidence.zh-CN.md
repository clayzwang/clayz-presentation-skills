# 当前专业知识证据的读者投影

`reader-prepare` 仍按原 mode-reader/1.0 的 first / comparison / confirmation 顺序和原准则执行。first 不增加知识、研究报告、作者过程或评价。layout / final / audit 的 comparison 与适用 confirmation 中，`knowledge_reading_evidence` 改为派生的 `io.clayz.presentation.reader-knowledge-evidence/1.0` 文件；不再将整个作者 knowledge JSON 原封复制给比较读者。此项不修改任何 verdict、deferred、闭合、返工或发布条件。

当前支持的源格式为 `io.clayz.presentation.art-knowledge-evidence/1.0`。保留 version、recorded_at、navigation_scope 和 actual_adoption；actual_adoption 只记录当前表达问题下采用、调整或不采用专业方法的具体理由。它可以合法讨论读者的阅读路径，不能用关键词删除“读者”。历史 reader_id、verdict、revision_adoption，以及 effect_status、actual_visual_observations、visual_inspection、quality / self-evaluation 等评价分支不投影。历史原件及作者完整过程继续留在原任务和完整审计记录中。

Art 应通过 commit 的具名文件角色保存实际读取返回：`knowledge-node-return`、`knowledge-cu-return`、`knowledge-read-command`、`knowledge-manifest`。仅解析本 run 已提交且 path / sha256 / bytes 验证一致的当前快照；knowledge 内的 raw_returns / manifest 只按身份与这些具名快照匹配。不沿 original_path、source、stdout_path 或其他外部原路径补读。没有具名匹配时明确 unobserved；其他角色和历史资源不会自动成为知识输入。

节点返回白名单保留 code、kind、parent、title、principle、applicability、actions、limits、正反例、concepts、related_codes、flow_ids、source_ids、provenance 和 reading 的实际专业内容。composition-reading/1.0 的 entries.understanding 是该知识读取协议中的 CU 源正文字段，派生文件将它明确命名为 source_cu_text，并保留实际正文哈希和来源字段；CU 的 id、title、知识映射、采用方法及 corpus review_id 等知识来源元数据仍可保留。corpus review_id 是知识来源标识，不是本任务 reader_id 或判断。

CU 正文仅在提交返回明确 full_body=true、实际非空正文与 body_sha256 相符时进入 source_cu_text。只有 ID、索引、作者转述、full_body 声明或不相符哈希均不足，正文状态明确为 unobserved。`submitted-source-text-with-matching-declared-hash` 仅说明提交文本与其声明哈希一致；`original_package_text_identity=unobserved-in-projection` 明确本投影没有向包外查证原文。比较读者可以看到已有实际提交文本，不能据此声称作者设计前已读取。判断原包原文须另对该 run 绑定的真实 package/hash 及相应 CU 定义核实；原始读取回执和真实时序另行证明前置读取，不由这次投影新造。

派生文件保留 source_snapshot、各 proof 的真实 hash / bytes 及 source_package_snapshot；专业正文直接在随包 JSON 内可读，不把污染原件路径重新交给比较读者。命令返回仅保留真实 recorded_at / returncode 和来源身份；0 返回码、正文存在和采用理由都不是读取行为或专业质量通过。缺失/未知 schema、不可验证快照、缺失完整正文均显式列出 unobserved，不制造宿主返回、原文或 QA 结论。

此白名单按已定义字段语义工作，不是自由文本的语义净化器。生产者须把当前方法理由与历史评价分列；若把历史评价伪装进合法当前理由或专业正文字段，本投影不能自动识别。未知证据模式不会默认可信，应先提交可识别的实际证据并保留缺失范围。Output 的其他具名资源宽投影不在此修复范围；不声称它已形成强文件系统隔离。

manifest proof仅识别已观察的art-learning-pack/1.0；未知manifest contract也明确unobserved，不把具名角色或版本字符串当作已识别schema。
