# 一等公民 Index 门禁

Index 是执行依赖，不是背景阅读。在个人模式下，不能凭“已参考资料库”“计划与渲染一致”之类陈述批准任何阶段。

## 版本首次学习与任务级复用

Logic 开始前，把以下工作纳入资源盘点，并把每个来源写入 `ppt-resource-inventory.json`：

1. 校验 `runtime/personal-extension.json`，读取其中的 `index_execution` 政策。
2. 根据资源盘点发现的所有者资源，在任务目录生成 `io.clayz.presentation.owner-learning-sources/1.0` 清单。每个来源必须显式声明 `knowledge_kinds`，至少整体覆盖 `private-knowledge`、`template`、`standard` 和 `method`。该清单只作为运行时输入，不得打包进公开插件。
3. 通过已锁定的所有者 Library 挂载，读取各阶段标记为 `required` 的真实原文件；只读定位元数据不算完成。解析宿主提供的持久 owner-private version-learning state root，临时任务目录不能冒充持久状态。
4. 运行 `scripts/bootstrap_owner_learning.py`。若当前 Public Core 版本没有状态记录，脚本逐字节哈希全部来源，调用 `materialize_owner_index.py` 构建 `task-private-learning`，用真实 CompositeIndex 检索探针验证四类必需学习，并写出独立 `version-private-learning-audit.json` 和 Markdown 简报。审计必须列出每个来源、记录数、类型、阶段、摘要、代表性标题、索引快照、检索回执和缺失项。
5. 若当前版本已有完整状态，脚本必须验证来源集合、审计和索引哈希并直接复用，不重新学习。同版本来源字节变化是 `PRIVATE_LEARNING_SOURCE_DRIFT`，不得静默覆盖首次审计；应形成新版本或经过单独治理的迁移。
6. 将 `builtin-catalog`、已锁定的私有 Provider 和版本绑定的 `task-private-learning` 合并为一个 `CompositeIndex`。Provider 快照只排序、哈希和锁定一次，任务中途不得替换。
7. 按 `io.clayz.presentation.index-execution-evidence/1.0` 生成 `index_evidence`。`owner_materialization.learning_mode` 必须为 `first-run` 或 `reused-version-index`，并绑定 `learning_key` 和 `version_learning_audit_sha256`。把来源池加入已选资源盘点，先向用户展示学习审计与资源摘要，再在所有交接中原样携带锁。

任何必需 Library 原文件无法读取、解压、解析、计算哈希、首次物化、持久保存或复用验证时，在相应阶段前停止。不得用模型记忆、通用默认、定位清单、每次重新物化或无回执的网页检索代替。

## 逐阶段门禁

批准每个阶段前：

1. 针对该阶段向锁定的 CompositeIndex 发出检索请求。
2. 对每份检索回执登记已选和未选的注册记录及具体理由，并完成回执。
3. 个人模式必须选择任务清单为该阶段声明的全部 `task-private-learning` 来源记录。阶段要求来自已锁定证据，不得硬编码来源名称或数量。
4. 将完整回执追加到 `index_evidence.stage_receipts.<stage>`。
5. 运行当前阶段验证器。缺少选择、来源覆盖不足、使用 fallback、记录虚构、快照变化或仅写“已参考”均失败关闭。

Index 只能通过“已选择且有回执”的记录影响决策。记录 ID、来源 ID、哈希、Provider 快照、`never_copy` 边界和采用结果必须保留为可见证据。

## 实质门禁

有回执不代表内容自动合格。Copy 仍须通过跨页句法和短语变化检查；Art Direction 仍须通过内容特定首要视觉、轮廓连续重复、结构复用、主媒介多样性、量化编码和参考采用检查；Output 必须证明最终 PPTX 中存在计划要求的原生对象；Supervisor 必须针对最终 PPTX 重跑上游验证，并拒绝重复或不含页面身份的检查证据。
