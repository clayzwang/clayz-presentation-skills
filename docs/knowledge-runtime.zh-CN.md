# 可移植知识运行层

v0.2.0 让空知识架构真正可运行，但不附带任何人的审美偏好、真实案例或公司资产。除非显式传入其他配置，所有运行路径和检索上限都从 `config/default.json` 解析。

## 边界

- 来源按文件类型保存在 `knowledge/sources/`。
- 登记只记录身份、哈希、来源、许可、语言、用途和邻居，不代表质量批准。
- 人工准入是独立且显式的动作，必须提供 `--confirm-human-decision`。
- 只有同时存在准入记录且文件哈希未变化的来源才进入索引。
- 文本类文件使用本地词法索引；PPTX、PDF 与图片不会被静默解析，除非宿主提供经过授权的解析器。
- 检索分数只负责召回候选，不能晋升质量、替代判断或改变当前任务的批准基准。
- 学习回写始终以 `promotion_status=observation` 开始。

## 常用命令

```bash
python scripts/knowledge_cli.py register knowledge/sources/documents/example.md \
  --source-uri https://example.org/source --license CC-BY-4.0 \
  --language zh-CN --purpose-tag narrative-structure

python scripts/knowledge_cli.py admit asset <asset-id> \
  --admitted-by maintainer --use-for narrative-structure \
  --never-copy wording --confirm-human-decision

python scripts/knowledge_cli.py build-index
python scripts/knowledge_cli.py search "先证据后建议" --purpose narrative-structure
```

学习记录只能作为待判断观察：

```bash
python scripts/knowledge_cli.py record-learning art-direction \
  --task-purpose comparison-page \
  --observation "本地化后标签在渲染中发生碰撞。" \
  --evidence-ref output/rendered/3.png \
  --decision "把容量冲突交还 Art Direction。"
```

宿主可以更换为向量检索、映射到 ChatGPT Library 或增加 PDF/PPTX 解析器，但必须保留稳定 ID、来源/许可、人工准入、`never_copy`、哈希和禁止自动晋升的约束，并如实报告读写失败。
