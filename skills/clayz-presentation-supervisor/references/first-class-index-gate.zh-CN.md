# 一等公民 Index 门禁

Index 是执行依赖，不是背景阅读。在个人模式下，不能凭“已参考资料库”“计划与渲染一致”之类陈述批准任何阶段。

## 资源盘点中的根级物化

Logic 开始前，把以下工作纳入资源盘点，并把每个来源写入 `ppt-resource-inventory.json`：

1. 校验 `runtime/personal-extension.json`，读取其中的 `index_execution` 政策。
2. 根据资源盘点发现的所有者资源，在任务目录生成 `io.clayz.presentation.owner-learning-sources/1.0` 清单。该清单只作为运行时输入，不得打包进公开插件。
3. 通过已锁定的所有者 Library 挂载，读取本次各阶段标记为 `required` 的每个原文件；只读定位元数据不算完成。
4. 将原始字节保存在任务目录，以 `scripts/materialize_owner_index.py --manifest <任务清单>` 和逐项 `source_id=path` 绑定执行物化。脚本先计算真实哈希，再生成临时的 `task-private-learning` Index Provider。
5. 将 `builtin-catalog`、已锁定的私有 Provider 和 `task-private-learning` 合并为一个 `CompositeIndex`。Provider 快照只排序、哈希和锁定一次，任务中途不得替换。
6. 按 `io.clayz.presentation.index-execution-evidence/1.0` 生成 `index_evidence`，把物化后的 Provider 和来源池加入已选资源盘点，先向用户展示资源摘要，再在所有交接中原样携带两份锁。

任何必需 Library 原文件无法读取、解压、解析、计算哈希或物化时，在相应阶段前以 `first-class-index-unavailable` 停止。不得用模型记忆、通用默认、定位清单或无回执的网页检索代替。

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
