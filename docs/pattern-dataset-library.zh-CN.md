# Pattern 与 Dataset Library

Stage 4 增加受治理、可面向未来 Dataset 的元数据合同，但不会把公开仓库
变成模板库、案例库或模型库。每条可选记录都必须拥有稳定 ID、人工准入的
Index 记录、哈希绑定的 JSON、明确权利边界，并且只有出现在 Retrieval
Receipt 中才能被选择。

## 四类记录合同

| 记录 | 回答什么 | 明确不包含什么 |
| --- | --- | --- |
| Composition Pattern | 已批准的语义关系怎样映射为空间关系 | 坐标、Theme、Variant、模板或资产 |
| Failure Pattern | 哪些渲染证据构成失败、最早可由谁预防、如何验证修复 | 自动审美真值或 Supervisor 自有修复权 |
| Reference Record | 页面职责、第一视觉、关系、密度、媒介、系列角色及受治理链接的 Dataset-ready 元数据 | 原文、媒体、坐标、字体或模型特征 |
| Sequence Record | 跨已登记 Reference 的持续元素、渐进变化、允许变化和退出原因 | 幻灯片、截图、母版或源演示文件 |

首批公开记录全部是 Clayz 原创方法与完全合成元数据，只用于证明合同，
不声称任何 Pattern 是普适审美答案。

## Receipt 绑定的 Pattern 决策

Art Direction 从已批准的任务模式、页面职责、语义关系、目的标签、语言、
约束与预期视觉效果构造请求。`packages/patterns/compile_composition_pattern.py`
依次执行：

1. 检索已登记的 Composition Pattern；
2. 只有剩下唯一一个可物化候选时才允许自动选择，或接受 Receipt 中实际
   出现的显式 preferred ID；
3. 把所选 Pattern 关联的全部 Failure Pattern 检索进第二张 Receipt；
4. 只有 Pattern 与全部 Failure Pattern 都已登记、人工准入、哈希有效、
   权利允许且已被 Receipt 选择时，才输出不含坐标的 Composition Plan。

无匹配、preferred ID 未召回、多义、关联 Failure 缺失或哈希漂移都会得到
`unresolved` 或验证错误。Fallback 是继续使用 Art Direction 核心方法，
但不得声称选择了某个具名 Pattern，也不会凭空发明替代记录。

## 分层边界

Composition Plan 保存所选 Pattern、任务约束、预期视觉效果、被拒绝候选、
语义到空间的映射以及 Receipt 绑定的 Failure guard。它不读取也不输出
Theme、Visual Variant、Layout Contract、Layout Tree 或 resolved coordinates。

Art Direction 负责选择 Pattern 与视觉判断；Output 只消费已批准的 Plan，
不得重新选择方法。Supervisor 只能用已登记 Failure Pattern 诊断渲染证据，
并把修复返回最早责任 Stage；它不拥有修复，也不自动晋升知识。

## Metadata-only Dataset 导出

`packages/patterns/export_metadata_dataset.py` 只导出四类 Stage 4 记录中已登记、
人工准入且可公开的元数据。导出保留稳定 ID、来源修订与哈希、分类及已验证
元数据，并显式排除资产字节、源原文、坐标、字体、模型权重、生成物自动准入
和自动审美真值。

它只是未来互操作接口，不是随仓库发布的训练集或训练管线；不会下载上游
Dataset、嵌入视觉特征，也不会把生成结果变成参考真值。

## 合成示例

```bash
python packages/patterns/compile_composition_pattern.py \
  examples/synthetic-pattern-library/comparison-request.json \
  --resolution-output /tmp/pattern-resolution.json \
  --receipt-dir /tmp/pattern-receipts \
  --plan-output /tmp/composition-plan.json

python packages/patterns/export_metadata_dataset.py \
  /tmp/clayz-metadata-dataset.json
```

公开 Catalog 只允许 JSON 方法元数据。CI 会拒绝演示文件、母版、Theme、
图片、字体、表格型 Dataset、模型权重、未登记 Payload、陈旧哈希、孤儿链接
和品牌专用记录。
