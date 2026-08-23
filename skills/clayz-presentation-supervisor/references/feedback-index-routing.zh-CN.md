# 反馈索引路由

Supervisor 负责诊断和路由证据，不拥有反馈存储，也不负责判断某条观察已经成为可复用真值。

1. 把每条 learning candidate 退回最早责任层：Logic、Copy、Art Direction 或 Output。
2. 来源记录必须保持 `promotion_status=observation`。
3. 另一次独立人工准入必须绑定候选的规范 SHA-256、获准用途、`never_copy` 边界和晋升目标。
4. 准入后，责任运行层才可重建私有 learning provider。记录发生变化、缺少准入或准入格式错误时必须跳过并报告。
5. `public-open-source` 检索必须排除这些私有学习记录。把它们放入 built-in catalog 属于另一次独立的来源审阅和发布决策。
6. Retrieval Benchmark 快照只是审阅证据，不是自适应记忆。Supervisor 可以报告漂移，但不得自动更新基线。

没有已准入记录匹配时，保留 `unresolved`，或采用责任层核心合同已经允许的 fallback。不得为填补空缺而虚构 Learning、Failure Pattern、Layout Contract 或 Composition Pattern。
