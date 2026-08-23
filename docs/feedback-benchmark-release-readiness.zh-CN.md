# 反馈、Benchmark、迁移与发布就绪

Stage 5 在不改变五阶段权责的前提下闭合 v0.4.0 开发循环；只有另一次独立、明确的人工授权被记录后，发布门禁才会打开。

## 人工准入反馈闭环

Logic、Copy、Art Direction 与 Output 可以追加带证据的观察。Supervisor 只能把候选退回其中一个责任层，不建立第五个学习库。来源记录始终保持 `promotion_status=observation`。

`packages/feedback/learning.py` 只会把拥有独立人工准入、且规范 SHA-256 完全一致的记录编入 provider。缺少准入、内容变化、决定格式错误或身份重复都会被拒绝或报告。准入后的 learning 仍然是 `local-private`、`local-only`，且 `public_catalog_eligible=false`。

## Retrieval Benchmark

合成 Benchmark 固定两个 Provider 快照和四个用例：已登记 Composition Pattern、已登记 Failure Pattern、一条哈希绑定且人工准入的私有 Learning，以及一个必须保持空结果和 `unresolved` 的未登记请求。

Provider 漂移、缺少预期候选、返回禁止候选、unresolved 用例非空或出现虚构 ID 都会使运行失败。运行层绝不自动改写预期基线。

## 旧索引迁移

`scripts/migrate_knowledge_index.py` 把旧的文件系统登记表转换为通用 Index Record 合同。只有内容未变化且有人类准入的资产与 Learning 才能迁移；私有范围必须保留，孤立邻居会被删除并报告，每个跳过对象都保留原因。

仓库 Fixture 完全合成：三项资产和两条 Learning 最终迁移一条知识记录与一条学习记录；一项哈希陈旧资产和两个未准入对象被跳过。

## 发布就绪仍需独立授权

`release/v0.4.0-readiness.json` 记录五个开发阶段已有证据。用户在 2026-08-23 明确作出发布决定后，状态从 `draft-review` 转为 `release-authorized`，绑定 `VERSION=0.4.0`，并授权 merge、不可变 Tag、GitHub 发布和 Experience Center 当前版本标记。正式发布工作流仍须先通过完整仓库验证。

```bash
python scripts/validate_feedback_benchmark.py
python scripts/validate_all.py
```

Stage 5 Fixture 只包含原创方法元数据和合成文本，不包含模板、母版、Brand Kit、Logo、字体、企业数据、源媒体、数据集、模型特征或模型权重。
