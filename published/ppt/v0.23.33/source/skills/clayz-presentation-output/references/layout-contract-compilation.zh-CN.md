# Layout Contract 编译

Output 只消费已经过 Art Direction 批准的 Layout Contract resolution、检索回执、
任务级槽位绑定与已编译 Layout Tree。它不选择合同，不决定 Theme 或 Visual Variant，
也不改变语义拓扑。

坐标求解前必须核验：被选记录确实在回执中，catalog 载荷路径位于
`catalog/layout-contracts/` 内，载荷 SHA-256 与记录一致，所有必需槽位符合基数，
每个 Semantic Layout Tree 节点与 `copy_id` 最多绑定一次。

先运行 `packages/layout/compile_layout_contract.py`，再用现有相对布局求解器解析输出
Layout Tree。编译 envelope 中 Theme 与 Visual Variant 保持
`external-not-consumed`；只有坐标存在后，且输入已批准时，可编辑对象创建才可应用它们。

`unresolved` 不是构建许可。应回到已批准的核心 Semantic Layout Tree 路径，不得发明
命名合同或 fallback tree。
