# 索引原生检索基础层

v0.4.0 的开发从一件事开始：把检索从“可选的文件搜索”升级为受治理的运行层。本阶段不改变五阶段权责，也不发布新版本。

## 索引负责什么

索引运行层负责稳定记录ID、Provider快照、硬过滤、词法排序、邻居展开、权利判断和检索回执。它不负责业务判断、视觉判断、文案批准或最终渲染。

每个候选都必须保留 `provider_id`、来源版本、许可、`never_copy`、可否物化及命中依据。各阶段可以采用或拒绝候选，但不能选取回执中不存在的记录ID。

## Provider 模型

第一版合同支持多个彼此独立的 Provider：

- `builtin-catalog`：项目维护、可以安全随开源仓库分发的合同和原创方法；
- `filesystem-library`：用户拥有的本地或 NAS 知识；
- `host-library`：宿主的 Library 或企业知识服务；
- `external-ephemeral`：当前任务临时搜索得到的元数据，不自动持久化。

Provider 身份不能被抹平。即使标题相同，不同 Provider 的记录仍保留独立的权利、版本和来源。

## 知识幻觉边界

运行层不会编造兜底记录。没有任何已登记且合规的记录命中时，回执必须明确写出：

```json
{
  "fallback": {
    "used": false,
    "reason": "no-eligible-registered-record"
  },
  "hallucination_guard": {
    "only_registered_records": true,
    "invented_record_count": 0
  }
}
```

后续阶段可以在没有参考的情况下继续、把冲突交回上游，或执行明确标记的外部搜索；但不能假装某个不存在的版式、来源或模板已经被找到。

## 公开品牌资产防护

私有 Library 可以保存由所有者授权、仅供本地使用的品牌资产；成功检索绝不等于可以公开。

公开内置目录只保存元数据和方法。机器校验禁止在 `catalog/` 中放入演示模板、母版、主题和字体二进制。品牌专属模板、母版、字体或品牌包，只有在“允许再分发”和“允许物化”均有明确许可且经过人工准入时，才可能被标为公开目录可用。

这是一条公司中立的规则：它保护所有企业模板，阻止任何私有企业视觉身份混入开源模型、示例或回归材料。

## 合同和入口

- `packages/contracts/index-record.schema.json`
- `packages/contracts/retrieval-request.schema.json`
- `packages/contracts/retrieval-receipt.schema.json`
- 运行实现：`packages/index_runtime/`
- CLI：`scripts/index_runtime_cli.py`

## 当前状态

这是未发布的基础阶段，`VERSION` 保持不变。v0.4.0 后续阶段会在同一套回执上继续接入能力路由、Layout Contract、构图/失败模式、学习晋升和检索 Benchmark。
