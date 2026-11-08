# 当前阶段 process.events 记录格式

Logic / Copy / Art / Output 通过当前 commit 提交的 process 文件，顶层必须为含非空 `events` 数组的 JSON 对象。每项须有非空字符串 action、record；artifacts 为实际文件引用数组，单项只含 path、sha256、bytes，引用须实际存在且字节匹配。Logic 研究过程每项还须有真实 evidence；启用 source_ids 核查时仅使用已登记来源。actual_actions、commands 或其他自定义列表可以是原始日志，但不能代替顶层 process.events。

格式示意（占位文字和路径必须换成当时真实记录；示例不是任何任务已执行的证据）：

```json
{"events":[{"action":"实际操作名称","record":"当时完成/失败的具体操作、观察与范围","artifacts":[{"path":"/absolute/actual-evidence-file","sha256":"该文件真实SHA256","bytes":123}]}]}
```

执行时随实际操作保存命令、返回、产物、失败、读取来源和时间范围，事件 record 引用对应真实记录。若已有 actual_actions / commands 等原始记录，只把已发生事项准确适配为 events，并保存原始文件及适配理由；不能补造未做操作、把示例当日志或从终稿倒填前置行为。技术文件路径和哈希属于过程证据，不增加下游作者的内容输入。校验条件和可接受范围沿用原 validate_process；错误信息只明确指出 process.events 字段。
