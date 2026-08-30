# 运行时架构

v0.7.0 保留 v0.5.2 对演示推理、受治理检索与执行的分离，并把 Logic 前的资源盘点升级为强制步骤。唯一 Public Core 与随包公共 Provider 在所有目标中构成同一个脑；本地适配器执行 Local Light 路线，ChatGPT 宿主工具构成 Cloud Light 的身体。五个 Skill 继续拥有内容和设计决策；Runtime 负责资源与能力发现、路线锁定、有界工具调用和宿主边界。

## 固定生命周期

`自然语言请求 → Supervisor签发新鲜任务挑战并绑定配置 → 一次预检与资源简报 → 锁定路线/来源 → Logic → Copy → Art Direction → Output构建 → Supervisor最终渲染审计 → 最多一次定向修复 → 经校验的成对发布目录`

运行中不换路线。后端发生硬失败时结束本次运行；中央配置最多允许从新预检开始一次备选路线重启。

## 模型交互

A—D 是能力分级，不是模型品牌排名。A、B 可直接编排 Runtime；C 输出内部结构化交接，由外部适配器执行；D 有窄工具能力时只调用一次，否则复用 C 的路线。用户不需要手写 JSON。

Codex 与 marketplace 插件宿主应把“生成 PPT”的意图绑定到五个 Clayz Skill，由 Supervisor 起点把新文稿路由到 Logic，再按批准状态逐层交接。ChatGPT Skills 宿主使用一个复合根 Skill 执行同样的 Supervisor 前置控制，并在每次转换时只读取所需内部阶段模块。只暴露演示工具、但不经过这些受治理阶段，不属于符合本架构的接入。

云端宿主先检查当前真实可用的演示能力，再向预检传入任务级 `host_capabilities` 声明；声明“可用”时，必须携带相同 run/task/nonce/challenge 字段，以及指向预检脚本已校验 inventory 文件的结构化 SHA-256 回执。Runtime 只能据此把 `native-presentation-tool` 锁定为 provisional/attemptable 路线；声明必须保持 `host-declared-unverified`，不得标记为 `verified: true`，也不能把路线写成 ready。该路线可继续非制作阶段并锁定尝试一次 Output，但只有写盘 PPTX 对象和最终渲染被独立校验后才可交付；宿主声明本身既不是随包工具，也不是永久可用承诺。

运行时预检合同 1.2 根据规范化任务请求的实际字节签发运行 ID、任务请求 SHA-256、nonce、任务根摘要和有限有效期。签发器写入 `.clayz-run-challenges/<run>.issued.json`；唯一一次扫描必须再次提交同一任务字节和同一任务根，重读并校验该签发台账，再以排他写入方式生成 `.clayz-run-challenges/consumed/<challenge-sha>.json`。预检库会重新读取两份台账并核对其字节哈希，因此复制或改名挑战不能形成第二次运行，移动到另一任务根也会被拒绝。随后预检绑定实际 resolved config SHA-256。`required_capabilities` 必须取 resolved config 与任务追加要求的并集，调用方不得缩减配置要求。预检再把这些制作路线硬条件与目标应用验收分开：`target_application_checks` 无论有无都逐项记录配置中的 PowerPoint、WPS、LibreOffice 等目标，结果为 `available`/`unavailable`，且始终 `blocks_authoring=false`。目标应用不可用时继续制作并在最终审计中记录 `deferred`；能力可用但未入选时记录 `not-selected`；只有实际执行后才能记录 `pass` 或 `fail`。

最终报告校验通过后，`scripts/publish_supervised_pair.py` 是唯一正常交付路径。它先把 PPTX 与报告复制到全新暂存目录，对暂存字节做语义校验，再原子发布目录，并对发布后字节重复哈希与语义校验。目录中只包含 PPTX、`ppt-supervision-report.json` 和 `delivery-manifest.json`。人工单独复制 PPTX 或报告不构成完成交付。

## 依赖层级

1. 通用作者链：Python 3.10+、`python-pptx`、Pillow、PyYAML；不要求宿主模型提供私有演示工具。
2. v0.7.0 本地发布的最终渲染：Windows 使用一个 PowerPoint COM 进程。Cloud Public Light 可在预检时选择宿主提供的演示或 Artifact Tool 路线。其他本地操作系统路线不是本版发布承诺。
3. 按需媒体能力：只有 PDF 页面输入或 LibreOffice 的 PDF→PNG 渲染路线才需要 Poppler；只有实际使用 SVG 且当前后端不能原生插入时才需要 SVG 转换器。

仓库自带合同、适配器、验证器、预检逻辑和分系统启动脚本。第三方应用与二进制只有在许可和平台打包单独审查后才可随包分发。

## 公共 Light 目标与本地系统包

运行`python scripts/build_runtime_packs.py --bundle light`可在`dist/`生成确定性的 Cloud Public Light 与 Local Public Light。两者绑定相同的 `public_core_sha256` 和公共 Provider snapshot。Cloud Light 因 ChatGPT 已提供工具而排除本地适配器与系统包；Local Light 保留本地执行路线。维护者用`scripts/fetch_offline_wheels.py --platform windows`暂存经过审阅的 CPython 3.12 wheel，v0.7.0 只生成 Windows 离线依赖附加包。两个 Light 都不带第三方 wheel，本版不生成 macOS、Linux 或 iOS 发版包。详见[`release-packages.zh-CN.md`](release-packages.zh-CN.md)。
