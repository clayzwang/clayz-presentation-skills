# 执行账本与有限反思

当任务涉及多个工具、渲染尝试、修复轮次或不同环境时，使用本路由。它把 [PPTAgent](https://github.com/icip-cas/PPTAgent) 与 [DeepPresenter](https://arxiv.org/abs/2602.22839) 的执行历史和环境反思思想落成通用账本，但不复制其编排代码、提示词、模型或工具。

## 先记事实，再做解释

使用 `scripts/execution_ledger.py` 记录阶段、工具、有限轮次、状态、稳定错误码、输入输出文件哈希、渲染/检查证据和简短环境消息。不要记录隐藏思维链、推测动机或未经核实的成功。账本是审计轨迹，不是模型聊天记录，也不是新的批准源。

```bash
python scripts/execution_ledger.py init run-ledger.json --run-id RUN-001 --config config/default.json
python scripts/execution_ledger.py record run-ledger.json --cycle 1 --stage output \
  --tool pptxgenjs --status failed --input render-manifest.json \
  --error-code PPTX_WRITE_FAILED --message "Renderer returned a non-zero exit status"
python scripts/execution_ledger.py close run-ledger.json --final-status incomplete
```

## 反思路由

- 事实、主张、页序或证据问题回 Logic；
- 锁定措辞、长度、语法或术语问题回 Copy；
- 构图、面积、媒介、语义树或阅读顺序回 Art Direction；
- 坐标、对象 API、媒体、字体、兼容性或文件修复归 Output；
- 缺少能力、依赖、权限或渲染器归环境/用户。

Supervisor 只报告冲突与路由，不创作新构图、不替用户批准，也不重复执行直到偶然出现好结果。

当技术检查通过、达到轮次上限、同一错误无新增证据地重复、必须修改上游基准或缺少必需能力时停止。应如实关闭为 `known-risk` 或 `incomplete`，不能掩盖缺口。自动分数只作诊断，最终 PPTX 与真实渲染证据优先。
