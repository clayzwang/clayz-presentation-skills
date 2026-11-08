# Layout Contract

Stage 3 在现有任务级 Semantic Layout Tree 与相对布局求解器之上增加一个
已登记的语义层。它不增加第六个 Skill，也不是模板库或样式引擎。

## 分层边界

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| Theme | 中央配置中的颜色、字体与演示默认值 | 语义拓扑或合同选择 |
| Visual Variant | 已批准的密度、形状语言、motif 等表达选择 | 已登记的槽位拓扑或最终坐标 |
| Layout Contract | 中性的角色、槽位、关系、相对权重与选择元数据 | 文案、资产、主题、变体或坐标 |
| Layout Tree | 把已批准 Semantic Layout Tree 的节点 ID 与 `copy_id` 绑定为任务级相对行、列、网格和叶节点 | 主题样式或渲染器对象 |
| Resolved coordinates | 由现有求解器确定性产出的区域坐标 | 上游语义或视觉决策 |

编译器不接受 Theme 或 Visual Variant 字段。输出将两者标记为
`external-not-consumed`，记录被选合同与检索回执，并把坐标保留为
`pending`；只有坐标求解器物化最后一层。

## 选择与编译

1. Art Direction 使用已批准的页面角色、语义关系、用途标签、locale 与
   rights context 生成 `layout-contract-request`。
2. Index 只返回带 Provider、版本、权利和哈希证据的已登记、人工准入候选。
3. 只有唯一合格候选可以自动选择；多个候选必须显式给出首选 ID。首选 ID
   若未出现在回执中，选择动作直接拒绝。
4. 任务级实例把已批准 Semantic Layout Tree 节点 ID 和 `copy_id` 绑定到合同的
   命名槽位。
5. 编译器核验回执选择、登记记录、载荷路径、SHA-256、槽位基数、内容类型和
   一次性绑定，然后输出相对 Layout Tree。
6. Output 再把 Layout Tree 求解为坐标并创建可编辑对象；它不得重新选择合同或
   改写语义拓扑。

没有合格的已登记合同时，resolution 必须为 `unresolved`，fallback action 为
`use-core-semantic-layout-tree-without-claiming-a-contract`。系统不会凭空生成合同、
布局树、Theme 或 Visual Variant。

## 公开边界

`catalog/layout-contracts/` 只包含原创 JSON 语义拓扑。机器校验会拒绝未登记或
哈希漂移的文件，并禁止演示模板、master、theme、brand kit、logo、字体文件、
私有数据和模型权重进入该目录。所有示例都只用合成 ID 和中性语义。

机器可读演示合同、视觉变体与渲染分离的概念受到
[Tahta](https://github.com/zcag/tahta/tree/7720bc9fc139e8561c282259a4a2519b0c0877bd)
启发。Clayz 的 schema、检索规则、编译器、fixture 与求解器接入均为原创；不复制
或再分发 Tahta 的代码、合同、版式、变体、组件、token、字体、示例、资产、主题、
模板或媒体。
