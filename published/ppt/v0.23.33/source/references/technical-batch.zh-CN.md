# 确定性技术步骤批处理

先完整理解当前必要的研究、Copy正文/关系及设计知识。专业原文不通过本接口压成摘要；模型仍负责判断和专业取舍。

对已准备好的本地生成/检查脚本，写一份`io.clayz.presentation.technical-batch/1` JSON：`case_root`、`run_id`、`context_id`、`role`、当前包的精确`packet`引用，以及有限`actions`。每项有稳定`id`、已存在程序的`program`精确path/bytes/SHA256、字面量`arguments`数组和可选超时秒数。程序属于本轮或当前工具包。运行`scripts/technical_batch.py --plan ... --registry ... --output 新目录`。

批处理使用当前Python环境，不开shell，不安装依赖。各动作顺序执行，完整stdout/stderr与程序身份保存在本轮，不在模型上下文中反复打印整份技术JSON。只输出有限机械摘要及精确回执；失败或超时即停止，不重复成功动作、不自动重试。需要诊断时按当前错误读取必要字段，不能为少读日志丢掉真实失败。

Office仍只能通过本轮已绑定的唯一原Office执行器，原保存/导出/回退预算及实际累计计数不变。批处理不提供新预算，也不代替原生校验或权限边界。新建PPTX仍须由原先的单次保存保护与实际回执核对，不能借一个批次隐藏多次保存。

该API限定本case/run/role；已登记有读图观察或退役的物理上下文不能继续技术批处理。先在无图阶段准备脚本并核验，再集中看图、集中写完整专业判断/coverage并结束；之后需要机械修订，使用fresh无图上下文和明确工件指针。主机未向工具报告的内部重放不受此API控制，登记不构成OS或签名隔离。

程序可以属于本轮目录、当前传输工具包，或initialized.json中实际固定的本轮Native工具包；后者按程序精确hash核对，不能把别轮产物当工具代码。

记录实际批次数、命令数与原始技术输出。API返回数据，不声称它已经输出给模型：`serialized_cli_summary_bytes`只是该数据按标准CLI形式序列化的大小。标准CLI另记实际写入其stdout的`actual_cli_stdout_bytes`；调用者仍可能重定向、过滤或摘要，因此两者都不是实际模型输入或VPN字节。Tool29的`actual_summary_bytes`在直接API调用时也只能解释为名义CLI序列化大小，旧记录保留并标明这个限制，不当作节省实测。质量、实际模型usage和真实网络计数分别核验；一次批处理也不等于自动节省了相同数量的模型调用。
