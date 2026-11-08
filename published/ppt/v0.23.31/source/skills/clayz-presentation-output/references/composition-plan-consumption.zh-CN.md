# Composition Plan 消费边界

Output 只消费 Art Direction 已批准的 Composition Plan，不选择也不替换
Composition Pattern。必须核对 resolution 与每张 Receipt ID，确认所选 Pattern
及关联 Failure Pattern 仍已登记且哈希有效；任何在 Pattern 编译时声称产生
坐标，或消费 Theme、Visual Variant、Layout Contract、Layout Tree 的 Plan
都必须拒绝。

Output 把 Plan 的语义映射、任务约束、预期视觉效果和 Failure guard，与独立
批准的 Layout Contract 或核心 Layout Tree 共同使用。坐标只能在 Output 内
解析；必须保持可编辑对象要求，语义冲突应返回 Art Direction，不得静默改选
另一个 Pattern。

详见 `../../../docs/pattern-dataset-library.zh-CN.md`。
